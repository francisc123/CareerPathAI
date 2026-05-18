"""
Minimal async WebSocket helpers for the Flow 3 e2e test.

Wraps the `websockets` library with a few convenience methods:
  • `collect_until` — read messages until a predicate matches (or timeout)
  • `expect_event` — assert a single envelope arrives with the given type
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any, AsyncIterator, Awaitable, Callable

import websockets

logger = logging.getLogger(__name__)


class WSTimeout(Exception):
    pass


@contextlib.asynccontextmanager
async def connect_ws(url: str) -> AsyncIterator[websockets.WebSocketClientProtocol]:
    logger.info("WS connect → %s", url)
    async with websockets.connect(url, max_size=10 * 1024 * 1024) as ws:
        yield ws


async def send_json(ws: websockets.WebSocketClientProtocol, payload: dict[str, Any]) -> None:
    await ws.send(json.dumps(payload))


async def collect_until(
    ws: websockets.WebSocketClientProtocol,
    predicate: Callable[[Any], bool | Awaitable[bool]],
    *,
    timeout: float = 30.0,
) -> list[Any]:
    """
    Read messages until `predicate(msg)` returns True. Returns all received
    messages including the one that satisfied the predicate.
    """
    collected: list[Any] = []

    async def _inner() -> None:
        while True:
            raw = await ws.recv()
            try:
                msg = json.loads(raw)
            except (TypeError, ValueError):
                msg = raw
            collected.append(msg)
            result = predicate(msg)
            if asyncio.iscoroutine(result):
                result = await result
            if result:
                return

    try:
        await asyncio.wait_for(_inner(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        raise WSTimeout(
            f"Timed out after {timeout}s waiting for predicate. "
            f"Got {len(collected)} messages."
        ) from exc

    return collected


async def expect_event(
    ws: websockets.WebSocketClientProtocol,
    event_type: str,
    *,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Read until an envelope with `type == event_type` arrives."""
    msgs = await collect_until(
        ws,
        lambda m: isinstance(m, dict) and m.get("type") == event_type,
        timeout=timeout,
    )
    return msgs[-1]
