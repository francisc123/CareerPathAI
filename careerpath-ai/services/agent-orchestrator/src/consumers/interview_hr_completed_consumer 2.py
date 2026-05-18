import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

from .finalize import maybe_finalize_workflow
from .notifier import notify_user
from .workflow_state import load_state, merge_state

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
TOPIC = "interview.hr.completed"
DLQ_TOPIC = f"{TOPIC}.dlq"
GROUP_ID = "agent-orchestrator-interview-hr-completed"


async def _handle(payload: dict) -> None:
    user_id = payload.get("user_id")
    if not user_id:
        logger.warning("interview.hr.completed missing user_id — skip.")
        return

    score = payload.get("score")

    await merge_state(
        user_id,
        {
            "hr_completed": True,
            "hr_score": score,
            "current_node": "hr_interview_completed",
        },
    )

    # Nudge to take the technical interview if not done yet.
    state = await load_state(user_id)
    if not state.get("tech_completed"):
        await notify_user(
            user_id,
            event_type="interview.hr.completed",
            payload={"message": "Great job! Now try the Technical Interview."},
        )

    # The workflow may already be ready to finalize if tech was done first.
    await maybe_finalize_workflow(user_id)
    logger.info("interview.hr.completed processed for %s (score=%s).", user_id, score)


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
                    "Failed to process interview.hr.completed — sending to DLQ and committing."
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
                await consumer.commit()
    except asyncio.CancelledError:
        raise
    except KafkaError:
        logger.exception("Kafka error in interview.hr.completed consumer loop.")
        raise
    finally:
        await consumer.stop()
        await dlq.stop()
