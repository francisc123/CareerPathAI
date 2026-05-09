from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="qdrant", port=6333)

COLLECTIONS = {
    "cv_embeddings": {"size": 3072, "distance": Distance.COSINE},
    "job_embeddings": {"size": 3072, "distance": Distance.COSINE},
    "course_embeddings": {"size": 3072, "distance": Distance.COSINE},
}

existing = {c.name for c in client.get_collections().collections}

for name, config in COLLECTIONS.items():
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=config["size"],
                distance=config["distance"]
            )
        )
        print(f"✓ Creata colectia {name}")
    else:
        print(f"✓ Colectia {name} exista")

print("\nColectii active:")
for c in client.get_collections().collections:
    info = client.get_collection(c.name)
    print(f"  - {c.name}: {info.points_count} puncte")

