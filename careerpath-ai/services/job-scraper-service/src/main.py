import os
import redis
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from tasks import run_scraping_pipeline

app = FastAPI(title="Job Scraper Service")

# Conexiunea la Redis pentru Rate Limiting
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

class ScrapeRequest(BaseModel):
    user_id: str
    skills: List[str]
    seniority: str
    location: str

@app.post("/scrape/trigger")
async def trigger_scrape(request: ScrapeRequest):
    # --- LOGICA DE RATE LIMITING  ---
    today = datetime.date.today().isoformat()
    rate_key = f"scrape_limit:{request.user_id}:{today}"

    current_runs = redis_client.incr(rate_key)
    if current_runs == 1:
        redis_client.expire(rate_key, 86400) # Expira dupa 24h

    if current_runs > 2:
        raise HTTPException(
            status_code=429,
            detail="Limita atinsă: Maxim 2 scanări pe zi per utilizator."
        )

    # --- TRIMITEREA CATRE CELERY ---
    run_scraping_pipeline.delay(
        request.user_id,
        request.skills,
        request.seniority,
        request.location
    )

    return {
        "status": "queued",
        "user_id": request.user_id,
        "run_number": current_runs
    }