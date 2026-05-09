import asyncpg
from .config import DATABASE_URL

async def save_interview_results(session_id: str, user_id: str, score: int, feedback: str, transcript: str):
    """Saves the interview results to the database."""
    query = """
    INSERT INTO interview_sessions (id, user_id, type, score, feedback, transcript, completed_at)
    VALUES ($1, $2, 'Technical', $3, $4, $5, NOW())
    ON CONFLICT (id) DO UPDATE SET
        score = EXCLUDED.score,
        feedback = EXCLUDED.feedback,
        transcript = EXCLUDED.transcript,
        completed_at = NOW();
    """
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute(query, session_id, user_id, score, feedback, transcript)
        await conn.close()
        print(f"💾 Interview results for session {session_id} saved.")
    except Exception as e:
        print(f"❌ Error saving interview results: {e}")

