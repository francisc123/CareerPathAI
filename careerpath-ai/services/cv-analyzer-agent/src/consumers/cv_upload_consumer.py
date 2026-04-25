"""
Consumer Redpanda pentru topic-ul 'cv.uploaded'.

Acest fisier contine logica care ASCULTA continuu mesajele venite de la
cv-service (cel care primeste CV-ul de la utilizator). Pentru fiecare mesaj
primit, deocamdata DOAR LOGAM (CP-009 = doar scheletul). Logica reala de
analiza (Gemini, Qdrant, PostgreSQL) vine la CP-020.

Cum functioneaza un consumer Kafka/Redpanda:
1. Se conecteaza la broker (start)
2. Se "aboneaza" la un topic (cv.uploaded)
3. Intra intr-o bucla infinita: asteapta mesaje noi -> proceseaza -> confirma
4. La oprirea aplicatiei, inchide curat conexiunea (stop)
"""

import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

# Logger pentru acest modul. Folosim logging in loc de print ca sa avem
# nivele (INFO, WARNING, ERROR) si format consistent cu restul aplicatiei.
logger = logging.getLogger(__name__)

# Citim configurarea din variabile de mediu, cu fallback la valoarea Docker.
# IMPORTANT: in fisierul tau .env trebuie sa ai KAFKA_BROKERS=redpanda:9092.
# .env.example are gresit "kafka:9092" — serviciul nostru se cheama "redpanda".
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
KAFKA_TOPIC = "cv.uploaded"

# Group ID = identificator al "grupului de consumatori". Toate instantele
# cu acelasi group_id impart mesajele intre ele (load balancing).
# Daca scalezi cv-analyzer-agent la 3 replici, Redpanda distribuie mesajele
# intre cei 3 — nu primesc toti acelasi mesaj.
KAFKA_GROUP_ID = "cv-analyzer-agent"


async def consume_cv_uploaded_events() -> None:
    """
    Bucla async care asculta topic-ul 'cv.uploaded' si logheaza fiecare mesaj.

    Functia ruleaza cat timp aplicatia e pornita. Se opreste cand task-ul e
    anulat (asyncio.CancelledError) — asta se intampla in main.py la shutdown.
    """
    # Construim consumer-ul. Parametrii cheie:
    #   KAFKA_TOPIC          = topic-ul pe care ascultam
    #   bootstrap_servers    = adresa brokerului
    #   group_id             = grupul nostru (vezi explicatia de mai sus)
    #   auto_offset_reset    = "earliest" -> la prima rulare citim de la primul
    #                          mesaj din topic. La rulari ulterioare continuam
    #                          de unde am ramas (Redpanda tine offsetul per group).
    #   value_deserializer   = functia care transforma bytes-urile primite in
    #                          obiect Python. Mesajele sunt JSON, deci facem
    #                          json.loads dupa decode utf-8.
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
    )

    # start() face conexiunea la broker. Daca Redpanda nu raspunde, da eroare.
    await consumer.start()
    logger.info(
        "Consumer connected to Redpanda (brokers=%s, topic=%s, group=%s)",
        KAFKA_BROKERS,
        KAFKA_TOPIC,
        KAFKA_GROUP_ID,
    )

    try:
        # `async for` peste consumer = bucla de polling.
        # aiokafka se ocupa in spate sa intrebe brokerul "ai ceva nou?".
        # Cand vine un mesaj il pune in iterator. Nu trebuie noi sa
        # implementam `while True: poll(...)` cum face kafka-python.
        async for message in consumer:
            # Pentru CP-009 doar logam. La CP-020 aici va fi:
            #   payload = message.value
            #   result  = await analyze_cv(payload)
            #   await publish_cv_analyzed(result)
            logger.info(
                "Received cv.uploaded event: partition=%d offset=%d payload=%s",
                message.partition,
                message.offset,
                message.value,
            )
    except asyncio.CancelledError:
        # Task-ul a fost anulat la shutdown. Comportament normal, nu eroare.
        logger.info("Consumer task cancelled, shutting down...")
        raise  # Re-aruncam ca asyncio sa marcheze task-ul ca finalizat corect
    except KafkaError:
        # Eroare de comunicare cu brokerul (retea picata, broker down, etc.)
        logger.exception("Kafka error in consumer loop")
        raise
    finally:
        # Oricum s-ar termina (eroare sau cancel), inchidem curat conexiunea.
        # Asta inseamna: trimitem brokerului "am terminat", commit la offset.
        await consumer.stop()
        logger.info("Consumer disconnected from Redpanda")
