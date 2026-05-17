import os
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

# Conexiunea asincronă la Qdrant
client = AsyncQdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
COLLECTION_NAME = "job_embeddings"

async def upsert_job_embeddings(jobs: list[dict], embeddings: list[list[float]]):
    """Inserează joburile scrapate și vectorii lor în Qdrant (Pasul 3 din task)."""
    points = [
        models.PointStruct(
            id=job['id'],
            vector=emb,
            payload={
                "scrape_run_id": job['scrape_run_id'],
                "seniority": job['seniority'],
                "title": job['title']
            }
        )
        for job, emb in zip(jobs, embeddings)
    ]
    await client.upsert(collection_name=COLLECTION_NAME, points=points)

async def get_cv_details(user_id: str, qdrant_client: AsyncQdrantClient = None):
    """Extrage vectorul CV-ului și nivelul de seniority pentru utilizator (Pasul 4)."""
    q_client = qdrant_client or client
    result = await q_client.retrieve(
        collection_name="cv_embeddings",
        ids=[user_id],
        with_vectors=True
    )
    if result:
        # Extragem vectorul și seniority din payload-ul salvat la CP-021
        vector = result[0].vector
        seniority = result[0].payload.get("seniority", "junior")
        return vector, seniority
    return None, "junior"

async def find_similar_jobs(cv_embedding: list[float], user_seniority: str, qdrant_client: AsyncQdrantClient = None, limit: int = 50):
    """Caută cele mai apropiate 50 de joburi bazat pe similaritatea cosinus și filtru de seniority (Pasul 5)."""
    q_client = qdrant_client or client
    return await q_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=cv_embedding,
        limit=limit,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="seniority",
                    match=models.MatchValue(value=user_seniority)
                )
            ]
        )
    )