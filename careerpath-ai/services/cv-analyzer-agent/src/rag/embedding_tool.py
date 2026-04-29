import logging
from src.config.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-001"


def generate_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Textul pentru embedding nu poate fi gol.")

    try:
        logger.debug("Generez vector pentru %d caractere cu %s", len(text), EMBEDDING_MODEL)
        response = get_gemini_client().models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        return response.embeddings[0].values
    except Exception as e:
        logger.error("Eroare la generarea embedding-ului: %s", e)
        raise
