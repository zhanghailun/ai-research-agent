"""
analyze.py — Literature landscape analysis and research-gap detection.

Public API
----------
analyze_literature(summaries, keywords) -> str
"""

from __future__ import annotations

import logging
from typing import Any

from openai import OpenAI

import config

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
# Prompts
# ---------------------------------------------------------------------------

_ANALYSIS_SYSTEM = """\
You are a senior academic researcher specializing in management science, operations \
management, and organizational behavior. You excel at synthesizing large bodies of \
literature and identifying patterns, trends, and underexplored research avenues."""

_ANALYSIS_USER_TMPL = """\
You have been provided with summaries of {n} research papers related to the topic: "{topic}".

Paper Summaries:
{summaries_block}

Please produce a comprehensive literature landscape analysis covering:

1. **Common Themes**: What recurring theoretical or empirical themes appear across the papers?
2. **Dominant Methodologies**: Which research methods (quantitative, qualitative, experimental, etc.) are most prevalent?
3. **Key Findings & Consensus**: Where do the papers converge in their findings?
4. **Contradictions & Debates**: Are there conflicting results or unresolved debates in the literature?
5. **Research Gaps**: What important questions are *not* adequately addressed by existing work?
6. **Emerging Trends**: What newer directions or topics are beginning to appear?
7. **Practical Implications**: What do these papers collectively say for practitioners and organizations?
8. **Recommended Future Directions**: Based on the gaps and trends, where should future research focus?
"""


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def analyze_literature(
    papers: list[dict[str, Any]],
    keywords: list[str] | None = None,
) -> str:
    """
    Synthesize the summaries of multiple papers into a landscape analysis.

    Parameters
    ----------
    papers   : list of paper dicts, each with at least a ``summary`` key
    keywords : the original search keywords (used for topic labeling)

    Returns the analysis text.
    """
    summaries = [p.get("summary", "") for p in papers if p.get("summary")]
    if not summaries:
        return "[No summaries available for analysis]"

    topic = " | ".join(keywords) if keywords else "management science research"

    # Build a numbered block of summaries, truncated to keep within context limits
    blocks: list[str] = []
    budget = 10000  # approximate character budget for summaries
    per_summary = max(200, budget // len(summaries))
    for i, summary in enumerate(summaries, start=1):
        blocks.append(f"[Paper {i}]\n{summary[:per_summary]}")
    summaries_block = "\n\n".join(blocks)

    user_message = _ANALYSIS_USER_TMPL.format(
        n=len(summaries),
        topic=topic,
        summaries_block=summaries_block,
    )

    try:
        response = _get_client().chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _ANALYSIS_SYSTEM},
                {"role": "user", "content": user_message},
            ],
            max_tokens=config.ANALYSIS_MAX_TOKENS,
            temperature=0.4,
        )
        analysis = response.choices[0].message.content or ""
        logger.info(
            "Literature analysis complete (%d papers → %d chars)", len(summaries), len(analysis)
        )
        return analysis.strip()
    except Exception as exc:
        logger.error("Literature analysis failed: %s", exc)
        return f"[Literature analysis failed: {exc}]"
