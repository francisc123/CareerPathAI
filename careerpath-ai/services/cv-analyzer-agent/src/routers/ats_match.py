"""
CP-052 — Synchronous ATS keyword match endpoint.

Unlike the async `cv.uploaded` consumer pipeline, this endpoint is meant for
the frontend's "tailor my CV to this job" flow: the user pastes a job
description, the CV is already known (or pasted), and the response is needed
inline. We call Gemini directly and return the structured match report.

Schema lives in `prompts/ats_match.txt`. Validation: any non-JSON output from
Gemini collapses to a 502 (so the caller surfaces a retry-able error rather
than serving garbage).
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from src.config.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cv", tags=["ATS"])

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")
_PROMPT_PATH = os.path.join(_PROMPTS_DIR, "ats_match.txt")

with open(_PROMPT_PATH, "r", encoding="utf-8") as _f:
    ATS_MATCH_PROMPT = _f.read()

_MODEL = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")
_MAX_CV_CHARS = 20_000
_MAX_JD_CHARS = 10_000


# ---------- Pydantic models ---------- #


class ATSMatchRequest(BaseModel):
    cv_text: str = Field(..., min_length=80, max_length=_MAX_CV_CHARS)
    job_description: str = Field(..., min_length=40, max_length=_MAX_JD_CHARS)


class PartialMatch(BaseModel):
    jd_term: str
    cv_term: str
    note: str


class SuggestedRewrite(BaseModel):
    cv_section: str
    current: str
    suggested: str
    why: str


class ATSMatchResponse(BaseModel):
    match_rate_pct: int = Field(..., ge=0, le=100)
    verdict: str
    matched_keywords: list[str]
    missing_keywords: list[str]
    partial_matches: list[PartialMatch] = []
    anti_patterns: list[str] = []
    suggested_rewrites: list[SuggestedRewrite] = []
    ats_readiness_notes: list[str] = []


# ---------- Helper ---------- #


def _extract_json(raw: str) -> Optional[dict]:
    """Gemini occasionally wraps JSON in ```json fences even with mime_type set."""
    if not raw:
        return None
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("ATS match returned non-JSON: %s", raw[:200])
        return None


# ---------- Endpoint ---------- #


@router.post(
    "/ats-match",
    response_model=ATSMatchResponse,
    summary="Score a CV against a job description (ATS-style)",
)
async def ats_match(request: ATSMatchRequest) -> ATSMatchResponse:
    user_content = (
        f"JOB DESCRIPTION:\n{request.job_description}\n\n"
        f"CV TEXT:\n{request.cv_text}"
    )
    try:
        response = await get_gemini_client().aio.models.generate_content(
            model=_MODEL,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=ATS_MATCH_PROMPT,
                response_mime_type="application/json",
            ),
        )
    except Exception:
        logger.exception("Gemini call failed for ATS match.")
        raise HTTPException(status_code=502, detail="LLM provider unreachable")

    payload = _extract_json(response.text or "")
    if payload is None:
        raise HTTPException(status_code=502, detail="LLM returned invalid JSON")

    try:
        return ATSMatchResponse(**payload)
    except ValidationError as exc:
        logger.warning("ATS match response failed schema validation: %s", exc)
        raise HTTPException(
            status_code=502, detail="LLM response did not match expected schema"
        )
