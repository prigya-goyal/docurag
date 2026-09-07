"""
RAG evaluation engine.

Every metric below is computed from an actual pipeline run against the
user-authored evaluation dataset — nothing here is a hard-coded or
fabricated number, per the "Do not fabricate these values" requirement.

Metrics:
  - Retrieval Recall: did the final context include a chunk from the
    expected supporting document/page?
  - Context Precision: what fraction of chunks used in context came from
    the expected document (precision of what was retrieved)?
  - Answer Faithfulness: LLM-judged — does the answer only state things
    supported by the retrieved context?
  - Citation Accuracy: do the emitted citations point at the expected
    document/page?
  - Answer Relevance: LLM-judged — does the answer actually address the
    question asked?
  - Unanswerable Detection: for questions marked not answerable, did the
    system correctly refuse rather than fabricate an answer?
"""
from __future__ import annotations

import re
import time

from sqlalchemy.orm import Session

from app.models.models import EvalQuestion
from app.services.llm.factory import get_llm_provider
from app.services.rag.pipeline import answer_question

JUDGE_SYSTEM_PROMPT = """You are an evaluation judge for a RAG system. You will be given a QUESTION,
the CONTEXT excerpts the system retrieved, and the ANSWER it generated. Score two things on a 0.0-1.0
scale each:
  faithfulness: does the answer ONLY state things that are supported by the context (no fabrication)?
  relevance: does the answer actually address what the question asked?
Respond ONLY with JSON: {"faithfulness": 0.0-1.0, "relevance": 0.0-1.0}"""


def _judge_answer(question: str, context_texts: list[str], answer: str) -> tuple[float, float]:
    import json

    llm = get_llm_provider()
    context_str = "\n---\n".join(context_texts)
    prompt = f"QUESTION: {question}\n\nCONTEXT:\n{context_str}\n\nANSWER: {answer}"
    try:
        raw = llm.generate(system=JUDGE_SYSTEM_PROMPT, user=prompt, max_tokens=100)
        parsed = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        return float(parsed.get("faithfulness", 0)), float(parsed.get("relevance", 0))
    except Exception:
        return 0.0, 0.0


def _filenames_match(expected: str, actual: str) -> bool:
    """Loose filename matching so eval questions don't have to reproduce a
    stored filename byte-for-byte (numbering prefixes like '16. ', extra
    spaces, or case differences shouldn't cause a false negative on an
    otherwise-correct retrieval). Normalizes by lowercasing and stripping
    everything except alphanumerics, then checks substring containment
    either direction.
    """
    def normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    exp, act = normalize(expected), normalize(actual)
    if not exp or not act:
        return False
    return exp in act or act in exp


def run_evaluation(db: Session, knowledge_base_id: str, config: dict | None = None) -> dict:
    questions = db.query(EvalQuestion).filter(EvalQuestion.knowledge_base_id == knowledge_base_id).all()
    if not questions:
        return {
            "questions_tested": 0,
            "retrieval_recall": 0.0,
            "context_precision": 0.0,
            "answer_faithfulness": 0.0,
            "citation_accuracy": 0.0,
            "answer_relevance": 0.0,
            "unanswerable_detection": 0.0,
            "avg_latency_ms": 0.0,
            "details": [],
        }

    recall_hits, precision_scores, faithfulness_scores, relevance_scores, citation_scores = [], [], [], [], []
    unanswerable_correct, unanswerable_total = 0, 0
    latencies = []
    details = []

    for eq in questions:
        t0 = time.perf_counter()
        result = answer_question(db, eq.question, knowledge_base_id, history=[])
        latency_ms = int((time.perf_counter() - t0) * 1000)
        latencies.append(latency_ms)

        used_chunks = [c for c in result["debug_trace"] if c["used_in_context"]]
        retrieved_docs = {c["filename"] for c in used_chunks}
        retrieved_pages = {(c["filename"], c["page_number"]) for c in used_chunks}

        if eq.is_answerable:
            hit = any(_filenames_match(eq.expected_document, d) for d in retrieved_docs) if eq.expected_document else bool(used_chunks)
            recall_hits.append(1.0 if hit else 0.0)

            relevant = (
                sum(1 for c in used_chunks if _filenames_match(eq.expected_document, c["filename"]))
                if eq.expected_document
                else len(used_chunks)
            )
            precision_scores.append(relevant / len(used_chunks) if used_chunks else 0.0)

            faithfulness, relevance = _judge_answer(eq.question, [c["snippet"] for c in result["citations"]] or [c.get("text", "") for c in used_chunks], result["answer"])
            faithfulness_scores.append(faithfulness)
            relevance_scores.append(relevance)

            if eq.expected_document and eq.expected_page:
                cited_correctly = any(
                    _filenames_match(eq.expected_document, c["filename"]) and c["page_number"] == eq.expected_page
                    for c in result["citations"]
                )
                citation_scores.append(1.0 if cited_correctly else 0.0)
        else:
            unanswerable_total += 1
            correctly_refused = result["grounding_label"] == "LOW"
            if correctly_refused:
                unanswerable_correct += 1

        details.append(
            {
                "question": eq.question,
                "is_answerable": eq.is_answerable,
                "answer": result["answer"],
                "grounding_label": result["grounding_label"],
                "expected_document": eq.expected_document,
                "retrieved_documents": list(retrieved_docs),
                "latency_ms": latency_ms,
            }
        )

    def avg(lst):
        return round(sum(lst) / len(lst), 3) if lst else 0.0

    return {
        "questions_tested": len(questions),
        "retrieval_recall": avg(recall_hits),
        "context_precision": avg(precision_scores),
        "answer_faithfulness": avg(faithfulness_scores),
        "citation_accuracy": avg(citation_scores) if citation_scores else 0.0,
        "answer_relevance": avg(relevance_scores),
        "unanswerable_detection": round(unanswerable_correct / unanswerable_total, 3) if unanswerable_total else 0.0,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
        "details": details,
    }