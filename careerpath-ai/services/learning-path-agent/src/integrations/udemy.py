"""
Udemy Affiliate API wrapper.

Get credentials at https://www.udemy.com/affiliate/
Set in `.env`:
  UDEMY_CLIENT_ID=...
  UDEMY_CLIENT_SECRET=...

If either is missing we degrade gracefully and return [].
"""

from __future__ import annotations

import base64
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

_BASE_URL = "https://www.udemy.com/api-2.0/courses/"
_TIMEOUT = httpx.Timeout(10.0)
_CLIENT_ID = os.getenv("UDEMY_CLIENT_ID")
_CLIENT_SECRET = os.getenv("UDEMY_CLIENT_SECRET")


def _is_placeholder(v: str | None) -> bool:
    return bool(v) and v.startswith(("your-", "YOUR-", "REPLACE_ME", "changeme"))


def _auth_header() -> dict[str, str] | None:
    if not (_CLIENT_ID and _CLIENT_SECRET):
        return None
    if _is_placeholder(_CLIENT_ID) or _is_placeholder(_CLIENT_SECRET):
        return None
    token = base64.b64encode(f"{_CLIENT_ID}:{_CLIENT_SECRET}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json, text/plain, */*",
    }


async def search_courses(
    query: str,
    *,
    max_results: int = 3,
    max_price: float | None = 20.0,
    min_rating: float = 4.5,
) -> list[dict[str, Any]]:
    """
    Returns a list of dicts shaped like our Resource schema:
      [{"type": "course", "title": ..., "url": ...}, ...]

    Never raises. Returns [] on missing creds, transient failures, or no hits.
    """
    headers = _auth_header()
    if headers is None:
        logger.info("UDEMY_CLIENT_ID/SECRET unset — Udemy lookup skipped for '%s'.", query)
        return []

    params: dict[str, Any] = {
        "search": query,
        "page_size": max_results,
        "ordering": "highest-rated",
        "ratings": min_rating,
    }
    if max_price is not None:
        # The API accepts either `price=price-free` or a price filter via `price`.
        # We approximate "cheap-or-free" with a coarse filter.
        params["price"] = "price-free" if max_price <= 0 else "price-paid,price-free"

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            retry=retry_if_exception_type(httpx.HTTPError),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(timeout=_TIMEOUT, headers=headers) as client:
                    resp = await client.get(_BASE_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    break
    except httpx.HTTPError as exc:
        logger.warning("Udemy search failed for '%s': %s", query, exc)
        return []

    results: list[dict[str, Any]] = []
    for course in (data or {}).get("results", [])[:max_results]:
        url_path = course.get("url") or ""
        results.append(
            {
                "type": "course",
                "title": course.get("title") or "Untitled course",
                "url": f"https://www.udemy.com{url_path}" if url_path.startswith("/") else url_path,
            }
        )
    logger.info("Udemy returned %d courses for '%s'.", len(results), query)
    return results
