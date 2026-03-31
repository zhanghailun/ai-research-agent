"""
download.py — Automated PDF downloader with retry logic.

Public API
----------
download_pdf(url, dest_path) -> bool
download_papers(papers, papers_dir) -> list[dict]
find_open_access_pdf(doi) -> str | None   (via Unpaywall)
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any

import requests

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AIResearchAgent/1.0; "
        "+https://github.com/zhanghailun/ai-research-agent)"
    )
}


def _sanitize_filename(name: str, max_len: int = 80) -> str:
    """Convert an arbitrary string to a safe filesystem filename."""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r"\s+", "_", name).strip("_.")
    return name[:max_len]


# ---------------------------------------------------------------------------
# Core download
# ---------------------------------------------------------------------------

def download_pdf(
    url: str,
    dest_path: Path | str,
    retries: int | None = None,
    timeout: int | None = None,
    backoff: float | None = None,
) -> bool:
    """
    Download a PDF from *url* and save it to *dest_path*.

    Retries on transient failures using exponential back-off.

    Returns True on success, False otherwise.
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    max_retries = retries if retries is not None else config.DOWNLOAD_RETRIES
    timeout_sec = timeout if timeout is not None else config.DOWNLOAD_TIMEOUT
    backoff_sec = backoff if backoff is not None else config.DOWNLOAD_BACKOFF

    for attempt in range(1, max_retries + 1):
        try:
            logger.debug("Downloading %s (attempt %d/%d)", url, attempt, max_retries)
            resp = requests.get(
                url, headers=_HEADERS, timeout=timeout_sec, stream=True, allow_redirects=True
            )
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            if "pdf" not in content_type and attempt == max_retries:
                logger.warning(
                    "Unexpected Content-Type '%s' for %s — saving anyway", content_type, url
                )

            with open(dest_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    fh.write(chunk)

            size = dest_path.stat().st_size
            if size < 1024:
                logger.warning("Downloaded file is suspiciously small (%d bytes): %s", size, dest_path)
                dest_path.unlink(missing_ok=True)
                return False

            logger.info("Saved PDF (%d bytes) → %s", size, dest_path)
            return True

        except requests.HTTPError as exc:
            # Don't retry on 4xx client errors
            if exc.response is not None and exc.response.status_code < 500:
                logger.warning("HTTP %d for %s — skipping", exc.response.status_code, url)
                return False
            logger.warning("HTTP error on attempt %d: %s", attempt, exc)

        except requests.RequestException as exc:
            logger.warning("Request error on attempt %d: %s", attempt, exc)

        if attempt < max_retries:
            sleep_time = backoff_sec ** attempt
            logger.debug("Retrying in %.1f seconds…", sleep_time)
            time.sleep(sleep_time)

    logger.error("Failed to download %s after %d attempts", url, max_retries)
    return False


# ---------------------------------------------------------------------------
# Unpaywall (open-access lookup by DOI)
# ---------------------------------------------------------------------------

def find_open_access_pdf(doi: str) -> str | None:
    """
    Use the Unpaywall API to find an open-access PDF URL for a given DOI.

    Returns the URL string on success, None otherwise.
    """
    if not doi:
        return None
    email = config.UNPAYWALL_EMAIL
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("is_oa"):
            best = data.get("best_oa_location") or {}
            pdf_url = best.get("url_for_pdf") or best.get("url")
            if pdf_url:
                logger.debug("Unpaywall found PDF for DOI %s: %s", doi, pdf_url)
                return pdf_url
    except Exception as exc:
        logger.debug("Unpaywall lookup failed for DOI %s: %s", doi, exc)
    return None


# ---------------------------------------------------------------------------
# Batch download
# ---------------------------------------------------------------------------

def download_papers(
    papers: list[dict[str, Any]],
    papers_dir: Path | str | None = None,
) -> list[dict[str, Any]]:
    """
    Download PDFs for a list of paper dicts.

    Each paper dict should have at least:
      - title
      - open_access_pdf  (direct PDF URL)
      - doi              (optional fallback via Unpaywall)

    The function adds a ``local_pdf`` key (path string) to papers that were
    successfully downloaded.  Papers without a downloadable PDF are skipped
    but kept in the returned list (with ``local_pdf`` absent or empty).

    Returns the updated papers list.
    """
    if papers_dir is None:
        papers_dir = config.PAPERS_DIR
    papers_dir = Path(papers_dir)
    papers_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    for i, paper in enumerate(papers):
        title = paper.get("title", f"paper_{i}")
        pdf_url = paper.get("open_access_pdf", "")

        # Fallback: try Unpaywall
        if not pdf_url and paper.get("doi"):
            pdf_url = find_open_access_pdf(paper["doi"]) or ""

        if not pdf_url:
            logger.debug("No PDF URL for: %s", title)
            paper["local_pdf"] = ""
            continue

        safe_name = _sanitize_filename(title)
        dest = papers_dir / f"{i:03d}_{safe_name}.pdf"

        if dest.exists():
            logger.debug("Already downloaded: %s", dest)
            paper["local_pdf"] = str(dest)
            downloaded += 1
            continue

        success = download_pdf(pdf_url, dest)
        paper["local_pdf"] = str(dest) if success else ""
        if success:
            downloaded += 1
        # Small delay to be polite
        time.sleep(0.3)

    logger.info("Downloaded %d / %d PDFs", downloaded, len(papers))
    return papers
