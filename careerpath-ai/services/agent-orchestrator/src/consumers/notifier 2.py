"""
Best-effort SSE notifier — posts to notification-service.

Notification-service is owned by Francisc and currently a stub. We catch all
HTTP errors so a missing endpoint never breaks the workflow loop.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

NOTIFICATION_SERVICE_URL = os.getenv(
    "NOTIFICATION_SERVICE_URL", "http://cp-notification:8004"
)
NOTIFY_TIMEOUT_SECONDS = 3.0


async def notify_user(user_id: str, event_type: str, payload: dict[str, Any]) -> None:
    """
    Fire-and-forget POST. Logs but never raises so it cannot block consumers.
    """
    url = f"{NOTIFICATION_SERVICE_URL}/notify/{user_id}"
    body = {"type": event_type, "data": payload}
    try:
        async with httpx.AsyncClient(timeout=NOTIFY_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=body)
            if response.status_code >= 400:
                logger.warning(
                    "notification-service %s returned %d for user %s",
                    url,
                    response.status_code,
                    user_id,
                )
    except httpx.HTTPError as exc:
        logger.warning("Notification call failed for user %s: %s", user_id, exc)
