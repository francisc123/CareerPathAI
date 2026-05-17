"""
Judge0 wrapper — submit code, poll for the result, return a structured dict.

Two deployment modes are supported, selected by env vars:

  • Self-host: JUDGE0_API_URL=http://judge0:2358   (no API key required)
  • RapidAPI:  JUDGE0_API_URL=https://judge0-ce.p.rapidapi.com
               JUDGE0_API_KEY=<your RapidAPI key>

The function never raises — failures are returned as a `TestResult` with
`status="error"` so the interview can keep going.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

_API_URL = os.getenv("JUDGE0_API_URL", "http://judge0:2358").rstrip("/")
_API_KEY = os.getenv("JUDGE0_API_KEY")
_TIMEOUT = httpx.Timeout(15.0)
_POLL_INTERVAL_SECONDS = 0.6
_MAX_POLL_SECONDS = 10.0

# Common language IDs (Judge0 CE 1.13+). Extend if you need more.
LANGUAGE_IDS: dict[str, int] = {
    "python": 71,
    "javascript": 63,
    "typescript": 74,
    "java": 62,
    "cpp": 54,
    "c": 50,
    "go": 60,
    "rust": 73,
    "csharp": 51,
}


@dataclass
class TestResult:
    status: str  # "accepted" | "wrong_answer" | "compile_error" | "runtime_error" | "timeout" | "error"
    stdout: str
    stderr: str
    compile_output: str
    time_seconds: float | None
    memory_kb: int | None
    raw_status_id: int | None = None


def _headers() -> dict[str, str]:
    base = {"Content-Type": "application/json"}
    if _API_KEY and "rapidapi" in _API_URL:
        base["X-RapidAPI-Key"] = _API_KEY
        base["X-RapidAPI-Host"] = _API_URL.replace("https://", "").replace("http://", "")
    return base


def _encode(value: str | None) -> str | None:
    if value is None:
        return None
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return ""


# Judge0 status IDs — https://github.com/judge0/judge0/blob/master/docs/statuses.md
_STATUS_MAP: dict[int, str] = {
    1: "in_queue",
    2: "processing",
    3: "accepted",
    4: "wrong_answer",
    5: "timeout",
    6: "compile_error",
    7: "runtime_error",
    8: "runtime_error",
    9: "runtime_error",
    10: "runtime_error",
    11: "runtime_error",
    12: "runtime_error",
    13: "error",
    14: "error",
}


async def _create_submission(
    client: httpx.AsyncClient,
    *,
    source_code: str,
    language_id: int,
    stdin: str | None,
) -> str | None:
    body = {
        "source_code": _encode(source_code),
        "language_id": language_id,
        "stdin": _encode(stdin),
        "redirect_stderr_to_stdout": False,
    }
    params = {"base64_encoded": "true", "wait": "false"}
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    ):
        with attempt:
            resp = await client.post(
                f"{_API_URL}/submissions", json=body, params=params
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("token")
    return None


async def _poll_submission(
    client: httpx.AsyncClient, token: str
) -> dict[str, Any] | None:
    deadline = asyncio.get_running_loop().time() + _MAX_POLL_SECONDS
    params = {"base64_encoded": "true", "fields": "*"}
    while asyncio.get_running_loop().time() < deadline:
        try:
            resp = await client.get(
                f"{_API_URL}/submissions/{token}", params=params
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Judge0 polling error for token %s.", token)
            return None
        data = resp.json()
        status_id = (data.get("status") or {}).get("id")
        if status_id and status_id > 2:  # not in_queue / processing
            return data
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
    logger.warning("Judge0 polling timeout for token %s.", token)
    return None


async def run_code(
    *,
    source_code: str,
    language: str,
    stdin: str | None = None,
) -> TestResult:
    """Submit code to Judge0 and wait for the result (capped at 10s)."""
    language_id = LANGUAGE_IDS.get(language.lower())
    if language_id is None:
        return TestResult(
            status="error",
            stdout="",
            stderr=f"Unsupported language: {language}",
            compile_output="",
            time_seconds=None,
            memory_kb=None,
        )

    headers = _headers()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=headers) as client:
            token = await _create_submission(
                client,
                source_code=source_code,
                language_id=language_id,
                stdin=stdin,
            )
            if not token:
                return TestResult(
                    status="error",
                    stdout="",
                    stderr="Judge0 did not return a token",
                    compile_output="",
                    time_seconds=None,
                    memory_kb=None,
                )

            data = await _poll_submission(client, token)
    except httpx.HTTPError as exc:
        logger.warning("Judge0 HTTP error: %s", exc)
        return TestResult(
            status="error",
            stdout="",
            stderr=f"Judge0 unreachable: {exc}",
            compile_output="",
            time_seconds=None,
            memory_kb=None,
        )

    if data is None:
        return TestResult(
            status="timeout",
            stdout="",
            stderr="Execution exceeded the 10s polling window",
            compile_output="",
            time_seconds=None,
            memory_kb=None,
        )

    status_id = (data.get("status") or {}).get("id")
    time_raw = data.get("time")
    try:
        time_seconds = float(time_raw) if time_raw is not None else None
    except (TypeError, ValueError):
        time_seconds = None

    return TestResult(
        status=_STATUS_MAP.get(int(status_id) if status_id is not None else -1, "error"),
        stdout=_decode(data.get("stdout")),
        stderr=_decode(data.get("stderr")),
        compile_output=_decode(data.get("compile_output")),
        time_seconds=time_seconds,
        memory_kb=data.get("memory"),
        raw_status_id=status_id,
    )
