import logging
import os
import asyncpg

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
_pool: asyncpg.Pool | None = None


async def init_db_pool() -> None:
    global _pool
    if not DATABASE_URL:
        logger.warning("DATABASE_URL nesetat — salvarea în PostgreSQL este dezactivată.")
        return
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    logger.info("Pool PostgreSQL inițializat.")


async def close_db_pool() -> None:
    if _pool:
        await _pool.close()
        logger.info("Pool PostgreSQL închis.")


def get_pool() -> asyncpg.Pool | None:
    return _pool


async def save_cv_analysis(user_id: str, score: int, seniority: str, target_role: str) -> None:
    if not _pool:
        logger.warning("PostgreSQL indisponibil — skip save pentru user %s.", user_id)
        return
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO cv_analysis_results (user_id, score, seniority, target_role, analyzed_at)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (user_id) DO UPDATE
              SET score        = EXCLUDED.score,
                  seniority    = EXCLUDED.seniority,
                  target_role  = EXCLUDED.target_role,
                  analyzed_at  = NOW()
            """,
            user_id,
            score,
            seniority,
            target_role,
        )
        logger.info("Analiză salvată în PostgreSQL pentru user: %s", user_id)
