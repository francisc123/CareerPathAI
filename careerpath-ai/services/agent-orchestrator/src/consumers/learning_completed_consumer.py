import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

from .notifier import notify_user
from .workflow_state import merge_state

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
TOPIC = "learning.completed"
DLQ_TOPIC = f"{TOPIC}.dlq"
GROUP_ID = "agent-orchestrator-learning-completed"


async def _handle(payload: dict) -> None:
    user_id = payload.get("user_id")
    if not user_id:
        logger.warning("learning.completed payload missing user_id — skip.")
        return

    await merge_state(
        user_id,
        {
            "current_node": "interview_ready",
            "learning_completed": True,
        },
    )
    await notify_user(
        user_id,
        event_type="learning.completed",
        payload={"message": "You're ready for interviews!"},
    )
    logger.info("learning.completed processed for %s.", user_id)


async def consume() -> None:
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
    )
    dlq = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    await consumer.start()
    await dlq.start()
    logger.info("Consumer started for topic %s.", TOPIC)
    try:
        async for message in consumer:
            try:
                await _handle(message.value)
                await consumer.commit()
            except Exception:
                logger.exception(
                    "Failed to process learning.completed — sending to DLQ and committing."
                )
                try:
                    await dlq.send_and_wait(
                        DLQ_TOPIC,
                        json.dumps(
                            {"reason": "exception", "payload": message.value}
                        ).encode("utf-8"),
                    )
                except Exception:
                    logger.exception("DLQ send failed for %s.", TOPIC)
                # Commit anyway so we don't infinite-loop on a bad message.
                await consumer.commit()
    except asyncio.CancelledError:
        raise
    except KafkaError:
        logger.exception("Kafka error in learning.completed consumer loop.")
        raise
    finally:
        await consumer.stop()
        await dlq.stop()
