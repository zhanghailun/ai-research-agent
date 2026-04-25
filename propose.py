"""
propose.py — INFORMS top-journal style paper proposal generator.

Public API
----------
generate_proposal(idea, research_context, literature_analysis) -> str

The proposal is written in the style described in
``management_science_writing_skill.md``, which is loaded from the project root
and injected as the system prompt so the LLM internalises the INFORMS house
style before it writes a single word of the proposal.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import fastapi_poe as fp

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Writing-skill guide
# ---------------------------------------------------------------------------

_SKILL_PATH = Path(__file__).parent / "management_science_writing_skill.md"


def _load_writing_guide() -> str:
    """Return the contents of the writing-skill Markdown file, or '' on error."""
    try:
        return _SKILL_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("Writing guide not found at %s; proceeding without it.", _SKILL_PATH)
        return ""


# ---------------------------------------------------------------------------
# POE API helper (same pattern as ideas.py / analyze.py)
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

_PROPOSAL_SYSTEM_TMPL = """\
You are a senior management science researcher with deep expertise in writing \
papers for INFORMS top journals: Management Science, Operations Research, and \
Manufacturing & Service Operations Management (MSOM).

You must follow the writing principles and style rules described in the guide \
below. These rules were distilled from successful revisions of papers in \
Management Science and capture exactly what the editors and referees of INFORMS \
top journals expect.

=== INFORMS WRITING GUIDE ===
{writing_guide}
=== END OF GUIDE ===

Apply these principles throughout the proposal you are about to write. \
In particular:
- Lead with the managerial question, not the technique.
- Structure the introduction using the Six-Paragraph Narrative Architecture \
  (Context → Trade-off → Difficulty → Research Question → Our Answer → Contributions → Roadmap).
- Make the central trade-off concrete and explicit.
- After every claimed result, answer: what does it say? why does it happen? \
  why should a manager care?
- Maintain formal precision; do not overclaim.
"""

_PROPOSAL_USER_TMPL = """\
Write a detailed paper proposal in the style of an INFORMS top-journal \
submission (Management Science / Operations Research / MSOM).

Research Idea:
{idea}

Research Context / Focus Area:
{context}

Literature Background (from automated review):
{literature}

Your proposal must include the following sections, each clearly headed:

## 1. Title
A precise, descriptive title in the style of a Management Science paper \
(no exclamation marks; action-oriented noun phrase or question).

## 2. Abstract (≈150 words)
A structured abstract covering: motivation, research question, methodology, \
key results, and managerial implications.

## 3. Introduction (≈500 words)
Follow the Six-Paragraph Narrative Architecture from the writing guide:
- P1 Context: real-world setting and the decision objects.
- P2 Trade-off: a concrete domain-grounded example showing both extremes.
- P3 Difficulty: why the problem is hard and why a structural insight is needed.
- P4 Research Question: closest prior work, its limitations, and the \
  research question as a single interrogative sentence.
- P5 Our Answer (managerial): the structural condition, practical recipe, \
  and retailer/manager upshot — without technical details.
- Contributions block: 3–5 formal contributions, each with a bold title \
  and 2–4 sentences.
- P6 Roadmap: one sentence per section.

## 4. Research Gap and Novelty
Why has this question not been adequately addressed? What gap in the \
literature does this paper fill? How does it differ from the three closest \
prior studies?

## 5. Theoretical Framework and Model
Which theory or analytical framework underpins the study? Describe the \
model primitives, decision variables, and key assumptions. Explain why \
each assumption is reasonable in practice (writing rule 10).

## 6. Proposed Methodology
Data sources, research design, and analytical approach. If empirical: \
identification strategy and robustness checks. If theoretical/analytical: \
solution approach and proof strategy. Mention feasibility.

## 7. Expected Contributions
What new knowledge does this paper generate? Include: theoretical contribution, \
empirical/methodological contribution, and managerial/policy contribution.

## 8. Target Journals and Positioning
Which INFORMS journals are the primary target, and why? How does this paper \
fit their recent editorial direction?

## 9. Feasibility Assessment
Data availability, timeline (phases and milestones), and key challenges \
with mitigation strategies.
"""


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def generate_proposal(
    idea: str,
    research_context: str = "",
    literature_analysis: str = "",
) -> str:
    """
    Generate an INFORMS top-journal style paper proposal from a research idea.

    Parameters
    ----------
    idea               : the research idea text (free-form or from generate_ideas())
    research_context   : optional focus area / additional constraints
    literature_analysis: optional background from analyze_literature()

    Returns a formatted Markdown proposal string.
    """
    if not idea or not idea.strip():
        return "[Cannot generate proposal: no research idea provided]"

    writing_guide = _load_writing_guide()

    system_prompt = _PROPOSAL_SYSTEM_TMPL.format(writing_guide=writing_guide)

    # Truncate the literature analysis to keep the prompt within reason
    lit_excerpt = (literature_analysis or "Not provided")[:4000]
    context = research_context or "General management science / operations research focus"

    user_message = _PROPOSAL_USER_TMPL.format(
        idea=idea.strip()[:3000],
        context=context,
        literature=lit_excerpt,
    )

    try:
        proposal = _call_llm(system_prompt, user_message)
        logger.info("Generated paper proposal (%d chars)", len(proposal))
        return proposal.strip()
    except Exception as exc:
        logger.error("Proposal generation failed: %s", exc)
        return f"[Proposal generation failed: {exc}]"
