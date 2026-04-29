import os
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from dotenv import load_dotenv  # <-- 1. Adaugă acest import

# 2. Citește fișierul .env ca să găsească cheia
load_dotenv()

# 1. Inițializăm clienții
client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
qdrant = QdrantClient(url="http://localhost:6333")

# ... restul codului rămâne exact la fel ...
# 2. Pregătim 3 CV-uri mock (unul junior, unul mid, unul complet diferit)
CV_MOCKS = [
    {
        "id": 1,
        "text": "Junior Web Developer. Stiu HTML, CSS si invat React. Experienta 3 luni la un internship.",
        "seniority": "junior",
        "skills": ["HTML", "CSS", "React"]
    },
    {
        "id": 2,
        "text": "Mid Python Backend Developer. Construiesc API-uri robuste cu FastAPI, lucrez cu baze de date PostgreSQL si Docker. Experienta 3 ani.",
        "seniority": "mid",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"]
    },
    {
        "id": 3,
        "text": "Bucatar sef la un restaurant local de top. Coordonez o echipa de 5 oameni. Experienta 10 ani in gastronomie si managementul meniului.",
        "seniority": "senior_chef",
        "skills": ["Gatit", "Management", "Organizare"]
    }
]


def genereaza_vector(text):
    """Transformă textul într-un vector folosind Gemini."""
    res = client_gemini.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return res.embeddings[0].values


def testeaza_pipeline():
    print("=> PASUL 1: Generare și urcare vectori în Qdrant...")
    puncte_qdrant = []

    for cv in CV_MOCKS:
        print(f"   [...] Generez vector pentru CV: {cv['seniority']}...")
        vector = genereaza_vector(cv["text"])

        # Validare de siguranță: Ne asigurăm că lungimea e corectă
        if len(vector) != 3072:
            print(f"[EROARE FATALĂ] Dimensiune greșită a vectorului: {len(vector)}, așteptat 3072. Qdrant va crăpa.")
            return

        punct = PointStruct(
            id=cv["id"],
            vector=vector,
            payload={
                "seniority": cv["seniority"],
                "skills": cv["skills"],
                "text_original": cv["text"]
            }
        )
        puncte_qdrant.append(punct)
        print(f"   [+] Vector generat cu succes! (Dimensiune: {len(vector)})")

    # Salvăm tot în colecția noastră (upsert = insert sau update)
    qdrant.upsert(collection_name="cv_embeddings", points=puncte_qdrant)
    print("\n[OK] Toate cele 3 CV-uri au fost stocate în baza de date vectorială!\n")

    # ---------------------------------------------------------
    print("=> PASUL 2: Căutare Semantică (Job Match)...")
    # Asta va face platforma ta când va căuta candidatul potrivit
    query_text = "Cautam un Python backend developer care stie sa foloseasca FastAPI"
    print(f"   ? Căutăm candidatul pentru: '{query_text}'\n")

    query_vector = genereaza_vector(query_text)

    rezultate = qdrant.search(
        collection_name="cv_embeddings",
        query_vector=query_vector,
        limit=3  # Vrem top 3 candidați
    )

    print("=> REZULTATELE CĂUTĂRII:")
    for i, rez in enumerate(rezultate):
        print(f"   Locul {i + 1} | Scor similaritate: {rez.score:.4f} | Profil: {rez.payload['seniority']}")


if __name__ == "__main__":
    testeaza_pipeline()