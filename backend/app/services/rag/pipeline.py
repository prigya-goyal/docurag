"""
Orchestrates a single question-answering turn:

  query rewrite -> hybrid retrieval -> rerank -> grounded generation
  -> citation extraction -> grounding score -> debug trace

Every stage is timed so latency can be reported to the user and logged for
analytics, matching the "measure actual values rather than hard-coding
them" requirement.
"""
from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.core.cache import faq_cache, make_key
from app.services.llm.factory import get_llm_provider
from app.services.rag.grounding import compute_grounding, extract_citations
from app.services.rag.prompts import SYSTEM_PROMPT, build_user_prompt
from app.services.retrieval.hybrid import hybrid_retrieve
from app.services.retrieval.query_rewrite import rewrite_query
from app.services.retrieval.rerank import rerank


def answer_question(
    db: Session,
    question: str,
    knowledge_base_id: str,
    history: list[dict],
    document_ids: list[str] | None = None,
) -> dict:
    timings: dict[str, int] = {}
    t0 = time.perf_counter()

    # FAQ cache: only applies to fresh questions with no conversation history,
    # since query rewriting depends on history and would make a cached answer
    # to a follow-up question wrong for a different conversation. Skips
    # retrieval, reranking, AND the LLM generation call entirely on a hit —
    # this is the one that actually saves LLM quota.
    cache_key = None
    if not history:
        cache_key = make_key("faq", knowledge_base_id, question, ",".join(sorted(document_ids or [])))
        cached = faq_cache.get(cache_key)
        if cached is not None:
            result = dict(cached)
            result["timings"] = {"retrieval_ms": 0, "rerank_ms": 0, "generation_ms": 0, "total_ms": 0, "cached": True}
            return result

    rewritten_query = rewrite_query(question, history)

    t1 = time.perf_counter()
    candidates = hybrid_retrieve(db, rewritten_query, knowledge_base_id, document_ids)
    timings["retrieval_ms"] = int((time.perf_counter() - t1) * 1000)

    t2 = time.perf_counter()
    top_chunks = rerank(rewritten_query, candidates)
    timings["rerank_ms"] = int((time.perf_counter() - t2) * 1000)

    t3 = time.perf_counter()
    usage = {"input_tokens": None, "output_tokens": None}
    if not top_chunks:
        answer = "I couldn't find sufficient information about this in the uploaded documents."
    else:
        llm = get_llm_provider()
        user_prompt = build_user_prompt(question, top_chunks)
        answer = llm.generate(system=SYSTEM_PROMPT, user=user_prompt, max_tokens=1024)
        usage = {"input_tokens": llm.last_input_tokens, "output_tokens": llm.last_output_tokens}
    timings["generation_ms"] = int((time.perf_counter() - t3) * 1000)

    citations = extract_citations(top_chunks, answer)
    grounding_label, grounding_score, grounding_reason = compute_grounding(top_chunks, answer)

    timings["total_ms"] = int((time.perf_counter() - t0) * 1000)

    used_chunk_ids = {c["chunk_id"] for c in top_chunks}
    debug_trace = [
        {
            "document_id": c["metadata"].get("document_id"),
            "filename": c["metadata"].get("filename", ""),
            "chunk_id": c["chunk_id"],
            "page_number": c["metadata"].get("page_number", 0),
            "vector_score": c.get("vector_score", 0.0),
            "bm25_score": c.get("bm25_score", 0.0),
            "hybrid_score": c.get("hybrid_score", 0.0),
            "reranker_score": c.get("reranker_score"),
            "used_in_context": c["chunk_id"] in used_chunk_ids,
        }
        for c in candidates[:30]
    ]

    result = {
        "answer": answer,
        "rewritten_query": rewritten_query,
        "citations": citations,
        "grounding_label": grounding_label,
        "grounding_score": grounding_score,
        "grounding_reason": grounding_reason,
        "source_count": len({c["document_id"] for c in citations}),
        "retrieved_chunks": len(top_chunks),
        "debug_trace": debug_trace,
        "timings": timings,
        "usage": usage,
    }

    if cache_key is not None:
        faq_cache.set(cache_key, result)

    return result