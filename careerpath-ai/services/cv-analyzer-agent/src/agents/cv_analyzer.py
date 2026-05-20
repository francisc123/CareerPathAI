import json
import logging
import os
import time
from pydantic import BaseModel, ValidationError
from google.genai import types

from src.config.gemini_client import get_gemini_client
from src.rag.embedding_tool import generate_embedding
from src.rag.qdrant_client import save_cv_embedding

logger = logging.getLogger(__name__)

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")


def _load_prompt(filename: str) -> str:
    path = os.path.join(_PROMPTS_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error("Fișier prompt negăsit: %s", path)
        raise


SCORING_PROMPT = _load_prompt("cv_scoring.txt")
GAP_ANALYSIS_PROMPT = _load_prompt("gap_analysis.txt")


# --- SCHEME PYDANTIC ---

class ScoreBreakdown(BaseModel):
    experience: int
    skill_stack: int
    projects: int
    education: int
    certifications: int


class CVAnalysisResult(BaseModel):
    score: int
    seniority: str
    target_role: str
    skills: list[str]
    strengths: list[str]
    gaps: list[str]
    career_roadmap: list[str] = []  # exactly 3 platform-native action items; default keeps old transcripts loadable
    score_breakdown: ScoreBreakdown


class PriorityGap(BaseModel):
    skill: str
    reason: str
    market_demand: str
    suggested_resource: str


class GapAnalysisResult(BaseModel):
    gaps: list[str]
    priority_gaps: list[PriorityGap]
    estimated_weeks_to_close: int
    learning_order: list[str]


# --- HELPER ---

def _call_gemini_with_retry(system_prompt: str, user_content: str, schema: type, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = get_gemini_client().models.generate_content(
                model="gemini-2.5-flash",
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            return schema(**json.loads(response.text or "{}"))
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("Validare eșuată (încercarea %d/%d): %s", attempt + 1, max_retries, e)
            time.sleep(2)
        except Exception as e:
            logger.error("Eroare API Gemini (încercarea %d/%d): %s", attempt + 1, max_retries, e)
            time.sleep(5)
    raise RuntimeError(f"Nu am obținut răspuns valid după {max_retries} încercări.")


# --- PIPELINE PRINCIPAL ---

def process_cv_pipeline(cv_text: str, user_id: str) -> dict:
    logger.info("Încep procesarea CV-ului pentru user: %s", user_id)

    # PASUL A: Scoring și structurare cu Gemini
    analiza: CVAnalysisResult = _call_gemini_with_retry(
        system_prompt=SCORING_PROMPT,
        user_content=f"CV TEXT:\n{cv_text}",
        schema=CVAnalysisResult,
    )
    logger.info("Analiză validată: score=%d, seniority=%s", analiza.score, analiza.seniority)

    # PASUL B: Gap analysis detaliat — doar pentru candidații cu scor < 70
    gap_details: GapAnalysisResult | None = None
    if analiza.score < 70:
        gap_input = json.dumps({
            "cv_score": analiza.score,
            "seniority": analiza.seniority,
            "skills": analiza.skills,
            "target_role": analiza.target_role,
        })
        gap_details = _call_gemini_with_retry(
            system_prompt=GAP_ANALYSIS_PROMPT,
            user_content=gap_input,
            schema=GapAnalysisResult,
        )
        logger.info("Gap analysis completat: %d gap-uri prioritare", len(gap_details.priority_gaps))

    # PASUL C: Generare embedding
    vector = generate_embedding(cv_text)
    logger.info("Vector generat: %d dimensiuni", len(vector))

    # PASUL D: Salvare în Qdrant
    save_cv_embedding(user_id=user_id, vector=vector, payload=analiza.model_dump())

    # PASUL E: Compune evenimentul final pentru Redpanda
    result = {
        "user_id": user_id,
        "status": "success",
        "score": analiza.score,
        "seniority": analiza.seniority,
        "target_role": analiza.target_role,
        "skills_extracted": analiza.skills,
        "strengths": analiza.strengths,
        "gaps": analiza.gaps,
        "gaps_identified": analiza.gaps,
        "career_roadmap": analiza.career_roadmap,
        "score_breakdown": analiza.score_breakdown.model_dump(),
    }

    if gap_details:
        result["priority_gaps"] = [g.model_dump() for g in gap_details.priority_gaps]
        result["estimated_weeks_to_close"] = gap_details.estimated_weeks_to_close
        result["learning_order"] = gap_details.learning_order

    logger.info("Pipeline completat pentru user: %s", user_id)
    return result
