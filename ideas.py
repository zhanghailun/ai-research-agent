"""
ideas.py — Novel research idea generation for management science papers.

Public API
----------
generate_ideas(literature_analysis, keywords, research_context) -> str
"""

from __future__ import annotations

import logging

import fastapi_poe as fp

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# POE API helper
# ---------------------------------------------------------------------------

def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Synchronous call to POE API via get_bot_response_sync."""
    if not config.POE_API_KEY:
        raise RuntimeError(
            "POE_API_KEY is not set. Add it to your .env file or environment."
        )
    combined = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
    messages = [fp.ProtocolMessage(role="user", content=combined)]
    text = ""
    try:
        for partial in fp.get_bot_response_sync(
            messages=messages,
            bot_name=config.POE_BOT_NAME,
            api_key=config.POE_API_KEY,
        ):
            if hasattr(partial, "text"):
                text += partial.text
    except fp.BotError as exc:
        exc_str = str(exc)
        if "403" in exc_str or "Forbidden" in exc_str or "SSEError" in exc_str:
            raise RuntimeError(
                f"Poe API returned 403 Forbidden for bot '{config.POE_BOT_NAME}'. "
                "The bot may not exist or your API key may not have access to it. "
                "Try a different bot (e.g. Claude-3-5-Sonnet) in the sidebar, "
                "or check your Poe subscription at https://poe.com/api_key."
            ) from exc
        raise
    return text


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_IDEAS_SYSTEM = """\
You are a creative and rigorous management science researcher with deep expertise in \
generating novel, publishable research ideas. You think across disciplinary boundaries, \
connecting emerging trends with fundamental management questions, and you are skilled \
at designing feasible research studies."""

_IDEAS_USER_TMPL = """\
Based on the following literature analysis, generate 5 novel and compelling research \
ideas suitable for publication in top management science or operations management journals \
(e.g., Management Science, Operations Research, Journal of Operations Management).

Literature Analysis:
{analysis}

Original Research Topic / Keywords: {topic}
Additional Research Context: {context}

For each idea, provide:

**Idea [N]: [Compelling Short Title]**

- **Research Question**: The core question this study will answer.
- **Novelty & Gap**: Why this has not been adequately explored; how it fills a gap in the literature.
- **Theoretical Grounding**: The theory or framework underpinning the study.
- **Proposed Methodology**: Data sources, research design, and analytical approach.
- **Expected Contributions**: What new knowledge or practical value this generates.
- **Potential Journals**: Which top journals would be suitable outlets.
- **Feasibility Assessment**: Data availability, timeline, and key challenges.

Ensure the ideas:
1. Build directly on gaps identified in the literature analysis.
2. Combine emerging trends with classic management questions.
3. Have clear practical relevance to organizations or policy.
4. Are methodologically feasible with available data.
5. Span a variety of methodological approaches (e.g., empirical, theoretical, experimental).
"""


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def generate_ideas(
    literature_analysis: str,
    keywords: list[str] | None = None,
    research_context: str = "",
) -> str:
    """
    Generate novel management science research ideas from a literature analysis.

    Parameters
    ----------
    literature_analysis : the output of analyze.analyze_literature()
    keywords            : original search keywords
    research_context    : optional free-text context describing the user's focus area

    Returns a formatted string of research ideas.
    """
    if not literature_analysis or literature_analysis.startswith("["):
        return "[Cannot generate ideas: no valid literature analysis provided]"

    topic = " | ".join(keywords) if keywords else "management science"
    context = research_context or "General management science research focus"

    user_message = _IDEAS_USER_TMPL.format(
        analysis=literature_analysis[:6000],
        topic=topic,
        context=context,
    )

    try:
        ideas = _call_llm(_IDEAS_SYSTEM, user_message)
        logger.info("Generated research ideas (%d chars)", len(ideas))
        return ideas.strip()
    except Exception as exc:
        logger.error("Idea generation failed: %s", exc)
        return f"[Idea generation failed: {exc}]"
