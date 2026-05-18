"""
Shared helpers for reading/updating the per-user workflow state in Redis.

All completion consumers converge on `workflow:{user_id}` and merge their
contribution (learning_done, hr_done/score, tech_done/score, etc.) so the
final score and the workflow.completed event can be computed deterministically.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STATE_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days — covers a typical user journey

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def _key(user_id: str) -> str:
    return f"workflow:{user_id}"


async def load_state(user_id: str) -> dict[str, Any]:
    raw = await get_redis().get(_key(user_id))
    if not raw:
        return {"user_id": user_id}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Corrupt workflow state for %s — resetting.", user_id)
        return {"user_id": user_id}


async def merge_state(user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """
    Read-merge-write. Not atomic across multiple consumers, but a single user's
    HR / tech / learning events arrive infrequently enough that we accept the
    tradeoff for simplicity.
    """
    state = await load_state(user_id)
    state.update(updates)
    state["user_id"] = user_id
    await get_redis().set(_key(user_id), json.dumps(state), ex=STATE_TTL_SECONDS)
    return state
