from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Chunk, Conversation, Document, KnowledgeBase, Message, User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    kb_ids = [kb.id for kb in db.query(KnowledgeBase.id).filter(KnowledgeBase.owner_id == user.id).all()]

    total_documents = db.query(func.count(Document.id)).filter(Document.owner_id == user.id).scalar() or 0
    total_pages = db.query(func.sum(Document.page_count)).filter(Document.owner_id == user.id).scalar() or 0
    total_chunks = db.query(func.sum(Document.chunk_count)).filter(Document.owner_id == user.id).scalar() or 0

    questions_asked = (
        db.query(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.owner_id == user.id, Message.role == "assistant")
        .scalar()
        or 0
    )

    avg_grounding = (
        db.query(func.avg(Message.grounding_score))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.owner_id == user.id, Message.role == "assistant")
        .scalar()
    )

    recent_documents = (
        db.query(Document).filter(Document.owner_id == user.id).order_by(Document.created_at.desc()).limit(5).all()
    )
    recent_conversations = (
        db.query(Conversation).filter(Conversation.owner_id == user.id).order_by(Conversation.updated_at.desc()).limit(5).all()
    )

    processing_counts = (
        db.query(Document.status, func.count(Document.id))
        .filter(Document.owner_id == user.id)
        .group_by(Document.status)
        .all()
    )

    return {
        "knowledge_bases": len(kb_ids),
        "documents": total_documents,
        "pages": int(total_pages),
        "indexed_chunks": int(total_chunks),
        "questions_asked": questions_asked,
        "average_retrieval_score": round(float(avg_grounding), 2) if avg_grounding else 0.0,
        "recent_documents": [{"id": d.id, "filename": d.filename, "status": d.status} for d in recent_documents],
        "recent_conversations": [{"id": c.id, "title": c.title, "updated_at": c.updated_at} for c in recent_conversations],
        "processing_status": {str(status): count for status, count in processing_counts},
    }
