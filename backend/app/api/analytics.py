from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Conversation, Document, KnowledgeBase, Message, User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
def analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    assistant_messages = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.owner_id == user.id, Message.role == "assistant")
        .all()
    )

    total_questions = len(assistant_messages)
    failed_questions = sum(1 for m in assistant_messages if m.grounding_label == "LOW")
    upvotes = sum(1 for m in assistant_messages if m.feedback == "up")
    downvotes = sum(1 for m in assistant_messages if m.feedback == "down")

    avg_total_latency = round(sum(m.total_latency_ms for m in assistant_messages) / total_questions, 1) if total_questions else 0
    avg_retrieval_latency = round(sum(m.retrieval_latency_ms for m in assistant_messages) / total_questions, 1) if total_questions else 0
    avg_generation_latency = round(sum(m.generation_latency_ms for m in assistant_messages) / total_questions, 1) if total_questions else 0
    avg_citations = round(sum(len(m.citations or []) for m in assistant_messages) / total_questions, 2) if total_questions else 0

    kb_counter = Counter(m.conversation.knowledge_base_id for m in assistant_messages)
    kbs = {kb.id: kb.name for kb in db.query(KnowledgeBase).filter(KnowledgeBase.owner_id == user.id).all()}
    most_used_kbs = [{"knowledge_base": kbs.get(kb_id, kb_id), "questions": count} for kb_id, count in kb_counter.most_common(5)]

    # Most referenced documents: count how often each document appears across
    # every citation in every answer, regardless of which KB the question was
    # asked in.
    doc_ref_counter: Counter[str] = Counter()
    for m in assistant_messages:
        for citation in m.citations or []:
            filename = citation.get("filename")
            if filename:
                doc_ref_counter[filename] += 1
    most_referenced_docs = [{"filename": name, "citations": count} for name, count in doc_ref_counter.most_common(5)]

    # Token usage: only counts messages where the provider actually reported
    # usage (None for cached/FAQ-hit answers and providers that don't expose
    # it) — summed separately from the "how many messages had usage data" so
    # the average isn't silently diluted by unmeasured messages.
    messages_with_usage = [m for m in assistant_messages if m.input_tokens is not None and m.output_tokens is not None]
    total_input_tokens = sum(m.input_tokens for m in messages_with_usage)
    total_output_tokens = sum(m.output_tokens for m in messages_with_usage)
    avg_tokens_per_answer = (
        round((total_input_tokens + total_output_tokens) / len(messages_with_usage), 1) if messages_with_usage else 0
    )

    doc_processing_times = (
        db.query(func.avg(Document.processing_time_ms)).filter(Document.owner_id == user.id, Document.status == "COMPLETED").scalar()
    )

    return {
        "questions_asked": total_questions,
        "failed_questions": failed_questions,
        "feedback": {"up": upvotes, "down": downvotes},
        "avg_total_latency_ms": avg_total_latency,
        "avg_retrieval_latency_ms": avg_retrieval_latency,
        "avg_generation_latency_ms": avg_generation_latency,
        "avg_citations_per_answer": avg_citations,
        "most_used_knowledge_bases": most_used_kbs,
        "most_referenced_documents": most_referenced_docs,
        "token_usage": {
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "avg_tokens_per_answer": avg_tokens_per_answer,
            "messages_measured": len(messages_with_usage),
            "messages_total": total_questions,
        },
        "avg_document_processing_time_ms": round(float(doc_processing_times), 1) if doc_processing_times else 0,
    }