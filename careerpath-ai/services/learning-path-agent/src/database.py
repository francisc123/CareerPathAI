import asyncpg
import json
import logging
from typing import Any
from .config import DATABASE_URL

logger = logging.getLogger(__name__)

async def get_db_pool():
    """Creates and returns a database connection pool."""
    return await asyncpg.create_pool(DATABASE_URL)

async def save_learning_path(pool, user_id: str, target_role: str, path_data: dict):
    """
    Saves the generated learning path to the PostgreSQL database.
    """
    # The `learning_paths` table is assumed to exist.
    # It should have columns like: user_id, target_role, title, estimated_weeks, plan_data (JSONB)
    query = """
    INSERT INTO learning_paths (user_id, target_role, title, estimated_weeks, plan_data, created_at)
    VALUES ($1, $2, $3, $4, $5, NOW())
    ON CONFLICT (user_id) DO UPDATE SET
        target_role = EXCLUDED.target_role,
        title = EXCLUDED.title,
        estimated_weeks = EXCLUDED.estimated_weeks,
        plan_data = EXCLUDED.plan_data,
        created_at = NOW();
    """
    try:
        async with pool.acquire() as connection:
            await connection.execute(
                query,
                user_id,
                target_role,
                path_data.get("title"),
                path_data.get("estimated_weeks"),
                json.dumps(path_data.get("weekly_plan"))
            )
        print(f"💾 Learning path for user {user_id} saved to database.")
    except Exception as e:
        print(f"❌ Error saving learning path to database: {e}")

async def get_learning_path(pool, user_id: str) -> dict | None:
    """Retrieves the learning path for a user from the database."""
    query = """
    SELECT user_id, target_role, title, estimated_weeks, plan_data, created_at
    FROM learning_paths
    WHERE user_id = $1;
    """
    try:
        async with pool.acquire() as connection:
            row = await connection.fetchrow(query, user_id)
            if row is None:
                return None
            return dict(row)
    except Exception as e:
        print(f"Error retrieving learning path: {e}")
        return None


def parse_module_id(module_id: str) -> tuple[str, int, int]:
    """
    module_id format: {user_id}__{week_num}__{module_idx}
    user_id may itself contain underscores, so we split on the LAST two `__`.
    Raises ValueError if malformed.
    """
    parts = module_id.rsplit("__", 2)
    if len(parts) != 3:
        raise ValueError(f"Malformed module_id: {module_id!r}")
    user_id, week_str, module_idx_str = parts
    if not user_id:
        raise ValueError(f"Empty user_id in module_id: {module_id!r}")
    try:
        return user_id, int(week_str), int(module_idx_str)
    except ValueError as exc:
        raise ValueError(f"Non-integer week/module_idx in module_id: {module_id!r}") from exc


def find_module_in_path(plan_data: Any, week: int, module_idx: int) -> dict | None:
    """
    Locate a module inside plan_data (the JSONB weekly_plan array).
    plan_data may arrive as a JSON string (from asyncpg JSONB) or as a list/dict.
    Returns the module dict or None if not found.
    """
    if isinstance(plan_data, (str, bytes, bytearray)):
        try:
            plan_data = json.loads(plan_data)
        except (json.JSONDecodeError, TypeError):
            return None

    if not isinstance(plan_data, list):
        return None

    for week_obj in plan_data:
        if not isinstance(week_obj, dict):
            continue
        if week_obj.get("week") != week:
            continue
        modules = week_obj.get("modules") or []
        if 0 <= module_idx < len(modules):
            module = modules[module_idx]
            if isinstance(module, dict):
                return module
        return None
    return None


async def get_quiz_for_module(pool, module_id: str) -> dict | None:
    """
    Returns {"module_title": str, "quiz": [{question, options, correct_index}]}
    or None if the user / week / module / quiz does not exist.
    """
    user_id, week, module_idx = parse_module_id(module_id)
    query = "SELECT plan_data FROM learning_paths WHERE user_id = $1;"
    async with pool.acquire() as connection:
        row = await connection.fetchrow(query, user_id)
    if row is None:
        return None

    module = find_module_in_path(row["plan_data"], week, module_idx)
    if module is None:
        return None

    quiz = module.get("quiz")
    if not isinstance(quiz, list) or not quiz:
        return None

    return {
        "module_title": module.get("module_title", ""),
        "quiz": quiz,
    }


async def save_quiz_attempt(
    pool,
    user_id: str,
    module_id: str,
    answers: list[int],
    score: int,
) -> int:
    """Persists a quiz attempt and returns the new row id."""
    query = """
    INSERT INTO quiz_attempts (user_id, module_id, answers, score)
    VALUES ($1, $2, $3::jsonb, $4)
    RETURNING id;
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(
            query, user_id, module_id, json.dumps(answers), score
        )


async def get_user_difficulty_signal(pool, user_id: str) -> dict:
    """
    Aggregates the user's recent quiz performance into a difficulty hint the
    learning-path generator can use to calibrate the next plan.

    Returns:
      {"attempts": int, "avg_score": float | None, "hint": "easier"|"steady"|"harder"}

    Rules:
      - 0 attempts → "steady" (no signal yet)
      - avg < 60 over last 5 → "easier"
      - avg > 90 over last 5 → "harder"
      - otherwise → "steady"
    """
    query = """
    SELECT score
    FROM quiz_attempts
    WHERE user_id = $1
    ORDER BY created_at DESC
    LIMIT 5;
    """
    try:
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, user_id)
    except Exception:
        logger.exception("Failed to read quiz history for %s.", user_id)
        return {"attempts": 0, "avg_score": None, "hint": "steady"}

    scores = [r["score"] for r in rows if r["score"] is not None]
    if not scores:
        return {"attempts": 0, "avg_score": None, "hint": "steady"}

    avg = sum(scores) / len(scores)
    if avg < 60:
        hint = "easier"
    elif avg > 90:
        hint = "harder"
    else:
        hint = "steady"
    return {"attempts": len(scores), "avg_score": round(avg, 1), "hint": hint}

