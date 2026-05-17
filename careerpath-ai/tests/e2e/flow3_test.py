"""
CP-043 — End-to-end test for Flow 3 (Interview).

What it covers:
  1. Mints a short-lived RS256 JWT signed with `keys/private.pem`
     (so we don't need user-service running for the test).
  2. Opens a WS to hr-interview-agent, sends ~3 chat turns, then disconnects
     to trigger post-interview analysis.
  3. Polls Postgres until an `interview_sessions` row of type 'HR' appears for
     the test user.
  4. Opens a WS to technical-interview-agent, waits for the seeded problem,
     submits a Python solution, waits for `test_results`, then disconnects.
  5. Polls Postgres until an `interview_sessions` row of type 'Technical'
     appears.

Run from `careerpath-ai/` after `make up`:
    python tests/e2e/flow3_test.py
    python tests/e2e/flow3_test.py --hr-url ws://localhost:8009 --tech-url ws://localhost:8010

Exit code 0 on success, non-zero on any failure.

Notes:
  • Judge0 needs to be reachable for the tech submission to actually compile.
    If JUDGE0_API_URL is unreachable, the test still passes provided the agent
    publishes test_results with status="error" (which is the expected behaviour).
  • Requires the `pyjwt` (or `python-jose`), `websockets`, `httpx`, and `asyncpg`
    packages in the runner's environment.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import asyncpg
from jose import jwt

from helpers.ws_client import collect_until, connect_ws, expect_event, send_json

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("flow3_test")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRIVATE_KEY = REPO_ROOT / "keys" / "private.pem"

HR_CHAT_TURNS = [
    "Hi Alex! I'm Rareș, glad to be here.",
    "Sure — I'm a backend dev with about 2 years building event-driven systems.",
    "One challenge: a Kafka consumer was double-processing on rebalances. "
    "I added idempotency keys and offset commits after side effects.",
]

PYTHON_SOLUTION = """\
import sys

def main():
    data = sys.stdin.read().split()
    print(sum(int(x) for x in data))

if __name__ == "__main__":
    main()
"""


def _mint_jwt(user_id: str, private_key_path: Path) -> str:
    if not private_key_path.is_file():
        raise SystemExit(
            f"Private key not found at {private_key_path}. Run `make keys` first."
        )
    private_key = private_key_path.read_text(encoding="utf-8")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


async def _wait_for_interview_row(
    dsn: str, user_id: str, interview_type: str, *, timeout: float = 30.0
) -> dict:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        try:
            conn = await asyncpg.connect(dsn)
            try:
                row = await conn.fetchrow(
                    "SELECT id, score, feedback FROM interview_sessions "
                    "WHERE user_id = $1 AND type = $2 "
                    "ORDER BY completed_at DESC LIMIT 1",
                    user_id,
                    interview_type,
                )
            finally:
                await conn.close()
            if row:
                return dict(row)
        except Exception as exc:
            logger.warning("DB poll failed: %s", exc)
        if asyncio.get_running_loop().time() >= deadline:
            raise TimeoutError(
                f"No {interview_type} interview row for user {user_id} after {timeout}s"
            )
        await asyncio.sleep(1.0)


async def _run_hr(hr_url: str, token: str, user_id: str, dsn: str) -> None:
    session_id = str(uuid.uuid4())
    url = f"{hr_url}/interview/hr/{session_id}?token={token}"

    async with connect_ws(url) as ws:
        # Greeting should arrive (plain text in HR agent).
        first = await ws.recv()
        logger.info("HR greeting: %s", str(first)[:80])

        for turn_text in HR_CHAT_TURNS:
            await ws.send(turn_text)
            # Drain reply tokens until the model goes quiet (~1.5s gap).
            try:
                while True:
                    await asyncio.wait_for(ws.recv(), timeout=1.5)
            except asyncio.TimeoutError:
                pass

    logger.info("HR session %s disconnected — waiting for DB row.", session_id)
    row = await _wait_for_interview_row(dsn, user_id, "HR")
    logger.info("HR interview persisted: score=%s", row.get("score"))


async def _run_tech(tech_url: str, token: str, user_id: str, dsn: str) -> None:
    session_id = str(uuid.uuid4())
    url = (
        f"{tech_url}/interview/tech/{session_id}"
        f"?token={token}&seniority=mid&skills=python,kafka"
    )

    async with connect_ws(url) as ws:
        # Discard the init chat_done + greeting + initial chat_delta.
        await collect_until(
            ws,
            lambda m: isinstance(m, dict) and m.get("type") == "problem",
            timeout=30.0,
        )
        logger.info("Tech: first problem received.")

        await send_json(
            ws,
            {
                "type": "code_submission",
                "content": PYTHON_SOLUTION,
                "language": "python",
            },
        )

        results = await expect_event(ws, "test_results", timeout=20.0)
        logger.info("Tech submission graded: %s", json.dumps(results)[:160])

    logger.info("Tech session %s disconnected — waiting for DB row.", session_id)
    row = await _wait_for_interview_row(dsn, user_id, "Technical")
    logger.info("Tech interview persisted: score=%s", row.get("score"))


async def main_async(args: argparse.Namespace) -> int:
    private_key = Path(args.private_key)
    user_id = args.user_id or f"e2e-{uuid.uuid4()}"
    token = _mint_jwt(user_id, private_key)

    logger.info("Test user: %s", user_id)

    try:
        await _run_hr(args.hr_url, token, user_id, args.dsn)
    except Exception:
        logger.exception("HR flow failed.")
        return 1

    try:
        await _run_tech(args.tech_url, token, user_id, args.dsn)
    except Exception:
        logger.exception("Tech flow failed.")
        return 2

    logger.info("✅ Flow 3 e2e test PASSED for user %s.", user_id)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CP-043 — Flow 3 e2e test.")
    parser.add_argument("--hr-url", default=os.getenv("HR_WS_URL", "ws://localhost:8009"))
    parser.add_argument("--tech-url", default=os.getenv("TECH_WS_URL", "ws://localhost:8010"))
    parser.add_argument(
        "--dsn",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql://careerpath_user:change_me_strong_password@localhost:5432/careerpath",
        ),
    )
    parser.add_argument(
        "--private-key",
        default=str(DEFAULT_PRIVATE_KEY),
        help="Path to keys/private.pem used to mint the test JWT.",
    )
    parser.add_argument(
        "--user-id",
        default=None,
        help="Override the test user_id (default: generated UUID).",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    code = asyncio.run(main_async(args))
    sys.exit(code)


if __name__ == "__main__":
    main()
