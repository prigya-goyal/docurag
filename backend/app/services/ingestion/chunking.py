"""
Structure-aware chunking.

Rather than blindly splitting on a fixed character count, chunking follows:

    Document -> Page/Section -> Paragraph -> Chunk

Paragraphs within a page/section are greedily packed into chunks up to
`chunk_size` characters, with `chunk_overlap` characters of trailing context
carried into the next chunk so retrieval doesn't lose meaning at boundaries.
A paragraph longer than `chunk_size` on its own is hard-split as a last
resort. Every chunk keeps a reference to its page number, section, and
heading for citations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.ingestion.extract import PageContent


@dataclass
class ChunkResult:
    text: str
    page_number: int
    section: str
    heading: str
    chunk_index: int


def _split_paragraphs(text: str) -> list[str]:
    paras = re.split(r"\n\s*\n|\n(?=[A-Z0-9])", text)
    return [p.strip() for p in paras if p.strip()]


def chunk_pages(
    pages: list[PageContent],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[ChunkResult]:
    chunks: list[ChunkResult] = []
    global_index = 0

    for page in pages:
        if not page.text.strip():
            continue

        paragraphs = _split_paragraphs(page.text)
        current = ""

        def flush(buf: str):
            nonlocal global_index
            if buf.strip():
                chunks.append(
                    ChunkResult(
                        text=buf.strip(),
                        page_number=page.page_number,
                        section=page.section,
                        heading=page.heading,
                        chunk_index=global_index,
                    )
                )
                global_index += 1

        for para in paragraphs:
            # Hard-split paragraphs that alone exceed chunk_size
            if len(para) > chunk_size:
                if current:
                    flush(current)
                    current = ""
                for i in range(0, len(para), chunk_size - chunk_overlap):
                    flush(para[i : i + chunk_size])
                continue

            if len(current) + len(para) + 1 <= chunk_size:
                current = f"{current}\n{para}".strip()
            else:
                flush(current)
                # carry overlap from the tail of the previous chunk
                overlap_text = current[-chunk_overlap:] if chunk_overlap else ""
                current = f"{overlap_text}\n{para}".strip()

        flush(current)

    return chunks
