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
        "avg_document_processing_time_ms": round(float(doc_processing_times), 1) if doc_processing_times else 0,
    }
