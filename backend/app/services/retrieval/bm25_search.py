"""
BM25 keyword search.

Good for exact names, IDs, numbers, acronyms, and specific phrases that
dense/semantic vector search can under-rank because it optimizes for
conceptual similarity rather than lexical overlap.

The index is rebuilt from the `chunks` table per knowledge base at query
time. This keeps the implementation simple and always-consistent with the
relational store; at production scale you'd cache/persist this index and
invalidate it on document add/remove instead of rebuilding every query.
"""
from __future__ import annotations

import re

from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session

from app.models.models import Chunk, Document


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def bm25_search(
    db: Session,
    query: str,
    knowledge_base_id: str,
    n_results: int,
    document_ids: list[str] | None = None,
) -> list[dict]:
    q = db.query(Chunk, Document).join(Document, Chunk.document_id == Document.id).filter(
        Chunk.knowledge_base_id == knowledge_base_id
    )
    if document_ids:
        q = q.filter(Chunk.document_id.in_(document_ids))

    rows = q.all()
    if not rows:
        return []

    corpus_tokens = [_tokenize(chunk.text) for chunk, _ in rows]
    bm25 = BM25Okapi(corpus_tokens)
    scores = bm25.get_scores(_tokenize(query))

    max_score = max(scores) if len(scores) and max(scores) > 0 else 1.0
    ranked = sorted(zip(rows, scores), key=lambda x: x[1], reverse=True)[:n_results]

    return [
        {
            "chunk_id": chunk.id,
            "text": chunk.text,
            "metadata": {
                "document_id": chunk.document_id,
                "knowledge_base_id": chunk.knowledge_base_id,
                "filename": doc.filename,
                "page_number": chunk.page_number,
                "section": chunk.section,
                "heading": chunk.heading,
            },
            "bm25_score": round(float(score) / max_score, 4) if max_score else 0.0,
        }
        for (chunk, doc), score in ranked
        if score > 0
    ]
