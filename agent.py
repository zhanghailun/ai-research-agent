"""
agent.py — Main ResearchAgent orchestration pipeline.

Usage
-----
    from agent import ResearchAgent

    agent = ResearchAgent()
    report = agent.run(
        keywords=["supply chain", "sustainability", "circular economy"],
        research_context="Focus on circular economy practices in manufacturing",
        max_results=15,
    )
    print(report["novel_ideas"])
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config
from analyze import analyze_literature
from download import download_papers
from extract import extract_papers
from ideas import generate_ideas
from search import search_all
from summarize import summarize_papers

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    End-to-end AI research agent for management science literature review
    and novel idea generation.

    Pipeline
    --------
    search → download → extract → summarize → analyze → generate ideas → save report
    """

    def __init__(
        self,
        papers_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
    ) -> None:
        self.papers_dir = Path(papers_dir) if papers_dir else config.PAPERS_DIR
        self.output_dir = Path(output_dir) if output_dir else config.OUTPUT_DIR
        config.ensure_dirs()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(
        self,
        keywords: list[str],
        research_context: str = "",
        max_results: int | None = None,
        sources: list[str] | None = None,
        skip_download: bool = False,
        save_report: bool = True,
    ) -> dict[str, Any]:
        """
        Execute the full research pipeline.

        Parameters
        ----------
        keywords         : search terms (e.g. ["supply chain", "optimization"])
        research_context : free-text focus area for idea generation
        max_results      : papers to retrieve per source (default from config)
        sources          : ["semantic_scholar", "arxiv"] or a subset
        skip_download    : if True, skip PDF downloading (use abstract only)
        save_report      : persist the JSON report to output_dir

        Returns
        -------
        A dict with keys: keywords, papers_found, papers_with_pdf,
        papers_summarized, literature_analysis, novel_ideas, papers, timestamp
        """
        limit = max_results or config.DEFAULT_MAX_RESULTS
        logger.info("=== Research Agent starting ===")
        logger.info("Keywords: %s | Max results: %d", keywords, limit)

        # ── 1. Search ──────────────────────────────────────────────────
        logger.info("[1/6] Searching for papers…")
        papers = search_all(keywords, limit=limit, sources=sources)
        if not papers:
            logger.warning("No papers found for keywords: %s", keywords)

        # ── 2. Download PDFs ───────────────────────────────────────────
        if skip_download:
            logger.info("[2/6] Skipping PDF download (skip_download=True)")
            for paper in papers:
                paper.setdefault("local_pdf", "")
        else:
            logger.info("[2/6] Downloading PDFs…")
            papers = download_papers(papers, papers_dir=self.papers_dir)

        papers_with_pdf = sum(1 for p in papers if p.get("local_pdf"))

        # ── 3. Extract text ────────────────────────────────────────────
        logger.info("[3/6] Extracting text from PDFs…")
        papers = extract_papers(papers)

        # ── 4. Summarize ───────────────────────────────────────────────
        logger.info("[4/6] Summarizing papers…")
        papers = summarize_papers(papers)
        papers_summarized = sum(
            1 for p in papers
            if p.get("summary") and not p["summary"].startswith("[")
        )

        # ── 5. Analyze literature ──────────────────────────────────────
        logger.info("[5/6] Analyzing literature landscape…")
        literature_analysis = analyze_literature(papers, keywords=keywords)

        # ── 6. Generate ideas ──────────────────────────────────────────
        logger.info("[6/6] Generating novel research ideas…")
        novel_ideas = generate_ideas(
            literature_analysis,
            keywords=keywords,
            research_context=research_context,
        )

        # ── Compile report ─────────────────────────────────────────────
        report: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "keywords": keywords,
            "research_context": research_context,
            "papers_found": len(papers),
            "papers_with_pdf": papers_with_pdf,
            "papers_summarized": papers_summarized,
            "literature_analysis": literature_analysis,
            "novel_ideas": novel_ideas,
            "papers": self._strip_large_fields(papers),
        }

        if save_report:
            self._save_report(report, keywords)

        logger.info("=== Research Agent complete ===")
        logger.info(
            "Found %d papers | PDFs: %d | Summarized: %d",
            len(papers),
            papers_with_pdf,
            papers_summarized,
        )
        return report

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_large_fields(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove bulky extracted_text from the report to keep JSON size manageable."""
        clean = []
        for p in papers:
            stripped = {k: v for k, v in p.items() if k != "extracted_text"}
            clean.append(stripped)
        return clean

    def _save_report(self, report: dict[str, Any], keywords: list[str]) -> Path:
        """Persist the report as a JSON file and return its path."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        slug = "_".join(keywords[:3]).replace(" ", "-").lower()[:40]
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"report_{slug}_{ts}.json"
        with open(filename, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
        logger.info("Report saved → %s", filename)
        return filename


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def run_research(
    keywords: list[str],
    research_context: str = "",
    max_results: int = 20,
    skip_download: bool = False,
) -> dict[str, Any]:
    """Shortcut: create a ResearchAgent and run the full pipeline."""
    config.setup_logging()
    agent = ResearchAgent()
    return agent.run(
        keywords=keywords,
        research_context=research_context,
        max_results=max_results,
        skip_download=skip_download,
    )


if __name__ == "__main__":
    import sys

    kw = sys.argv[1:] or ["supply chain", "sustainability"]
    result = run_research(kw)
    print("\n=== LITERATURE ANALYSIS ===\n")
    print(result["literature_analysis"])
    print("\n=== NOVEL IDEAS ===\n")
    print(result["novel_ideas"])
