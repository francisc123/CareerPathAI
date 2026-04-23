import sys
import os
import json
import re
from google import genai
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

CV_SAMPLES = {
    "junior": """
    Ana Popescu
    Student an 3, Facultatea de Matematica-Informatica, Universitatea Babes-Bolyai
    Skills: Python, HTML, CSS, JavaScript, Git
    Proiecte: Aplicatie web To-Do List (HTML/CSS/JS, proiect universitar)
               Calculator BMI in Python (tema de curs)
    Experienta: stagiu 2 luni la o firma locala de web design (WordPress)
    """,

    "mid": """
    Rares Constantinescu
    Python Developer — 2 ani experienta
    Skills: Python, FastAPI, PostgreSQL, Docker
    Proiecte: API REST pentru platforma e-commerce (500 useri activi)
    Educatie: Universitatea Politehnica Bucuresti, Calculatoare, anul 2
    """,

    "senior": """
    Mihai Ionescu
    Senior Software Engineer — 9 ani experienta
    Skills: Python, Go, Kubernetes, AWS (EKS, RDS, S3, Lambda), Terraform, PostgreSQL,
            Redis, Kafka, Docker, CI/CD (GitHub Actions, ArgoCD), gRPC, REST, Prometheus, Grafana
    Experienta:
      - Tech Lead la startup fintech (echipa 6 dev): arhitectat sistemul de procesare plati
        (500k tranzactii/zi, latenta p99 < 80ms)
      - Senior Engineer la companie SaaS: migrat monolith Rails la microservicii Go,
        redus costurile de infrastructura cu 40%
    Educatie: Masterat Sisteme Distribuite, Politehnica Bucuresti
    Certificari: AWS Solutions Architect Professional, CKA (Certified Kubernetes Administrator)
    """,

    "career_changer": """
    Elena Dumitrescu
    Fost profesor de matematica, 6 ani. Reconversie profesionala catre IT — 8 luni.
    Educatie: Licenta Matematica, Universitatea Bucuresti
    Cursuri absolvite: Python for Everybody (Coursera), CS50 Harvard (online, certificat),
                       SQL Bootcamp (Udemy)
    Proiecte personale: Script Python pentru analiza notelor elevilor (pandas, matplotlib)
                        Dashboard Excel automatizat cu Python openpyxl
    Skills: Python, SQL (SQLite), pandas, matplotlib, Excel, Git (basic)
    GitHub: 12 repositorii publice, commits regulate in ultimele 6 luni
    """,

    "bootcamp": """
    Andrei Marin
    Absolvent bootcamp FullStack JavaScript — 4 luni (ProFactor Academy)
    Skills: JavaScript, TypeScript, React, Node.js, Express, MongoDB, REST APIs,
            HTML, CSS, Tailwind CSS, Git, GitHub
    Proiecte:
      - Platforma de blogging cu autentificare JWT (React + Node + MongoDB, deployed pe Render)
      - App de gestiune task-uri in timp real cu WebSocket (React + Express + Socket.io)
      - Clone Trello minimal cu drag-and-drop (React)
    Educatie: Licenta Drept (nefinalizata, 2 ani)
    """
}

with open("../services/cv-analyzer-agent/prompts/cv_scoring.txt", encoding="utf-8") as f:
    system_prompt = f.read()

REQUIRED_KEYS = {"score", "seniority", "skills", "strengths", "gaps", "target_role", "score_breakdown"}
SCORE_BREAKDOWN_KEYS = {"experience", "skill_stack", "projects", "education", "certifications"}
VALID_SENIORITY = {"junior", "mid", "senior", "lead"}

all_passed = True

for cv_type, cv_text in CV_SAMPLES.items():
    print(f"\n{'='*60}")
    print(f"CV TYPE: {cv_type.upper()}")
    print('='*60)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{system_prompt}\n\nCV TEXT:\n{cv_text}"
    )

    raw = response.text or ""
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())

    try:
        result = json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"[FAIL] JSON invalid: {e}")
        print(raw)
        all_passed = False
        continue

    errors = []

    missing_keys = REQUIRED_KEYS - result.keys()
    if missing_keys:
        errors.append(f"Campuri lipsa: {missing_keys}")

    score = result.get("score")
    if not isinstance(score, int) or not (0 <= score <= 100):
        errors.append(f"score invalid: {score}")

    if result.get("seniority") not in VALID_SENIORITY:
        errors.append(f"seniority invalid: {result.get('seniority')}")

    breakdown = result.get("score_breakdown", {})
    missing_bd = SCORE_BREAKDOWN_KEYS - breakdown.keys()
    if missing_bd:
        errors.append(f"score_breakdown campuri lipsa: {missing_bd}")
    else:
        total = sum(breakdown.values())
        if abs(total - score) > 2:
            errors.append(f"score_breakdown suma ({total}) != score ({score})")

    if errors:
        print(f"[FAIL] {'; '.join(errors)}")
        all_passed = False
    else:
        print(f"[PASS] score={score}, seniority={result['seniority']}, target={result['target_role']}")
        print(f"       breakdown: {breakdown}")

print(f"\n{'='*60}")
print("REZULTAT FINAL:", "TOATE TESTELE TRECUTE" if all_passed else "UNELE TESTE AU ESUAT")
print('='*60)
