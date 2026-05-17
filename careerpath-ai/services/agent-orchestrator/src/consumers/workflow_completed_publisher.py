import json
import logging
import os
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
TOPIC_NAME = "workflow.completed"
DLQ_TOPIC_NAME = f"{TOPIC_NAME}.dlq"

_producer: AIOKafkaProducer | None = None


async def init_producer() -> None:
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        enable_idempotence=True,
        acks="all",
    )
    await _producer.start()


async def stop_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None


async def publish_workflow_completed(
    *,
    user_id: str,
    final_score: int,
    cv_score: int | None,
    hr_score: int | None,
    tech_score: int | None,
) -> None:
    if _producer is None:
        logger.warning("Producer not initialized — skip workflow.completed for %s.", user_id)
        return

    payload = {
        "user_id": user_id,
        "final_score": final_score,
        "cv_score": cv_score,
        "hr_score": hr_score,
        "tech_score": tech_score,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    message = json.dumps(payload).encode("utf-8")
    try:
        await _producer.send_and_wait(TOPIC_NAME, message)
        logger.info("workflow.completed published for user %s (final=%d).", user_id, final_score)
    except KafkaError:
        logger.exception("Failed to publish workflow.completed for %s — trying DLQ.", user_id)
        try:
            await _producer.send_and_wait(DLQ_TOPIC_NAME, message)
        except Exception:
            logger.exception("DLQ publish also failed for %s.", user_id)
