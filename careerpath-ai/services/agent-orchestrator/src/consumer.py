import asyncio
import json
import logging
import redis.asyncio as redis
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from .config import (
    KAFKA_BROKERS,
    TOPIC_CV_ANALYZED,
    TOPIC_LEARNING_COMPLETED,
    TOPIC_ORCHESTRATOR_DLQ,
    REDIS_URL,
)
from .state import CvAnalyzedEvent, WorkflowState
from .workflow import graph
from .retry import startup_retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# ─────────────────────────────────────────────────────────────────────────────
# Bootstrap helpers (retry on transient Kafka unreadiness during cold start)
# ─────────────────────────────────────────────────────────────────────────────
@startup_retry("kafka")
async def _start_kafka_consumer(topic: str, group_id: str, offset_reset: str):
    """Create + start an AIOKafkaConsumer, retrying on broker unreadiness."""
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BROKERS,
        group_id=group_id,
        auto_offset_reset=offset_reset,
    )
    await consumer.start()
    return consumer


@startup_retry("kafka")
async def _start_kafka_producer():
    """Create + start an AIOKafkaProducer, retrying on broker unreadiness."""
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    await producer.start()
    return producer


# ─────────────────────────────────────────────────────────────────────────────
# CV-analyzed consumer (existing pipeline)
# ─────────────────────────────────────────────────────────────────────────────
async def process_message(message, redis_client, producer):
    """Processes a single Kafka message from cv.analyzed."""
    try:
        data = json.loads(message.value.decode("utf-8"))
        # Map cv-analyzer field names (gaps_identified) to the orchestrator schema (gaps).
        if "gaps_identified" in data and "gaps" not in data:
            data["gaps"] = data["gaps_identified"]
        event = CvAnalyzedEvent(**data)

        logging.info(f"Received CV analysis for user: {event.user_id}, Score: {event.score}")

        # Keep the raw triggering event so monitoring API can replay it on /retry.
        await redis_client.set(
            f"workflow:{event.user_id}:last_event",
            json.dumps(data),
            ex=3600 * 24,
        )

        initial_state = WorkflowState(
            user_id=event.user_id,
            cv_score=event.score,
            gaps=event.gaps,
            target_role=event.target_role,
            seniority=event.seniority,
            skills=event.skills_extracted,
            retry_count=0,
        )

        final_state = await graph.ainvoke(initial_state)

        state_json = json.dumps(final_state)
        await redis_client.set(f"workflow:{event.user_id}", state_json, ex=3600 * 24)

        logging.info(
            f"Workflow finished for user: {event.user_id}. "
            f"Final node: {final_state.get('current_node')}"
        )

    except (json.JSONDecodeError, TypeError) as e:
        logging.error(f"Failed to decode or validate message: {e}. Sending to DLQ.")
        await producer.send_and_wait(
            TOPIC_ORCHESTRATOR_DLQ,
            value=message.value,
            key=message.key,
        )
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")


async def consume():
    """Main consumer loop for cv.analyzed, with DLQ producer."""
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    dlq_producer = await _start_kafka_producer()
    consumer = await _start_kafka_consumer(
        TOPIC_CV_ANALYZED,
        group_id="agent-orchestrator-group",
        offset_reset="latest",
    )
    logging.info(f"Consumer started on topic '{TOPIC_CV_ANALYZED}'...")

    try:
        async for message in consumer:
            await process_message(message, redis_client, dlq_producer)
    finally:
        await consumer.stop()
        await dlq_producer.stop()
        await redis_client.close()
        logging.info("cv.analyzed consumer and DLQ producer stopped.")


# ─────────────────────────────────────────────────────────────────────────────
# Learning-completed consumer (workflow → interview_ready transition)
#
# Note: a fresh Redis client is created per message. This avoids a known issue
# where redis-py's async timeouts raise `RuntimeError: Timeout should be used
# inside a task` when a pool connection's owning task is destroyed between
# Kafka fetcher iterations.
# ─────────────────────────────────────────────────────────────────────────────
async def consume_learning_completed():
    """Consumes learning.completed events and transitions workflow state to 'interview_ready'."""
    consumer = await _start_kafka_consumer(
        TOPIC_LEARNING_COMPLETED,
        group_id="agent-orchestrator-learning-group",
        offset_reset="earliest",  # replay anything published before the consumer existed
    )
    logging.info(f"Consumer started on topic '{TOPIC_LEARNING_COMPLETED}'...")

    try:
        async for message in consumer:
            redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            try:
                user_id = message.key.decode("utf-8") if message.key else None
                if not user_id:
                    logging.warning("learning.completed message with no key, skipping.")
                    continue

                logging.info(f"Learning completed for user: {user_id}")

                # Merge with existing workflow state if present, otherwise create fresh
                existing = await redis_client.get(f"workflow:{user_id}")
                if existing:
                    try:
                        state = json.loads(existing)
                    except json.JSONDecodeError:
                        state = {}
                else:
                    state = {"user_id": user_id}

                state["status"] = "interview_ready"
                state["learning_completed_at"] = message.timestamp

                await redis_client.set(
                    f"workflow:{user_id}",
                    json.dumps(state),
                    ex=3600 * 24 * 7,
                )
                logging.info(f"Workflow transitioned to 'interview_ready' for user: {user_id}")

            except Exception as e:
                logging.error(
                    f"Failed to process learning.completed message: {e}",
                    exc_info=True,
                )
            finally:
                await redis_client.aclose()
    finally:
        await consumer.stop()
        logging.info("learning.completed consumer stopped.")


# ─────────────────────────────────────────────────────────────────────────────
# Bootstrap entry-point called from main.py:lifespan
# ─────────────────────────────────────────────────────────────────────────────
def run_consumer_in_background():
    """Runs both Kafka consumers in background asyncio tasks."""
    logging.info("Starting background Kafka consumers...")
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
    loop.create_task(consume_learning_completed())