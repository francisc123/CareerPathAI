"""
Technical-interview conversation engine.

Each session runs through up to MAX_PROBLEMS problems. The client sends
two kinds of messages over the WebSocket:

  {"type": "chat",            "content": "<text>"}
  {"type": "code_submission", "content": "<source>", "language": "python"}

The engine emits:

  {"type": "problem",     "data": {...}}            # new problem assigned
  {"type": "chat_delta",  "content": "<token>"}     # Gemini stream chunk
  {"type": "chat_done"}                             # end of stream
  {"type": "test_results", "data": {...}}           # Judge0 + evaluation
  {"type": "session_end",  "summary": {...}}        # final score/feedback
  {"type": "error",        "message": "..."}        # graceful failure
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, NamedTuple

import google.generativeai as genai
import redis.asyncio as redis

from .config import GEMINI_API_KEY, REDIS_URL
from .database import save_interview_results
from .integrations.judge0 import TestResult, run_code
from .prompts import (
    get_eval_prompt,
    get_post_prompt,
    get_problem_prompt,
    get_system_prompt,
    normalize_lang,
)

logger = logging.getLogger(__name__)

MAX_PROBLEMS = 2
MAX_HINTS_PER_PROBLEM = 3
HISTORY_TTL_SECONDS = 60 * 60 * 2
SESSION_TTL_SECONDS = 60 * 60 * 2

genai.configure(api_key=GEMINI_API_KEY)


def _model(kind: str, lang: str) -> "genai.GenerativeModel":
    """
    Lazily build per-(kind, lang) Gemini models, cached on the function.
    `kind` is one of: chat, problem, eval, post.
    """
    cache = _model.__dict__.setdefault("_cache", {})
    key = (kind, normalize_lang(lang))
    if key in cache:
        return cache[key]
    if kind == "chat":
        m = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=get_system_prompt(lang),
        )
    elif kind == "problem":
        m = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=get_problem_prompt(lang),
            generation_config={"response_mime_type": "application/json"},
        )
    elif kind == "eval":
        m = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=get_eval_prompt(lang),
            generation_config={"response_mime_type": "application/json"},
        )
    elif kind == "post":
        m = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=get_post_prompt(lang),
            generation_config={"response_mime_type": "application/json"},
        )
    else:
        raise ValueError(f"Unknown model kind: {kind}")
    cache[key] = m
    return m

_redis = redis.from_url(REDIS_URL, decode_responses=True)


def _hist_key(s: str) -> str:
    return f"tech_interview:{s}:history"


def _state_key(s: str) -> str:
    return f"tech_interview:{s}:state"


# ---------- Session state ---------- #


class InterviewSummary(NamedTuple):
    score: int | None
    feedback: str | None
    transcript: str
    problems_attempted: int
    problems_passed: int


async def _load_state(session_id: str) -> dict[str, Any]:
    raw = await _redis.get(_state_key(session_id))
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return {"problems": [], "current_index": -1}


async def _save_state(session_id: str, state: dict[str, Any]) -> None:
    await _redis.set(_state_key(session_id), json.dumps(state), ex=SESSION_TTL_SECONDS)


async def _load_history(session_id: str) -> list[dict]:
    raw = await _redis.get(_hist_key(session_id))
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return []


async def _save_history(session_id: str, history: list[dict]) -> None:
    await _redis.set(_hist_key(session_id), json.dumps(history), ex=HISTORY_TTL_SECONDS)


async def reset_session(session_id: str) -> None:
    await _redis.delete(_hist_key(session_id), _state_key(session_id))


# ---------- Problem selection ---------- #


async def pick_next_problem(
    session_id: str, *, skills: list[str], seniority: str, lang: str = "en"
) -> dict[str, Any] | None:
    """
    Ask Gemini for a problem the user hasn't seen, persist it in state,
    and return it. Returns None on irrecoverable failure.
    """
    state = await _load_state(session_id)
    already = [p.get("title") for p in state.get("problems", [])]
    user_prompt = json.dumps(
        {
            "skills": skills,
            "seniority": seniority,
            "exclude_titles": already,
            "preferred_difficulty": (
                "easy" if seniority.lower() == "junior" else "medium"
            ),
        }
    )

    try:
        response = await _model("problem", lang).generate_content_async(user_prompt)
        problem = json.loads(response.text or "{}")
    except Exception:
        logger.exception("Problem selector failed for session %s.", session_id)
        return None

    if not problem.get("title") or not problem.get("statement"):
        logger.warning("Problem selector returned invalid payload: %s", problem)
        return None

    # Initialize per-problem hint counter
    problem["hints_used"] = 0
    state.setdefault("problems", []).append(problem)
    state["current_index"] = len(state["problems"]) - 1
    state["last_evaluation"] = None
    await _save_state(session_id, state)
    return problem


async def request_hint(session_id: str) -> int:
    """
    Increment hint counter for the current problem. Returns the NEW hint level
    (1, 2, or 3). Returns 0 if no problem or already at max.
    """
    state = await _load_state(session_id)
    idx = state.get("current_index", -1)
    problems = state.get("problems", [])
    if not (0 <= idx < len(problems)):
        return 0
    current_hints = int(problems[idx].get("hints_used", 0))
    if current_hints >= MAX_HINTS_PER_PROBLEM:
        return current_hints
    problems[idx]["hints_used"] = current_hints + 1
    await _save_state(session_id, state)
    return current_hints + 1


async def get_current_hint_level(session_id: str) -> int:
    state = await _load_state(session_id)
    idx = state.get("current_index", -1)
    problems = state.get("problems", [])
    if not (0 <= idx < len(problems)):
        return 0
    return int(problems[idx].get("hints_used", 0))


async def get_current_problem(session_id: str) -> dict[str, Any] | None:
    state = await _load_state(session_id)
    idx = state.get("current_index", -1)
    problems = state.get("problems", [])
    if 0 <= idx < len(problems):
        return problems[idx]
    return None


# ---------- Chat streaming ---------- #


async def stream_ai_reply(
    session_id: str, user_message: str, lang: str = "en"
) -> AsyncIterator[str]:
    """Stream Gemini's response anchored on the current problem + hint level."""
    history = await _load_history(session_id)
    problem = await get_current_problem(session_id)
    hint_level = await get_current_hint_level(session_id)
    problem_anchor = (
        f"\n\n[CURRENT PROBLEM]\n{problem.get('title')}: {problem.get('statement')}"
        f"\n[HINT_LEVEL] {hint_level}"
        if problem
        else ""
    )

    chat = _model("chat", lang).start_chat(history=history)
    full = ""
    try:
        stream = await chat.send_message_async(
            f"{user_message}{problem_anchor}", stream=True
        )
        async for chunk in stream:
            text = chunk.text or ""
            if text:
                full += text
                yield text
    except Exception:
        logger.exception("Gemini stream failed for session %s.", session_id)
        yield "I'm having a technical issue — could you repeat that?"
        return

    history.append({"role": "user", "parts": [user_message]})
    history.append({"role": "model", "parts": [full]})
    await _save_history(session_id, history)


