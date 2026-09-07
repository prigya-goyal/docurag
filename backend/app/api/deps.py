from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import KnowledgeBase, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), request: Request = None) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if not user_id:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    if request is not None:
        # Lets the rate limiter key by authenticated user instead of raw IP.
        request.state.user_id = user.id
    return user


def get_owned_knowledge_base(kb_id: str, db: Session, user: User) -> KnowledgeBase:
    """Enforces per-user isolation: a knowledge base is only visible to its owner."""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb