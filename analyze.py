"""
analyze.py — Literature landscape analysis and research-gap detection.

Public API
----------
analyze_literature(summaries, keywords) -> str
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import fastapi_poe as fp

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# POE API helper
# ---------------------------------------------------------------------------

async def _async_call_llm(system_prompt: str, user_prompt: str) -> str:
    """Async call to POE API; combines system and user prompts."""
    combined = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
    messages = [fp.ProtocolMessage(role="user", content=combined)]
    text = ""
    async for partial in fp.get_bot_response(
        messages=messages,
        bot_name=config.POE_BOT_NAME,
        api_key=config.POE_API_KEY,
    ):
        if hasattr(partial, "text"):
            text += partial.text
    return text


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Synchronous wrapper around the async POE API call."""
    if not config.POE_API_KEY:
        raise RuntimeError(
            "POE_API_KEY is not set. Add it to your .env file or environment."
        )
    return asyncio.run(_async_call_llm(system_prompt, user_prompt))


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
        analysis = _call_llm(_ANALYSIS_SYSTEM, user_message)
        logger.info(
            "Literature analysis complete (%d papers → %d chars)", len(summaries), len(analysis)
        )
        return analysis.strip()
    except Exception as exc:
        logger.error("Literature analysis failed: %s", exc)
        return f"[Literature analysis failed: {exc}]"
