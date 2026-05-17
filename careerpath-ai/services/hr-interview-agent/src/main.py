import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect

from .auth import WebSocketAuthError, authenticate_ws
from .connection_manager import manager
from .conversation import (
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


async def _finalize_session(
    session_id: str, user_id: str, reason: str, lang: str = "en"
) -> None:
    """Run post-interview analysis, publish event, then clean up Redis."""
    try:
        summary = await analyze_and_save_transcript(session_id, user_id, lang=lang)
        await publish_interview_hr_completed(
            user_id=user_id,
            session_id=session_id,
            score=summary.score,
            feedback=summary.feedback,
            transcript=summary.transcript,
            turn_count=summary.turn_count,
            reason=reason,
        )
    except Exception:
        logger.exception("Eroare la finalizarea session %s.", session_id)
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
    await manager.send_message(get_initial_greeting(lang), session_id)

    reason = "session_ended"
    try:
        while True:
            user_message = await websocket.receive_text()

            turn = await increment_turn_count(session_id)

            async for chunk in stream_ai_response(session_id, user_message, lang=lang):
                await manager.send_message(chunk, session_id)

            if turn >= MAX_TURNS:
                logger.info(
                    "Limită de %d turns atinsă pentru session %s — închid conversația.",
                    MAX_TURNS,
                    session_id,
                )
                await manager.send_message(
                    "[SYSTEM] We've reached the end of this interview. "
                    "Thank you for your time — generating your feedback now.",
                    session_id,
                )
                reason = "turn_limit_reached"
                await websocket.close(code=1000, reason="Turn limit reached")
                break

    except WebSocketDisconnect:
        reason = "disconnect"
        logger.info("Session %s deconectată de client.", session_id)
    except Exception:
        reason = "error"
        logger.exception("Eroare neașteptată în session %s.", session_id)
    finally:
        manager.disconnect(session_id)
        await _finalize_session(session_id, user_id, reason, lang=lang)


@app.exception_handler(WebSocketAuthError)
async def _ws_auth_handler(_, __):
    # The dependency already closed the socket; nothing else to do.
    return None
