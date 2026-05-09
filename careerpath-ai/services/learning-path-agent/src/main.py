from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .consumer import run_consumer_in_background
from .database import get_db_pool, get_learning_path

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
    title="Learning Path Agent",
    description="Generates personalized learning paths based on CV gaps.",
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


@app.get("/learning/{user_id}")
async def get_learning_path_endpoint(user_id: str):
    """Retrieves the generated learning path for a user."""
    if _db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    result = await get_learning_path(_db_pool, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Learning path not found for this user")

    return result


@app.get("/learning/quiz/{module_id}")
async def get_quiz(module_id: str):
    """Retrieves the quiz for a specific learning module. (Not yet implemented)"""
    raise HTTPException(status_code=501, detail="Quiz feature not yet implemented")


@app.post("/learning/quiz/{module_id}/submit")
async def submit_quiz(module_id: str, answers: dict):
    """Submits user answers for a quiz. (Not yet implemented)"""
    raise HTTPException(status_code=501, detail="Quiz feature not yet implemented")
