import json
import logging
import os
from typing import Iterable

import asyncpg

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
_pool: asyncpg.Pool | None = None


# `cv_uploads` is owned by cv-service which only creates a minimal subset of
# columns via SQLAlchemy. We additively ensure the analysis-result columns
# exist so the analyzer can persist its output without stepping on cv-service.
_CV_UPLOADS_ALTER_STATEMENTS: tuple[str, ...] = (
    "ALTER TABLE cv_uploads ADD COLUMN IF NOT EXISTS score INT",
    "ALTER TABLE cv_uploads ADD COLUMN IF NOT EXISTS skills JSONB",
    "ALTER TABLE cv_uploads ADD COLUMN IF NOT EXISTS gaps JSONB",
    "ALTER TABLE cv_uploads ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMPTZ",
)


async def init_db_pool() -> None:
    global _pool
    if not DATABASE_URL:
        logger.warning("DATABASE_URL nesetat — salvarea în PostgreSQL este dezactivată.")
        return
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    logger.info("Pool PostgreSQL inițializat.")
    await _ensure_cv_uploads_columns(_pool)


async def close_db_pool() -> None:
    if _pool:
        await _pool.close()
        logger.info("Pool PostgreSQL închis.")


def get_pool() -> asyncpg.Pool | None:
    return _pool


async def _ensure_cv_uploads_columns(pool: asyncpg.Pool) -> None:
    """
    Best-effort schema migration. Safe to run repeatedly.
    If `cv_uploads` does not exist yet (cv-service not started), we swallow
    the error — the next analyzer restart will pick it up.
    """
    try:
        async with pool.acquire() as conn:
            for stmt in _CV_UPLOADS_ALTER_STATEMENTS:
                await conn.execute(stmt)
        logger.info("Schema `cv_uploads` aliniată (score/skills/gaps/analyzed_at).")
    except asyncpg.UndefinedTableError:
        logger.warning(
            "Tabela `cv_uploads` nu există încă — sar peste ALTER. "
            "Va fi reîncercat la următoarea pornire."
        )
    except Exception:
        logger.exception("Eroare la alinierea schemei `cv_uploads` (continui oricum).")


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


async def update_cv_upload_result(
    job_id: str,
    status: str,
    score: int | None = None,
    skills: Iterable[str] | None = None,
    gaps: Iterable[str] | None = None,
) -> bool:
    """
    Update the cv_uploads row owned by cv-service with the analyzer's result so
    that `GET /api/cv/status/{job_id}` returns the final state even if SSE
    notifications drop. Returns True if a row was updated.

    DB failures are caught and logged — Kafka remains the source of truth.
    """
    if not _pool:
        logger.warning("PostgreSQL indisponibil — skip update cv_uploads pentru job %s.", job_id)
        return False

    skills_payload = json.dumps(list(skills) if skills is not None else None)
    gaps_payload = json.dumps(list(gaps) if gaps is not None else None)

    query = """
    UPDATE cv_uploads
       SET status      = $2,
           score       = COALESCE($3, score),
           skills      = COALESCE($4::jsonb, skills),
           gaps        = COALESCE($5::jsonb, gaps),
           analyzed_at = NOW()
     WHERE id = $1
    """
    try:
        async with _pool.acquire() as conn:
            result = await conn.execute(
                query, job_id, status, score, skills_payload, gaps_payload
            )
        # `result` looks like "UPDATE 1"
        updated = result.endswith(" 0") is False
        if updated:
            logger.info(
                "cv_uploads actualizat (job_id=%s, status=%s, score=%s).",
                job_id,
                status,
                score,
            )
        else:
            logger.warning(
                "Niciun rând cv_uploads găsit pentru job_id=%s — sar peste update.",
                job_id,
            )
        return updated
    except asyncpg.UndefinedColumnError:
        logger.exception(
            "Coloane lipsă în cv_uploads — re-rulez ALTER și reîncerc o singură dată."
        )
        await _ensure_cv_uploads_columns(_pool)
        try:
            async with _pool.acquire() as conn:
                await conn.execute(
                    query, job_id, status, score, skills_payload, gaps_payload
                )
            return True
        except Exception:
            logger.exception("Retry update cv_uploads eșuat pentru job_id=%s.", job_id)
            return False
    except Exception:
        logger.exception(
            "Eroare la update cv_uploads (job_id=%s). Continui — Kafka rămâne sursa de adevăr.",
            job_id,
        )
        return False
