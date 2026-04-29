from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def setup_qdrant():
    print("Mă conectez la Qdrant pe localhost:6333...")
    client = QdrantClient(url="http://localhost:6333")

    colectii = ["cv_embeddings", "job_embeddings", "course_embeddings"]

    for nume_colectie in colectii:
        if client.collection_exists(collection_name=nume_colectie):
            print(f"[OK] Colecția '{nume_colectie}' există deja.")
        else:
            # ATENȚIE: size=3072 pentru modelul gemini-embedding-001
            client.create_collection(
                collection_name=nume_colectie,
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
            )
            print(f"[+] Colecție creată cu succes: {nume_colectie}")

    print("\n=> Qdrant este pregătit pentru proiect!")

if __name__ == "__main__":
    setup_qdrant()