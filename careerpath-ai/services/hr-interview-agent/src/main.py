import json
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect

from .auth import WebSocketAuthError, authenticate_ws
from .connection_manager import manager
from .conversation import (
    InterviewSummary,
    MAX_TURNS,
    analyze_and_save_transcript,
    get_turn_count,
    increment_turn_count,
    reset_session_state,
    stream_ai_response,
)
from .prompts import get_initial_greeting, normalize_lang
from .publishers.interview_completed_publisher import (
    init_producer,
    publish_interview_hr_completed,
    stop_producer,
)
from .retry import startup_retry  # noqa: F401  - utility decorator available to wrap startup tasks

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_producer()
    try:
        yield
    finally:
        await stop_producer()


app = FastAPI(title="HR Interview Agent", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


def _parse_ws_message(raw: str) -> tuple[str, str]:
    """
    The frontend wraps messages as `{"type": "chat_message", "text": "..."}` or
    sends `{"type": "end_interview"}`. Older clients send raw text. Return
    (msg_type, content) so the rest of the handler can stay simple.
    """
    raw = (raw or "").strip()
    if raw.startswith("{"):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return "chat_message", raw
        msg_type = str(payload.get("type") or "chat_message")
        content = str(payload.get("text") or payload.get("content") or "")
        return msg_type, content
    return "chat_message", raw


async def _finalize_session(
    session_id: str,
    user_id: str,
    reason: str,
    lang: str = "en",
    summary: InterviewSummary | None = None,
) -> InterviewSummary | None:
    """Run post-interview analysis (if not already done), publish event, clean up Redis."""
    try:
        if summary is None:
            summary = await analyze_and_save_transcript(session_id, user_id, lang=lang)
        await publish_interview_hr_completed(
            user_id=user_id,
            session_id=session_id,
            verdict=summary.verdict,
            summary=summary.summary,
            strengths=summary.strengths,
            areas_of_improvement=summary.areas_of_improvement,
            transcript=summary.transcript,
            turn_count=summary.turn_count,
            reason=reason,
        )
        return summary
    except Exception:
        logger.exception("Eroare la finalizarea session %s.", session_id)
        return summary
    finally:
        try:
            await reset_session_state(session_id)
        except Exception:
            logger.exception("Reset state Redis eșuat pentru session %s.", session_id)


@app.websocket("/interview/hr/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    lang: str = Query("en", description="Interview language: 'en' or 'ro'"),
    user_id: str = Depends(authenticate_ws),
):
    """
    WebSocket endpoint for an HR interview session.

    Auth: pass `?token=<JWT>` in the query string. The token's `sub` claim
    is the authoritative user_id (we no longer accept it from the path,
    which would let any client impersonate any user).

    Localization: pass `?lang=ro` for Romanian, otherwise English.
    """
    lang = normalize_lang(lang)
    await manager.connect(session_id, websocket)
    # Spec requires the FIRST greeting in EN (handled by prompts) and "instant"
    # render with no character-by-character animation, so we always send the
    # full message in a single JSON envelope.
    await websocket.send_json(
        {"type": "chat_message", "text": get_initial_greeting(lang)}
    )

    reason = "session_ended"
    early_summary: InterviewSummary | None = None
    try:
        while True:
            raw = await websocket.receive_text()
            msg_type, content = _parse_ws_message(raw)

            if msg_type == "end_interview":
                reason = "session_ended"
                break

            if not content:
                continue

            turn = await increment_turn_count(session_id)

            # Collect the full AI reply, then emit it once. No mid-stream sends
            # → frontend renders the entire bubble instantly per spec.
            full_reply = ""
            async for chunk in stream_ai_response(session_id, content, lang=lang):
                full_reply += chunk
            await websocket.send_json({"type": "chat_message", "text": full_reply})

            if turn >= MAX_TURNS:
                logger.info(
                    "Limită de %d turns atinsă pentru session %s — închid conversația.",
                    MAX_TURNS,
                    session_id,
                )
                reason = "turn_limit_reached"
                break

        # Natural end (turn limit or explicit end_interview): analyze NOW so we
        # can push the verdict over the still-open WS before disconnecting.
        early_summary = await analyze_and_save_transcript(session_id, user_id, lang=lang)
        try:
            await websocket.send_json({
                "type": "interview_complete",
                "verdict": early_summary.verdict,
                "summary": early_summary.summary,
                "strengths": early_summary.strengths,
                "areas_of_improvement": early_summary.areas_of_improvement,
            })
        except Exception:
            logger.exception("Trimitere interview_complete eșuată pentru %s.", session_id)
        try:
            await websocket.close(code=1000, reason="Interview complete")
        except Exception:
            pass

    except WebSocketDisconnect:
        reason = "disconnect"
        logger.info("Session %s deconectată de client.", session_id)
    except Exception:
        reason = "error"
        logger.exception("Eroare neașteptată în session %s.", session_id)
    finally:
        manager.disconnect(session_id)
        await _finalize_session(
            session_id, user_id, reason, lang=lang, summary=early_summary
        )


@app.exception_handler(WebSocketAuthError)
async def _ws_auth_handler(_, __):
    # The dependency already closed the socket; nothing else to do.
    return None
