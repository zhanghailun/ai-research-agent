"""
extract.py — PDF text extraction using PyMuPDF (fitz).

Public API
----------
extract_text(pdf_path)         -> tuple[str, dict]
extract_papers(papers)         -> list[dict]
truncate_text(text, max_chars) -> str
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Single-file extraction
# ---------------------------------------------------------------------------

def extract_text(pdf_path: Path | str) -> tuple[str, dict[str, Any]]:
    """
    Extract all text from *pdf_path* using PyMuPDF.

    Returns
    -------
    (full_text, metadata)
        full_text : concatenated page text
        metadata  : dict with title, author, subject, page_count
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        raise RuntimeError(f"Cannot open PDF '{pdf_path}': {exc}") from exc

    metadata: dict[str, Any] = {
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "subject": doc.metadata.get("subject", ""),
        "page_count": doc.page_count,
    }

    pages: list[str] = []
    for page_num, page in enumerate(doc, start=1):
        try:
            text = page.get_text("text")
            if text.strip():
                pages.append(f"--- Page {page_num} ---\n{text}")
        except Exception as exc:
            logger.warning("Failed to extract page %d from %s: %s", page_num, pdf_path, exc)

    doc.close()
    full_text = "\n".join(pages)
    logger.debug(
        "Extracted %d characters from %s (%d pages)", len(full_text), pdf_path.name, len(pages)
    )
    return full_text, metadata


# ---------------------------------------------------------------------------
# Batch extraction
# ---------------------------------------------------------------------------

def extract_papers(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Extract text from PDFs referenced by the ``local_pdf`` key in each paper dict.

    Adds ``extracted_text`` and ``pdf_metadata`` keys to each paper in-place.
    Papers without a valid ``local_pdf`` are skipped.

    Returns the updated papers list.
    """
    extracted = 0
    for paper in papers:
        local_pdf = paper.get("local_pdf", "")
        if not local_pdf:
            paper.setdefault("extracted_text", "")
            paper.setdefault("pdf_metadata", {})
            continue

        try:
            text, meta = extract_text(local_pdf)
            paper["extracted_text"] = text
            paper["pdf_metadata"] = meta
            extracted += 1
            logger.debug("Extracted text from: %s", local_pdf)
        except Exception as exc:
            logger.warning("Text extraction failed for %s: %s", local_pdf, exc)
            paper["extracted_text"] = ""
            paper["pdf_metadata"] = {}

    logger.info("Extracted text from %d / %d papers", extracted, len(papers))
    return papers


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def truncate_text(text: str, max_chars: int | None = None) -> str:
    """
    Truncate *text* to *max_chars* characters, appending an ellipsis if cut.

    Defaults to the configured ``PDF_TEXT_LIMIT`` if *max_chars* is None.
    """
    limit = max_chars if max_chars is not None else config.PDF_TEXT_LIMIT
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[… text truncated …]"
