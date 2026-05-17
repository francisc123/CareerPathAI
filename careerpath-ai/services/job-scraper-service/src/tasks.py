import xxhash
from src.celery_app import celery_app
from src.database import SessionLocal, ScrapedJob
from src.scrapers.linkedin import scrape_linkedin
from src.scrapers.ejobs import scrape_ejobs
# de implementat similar pentru Indeed

@celery_app.task(name="tasks.run_scraping_pipeline")
def run_scraping_pipeline(user_id, skills, seniority, location):
    all_jobs = []

    # 1. Rulăm scraperele (LinkedIn cu Playwright, eJobs cu BS4)
    all_jobs.extend(scrape_linkedin(skills, seniority, location))
    all_jobs.extend(scrape_ejobs(skills))

    db = SessionLocal()
    new_entries = []

    for job_data in all_jobs:
        # Deduplicare: hash pe URL
        url_hash = xxhash.xxh64(job_data['url']).hexdigest()

        exists = db.query(ScrapedJob).filter(
            ScrapedJob.job_hash == url_hash
        ).first()

        if not exists:
            new_job = ScrapedJob(
                job_hash=url_hash,
                user_id=user_id,
                title=job_data['title'],
                company=job_data['company'],
                location=job_data['location'],
                url=job_data['url'],
                source=job_data['source']
            )
            new_entries.append(new_job)

    if new_entries:
        db.bulk_save_objects(new_entries)
        db.commit()
        # TODO: Publish jobs.scraped event to Kafka

    db.close()
    return f"Processed {len(all_jobs)} jobs, inserted {len(new_entries)} new."