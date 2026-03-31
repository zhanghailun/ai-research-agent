"""
search.py — Paper discovery via Semantic Scholar, arXiv, and SSRN.

Public API
----------
search_semantic_scholar(keywords, limit) -> list[dict]
search_arxiv(keywords, limit)           -> list[dict]
search_ssrn(keywords, limit)            -> list[dict]
search_all(keywords, limit)             -> list[dict]
"""

from __future__ import annotations

import logging
import time
import urllib.parse
from typing import Any

import feedparser
import requests
from bs4 import BeautifulSoup

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ss_headers() -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if config.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = config.SEMANTIC_SCHOLAR_API_KEY
    return headers


def _safe_get(url: str, params: dict | None = None, timeout: int = 30) -> requests.Response | None:
    """GET with basic error handling; returns None on failure."""
    try:
        resp = requests.get(url, params=params, headers=_ss_headers(), timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.RequestException as exc:
        logger.warning("HTTP request failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Semantic Scholar
# ---------------------------------------------------------------------------

def search_semantic_scholar(keywords: list[str], limit: int = 20) -> list[dict[str, Any]]:
    """
    Search Semantic Scholar for papers matching *keywords*.

    Returns a list of paper dicts with normalised keys:
      title, abstract, year, authors, doi, url,
      open_access_pdf, source
    """
    query = " ".join(keywords)
    url = f"{config.SEMANTIC_SCHOLAR_BASE_URL}/paper/search"
    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": "title,abstract,authors,year,externalIds,isOpenAccess,openAccessPdf,url",
    }

    logger.info("Searching Semantic Scholar for: %s (limit=%d)", query, limit)
    resp = _safe_get(url, params=params)
    if resp is None:
        return []

    data = resp.json().get("data", [])
    results: list[dict[str, Any]] = []
    for paper in data:
        doi = (paper.get("externalIds") or {}).get("DOI", "")
        open_pdf = (paper.get("openAccessPdf") or {}).get("url", "")
        results.append({
            "title": paper.get("title", ""),
            "abstract": paper.get("abstract", ""),
            "year": paper.get("year"),
            "authors": [a.get("name", "") for a in (paper.get("authors") or [])],
            "doi": doi,
            "url": paper.get("url", ""),
            "open_access_pdf": open_pdf,
            "source": "SemanticScholar",
        })

    logger.info("Semantic Scholar returned %d papers", len(results))
    return results


# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------

def search_arxiv(keywords: list[str], limit: int = 20) -> list[dict[str, Any]]:
    """
    Search arXiv for papers matching *keywords*.

    Returns a normalised list matching the Semantic Scholar format.
    """
    # Build query string — AND together all keywords
    query_parts = [urllib.parse.quote(kw) for kw in keywords]
    query = "+AND+".join(f"all:{part}" for part in query_parts)
    url = f"{config.ARXIV_BASE_URL}?search_query={query}&max_results={limit}&sortBy=relevance"

    logger.info("Searching arXiv for: %s (limit=%d)", " AND ".join(keywords), limit)

    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        logger.warning("arXiv search failed: %s", exc)
        return []

    results: list[dict[str, Any]] = []
    for entry in feed.entries:
        # Find the PDF link
        pdf_url = ""
        for link in getattr(entry, "links", []):
            if link.get("type") == "application/pdf":
                pdf_url = link.get("href", "")
                break
        if not pdf_url:
            arxiv_id = entry.get("id", "").split("/abs/")[-1]
            if arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        authors = [a.get("name", "") for a in getattr(entry, "authors", [])]
        year = None
        published = getattr(entry, "published", "")
        if published:
            try:
                year = int(published[:4])
            except ValueError:
                pass

        results.append({
            "title": getattr(entry, "title", "").replace("\n", " ").strip(),
            "abstract": getattr(entry, "summary", "").replace("\n", " ").strip(),
            "year": year,
            "authors": authors,
            "doi": "",
            "url": getattr(entry, "id", ""),
            "open_access_pdf": pdf_url,
            "source": "arXiv",
        })

    logger.info("arXiv returned %d papers", len(results))
    return results


# ---------------------------------------------------------------------------
# SSRN
# ---------------------------------------------------------------------------

_SSRN_SEARCH_URL = "https://papers.ssrn.com/sol3/results.cfm"
_SSRN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ai-research-agent/1.0; "
        "+https://github.com/zhanghailun/ai-research-agent)"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_SSRN_REQUEST_DELAY: float = 0.5  # seconds — be polite to the server


def search_ssrn(keywords: list[str], limit: int = 20) -> list[dict[str, Any]]:
    """
    Search SSRN for papers matching *keywords* by scraping the HTML search results.

    Returns a normalised list matching the Semantic Scholar format.
    """
    import re

    query = " ".join(keywords)
    params = {"txtSearch": query, "sortBy": "0", "start": "0"}

    logger.info("Searching SSRN for: %s (limit=%d)", query, limit)

    try:
        resp = requests.get(
            _SSRN_SEARCH_URL,
            params=params,
            headers=_SSRN_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("SSRN search failed: %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results: list[dict[str, Any]] = []

    # SSRN result items are contained in <div class="title"> inside result rows
    for title_div in soup.select("div.title")[:limit]:
        link = title_div.find("a", href=True)
        if not link:
            continue

        title = link.get_text(strip=True)
        paper_url: str = link["href"]
        if paper_url and not paper_url.startswith("http"):
            paper_url = "https://papers.ssrn.com" + paper_url

        # Walk up to the nearest result container to find metadata
        container = title_div.find_parent("div", class_="result-item") or title_div.parent

        abstract = ""
        authors: list[str] = []
        year: int | None = None

        if container:
            # Abstract
            abstract_el = container.find("div", class_=re.compile(r"abstract", re.I))
            if abstract_el:
                abstract = abstract_el.get_text(separator=" ", strip=True)

            # Authors
            for author_tag in container.select("a.author, span.author, .authors a"):
                name = author_tag.get_text(strip=True)
                if name:
                    authors.append(name)

            # Year: look for a 4-digit year in any text within the container
            date_text = container.get_text(separator=" ")
            year_match = re.search(r"\b(19|20)\d{2}\b", date_text)
            if year_match:
                year = int(year_match.group())

        results.append({
            "title": title,
            "abstract": abstract,
            "year": year,
            "authors": authors,
            "doi": "",
            "url": paper_url,
            "open_access_pdf": "",
            "source": "SSRN",
        })

    logger.info("SSRN returned %d papers", len(results))
    return results


# ---------------------------------------------------------------------------
# Combined search
# ---------------------------------------------------------------------------

def search_all(
    keywords: list[str],
    limit: int = 20,
    sources: list[str] | None = None,
    deduplicate: bool = True,
) -> list[dict[str, Any]]:
    """
    Search multiple sources and return a combined, optionally deduplicated list.

    Parameters
    ----------
    keywords   : list of keyword strings
    limit      : max results *per source*
    sources    : list of source names to query; defaults to ["semantic_scholar", "arxiv"]
    deduplicate: remove papers with the same (normalised) title
    """
    if sources is None:
        sources = ["semantic_scholar", "arxiv"]

    all_papers: list[dict[str, Any]] = []

    if "semantic_scholar" in sources:
        all_papers.extend(search_semantic_scholar(keywords, limit=limit))
        time.sleep(0.5)  # Be polite to the API

    if "arxiv" in sources:
        all_papers.extend(search_arxiv(keywords, limit=limit))

    if "ssrn" in sources:
        time.sleep(_SSRN_REQUEST_DELAY)  # Be polite to the server
        all_papers.extend(search_ssrn(keywords, limit=limit))

    if deduplicate:
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for paper in all_papers:
            key = paper.get("title", "").lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(paper)
        all_papers = unique

    logger.info("Combined search returned %d unique papers", len(all_papers))
    return all_papers
