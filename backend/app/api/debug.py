from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_knowledge_base
from app.core.database import get_db
from app.models.models import Conversation, Message, User
from app.services.rag.pipeline import answer_question

router = APIRouter(prefix="/api/knowledge-bases/{kb_id}/debug", tags=["debug"])


@router.get("/retrieve")
def debug_retrieve(kb_id: str, q: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Runs the full pipeline for a question and returns the internal trace:
    candidates with vector/BM25/reranker scores, which chunks made the final
    context, the generated answer, and citations — for the developer/admin
    retrieval debugger page."""
    get_owned_knowledge_base(kb_id, db, user)
    result = answer_question(db, q, kb_id, history=[])
    return {
        "query": q,
        "rewritten_query": result["rewritten_query"],
        "candidates": result["debug_trace"],
        "final_context_chunk_ids": [c["chunk_id"] for c in result["debug_trace"] if c["used_in_context"]],
        "answer": result["answer"],
        "citations": result["citations"],
        "grounding_label": result["grounding_label"],
        "grounding_score": result["grounding_score"],
        "timings_ms": result["timings"],
    }


@router.get("/failed-queries")
def failed_queries(kb_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Surfaces low-grounding / 'not found' answers for developers to review."""
    get_owned_knowledge_base(kb_id, db, user)
    messages = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.knowledge_base_id == kb_id, Message.role == "assistant", Message.grounding_label == "LOW")
        .order_by(Message.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {"message_id": m.id, "question": m.rewritten_query, "answer": m.content, "created_at": m.created_at}
        for m in messages
    ]