# ---------- Code submission ---------- #


async def grade_submission(
    session_id: str, *, source_code: str, language: str, lang: str = "en"
) -> dict[str, Any]:
    """
    Run the user's code against the reference stdin, then ask Gemini to
    grade it. Persists the evaluation in the session state and history.
    """
    problem = await get_current_problem(session_id)
    if problem is None:
        return {
            "ok": False,
            "error": "No active problem — session may have expired.",
        }

    stdin = problem.get("reference_stdin") or ""
    test_result: TestResult = await run_code(
        source_code=source_code, language=language, stdin=stdin
    )

    judge_payload = {
        "status": test_result.status,
        "stdout": test_result.stdout,
        "stderr": test_result.stderr,
        "compile_output": test_result.compile_output,
        "time_seconds": test_result.time_seconds,
        "memory_kb": test_result.memory_kb,
        "expected_stdout": problem.get("reference_expected_stdout", ""),
        "stdout_matches_expected": (
            test_result.stdout.strip()
            == (problem.get("reference_expected_stdout") or "").strip()
            if test_result.status in ("accepted", "wrong_answer")
            else False
        ),
    }

    evaluation: dict[str, Any] = {
        "correctness": 0,
        "complexity": "n/a",
        "code_quality": 0,
        "passed": False,
        "feedback": "Automated evaluation unavailable.",
    }
    hints_used = int(problem.get("hints_used", 0))
    try:
        eval_input = json.dumps(
            {
                "problem": {
                    "title": problem.get("title"),
                    "statement": problem.get("statement"),
                    "constraints": problem.get("constraints", []),
                },
                "user_code": source_code,
                "language": language,
                "judge0": judge_payload,
                "hints_used": hints_used,
            }
        )
        eval_response = await _model("eval", lang).generate_content_async(eval_input)
        evaluation.update(json.loads(eval_response.text or "{}"))
    except Exception:
        logger.exception("Code eval failed for session %s.", session_id)

    # Persist into history + state
    state = await _load_state(session_id)
    idx = state.get("current_index", -1)
    if 0 <= idx < len(state.get("problems", [])):
        state["problems"][idx]["evaluation"] = evaluation
        state["problems"][idx]["submitted_code"] = source_code
        state["problems"][idx]["submitted_language"] = language
        state["last_evaluation"] = evaluation
    await _save_state(session_id, state)

    history = await _load_history(session_id)
    history.append(
        {
            "role": "user",
            "parts": [f"[CODE SUBMISSION — {language}]\n{source_code}"],
        }
    )
    history.append(
        {
            "role": "model",
            "parts": [f"[EVALUATION] {json.dumps(evaluation)}"],
        }
    )
    await _save_history(session_id, history)

    return {
        "ok": True,
        "judge0": judge_payload,
        "evaluation": evaluation,
    }


async def has_more_problems(session_id: str) -> bool:
    state = await _load_state(session_id)
    return len(state.get("problems", [])) < MAX_PROBLEMS


# ---------- End-of-session analysis ---------- #


def _build_transcript(history: list[dict]) -> str:
    return "\n".join(
        f"{item.get('role', 'unknown')}: {(item.get('parts') or [''])[0]}"
        for item in history
    )


async def analyze_and_save(
    session_id: str, user_id: str, lang: str = "en"
) -> InterviewSummary:
    history = await _load_history(session_id)
    state = await _load_state(session_id)
    transcript = _build_transcript(history)

    problems = state.get("problems", [])
    problems_attempted = len(problems)
    problems_passed = sum(1 for p in problems if (p.get("evaluation") or {}).get("passed"))

    if not history:
        return InterviewSummary(None, None, "", 0, 0)

    score: int | None = None
    feedback: str | None = None
    try:
        response = await _model("post", lang).generate_content_async(transcript)
        analysis = json.loads(response.text or "{}")
        score = analysis.get("score")
        feedback = analysis.get("feedback")
    except Exception:
        logger.exception("Post-interview analysis failed for %s.", session_id)

    try:
        await save_interview_results(session_id, user_id, score, feedback, transcript)
    except Exception:
        logger.exception("Save interview results failed for %s.", session_id)

    return InterviewSummary(
        score=score,
        feedback=feedback,
        transcript=transcript,
        problems_attempted=problems_attempted,
        problems_passed=problems_passed,
    )
