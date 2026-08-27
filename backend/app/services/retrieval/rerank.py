"""
Reranking stage: takes the top 20-30 hybrid candidates and re-scores each
(query, chunk) pair with a cross-encoder, which is far more accurate than
bi-encoder similarity because it attends over the query and passage jointly.
Only the top RERANK_TOP_K survive to become LLM context.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings


@lru_cache
def _get_cross_encoder(model_name: str):
    from sentence_transformers import CrossEncoder  # lazy import: heavy dependency

    return CrossEncoder(model_name)


def rerank(query: str, candidates: list[dict]) -> list[dict]:
    settings = get_settings()

    if not settings.RERANKER_ENABLED or not candidates:
        # Reranker disabled: fall back to hybrid_score order (still populate the
        # field so the retrieval debugger UI has a consistent shape).
        for c in candidates:
            c["reranker_score"] = None
        return candidates[: settings.RERANK_TOP_K]

    model = _get_cross_encoder(settings.RERANKER_MODEL)
    pairs = [(query, c["text"]) for c in candidates]
    scores = model.predict(pairs)

    for c, score in zip(candidates, scores):
        c["reranker_score"] = round(float(score), 4)

    candidates.sort(key=lambda c: c["reranker_score"], reverse=True)
    return candidates[: settings.RERANK_TOP_K]
