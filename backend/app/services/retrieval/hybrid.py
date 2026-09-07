from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.cache import make_key, retrieval_cache
from app.core.config import get_settings
from app.services.embeddings.factory import get_embedding_provider
from app.services.retrieval.bm25_search import bm25_search
from app.services.vectorstore.chroma_store import get_vector_store


def hybrid_retrieve(
    db: Session,
    query: str,
    knowledge_base_id: str,
    document_ids: list[str] | None = None,
) -> list[dict]:
    settings = get_settings()

    # Cache repeated retrieval queries (spec section 31): identical question
    # + KB + document filter within the TTL window skips vector search, BM25,
    # and the merge/scoring step entirely.
    cache_key = make_key(
        "hybrid_retrieve", knowledge_base_id, query, ",".join(sorted(document_ids or []))
    )
    cached = retrieval_cache.get(cache_key)
    if cached is not None:
        return cached

    n = settings.RETRIEVAL_CANDIDATES

    embedder = get_embedding_provider()
    query_vec = embedder.embed_query(query)

    vector_hits = get_vector_store().query(
        query_embedding=query_vec,
        n_results=n,
        knowledge_base_id=knowledge_base_id,
        document_ids=document_ids,
    )
    keyword_hits = bm25_search(
        db=db, query=query, knowledge_base_id=knowledge_base_id, n_results=n, document_ids=document_ids
    )

    merged: dict[str, dict] = {}

    for hit in vector_hits:
        merged[hit["chunk_id"]] = {
            "chunk_id": hit["chunk_id"],
            "text": hit["text"],
            "metadata": hit["metadata"],
            "vector_score": hit["vector_score"],
            "bm25_score": 0.0,
        }

    for hit in keyword_hits:
        if hit["chunk_id"] in merged:
            merged[hit["chunk_id"]]["bm25_score"] = hit["bm25_score"]
        else:
            merged[hit["chunk_id"]] = {
                "chunk_id": hit["chunk_id"],
                "text": hit["text"],
                "metadata": hit["metadata"],
                "vector_score": 0.0,
                "bm25_score": hit["bm25_score"],
            }

    candidates = list(merged.values())
    for c in candidates:
        c["hybrid_score"] = round(
            settings.HYBRID_VECTOR_WEIGHT * c["vector_score"] + settings.HYBRID_KEYWORD_WEIGHT * c["bm25_score"], 4
        )

    candidates.sort(key=lambda c: c["hybrid_score"], reverse=True)
    retrieval_cache.set(cache_key, candidates)
    return candidates