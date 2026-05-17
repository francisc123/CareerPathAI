import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from .config import KAFKA_BROKERS, TOPIC_GAPS_IDENTIFIED, TOPIC_LEARNING_PATH_CREATED
from .generator import generate_learning_path_structure
from .database import get_db_pool, save_learning_path

logger = logging.getLogger(__name__)

async def process_message(message, db_pool, producer):
    """Processes a single Kafka message safely without blocking heartbeats."""
    try:
        payload = message.value.decode("utf-8")
        data = json.loads(payload)

        # Suport flexibil pentru identificatori
        user_id = data.get("user_id") or data.get("userId")
        target_role = data.get("target_role") or data.get("targetRole") or "Software Developer Internship"

        # Extragere robustă a skill gaps-urilor
        gaps = None
        possible_gap_keys = ["gaps", "skill_gaps", "skillGaps", "gaps_identified", "missing_skills"]

        for key in possible_gap_keys:
            val = data.get(key)
            if val and isinstance(val, list) and len(val) > 0:
                gaps = val
                break

        if not gaps:
            print("⚠️ Warning: No explicit gaps found in payload. Applying default tracking gaps.")
            gaps = ["REST APIs", "Microservices Architecture", "PostgreSQL Databases and SQL Optimization"]

        if not user_id:
            print("❌ Error: Missing critical user_id field in message.")
            return

        print(f"📨 Received gap analysis for user: {user_id}. Starting non-blocking AI generation...")

        # Rulăm generarea structurii într-un thread separat pentru a nu bloca loop-ul principal de heartbeat-uri
        path_json_string = await asyncio.to_thread(
            lambda: asyncio.run(generate_learning_path_structure(gaps, target_role))
        )

        if not path_json_string:
            print(f"Skipping database save for user {user_id} due to generation failure.")
            return

        path_data = json.loads(path_json_string)

        # 2. Salvare în baza de date
        await save_learning_path(db_pool, user_id, target_role, path_data)

        # 3. Trimitere eveniment de confirmare
        event_payload = {
            "user_id": user_id,
            "status": "created",
            "title": path_data.get("title")
        }

        await producer.send_and_wait(TOPIC_LEARNING_PATH_CREATED, event_payload)
        print(f"🏁 Published 'learning.path.created' for user: {user_id}")

    except json.JSONDecodeError:
        print("Error: Could not decode message JSON")
    except Exception as e:
        print(f"An unexpected error occurred in process_message: {e}")

async def consume():
    """Main consumer loop with optimized timeout session configuration."""
    db_pool = await get_db_pool()
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    # Configurație robustă: mărim timpii de sesiune pentru a tolera latențele API-ului Gemini
    consumer = AIOKafkaConsumer(
        TOPIC_GAPS_IDENTIFIED,
        bootstrap_servers=KAFKA_BROKERS,
        group_id="learning-path-agent-group-prod", # Schimbăm grupul pentru un reset curat
        auto_offset_reset="latest",                # Ignoră istoricul, citește doar evenimentele noi
        session_timeout_ms=60000,
        max_poll_interval_ms=300000,
        heartbeat_interval_ms=10000
    )

    await producer.start()
    await consumer.start()

    print(f"👂 Consumer started on topic '{TOPIC_GAPS_IDENTIFIED}'...")
    try:
        async for message in consumer:
            await process_message(message, db_pool, producer)
    except Exception as e:
        print(f"Exception in consumer loop: {e}")
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