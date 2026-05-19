"""Validare cap-coadă WS prin api-gateway pentru HR + Tech + Chat orchestrator.
Generează JWT-uri RS256, deschide WS prin gateway (ws://localhost:8000/ws/...),
așteaptă greeting + minim un răspuns. Raport scurt la sfârșit.
"""
import asyncio
import json
import sys
import time
import uuid

import websockets
from jose import jwt

WITH_KEY = "keys/private.pem"
GATEWAY_WS = "ws://localhost:8000"
ORCHESTRATOR_DIRECT_WS = "ws://localhost:8005"  # chat e direct la orchestrator


def make_token(sub: str) -> str:
    with open(WITH_KEY) as f:
        priv = f.read()
    return jwt.encode(
        {"sub": sub, "iat": int(time.time()), "exp": int(time.time()) + 3600},
        priv,
        algorithm="RS256",
    )


async def test_hr() -> str:
    token = make_token("test-hr-e2e")
    session_id = f"hr-{uuid.uuid4().hex[:6]}"
    uri = f"{GATEWAY_WS}/ws/hr-interview/{session_id}?token={token}&lang=en"
    try:
        async with websockets.connect(uri, open_timeout=10) as ws:
            greeting = await asyncio.wait_for(ws.recv(), timeout=15)
            await ws.send("Hi, I'm a junior backend dev with 1 yr Python.")
            try:
                reply = await asyncio.wait_for(ws.recv(), timeout=45)
            except asyncio.TimeoutError:
                return f"PARTIAL (greeting={greeting[:60]!r}, no AI reply in 45s)"
            return f"OK greeting={greeting[:60]!r} reply={str(reply)[:80]!r}"
    except Exception as e:
        return f"FAIL: {type(e).__name__}: {e}"


async def test_tech() -> str:
    token = make_token("test-tech-e2e")
    session_id = f"tech-{uuid.uuid4().hex[:6]}"
    uri = f"{GATEWAY_WS}/ws/tech-interview/{session_id}?token={token}&lang=en"
    try:
        async with websockets.connect(uri, open_timeout=10) as ws:
            greeting = await asyncio.wait_for(ws.recv(), timeout=15)
            await ws.send("I know Python, Django, REST APIs.")
            try:
                reply = await asyncio.wait_for(ws.recv(), timeout=45)
            except asyncio.TimeoutError:
                return f"PARTIAL (greeting={greeting[:60]!r}, no AI reply in 45s)"
            return f"OK greeting={greeting[:60]!r} reply={str(reply)[:80]!r}"
    except Exception as e:
        return f"FAIL: {type(e).__name__}: {e}"


async def test_chat() -> str:
    user_id = "test-chat-e2e"
    uri = f"{ORCHESTRATOR_DIRECT_WS}/ws/chat/{user_id}"
    try:
        async with websockets.connect(uri, open_timeout=10) as ws:
            await ws.send(json.dumps({"type": "user_message", "content": "Hi, what can you do?"}))
            collected = []
            deadline = asyncio.get_event_loop().time() + 30
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10)
                    collected.append(msg)
                    if len(collected) >= 2:
                        break
                except asyncio.TimeoutError:
                    break
            if not collected:
                return "FAIL: no response in 30s"
            return f"OK {len(collected)} msgs, first={str(collected[0])[:80]!r}"
    except Exception as e:
        return f"FAIL: {type(e).__name__}: {e}"


async def main():
    results = await asyncio.gather(test_hr(), test_tech(), test_chat())
    print("\n=== AGENT WS VALIDATION ===")
    for name, res in zip(["HR interview ", "Tech interview", "Chat orchestr."], results):
        print(f"{name}: {res}")


if __name__ == "__main__":
    asyncio.run(main())
