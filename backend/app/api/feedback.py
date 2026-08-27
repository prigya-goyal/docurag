from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Conversation, Message, User
from app.schemas.schemas import FeedbackCreate

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

VALID_REASONS = {"incorrect_answer", "wrong_source", "missing_information", "poor_explanation", "hallucination"}


@router.post("")
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.feedback not in {"up", "down"}:
        raise HTTPException(status_code=400, detail="feedback must be 'up' or 'down'")
    if payload.feedback == "down" and payload.reason and payload.reason not in VALID_REASONS:
        raise HTTPException(status_code=400, detail=f"reason must be one of {VALID_REASONS}")

    message = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Message.id == payload.message_id, Conversation.owner_id == user.id)
        .first()
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.feedback = payload.feedback
    message.feedback_reason = payload.reason or ""
    db.commit()
    return {"saved": True}
