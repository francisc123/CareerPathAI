from google import genai

EMBEDDING_MODEL = "gemini-embedding-001"


def generate_embedding(text: str) -> list[float]:
    """Generates a text embedding using Gemini, consistent with cv-analyzer-agent."""
    import os
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return response.embeddings[0].values

