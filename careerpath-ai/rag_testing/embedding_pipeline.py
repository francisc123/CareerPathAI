import sys
import os
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

load_dotenv("../.env")

gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
qdrant = QdrantClient(host="localhost", port=6333, check_compatibility=False)

CV_SAMPLES = [
    {
        "id": 1,
        "text": """
        Ana Popescu. Student an 3 Informatica.
        Skills: Python, HTML, CSS, JavaScript, Git.
        Proiecte: aplicatie To-Do List (HTML/CSS/JS), calculator BMI Python.
        Stagiu 2 luni WordPress.
        """,
        "payload": {
            "user_id": "user_001",
            "seniority": "junior",
            "skills": ["Python", "HTML", "CSS", "JavaScript"],
            "score": 38
        }
    },
    {
        "id": 2,
        "text": """
        Rares Constantinescu. Python Developer, 2 ani experienta.
        Skills: Python, FastAPI, PostgreSQL, Docker.
        Proiecte: API REST e-commerce cu 500 useri activi.
        Educatie: Politehnica Bucuresti, Calculatoare.
        """,
        "payload": {
            "user_id": "user_002",
            "seniority": "mid",
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "score": 69
        }
    },
    {
        "id": 3,
        "text": """
        Mihai Ionescu. Senior Software Engineer, 9 ani experienta.
        Skills: Python, Go, Kubernetes, AWS, Terraform, Kafka, Redis, gRPC.
        Tech Lead la startup fintech: sistem procesare plati 500k tranzactii/zi.
        Certificari: AWS Solutions Architect Professional, CKA.
        """,
        "payload": {
            "user_id": "user_003",
            "seniority": "senior",
            "skills": ["Python", "Go", "Kubernetes", "AWS", "Terraform", "Kafka"],
            "score": 100
        }
    }
]

def generate_embedding(text: str) -> list[float]:
    result = gemini.models.embed_content(
        model="gemini-embedding-001",
        contents=text.strip()
    )
    vector = result.embeddings[0].values
    assert len(vector) == 3072, f"Vector gresit: {len(vector)} dimensiuni in loc de 3072"
    return vector


print("=" * 55)
print("PASUL 1 — Generez embeddings si urc in Qdrant")
print("=" * 55)

points = []
for cv in CV_SAMPLES:
    vector = generate_embedding(cv["text"])
    points.append(PointStruct(
        id=cv["id"],
        vector=vector,
        payload=cv["payload"]
    ))
    print(f"✓  CV {cv['id']} ({cv['payload']['seniority']}) — vector generat, {len(vector)} dim")

qdrant.upsert(collection_name="cv_embeddings", points=points)
print(f"\n✓  {len(points)} CV-uri urcate in Qdrant cv_embeddings")

print("\n" + "=" * 55)
print("PASUL 2 — Testez cautarea semantica")
print("=" * 55)

queries = [
    "Python developer with FastAPI and REST API experience",
    "cloud infrastructure Kubernetes AWS DevOps engineer",
    "beginner web developer HTML CSS JavaScript",
]

for query_text in queries:
    query_vector = generate_embedding(query_text)
    results = qdrant.query_points(
        collection_name="cv_embeddings",
        query=query_vector,
        limit=3
    ).points
    print(f'\nQuery: "{query_text}"')
    for i, r in enumerate(results, 1):
        print(f"  {i}. user={r.payload['user_id']} | seniority={r.payload['seniority']} | score_cv={r.payload['score']} | similaritate={r.score:.3f}")

print("\n" + "=" * 55)
print("VALIDARE FINALA")
print("=" * 55)

query_python = generate_embedding("Python developer with FastAPI and REST API experience")
top = qdrant.query_points(collection_name="cv_embeddings", query=query_python, limit=1).points[0]

if top.payload["user_id"] == "user_002":
    print("✓  Cautare Python developer → CV mid Python pe primul loc (CORECT)")
else:
    print(f"✗  Asteptam user_002, am primit {top.payload['user_id']} (VERIFICATI)")

query_cloud = generate_embedding("cloud infrastructure Kubernetes AWS DevOps engineer")
top_cloud = qdrant.query_points(collection_name="cv_embeddings", query=query_cloud, limit=1).points[0]

if top_cloud.payload["user_id"] == "user_003":
    print("✓  Cautare DevOps/cloud → CV senior pe primul loc (CORECT)")
else:
    print(f"✗  Asteptam user_003, am primit {top_cloud.payload['user_id']} (VERIFICATI)")
