import logging
import sys

# Configure root logger so consumer.py / generator.py / database.py log lines
# actually reach stdout (uvicorn only configures its own loggers).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
    force=True,
)

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import List, Optional
from .consumer import run_consumer_in_background
from .database import (
    get_db_pool,
    get_learning_path,
    get_quiz_for_module,
    get_user_difficulty_signal,
    parse_module_id,
    save_learning_path,
    save_quiz_attempt,
)
from .generator import generate_learning_path_structure
from .retry import startup_retry  # noqa: F401  - utility decorator available to wrap startup tasks

logger = logging.getLogger(__name__)

_db_pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_pool
    _db_pool = await get_db_pool()
    run_consumer_in_background()
    yield
    if _db_pool:
        await _db_pool.close()


app = FastAPI(
    title="Learning Path Agent",
    description="Generates personalized learning paths based on CV gaps.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------- Pydantic models for the public quiz API ---------- #

class QuizQuestionPublic(BaseModel):
    """Quiz question as returned to the client — `correct_index` stripped."""
    question: str
    options: List[str]


class QuizResponse(BaseModel):
    module_id: str
    module_title: str
    questions: List[QuizQuestionPublic]


class QuizSubmission(BaseModel):
    answers: List[int] = Field(
        ...,
        description="One option index (0-based) per question, in question order.",
    )


class QuizResultItem(BaseModel):
    correct: bool
    correct_index: int


class QuizSubmissionResult(BaseModel):
    module_id: str
    attempt_id: int
    score: int = Field(..., description="Percentage 0-100")
    correct: int
    total: int
    results: List[QuizResultItem]


# ---------- Endpoints ---------- #


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/learning/{user_id}")
async def get_learning_path_endpoint(user_id: str):
    """Retrieves the generated learning path for a user."""
    if _db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    result = await get_learning_path(_db_pool, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Learning path not found for this user")

    return result


class RegenerateRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    target_role: str = Field(..., min_length=1)
    # Optional: frontend can pass the gaps it cached from the CV analysis so the
    # new curriculum still attacks the same weaknesses. Empty → Gemini builds a
    # full curriculum for the role from scratch.
    gaps: Optional[List[str]] = None


@app.post("/learning/regenerate")
async def regenerate_learning_path(req: RegenerateRequest):
    """
    Regenerates the learning path for a user with a new target_role.
    Triggered when the user changes their Target Role in the dashboard.
    Upserts on user_id, so the old path is replaced.
    """
    if _db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    target_role = req.target_role.strip()
    if not target_role:
        raise HTTPException(status_code=400, detail="target_role is required")

    gaps = [g.strip() for g in (req.gaps or []) if g and g.strip()]
    difficulty = await get_user_difficulty_signal(_db_pool, req.user_id)

    logger.info(
        "Regenerating learning path for user=%s target_role=%s gaps=%d",
        req.user_id, target_role, len(gaps),
    )

    path_json_string = await generate_learning_path_structure(
        gaps, target_role, difficulty_hint=difficulty.get("hint"),
    )
    if not path_json_string:
        raise HTTPException(status_code=502, detail="Failed to generate learning path")

    path_data = json.loads(path_json_string)
    await save_learning_path(_db_pool, req.user_id, target_role, path_data)

    saved = await get_learning_path(_db_pool, req.user_id)
    if saved is None:
        raise HTTPException(status_code=500, detail="Failed to persist learning path")
    return saved


@app.get("/learning/quiz/{module_id}", response_model=QuizResponse)
async def get_quiz(module_id: str):
    """
    Returns the quiz for a module without the `correct_index` field
    (so the client cannot read the answers).
    `module_id` format: `{user_id}__{week}__{module_idx}`.
    """
    if _db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        parse_module_id(module_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    quiz_data = await get_quiz_for_module(_db_pool, module_id)
    if quiz_data is None:
        raise HTTPException(status_code=404, detail="Quiz not found for this module")

    public_questions = [
        QuizQuestionPublic(question=q["question"], options=q["options"])
        for q in quiz_data["quiz"]
    ]
    return QuizResponse(
        module_id=module_id,
        module_title=quiz_data["module_title"],
        questions=public_questions,
    )


@app.post("/learning/quiz/{module_id}/submit", response_model=QuizSubmissionResult)
async def submit_quiz(module_id: str, submission: QuizSubmission):
    """
    Scores the user's quiz submission, persists it, and returns per-question feedback.
    """
    if _db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        user_id, _, _ = parse_module_id(module_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    quiz_data = await get_quiz_for_module(_db_pool, module_id)
    if quiz_data is None:
        raise HTTPException(status_code=404, detail="Quiz not found for this module")

    quiz = quiz_data["quiz"]
    if len(submission.answers) != len(quiz):
        raise HTTPException(
            status_code=400,
            detail=f"Expected {len(quiz)} answers, got {len(submission.answers)}",
        )

    results: List[QuizResultItem] = []
    correct_count = 0
    for question, user_answer in zip(quiz, submission.answers):
        correct_index = int(question.get("correct_index", -1))
        is_correct = user_answer == correct_index
        if is_correct:
            correct_count += 1
        results.append(QuizResultItem(correct=is_correct, correct_index=correct_index))

    total = len(quiz)
    score_pct = round(100 * correct_count / total) if total else 0

    try:
        attempt_id = await save_quiz_attempt(
            _db_pool, user_id, module_id, submission.answers, score_pct
        )
    except Exception:
        logger.exception("Failed to persist quiz attempt for %s", module_id)
        raise HTTPException(status_code=500, detail="Could not save quiz attempt")

    return QuizSubmissionResult(
        module_id=module_id,
        attempt_id=attempt_id,
        score=score_pct,
        correct=correct_count,
        total=total,
        results=results,
    )
