"""
Smoke test cap-coadă pentru fluxul de interview:
  1. Genereaza JWT RS256 cu sub=user_id
  2. Conecteaza WS la HR interview agent, schimba cateva turns, deconecteaza
  3. Consuma interview.hr.completed si valideaza payloadul
  4. Repeta pentru technical interview agent
  5. Consuma interview.tech.completed si valideaza

Ruleaza din interiorul cp-hr-agent (are jose, websockets, aiokafka, private key montat).
"""
import asyncio
import json
import os
import sys
import time
import uuid
from pathlib import Path

from aiokafka import AIOKafkaConsumer
from jose import jwt
import websockets

BROKERS = os.getenv("KAFKA_BROKERS", "redpanda:9092")
TIMEOUT = int(os.getenv("E2E_TIMEOUT", "120"))
PRIVATE_KEY_PATH = os.getenv("JWT_PRIVATE_KEY_PATH", "/app/keys/private.pem")

# Inside docker network, services are reachable by their container hostname.
HR_WS_BASE = os.getenv("HR_WS_BASE", "ws://cp-hr-agent:8009")
TECH_WS_BASE = os.getenv("TECH_WS_BASE", "ws://cp-tech-agent:8010")


def make_token(user_id: str) -> str:
    private_key = Path(PRIVATE_KEY_PATH).read_text(encoding="utf-8")
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + 900,  # 15 min
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


async def _consume_one(topic: str, user_id: str, timeout: int) -> dict | None:
    """Consume next event matching user_id on topic."""
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=BROKERS,
        group_id=f"smoke-interview-{uuid.uuid4().hex[:8]}",
        auto_offset_reset="latest",
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    await consumer.start()
    deadline = asyncio.get_event_loop().time() + timeout
    try:
        while asyncio.get_event_loop().time() < deadline:
            remaining = deadline - asyncio.get_event_loop().time()
            try:
                msg = await asyncio.wait_for(consumer.getone(), timeout=remaining)
            except asyncio.TimeoutError:
                return None
            if msg.value.get("user_id") == user_id:
                return msg.value
        return None
    finally:
        await consumer.stop()


async def _drain_websocket_until_idle(ws, idle_seconds: float = 2.0) -> None:
    """Read everything the server streams until it goes idle for `idle_seconds`."""
    while True:
        try:
            await asyncio.wait_for(ws.recv(), timeout=idle_seconds)
        except asyncio.TimeoutError:
            return
        except websockets.ConnectionClosed:
            return


async def run_hr_interview(user_id: str) -> dict | None:
    session_id = f"hr-{uuid.uuid4().hex[:8]}"
    token = make_token(user_id)
    url = f"{HR_WS_BASE}/interview/hr/{session_id}?token={token}&lang=en"

    print(f"[hr] Connecting to {HR_WS_BASE}/interview/hr/{session_id}", flush=True)

    # Start consumer BEFORE the conversation so it doesn't miss the event.
    consumer_task = asyncio.create_task(
        _consume_one("interview.hr.completed", user_id, TIMEOUT)
    )
    await asyncio.sleep(0.5)

    answers = [
        "Hi! I'm a backend engineer with 3 years of experience in Python and FastAPI.",
        "My biggest strength is debugging distributed systems under pressure.",
        "I'd like to move into a cloud architect role within the next two years.",
        "I prefer collaborative teams with clear ownership of services.",
        "Thanks, that's all I have today.",
    ]

    async with websockets.connect(url, max_size=2**20) as ws:
        # Initial greeting
        await _drain_websocket_until_idle(ws, idle_seconds=3.0)
        print("[hr] Greeting received", flush=True)

        for i, answer in enumerate(answers, 1):
            await ws.send(answer)
            await _drain_websocket_until_idle(ws, idle_seconds=3.0)
            print(f"[hr] Turn {i}/{len(answers)} done", flush=True)

    print("[hr] WS closed — waiting for interview.hr.completed event…", flush=True)
    return await consumer_task


async def run_tech_interview(user_id: str) -> dict | None:
    session_id = f"tech-{uuid.uuid4().hex[:8]}"
    token = make_token(user_id)
    url = (
        f"{TECH_WS_BASE}/interview/tech/{session_id}"
        f"?token={token}&lang=en&seniority=mid&skills=Python,FastAPI"
    )

    print(f"[tech] Connecting to {TECH_WS_BASE}/interview/tech/{session_id}", flush=True)

    consumer_task = asyncio.create_task(
        _consume_one("interview.tech.completed", user_id, TIMEOUT)
    )
    await asyncio.sleep(0.5)

    answers = [
        "Hello — ready for the technical interview.",
        "I'd use a sliding-window approach with O(n) time complexity.",
        "For the second problem I'd reach for a hash map keyed by frequency.",
        "Thanks, I'll stop here.",
    ]

    async with websockets.connect(url, max_size=2**20) as ws:
        await _drain_websocket_until_idle(ws, idle_seconds=3.0)
        print("[tech] Greeting received", flush=True)

        for i, answer in enumerate(answers, 1):
            await ws.send(answer)
            await _drain_websocket_until_idle(ws, idle_seconds=3.0)
            print(f"[tech] Turn {i}/{len(answers)} done", flush=True)

    print("[tech] WS closed — waiting for interview.tech.completed event…", flush=True)
    return await consumer_task


async def run() -> int:
    user_id = f"smoke-iv-{uuid.uuid4().hex[:8]}"
    print(f"[smoke] User ID: {user_id}", flush=True)

    # ---------- HR ----------
    hr_result = await run_hr_interview(user_id)
    if not hr_result:
        print("[hr] FAIL — no interview.hr.completed event received", flush=True)
        return 1

    print(
        f"[hr] PASS — score={hr_result.get('score')} reason={hr_result.get('reason')} "
        f"turns={hr_result.get('turn_count')}",
        flush=True,
    )
    assert hr_result.get("user_id") == user_id
    assert "session_id" in hr_result
    assert "transcript" in hr_result

    # ---------- TECH ----------
    tech_result = await run_tech_interview(user_id)
    if not tech_result:
        print("[tech] FAIL — no interview.tech.completed event received", flush=True)
        return 1

    print(
        f"[tech] PASS — score={tech_result.get('score')} reason={tech_result.get('reason')} "
        f"attempted={tech_result.get('problems_attempted')} passed={tech_result.get('problems_passed')}",
        flush=True,
    )
    assert tech_result.get("user_id") == user_id
    assert "session_id" in tech_result

    print("[smoke] INTERVIEW FLOW PASS", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
