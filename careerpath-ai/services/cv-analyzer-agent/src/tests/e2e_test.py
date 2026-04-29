"""
Test end-to-end pentru CV Analyzer Agent.

Simulează un mesaj pe 'cv.uploaded' și verifică că 'cv.analyzed' apare
cu structura corectă și datele așteptate.

Necesită: Redpanda și Qdrant pornite.
  docker-compose --profile agents up

Rulare:
  python -m pytest src/tests/e2e_test.py -v -s

Variabile de mediu opționale:
  KAFKA_BROKERS_EXTERNAL  — default: localhost:19092 (portul expus în docker-compose)
  E2E_TIMEOUT_SECONDS     — default: 60
"""

import asyncio
import json
import os
import uuid

import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS_EXTERNAL", "localhost:19092")
TIMEOUT = int(os.getenv("E2E_TIMEOUT_SECONDS", "60"))

CV_JUNIOR_MOCK = """
Ion Popescu — Python Developer
Experiență: 8 luni internship backend la TechStartup SRL.
Tehnologii: Python, FastAPI, PostgreSQL, Docker, Git.
Proiecte: API REST pentru gestionarea comenzilor (proiect academic, ~200 utilizatori).
Educație: Facultatea de Automatică și Calculatoare, an 3.
"""

CV_SENIOR_MOCK = """
Maria Ionescu — Senior Cloud Architect
Experience: 8 years — AWS Solutions Architect at CloudCorp, previously Google SRE.
Skills: Kubernetes, Terraform, AWS, GCP, Python, Go, Prometheus, Grafana, CI/CD, LangChain.
Projects: Migrated monolith to microservices (500k req/day, 99.99% uptime SLA).
Education: MSc Computer Science, Universitatea Politehnica București.
Certifications: AWS Solutions Architect Professional, CKA, GCP Professional Cloud Architect.
"""


async def _send_cv(user_id: str, cv_text: str) -> None:
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    await producer.start()
    try:
        payload = json.dumps({"user_id": user_id, "cv_text": cv_text}).encode()
        await producer.send_and_wait("cv.uploaded", payload)
    finally:
        await producer.stop()


async def _wait_for_result(user_id: str, timeout: int) -> dict | None:
    consumer = AIOKafkaConsumer(
        "cv.analyzed",
        bootstrap_servers=KAFKA_BROKERS,
        group_id=f"e2e-test-{uuid.uuid4().hex[:8]}",
        auto_offset_reset="latest",
        value_deserializer=lambda v: json.loads(v.decode()),
        consumer_timeout_ms=timeout * 1000,
    )
    await consumer.start()
    try:
        async for msg in consumer:
            if msg.value.get("user_id") == user_id:
                return msg.value
    finally:
        await consumer.stop()
    return None


def _assert_base_structure(result: dict, user_id: str) -> None:
    assert result["user_id"] == user_id
    assert result["status"] == "success"
    assert isinstance(result["score"], int), "score trebuie să fie int"
    assert 0 <= result["score"] <= 100, f"score în afara intervalului: {result['score']}"
    assert result["seniority"] in {"junior", "mid", "senior", "lead"}
    assert isinstance(result["target_role"], str) and result["target_role"]
    assert isinstance(result["skills_extracted"], list) and len(result["skills_extracted"]) > 0
    assert isinstance(result["gaps_identified"], list)
    assert "score_breakdown" in result
    breakdown = result["score_breakdown"]
    assert set(breakdown.keys()) == {"experience", "skill_stack", "projects", "education", "certifications"}
    total = sum(breakdown.values())
    assert abs(total - result["score"]) <= 2, f"score_breakdown total ({total}) ≠ score ({result['score']})"


@pytest.mark.asyncio
async def test_junior_cv_includes_gap_analysis():
    user_id = f"e2e-junior-{uuid.uuid4().hex[:8]}"

    consumer_task = asyncio.create_task(_wait_for_result(user_id, TIMEOUT))
    await asyncio.sleep(1)  # asigurăm că consumer-ul e subscris înainte să trimitem
    await _send_cv(user_id, CV_JUNIOR_MOCK)

    result = await consumer_task
    assert result is not None, f"Nu s-a primit niciun eveniment cv.analyzed în {TIMEOUT}s"

    _assert_base_structure(result, user_id)

    if result["score"] < 70:
        assert "priority_gaps" in result, "Candidații cu score < 70 trebuie să aibă priority_gaps"
        assert "estimated_weeks_to_close" in result
        assert "learning_order" in result
        assert isinstance(result["priority_gaps"], list)
        assert len(result["priority_gaps"]) <= 3


@pytest.mark.asyncio
async def test_senior_cv_has_high_score():
    user_id = f"e2e-senior-{uuid.uuid4().hex[:8]}"

    consumer_task = asyncio.create_task(_wait_for_result(user_id, TIMEOUT))
    await asyncio.sleep(1)
    await _send_cv(user_id, CV_SENIOR_MOCK)

    result = await consumer_task
    assert result is not None, f"Nu s-a primit niciun eveniment cv.analyzed în {TIMEOUT}s"

    _assert_base_structure(result, user_id)
    assert result["score"] >= 70, f"CV-ul senior ar trebui să aibă score ≥ 70, primit: {result['score']}"
    assert result["seniority"] in {"senior", "lead"}


@pytest.mark.asyncio
async def test_invalid_message_is_skipped():
    """Un mesaj fără cv_text nu trebuie să blocheze consumer-ul."""
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    await producer.start()
    try:
        bad_payload = json.dumps({"user_id": "bad-user", "wrong_field": "oops"}).encode()
        await producer.send_and_wait("cv.uploaded", bad_payload)
    finally:
        await producer.stop()

    # Trimitem imediat după un CV valid ca să verificăm că pipeline-ul continuă
    user_id = f"e2e-after-bad-{uuid.uuid4().hex[:8]}"
    consumer_task = asyncio.create_task(_wait_for_result(user_id, TIMEOUT))
    await asyncio.sleep(1)
    await _send_cv(user_id, CV_JUNIOR_MOCK)

    result = await consumer_task
    assert result is not None, "Consumer-ul s-a blocat după un mesaj invalid"
    assert result["status"] == "success"
