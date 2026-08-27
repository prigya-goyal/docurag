from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_knowledge_base
from app.core.database import get_db
from app.models.models import Document, KnowledgeBase, User
from app.services.vectorstore.chroma_store import get_vector_store
from app.schemas.schemas import KnowledgeBaseCreate, KnowledgeBaseOut, KnowledgeBaseUpdate

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])


def _to_out(db: Session, kb: KnowledgeBase) -> KnowledgeBaseOut:
    doc_count = db.query(func.count(Document.id)).filter(Document.knowledge_base_id == kb.id).scalar()
    out = KnowledgeBaseOut.model_validate(kb)
    out.document_count = doc_count or 0
    return out


@router.get("", response_model=list[KnowledgeBaseOut])
def list_knowledge_bases(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    kbs = db.query(KnowledgeBase).filter(KnowledgeBase.owner_id == user.id).order_by(KnowledgeBase.updated_at.desc()).all()
    return [_to_out(db, kb) for kb in kbs]


@router.post("", response_model=KnowledgeBaseOut)
def create_knowledge_base(payload: KnowledgeBaseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    kb = KnowledgeBase(owner_id=user.id, name=payload.name, description=payload.description)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return _to_out(db, kb)


@router.get("/{kb_id}", response_model=KnowledgeBaseOut)
def get_knowledge_base(kb_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    kb = get_owned_knowledge_base(kb_id, db, user)
    return _to_out(db, kb)


@router.patch("/{kb_id}", response_model=KnowledgeBaseOut)
def update_knowledge_base(kb_id: str, payload: KnowledgeBaseUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    kb = get_owned_knowledge_base(kb_id, db, user)
    if payload.name is not None:
        kb.name = payload.name
    if payload.description is not None:
        kb.description = payload.description
    db.commit()
    db.refresh(kb)
    return _to_out(db, kb)


@router.delete("/{kb_id}")
def delete_knowledge_base(kb_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    kb = get_owned_knowledge_base(kb_id, db, user)
    get_vector_store().delete_by_knowledge_base(kb.id)
    db.delete(kb)
    db.commit()
    return {"deleted": True}
