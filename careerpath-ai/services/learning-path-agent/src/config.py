import os
from dotenv import load_dotenv

load_dotenv()

# În interiorul aceleiași rețele Docker, folosim denumirea containerului 'cp-redpanda' și portul intern expus 19092 sau 9092.
# Prioritizăm variabila injectată de ancoră, dar punem un fallback complet valid pentru Docker bridge.
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "cp-redpanda:19092")

# Topic-ul aliniat perfect cu cp-cv-analyzer
TOPIC_GAPS_IDENTIFIED = "cv.analyzed"
TOPIC_LEARNING_PATH_CREATED = "learning.path.created"
TOPIC_GAPS_IDENTIFIED_DLQ = "gaps.identified.dlq"

# CRITIC: Schimbat din localhost în cp-postgres pentru ca containerul să poată vedea baza de date în rețeaua Docker
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://cp_user:change_me@cp-postgres:5432/careerpath")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")