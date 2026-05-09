import json
import logging
import redis.asyncio as redis_lib
from google import genai
from google.genai import types
from .config import GEMINI_API_KEY, REDIS_URL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are CareerPath AI, an intelligent and empathetic career advisor embedded in a career development platform.

Your goals:
1. Help users clarify their career goals through natural, friendly conversation.
2. Silently build their professional profile from what they share (shadow profiling).
3. Ask smart follow-up questions about: target role, years of experience, tech stack, seniority level.
4. When you have a good picture of who they are, suggest uploading their CV for deeper analysis and personalized job matches.
5. Keep responses SHORT — 1-3 sentences maximum. Be conversational, not robotic.

Rules:
- Never ask more than one question at a time.
- Sound like a knowledgeable human advisor, not a form.
- If the user greets you, greet back and ask ONE question about their career.
- Always respond in the SAME LANGUAGE the user writes in.
- If the user seems interested in jobs or learning paths, gently guide them to upload their CV.
"""

PROFILE_EXTRACTION_PROMPT = """Extract career information from this conversation. Return ONLY valid JSON, no markdown.

Conversation:
{conversation}

JSON schema (use null if not mentioned):
{{
  "target_role": "string or null",
  "experience_years": "number or null",
  "skills": ["list of technical skills"],
  "seniority": "junior | mid | senior | null",
  "location": "string or null",
  "ready_for_cv_upload": true or false
}}"""


async def _get_history(redis_client, user_id: str) -> list[dict]:
    raw = await redis_client.get(f"chat:{user_id}")
    return json.loads(raw) if raw else []


async def _save_history(redis_client, user_id: str, history: list[dict]):
    await redis_client.set(f"chat:{user_id}", json.dumps(history), ex=86400)


async def _extract_profile(redis_client, user_id: str, history: list[dict]):
    """Background shadow profiling — extracts structured data from conversation."""
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
        text = resp.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        profile = json.loads(text)
        await redis_client.set(f"profile:{user_id}", json.dumps(profile), ex=86400 * 7)
        logger.info(f"Shadow profile updated for {user_id}: {profile}")
    except Exception as e:
        logger.warning(f"Profile extraction skipped for {user_id}: {e}")


async def chat(user_id: str, user_message: str) -> str:
    """Process a user message through Gemini and return the AI response."""
    redis_client = redis_lib.from_url(REDIS_URL, decode_responses=True)
    try:
        history = await _get_history(redis_client, user_id)
        history.append({"role": "user", "content": user_message})

        # Build Gemini content list
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
                temperature=0.75,
                max_output_tokens=250,
            ),
        )

        ai_text = response.text.strip()
        history.append({"role": "model", "content": ai_text})
        await _save_history(redis_client, user_id, history)

        # Run shadow profiling every 3 user messages
        user_msg_count = sum(1 for m in history if m["role"] == "user")
        if user_msg_count % 3 == 0:
            await _extract_profile(redis_client, user_id, history)

        return ai_text

    finally:
        await redis_client.aclose()
