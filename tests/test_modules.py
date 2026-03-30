"""
tests/test_modules.py — Unit tests for AI Research Agent modules.

Tests use mocks to avoid external API calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

class TestConfig:
    def test_defaults_exist(self):
        import config
        assert isinstance(config.DEFAULT_MAX_RESULTS, int)
        assert config.DEFAULT_MAX_RESULTS > 0
        assert isinstance(config.DOWNLOAD_RETRIES, int)
        assert isinstance(config.PAPERS_DIR, Path)

    def test_setup_logging(self):
        import logging
        import config
        logger = config.setup_logging()
        assert isinstance(logger, logging.Logger)

    def test_ensure_dirs(self, tmp_path):
        import config
        orig_papers = config.PAPERS_DIR
        orig_output = config.OUTPUT_DIR
        config.PAPERS_DIR = tmp_path / "papers"
        config.OUTPUT_DIR = tmp_path / "output"
        config.ensure_dirs()
        assert config.PAPERS_DIR.exists()
        assert config.OUTPUT_DIR.exists()
        config.PAPERS_DIR = orig_papers
        config.OUTPUT_DIR = orig_output


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_search_semantic_scholar_success(self):
        """Mock a successful Semantic Scholar response."""
        from search import search_semantic_scholar

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "data": [
                {
                    "title": "Test Paper",
                    "abstract": "An abstract.",
                    "year": 2023,
                    "authors": [{"name": "Alice"}, {"name": "Bob"}],
                    "externalIds": {"DOI": "10.1234/test"},
                    "isOpenAccess": True,
                    "openAccessPdf": {"url": "https://example.com/paper.pdf"},
                    "url": "https://semanticscholar.org/paper/test",
                }
            ]
        }

        with patch("search.requests.get", return_value=mock_response):
            results = search_semantic_scholar(["supply chain"], limit=5)

        assert len(results) == 1
        assert results[0]["title"] == "Test Paper"
        assert results[0]["doi"] == "10.1234/test"
        assert results[0]["source"] == "SemanticScholar"
        assert results[0]["open_access_pdf"] == "https://example.com/paper.pdf"

    def test_search_semantic_scholar_failure(self):
        """Mock a failed HTTP request."""
        import requests
        from search import search_semantic_scholar

        with patch("search.requests.get", side_effect=requests.RequestException("timeout")):
            results = search_semantic_scholar(["test"], limit=5)
        assert results == []

    def test_search_arxiv_success(self):
        """Mock a successful arXiv feedparser response."""
        from search import search_arxiv

        mock_entry = MagicMock()
        mock_entry.title = "ArXiv Test Paper"
        mock_entry.summary = "A great paper."
        mock_entry.published = "2023-01-15T00:00:00Z"
        mock_entry.authors = [MagicMock(name="Charlie")]
        mock_entry.id = "https://arxiv.org/abs/2301.00001"
        mock_entry.links = [
            {"type": "application/pdf", "href": "https://arxiv.org/pdf/2301.00001.pdf"}
        ]

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]

        with patch("search.feedparser.parse", return_value=mock_feed):
            results = search_arxiv(["supply chain"], limit=5)

        assert len(results) == 1
        assert results[0]["title"] == "ArXiv Test Paper"
        assert results[0]["year"] == 2023
        assert results[0]["source"] == "arXiv"

    def test_search_all_deduplication(self):
        """Ensure combined search deduplicates by title."""
        from search import search_all

        paper_a = {
            "title": "Duplicate Paper",
            "abstract": "A",
            "year": 2023,
            "authors": [],
            "doi": "",
            "url": "",
            "open_access_pdf": "",
            "source": "SemanticScholar",
        }
        paper_b = {**paper_a, "source": "arXiv"}

        with patch("search.search_semantic_scholar", return_value=[paper_a]), \
             patch("search.search_arxiv", return_value=[paper_b]):
            results = search_all(["test"], limit=5, deduplicate=True)

        # Should have only 1 after deduplication
        assert len(results) == 1


# ---------------------------------------------------------------------------
# download
# ---------------------------------------------------------------------------

class TestDownload:
    def test_download_pdf_success(self, tmp_path):
        from download import download_pdf

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_response.iter_content.return_value = [b"%" * 2048, b"PDF" * 500]

        dest = tmp_path / "test.pdf"
        with patch("download.requests.get", return_value=mock_response):
            result = download_pdf("https://example.com/paper.pdf", dest)

        assert result is True
        assert dest.exists()

    def test_download_pdf_http_error(self, tmp_path):
        import requests as req
        from download import download_pdf

        mock_response = MagicMock()
        mock_response.status_code = 404
        http_err = req.HTTPError(response=mock_response)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = http_err

        dest = tmp_path / "test.pdf"
        with patch("download.requests.get", return_value=mock_resp):
            result = download_pdf("https://example.com/missing.pdf", dest)

        assert result is False

    def test_sanitize_filename(self):
        from download import _sanitize_filename
        name = _sanitize_filename('My Paper: "Title" / With <Special> Chars?')
        assert "/" not in name
        assert ":" not in name
        assert '"' not in name

    def test_find_open_access_pdf_success(self):
        from download import find_open_access_pdf

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "is_oa": True,
            "best_oa_location": {"url_for_pdf": "https://example.com/oa.pdf"},
        }

        with patch("download.requests.get", return_value=mock_resp):
            url = find_open_access_pdf("10.1234/test")

        assert url == "https://example.com/oa.pdf"

    def test_find_open_access_pdf_no_doi(self):
        from download import find_open_access_pdf
        assert find_open_access_pdf("") is None
        assert find_open_access_pdf(None) is None


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

class TestExtract:
    def test_extract_text_file_not_found(self):
        from extract import extract_text
        with pytest.raises(FileNotFoundError):
            extract_text("/nonexistent/path/paper.pdf")

    def test_extract_text_valid_pdf(self, tmp_path):
        """Create a minimal PDF with fitz and extract text from it."""
        import fitz
        from extract import extract_text

        # Create a minimal PDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 100), "Hello, research world!")
        pdf_path = tmp_path / "test.pdf"
        doc.save(str(pdf_path))
        doc.close()

        text, meta = extract_text(pdf_path)
        assert "Hello, research world!" in text
        assert isinstance(meta, dict)
        assert "page_count" in meta
        assert meta["page_count"] == 1

    def test_truncate_text(self):
        from extract import truncate_text
        long_text = "x" * 20000
        truncated = truncate_text(long_text, max_chars=1000)
        assert len(truncated) <= 1100  # 1000 + ellipsis
        assert "truncated" in truncated

    def test_truncate_text_short(self):
        from extract import truncate_text
        short = "hello world"
        assert truncate_text(short, max_chars=1000) == short


# ---------------------------------------------------------------------------
# summarize
# ---------------------------------------------------------------------------

class TestSummarize:
    def test_summarize_paper_success(self):
        from summarize import summarize_paper
        import summarize as summarize_mod

        mock_choice = MagicMock()
        mock_choice.message.content = "**Main Problem**: Test summary content."

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(summarize_mod, "_client", mock_client):
            summary = summarize_paper(
                text="A paper about supply chains.",
                title="Test Paper",
                abstract="Abstract text.",
            )

        assert "Main Problem" in summary

    def test_summarize_paper_no_api_key(self):
        import summarize as summarize_mod
        from summarize import summarize_paper

        with patch.object(summarize_mod, "_client", None), \
             patch("summarize.config.OPENAI_API_KEY", ""):
            result = summarize_paper("text", "title")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------

class TestAnalyze:
    def test_analyze_literature_no_summaries(self):
        from analyze import analyze_literature
        result = analyze_literature([])
        assert "No summaries" in result

    def test_analyze_literature_success(self):
        from analyze import analyze_literature
        import analyze as analyze_mod

        papers = [
            {"summary": "Paper 1 summary about supply chain management."},
            {"summary": "Paper 2 summary about sustainability."},
        ]

        mock_choice = MagicMock()
        mock_choice.message.content = "**Common Themes**: Supply chain and sustainability."

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(analyze_mod, "_client", mock_client):
            result = analyze_literature(papers, keywords=["supply chain"])

        assert "Common Themes" in result


# ---------------------------------------------------------------------------
# ideas
# ---------------------------------------------------------------------------

class TestIdeas:
    def test_generate_ideas_empty_analysis(self):
        from ideas import generate_ideas
        result = generate_ideas("[No analysis]")
        assert "Cannot generate" in result

    def test_generate_ideas_success(self):
        from ideas import generate_ideas
        import ideas as ideas_mod

        mock_choice = MagicMock()
        mock_choice.message.content = "**Idea 1**: Test research idea about supply chains."

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(ideas_mod, "_client", mock_client):
            result = generate_ideas(
                "A good literature analysis.",
                keywords=["supply chain"],
                research_context="B2B focus",
            )

        assert "Idea 1" in result


# ---------------------------------------------------------------------------
# agent
# ---------------------------------------------------------------------------

class TestAgent:
    def test_strip_large_fields(self):
        from agent import ResearchAgent
        papers = [{"title": "Test", "extracted_text": "x" * 10000, "summary": "short"}]
        stripped = ResearchAgent._strip_large_fields(papers)
        assert "extracted_text" not in stripped[0]
        assert stripped[0]["title"] == "Test"

    def test_run_saves_report(self, tmp_path):
        from agent import ResearchAgent

        agent = ResearchAgent(papers_dir=tmp_path / "papers", output_dir=tmp_path / "output")

        with patch("agent.search_all", return_value=[
            {"title": "Paper A", "abstract": "Abstract A", "year": 2023,
             "authors": [], "open_access_pdf": "", "source": "arXiv", "doi": ""}
        ]), \
        patch("agent.download_papers", side_effect=lambda p, **kw: p), \
        patch("agent.extract_papers", side_effect=lambda p: p), \
        patch("agent.summarize_papers", side_effect=lambda p: [
            {**paper, "summary": "Mock summary"} for paper in p
        ]), \
        patch("agent.analyze_literature", return_value="Mock analysis"), \
        patch("agent.generate_ideas", return_value="Mock ideas"):

            report = agent.run(
                keywords=["supply chain"],
                research_context="Test context",
                max_results=5,
                save_report=True,
            )

        assert report["papers_found"] == 1
        assert report["literature_analysis"] == "Mock analysis"
        assert report["novel_ideas"] == "Mock ideas"
        output_files = list((tmp_path / "output").glob("report_*.json"))
        assert len(output_files) == 1

    def test_run_skip_download(self, tmp_path):
        from agent import ResearchAgent

        agent = ResearchAgent(papers_dir=tmp_path / "papers", output_dir=tmp_path / "output")

        with patch("agent.search_all", return_value=[]), \
        patch("agent.extract_papers", side_effect=lambda p: p), \
        patch("agent.summarize_papers", side_effect=lambda p: p), \
        patch("agent.analyze_literature", return_value="Analysis"), \
        patch("agent.generate_ideas", return_value="Ideas"):

            report = agent.run(
                keywords=["test"],
                skip_download=True,
                save_report=False,
            )

        assert report["papers_found"] == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def test_cli_help(self):
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "research" in result.output.lower()

    def test_search_command_table(self):
        from click.testing import CliRunner
        from cli import cli

        mock_papers = [
            {
                "title": "Test Paper",
                "abstract": "An abstract.",
                "year": 2023,
                "authors": ["Alice"],
                "doi": "",
                "url": "",
                "open_access_pdf": "https://example.com/paper.pdf",
                "source": "arXiv",
            }
        ]

        runner = CliRunner()
        with patch("search.search_semantic_scholar", return_value=[]), \
             patch("search.search_arxiv", return_value=mock_papers):
            result = runner.invoke(cli, ["search", "supply", "chain"])

        assert result.exit_code == 0
        assert "Test Paper" in result.output

    def test_run_command_no_keywords(self):
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["run"])
        assert result.exit_code != 0

    def test_report_command(self, tmp_path):
        from click.testing import CliRunner
        from cli import cli

        report_data = {
            "keywords": ["supply chain"],
            "timestamp": "2024-01-01T00:00:00Z",
            "papers_found": 5,
            "papers_with_pdf": 3,
            "papers_summarized": 3,
            "literature_analysis": "Test analysis",
            "novel_ideas": "Test ideas",
            "papers": [],
        }
        report_file = tmp_path / "report_test.json"
        report_file.write_text(json.dumps(report_data))

        runner = CliRunner()
        result = runner.invoke(cli, ["report", str(report_file), "--section", "analysis"])
        assert result.exit_code == 0
        assert "Test analysis" in result.output
