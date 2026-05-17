import asyncio
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from .consumer import consume
from .database import get_db_session, get_job_matches_for_user
from .retry import startup_retry

consumer_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task
    print("Starting Job Match Agent lifespan...")

    # Pornim consumer-ul curat
    consumer_task = asyncio.create_task(consume())

    yield

    # Oprim consumer-ul curat la shutdown
    print("Shutting down Job Match Agent...")
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="Job Match Agent",
    description="Matches scraped jobs with user CVs using vector search and Gemini re-ranking.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/jobs/{user_id}")
async def get_job_matches(user_id: str, session: AsyncSession = Depends(get_db_session)):
    """Retrieves the matched jobs for a user, ordered by match score."""
    matches = await get_job_matches_for_user(session, user_id)

    if not matches:
        raise HTTPException(status_code=404, detail="No job matches found for this user")

    return {"user_id": user_id, "matches": matches, "count": len(matches)}