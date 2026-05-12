import json
import logging
import redis.asyncio as redis_lib
from google import genai
from google.genai import types
from .config import GEMINI_API_KEY, REDIS_URL

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — structured 5-question career interview
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a Senior IT Career Advisor on the CareerPath AI platform.
You are professional, analytical, and direct. Your pace is fast and decision-oriented. No small talk — you run an efficient triage.

STRICT RULES (follow without exception):

1. LENGTH: Every response is MAXIMUM 2-3 short sentences.

2. ONE question per message only.

3. CRITICAL MECHANISM — NEVER ask open-ended questions. Frame EVERY question with 2 or 3 clear contrasting options.
   Correct examples:
   - "Do you prefer working with numbers and logic, or are you more of a visual and creative person?"
   - "Do you enjoy finding bugs and testing things, or do you prefer building them from scratch?"
   - "Do you like explaining and documenting, or do you prefer staying in the code?"
   Adapt the options to what the user just told you.

4. LIMIT: You have a budget of MAXIMUM 10 questions for the entire session. If the profile is clear after 4-5, go straight to the conclusion.

5. CONCLUSION: When you have enough data, write:
   - The recommended role (e.g. Frontend Developer, QA Engineer, Data Analyst)
   - 2 concrete steps to get started
   - On the very next line, write exactly: CTA_READY
   Do not write anything after CTA_READY.

CORRECT ending example:
  Your profile fits best with a **QA Engineer** role.
  Step 1: Start with manual testing fundamentals (ISTQB Foundation level).
  Step 2: Upload your CV for a detailed skills gap analysis.
  CTA_READY

LANGUAGE RULE: Always respond in the same language the user writes in. If the user writes in Romanian, respond in Romanian. If in English, respond in English.

SPECIAL CASE — if the user's first message is "__init__":
  Reply with EXACTLY the following text, no extra words, no modifications:
  "Bun venit! Sunt aici să te ajut să-ți conturezi parcursul profesional. Pentru început, aș vrea să știu dacă lucrezi deja în domeniul tech, ești student sau te gândești să faci o reconversie?"
"""

# ---------------------------------------------------------------------------
# Profile extraction prompt (shadow profiling)
# ---------------------------------------------------------------------------
PROFILE_EXTRACTION_PROMPT = """Extrage datele de profil de carieră din această conversație. Returnează DOAR JSON valid, fără markdown.

Conversație:
{conversation}

Schema JSON (null dacă nu a fost menționat):
{{
  "target_role": "string or null",
  "experience_years": "number or null",
  "skills": ["lista de competențe tehnice"],
  "seniority": "junior | mid | senior | null",
  "current_situation": "in_tech | student | career_switch | null",
  "actively_job_hunting": "boolean or null",
  "location": "string or null"
}}"""


async def _get_history(redis_client, user_id: str) -> list[dict]:
    raw = await redis_client.get(f"chat:{user_id}")
    return json.loads(raw) if raw else []


async def _save_history(redis_client, user_id: str, history: list[dict]):
    await redis_client.set(f"chat:{user_id}", json.dumps(history), ex=86400)


async def _extract_and_save_profile(redis_client, user_id: str, history: list[dict]):
    """Silently extract structured profile from conversation and persist to Redis."""
    conversation_text = "\n".join(
        f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in history
    )
    prompt = PROFILE_EXTRACTION_PROMPT.format(conversation=conversation_text)
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        resp = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = (
            resp.text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        profile = json.loads(text)
        await redis_client.set(f"profile:{user_id}", json.dumps(profile), ex=86400 * 7)
        logger.info(f"Profile updated for {user_id}: {profile}")
    except Exception as e:
        logger.warning(f"Profile extraction skipped for {user_id}: {e}")


async def chat(user_id: str, user_message: str) -> dict:
    """
    Process one user turn.
    Returns {"text": str, "cta": bool}
    cta=True means the interview is complete → frontend should show upload card.
    """
    redis_client = redis_lib.from_url(REDIS_URL, decode_responses=True)
    try:
        history = await _get_history(redis_client, user_id)
        history.append({"role": "user", "content": user_message})

        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part(text=m["content"])],
            )
            for m in history
        ]

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.65,
                max_output_tokens=512,
            ),
        )

        raw = response.text.strip()

        # Detect CTA_READY signal
        cta = "CTA_READY" in raw
        # Strip the marker — show only the summary sentence
        text = raw.replace("CTA_READY", "").strip()

        history.append({"role": "model", "content": raw})
        await _save_history(redis_client, user_id, history)

        # Shadow profile extraction after every 2 user messages
        user_count = sum(1 for m in history if m["role"] == "user")
        if user_count % 2 == 0 or cta:
            await _extract_and_save_profile(redis_client, user_id, history)

        return {"text": text, "cta": cta}

    finally:
        await redis_client.aclose()
