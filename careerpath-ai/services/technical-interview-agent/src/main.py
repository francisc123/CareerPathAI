from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect

from .auth import WebSocketAuthError, authenticate_ws
from .connection_manager import manager
from .conversation import (
    MAX_PROBLEMS,
    analyze_and_save,
    grade_submission,
    has_more_problems,
    pick_next_problem,
    request_hint,
    reset_session,
    stream_ai_reply,
)
from .prompts import get_initial_greeting, normalize_lang
from .publishers.interview_completed_publisher import (
    init_producer,
    publish_interview_tech_completed,
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


app = FastAPI(title="Technical Interview Agent", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


async def _finalize(session_id: str, user_id: str, reason: str, lang: str = "en") -> None:
    try:
        summary = await analyze_and_save(session_id, user_id, lang=lang)
        await publish_interview_tech_completed(
            user_id=user_id,
            session_id=session_id,
            score=summary.score,
            feedback=summary.feedback,
            transcript=summary.transcript,
            problems_attempted=summary.problems_attempted,
            problems_passed=summary.problems_passed,
            reason=reason,
        )
        await manager.send_json(
            session_id,
            {
                "type": "session_end",
                "summary": {
                    "score": summary.score,
                    "feedback": summary.feedback,
                    "problems_attempted": summary.problems_attempted,
                    "problems_passed": summary.problems_passed,
                },
            },
        )
    except Exception:
        logger.exception("Tech interview finalize failed for %s.", session_id)
    finally:
        try:
            await reset_session(session_id)
        except Exception:
            logger.exception("reset_session failed for %s.", session_id)


@app.websocket("/interview/tech/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    skills: str = Query("", description="Comma-separated list of skills"),
    seniority: str = Query("mid", description="junior | mid | senior"),
    lang: str = Query("en", description="Interview language: 'en' or 'ro'"),
    user_id: str = Depends(authenticate_ws),
):
    lang = normalize_lang(lang)
    await manager.connect(session_id, websocket)
    skills_list = [s.strip() for s in skills.split(",") if s.strip()]

    await manager.send_json(session_id, {"type": "chat_done"})  # init handshake
    await manager.send_json(
        session_id, {"type": "chat_delta", "content": get_initial_greeting(lang)}
    )

    # Seed the first problem before the user types anything.
    first_problem = await pick_next_problem(
        session_id, skills=skills_list, seniority=seniority, lang=lang
    )
    if first_problem is None:
        await manager.send_json(
            session_id,
            {"type": "error", "message": "Could not pick a problem. Please retry."},
        )
        await websocket.close(code=1011)
        manager.disconnect(session_id)
        return
    await manager.send_json(session_id, {"type": "problem", "data": first_problem})

    reason = "session_ended"
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                envelope = json.loads(raw) if raw.startswith("{") else {"type": "chat", "content": raw}
            except json.JSONDecodeError:
                envelope = {"type": "chat", "content": raw}

            msg_type = envelope.get("type", "chat")

            if msg_type == "chat":
                content = envelope.get("content", "").strip()
                if not content:
                    continue
                async for delta in stream_ai_reply(session_id, content, lang=lang):
                    await manager.send_json(
                        session_id, {"type": "chat_delta", "content": delta}
                    )
                await manager.send_json(session_id, {"type": "chat_done"})

            elif msg_type == "hint_request":
                # User explicitly asked for a hint — bump the counter, then let
                # the next chat message generate the hint at the new level.
                new_level = await request_hint(session_id)
                await manager.send_json(
                    session_id,
                    {"type": "hint_acknowledged", "hint_level": new_level},
                )
                # Auto-generate the hint by sending a synthetic chat turn.
                hint_trigger = (
                    "I'm stuck — please give me a hint at the current level."
                    if lang == "en"
                    else "M-am blocat — dă-mi un hint la nivelul curent."
                )
                async for delta in stream_ai_reply(session_id, hint_trigger, lang=lang):
                    await manager.send_json(
                        session_id, {"type": "chat_delta", "content": delta}
                    )
                await manager.send_json(session_id, {"type": "chat_done"})

            elif msg_type == "code_submission":
                content = envelope.get("content", "")
                language = envelope.get("language", "python")
                if not content:
                    await manager.send_json(
                        session_id,
                        {"type": "error", "message": "Empty code submission."},
                    )
                    continue

                result = await grade_submission(
                    session_id, source_code=content, language=language, lang=lang
                )
                await manager.send_json(
                    session_id, {"type": "test_results", "data": result}
                )

                # Advance to next problem (or finalize) after each submission.
                if await has_more_problems(session_id):
                    next_problem = await pick_next_problem(
                        session_id, skills=skills_list, seniority=seniority, lang=lang
                    )
                    if next_problem is None:
                        await manager.send_json(
                            session_id,
                            {"type": "error", "message": "Could not pick next problem."},
                        )
                    else:
                        await manager.send_json(
                            session_id, {"type": "problem", "data": next_problem}
                        )
                else:
                    reason = "session_ended"
                    await websocket.close(
                        code=1000,
                        reason=f"Completed {MAX_PROBLEMS} problems",
                    )
                    break
            else:
                await manager.send_json(
                    session_id,
                    {"type": "error", "message": f"Unknown message type: {msg_type}"},
                )

    except WebSocketDisconnect:
        reason = "disconnect"
        logger.info("Tech interview session %s disconnected.", session_id)
    except Exception:
        reason = "error"
        logger.exception("Tech interview session %s crashed.", session_id)
    finally:
        manager.disconnect(session_id)
        await _finalize(session_id, user_id, reason, lang=lang)


@app.exception_handler(WebSocketAuthError)
async def _ws_auth_handler(_, __):
    return None
