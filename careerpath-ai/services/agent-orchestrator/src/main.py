 from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import redis.asyncio as redis
import json
from .consumer import run_consumer_in_background
from .config import REDIS_URL
from prometheus_fastapi_instrumentator import Instrumentator

# Redis client instance
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    run_consumer_in_background()
    yield
    # On shutdown
    await redis_client.close()

app = FastAPI(
    title="Agent Orchestrator",
    description="Coordinates AI agents based on CV analysis results.",
    lifespan=lifespan
)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/workflow/{user_id}/status")
async def get_workflow_status(user_id: str):
    """
    Retrieves the last known state of a user's workflow from Redis.
    """
    state_json = await redis_client.get(f"workflow:{user_id}")
    if not state_json:
        raise HTTPException(status_code=404, detail="Workflow state not found for this user.")

    return json.loads(state_json)
