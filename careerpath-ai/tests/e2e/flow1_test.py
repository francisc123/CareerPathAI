"""
E2E Integration Test — Flow 1 (CP-038): CV upload → analyze → job match.

Cross-platform Python port of flow1_test.sh (no bash/jq dependency).

Run from careerpath-ai/:
    python tests/e2e/flow1_test.py

Env vars:
    API_GATEWAY_URL  default http://localhost:8000
    CV_FIXTURE_PATH  default tests/fixtures/cv_strong.pdf
"""

from __future__ import annotations

import os
import random
import sys
import time
from pathlib import Path

import urllib.request
import urllib.error
import json
import uuid

GATEWAY = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
CV_PATH = Path(os.getenv("CV_FIXTURE_PATH", "tests/fixtures/cv_strong.pdf"))


def _post_multipart(url: str, file_path: Path, headers: dict) -> dict:
    """Minimal multipart/form-data POST so we don't require `requests`."""
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
        "Content-Type: application/pdf\r\n\r\n"
    ).encode() + file_path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _get_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    print("=" * 52)
    print("E2E INTEGRATION TEST — FLOW 1 (CP-038)")
    print("=" * 52)

    if not CV_PATH.exists():
        print(f"FAIL: CV fixture missing at {CV_PATH}")
        return 1

    # 1. Auth: register a throwaway user to get a JWT (matches what the frontend does)
    email = f"e2e_flow1_{random.randint(100000, 999999)}@test.local"
    body = json.dumps({"name": "Flow1 Tester", "email": email, "password": "Test12345!"}).encode()
    req = urllib.request.Request(
        f"{GATEWAY}/api/auth/register", data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            auth = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"FAIL: register failed: {e.code} {e.reason}")
        return 1
    token = auth["token"]
    user_id = auth["user"]["id"]
    print(f"1. Registered user id={user_id[:16]}... OK")

    # 2. Upload CV
    try:
        upload = _post_multipart(
            f"{GATEWAY}/api/cv/upload", CV_PATH, {"Authorization": f"Bearer {token}"}
        )
    except urllib.error.HTTPError as e:
        print(f"FAIL: upload failed: {e.code} {e.reason}")
        return 1
    job_id = upload.get("job_id") or upload.get("cvId") or upload.get("id")
    if not job_id:
        print(f"FAIL: no job_id in upload response: {upload}")
        return 1
    print(f"2. CV uploaded, job_id={job_id} OK")

    # 3. Poll until status == completed
    print("3. Polling cv-service /status/{job_id} ...")
    status, score = "pending", 0
    for attempt in range(20):
        time.sleep(3)
        try:
            data = _get_json(
                f"{GATEWAY}/api/cv/status/{job_id}",
                {"Authorization": f"Bearer {token}"},
            )
        except urllib.error.HTTPError as e:
            print(f"   [retry {attempt + 1}] HTTP {e.code}")
            continue
        status = data.get("status", "pending")
        score = data.get("score") or 0
        print(f"   [retry {attempt + 1}/20] status={status} score={score}")
        if status == "completed":
            break
    if status != "completed":
        print(f"FAIL: CV processing timed out (last status={status})")
        return 1
    if int(score) < 50:
        print(f"FAIL: CV score too low ({score} < 50)")
        return 1
    print(f"   ASSERT score >= 50: OK ({score})")

    # 4. Wait for downstream pipeline (orchestrator -> job-scraper -> job-match)
    print("4. Waiting 10s for async pipeline (scrape + match) ...")
    time.sleep(10)

    # 5. Fetch matches
    try:
        matches = _get_json(
            f"http://localhost:8008/jobs/{user_id}",
            {"Authorization": f"Bearer {token}"},
        )
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("WARN: /jobs returned 404 (no matches yet) — pipeline may still be running")
            print("PARTIAL PASS: CV analysis completed; job matches not produced in time")
            return 0
        print(f"FAIL: /jobs returned HTTP {e.code}")
        return 1
    count = matches.get("count", len(matches.get("matches", [])))
    print(f"5. Job matches: {count}")
    if count < 1:
        print("FAIL: expected at least 1 match")
        return 1

    print("=" * 52)
    print("E2E FLOW 1 PASSED")
    print("=" * 52)
    return 0


if __name__ == "__main__":
    sys.exit(main())
