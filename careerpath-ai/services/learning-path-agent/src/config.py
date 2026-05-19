import os
from dotenv import load_dotenv

load_dotenv()

# În interiorul aceleiași rețele Docker, folosim denumirea containerului 'cp-redpanda' și portul intern expus 19092 sau 9092.
# Prioritizăm variabila injectată de ancoră, dar punem un fallback complet valid pentru Docker bridge.
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "cp-redpanda:19092")

# Orchestrator-ul publică pe `gaps.identified` după ce decide ramura learning_path.
# Learning-path-agent consumă din acest topic, nu direct din `cv.analyzed`.
TOPIC_GAPS_IDENTIFIED = "gaps.identified"
TOPIC_LEARNING_PATH_CREATED = "learning.path.created"
TOPIC_GAPS_IDENTIFIED_DLQ = "gaps.identified.dlq"

# CRITIC: Schimbat din localhost în cp-postgres pentru ca containerul să poată vedea baza de date în rețeaua Docker
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://cp_user:change_me@cp-postgres:5432/careerpath")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")