import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_knowledge_base
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.models import Document, ProcessingStatus, User
from app.schemas.schemas import DocumentOut
from app.services.processing.pipeline import delete_document_from_indexes, process_document

router = APIRouter(prefix="/api/knowledge-bases/{kb_id}/documents", tags=["documents"])
settings = get_settings()


def _validate_upload(file: UploadFile, size_bytes: int) -> str:
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Allowed: {settings.ALLOWED_EXTENSIONS}")
    if size_bytes > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")
    return ext


@router.post("/upload", response_model=list[DocumentOut])
@limiter.limit("20/minute")
async def upload_documents(
    request: Request,
    kb_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb = get_owned_knowledge_base(kb_id, db, user)
    upload_dir = Path(settings.UPLOAD_DIR) / kb.id
    upload_dir.mkdir(parents=True, exist_ok=True)

    created: list[Document] = []
    for file in files:
        content = await file.read()
        ext = _validate_upload(file, len(content))

        storage_path = upload_dir / f"{uuid.uuid4()}{ext}"
        storage_path.write_bytes(content)

        doc = Document(
            knowledge_base_id=kb.id,
            owner_id=user.id,
            filename=file.filename,
            file_type=ext.lstrip("."),
            file_size_bytes=len(content),
            storage_path=str(storage_path),
            status=ProcessingStatus.UPLOADING,
            progress_pct=5,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        created.append(doc)

        # Async, non-blocking: the client polls GET /documents/{id} for status.
        background_tasks.add_task(process_document, doc.id)

    return created


@router.get("", response_model=list[DocumentOut])
def list_documents(kb_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    kb = get_owned_knowledge_base(kb_id, db, user)
    return db.query(Document).filter(Document.knowledge_base_id == kb.id).order_by(Document.created_at.desc()).all()


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(kb_id: str, doc_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_knowledge_base(kb_id, db, user)
    doc = db.query(Document).filter(Document.id == doc_id, Document.knowledge_base_id == kb_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}")
def delete_document(kb_id: str, doc_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_knowledge_base(kb_id, db, user)
    doc = db.query(Document).filter(Document.id == doc_id, Document.knowledge_base_id == kb_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_from_indexes(doc.id)
    Path(doc.storage_path).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
    return {"deleted": True}


@router.get("/{doc_id}/content")
def get_document_content(kb_id: str, doc_id: str, page: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Backs the source viewer: returns the raw file path info + (optionally)
    the extracted text for a specific page so the frontend can render/jump
    to it without re-parsing the file client-side."""
    get_owned_knowledge_base(kb_id, db, user)
    doc = db.query(Document).filter(Document.id == doc_id, Document.knowledge_base_id == kb_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    from app.models.models import Chunk

    q = db.query(Chunk).filter(Chunk.document_id == doc.id)
    if page is not None:
        q = q.filter(Chunk.page_number == page)
    chunks = q.order_by(Chunk.chunk_index).all()

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "page_count": doc.page_count,
        "page": page,
        "chunks": [
            {"chunk_id": c.id, "page_number": c.page_number, "section": c.section, "heading": c.heading, "text": c.text}
            for c in chunks
        ],
    }
