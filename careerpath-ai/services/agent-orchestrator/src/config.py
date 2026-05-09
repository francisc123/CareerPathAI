import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:19092")
TOPIC_CV_ANALYZED = "cv.analyzed"
TOPIC_GAPS_IDENTIFIED = "gaps.identified"
TOPIC_ORCHESTRATOR_DLQ = "orchestrator.dlq" # Dead Letter Queue
JOB_SCRAPER_URL = os.getenv("JOB_SCRAPER_URL", "http://localhost:8003")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
