"""
Grounding / confidence scoring.

This intentionally does NOT pretend to be a calibrated probability. It's a
transparent heuristic over retrieval signals, mapped to HIGH/MEDIUM/LOW so
users get an honest, interpretable signal rather than a fake precise number.

Score inputs:
  - top reranker score (or hybrid score if reranker disabled)
  - number of distinct supporting sources
  - whether the model itself emitted the "not found" phrase
"""
from __future__ import annotations

import re

NOT_FOUND_PHRASE = "I couldn't find sufficient information about this in the uploaded documents."


def compute_grounding(chunks: list[dict], answer: str) -> tuple[str, float, str]:
    """Returns (label, score, reason)."""
    if NOT_FOUND_PHRASE.lower() in answer.lower():
        return "LOW", 0.0, "No retrieved passage sufficiently supports the requested answer."

    if not chunks:
        return "LOW", 0.0, "No chunks were retrieved for this query."

    top_scores = [c.get("reranker_score") if c.get("reranker_score") is not None else c.get("hybrid_score", 0) for c in chunks]
    top_score = max(top_scores) if top_scores else 0.0
    # normalize reranker scores (roughly -10..10 for MiniLM cross-encoders) into 0..1
    normalized_top = top_score if 0 <= top_score <= 1 else 1 / (1 + pow(2.718281828, -top_score))

    distinct_sources = len({c["metadata"]["document_id"] for c in chunks})
    citation_count = len(re.findall(r"\[\d+\]", answer))

    score = 0.55 * normalized_top + 0.25 * min(distinct_sources / 2, 1.0) + 0.20 * min(citation_count / 2, 1.0)
    score = round(min(score, 1.0), 3)

    if score >= 0.66:
        label = "HIGH"
    elif score >= 0.35:
        label = "MEDIUM"
    else:
        label = "LOW"

    reason = (
        f"Top retrieval score {normalized_top:.2f} across {distinct_sources} source(s), "
        f"{citation_count} inline citation(s)."
    )
    return label, score, reason


def extract_citations(chunks: list[dict], answer: str) -> list[dict]:
    """Builds citation objects from the chunks actually used in context.

    Every citation traces back to a real retrieved chunk_id/page_number —
    never invented — satisfying the "citations must come from actual
    retrieved chunks" requirement.
    """
    cited_indices = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
    citations = []
    for i, c in enumerate(chunks, start=1):
        if cited_indices and i not in cited_indices:
            continue
        meta = c["metadata"]
        citations.append(
            {
                "document_id": meta.get("document_id"),
                "filename": meta.get("filename", ""),
                "page_number": meta.get("page_number", 0),
                "section": meta.get("section", ""),
                "chunk_id": c["chunk_id"],
                "snippet": c["text"][:280],
                "relevance_score": c.get("reranker_score") if c.get("reranker_score") is not None else c.get("hybrid_score", 0),
            }
        )
    # If the model didn't emit bracket citations, fall back to top chunks so the
    # UI still shows real supporting sources rather than nothing at all.
    if not citations:
        for c in chunks[:3]:
            meta = c["metadata"]
            citations.append(
                {
                    "document_id": meta.get("document_id"),
                    "filename": meta.get("filename", ""),
                    "page_number": meta.get("page_number", 0),
                    "section": meta.get("section", ""),
                    "chunk_id": c["chunk_id"],
                    "snippet": c["text"][:280],
                    "relevance_score": c.get("reranker_score") if c.get("reranker_score") is not None else c.get("hybrid_score", 0),
                }
            )
    return citations
