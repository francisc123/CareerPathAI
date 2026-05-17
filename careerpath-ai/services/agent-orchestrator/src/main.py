from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis
import json
import logging
from .consumer import run_consumer_in_background
from .config import REDIS_URL
from .chat_agent import chat
from prometheus_fastapi_instrumentator import Instrumentator
from .retry import startup_retry

logger = logging.getLogger(__name__)

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Tracks active WebSocket sessions: user_id -> WebSocket
_active_ws: dict[str, WebSocket] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_consumer_in_background()
    yield
    await redis_client.aclose()


app = FastAPI(
    title="Agent Orchestrator",
    description="Conversational AI agent + CV workflow coordinator.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/workflow/{user_id}/status")
async def get_workflow_status(user_id: str):
    state_json = await redis_client.get(f"workflow:{user_id}")
    if not state_json:
        raise HTTPException(status_code=404, detail="Workflow state not found for this user.")
    return json.loads(state_json)


@app.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """Returns the shadow profile extracted from conversation."""
    profile_json = await redis_client.get(f"profile:{user_id}")
    if not profile_json:
        raise HTTPException(status_code=404, detail="No profile found yet.")
    return json.loads(profile_json)


@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    await websocket.accept()
    _active_ws[user_id] = websocket
    logger.info(f"WebSocket connected: user={user_id}")

    try:
        await websocket.send_json({"type": "typing"})
        greeting = await chat(user_id, "__init__")
        await websocket.send_json({"type": "message", "text": greeting["text"]})
        if greeting.get("cta"):
            await websocket.send_json({"type": "cta"})
    except Exception as e:
        logger.error(f"Greeting failed for {user_id}: {e}")
        await websocket.send_json({
            "type": "message",
            "text": "Hello! I'm CareerPath AI. Tell me about your career goals.",
        })

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data) if data.startswith("{") else {"message": data}
            user_message = payload.get("message", "").strip()

            if not user_message:
                continue

            await websocket.send_json({"type": "typing"})

            result = await chat(user_id, user_message)
            await websocket.send_json({"type": "message", "text": result["text"]})
            if result.get("cta"):
                await websocket.send_json({"type": "cta"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")
    finally:
        _active_ws.pop(user_id, None)