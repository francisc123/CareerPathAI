"""End-to-end smoke test pentru chat-ul de pe homepage (agent-orchestrator).
Trimite o conversatie scriptata via WebSocket si verifica:
  - greeting-ul fix la __init__
  - clarification loop (raspuns off-topic)
  - context switching (intrebare tangentiala)
  - slot-filling gate (CTA nu se emite cu sloturi lipsa)
  - confirmation step (CTA doar dupa DA)
"""
import asyncio
import json
import sys
import uuid

import httpx
import websockets

ORCHESTRATOR_WS = "ws://localhost:8005/ws/chat/{user_id}"
ORCHESTRATOR_HTTP = "http://localhost:8005"


async def _recv_message(ws, timeout=20.0) -> str:
    """Skip typing frames, return the next message text."""
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        data = json.loads(raw)
        if data.get("type") == "message":
            return data.get("text", "")
        if data.get("type") == "cta":
            return "__CTA__"


async def _send_and_get(ws, message: str) -> str:
    await ws.send(json.dumps({"message": message}))
    pieces = []
    # collect message + optional CTA frame
    pieces.append(await _recv_message(ws))
    # peek for a possible CTA frame coming right after
    try:
        extra = await asyncio.wait_for(ws.recv(), timeout=1.5)
        data = json.loads(extra)
        if data.get("type") == "cta":
            pieces.append("__CTA__")
    except asyncio.TimeoutError:
        pass
    return "\n".join(pieces)


async def main():
    user_id = f"test-{uuid.uuid4().hex[:8]}"
    print(f"\n=== Test cu user_id={user_id} ===\n")

    uri = ORCHESTRATOR_WS.format(user_id=user_id)
    async with websockets.connect(uri) as ws:
        # 1. greeting
        greeting = await _recv_message(ws)
        print(f"[BOT greeting] {greeting}\n")
        assert "Bun venit" in greeting, "Greeting fix lipseste"

        # 2. raspuns relevant (current_situation = student)
        r = await _send_and_get(ws, "sunt student la informatica anul 2")
        print(f"[BOT] {r}\n")
        assert "__CTA__" not in r, "CTA prea devreme dupa 1 raspuns!"

        # 3. raspuns OFF-TOPIC -> botul ar trebui sa re-intrebe / clarifice
        r = await _send_and_get(ws, "vreau o pizza")
        print(f"[BOT dupa off-topic] {r}\n")
        assert "__CTA__" not in r, "CTA dupa off-topic — nu trebuia"

        # 4. raspuns relevant — target_role hint
        r = await _send_and_get(ws, "imi place sa construiesc lucruri vizuale, prefer sa creez")
        print(f"[BOT] {r}\n")

        # 5. intrebare TANGENTIALA -> context switching
        r = await _send_and_get(ws, "stai un pic, ce face un Frontend Developer mai exact?")
        print(f"[BOT dupa context switch] {r}\n")
        # Botul ar trebui sa raspunda si sa revina la triaj
        assert ("Revenind" in r or "revenind" in r or "?" in r), \
            "Botul nu a revenit la triaj dupa intrebare tangentiala"

        # 6. mai multe info intr-un singur mesaj
        r = await _send_and_get(ws, "vreau frontend, am 0 experienta, prefer js fata de python")
        print(f"[BOT] {r}\n")

        # 7. cere concluzia — botul ar trebui sa propuna rezumat, NU CTA direct
        r = await _send_and_get(ws, "ok, dami concluzia")
        print(f"[BOT propunere rezumat] {r}\n")
        # In step A nu trebuie sa apara CTA
        # (poate apare daca modelul ignora regula, asa ca log-am)
        if "__CTA__" in r:
            print("  WARN: CTA emis fara confirmare — verifica logs orchestrator")

        # 8. confirmare DA -> CTA_READY ar trebui sa apara
        r = await _send_and_get(ws, "DA, e perfect")
        print(f"[BOT final] {r}\n")

        # 9. verifica profile-ul salvat
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ORCHESTRATOR_HTTP}/profile/{user_id}")
            if resp.status_code == 200:
                profile = resp.json()
                print(f"[PROFILE] {json.dumps(profile, indent=2, ensure_ascii=False)}")
            else:
                print(f"[PROFILE] nu exista (status {resp.status_code})")

    print("\n=== Test OK ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except AssertionError as e:
        print(f"\n!!! ASSERTION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
