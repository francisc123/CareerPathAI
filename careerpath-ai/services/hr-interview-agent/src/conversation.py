import json
import logging
from typing import AsyncIterator, NamedTuple

import google.generativeai as genai
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

genai.configure(api_key=GEMINI_API_KEY)
redis_client = redis.from_url(REDIS_URL)

# Per-language model cache so we don't re-create models on every turn.
_chat_models: dict[str, "genai.GenerativeModel"] = {}
_analysis_models: dict[str, "genai.GenerativeModel"] = {}


def _get_chat_model(lang: str) -> "genai.GenerativeModel":
    lang = normalize_lang(lang)
    if lang not in _chat_models:
        _chat_models[lang] = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=get_system_prompt(lang),
        )
    return _chat_models[lang]


def _get_analysis_model(lang: str) -> "genai.GenerativeModel":
    lang = normalize_lang(lang)
    if lang not in _analysis_models:
        _analysis_models[lang] = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=get_analysis_prompt(lang),
            generation_config={"response_mime_type": "application/json"},
        )
    return _analysis_models[lang]


def _history_key(session_id: str) -> str:
    return f"hr_interview:{session_id}"


def _turn_key(session_id: str) -> str:
    return f"hr_interview:{session_id}:turns"


class InterviewSummary(NamedTuple):
    score: int | None
    feedback: str | None
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
    chat = _get_chat_model(lang).start_chat(history=history)
    full_ai_response = ""

    try:
        response_stream = await chat.send_message_async(user_message, stream=True)
        async for chunk in response_stream:
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
        return InterviewSummary(score=None, feedback=None, transcript="", turn_count=0)

    score: int | None = None
    feedback: str | None = None

    try:
        response = await _get_analysis_model(lang).generate_content_async(transcript)
        analysis_result = json.loads(response.text or "{}")
        score = analysis_result.get("score")
        feedback = analysis_result.get("feedback")
    except Exception:
        logger.exception("Analiza post-interview a eșuat pentru session %s.", session_id)

    try:
        await save_interview_results(session_id, user_id, score, feedback, transcript)
    except Exception:
        logger.exception("Salvarea în DB a eșuat pentru session %s.", session_id)

    return InterviewSummary(
        score=score,
        feedback=feedback,
        transcript=transcript,
        turn_count=turn_count,
    )
