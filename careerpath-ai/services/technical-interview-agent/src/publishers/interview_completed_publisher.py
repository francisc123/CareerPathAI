import json
import logging
import os
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
TOPIC_NAME = "interview.tech.completed"
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


async def publish_interview_tech_completed(
    *,
    user_id: str,
    session_id: str,
    verdict: str | None,
    summary: str | None,
    strengths: list[str],
    weaknesses: list[str],
    optimization_insights: list[str],
    readiness_level: str | None,
    score: int | None,
    transcript: str,
    problems_attempted: int,
    problems_passed: int,
    reason: str = "session_ended",
) -> None:
    if _producer is None:
        logger.warning("Producer Kafka neinițializat — skip publish pentru session %s.", session_id)
        return
    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "type": "technical",
        "verdict": verdict,
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "optimization_insights": optimization_insights,
        "readiness_level": readiness_level,
        "score": score,
        "transcript": transcript,
        "problems_attempted": problems_attempted,
        "problems_passed": problems_passed,
        "reason": reason,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    message = json.dumps(payload).encode("utf-8")
    try:
        await _producer.send_and_wait(TOPIC_NAME, message)
        logger.info(
            "Eveniment publicat pe '%s' (user_id=%s, session_id=%s, reason=%s).",
            TOPIC_NAME, user_id, session_id, reason,
        )
    except KafkaError:
        logger.exception("Publish eșuat pe '%s' — trimit în DLQ.", TOPIC_NAME)
        try:
            await _producer.send_and_wait(DLQ_TOPIC_NAME, message)
        except Exception:
            logger.exception("Și DLQ publish a eșuat pentru session %s.", session_id)
