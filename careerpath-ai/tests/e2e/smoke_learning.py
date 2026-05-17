"""
Smoke test pentru flow-ul cu score mic: cv.uploaded -> cv.analyzed -> gaps.identified.
"""
import asyncio
import json
import os
import sys
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
TIMEOUT = int(os.getenv("E2E_TIMEOUT", "90"))

CV_WEAK = """
Andrei - Student.
Obiectiv: primul internship in IT.
Educatie: anul 1 facultate, niciun proiect terminat.
Tehnologii: HTML, putin CSS.
Nu am experienta profesionala, nu am proiecte publicate, nu cunosc baze de date sau cloud.
"""


async def run() -> int:
    user_id = f"smoke-weak-{uuid.uuid4().hex[:8]}"
    print(f"[smoke] User ID: {user_id}", flush=True)

    gaps_consumer = AIOKafkaConsumer(
        "gaps.identified",
        bootstrap_servers=BROKERS,
        group_id=f"smoke-gaps-{uuid.uuid4().hex[:8]}",
        auto_offset_reset="latest",
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    await gaps_consumer.start()

    producer = AIOKafkaProducer(bootstrap_servers=BROKERS)
    await producer.start()

    try:
        payload = json.dumps({"user_id": user_id, "cv_text": CV_WEAK}).encode()
        await producer.send_and_wait("cv.uploaded", payload)
        print("[smoke] Sent cv.uploaded (weak CV)", flush=True)

        deadline = asyncio.get_event_loop().time() + TIMEOUT
        while asyncio.get_event_loop().time() < deadline:
            remaining = deadline - asyncio.get_event_loop().time()
            try:
                msg = await asyncio.wait_for(gaps_consumer.getone(), timeout=remaining)
            except asyncio.TimeoutError:
                break
            if msg.value.get("user_id") != user_id:
                continue
            print(f"[smoke] Got gaps.identified: gaps={msg.value.get('gaps')} target={msg.value.get('target_role')}", flush=True)
            assert msg.value.get("gaps"), "gaps must be non-empty for weak CV"
            print("[smoke] PASS", flush=True)
            return 0

        print(f"[smoke] TIMEOUT after {TIMEOUT}s waiting for gaps.identified", flush=True)
        return 1
    finally:
        await gaps_consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
