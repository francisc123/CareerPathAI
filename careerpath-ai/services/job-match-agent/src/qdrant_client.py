import os
from qdrant_client import AsyncQdrantClient, models
from google import genai
from .config import QDRANT_URL, CV_COLLECTION_NAME, JOB_COLLECTION_NAME, GEMINI_API_KEY, EMBEDDING_MODEL


def get_gemini_client() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)


async def get_cv_details(user_id: str, qdrant: AsyncQdrantClient):
    """Retrieves a user's CV embedding vector and seniority from Qdrant."""
    points = await qdrant.retrieve(
        collection_name=CV_COLLECTION_NAME,
        ids=[user_id],
        with_vectors=True,
        with_payload=True
    )
    if not points:
        return None, None

    vector = points[0].vector
    seniority = points[0].payload.get("seniority")
    return vector, seniority


async def find_similar_jobs(cv_vector: list[float], seniority: str, qdrant: AsyncQdrantClient, limit: int = 50):
    """Finds similar jobs in Qdrant, filtering by seniority."""
    seniority_filter_map = {
        "Junior": ["Junior", "Entry-level"],
        "Mid-level": ["Mid-level", "Intermediate"],
        "Senior": ["Senior", "Lead", "Principal"]
    }

    filter_conditions = []
    if seniority and seniority in seniority_filter_map:
        filter_conditions.append(
            models.FieldCondition(
                key="seniority",
                match=models.MatchAny(any=seniority_filter_map[seniority])
            )
        )

    search_result = await qdrant.search(
        collection_name=JOB_COLLECTION_NAME,
        query_vector=cv_vector,
        query_filter=models.Filter(must=filter_conditions) if filter_conditions else None,
        limit=limit,
        with_payload=True
    )
    return search_result


def get_embedding_for_text(text: str) -> list[float]:
    """Generates a Gemini embedding for text (dim=3072, consistent with cv-analyzer-agent)."""
    response = get_gemini_client().models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return response.embeddings[0].values
