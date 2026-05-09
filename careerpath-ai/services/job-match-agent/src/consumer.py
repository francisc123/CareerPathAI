import asyncio
import json
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from qdrant_client import AsyncQdrantClient
from .config import KAFKA_BROKERS, TOPIC_JOBS_SCRAPED, TOPIC_JOBS_MATCHED, QDRANT_URL
from .matcher import find_and_match_jobs
from .database import get_db_pool, save_job_matches

async def process_message(message, db_pool, qdrant_client, producer):
    """Processes a single Kafka message from the job scraper."""
    try:
        data = json.loads(message.value.decode("utf-8"))
        user_id = data.get("user_id")
        cv_text = data.get("cv_text") # Assuming scraper passes this through

        if not all([user_id, cv_text]):
            print("Error: Missing user_id or cv_text in message")
            return

        print(f"📨 Received scraped jobs for user: {user_id}")

        # 1. Find and match jobs
        matched_jobs = await find_and_match_jobs(user_id, cv_text, qdrant_client)
        if not matched_jobs:
            print(f"No job matches found for user {user_id}. Process finished.")
            return

        # 2. Save to database
        await save_job_matches(db_pool, user_id, matched_jobs)

        # 3. Publish event
        await producer.send_and_wait(
            TOPIC_JOBS_MATCHED,
            {"user_id": user_id, "status": "completed", "match_count": len(matched_jobs)}
        )
        print(f"🏁 Published 'jobs.matched' for user: {user_id}")

    except Exception as e:
        print(f"An unexpected error occurred in consumer: {e}")

async def consume():
    """Main consumer loop."""
    db_pool = await get_db_pool()
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

    print(f"👂 Consumer started on topic '{TOPIC_JOBS_SCRAPED}'...")
    try:
        async for message in consumer:
            await process_message(message, db_pool, qdrant_client, producer)
    finally:
        await consumer.stop()
        await producer.stop()
        await db_pool.close()
        print("🛑 Consumer and connections stopped.")

def run_consumer_in_background():
    """Runs the Kafka consumer in a background asyncio task."""
    print("🚀 Starting background Kafka consumer...")
    loop = asyncio.get_event_loop()
    loop.create_task(consume())

