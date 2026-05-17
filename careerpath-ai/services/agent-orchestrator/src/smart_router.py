"""
LLM-based routing decision for the orchestrator.

Replaces the binary `if score >= 70` rule with a small Gemini call that looks
at the full picture (score, gaps, target_role, optionally chat signals) and
returns one of four routes:

  - job_search        — CV is solid, prioritize matching to jobs
  - learning_path     — CV needs upskilling first
  - hybrid            — borderline: do both in parallel
  - recommend_pivot   — target role mismatches CV; suggest career pivot

The function NEVER raises — on any failure it falls back to the legacy binary
rule so the orchestrator can always make a routing decision.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Literal

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

_MODEL = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")
_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_client: genai.Client | None = None

Route = Literal["job_search", "learning_path", "hybrid", "recommend_pivot"]
VALID_ROUTES: set[str] = {"job_search", "learning_path", "hybrid", "recommend_pivot"}

ROUTER_SYSTEM_PROMPT = """
You are the routing brain of a career-coaching pipeline. Given a CV analysis
result, decide what the user should do NEXT. Return STRICT JSON:

{"route": "job_search" | "learning_path" | "hybrid" | "recommend_pivot",
 "reason": "one short sentence explaining the choice"}

Heuristics (apply your judgment, not a rigid formula):
- score >= 75 AND <= 2 critical gaps for target_role → "job_search"
- score < 55 → "learning_path"
- 55 <= score < 75 with manageable gaps → "hybrid" (do both)
- target_role is wildly mismatched with skills (e.g. CV is Data Scientist but
  target is Mobile Dev with zero mobile evidence) → "recommend_pivot"
- When in doubt between learning_path and hybrid, prefer hybrid.

Output ONLY the JSON, no other text.
"""


def _get_client() -> genai.Client | None:
    global _client
    if not _GEMINI_API_KEY:
        return None
    if _client is None:
        _client = genai.Client(api_key=_GEMINI_API_KEY)
    return _client


def _fallback_route(score: int) -> Route:
    """Legacy binary rule — used when the LLM call cannot run or returns junk."""
    return "job_search" if score >= 70 else "learning_path"


async def decide_route(
    *,
    score: int,
    gaps: list[str],
    target_role: str,
    timeout_seconds: float = 6.0,
) -> tuple[Route, str]:
    """
    Returns (route, reason). Reason is a human-readable sentence the orchestrator
    can surface in the workflow state for monitoring/debugging.
    """
    client = _get_client()
    if client is None:
        route = _fallback_route(score)
        return route, "fallback: GEMINI_API_KEY missing"

    payload = {"cv_score": score, "gaps": gaps, "target_role": target_role}

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=_MODEL,
                contents=json.dumps(payload),
                config=types.GenerateContentConfig(
                    system_instruction=ROUTER_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                ),
            ),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.warning("Smart router timed out — using fallback for score=%s.", score)
        return _fallback_route(score), "fallback: router timeout"
    except Exception:
        logger.exception("Smart router LLM call failed — using fallback.")
        return _fallback_route(score), "fallback: router error"

    try:
        decision = json.loads(response.text or "{}")
    except json.JSONDecodeError:
        logger.warning("Router returned non-JSON: %s", (response.text or "")[:120])
        return _fallback_route(score), "fallback: invalid JSON"

    route = decision.get("route")
    reason = (decision.get("reason") or "").strip() or "(no reason given)"
    if route not in VALID_ROUTES:
        logger.warning("Router returned invalid route %r — fallback.", route)
        return _fallback_route(score), f"fallback: invalid route {route!r}"

    return route, reason  # type: ignore[return-value]
