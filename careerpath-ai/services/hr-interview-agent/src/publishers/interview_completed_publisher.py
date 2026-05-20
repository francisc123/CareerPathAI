import json
import logging
import os
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
TOPIC_NAME = "interview.hr.completed"
DLQ_TOPIC_NAME = f"{TOPIC_NAME}.dlq"

_producer: AIOKafkaProducer | None = None


async def init_producer() -> None:
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        # aiokafka enforces max_in_flight=1 implicitly when idempotence is on.
        enable_idempotence=True,
        acks="all",
    )
    await _producer.start()
    logger.info("Kafka producer pornit (brokers=%s)", KAFKA_BROKERS)


async def stop_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer oprit.")


async def publish_interview_hr_completed(
    *,
    user_id: str,
    session_id: str,
    verdict: str | None,
    summary: str | None,
    strengths: list[str],
    areas_of_improvement: list[str],
    transcript: str,
    turn_count: int,
    reason: str = "session_ended",
) -> None:
    """
    Publish `interview.hr.completed`. The HR verdict is now PASS/FAIL with
    structured strengths + growth areas; downstream consumers should read
    `verdict` instead of the legacy numeric `score`.

    `reason`: "session_ended" | "turn_limit_reached" | "disconnect"
    """
    if not _producer:
        logger.warning("Producer Kafka neinițializat — skip publish pentru session %s.", session_id)
        return

    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "type": "hr",
        "verdict": verdict,
        "summary": summary,
        "strengths": strengths,
        "areas_of_improvement": areas_of_improvement,
        "transcript": transcript,
        "turn_count": turn_count,
        "reason": reason,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    message = json.dumps(payload).encode("utf-8")

    try:
        await _producer.send_and_wait(TOPIC_NAME, message)
        logger.info(
            "Eveniment publicat pe '%s' (user_id=%s, session_id=%s, reason=%s).",
            TOPIC_NAME,
            user_id,
            session_id,
            reason,
        )
    except KafkaError:
        logger.exception(
            "Publish eșuat pe '%s' pentru session %s — trimit în DLQ.",
            TOPIC_NAME,
            session_id,
        )
        try:
            await _producer.send_and_wait(DLQ_TOPIC_NAME, message)
        except Exception:
            logger.exception("Și DLQ publish a eșuat pentru session %s.", session_id)
