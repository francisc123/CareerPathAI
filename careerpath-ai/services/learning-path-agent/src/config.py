import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:19092")
TOPIC_GAPS_IDENTIFIED = "gaps.identified"
TOPIC_LEARNING_PATH_CREATED = "learning.path.created"

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://cp_user:change_me@localhost:5432/careerpath")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
