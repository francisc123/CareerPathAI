"""
Health check endpoint pentru Docker.

Docker ruleaza periodic un health check ca sa stie daca containerul e viu.
Daca endpoint-ul ăsta returneaza 200, containerul e marcat ca "healthy".
Daca nu raspunde sau da eroare, Docker poate restarta containerul automat.
"""

from fastapi import APIRouter

# APIRouter = un "mini-FastAPI" pe care il atasam de aplicatia principala.
# Folosim routere ca sa grupam endpoint-uri pe domenii (health, cv, jobs).
router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Returneaza statusul agentului. Folosit de Docker pentru liveness probe."""
    return {"status": "ok"}
