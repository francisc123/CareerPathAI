"""
Asyncpg helper to update the `profiles.final_score` column after the user has
completed every stage of the workflow.
"""

from __future__ import annotations

import logging
import os

import asyncpg

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not set — profile updates disabled.")
        return
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=3)


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def update_final_score(user_id: str, final_score: int) -> None:
    """
    Best-effort. Adds the `final_score` column on first use so we don't depend
    on Francisc's schema being up to date.
    """
    if _pool is None:
        logger.warning("Pool not initialized — skip final_score for %s.", user_id)
        return
    try:
        async with _pool.acquire() as conn:
            await conn.execute(
                "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS final_score INT"
            )
            result = await conn.execute(
                "UPDATE profiles SET final_score = $2 WHERE user_id = $1",
                user_id,
                final_score,
            )
            if result.endswith(" 0"):
                logger.info(
                    "No profile row for user %s — skipping final_score update.",
                    user_id,
                )
            else:
                logger.info(
                    "profiles.final_score=%d updated for user %s.",
                    final_score,
                    user_id,
                )
    except asyncpg.UndefinedTableError:
        logger.warning("Table `profiles` not found — skip final_score for %s.", user_id)
    except Exception:
        logger.exception("Failed to update profiles.final_score for %s.", user_id)
