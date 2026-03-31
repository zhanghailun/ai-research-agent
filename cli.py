"""
cli.py — Command-line interface for the AI Research Agent.

Usage examples
--------------
    # Basic search + full pipeline
    python cli.py run "supply chain" "sustainability" "circular economy"

    # With research context and custom limits
    python cli.py run "digital transformation" "SMEs" \
        --context "Focus on SMEs in developing economies" \
        --max-results 15

    # Search only (no LLM calls)
    python cli.py search "operations management" "optimization" --limit 10

    # Show existing report
    python cli.py report output/report_*.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

import config

config.setup_logging()


# ---------------------------------------------------------------------------
# Main CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option("1.0.0", prog_name="research-agent")
def cli() -> None:
    """AI Research Agent — automated literature review and idea generation."""


# ---------------------------------------------------------------------------
# run command
# ---------------------------------------------------------------------------

@cli.command("run")
@click.argument("keywords", nargs=-1, required=True)
@click.option(
    "--context",
    "-c",
    default="",
    help="Free-text research context / focus area for idea generation.",
)
@click.option(
    "--max-results",
    "-n",
    default=config.DEFAULT_MAX_RESULTS,
    show_default=True,
    help="Maximum papers to retrieve per source.",
)
@click.option(
    "--sources",
    "-s",
    multiple=True,
    default=["openalex_informs", "semantic_scholar"],
    show_default=True,
    help="Sources to search (openalex_informs, semantic_scholar, arxiv, ssrn). Repeatable.",
)
@click.option(
    "--skip-download",
    is_flag=True,
    default=False,
    help="Skip PDF download (summarize from abstract only).",
)
@click.option(
    "--output-dir",
    "-o",
    default=None,
    help="Directory to save the JSON report (default from config).",
)
@click.option(
    "--no-save",
    is_flag=True,
    default=False,
    help="Do not save report to disk.",
)
def run_command(
    keywords: tuple[str, ...],
    context: str,
    max_results: int,
    sources: tuple[str, ...],
    skip_download: bool,
    output_dir: str | None,
    no_save: bool,
) -> None:
    """Run the full research pipeline for the given KEYWORDS."""
    from agent import ResearchAgent

    click.echo(f"🔍 Starting research pipeline for: {list(keywords)}")

    agent = ResearchAgent(output_dir=output_dir or config.OUTPUT_DIR)
    report = agent.run(
        keywords=list(keywords),
        research_context=context,
        max_results=max_results,
        sources=list(sources) if sources else None,
        skip_download=skip_download,
        save_report=not no_save,
    )

    click.echo(f"\n📊 Papers found      : {report['papers_found']}")
    click.echo(f"📄 PDFs downloaded   : {report['papers_with_pdf']}")
    click.echo(f"📝 Papers summarized : {report['papers_summarized']}")

    click.echo("\n" + "=" * 60)
    click.echo("LITERATURE ANALYSIS")
    click.echo("=" * 60)
    click.echo(report["literature_analysis"])

    click.echo("\n" + "=" * 60)
    click.echo("NOVEL RESEARCH IDEAS")
    click.echo("=" * 60)
    click.echo(report["novel_ideas"])


# ---------------------------------------------------------------------------
# search command
# ---------------------------------------------------------------------------

@cli.command("search")
@click.argument("keywords", nargs=-1, required=True)
@click.option(
    "--limit",
    "-n",
    default=config.DEFAULT_MAX_RESULTS,
    show_default=True,
    help="Maximum results per source.",
)
@click.option(
    "--sources",
    "-s",
    multiple=True,
    default=["openalex_informs", "semantic_scholar"],
    show_default=True,
    help="Sources to search (openalex_informs, semantic_scholar, arxiv, ssrn). Repeatable.",
)
@click.option(
    "--json-output",
    is_flag=True,
    default=False,
    help="Print results as JSON.",
)
def search_command(
    keywords: tuple[str, ...],
    limit: int,
    sources: tuple[str, ...],
    json_output: bool,
) -> None:
    """Search for papers matching KEYWORDS without running the full pipeline."""
    from search import search_all

    click.echo(f"🔍 Searching for: {list(keywords)}", err=True)
    papers = search_all(list(keywords), limit=limit, sources=list(sources))

    if json_output:
        click.echo(json.dumps(papers, indent=2, ensure_ascii=False))
    else:
        click.echo(f"\nFound {len(papers)} papers:\n")
        for i, p in enumerate(papers, start=1):
            authors = ", ".join(p.get("authors", [])[:3])
            if len(p.get("authors", [])) > 3:
                authors += " et al."
            pdf_marker = "📄" if p.get("open_access_pdf") else "  "
            click.echo(
                f"{i:3}. {pdf_marker} [{p.get('year', '?')}] {p.get('title', 'N/A')}"
            )
            if authors:
                click.echo(f"       {authors}")
            if p.get("abstract"):
                snippet = p["abstract"][:120].replace("\n", " ")
                click.echo(f"       {snippet}…")
            click.echo()


# ---------------------------------------------------------------------------
# summarize command (single PDF)
# ---------------------------------------------------------------------------

@cli.command("summarize")
@click.argument("pdf_path", type=click.Path(exists=True, path_type=Path))
@click.option("--title", "-t", default="", help="Paper title (optional).")
def summarize_command(pdf_path: Path, title: str) -> None:
    """Extract and summarize text from a single PDF file."""
    from extract import extract_text
    from summarize import summarize_paper

    click.echo(f"📖 Extracting text from {pdf_path.name}…")
    try:
        text, meta = extract_text(pdf_path)
    except Exception as exc:
        click.echo(f"❌ Extraction failed: {exc}", err=True)
        sys.exit(1)

    paper_title = title or meta.get("title") or pdf_path.stem
    click.echo(f"🤖 Summarizing '{paper_title}'…")
    summary = summarize_paper(text=text, title=paper_title)
    click.echo("\n" + "=" * 60)
    click.echo(summary)


# ---------------------------------------------------------------------------
# report command (view saved report)
# ---------------------------------------------------------------------------

@cli.command("report")
@click.argument("report_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--section",
    "-s",
    type=click.Choice(["analysis", "ideas", "papers", "all"], case_sensitive=False),
    default="all",
    help="Which section(s) to display.",
)
def report_command(report_path: Path, section: str) -> None:
    """Display a previously saved research report."""
    with open(report_path, encoding="utf-8") as fh:
        report = json.load(fh)

    click.echo(f"📋 Report: {report_path.name}")
    click.echo(f"   Keywords  : {report.get('keywords')}")
    click.echo(f"   Timestamp : {report.get('timestamp')}")
    click.echo(
        f"   Papers    : {report.get('papers_found')} found | "
        f"{report.get('papers_with_pdf')} PDFs | "
        f"{report.get('papers_summarized')} summarized"
    )

    if section in ("analysis", "all"):
        click.echo("\n" + "=" * 60)
        click.echo("LITERATURE ANALYSIS")
        click.echo("=" * 60)
        click.echo(report.get("literature_analysis", "(none)"))

    if section in ("ideas", "all"):
        click.echo("\n" + "=" * 60)
        click.echo("NOVEL RESEARCH IDEAS")
        click.echo("=" * 60)
        click.echo(report.get("novel_ideas", "(none)"))

    if section in ("papers", "all"):
        click.echo("\n" + "=" * 60)
        click.echo("PAPERS")
        click.echo("=" * 60)
        for i, p in enumerate(report.get("papers", []), start=1):
            click.echo(f"\n{i}. {p.get('title')}")
            click.echo(f"   Authors: {', '.join(p.get('authors', []))}")
            click.echo(f"   Year: {p.get('year')} | Source: {p.get('source')}")
            if p.get("summary"):
                click.echo(f"   Summary:\n{p['summary'][:400]}…")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
