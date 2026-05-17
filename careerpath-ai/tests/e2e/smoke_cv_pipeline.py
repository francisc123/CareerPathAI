"""
Smoke test cap-coadă pentru CV analyzer pipeline.

Publică pe cv.uploaded și așteaptă rezultatul pe cv.analyzed.
Folosește doar aiokafka (deja instalat în container).
"""
import asyncio
import json
import os
import sys
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
TIMEOUT = int(os.getenv("E2E_TIMEOUT", "90"))

CV_SENIOR = """
Maria Ionescu - Senior Cloud Architect
Experience: 8 years - AWS Solutions Architect at CloudCorp, previously Google SRE.
Skills: Kubernetes, Terraform, AWS, GCP, Python, Go, Prometheus, Grafana, CI/CD, LangChain.
Projects: Migrated monolith to microservices (500k req/day, 99.99% uptime SLA).
Education: MSc Computer Science, Universitatea Politehnica Bucuresti.
Certifications: AWS Solutions Architect Professional, CKA, GCP Professional Cloud Architect.
"""


async def run() -> int:
    user_id = f"smoke-{uuid.uuid4().hex[:8]}"
    print(f"[smoke] User ID: {user_id}", flush=True)
    print(f"[smoke] Brokers: {BROKERS}", flush=True)

    consumer = AIOKafkaConsumer(
        "cv.analyzed",
        bootstrap_servers=BROKERS,
        group_id=f"smoke-{uuid.uuid4().hex[:8]}",
        auto_offset_reset="latest",
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    await consumer.start()

    producer = AIOKafkaProducer(bootstrap_servers=BROKERS)
    await producer.start()

    try:
        payload = json.dumps({"user_id": user_id, "cv_text": CV_SENIOR}).encode()
        await producer.send_and_wait("cv.uploaded", payload)
        print("[smoke] Sent cv.uploaded", flush=True)

        deadline = asyncio.get_event_loop().time() + TIMEOUT
        while asyncio.get_event_loop().time() < deadline:
            remaining = deadline - asyncio.get_event_loop().time()
            try:
                msg = await asyncio.wait_for(consumer.getone(), timeout=remaining)
            except asyncio.TimeoutError:
                break
            if msg.value.get("user_id") != user_id:
                continue
            result = msg.value
            print(f"[smoke] Got cv.analyzed: status={result.get('status')} score={result.get('score')} seniority={result.get('seniority')}", flush=True)
            assert result["status"] == "success", f"Status not success: {result}"
            assert isinstance(result.get("score"), int), "score must be int"
            assert 0 <= result["score"] <= 100
            assert result["seniority"] in {"junior", "mid", "senior", "lead"}
            assert isinstance(result.get("skills_extracted"), list) and len(result["skills_extracted"]) > 0
            print("[smoke] PASS", flush=True)
            return 0

        print(f"[smoke] TIMEOUT after {TIMEOUT}s", flush=True)
        return 1
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
