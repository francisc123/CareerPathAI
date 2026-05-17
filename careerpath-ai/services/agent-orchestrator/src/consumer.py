import asyncio
import json
import logging
import redis.asyncio as redis
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from .config import KAFKA_BROKERS, TOPIC_CV_ANALYZED, REDIS_URL, TOPIC_ORCHESTRATOR_DLQ
from .state import CvAnalyzedEvent, WorkflowState
from .workflow import graph

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def process_message(message, redis_client, producer):
    """Processes a single Kafka message."""
    try:
        data = json.loads(message.value.decode("utf-8"))
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
            retry_count=0, # Initialize retry count
        )

        # Invoke the graph
        final_state = await graph.ainvoke(initial_state)

        # Persist final state to Redis
        state_json = json.dumps(final_state)
        await redis_client.set(f"workflow:{event.user_id}", state_json, ex=3600 * 24)

        logging.info(f"Workflow finished for user: {event.user_id}. Final node: {final_state.get('current_node')}")

    except (json.JSONDecodeError, TypeError) as e:
        logging.error(f"Failed to decode or validate message: {e}. Sending to DLQ.")
        await producer.send_and_wait(
            TOPIC_ORCHESTRATOR_DLQ,
            value=message.value,
            key=message.key
        )
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")

async def consume():
    """Main consumer loop with DLQ producer."""
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Producer for DLQ
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
        logging.info("Consumer and connections stopped.")

def run_consumer_in_background():
    """Runs the Kafka consumer in a background asyncio task."""
    logging.info("Starting background Kafka consumer...")
    loop = asyncio.get_event_loop()
    loop.create_task(consume())
