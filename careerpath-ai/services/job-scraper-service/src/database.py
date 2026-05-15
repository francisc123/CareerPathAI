import os
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "postgresql://careerpath_user:change_me_strong_password@localhost:5432/jobs_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ScrapedJob(Base):
    __tablename__ = "scraped_jobs"

    id = Column(Integer, primary_key=True, index=True)
    # job_hash va fi rezultatul xxhash(url)
    job_hash = Column(String(64), unique=True, index=True)
    user_id = Column(String, index=True)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    url = Column(String)
    description = Column(Text, nullable=True)
    source = Column(String) # 'linkedin', 'indeed', 'ejobs'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Creăm tabela la startup dacă nu există
def init_db():
    Base.metadata.create_all(bind=engine)