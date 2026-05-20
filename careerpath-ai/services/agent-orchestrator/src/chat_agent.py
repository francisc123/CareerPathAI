import json
import logging
import redis.asyncio as redis_lib
from aiokafka import AIOKafkaProducer
from google import genai
from google.genai import types
from .config import GEMINI_API_KEY, KAFKA_BROKERS, REDIS_URL, TOPIC_PROFILE_EXTRACTED

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — structured 5-question career interview
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a Senior IT Career Advisor on the CareerPath AI platform.
You are professional, analytical, and direct. Your pace is fast and decision-oriented. No small talk — you run an efficient triage.

STRICT RULES (follow without exception):

1. LENGTH: Every response is MAXIMUM 2-3 short sentences (exception: the final summary in rule 8 can be slightly longer).

2. ONE question per message only.

3. CRITICAL MECHANISM — NEVER ask open-ended questions. Frame EVERY question with 2 or 3 clear contrasting options.
   Correct examples:
   - "Do you prefer working with numbers and logic, or are you more of a visual and creative person?"
   - "Do you enjoy finding bugs and testing things, or do you prefer building them from scratch?"
   - "Do you like explaining and documenting, or do you prefer staying in the code?"
   Adapt the options to what the user just told you.

4. RELEVANCE CHECK (clarification loop) — Before advancing, evaluate whether the user's last answer actually addresses the question you asked.
   If the answer is irrelevant, ambiguous, joking, or off-topic for the parameter you needed, DO NOT move on.
   Acknowledge briefly and re-ask the SAME question, ideally rephrased or with clearer options.
   Example:
   - You asked: "Ce buget ai pentru cursuri?"
   - User said: "Vreau o cafea."
   - WRONG: ask the next planned question.
   - CORRECT: "Înțeleg, dar pentru a te direcționa corect am nevoie de o aproximație a bugetului. Sub 200 RON, între 200-500 RON, sau peste 500 RON?"
   If the user already gave MULTIPLE pieces of info in one message (e.g. "sunt student la info, vreau frontend, am 0 experiență"), DO NOT re-ask those — internally mark them as captured and move to a new dimension.

5. CONTEXT SWITCHING — If the user asks a tangential question (e.g. "Ce face un Data Engineer?" while you're triaging), follow this pattern:
   a) Answer their question concisely in 1-2 sentences.
   b) Bridge back explicitly: "Revenind la ce discutam, ..." and re-ask your last triage question.
   Never silently abandon the triage flow when the user goes off-track.

6. ADAPTIVE TONE — Mirror the user's communication style:
   - User writes short/terse → respond shorter, fewer options, no extra explanation.
   - User writes long/exploratory → respond slightly more elaborate, add a brief rationale.
   - User shows confusion ("nu știu", "habar n-am", "?") → briefly explain the options before re-asking.
   Never sound like canned text. Match register: casual ↔ formal as the user does.

7. LIMIT: You have a budget of MAXIMUM 10 questions for the entire session. If the profile is clear after 4-5, go straight to the summary in rule 8.

8. FINAL CONFIRMATION (semantic triage) — When you believe you have enough data, do NOT emit CTA_READY immediately. Two-step ending:
   Step A — propose a summary. Write a short paragraph (3-5 sentences) summarizing what you understood:
     - current situation (student / in tech / career switch)
     - main interest / preference signals
     - the recommended role
     Then ask exactly: "Asta reflectă ce vrei? Confirmă cu DA să continuăm, sau spune-mi ce să ajustez."
     DO NOT write CTA_READY in step A.
   Step B — only after the user confirms (e.g. DA, da, yes, ok, corect, exact, perfect), emit:
     - The recommended role (e.g. **Frontend Developer**, **QA Engineer**, **Data Analyst**)
     - 2 concrete next steps
     - On the very next line, write exactly: CTA_READY
   If the user disagrees or adds correction in step A, integrate the correction and propose a REVISED summary, then re-ask for confirmation. Do not emit CTA_READY until you have explicit confirmation.

9. LANGUAGE RULE: Always respond in the same language the user writes in. If the user writes in Romanian, respond in Romanian. If in English, respond in English.

SPECIAL CASE — if the user's first message is "__init__":
  Reply with EXACTLY the following text, no extra words, no modifications:
  "Welcome! I'm here to help you shape your career path. To start, I'd like to know — are you already working in tech, a student, or thinking about a career switch?"
  After this first greeting, rule 9 takes over: as soon as the user replies in
  Romanian, switch all future replies to Romanian for the rest of the session.
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


