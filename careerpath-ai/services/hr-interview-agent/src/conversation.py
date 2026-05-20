import json
import logging
from typing import AsyncIterator, NamedTuple

from google import genai
from google.genai import types
import redis.asyncio as redis

from .config import GEMINI_API_KEY, REDIS_URL
from .database import save_interview_results
from .prompts import (
    get_analysis_prompt,
    get_system_prompt,
    normalize_lang,
)

logger = logging.getLogger(__name__)

MAX_TURNS = 15
HISTORY_TTL_SECONDS = 60 * 60  # 1 hour
TURN_TTL_SECONDS = 60 * 60
GEMINI_MODEL = "gemini-2.5-flash"

_client = genai.Client(api_key=GEMINI_API_KEY)
redis_client = redis.from_url(REDIS_URL)


def _chat_config(lang: str) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(system_instruction=get_system_prompt(normalize_lang(lang)))


def _analysis_config(lang: str) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=get_analysis_prompt(normalize_lang(lang)),
        response_mime_type="application/json",
    )


def _history_key(session_id: str) -> str:
    return f"hr_interview:{session_id}"


def _turn_key(session_id: str) -> str:
    return f"hr_interview:{session_id}:turns"


class InterviewSummary(NamedTuple):
    verdict: str | None                   # "PASS" | "FAIL" | None on analysis failure
    summary: str | None
    strengths: list[str]
    areas_of_improvement: list[str]
    transcript: str
    turn_count: int


async def get_chat_history(session_id: str) -> list:
    history_json = await redis_client.get(_history_key(session_id))
    if history_json:
        return json.loads(history_json)
    return []


async def save_chat_history(session_id: str, history: list) -> None:
    await redis_client.set(
        _history_key(session_id), json.dumps(history), ex=HISTORY_TTL_SECONDS
    )


async def get_turn_count(session_id: str) -> int:
    raw = await redis_client.get(_turn_key(session_id))
    return int(raw) if raw else 0


async def increment_turn_count(session_id: str) -> int:
    """Atomic increment. Sets TTL on first write."""
    key = _turn_key(session_id)
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, TURN_TTL_SECONDS)
    results = await pipe.execute()
    return int(results[0])


async def reset_session_state(session_id: str) -> None:
    """Called after a session is finalized to free Redis space."""
    await redis_client.delete(_history_key(session_id), _turn_key(session_id))


async def stream_ai_response(
    session_id: str,
    user_message: str,
    lang: str = "en",
) -> AsyncIterator[str]:
    """
    Stream the model's reply for one user turn and persist the updated history.
    """
    history = await get_chat_history(session_id)
    # History persisted as {"role": "user|model", "parts": ["text"]}; convert
    # to google.genai Content/Part objects.
    contents = [
        types.Content(
            role=item.get("role", "user"),
            parts=[types.Part(text=p) for p in (item.get("parts") or [""])],
        )
        for item in history
    ]
    chat = _client.aio.chats.create(
        model=GEMINI_MODEL,
        config=_chat_config(lang),
        history=contents,
    )
    full_ai_response = ""

    try:
        async for chunk in await chat.send_message_stream(user_message):
            text = chunk.text or ""
            full_ai_response += text
            if text:
                yield text

        history.append({"role": "user", "parts": [user_message]})
        history.append({"role": "model", "parts": [full_ai_response]})
        await save_chat_history(session_id, history)
    except Exception:
        logger.exception("Eroare la streaming Gemini pentru session %s.", session_id)
        yield "I'm sorry, I seem to be having some trouble. Could you please repeat that?"


def _build_transcript(history: list) -> str:
    return "\n".join(
        f"{item.get('role', 'unknown')}: {(item.get('parts') or [''])[0]}"
        for item in history
    )


async def analyze_and_save_transcript(
    session_id: str,
    user_id: str,
    lang: str = "en",
) -> InterviewSummary:
    """
    Analyze the full transcript, persist to PostgreSQL, and return a structured
    summary so the caller can publish a Kafka event with the same data.
    """
    history = await get_chat_history(session_id)
    transcript = _build_transcript(history)
    turn_count = await get_turn_count(session_id)

    if not history:
        logger.info("Niciun istoric pentru session %s — sar peste analiză.", session_id)
        return InterviewSummary(
            verdict=None,
            summary=None,
            strengths=[],
            areas_of_improvement=[],
            transcript="",
            turn_count=0,
        )

    verdict: str | None = None
    summary_text: str | None = None
    strengths: list[str] = []
    areas: list[str] = []

    try:
        response = await _client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=transcript,
            config=_analysis_config(lang),
        )
        analysis_result = json.loads(response.text or "{}")
        raw_verdict = str(analysis_result.get("verdict", "")).upper().strip()
        verdict = raw_verdict if raw_verdict in ("PASS", "FAIL") else None
        summary_text = analysis_result.get("summary")
        strengths = list(analysis_result.get("strengths") or [])
        areas = list(analysis_result.get("areas_of_improvement") or [])
    except Exception:
        logger.exception("Analiza post-interview a eșuat pentru session %s.", session_id)

    # Persist a structured feedback JSON so downstream consumers (and the DB)
    # keep the full detail without needing a schema migration. Score column is
    # derived from verdict purely for back-compat: PASS=80, FAIL=40, unknown=NULL.
    derived_score: int | None = (
        80 if verdict == "PASS" else 40 if verdict == "FAIL" else None
    )
    feedback_blob = json.dumps(
        {
            "verdict": verdict,
            "summary": summary_text,
            "strengths": strengths,
            "areas_of_improvement": areas,
        }
    )

    try:
        await save_interview_results(
            session_id, user_id, derived_score, feedback_blob, transcript
        )
    except Exception:
        logger.exception("Salvarea în DB a eșuat pentru session %s.", session_id)

    return InterviewSummary(
        verdict=verdict,
        summary=summary_text,
        strengths=strengths,
        areas_of_improvement=areas,
        transcript=transcript,
        turn_count=turn_count,
    )
