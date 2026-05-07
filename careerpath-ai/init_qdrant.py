#!/usr/bin/env python3
"""
Inițializează colecțiile Qdrant necesare pentru CareerPath AI.
Execută: python init_qdrant.py
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Conectare la Qdrant (în container, portul este 6333)
client = QdrantClient(host="localhost", port=6333)

COLLECTIONS = {
    "cv_embeddings": {
        "size": 3072,  # Gemini embedding model
        "distance": Distance.COSINE,
        "description": "Amprentele (embeddings) ale CV-urilor utilizatorilor"
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

print("\n🔍 Verificare colecții existente...\n")
existing = {c.name: c for c in client.get_collections().collections}

for name, config in COLLECTIONS.items():
    if name in existing:
        info = client.get_collection(name)
        current_dim = info.config.params.vectors.size
        if current_dim != config["size"]:
            print(f"⚠️  Colectia '{name}' avea dim={current_dim}, ștergere pentru recreare...")
            client.delete_collection(name)
        else:
            print(f"✓ Colectia '{name}' exista deja cu dim={config['size']} — skip")
            continue

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=config["size"],
            distance=config["distance"]
        )
    )
    print(f"✓ Colectie creata: {name} (dim={config['size']}, metric=Cosine)")

print("\n📊 Colecții active în Qdrant:\n")
for c in client.get_collections().collections:
    info = client.get_collection(c.name)
    print(f"  • {c.name}: {info.points_count} puncte")

print("\n✅ Inițializare Qdrant completă!\n")

