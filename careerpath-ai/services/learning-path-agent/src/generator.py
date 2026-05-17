import asyncio
import json
import logging
from typing import List

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from .config import GEMINI_API_KEY
from .integrations.udemy import search_courses as udemy_search_courses
from .integrations.youtube import search_videos as youtube_search_videos
from .prompts import LEARNING_PATH_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def get_gemini_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


class Resource(BaseModel):
    type: str = Field(..., description="Type: 'video', 'article', 'course', or 'docs'")
    title: str
    url: str


class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_index: int


class Module(BaseModel):
    module_title: str
    description: str
    resources: List[Resource]
    quiz: List[QuizQuestion]


class WeeklyPlan(BaseModel):
    week: int
    theme: str
    modules: List[Module]


class LearningPath(BaseModel):
    title: str
    estimated_weeks: int
    weekly_plan: List[WeeklyPlan]


# ---------- Resource enrichment ---------- #

_MAX_CONCURRENT_LOOKUPS = 4


async def _fetch_real_resources(module_title: str) -> list[dict]:
    """
    Run Udemy + YouTube concurrently, merge their hits. Both return [] when
    creds are missing or on transient errors, so the caller gets a possibly
    empty list to combine with Gemini's fallback resources.
    """
    udemy_task = asyncio.create_task(udemy_search_courses(module_title, max_results=1))
    youtube_task = asyncio.create_task(youtube_search_videos(module_title, max_results=2))
    udemy_hits, youtube_hits = await asyncio.gather(
        udemy_task, youtube_task, return_exceptions=False
    )
    return list(udemy_hits) + list(youtube_hits)


def _placeholder_resource(module_title: str) -> dict:
    """Last-resort link so the UI never renders an empty resources list."""
    encoded = module_title.replace(" ", "+")
    return {
        "type": "video",
        "title": f"Search YouTube for: {module_title}",
        "url": f"https://www.youtube.com/results?search_query={encoded}",
    }


def _dedupe_resources(resources: list[dict]) -> list[dict]:
    seen_urls: set[str] = set()
    deduped: list[dict] = []
    for resource in resources:
        url = (resource.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(resource)
    return deduped


async def _enrich_modules_with_real_links(path: LearningPath) -> LearningPath:
    """
    For each module: pull real Udemy + YouTube hits, merge them ahead of
    Gemini's (possibly hallucinated) resources, dedupe by URL, ensure at
    least one link exists.

    Concurrency is bounded so we don't open hundreds of sockets for a
    large plan.
    """
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_LOOKUPS)

    async def enrich_one(module: Module) -> None:
        async with semaphore:
            real_links = await _fetch_real_resources(module.module_title)

        gemini_links = [r.model_dump() for r in module.resources]
        # Prefer real-API hits; keep Gemini's links as fallback after dedupe.
        merged = _dedupe_resources(real_links + gemini_links)
        if not merged:
            merged = [_placeholder_resource(module.module_title)]

        module.resources = [Resource(**r) for r in merged]

    tasks = [
        enrich_one(module)
        for week in path.weekly_plan
        for module in week.modules
    ]
    if tasks:
        await asyncio.gather(*tasks)
    return path


# ---------- Public API ---------- #


async def generate_learning_path_structure(
    gaps: list[str],
    target_role: str,
    difficulty_hint: str | None = None,
) -> str | None:
    """
    Generates a structured learning path using Gemini with JSON output mode,
    then enriches each module's `resources` with real Udemy + YouTube links.

    `difficulty_hint`: "easier" | "steady" | "harder" — derived from the user's
    recent quiz performance (see `database.get_user_difficulty_signal`). Steers
    the model to calibrate depth/pace without changing schema.

    Returns a JSON string conforming to the LearningPath schema, or None on
    irrecoverable error.
    """
    from .prompts import DIFFICULTY_HINT_INSTRUCTIONS

    hint_block = DIFFICULTY_HINT_INSTRUCTIONS.get(difficulty_hint or "steady", "")
    logger.info(
        "Generating learning path for role '%s' with %d gaps (difficulty=%s)",
        target_role, len(gaps), difficulty_hint or "steady",
    )
    user_content = (
        f"Target Role: {target_role}\nSkill Gaps: {', '.join(gaps)}"
        + (f"\n\n{hint_block}" if hint_block else "")
    )

    try:
        response = await asyncio.to_thread(
            get_gemini_client().models.generate_content,
            model="gemini-2.5-flash",
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=LEARNING_PATH_SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
        path_data = json.loads(response.text)
        validated = LearningPath(**path_data)
        logger.info("Gemini structure validated for '%s'.", target_role)
    except Exception as exc:
        logger.error("Error generating learning path skeleton: %s", exc)
        return None

    try:
        enriched = await _enrich_modules_with_real_links(validated)
    except Exception:
        logger.exception("Resource enrichment failed — returning Gemini-only plan.")
        enriched = validated

    return enriched.model_dump_json()
