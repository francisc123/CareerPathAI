import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.consumers.cv_upload_consumer import consume_cv_uploaded_events
from src.db.cv_repository import init_db_pool, close_db_pool
from src.publishers.cv_analyzed_publisher import init_producer, stop_producer
from src.routers import ats_match, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Pornesc cv-analyzer-agent...")
    await init_producer()
    await init_db_pool()
    consumer_task = asyncio.create_task(consume_cv_uploaded_events())

    try:
        yield
    finally:
        logger.info("Opresc cv-analyzer-agent...")
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        await stop_producer()
        await close_db_pool()
        logger.info("cv-analyzer-agent oprit curat.")


app = FastAPI(
    title="CV Analyzer Agent",
    description="Worker invizibil care analizează CV-uri din topic 'cv.uploaded'",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(ats_match.router)