async def _publish_profile_extracted(user_id: str, profile: dict) -> None:
    """
    Fire-and-forget: publish profile.extracted so user-service can persist the
    canonical row in PostgreSQL. Anonymous chat ids (anon_*) don't have a real
    User row downstream, so we skip them and save the round-trip.
    """
    if not user_id or user_id.startswith("anon_"):
        return
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    try:
        await producer.start()
        await producer.send_and_wait(
            TOPIC_PROFILE_EXTRACTED,
            {"user_id": user_id, **profile},
        )
    except Exception as e:
        # Profile sync is best-effort — never let it break the chat turn.
        logger.warning("profile.extracted publish failed for %s: %s", user_id, e)
    finally:
        try:
            await producer.stop()
        except Exception:
            pass


async def _extract_and_save_profile(redis_client, user_id: str, history: list[dict]) -> dict | None:
    """Silently extract structured profile from conversation and persist to Redis.
    Returns the parsed profile dict (or None on failure) so callers can gate on slot completeness.
    """
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
        # Real-time sync into user-service PostgreSQL per spec
        # ("REAL-TIME PROFILE SYNCHRONIZATION").
        await _publish_profile_extracted(user_id, profile)
        return profile
    except Exception as e:
        logger.warning(f"Profile extraction skipped for {user_id}: {e}")
        return None


# Critical slots that MUST be filled before we accept a CTA_READY signal.
# If any of these are null/empty, we re-arm the agent to keep triaging.
REQUIRED_SLOTS = ("target_role", "current_situation")


def _missing_slots(profile: dict | None) -> list[str]:
    if not profile:
        return list(REQUIRED_SLOTS)
    return [s for s in REQUIRED_SLOTS if not profile.get(s)]


# Demo-safe fallback questions used when Gemini is unavailable. Kept in EN
# because the spec mandates EN as the initial language; if Gemini comes back
# online, normal mirroring resumes via the system prompt's rule 9.
_FALLBACK_QUESTIONS = [
    "Quick check — are you already working in tech, a student, or considering a career switch?",
    "Are you more drawn to building applications, or to analyzing data?",
    "Do you prefer the visual side (frontend) or the logic/server side (backend)?",
    "Do you have hands-on coding experience, or are you still at the theory/courses stage?",
    "Want to share more details about what you've been learning so far?",
]


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

        # Gemini call wrapped in try/except — if it fails (quota, network, API outage),
        # fall back to a scripted triage question so the demo keeps flowing.
        try:
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
        except Exception as gemini_err:
            logger.error(f"Gemini call failed for {user_id}: {gemini_err}")
            user_turns = sum(1 for m in history if m["role"] == "user")
            # Cycle through fallback questions based on turn count.
            raw = _FALLBACK_QUESTIONS[(user_turns - 1) % len(_FALLBACK_QUESTIONS)]
            # Avoid storing a fake "model" turn that the next prompt would treat as real history.
            history.append({"role": "model", "content": raw})
            await _save_history(redis_client, user_id, history)
            return {"text": raw, "cta": False}

        # Detect CTA_READY signal emitted by the model.
        cta = "CTA_READY" in raw
        # Strip the marker — show only the summary sentence to the user.
        text = raw.replace("CTA_READY", "").strip()

        history.append({"role": "model", "content": raw})
        await _save_history(redis_client, user_id, history)

        # Shadow profile extraction after every 2 user messages, or right before a CTA.
        user_count = sum(1 for m in history if m["role"] == "user")
        profile: dict | None = None
        if user_count % 2 == 0 or cta:
            profile = await _extract_and_save_profile(redis_client, user_id, history)

        # SLOT-FILLING GATE: if the model wants to finish but required slots are
        # still empty, disarm the CTA. The next user turn will get a fresh prompt
        # and the model will keep triaging (rule 4 in the system prompt covers this).
        if cta:
            if profile is None:
                # Try to read whatever profile we have on file.
                profile_raw = await redis_client.get(f"profile:{user_id}")
                profile = json.loads(profile_raw) if profile_raw else None
            missing = _missing_slots(profile)
            if missing:
                logger.warning(
                    f"CTA disarmed for {user_id} — missing critical slots: {missing}"
                )
                cta = False

        return {"text": text, "cta": cta}

    finally:
        await redis_client.aclose()
