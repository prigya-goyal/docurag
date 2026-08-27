"""
End-to-end document processing pipeline, run in a background task so
uploads never block the request/response cycle:

  validate -> extract text -> OCR fallback -> chunk -> embed -> index
  (vector store + relational chunk rows for BM25/citations) -> mark COMPLETED

Every stage updates `Document.status` / `progress_pct` so the frontend can
poll and render the exact status enum required by the spec (UPLOADING,
PROCESSING, OCR, CHUNKING, EMBEDDING, INDEXING, COMPLETED, FAILED).
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.models import Chunk, Document, ProcessingStatus
from app.services.embeddings.factory import get_embedding_provider
from app.services.ingestion.chunking import chunk_pages
from app.services.ingestion.extract import extract
from app.services.ingestion.ocr import ocr_pdf_pages
from app.services.vectorstore.chroma_store import get_vector_store

logger = logging.getLogger(__name__)


def _set_status(db: Session, doc: Document, status: ProcessingStatus, progress: int, detail: str = ""):
    doc.status = status
    doc.progress_pct = progress
    doc.status_detail = detail
    db.commit()


def process_document(document_id: str) -> None:
    """Entry point invoked as a background task (see workers/background.py)."""
    db = SessionLocal()
    settings = get_settings()
    start = time.perf_counter()

    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error("Document %s not found for processing", document_id)
            return

        _set_status(db, doc, ProcessingStatus.PROCESSING, 10, "Extracting text")
        file_ext = Path(doc.storage_path).suffix.lower()
        result = extract(doc.storage_path, file_ext)

        needs_ocr = any(p.needs_ocr for p in result.pages)
        if needs_ocr and file_ext == ".pdf":
            _set_status(db, doc, ProcessingStatus.OCR, 30, "Running OCR on scanned pages")
            result = ocr_pdf_pages(doc.storage_path, result)

        _set_status(db, doc, ProcessingStatus.CHUNKING, 50, "Splitting into structure-aware chunks")
        chunks = chunk_pages(result.pages, chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)

        if not chunks:
            _set_status(db, doc, ProcessingStatus.FAILED, 100, "No extractable text found in document")
            return

        _set_status(db, doc, ProcessingStatus.EMBEDDING, 70, f"Generating embeddings for {len(chunks)} chunks")
        embedder = get_embedding_provider()
        embeddings = embedder.embed_documents([c.text for c in chunks])

        _set_status(db, doc, ProcessingStatus.INDEXING, 90, "Indexing vectors and keywords")

        chunk_rows: list[Chunk] = []
        for c in chunks:
            chunk_rows.append(
                Chunk(
                    document_id=doc.id,
                    knowledge_base_id=doc.knowledge_base_id,
                    text=c.text,
                    page_number=c.page_number,
                    section=c.section,
                    heading=c.heading,
                    chunk_index=c.chunk_index,
                )
            )
        db.add_all(chunk_rows)
        db.commit()
        for row in chunk_rows:
            db.refresh(row)

        vector_store = get_vector_store()
        vector_store.upsert(
            ids=[row.id for row in chunk_rows],
            embeddings=embeddings,
            documents=[row.text for row in chunk_rows],
            metadatas=[
                {
                    "document_id": doc.id,
                    "knowledge_base_id": doc.knowledge_base_id,
                    "filename": doc.filename,
                    "page_number": row.page_number,
                    "section": row.section or "",
                    "heading": row.heading or "",
                }
                for row in chunk_rows
            ],
        )

        doc.page_count = len(result.pages)
        doc.chunk_count = len(chunk_rows)
        doc.used_ocr = result.used_ocr
        doc.author = result.author
        doc.processing_time_ms = int((time.perf_counter() - start) * 1000)
        _set_status(db, doc, ProcessingStatus.COMPLETED, 100, "Ready")

    except Exception as exc:  # noqa: BLE001
        logger.exception("Processing failed for document %s", document_id)
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            _set_status(db, doc, ProcessingStatus.FAILED, 100, f"Processing failed: {exc}")
    finally:
        db.close()


def delete_document_from_indexes(document_id: str) -> None:
    get_vector_store().delete_by_document(document_id)
