import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:19092")
TOPIC_CV_ANALYZED = "cv.analyzed"
TOPIC_GAPS_IDENTIFIED = "gaps.identified"
TOPIC_ORCHESTRATOR_DLQ = "orchestrator.dlq"
JOB_SCRAPER_URL = os.getenv("JOB_SCRAPER_URL", "http://cp-job-scraper:8003")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
