import asyncio
import json
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from .config import KAFKA_BROKERS, TOPIC_GAPS_IDENTIFIED, TOPIC_LEARNING_PATH_CREATED
from .generator import generate_learning_path_structure
from .database import get_db_pool, save_learning_path

async def process_message(message, db_pool, producer):
    """Processes a single Kafka message."""
    try:
        data = json.loads(message.value.decode("utf-8"))
        user_id = data.get("user_id")
        gaps = data.get("gaps")
        target_role = data.get("target_role")

        if not all([user_id, gaps, target_role]):
            print("Error: Missing required fields in message")
            return

        print(f"📨 Received gap analysis for user: {user_id}")

        # 1. Generate learning path
        path_json_string = await generate_learning_path_structure(gaps, target_role)
        if not path_json_string:
            print(f"Skipping database save and Kafka publish for user {user_id} due to generation failure.")
            return

        path_data = json.loads(path_json_string)

        # 2. Save to database
        await save_learning_path(db_pool, user_id, target_role, path_data)

        # 3. Publish event
        await producer.send_and_wait(
            TOPIC_LEARNING_PATH_CREATED,
            {"user_id": user_id, "status": "created", "title": path_data.get("title")}
        )
        print(f"🏁 Published 'learning.path.created' for user: {user_id}")

    except json.JSONDecodeError:
        print("Error: Could not decode message JSON")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

async def consume():
    """Main consumer loop."""
    db_pool = await get_db_pool()
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    consumer = AIOKafkaConsumer(
        TOPIC_GAPS_IDENTIFIED,
        bootstrap_servers=KAFKA_BROKERS,
        group_id="learning-path-agent-group",
        auto_offset_reset="latest",
    )

    await producer.start()
    await consumer.start()

    print(f"👂 Consumer started on topic '{TOPIC_GAPS_IDENTIFIED}'...")
    try:
        async for message in consumer:
            await process_message(message, db_pool, producer)
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
