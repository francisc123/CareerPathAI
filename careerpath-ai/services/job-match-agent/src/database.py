import asyncpg
import json
from .config import DATABASE_URL

async def get_db_pool():
    """Creates and returns a database connection pool."""
    return await asyncpg.create_pool(DATABASE_URL)

async def save_job_matches(pool, user_id: str, matched_jobs: list[dict]):
    """
    Saves the matched jobs to the PostgreSQL database.
    This function first deletes old matches for the user, then inserts the new ones.
    """
    # The `job_matches` table is assumed to exist.
    # It should have columns like: user_id, job_title, ..., generated_cover_letter (TEXT)
    delete_query = "DELETE FROM job_matches WHERE user_id = $1;"
    insert_query = """
    INSERT INTO job_matches (user_id, job_title, company, url, source, location, match_score, reason, generated_cover_letter, created_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW());
    """
    try:
        async with pool.acquire() as connection:
            async with connection.transaction():
                # Delete old matches
                await connection.execute(delete_query, user_id)

                # Insert new matches
                records_to_insert = [
                    (
                        user_id,
                        job.get("title"),
                        job.get("company"),
                        job.get("url"),
                        job.get("source"),
                        job.get("location"),
                        job.get("match_score"),
                        job.get("reason"),
                        job.get("generated_cover_letter")
                    ) for job in matched_jobs
                ]
                # copy_records_to_table is more efficient for bulk inserts
                await connection.copy_records_to_table(
                    'job_matches',
                    records=records_to_insert,
                    columns=[
                        'user_id', 'job_title', 'company', 'url', 'source',
                        'location', 'match_score', 'reason', 'generated_cover_letter'
                    ]
                )
        print(f"💾 {len(matched_jobs)} job matches for user {user_id} saved to database.")
    except Exception as e:
        print(f"❌ Error saving job matches to database: {e}")


async def get_job_matches_for_user(pool, user_id: str) -> list[dict]:
    """Retrieves all matched jobs for a user from the database."""
    query = """
    SELECT job_title, company, url, source, location, match_score, reason, generated_cover_letter, created_at
    FROM job_matches
    WHERE user_id = $1
    ORDER BY match_score DESC;
    """
    try:
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, user_id)
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ Error retrieving job matches: {e}")
        return []
