import json
import logging
import os
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
TOPIC_NAME = "cv.analyzed"

_producer: AIOKafkaProducer | None = None


async def init_producer() -> None:
    global _producer
    _producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    await _producer.start()
    logger.info("Kafka producer pornit (brokers=%s)", KAFKA_BROKERS)


async def stop_producer() -> None:
    if _producer:
        await _producer.stop()
        logger.info("Kafka producer oprit.")


def get_producer() -> AIOKafkaProducer | None:
    return _producer


async def publish_cv_analyzed_event(result_data: dict) -> None:
    if not _producer:
        raise RuntimeError("Producătorul Kafka nu este inițializat.")
    message = json.dumps(result_data).encode("utf-8")
    await _producer.send_and_wait(TOPIC_NAME, message)
    logger.info(
        "Eveniment publicat pe '%s' pentru user_id: %s",
        TOPIC_NAME,
        result_data.get("user_id"),
    )
