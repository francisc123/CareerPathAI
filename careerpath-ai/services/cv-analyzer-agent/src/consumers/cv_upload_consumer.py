import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from src.agents.cv_analyzer import process_cv_pipeline
from src.db.cv_repository import save_cv_analysis, update_cv_upload_result
from src.publishers.cv_analyzed_publisher import publish_cv_analyzed_event

logger = logging.getLogger(__name__)

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
KAFKA_TOPIC = "cv.uploaded"
KAFKA_GROUP_ID = "cv-analyzer-agent"


async def consume_cv_uploaded_events() -> None:
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
    )

    await consumer.start()
    logger.info(
        "Consumer conectat (brokers=%s, topic=%s, group=%s)",
        KAFKA_BROKERS,
        KAFKA_TOPIC,
        KAFKA_GROUP_ID,
    )

    try:
        async for message in consumer:
            payload = message.value
            user_id = payload.get("user_id")
            cv_text = payload.get("cv_text")
            job_id = payload.get("job_id")

            if not user_id or not cv_text:
                logger.warning("Mesaj invalid — lipsesc câmpuri obligatorii. Skip.")
                await consumer.commit()
                continue

            logger.info("CV primit pentru user: %s (job_id=%s)", user_id, job_id)
            try:
                result = await asyncio.to_thread(
                    process_cv_pipeline,
                    cv_text=cv_text,
                    user_id=user_id,
                )

                await save_cv_analysis(
                    user_id=user_id,
                    score=result["score"],
                    seniority=result["seniority"],
                    target_role=result["target_role"],
                )

                if job_id:
                    await update_cv_upload_result(
                        job_id=job_id,
                        status="analyzed",
                        score=result.get("score"),
                        skills=result.get("skills_extracted"),
                        gaps=result.get("gaps_identified"),
                    )
                else:
                    logger.warning(
                        "Lipsește job_id în payload pentru user %s — sar peste update cv_uploads.",
                        user_id,
                    )

                # Inject job_id in the outgoing event so downstream agents can
                # correlate analysis back to the original upload.
                if job_id and "job_id" not in result:
                    result["job_id"] = job_id

                await publish_cv_analyzed_event(result)
                await consumer.commit()
                logger.info("Procesare completă și offset comis pentru user: %s", user_id)
            except Exception as e:
                # Pipeline failed — best-effort mark the upload as failed,
                # but do NOT commit the offset so the message is redelivered.
                logger.error("Procesare eșuată pentru %s, offset necomis: %s", user_id, e)
                if job_id:
                    try:
                        await update_cv_upload_result(job_id=job_id, status="failed")
                    except Exception:
                        logger.exception(
                            "Și marcajul `failed` în cv_uploads a eșuat pentru job_id=%s.",
                            job_id,
                        )

    except asyncio.CancelledError:
        logger.info("Consumer anulat (shutdown).")
        raise
    except KafkaError:
        logger.exception("Eroare Kafka în bucla consumer-ului.")
        raise
    finally:
        await consumer.stop()
        logger.info("Consumer deconectat de la Redpanda.")
