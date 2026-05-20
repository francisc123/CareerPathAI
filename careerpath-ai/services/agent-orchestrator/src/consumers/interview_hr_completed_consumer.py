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

    verdict = payload.get("verdict")  # "PASS" | "FAIL" | None (analysis failure)
    # Derived numeric score keeps the downstream final-score blender working
    # (see finalize.py) without forcing it to special-case PASS/FAIL.
    derived_hr_score = 80 if verdict == "PASS" else 40 if verdict == "FAIL" else None

    await merge_state(
        user_id,
        {
            "hr_completed": True,
            "hr_verdict": verdict,
            "hr_score": derived_hr_score,
            "current_node": "hr_interview_completed",
        },
    )

    # Nudge to take the technical interview if HR passed and tech not yet done.
    # On FAIL, surface a softer follow-up instead of pushing tech.
    state = await load_state(user_id)
    if not state.get("tech_completed"):
        if verdict == "PASS":
            message = "Great job — you passed the HR screener! Try the Technical Interview next."
        elif verdict == "FAIL":
            message = "HR screener wrapped. Review your feedback and try again when you're ready."
        else:
            message = "HR interview complete. Take a look at your feedback."
        await notify_user(
            user_id,
            event_type="interview.hr.completed",
            payload={"message": message},
        )

    # The workflow may already be ready to finalize if tech was done first.
    await maybe_finalize_workflow(user_id)
    logger.info("interview.hr.completed processed for %s (verdict=%s).", user_id, verdict)


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
