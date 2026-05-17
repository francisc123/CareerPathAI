"""
Cross-encoder reranking between Qdrant ANN (broad recall) and the Gemini LLM
rerank (final precision + reasoning).

Why two rerank stages?
- ANN finds 50 candidates by cosine similarity over embeddings. This is fuzzy.
- A cross-encoder reads (CV, job_text) together and scores them jointly — much
  more precise than two separate embeddings compared via cosine.
- We send only the top-N cross-encoder survivors to Gemini, which is expensive
  per-call. Less context to Gemini → faster, cheaper, more focused output.

Model: BAAI/bge-reranker-v2-m3 (multilingual, ~570MB, ~30-80ms per pair on CPU).
Falls back to passthrough (keeping Qdrant's order) if fastembed is unavailable
or model download fails — we never want this to break the workflow.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

RERANKER_MODEL = os.getenv("RERANKER_MODEL", "Xenova/ms-marco-MiniLM-L-6-v2")
RERANKER_TOP_N = int(os.getenv("RERANKER_TOP_N", "10"))


@lru_cache(maxsize=1)
def _get_reranker():
    """Lazy-load the reranker. Returns None if fastembed isn't installed
    or the model can't be loaded (so callers can degrade gracefully)."""
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder  # type: ignore
    except ImportError:
        logger.warning(
            "fastembed not installed — cross-encoder rerank disabled, "
            "falling back to Qdrant ANN order."
        )
        return None
    try:
        return TextCrossEncoder(model_name=RERANKER_MODEL)
    except Exception:
        logger.exception("Failed to load reranker %s — disabling.", RERANKER_MODEL)
        return None


def _job_to_text(job_payload: dict[str, Any]) -> str:
    """Build a single string from a job payload so the cross-encoder can score it."""
    parts = [
        job_payload.get("title") or "",
        job_payload.get("company") or "",
        job_payload.get("location") or "",
        job_payload.get("description") or "",
    ]
    return " | ".join(p for p in parts if p)


def rerank_candidates(
    cv_text: str,
    candidates: list[Any],
    *,
    top_n: int | None = None,
) -> list[Any]:
    """
    Re-orders `candidates` (Qdrant ScoredPoint or dict-like with `.payload`) by
    cross-encoder relevance to `cv_text`. Returns the top_n best.

    Never raises — falls back to the input order on any error.
    """
    if not candidates:
        return candidates

    reranker = _get_reranker()
    if reranker is None:
        return list(candidates)[: top_n or RERANKER_TOP_N]

    try:
        documents = [
            _job_to_text(getattr(c, "payload", None) or {})
            for c in candidates
        ]
        # fastembed returns an iterable of float scores in the same order as `documents`.
        scores = list(reranker.rerank(cv_text, documents))
    except Exception:
        logger.exception("Cross-encoder scoring failed — keeping ANN order.")
        return list(candidates)[: top_n or RERANKER_TOP_N]

    paired = list(zip(candidates, scores))
    paired.sort(key=lambda item: item[1], reverse=True)
    keep = top_n or RERANKER_TOP_N
    reranked = [c for c, _score in paired[:keep]]
    logger.info(
        "Cross-encoder reranked %d → %d candidates (top score=%.3f, bottom=%.3f).",
        len(candidates), len(reranked),
        paired[0][1] if paired else 0.0,
        paired[len(reranked) - 1][1] if reranked else 0.0,
    )
    return reranked
