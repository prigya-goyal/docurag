"""
Agentic retrieval (optional, Phase 5).

A deliberately small planner: decides whether a question needs one search
or several (e.g. "What changed between the 2025 and 2026 policy?" needs a
search scoped to each document), runs each sub-query through the standard
pipeline's retrieval+rerank stages, then asks the LLM to synthesize a single
grounded answer across all gathered evidence. Kept modular and capped at a
small number of sub-queries so it can't spiral into unbounded tool calls.
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.services.llm.factory import get_llm_provider
from app.services.rag.grounding import compute_grounding, extract_citations
from app.services.rag.prompts import SYSTEM_PROMPT, build_context_block
from app.services.retrieval.hybrid import hybrid_retrieve
from app.services.retrieval.rerank import rerank

MAX_SUB_QUERIES = 3

PLANNER_PROMPT = """Decide how many separate retrieval searches this question needs (1-3) and
what each search query should be. Respond ONLY with JSON: {"queries": ["...", "..."]}."""


def plan_sub_queries(question: str) -> list[str]:
    try:
        llm = get_llm_provider()
        raw = llm.generate(system=PLANNER_PROMPT, user=question, max_tokens=200)
        parsed = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        queries = [q for q in parsed.get("queries", []) if q.strip()][:MAX_SUB_QUERIES]
        return queries or [question]
    except Exception:
        return [question]


def agentic_answer(db: Session, question: str, knowledge_base_id: str, document_ids: list[str] | None) -> dict:
    sub_queries = plan_sub_queries(question)

    all_chunks: list[dict] = []
    seen_ids: set[str] = set()
    for sq in sub_queries:
        candidates = hybrid_retrieve(db, sq, knowledge_base_id, document_ids)
        top = rerank(sq, candidates)
        for c in top:
            if c["chunk_id"] not in seen_ids:
                seen_ids.add(c["chunk_id"])
                all_chunks.append(c)

    llm = get_llm_provider()
    context_block = build_context_block(all_chunks)
    user_prompt = (
        f"{context_block}\n\nOriginal question: {question}\n\n"
        f"This question was broken into sub-queries: {sub_queries}\n"
        "Synthesize one grounded answer using only the excerpts above, citing excerpt numbers like [1]."
    )
    answer = llm.generate(system=SYSTEM_PROMPT, user=user_prompt, max_tokens=1200)

    citations = extract_citations(all_chunks, answer)
    grounding_label, grounding_score, grounding_reason = compute_grounding(all_chunks, answer)

    return {
        "answer": answer,
        "rewritten_query": " | ".join(sub_queries),
        "citations": citations,
        "grounding_label": grounding_label,
        "grounding_score": grounding_score,
        "grounding_reason": grounding_reason,
        "source_count": len({c["document_id"] for c in citations}),
        "retrieved_chunks": len(all_chunks),
        "sub_queries": sub_queries,
    }
