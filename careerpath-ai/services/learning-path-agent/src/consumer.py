import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

from .config import (
    KAFKA_BROKERS,
    TOPIC_GAPS_IDENTIFIED,
    TOPIC_GAPS_IDENTIFIED_DLQ,
    TOPIC_LEARNING_PATH_CREATED,
)
from .database import get_db_pool, get_user_difficulty_signal, save_learning_path
from .generator import generate_learning_path_structure

logger = logging.getLogger(__name__)


async def process_message(message, db_pool, producer, dlq_producer) -> None:
    """Process a single `gaps.identified` message."""
    raw_value = message.value
    try:
        data = json.loads(raw_value.decode("utf-8"))
    except json.JSONDecodeError:
        logger.exception("Could not decode message JSON — sending raw bytes to DLQ.")
        await dlq_producer.send_and_wait(TOPIC_GAPS_IDENTIFIED_DLQ, raw_value)
        return

    user_id = data.get("user_id")
    gaps = data.get("gaps")
    target_role = data.get("target_role")

    if not all([user_id, gaps, target_role]):
        logger.warning("Missing required fields in gaps.identified payload — DLQ.")
        await dlq_producer.send_and_wait(
            TOPIC_GAPS_IDENTIFIED_DLQ,
            json.dumps({"reason": "missing_fields", "payload": data}).encode("utf-8"),
        )
        return

    logger.info("Received gap analysis for user: %s", user_id)

    try:
        difficulty = await get_user_difficulty_signal(db_pool, user_id)
        path_json_string = await generate_learning_path_structure(
            gaps, target_role, difficulty_hint=difficulty.get("hint"),
        )
        if not path_json_string:
            logger.warning(
                "Learning path generation returned empty for %s — sending to DLQ.",
                user_id,
            )
            await dlq_producer.send_and_wait(
                TOPIC_GAPS_IDENTIFIED_DLQ,
                json.dumps({"reason": "generation_failed", "payload": data}).encode("utf-8"),
            )
            return

        path_data = json.loads(path_json_string)

        await save_learning_path(db_pool, user_id, target_role, path_data)

        await producer.send_and_wait(
            TOPIC_LEARNING_PATH_CREATED,
            json.dumps(
                {
                    "user_id": user_id,
                    "status": "created",
                    "title": path_data.get("title"),
                }
            ).encode("utf-8"),
        )
        logger.info("Published 'learning.path.created' for user: %s", user_id)

    except Exception as exc:
        logger.exception("Unhandled error processing %s — DLQ.", user_id)
        await dlq_producer.send_and_wait(
            TOPIC_GAPS_IDENTIFIED_DLQ,
            json.dumps(
                {"reason": "exception", "error": str(exc), "payload": data}
            ).encode("utf-8"),
        )


async def consume() -> None:
    """Main consumer loop with separate DLQ producer."""
    db_pool = await get_db_pool()
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    dlq_producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    consumer = AIOKafkaConsumer(
        TOPIC_GAPS_IDENTIFIED,
        bootstrap_servers=KAFKA_BROKERS,
        group_id="learning-path-agent-group",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    await producer.start()
    await dlq_producer.start()
    await consumer.start()

    logger.info("Consumer started on topic '%s'.", TOPIC_GAPS_IDENTIFIED)
    try:
        async for message in consumer:
            try:
                await process_message(message, db_pool, producer, dlq_producer)
                await consumer.commit()
            except KafkaError:
                # Don't commit — let the broker redeliver after rebalance.
                logger.exception("Kafka error while processing message — not committing.")
    finally:
        await consumer.stop()
        await producer.stop()
        await dlq_producer.stop()
        await db_pool.close()
        logger.info("Consumer and connections stopped.")


def run_consumer_in_background() -> None:
    """Schedule the consumer as a background asyncio task."""
    logger.info("Starting background Kafka consumer for learning-path-agent.")
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
