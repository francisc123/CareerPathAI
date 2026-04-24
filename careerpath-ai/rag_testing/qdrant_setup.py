import sys
sys.stdout.reconfigure(encoding="utf-8")

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

COLLECTIONS = {
    "cv_embeddings": {
        "size": 3072,
        "distance": Distance.COSINE,
        "description": "Amprentele CV-urilor utilizatorilor"
    },
    "job_embeddings": {
        "size": 3072,
        "distance": Distance.COSINE,
        "description": "Amprentele joburilor scrape-uite"
    },
    "course_embeddings": {
        "size": 3072,
        "distance": Distance.COSINE,
        "description": "Amprentele cursurilor de invatare"
    },
}

existing = {c.name: c for c in client.get_collections().collections}

for name, config in COLLECTIONS.items():
    if name in existing:
        info = client.get_collection(name)
        current_dim = info.config.params.vectors.size
        if current_dim != config["size"]:
            client.delete_collection(name)
            print(f"⚠  Colectia '{name}' avea dim={current_dim}, stearsa pentru recreare cu dim={config['size']}")
        else:
            print(f"⚠  Colectia '{name}' exista deja cu dim corecta — skip")
            continue

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=config["size"],
            distance=config["distance"]
        )
    )
    print(f"✓  Colectie creata: {name} (dim={config['size']}, metric=Cosine)")

print("\nColectii active in Qdrant:")
for c in client.get_collections().collections:
    info = client.get_collection(c.name)
    print(f"  - {c.name}: {info.points_count} puncte")
