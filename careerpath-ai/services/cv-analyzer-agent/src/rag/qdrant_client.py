import logging
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL)
    return _client


def save_cv_embedding(user_id: str, vector: list[float], payload: dict) -> bool:
    try:
        payload["user_id"] = user_id
        punct = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=payload,
        )
        get_qdrant_client().upsert(collection_name="cv_embeddings", points=[punct])
        logger.info("Vector salvat în Qdrant pentru user_id: %s", user_id)
        return True
    except Exception as e:
        logger.error("Eroare la salvarea în Qdrant pentru %s: %s", user_id, e)
        raise


def search_similar_jobs(query_vector: list[float], limit: int = 5):
    try:
        results = get_qdrant_client().query_points(
            collection_name="job_embeddings",
            query=query_vector,
            limit=limit,
        )
        return results.points
    except Exception as e:
        logger.error("Eroare la căutarea în Qdrant: %s", e)
        return []
