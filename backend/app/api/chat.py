from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_knowledge_base
from app.core.database import get_db
from app.models.models import Conversation, Message, User
from app.schemas.schemas import ChatRequest, ChatResponse, ConversationOut, MessageOut
from app.services.rag.agentic import agentic_answer
from app.services.rag.pipeline import answer_question

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    kb = get_owned_knowledge_base(payload.knowledge_base_id, db, user)

    if payload.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id, Conversation.owner_id == user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(knowledge_base_id=kb.id, owner_id=user.id, title=payload.message[:60])
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    history = [
        {"role": m.role, "content": m.content}
        for m in db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.created_at).all()
    ]

    user_msg = Message(conversation_id=conversation.id, role="user", content=payload.message)
    db.add(user_msg)
    db.commit()

    if payload.agentic:
        result = agentic_answer(db, payload.message, kb.id, payload.document_ids)
        timings = {"retrieval_ms": 0, "rerank_ms": 0, "generation_ms": 0, "total_ms": 0}
        debug_trace = []
    else:
        result = answer_question(db, payload.message, kb.id, history, payload.document_ids)
        timings = result["timings"]
        debug_trace = result["debug_trace"]

    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["answer"],
        rewritten_query=result["rewritten_query"],
        citations=result["citations"],
        retrieved_chunks_debug=debug_trace,
        grounding_label=result["grounding_label"],
        grounding_score=result["grounding_score"],
        source_count=result["source_count"],
        retrieval_latency_ms=timings.get("retrieval_ms", 0),
        rerank_latency_ms=timings.get("rerank_ms", 0),
        generation_latency_ms=timings.get("generation_ms", 0),
        total_latency_ms=timings.get("total_ms", 0),
    )
    db.add(assistant_msg)
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assistant_msg)

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
        answer=result["answer"],
        rewritten_query=result["rewritten_query"],
        citations=result["citations"],
        grounding_label=result["grounding_label"],
        grounding_score=result["grounding_score"],
        source_count=result["source_count"],
        retrieved_chunks=result["retrieved_chunks"],
        retrieval_debug=debug_trace,
        latency_ms=timings,
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(knowledge_base_id: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Conversation).filter(Conversation.owner_id == user.id)
    if knowledge_base_id:
        q = q.filter(Conversation.knowledge_base_id == knowledge_base_id)
    return q.order_by(Conversation.updated_at.desc()).all()


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
def get_conversation_messages(conv_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.owner_id == user.id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at).all()


@router.patch("/conversations/{conv_id}")
def rename_conversation(conv_id: str, title: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.owner_id == user.id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation.title = title
    db.commit()
    return {"updated": True}


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.owner_id == user.id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"deleted": True}
