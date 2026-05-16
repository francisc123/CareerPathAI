import json
import logging
import asyncio

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, RERANK_MODEL_NAME
from .prompts import (
    RERANK_SYSTEM_PROMPT, get_rerank_user_prompt,
    COVER_LETTER_SYSTEM_PROMPT, get_cover_letter_user_prompt
)

from .qdrant_service import get_cv_details, find_similar_jobs

logger = logging.getLogger(__name__)

from typing import Optional

_client: Optional[genai.Client] = None

def get_gemini_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Transformă descrierile joburilor în vectori folosind Gemini."""
    try:
        response = get_gemini_client().models.embed_content(
            model="text-embedding-004",
            contents=texts
        )
        return [emb.values for emb in response.embeddings]
    except Exception as e:
        logger.error("Error generating embeddings: %s", e)
        return []

async def generate_cover_letter(cv_text: str, job: dict) -> str:
    """Generates a cover letter for a matched job using Gemini."""
    user_prompt = get_cover_letter_user_prompt(cv_text, job)
    try:
        response = get_gemini_client().models.generate_content(
            model=RERANK_MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=COVER_LETTER_SYSTEM_PROMPT,
            ),
        )
        return response.text or ""
    except Exception as e:
        logger.error("Error generating cover letter: %s", e)
        return ""

async def rerank_jobs_with_llm(cv_text: str, candidate_jobs: list[models.ScoredPoint]) -> list[dict]:
    """Uses Gemini to re-rank a list of candidate jobs against a CV."""
    if not candidate_jobs:
        return []

    job_payloads = [job.payload for job in candidate_jobs]
    user_prompt = get_rerank_user_prompt(cv_text, job_payloads)

    try:
        response = get_gemini_client().models.generate_content(
            model=RERANK_MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=RERANK_SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )

        result = json.loads(response.text)
        ranked_indices = {item['job_index']: item for item in result.get('ranked_jobs', [])}

        final_jobs = []
        for i, job in enumerate(job_payloads):
            if i in ranked_indices:
                rank_data = ranked_indices[i]
                job['match_score'] = rank_data['match_score']
                job['reason'] = rank_data['reason']
                final_jobs.append(job)

        final_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        # Tăiem rezultatele la top 10
        return final_jobs[:10]

    except Exception as e:
        logger.error("Error re-ranking jobs with LLM: %s", e)
        return []

async def find_and_match_jobs(user_id: str, cv_text: str, qdrant: AsyncQdrantClient) -> list[dict]:
    """Orchestrates the vector search, reranking and cover letter generation."""
    logger.info("Starting job match process for user: %s", user_id)

    cv_vector, seniority = await get_cv_details(user_id, qdrant)
    if not cv_vector:
        logger.warning("Could not find CV details for user %s. Aborting.", user_id)
        return []

    candidate_jobs = await find_similar_jobs(cv_vector, seniority, qdrant, limit=50)
    logger.info("Found %d candidate jobs from vector search.", len(candidate_jobs))

    ranked_jobs = await rerank_jobs_with_llm(cv_text, candidate_jobs)
    logger.info("Re-ranked down to %d final job matches.", len(ranked_jobs))

    if ranked_jobs:
        logger.info("Generating personalized cover letters concurrently...")

        async def fetch_letter_for_job(job):
            letter = await generate_cover_letter(cv_text, job)
            job['generated_cover_letter'] = letter
            return job

        tasks = [fetch_letter_for_job(job) for job in ranked_jobs]
        ranked_jobs = await asyncio.gather(*tasks)

    return ranked_jobs