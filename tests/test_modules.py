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
            "venue": "Management Science",
            "source": "OpenAlex",
        }
        paper_b = {**paper_a, "source": "SemanticScholar"}

        with patch("search.search_openalex_informs", return_value=[paper_a]), \
             patch("search.search_semantic_scholar", return_value=[paper_b]):
            results = search_all(["test"], limit=5, deduplicate=True)

        # Should have only 1 after deduplication
        assert len(results) == 1

    def test_search_ssrn_success(self):
        """Mock a successful SSRN HTML response."""
        from search import search_ssrn

        fake_html = """
        <html><body>
        <div class="result-item">
          <div class="title">
            <a href="/sol3/papers.cfm?abstract_id=1234">SSRN Test Paper</a>
          </div>
          <div class="authors"><a class="author">Alice Smith</a></div>
          Posted: 15 Jan 2023
        </div>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = fake_html

        with patch("search.requests.get", return_value=mock_response):
            results = search_ssrn(["supply chain"], limit=5)

        assert len(results) == 1
        assert results[0]["title"] == "SSRN Test Paper"
        assert results[0]["source"] == "SSRN"
        assert results[0]["year"] == 2023
        assert "Alice Smith" in results[0]["authors"]

    def test_search_ssrn_failure(self):
        """Mock a failed SSRN request."""
        import requests
        from search import search_ssrn

        with patch("search.requests.get", side_effect=requests.RequestException("timeout")):
            results = search_ssrn(["test"], limit=5)
        assert results == []

    def test_search_all_includes_ssrn(self):
        """Ensure search_all calls SSRN when ssrn is in sources."""
        from search import search_all

        ssrn_paper = {
            "title": "SSRN Management Paper",
            "abstract": "B",
            "year": 2022,
            "authors": [],
            "doi": "",
            "url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=9999",
            "open_access_pdf": "",
            "venue": "",
            "source": "SSRN",
        }

        with patch("search.search_semantic_scholar", return_value=[]), \
             patch("search.search_arxiv", return_value=[]), \
             patch("search.search_ssrn", return_value=[ssrn_paper]):
            results = search_all(["test"], limit=5, sources=["ssrn"])

        assert len(results) == 1
        assert results[0]["source"] == "SSRN"

    def test_search_openalex_informs_success(self):
        """Mock a successful OpenAlex response for INFORMS journals."""
        from search import search_openalex_informs

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "https://openalex.org/W1234567",
                    "title": "Supply Chain Optimization in Management Science",
                    "abstract_inverted_index": {
                        "This": [0],
                        "is": [1],
                        "an": [2],
                        "abstract": [3],
                    },
                    "authorships": [
                        {"author": {"display_name": "Alice Zhang"}},
                        {"author": {"display_name": "Bob Lee"}},
                    ],
                    "publication_year": 2022,
                    "doi": "https://doi.org/10.1287/mnsc.2022.001",
                    "open_access": {"oa_url": ""},
                    "best_oa_location": {"pdf_url": ""},
                    "primary_location": {
                        "source": {"display_name": "Management Science"}
                    },
                }
            ]
        }

        with patch("search.requests.get", return_value=mock_response):
            results = search_openalex_informs(["supply chain"], limit=5)

        assert len(results) == 1
        assert results[0]["title"] == "Supply Chain Optimization in Management Science"
        assert results[0]["venue"] == "Management Science"
        assert results[0]["doi"] == "10.1287/mnsc.2022.001"
        assert results[0]["source"] == "OpenAlex"
        assert results[0]["abstract"] == "This is an abstract"

    def test_search_openalex_informs_failure(self):
        """Mock a failed OpenAlex request."""
        import requests
        from search import search_openalex_informs

        with patch("search.requests.get", side_effect=requests.RequestException("timeout")):
            results = search_openalex_informs(["test"], limit=5)
        assert results == []

    def test_filter_informs_papers(self):
        """Ensure filter_informs_papers keeps only INFORMS journal papers."""
        from search import filter_informs_papers

        papers = [
            {"title": "MS Paper", "venue": "Management Science", "source": "SemanticScholar"},
            {"title": "OR Paper", "venue": "Operations Research", "source": "SemanticScholar"},
            {"title": "MSOM Paper", "venue": "Manufacturing & Service Operations Management", "source": "OpenAlex"},
            {"title": "Other Paper", "venue": "Journal of Finance", "source": "SemanticScholar"},
            {"title": "No Venue Paper", "venue": "", "source": "arXiv"},
        ]

        filtered = filter_informs_papers(papers)
        assert len(filtered) == 3
        titles = {p["title"] for p in filtered}
        assert "MS Paper" in titles
        assert "OR Paper" in titles
        assert "MSOM Paper" in titles
        assert "Other Paper" not in titles
        assert "No Venue Paper" not in titles

    def test_filter_informs_papers_case_insensitive(self):
        """Venue matching must be case-insensitive."""
        from search import filter_informs_papers

        papers = [
            {"title": "P1", "venue": "management science", "source": "SemanticScholar"},
            {"title": "P2", "venue": "OPERATIONS RESEARCH", "source": "SemanticScholar"},
            {"title": "P3", "venue": "msom", "source": "OpenAlex"},
        ]
        filtered = filter_informs_papers(papers)
        assert len(filtered) == 3

    def test_search_all_defaults_to_informs_sources(self):
        """search_all should use openalex_informs and semantic_scholar by default."""
        from search import search_all

        informs_paper = {
            "title": "Inventory Management",
            "abstract": "MS paper",
            "year": 2023,
            "authors": ["Alice"],
            "doi": "10.1287/mnsc.2023.001",
            "url": "https://doi.org/10.1287/mnsc.2023.001",
            "open_access_pdf": "",
            "venue": "Management Science",
            "source": "OpenAlex",
        }

        with patch("search.search_openalex_informs", return_value=[informs_paper]) as mock_oa, \
             patch("search.search_semantic_scholar", return_value=[]) as mock_ss:
            results = search_all(["inventory"], limit=5)

        mock_oa.assert_called_once()
        mock_ss.assert_called_once()
        assert results[0]["venue"] == "Management Science"

    def test_search_all_semantic_scholar_filtered(self):
        """search_all should filter Semantic Scholar results to INFORMS journals."""
        from search import search_all

        ms_paper = {
            "title": "Revenue Management",
            "abstract": "MS paper",
            "year": 2022,
            "authors": [],
            "doi": "",
            "url": "",
            "open_access_pdf": "",
            "venue": "Management Science",
            "source": "SemanticScholar",
        }
        other_paper = {
            "title": "Finance Paper",
            "abstract": "Finance",
            "year": 2022,
            "authors": [],
            "doi": "",
            "url": "",
            "open_access_pdf": "",
            "venue": "Journal of Finance",
            "source": "SemanticScholar",
        }

        with patch("search.search_openalex_informs", return_value=[]), \
             patch("search.search_semantic_scholar", return_value=[ms_paper, other_paper]):
            results = search_all(["revenue"], limit=5, filter_journals=True)

        assert len(results) == 1
        assert results[0]["title"] == "Revenue Management"

    def test_reconstruct_abstract(self):
        """_reconstruct_abstract should reassemble inverted-index format correctly."""
        from search import _reconstruct_abstract

        inverted = {"Hello": [0], "world": [1], "foo": [2]}
        assert _reconstruct_abstract(inverted) == "Hello world foo"

    def test_reconstruct_abstract_multiposition(self):
        """Words appearing at multiple positions should each be placed correctly."""
        from search import _reconstruct_abstract

        # "the" appears at positions 0 and 3; "cat" at 1; "sat" at 2
        inverted = {"the": [0, 3], "cat": [1], "sat": [2]}
        assert _reconstruct_abstract(inverted) == "the cat sat the"

    def test_reconstruct_abstract_empty(self):
        from search import _reconstruct_abstract

        assert _reconstruct_abstract(None) == ""
        assert _reconstruct_abstract({}) == ""


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

        with patch("summarize._call_llm", return_value="**Main Problem**: Test summary content."):
            summary = summarize_paper(
                text="A paper about supply chains.",
                title="Test Paper",
                abstract="Abstract text.",
            )

        assert "Main Problem" in summary

    def test_summarize_paper_no_api_key(self):
        from summarize import summarize_paper

        with patch("summarize.config.POE_API_KEY", ""):
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

        papers = [
            {"summary": "Paper 1 summary about supply chain management."},
            {"summary": "Paper 2 summary about sustainability."},
        ]

        with patch("analyze._call_llm", return_value="**Common Themes**: Supply chain and sustainability."):
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

        with patch("ideas._call_llm", return_value="**Idea 1**: Test research idea about supply chains."):
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
                "venue": "Management Science",
                "source": "OpenAlex",
            }
        ]

        runner = CliRunner()
        with patch("search.search_openalex_informs", return_value=mock_papers), \
             patch("search.search_semantic_scholar", return_value=[]):
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


# ---------------------------------------------------------------------------
# propose
# ---------------------------------------------------------------------------

class TestPropose:
    def test_generate_proposal_success(self):
        """generate_proposal() calls the LLM and returns its text."""
        from propose import generate_proposal

        with patch("propose._call_llm", return_value="## 1. Title\nTest Proposal") as mock_llm:
            result = generate_proposal(
                idea="Platform opacity and consumer welfare",
                research_context="Focus on e-commerce",
                literature_analysis="Lit review here",
            )

        assert "Test Proposal" in result
        mock_llm.assert_called_once()
        # Verify the writing guide is injected into the system prompt
        system_prompt = mock_llm.call_args[0][0]
        assert "INFORMS" in system_prompt or "Management Science" in system_prompt

    def test_generate_proposal_no_api_key(self):
        """generate_proposal() returns an error string when the LLM raises."""
        from propose import generate_proposal

        with patch("propose._call_llm", side_effect=RuntimeError("No key")):
            result = generate_proposal(idea="Some idea")

        assert result.startswith("[Proposal generation failed")

    def test_generate_proposal_empty_idea(self):
        """generate_proposal() returns an error string for blank input."""
        from propose import generate_proposal

        result = generate_proposal(idea="")
        assert result.startswith("[Cannot generate proposal")

        result2 = generate_proposal(idea="   ")
        assert result2.startswith("[Cannot generate proposal")

    def test_load_writing_guide_present(self, tmp_path, monkeypatch):
        """_load_writing_guide() reads the skill file when it exists."""
        import propose as propose_module

        skill_file = tmp_path / "management_science_writing_skill.md"
        skill_file.write_text("# Guide\nSome content", encoding="utf-8")
        monkeypatch.setattr(propose_module, "_SKILL_PATH", skill_file)

        from propose import _load_writing_guide
        guide = _load_writing_guide()
        assert "Some content" in guide

    def test_load_writing_guide_missing(self, tmp_path, monkeypatch):
        """_load_writing_guide() returns '' when the file is not found."""
        import propose as propose_module

        monkeypatch.setattr(propose_module, "_SKILL_PATH", tmp_path / "missing.md")

        from propose import _load_writing_guide
        guide = _load_writing_guide()
        assert guide == ""

    def test_propose_cli_command_free_text(self):
        """CLI propose command works with a free-text idea argument."""
        from click.testing import CliRunner
        from cli import cli

        with patch("propose.generate_proposal", return_value="## 1. Title\nTest Proposal"):
            runner = CliRunner()
            result = runner.invoke(cli, ["propose", "My research idea"])

        assert result.exit_code == 0
        assert "Test Proposal" in result.output

    def test_propose_cli_command_from_report(self, tmp_path):
        """CLI propose command loads an idea from a saved report."""
        from click.testing import CliRunner
        from cli import cli

        report_data = {
            "keywords": ["supply chain"],
            "literature_analysis": "Some analysis",
            "novel_ideas": (
                "**Idea 1: First Idea**\n- Research Question: ...\n\n"
                "**Idea 2: Second Idea**\n- Research Question: ..."
            ),
        }
        report_file = tmp_path / "report_test.json"
        report_file.write_text(json.dumps(report_data))

        with patch("propose.generate_proposal", return_value="Proposal text") as mock_prop:
            runner = CliRunner()
            result = runner.invoke(
                cli, ["propose", "--from-report", str(report_file), "-i", "1"]
            )

        assert result.exit_code == 0
        assert "Proposal text" in result.output
        # Verify the first idea was passed in
        called_idea = mock_prop.call_args[1]["idea"] if mock_prop.call_args[1] else mock_prop.call_args[0][0]
        assert "First Idea" in called_idea

    def test_propose_cli_command_no_input(self):
        """CLI propose command exits with error when no idea is given."""
        from click.testing import CliRunner
        from cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["propose"])
        assert result.exit_code != 0

    def test_propose_cli_saves_output_file(self, tmp_path):
        """CLI propose command writes the proposal to a file when --output is set."""
        from click.testing import CliRunner
        from cli import cli

        output_file = tmp_path / "my_proposal.md"

        with patch("propose.generate_proposal", return_value="Saved proposal"):
            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["propose", "Some idea", "--output", str(output_file)],
            )

        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == "Saved proposal"

    def test_agent_write_proposal_flag(self, tmp_path):
        """ResearchAgent.run() calls generate_proposal when write_proposal=True."""
        from agent import ResearchAgent

        agent = ResearchAgent(
            papers_dir=tmp_path / "papers", output_dir=tmp_path / "output"
        )

        mock_paper = {
            "title": "A paper",
            "abstract": "Abstract",
            "year": 2023,
            "authors": ["Alice"],
            "doi": "",
            "url": "",
            "open_access_pdf": "",
            "local_pdf": "",
            "extracted_text": "",
            "summary": "Summary of the paper.",
            "source": "test",
        }

        with patch("agent.search_all", return_value=[mock_paper]), \
             patch("agent.download_papers", return_value=[mock_paper]), \
             patch("agent.extract_papers", side_effect=lambda p: p), \
             patch("agent.summarize_papers", side_effect=lambda p: p), \
             patch("agent.analyze_literature", return_value="Mock analysis"), \
             patch("agent.generate_ideas", return_value="Mock ideas"), \
             patch("agent.generate_proposal", return_value="Mock proposal") as mock_prop:

            report = agent.run(
                keywords=["test"],
                write_proposal=True,
                save_report=False,
            )

        mock_prop.assert_called_once()
        assert report["proposal"] == "Mock proposal"

    def test_agent_no_proposal_by_default(self, tmp_path):
        """ResearchAgent.run() does NOT call generate_proposal by default."""
        from agent import ResearchAgent

        agent = ResearchAgent(
            papers_dir=tmp_path / "papers", output_dir=tmp_path / "output"
        )

        with patch("agent.search_all", return_value=[]), \
             patch("agent.extract_papers", side_effect=lambda p: p), \
             patch("agent.summarize_papers", side_effect=lambda p: p), \
             patch("agent.analyze_literature", return_value="Analysis"), \
             patch("agent.generate_ideas", return_value="Ideas"), \
             patch("agent.generate_proposal") as mock_prop:

            report = agent.run(
                keywords=["test"],
                skip_download=True,
                save_report=False,
            )

        mock_prop.assert_not_called()
        assert "proposal" not in report
