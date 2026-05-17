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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# ---------- existing CV consumer ----------
async def process_message(message, redis_client, producer):
    try:
        data = json.loads(message.value.decode("utf-8"))
        event = CvAnalyzedEvent(**data)
        logging.info(f"Received CV analysis for user: {event.user_id}, Score: {event.score}")

        initial_state = WorkflowState(
            user_id=event.user_id,
            cv_score=event.score,
            gaps=event.gaps,
            target_role=event.target_role,
            retry_count=0,
        )
        final_state = await graph.ainvoke(initial_state)
        state_json = json.dumps(final_state)
        await redis_client.set(f"workflow:{event.user_id}", state_json, ex=3600 * 24)
        logging.info(f"Workflow finished for user: {event.user_id}. Final node: {final_state.get('current_node')}")
    except (json.JSONDecodeError, TypeError) as e:
        logging.error(f"Failed to decode or validate message: {e}. Sending to DLQ.")
        await producer.send_and_wait(TOPIC_ORCHESTRATOR_DLQ, value=message.value, key=message.key)
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")


async def consume():
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    dlq_producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    consumer = AIOKafkaConsumer(
        TOPIC_CV_ANALYZED,
        bootstrap_servers=KAFKA_BROKERS,
        group_id="agent-orchestrator-group",
        auto_offset_reset="latest",
    )
    await dlq_producer.start()
    await consumer.start()
    logging.info(f"Consumer started on topic '{TOPIC_CV_ANALYZED}'...")
    try:
        async for message in consumer:
            await process_message(message, redis_client, dlq_producer)
    finally:
        await consumer.stop()
        await dlq_producer.stop()
        await redis_client.close()


# ---------- NEW: learning.completed consumer ----------
async def consume_learning_completed():
    """Consumes learning.completed events and transitions workflow state to 'interview_ready'."""
    consumer = AIOKafkaConsumer(
        TOPIC_LEARNING_COMPLETED,
        bootstrap_servers=KAFKA_BROKERS,
        group_id="agent-orchestrator-learning-group",
        auto_offset_reset="earliest",
    )

    await consumer.start()
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
                logging.error(f"Failed to process learning.completed message: {e}", exc_info=True)
            finally:
                await redis_client.aclose()
    finally:
        await consumer.stop()


def run_consumer_in_background():
    """Runs both Kafka consumers in background asyncio tasks."""
    logging.info("Starting background Kafka consumers...")
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
    loop.create_task(consume_learning_completed())