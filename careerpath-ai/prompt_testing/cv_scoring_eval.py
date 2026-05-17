"""
CP-042 — CV scoring stability evaluation.

Runs each sample CV through Gemini N times and reports the standard deviation
of the returned `score`. Passes if every sample has stddev <= MAX_STDDEV.

Usage (from `careerpath-ai/`):
    python prompt_testing/cv_scoring_eval.py
    python prompt_testing/cv_scoring_eval.py --runs 5 --max-stddev 3.0
    python prompt_testing/cv_scoring_eval.py --samples-dir prompt_testing/samples

Exit code 0 if all samples pass, 1 otherwise (so it can be wired into CI).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Ensure UTF-8 for the Windows console when run locally.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cv_scoring_eval")

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = REPO_ROOT / "services" / "cv-analyzer-agent" / "prompts" / "cv_scoring.txt"

# Default in-script samples mirror prompt_testing/cv_scoring.py so the eval
# always has something to run even when prompt_testing/samples/ is empty.
DEFAULT_SAMPLES: dict[str, str] = {
    "junior": (
        "Ana Popescu\nStudent an 3, Facultatea de Matematica-Informatica\n"
        "Skills: Python, HTML, CSS, JavaScript, Git\n"
        "Proiecte: To-Do List, BMI Calculator (Python)\n"
        "Experienta: stagiu 2 luni WordPress"
    ),
    "mid": (
        "Rares Constantinescu\nPython Developer — 2 ani experienta\n"
        "Skills: Python, FastAPI, PostgreSQL, Docker\n"
        "Proiecte: API REST pentru platforma e-commerce (500 useri activi)"
    ),
    "senior": (
        "Mihai Ionescu\nSenior Software Engineer — 9 ani experienta\n"
        "Skills: Python, Go, Kubernetes, AWS, Terraform, PostgreSQL, Redis, Kafka\n"
        "Experienta: Tech Lead startup fintech (6 dev), Senior Engineer SaaS\n"
        "Certificari: AWS SAP, CKA"
    ),
    "career_changer": (
        "Elena Dumitrescu\nFost profesor matematica, reconversie IT — 8 luni\n"
        "Cursuri: Python for Everybody, CS50, SQL Bootcamp\n"
        "Skills: Python, SQL, pandas, matplotlib"
    ),
    "bootcamp": (
        "Andrei Marin\nBootcamp FullStack JS — 4 luni\n"
        "Skills: JS, TS, React, Node, Express, MongoDB, Tailwind\n"
        "Proiecte: Blogging platform, real-time task app, Trello clone"
    ),
}


@dataclass
class SampleResult:
    name: str
    scores: list[int]
    mean: float
    stddev: float
    passed: bool


def _load_samples(samples_dir: Path | None) -> dict[str, str]:
    if samples_dir is None or not samples_dir.is_dir():
        logger.info("No samples directory — using built-in samples.")
        return dict(DEFAULT_SAMPLES)

    samples: dict[str, str] = {}
    for path in sorted(samples_dir.glob("*.txt")):
        samples[path.stem] = path.read_text(encoding="utf-8").strip()
    if not samples:
        logger.info("Samples directory is empty — falling back to built-in samples.")
        return dict(DEFAULT_SAMPLES)
    return samples


def _extract_score(raw_text: str) -> int | None:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw_text or "").strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Non-JSON response: %s", raw_text[:200])
        return None
    score = data.get("score")
    if isinstance(score, int) and 0 <= score <= 100:
        return score
    logger.warning("Invalid score in response: %r", score)
    return None


async def _score_once(
    client: genai.Client, system_prompt: str, cv_text: str
) -> int | None:
    """One Gemini call. Returns the integer score or None on failure."""
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=f"{system_prompt}\n\nCV TEXT:\n{cv_text}",
    )
    return _extract_score(response.text or "")


async def _evaluate_sample(
    client: genai.Client,
    system_prompt: str,
    name: str,
    cv_text: str,
    runs: int,
    max_stddev: float,
) -> SampleResult:
    coros = [_score_once(client, system_prompt, cv_text) for _ in range(runs)]
    results = await asyncio.gather(*coros, return_exceptions=True)

    scores: list[int] = []
    for r in results:
        if isinstance(r, int):
            scores.append(r)
        elif isinstance(r, Exception):
            logger.warning("Gemini call raised for %s: %s", name, r)

    if len(scores) < 2:
        return SampleResult(name=name, scores=scores, mean=0.0, stddev=float("inf"), passed=False)

    mean = statistics.fmean(scores)
    stddev = statistics.stdev(scores)
    passed = stddev <= max_stddev
    return SampleResult(name=name, scores=scores, mean=mean, stddev=stddev, passed=passed)


def _print_report(results: list[SampleResult], max_stddev: float, runs: int) -> None:
    print("\n" + "=" * 78)
    print(f"CV SCORING STABILITY  ({runs} runs/sample, pass threshold stddev <= {max_stddev})")
    print("=" * 78)
    print(f"{'Sample':<24}{'Runs':<6}{'Mean':<10}{'StdDev':<10}{'Scores':<24}Status")
    print("-" * 78)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        scores_str = ",".join(str(s) for s in r.scores) or "—"
        print(
            f"{r.name:<24}{len(r.scores):<6}{r.mean:<10.2f}{r.stddev:<10.2f}"
            f"{scores_str:<24}{status}"
        )
    print("=" * 78)
    passed_count = sum(1 for r in results if r.passed)
    print(f"OVERALL: {passed_count}/{len(results)} samples passed.")


async def main_async(args: argparse.Namespace) -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set. Cannot run eval.", file=sys.stderr)
        return 2

    if not PROMPT_PATH.is_file():
        print(f"ERROR: prompt file not found at {PROMPT_PATH}", file=sys.stderr)
        return 2

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    samples = _load_samples(Path(args.samples_dir) if args.samples_dir else None)

    client = genai.Client(api_key=api_key)
    results: list[SampleResult] = []
    for name, cv_text in samples.items():
        result = await _evaluate_sample(
            client, system_prompt, name, cv_text, args.runs, args.max_stddev
        )
        results.append(result)

    _print_report(results, args.max_stddev, args.runs)
    return 0 if all(r.passed for r in results) else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CV scoring stability eval (CP-042).")
    parser.add_argument("--runs", type=int, default=3, help="Runs per sample (default: 3)")
    parser.add_argument(
        "--max-stddev",
        type=float,
        default=3.0,
        help="Maximum acceptable score stddev per sample (default: 3.0)",
    )
    parser.add_argument(
        "--samples-dir",
        default=None,
        help="Directory containing .txt CV samples (one per file). If empty, uses built-ins.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    exit_code = asyncio.run(main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
