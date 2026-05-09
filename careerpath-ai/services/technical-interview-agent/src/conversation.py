import google.generativeai as genai
import redis.asyncio as redis
import json
from .config import GEMINI_API_KEY, REDIS_URL
from .prompts import TECHNICAL_INTERVIEW_PROMPT, POST_INTERVIEW_ANALYSIS_PROMPT
from .database import save_interview_results

genai.configure(api_key=GEMINI_API_KEY)
redis_client = redis.from_url(REDIS_URL)

chat_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=TECHNICAL_INTERVIEW_PROMPT
)
analysis_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=POST_INTERVIEW_ANALYSIS_PROMPT,
    generation_config={"response_mime_type": "application/json"}
)


async def get_chat_history(session_id: str) -> list:
    """Retrieves chat history from Redis."""
    history_json = await redis_client.get(f"tech_interview:{session_id}")
    if history_json:
        return json.loads(history_json)
    return []


async def save_chat_history(session_id: str, history: list):
    """Saves chat history to Redis with 1-hour TTL."""
    await redis_client.set(f"tech_interview:{session_id}", json.dumps(history), ex=3600)


async def stream_ai_response(session_id: str, user_message: str):
    """Generates and streams the AI's response using the full conversation history."""
    history = await get_chat_history(session_id)

    # Pass existing history to the chat (without current message), then send current message
    chat = chat_model.start_chat(history=history)
    full_ai_response = ""

    try:
        response_stream = await chat.send_message_async(user_message, stream=True)

        async for chunk in response_stream:
            full_ai_response += chunk.text
            yield chunk.text

        # Save both user message and AI response to history
        history.append({"role": "user", "parts": [user_message]})
        history.append({"role": "model", "parts": [full_ai_response]})
        await save_chat_history(session_id, history)

    except Exception as e:
        print(f"Error generating AI response stream: {e}")
        yield "I'm sorry, I'm having a technical issue. Let's try that again."


async def analyze_and_save_transcript(session_id: str, user_id: str):
    """Analyzes the full transcript and saves the results."""
    history = await get_chat_history(session_id)
    if not history:
        return

    transcript = "\n".join([f"{item['role']}: {item['parts'][0]}" for item in history])

    try:
        response = await analysis_model.generate_content_async(transcript)
        analysis_result = json.loads(response.text)

        score = analysis_result.get("score")
        feedback = analysis_result.get("feedback")

        await save_interview_results(session_id, user_id, score, feedback, transcript)

    except Exception as e:
        print(f"Error analyzing transcript: {e}")
