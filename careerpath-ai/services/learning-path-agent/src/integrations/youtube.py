"""
YouTube Data API v3 wrapper — only the `search.list` endpoint.

Enable at https://console.cloud.google.com/apis/library/youtube.googleapis.com
Set in `.env`:
  YOUTUBE_API_KEY=...

Quota: 1,000 units/day on the free tier; `search.list` costs 100 units per call.
That's only 10 calls/day, so callers should cache aggressively (cache layer is
out of scope for this module — we just hit the API).
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.googleapis.com/youtube/v3/search"
_TIMEOUT = httpx.Timeout(10.0)
_API_KEY = os.getenv("YOUTUBE_API_KEY")
# Treat the .env.example placeholder as "unset" so we don't spam the API with
# guaranteed-400s. Anything starting with "your-" or "REPLACE_ME" is a stub.
_PLACEHOLDER = bool(_API_KEY) and (
    _API_KEY.startswith(("your-", "YOUR-", "REPLACE_ME", "changeme"))
)


async def search_videos(query: str, *, max_results: int = 3) -> list[dict[str, Any]]:
    """
    Returns Resource-shaped dicts:
      [{"type": "video", "title": ..., "url": "https://youtu.be/..."}, ...]
    """
    if not _API_KEY or _PLACEHOLDER:
        logger.info("YOUTUBE_API_KEY unset/placeholder — YouTube lookup skipped.")
        return []

    params = {
        "key": _API_KEY,
        "q": f"{query} tutorial",
        "part": "snippet",
        "type": "video",
        "maxResults": max_results,
        "order": "viewCount",
        "videoEmbeddable": "true",
        "safeSearch": "moderate",
    }

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            retry=retry_if_exception_type(httpx.HTTPError),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(_BASE_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    break
    except httpx.HTTPError as exc:
        logger.warning("YouTube search failed for '%s': %s", query, exc)
        return []

    results: list[dict[str, Any]] = []
    for item in (data or {}).get("items", [])[:max_results]:
        video_id = (item.get("id") or {}).get("videoId")
        snippet = item.get("snippet") or {}
        if not video_id:
            continue
        results.append(
            {
                "type": "video",
                "title": snippet.get("title") or "YouTube video",
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )
    logger.info("YouTube returned %d videos for '%s'.", len(results), query)
    return results
