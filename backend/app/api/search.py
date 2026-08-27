from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_knowledge_base
from app.core.database import get_db
from app.models.models import Document, User
from app.services.retrieval.hybrid import hybrid_retrieve

router = APIRouter(prefix="/api/knowledge-bases/{kb_id}/search", tags=["search"])


@router.get("")
def search(
    kb_id: str,
    q: str,
    document_id: str | None = None,
    file_type: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Raw hybrid-retrieval search over a knowledge base with optional
    metadata filters (document, file type). Used by the UI's search box and
    the 'search within a specific knowledge base' feature."""
    kb = get_owned_knowledge_base(kb_id, db, user)

    document_ids = None
    if document_id:
        document_ids = [document_id]
    elif file_type:
        docs = db.query(Document).filter(Document.knowledge_base_id == kb.id, Document.file_type == file_type).all()
        document_ids = [d.id for d in docs]

    results = hybrid_retrieve(db, q, kb.id, document_ids)
    return {
        "query": q,
        "results": [
            {
                "chunk_id": r["chunk_id"],
                "text": r["text"][:400],
                "filename": r["metadata"].get("filename"),
                "page_number": r["metadata"].get("page_number"),
                "section": r["metadata"].get("section"),
                "vector_score": r["vector_score"],
                "bm25_score": r["bm25_score"],
                "hybrid_score": r["hybrid_score"],
            }
            for r in results[:20]
        ],
    }
