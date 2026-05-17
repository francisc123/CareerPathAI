import asyncio
import json
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from qdrant_client import AsyncQdrantClient
from .config import KAFKA_BROKERS, TOPIC_JOBS_SCRAPED, TOPIC_JOBS_MATCHED, QDRANT_URL
from .matcher import find_and_match_jobs, generate_embeddings
from .database import AsyncSessionLocal, save_job_matches, get_jobs_by_scrape_run
from .qdrant_service import upsert_job_embeddings

async def process_message(message, qdrant_client, producer):
    """Processes a single Kafka message from the job scraper."""
    try:
        data = json.loads(message.value.decode("utf-8"))
        user_id = data.get("user_id")
        cv_text = data.get("cv_text")
        scrape_run_id = data.get("scrape_run_id")

        if not all([user_id, cv_text, scrape_run_id]):
            print("Error: Missing user_id, cv_text, or scrape_run_id in message")
            return

        print(f"Received scraped jobs event for user: {user_id}, run_id: {scrape_run_id}")

        async with AsyncSessionLocal() as session:
            # 1. Fetch all scraped jobs for scrape_run_id from PostgreSQL
            scraped_jobs = await get_jobs_by_scrape_run(session, scrape_run_id)
            if not scraped_jobs:
                print(f"No scraped jobs found for run_id {scrape_run_id}. Process finished.")
                return

            print(f"Extracted {len(scraped_jobs)} jobs from database.")

            # Formatăm joburile pentru AI și Qdrant
            jobs_for_embedding = [{
                "id": job.id,
                "scrape_run_id": job.scrape_run_id,
                "title": job.title,
                "seniority": job.seniority,
                "description": job.description
            } for job in scraped_jobs]

            # 2. Generate embeddings for each job description
            print("Generating embeddings for scraped jobs...")
            job_descriptions = [j["description"] for j in jobs_for_embedding]
            embeddings = await generate_embeddings(job_descriptions)

            if not embeddings:
                print("Error: Failed to generate embeddings.")
                return

            # 3. Upsert all job embeddings into Qdrant
            print("Upserting job embeddings to Qdrant...")
            await upsert_job_embeddings(jobs_for_embedding, embeddings)

            # 4, 5, 6, 7. Retrieve CV, Search Vector, Rerank, Generate Cover Letters
            print("Starting vector search and LLM reranking...")
            matched_jobs = await find_and_match_jobs(user_id, cv_text, qdrant_client)
            if not matched_jobs:
                print(f"No job matches found for user {user_id}. Process finished.")
                return

            # 8. Bulk insert into PostgreSQL job_matches
            print("Saving top job matches to database...")
            await save_job_matches(session, user_id, matched_jobs)

        # 9. Publish jobs.matched event
        await producer.send_and_wait(
            TOPIC_JOBS_MATCHED,
            {"user_id": user_id, "status": "completed", "match_count": len(matched_jobs)}
        )
        print(f"Published 'jobs.matched' event for user: {user_id}")

    except Exception as e:
        print(f"An unexpected error occurred in consumer: {e}")

async def consume():
    """Main consumer loop."""
    qdrant_client = AsyncQdrantClient(url=QDRANT_URL)
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    consumer = AIOKafkaConsumer(
        TOPIC_JOBS_SCRAPED,
        bootstrap_servers=KAFKA_BROKERS,
        group_id="job-match-agent-group",
        auto_offset_reset="latest",
    )

    await producer.start()
    await consumer.start()

    print(f"Consumer started on topic '{TOPIC_JOBS_SCRAPED}'...")
    try:
        async for message in consumer:
            await process_message(message, qdrant_client, producer)
    finally:
        await consumer.stop()
        await producer.stop()
        print("Consumer and connections stopped.")

def run_consumer_in_background():
    """Runs the Kafka consumer in a background asyncio task."""
    print("Starting background Kafka consumer...")
    loop = asyncio.get_event_loop()
    loop.create_task(consume())