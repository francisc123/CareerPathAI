import json
import logging
from pydantic import BaseModel, Field
from typing import List
from google import genai
from google.genai import types
from .config import GEMINI_API_KEY
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


class Module(BaseModel):
    module_title: str
    description: str
    resources: List[Resource]


class WeeklyPlan(BaseModel):
    week: int
    theme: str
    modules: List[Module]


class LearningPath(BaseModel):
    title: str
    estimated_weeks: int
    weekly_plan: List[WeeklyPlan]


async def generate_learning_path_structure(gaps: list[str], target_role: str) -> str | None:
    """
    Generates a structured learning path using Gemini with JSON output mode.
    Returns a JSON string conforming to the LearningPath schema.
    """
    logger.info("Generating learning path for role '%s' with %d gaps", target_role, len(gaps))
    user_content = f"Target Role: {target_role}\nSkill Gaps: {', '.join(gaps)}"

    try:
        response = get_gemini_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=LEARNING_PATH_SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
        path_data = json.loads(response.text)
        validated = LearningPath(**path_data)
        logger.info("Successfully generated learning path for '%s'", target_role)
        return validated.model_dump_json()
    except Exception as e:
        logger.error("Error generating learning path: %s", e)
        return None
