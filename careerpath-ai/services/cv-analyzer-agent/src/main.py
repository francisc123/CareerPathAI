"""
Entry point pentru cv-analyzer-agent.

Porneste un server FastAPI (pentru endpoint-uri HTTP precum /health) si,
in paralel, porneste in background consumer-ul Redpanda care asculta
topic-ul 'cv.uploaded'.

De ce avem si HTTP, si consumer Kafka?
- HTTP (FastAPI) = doar pentru health check. Docker are nevoie sa stie ca
  serviciul e viu. NU expunem logica de business prin HTTP.
- Consumer Kafka = "mainile" agentului. Toata munca lui pleaca de la evenimente.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.consumers.cv_upload_consumer import consume_cv_uploaded_events
from src.routers import health

# Configurare logging globala pentru aplicatie.
# Format = "TIMESTAMP LEVEL LOGGER_NAME: MESAJ"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Hook-ul de "ciclu de viata" al aplicatiei FastAPI.

    Tot codul INAINTE de `yield` ruleaza la STARTUP (cand porneste serverul).
    Tot codul DUPA `yield` ruleaza la SHUTDOWN (cand se opreste serverul).

    Aici pornim consumer-ul Kafka ca task de background si-l oprim curat
    cand aplicatia se inchide.
    """
    # asyncio.create_task() = porneste o coroutine in paralel cu serverul HTTP.
    # Task-ul ruleaza independent — FastAPI raspunde la cereri HTTP, iar
    # consumer-ul asculta mesaje, in acelasi loop async.
    logger.info("Starting cv-analyzer-agent...")
    consumer_task = asyncio.create_task(consume_cv_uploaded_events())

    try:
        yield  # Serverul e pornit si raspunde la cereri
    finally:
        # SHUTDOWN: anulam task-ul consumer-ului ca sa se opreasca curat.
        # cancel() trimite CancelledError in interiorul coroutinei, care
        # ajunge la finally din consumer si inchide conexiunea la broker.
        logger.info("Stopping cv-analyzer-agent...")
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass  # Comportament asteptat la cancel
        logger.info("cv-analyzer-agent stopped cleanly")


# Initializam aplicatia cu lifespan-ul nostru.
app = FastAPI(
    title="CV Analyzer Agent",
    description="Worker invizibil care analizeaza CV-uri din topic 'cv.uploaded'",
    lifespan=lifespan,
)

# Atasam routerul de health la aplicatie.
# Endpoint-urile din health.py devin disponibile sub root: GET /health.
app.include_router(health.router)
