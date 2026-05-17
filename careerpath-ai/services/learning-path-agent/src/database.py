import asyncpg
import json
from .config import DATABASE_URL

async def get_db_pool():
    """Creates and returns a database connection pool."""
    return await asyncpg.create_pool(DATABASE_URL)

async def save_learning_path(pool, user_id: str, target_role: str, path_data: dict):
    """
    Saves the generated learning path to the PostgreSQL database.
    """
    query = """
            INSERT INTO learning_paths (user_id, target_role, title, estimated_weeks, plan_data, created_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                target_role = EXCLUDED.target_role,
                                             title = EXCLUDED.title,
                                             estimated_weeks = EXCLUDED.estimated_weeks,
                                             plan_data = EXCLUDED.plan_data,
                                             created_at = NOW();
            """
    try:
        async with pool.acquire() as connection:
            await connection.execute(
                query,
                user_id,
                target_role,
                path_data.get("title"),
                path_data.get("estimated_weeks"),
                json.dumps(path_data.get("weekly_plan"))
            )
        print(f"💾 Learning path for user {user_id} saved to database.")
    except Exception as e:
        print(f"❌ Error saving learning path to database: {e}")

async def get_learning_path(pool, user_id: str) -> dict | None:
    """Retrieves the learning path for a user from the database."""
    query = """
            SELECT user_id, target_role, title, estimated_weeks, plan_data AS weekly_plan, created_at
            FROM learning_paths
            WHERE user_id = $1;
            """
    try:
        async with pool.acquire() as connection:
            row = await connection.fetchrow(query, user_id)
            if row is None:
                return None

            result = dict(row)

            # Conversie stabilă a string-ului sau a formatului nativ JSONB în structură Python validă
            if isinstance(result.get("weekly_plan"), str):
                result["weekly_plan"] = json.loads(result["weekly_plan"])
            elif result.get("weekly_plan") is None:
                result["weekly_plan"] = []

            return result
    except Exception as e:
        print(f"Error retrieving learning path: {e}")
        return None