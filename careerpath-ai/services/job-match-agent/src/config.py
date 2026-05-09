import os
from dotenv import load_dotenv

load_dotenv()

# Kafka
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:19092")
TOPIC_JOBS_SCRAPED = "jobs.scraped"
TOPIC_JOBS_MATCHED = "jobs.matched"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://cp_user:change_me@localhost:5432/careerpath")

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
CV_COLLECTION_NAME = "cv_embeddings"
JOB_COLLECTION_NAME = "job_embeddings"

# AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RERANK_MODEL_NAME = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-001"

