"""
Admin/monitoring API for the orchestrator.

Read endpoints are open (no auth) for the frontend polling case, while
mutating / fleet-wide endpoints (`/retry`, `/workflows/active`) require
HTTP Basic Auth so they are not exposed via the public gateway by default.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
from typing import Optional

import redis.asyncio as redis
from aiokafka import AIOKafkaProducer
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from ..config import KAFKA_BROKERS, REDIS_URL, TOPIC_CV_ANALYZED

logger = logging.getLogger(__name__)
router = APIRouter(tags=["monitoring"])

_redis = redis.from_url(REDIS_URL, decode_responses=True)
_security = HTTPBasic()

ADMIN_USERNAME = os.getenv("ORCHESTRATOR_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ORCHESTRATOR_ADMIN_PASSWORD", "")


def _require_admin(credentials: HTTPBasicCredentials = Depends(_security)) -> str:
    if not ADMIN_PASSWORD:
        # Refuse to operate with an unset password — fail-closed.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin endpoints disabled: ORCHESTRATOR_ADMIN_PASSWORD is not set.",
        )
    user_ok = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    pass_ok = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ---------- Response models ---------- #


class WorkflowStatus(BaseModel):
    user_id: str
    current_node: Optional[str] = None
    cv_score: Optional[int] = None
    target_role: Optional[str] = None
    retry_count: int = 0
    error: Optional[str] = None


class WorkflowHistoryEntry(BaseModel):
    user_id: str
    current_node: Optional[str] = None
    state: dict
    last_event: Optional[dict] = None


class RetryResult(BaseModel):
    user_id: str
    replayed_topic: str
    cleared_state: bool


class ActiveWorkflowsSummary(BaseModel):
    total: int
    by_node: dict[str, int]
    by_flow: dict[str, int]  # job_search / learning_path / failed / unknown


# ---------- Helpers ---------- #


def _classify_flow(state: dict) -> str:
    node = (state.get("current_node") or "").lower()
    if "job_search" in node:
        return "job_search"
    if "learning_path" in node:
        return "learning_path"
    if "fail" in node:
        return "failed"
    return "unknown"


async def _load_workflow(user_id: str) -> Optional[dict]:
    raw = await _redis.get(f"workflow:{user_id}")
    return json.loads(raw) if raw else None


async def _load_last_event(user_id: str) -> Optional[dict]:
    raw = await _redis.get(f"workflow:{user_id}:last_event")
    return json.loads(raw) if raw else None


# ---------- Endpoints ---------- #


@router.get("/workflow/{user_id}", response_model=WorkflowHistoryEntry)
async def get_workflow_history(user_id: str):
    """Full snapshot: current LangGraph state + the original triggering event."""
    state = await _load_workflow(user_id)
    if state is None:
        raise HTTPException(status_code=404, detail="No workflow for this user")
    return WorkflowHistoryEntry(
        user_id=user_id,
        current_node=state.get("current_node"),
        state=state,
        last_event=await _load_last_event(user_id),
    )


@router.post(
    "/workflow/{user_id}/retry",
    response_model=RetryResult,
    dependencies=[Depends(_require_admin)],
)
async def retry_workflow(user_id: str):
    """
    Re-runs the workflow for a user by re-publishing the original
    `cv.analyzed` event. Clears the cached state first so the next
    consumer pass starts fresh.
    """
    last_event = await _load_last_event(user_id)
    if last_event is None:
        raise HTTPException(
            status_code=404,
            detail="No cached trigger event for this user — nothing to retry.",
        )

    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    await producer.start()
    try:
        payload = json.dumps(last_event).encode("utf-8")
        await producer.send_and_wait(TOPIC_CV_ANALYZED, payload)
    finally:
        await producer.stop()

    await _redis.delete(f"workflow:{user_id}")
    logger.info("Workflow retry triggered for user %s", user_id)

    return RetryResult(
        user_id=user_id,
        replayed_topic=TOPIC_CV_ANALYZED,
        cleared_state=True,
    )


@router.get(
    "/workflows/active",
    response_model=ActiveWorkflowsSummary,
    dependencies=[Depends(_require_admin)],
)
async def list_active_workflows():
    """
    Scans `workflow:*` keys (skipping `:last_event` companions) and aggregates
    counts per LangGraph node and per flow category.
    """
    by_node: dict[str, int] = {}
    by_flow: dict[str, int] = {}
    total = 0

    async for key in _redis.scan_iter(match="workflow:*", count=200):
        if key.endswith(":last_event"):
            continue
        raw = await _redis.get(key)
        if not raw:
            continue
        try:
            state = json.loads(raw)
        except json.JSONDecodeError:
            continue
        total += 1
        node = state.get("current_node") or "unknown"
        by_node[node] = by_node.get(node, 0) + 1
        flow = _classify_flow(state)
        by_flow[flow] = by_flow.get(flow, 0) + 1

    return ActiveWorkflowsSummary(total=total, by_node=by_node, by_flow=by_flow)
