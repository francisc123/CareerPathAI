import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, mapped_column, Mapped
from sqlalchemy import Integer, String, Text, Float, DateTime, func, select, delete

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

# -----------------
# ORM Models
# -----------------
class ScrapedJob(Base):
    __tablename__ = 'scraped_jobs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scrape_run_id: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    company: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    seniority: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)

class JobMatch(Base):
    __tablename__ = 'job_matches'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    job_title: Mapped[str] = mapped_column(String)
    company: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    match_score: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    generated_cover_letter: Mapped[str] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

# -----------------
# Database Operations
# -----------------
async def get_db_session() -> AsyncSession:
    """Dependency for providing a database session."""
    async with AsyncSessionLocal() as session:
        yield session

async def save_job_matches(session: AsyncSession, user_id: str, matched_jobs: list[dict]):
    """
    Saves matched jobs using SQLAlchemy ORM.
    """
    try:
        await session.execute(delete(JobMatch).where(JobMatch.user_id == user_id))

        new_matches = []
        for job in matched_jobs:
            new_match = JobMatch(
                user_id=user_id,
                job_title=job.get("title"),
                company=job.get("company"),
                url=job.get("url"),
                source=job.get("source"),
                location=job.get("location"),
                match_score=job.get("match_score"),
                reason=job.get("reason"),
                generated_cover_letter=job.get("generated_cover_letter")
            )
            new_matches.append(new_match)

        session.add_all(new_matches)
        await session.commit()

        print(f"Saved {len(matched_jobs)} job matches for user {user_id} via ORM.")
    except Exception as e:
        await session.rollback()
        print(f"Error saving job matches to database: {e}")

async def get_jobs_by_scrape_run(session: AsyncSession, scrape_run_id: str) -> list[ScrapedJob]:
    """Extrage joburile scrapate pentru a le trimite spre Qdrant/Gemini."""
    stmt = select(ScrapedJob).where(ScrapedJob.scrape_run_id == scrape_run_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_job_matches_for_user(session: AsyncSession, user_id: str) -> list[dict]:
    """Retrieves all matched jobs for a user from the database via ORM."""
    stmt = select(JobMatch).where(JobMatch.user_id == user_id).order_by(JobMatch.match_score.desc())
    result = await session.execute(stmt)
    matches = result.scalars().all()

    return [{
        "job_title": m.job_title,
        "company": m.company,
        "url": m.url,
        "source": m.source,
        "location": m.location,
        "match_score": m.match_score,
        "reason": m.reason,
        "generated_cover_letter": m.generated_cover_letter,
        "created_at": m.created_at
    } for m in matches]