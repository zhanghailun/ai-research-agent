"""
Configuration management for AI Research Agent.
Loads settings from environment variables / .env file.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root
load_dotenv(Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# POE API
# ---------------------------------------------------------------------------
POE_API_KEY: str = os.getenv("POE_API_KEY", "")
POE_BOT_NAME: str = os.getenv("POE_BOT_NAME", "Claude-3.5-Sonnet")

# ---------------------------------------------------------------------------
# Semantic Scholar
# ---------------------------------------------------------------------------
SEMANTIC_SCHOLAR_API_KEY: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
SEMANTIC_SCHOLAR_BASE_URL: str = "https://api.semanticscholar.org/graph/v1"

# ---------------------------------------------------------------------------
# OpenAlex
# ---------------------------------------------------------------------------
OPENALEX_BASE_URL: str = "https://api.openalex.org"

# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------
ARXIV_BASE_URL: str = "http://export.arxiv.org/api/query"

# ---------------------------------------------------------------------------
# INFORMS journal targeting
# ---------------------------------------------------------------------------
# Human-readable journal names used in logging / UI
INFORMS_JOURNAL_NAMES: list[str] = [
    "Management Science",
    "Operations Research",
    "Manufacturing & Service Operations Management",
]
# When True, Semantic Scholar results are post-filtered to INFORMS journals
FILTER_TO_INFORMS_JOURNALS: bool = os.getenv(
    "FILTER_TO_INFORMS_JOURNALS", "true"
).lower() in ("1", "true", "yes")

# ---------------------------------------------------------------------------
# Unpaywall (optional, for finding open-access PDFs by DOI)
# ---------------------------------------------------------------------------
UNPAYWALL_EMAIL: str = os.getenv("UNPAYWALL_EMAIL", "research@example.com")

# ---------------------------------------------------------------------------
# Local storage
# ---------------------------------------------------------------------------
PAPERS_DIR: Path = Path(os.getenv("PAPERS_DIR", "papers"))
OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "output"))

# ---------------------------------------------------------------------------
# Search defaults
# ---------------------------------------------------------------------------
DEFAULT_MAX_RESULTS: int = int(os.getenv("DEFAULT_MAX_RESULTS", "20"))

# ---------------------------------------------------------------------------
# Download settings
# ---------------------------------------------------------------------------
DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "30"))
DOWNLOAD_RETRIES: int = int(os.getenv("DOWNLOAD_RETRIES", "3"))
DOWNLOAD_BACKOFF: float = float(os.getenv("DOWNLOAD_BACKOFF", "2.0"))

# ---------------------------------------------------------------------------
# LLM settings
# ---------------------------------------------------------------------------
SUMMARIZE_MAX_TOKENS: int = int(os.getenv("SUMMARIZE_MAX_TOKENS", "1500"))
ANALYSIS_MAX_TOKENS: int = int(os.getenv("ANALYSIS_MAX_TOKENS", "2000"))
IDEAS_MAX_TOKENS: int = int(os.getenv("IDEAS_MAX_TOKENS", "2500"))
PDF_TEXT_LIMIT: int = int(os.getenv("PDF_TEXT_LIMIT", "12000"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = os.getenv("LOG_FILE", "")


def setup_logging() -> logging.Logger:
    """Configure root logger based on settings."""
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if LOG_FILE:
        handlers.append(logging.FileHandler(LOG_FILE))

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )
    return logging.getLogger("research_agent")


def ensure_dirs() -> None:
    """Create required local directories if they don't exist."""
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
