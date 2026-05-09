from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from .consumer import run_consumer_in_background
from .database import get_db_pool, get_job_matches_for_user

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
    title="Job Match Agent",
    description="Matches scraped jobs with user CVs using vector search and Gemini re-ranking.",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/jobs/{user_id}")
async def get_job_matches(user_id: str):
    """Retrieves the matched jobs for a user, ordered by match score."""
    if _db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    matches = await get_job_matches_for_user(_db_pool, user_id)
    if not matches:
        raise HTTPException(status_code=404, detail="No job matches found for this user")

    return {"user_id": user_id, "matches": matches, "count": len(matches)}
