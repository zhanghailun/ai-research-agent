"""
summarize.py — LLM-powered paper summarization via OpenAI GPT-4.

Public API
----------
summarize_paper(text, title, abstract) -> str
summarize_papers(papers)               -> list[dict]
"""

from __future__ import annotations

import logging
from typing import Any

from openai import OpenAI

import config
from extract import truncate_text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OpenAI client (lazy init)
# ---------------------------------------------------------------------------

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to your .env file or environment."
            )
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


# ---------------------------------------------------------------------------
# Single-paper summarization
# ---------------------------------------------------------------------------

_SUMMARIZE_SYSTEM = """\
You are an expert academic research assistant specializing in management science, \
operations research, and related fields. You produce clear, structured paper summaries."""

_SUMMARIZE_USER_TMPL = """\
Please summarize the following research paper in a structured format.

Paper title: {title}

Abstract (if available):
{abstract}

Full text (may be truncated):
{text}

Provide the summary in these sections:
1. **Main Problem**: What core problem or question does the paper address?
2. **Key Methodology**: What approach, method, or theory is used?
3. **Main Findings**: What are the principal results or conclusions?
4. **Contributions**: What is novel or distinctive about this work?
5. **Limitations**: What acknowledged limitations or gaps remain?
6. **Relevance to Management Science**: How does this connect to management or organizational practice?
"""


def summarize_paper(
    text: str,
    title: str = "",
    abstract: str = "",
) -> str:
    """
    Summarize a single paper using the configured LLM.

    Parameters
    ----------
    text     : extracted full text (will be truncated to PDF_TEXT_LIMIT)
    title    : paper title
    abstract : paper abstract (optional; used as additional context)

    Returns the summary string.
    """
    truncated = truncate_text(text or abstract or "(No text available)")
    user_message = _SUMMARIZE_USER_TMPL.format(
        title=title or "(Unknown title)",
        abstract=abstract or "(Not available)",
        text=truncated,
    )

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SUMMARIZE_SYSTEM},
                {"role": "user", "content": user_message},
            ],
            max_tokens=config.SUMMARIZE_MAX_TOKENS,
            temperature=0.3,
        )
        summary = response.choices[0].message.content or ""
        logger.debug("Summarized paper: %s (%d chars)", title[:60], len(summary))
        return summary.strip()
    except Exception as exc:
        logger.error("Summarization failed for '%s': %s", title[:60], exc)
        return f"[Summarization failed: {exc}]"


# ---------------------------------------------------------------------------
# Batch summarization
# ---------------------------------------------------------------------------

def summarize_papers(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Summarize all papers in the list that have extractable text.

    Adds a ``summary`` key to each paper dict in-place.
    Falls back to summarizing from the abstract alone when full text is absent.

    Returns the updated papers list.
    """
    summarized = 0
    for i, paper in enumerate(papers):
        title = paper.get("title", f"Paper {i+1}")
        abstract = paper.get("abstract", "")
        text = paper.get("extracted_text", "")

        if not text and not abstract:
            logger.debug("Skipping '%s' — no text or abstract available", title[:60])
            paper["summary"] = "[No content available for summarization]"
            continue

        logger.info("Summarizing paper %d/%d: %s", i + 1, len(papers), title[:60])
        paper["summary"] = summarize_paper(text=text, title=title, abstract=abstract)
        if not paper["summary"].startswith("[Summarization failed"):
            summarized += 1

    logger.info("Summarized %d / %d papers", summarized, len(papers))
    return papers
