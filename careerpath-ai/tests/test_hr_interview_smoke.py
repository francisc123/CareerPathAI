"""Smoke test pentru HR interview agent.
Genereaza un JWT semnat cu private.pem, se conecteaza pe WebSocket si
verifica ca primeste greeting + cel putin un raspuns AI.
"""
import asyncio
import json
import sys
import time
import uuid

import websockets
from jose import jwt

HR_WS = "ws://localhost:8009/interview/hr/{session_id}?token={token}&lang=en"


def make_token() -> str:
    with open("keys/private.pem") as f:
        priv = f.read()
    return jwt.encode(
        {"sub": "demo-hr-001", "iat": int(time.time()), "exp": int(time.time()) + 3600},
        priv,
        algorithm="RS256",
    )


async def main():
    session_id = f"hr-{uuid.uuid4().hex[:6]}"
    token = make_token()
    uri = HR_WS.format(session_id=session_id, token=token)
    print(f"Connecting to {uri[:80]}...")

    async with websockets.connect(uri) as ws:
        # Greeting
        greeting = await asyncio.wait_for(ws.recv(), timeout=15)
        print(f"[HR greeting] {greeting[:200]}")
        assert greeting, "Empty greeting"

        # Trimitem un raspuns scurt
        await ws.send("Hi! I'm a junior backend developer with 1 year experience.")

        # Asteptam chunk-uri streaming
        collected = []
        deadline = asyncio.get_event_loop().time() + 30
        while asyncio.get_event_loop().time() < deadline:
            try:
                chunk = await asyncio.wait_for(ws.recv(), timeout=5)
                collected.append(chunk)
                print(f"[HR chunk] {chunk[:120]}")
                if len(collected) >= 3:
                    break
            except asyncio.TimeoutError:
                break

        assert collected, "Nu am primit niciun raspuns de la HR agent"
        print(f"\n=== HR smoke OK: {len(collected)} chunk-uri ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except AssertionError as e:
        print(f"!!! FAIL: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"!!! UNEXPECTED: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
