"""
OCR fallback for scanned/image-based PDF pages.

Only invoked for pages flagged `needs_ocr=True` by the extractor (i.e. pages
where native text extraction returned too little text). Page boundaries and
page numbers are preserved so citations and the source viewer still work
identically for OCR'd content.
"""
from __future__ import annotations

import io
import logging

import fitz
import pytesseract
from PIL import Image

from app.services.ingestion.extract import ExtractionResult

logger = logging.getLogger(__name__)

OCR_DPI_ZOOM = 2.0  # ~150 DPI equivalent; higher improves accuracy at the cost of speed


def ocr_pdf_pages(path: str, result: ExtractionResult) -> ExtractionResult:
    """Mutates `result` in place: fills in text for pages flagged needs_ocr."""
    pages_needing_ocr = [p for p in result.pages if p.needs_ocr]
    if not pages_needing_ocr:
        return result

    doc = fitz.open(path)
    matrix = fitz.Matrix(OCR_DPI_ZOOM, OCR_DPI_ZOOM)

    for page_content in pages_needing_ocr:
        try:
            pdf_page = doc[page_content.page_number - 1]
            pix = pdf_page.get_pixmap(matrix=matrix)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text = pytesseract.image_to_string(image)
            page_content.text = ocr_text.strip()
            result.used_ocr = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("OCR failed for page %s: %s", page_content.page_number, exc)
            page_content.text = page_content.text or ""

    doc.close()
    return result
