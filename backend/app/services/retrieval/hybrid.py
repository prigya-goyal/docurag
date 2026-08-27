"""
Hybrid retrieval: fuses semantic (vector) and keyword (BM25) candidate sets.

Each retriever is queried independently for `RETRIEVAL_CANDIDATES` results,
then merged by chunk_id. Missing scores (a chunk that only one retriever
surfaced) default to 0 for the other signal rather than being dropped —
this is what lets BM25 rescue an exact-match chunk that vector search
ranked poorly, and vice versa.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

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
    return candidates
