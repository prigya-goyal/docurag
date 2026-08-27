"""
Text extraction layer.

Every extractor returns a list of `PageContent` objects so downstream
chunking always has consistent page/section metadata to attach to chunks,
regardless of source format. For formats with no natural notion of a
"page" (txt, md, csv) we treat the whole file, or logical row-groups, as
page 1..N equivalents so the rest of the pipeline doesn't need special
cases.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd
from docx import Document as DocxDocument
from pptx import Presentation


@dataclass
class PageContent:
    page_number: int
    text: str
    heading: str = ""
    section: str = ""
    needs_ocr: bool = False


@dataclass
class ExtractionResult:
    pages: list[PageContent] = field(default_factory=list)
    author: str = ""
    used_ocr: bool = False


MIN_CHARS_PER_PAGE = 20  # below this, PDF page is considered "insufficient text" -> OCR fallback


def extract_pdf(path: str) -> ExtractionResult:
    doc = fitz.open(path)
    pages: list[PageContent] = []
    author = (doc.metadata or {}).get("author", "") or ""

    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        needs_ocr = len(text) < MIN_CHARS_PER_PAGE
        heading = _guess_heading(page)
        pages.append(PageContent(page_number=i, text=text, heading=heading, needs_ocr=needs_ocr))

    doc.close()
    return ExtractionResult(pages=pages, author=author)


def _guess_heading(page: "fitz.Page") -> str:
    """Heuristic: the largest-font line on a page is likely a heading."""
    try:
        blocks = page.get_text("dict")["blocks"]
        best_text, best_size = "", 0.0
        for b in blocks:
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    if span["size"] > best_size and span["text"].strip():
                        best_size = span["size"]
                        best_text = span["text"].strip()
        return best_text[:120]
    except Exception:
        return ""


def extract_docx(path: str) -> ExtractionResult:
    doc = DocxDocument(path)
    pages: list[PageContent] = []
    current_heading = ""
    buffer: list[str] = []
    page_num = 1

    def flush():
        nonlocal buffer, page_num
        if buffer:
            pages.append(PageContent(page_number=page_num, text="\n".join(buffer), heading=current_heading))
            buffer = []
            page_num += 1

    for para in doc.paragraphs:
        style = (para.style.name or "").lower() if para.style else ""
        if style.startswith("heading") and buffer:
            flush()
        if style.startswith("heading"):
            current_heading = para.text.strip()
        if para.text.strip():
            buffer.append(para.text.strip())

    flush()
    if not pages:
        pages = [PageContent(page_number=1, text="")]

    core_props = doc.core_properties
    return ExtractionResult(pages=pages, author=core_props.author or "")


def extract_pptx(path: str) -> ExtractionResult:
    prs = Presentation(path)
    pages: list[PageContent] = []

    for i, slide in enumerate(prs.slides, start=1):
        texts = []
        heading = ""
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                t = "".join(run.text for run in para.runs).strip()
                if t:
                    texts.append(t)
                    if not heading and shape == slide.shapes.title:
                        heading = t
        pages.append(PageContent(page_number=i, text="\n".join(texts), heading=heading, section=f"Slide {i}"))

    return ExtractionResult(pages=pages)


def extract_txt_md(path: str) -> ExtractionResult:
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    # Split on markdown-style headings to create pseudo "pages"/sections when possible
    lines = text.split("\n")
    pages: list[PageContent] = []
    heading, buffer = "", []
    page_num = 1

    def flush():
        nonlocal buffer, page_num
        if buffer:
            pages.append(PageContent(page_number=page_num, text="\n".join(buffer).strip(), heading=heading))
            buffer = []
            page_num += 1

    for line in lines:
        if line.strip().startswith("#"):
            if buffer:
                flush()
            heading = line.strip("# ").strip()
        buffer.append(line)

    flush()
    if not pages:
        pages = [PageContent(page_number=1, text=text)]
    return ExtractionResult(pages=pages)


def extract_csv(path: str) -> ExtractionResult:
    df = pd.read_csv(path)
    # Group rows into pages of ~50 rows so a CSV is chunked like any other document
    rows_per_page = 50
    pages: list[PageContent] = []
    for i in range(0, len(df), rows_per_page):
        chunk_df = df.iloc[i : i + rows_per_page]
        text = chunk_df.to_string(index=False)
        pages.append(
            PageContent(
                page_number=(i // rows_per_page) + 1,
                text=text,
                heading=f"Rows {i + 1}-{min(i + rows_per_page, len(df))}",
                section="CSV data",
            )
        )
    if not pages:
        pages = [PageContent(page_number=1, text=df.to_string(index=False))]
    return ExtractionResult(pages=pages)


EXTRACTORS = {
    ".pdf": extract_pdf,
    ".docx": extract_docx,
    ".pptx": extract_pptx,
    ".txt": extract_txt_md,
    ".md": extract_txt_md,
    ".csv": extract_csv,
}


def extract(path: str, file_ext: str) -> ExtractionResult:
    extractor = EXTRACTORS.get(file_ext.lower())
    if not extractor:
        raise ValueError(f"Unsupported file type: {file_ext}")
    return extractor(path)
