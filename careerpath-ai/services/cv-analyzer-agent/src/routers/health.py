import logging
import os

from fastapi import APIRouter

from src.db.cv_repository import get_pool
from src.publishers.cv_analyzed_publisher import get_producer
from src.rag.qdrant_client import get_qdrant_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check() -> dict:
    checks: dict[str, str] = {
        "gemini_api_key": "ok" if os.getenv("GEMINI_API_KEY") else "missing",
        "kafka_producer": "ok" if get_producer() else "not_initialized",
        "db_pool": "ok" if get_pool() else "not_initialized",
    }

    try:
        get_qdrant_client().get_collections()
        checks["qdrant"] = "ok"
    except Exception as e:
        logger.warning("Qdrant health check eșuat: %s", e)
        checks["qdrant"] = "unreachable"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
