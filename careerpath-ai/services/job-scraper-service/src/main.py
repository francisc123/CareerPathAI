from fastapi import FastAPI

app = FastAPI(title="Job Scraper Service", description="Scrapes jobs from LinkedIn, Indeed, eJobs. (In development)")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "job-scraper-service"}


@app.get("/scrape/{user_id}")
async def trigger_scrape(user_id: str):
    return {"status": "queued", "user_id": user_id, "message": "Scraping triggered (stub — not yet implemented)"}
