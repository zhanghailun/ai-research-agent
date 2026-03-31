"""
search.py — Paper discovery via Semantic Scholar, OpenAlex, arXiv, and SSRN.

Public API
----------
search_semantic_scholar(keywords, limit) -> list[dict]
search_openalex_informs(keywords, limit) -> list[dict]
search_arxiv(keywords, limit)            -> list[dict]
search_ssrn(keywords, limit)             -> list[dict]
filter_informs_papers(papers)            -> list[dict]
search_all(keywords, limit)              -> list[dict]
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
# INFORMS journal targeting
# ---------------------------------------------------------------------------

# Normalised (lower-cased) variants accepted as INFORMS venues
INFORMS_JOURNAL_NAMES: frozenset[str] = frozenset({
    "management science",
    "operations research",
    "manufacturing & service operations management",
    "manufacturing and service operations management",
    "msom",
    "m&som",
})

# ISSNs for the three target INFORMS journals (print + online)
_INFORMS_ISSNS: list[str] = [
    "0025-1909",  # Management Science (print)
    "1526-5501",  # Management Science (online)
    "0030-364X",  # Operations Research (print)
    "1526-5463",  # Operations Research (online)
    "1523-4614",  # MSOM (print)
    "1526-5498",  # MSOM (online)
]


def _is_informs_journal(venue: str) -> bool:
    """Return True if *venue* is one of the target INFORMS journals."""
    if not venue:
        return False
    return venue.lower().strip() in INFORMS_JOURNAL_NAMES


def filter_informs_papers(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only papers whose *venue* field matches a target INFORMS journal."""
    return [p for p in papers if _is_informs_journal(p.get("venue", ""))]


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


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """Reconstruct a readable abstract from OpenAlex's inverted-index format."""
    if not inverted_index:
        return ""
    position_word: dict[int, str] = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            position_word[pos] = word
    return " ".join(position_word[i] for i in sorted(position_word))


# ---------------------------------------------------------------------------
# Semantic Scholar
# ---------------------------------------------------------------------------

def search_semantic_scholar(keywords: list[str], limit: int = 20) -> list[dict[str, Any]]:
    """
    Search Semantic Scholar for papers matching *keywords*.

    Returns a list of paper dicts with normalised keys:
      title, abstract, year, authors, doi, url,
      open_access_pdf, venue, source
    """
    query = " ".join(keywords)
    url = f"{config.SEMANTIC_SCHOLAR_BASE_URL}/paper/search"
    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": (
            "title,abstract,authors,year,externalIds,"
            "isOpenAccess,openAccessPdf,url,venue,publicationVenue"
        ),
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
        venue = paper.get("venue", "") or (paper.get("publicationVenue") or {}).get("name", "")
        results.append({
            "title": paper.get("title", ""),
            "abstract": paper.get("abstract", ""),
            "year": paper.get("year"),
            "authors": [a.get("name", "") for a in (paper.get("authors") or [])],
            "doi": doi,
            "url": paper.get("url", ""),
            "open_access_pdf": open_pdf,
            "venue": venue,
            "source": "SemanticScholar",
        })

    logger.info("Semantic Scholar returned %d papers", len(results))
    return results


# ---------------------------------------------------------------------------
# OpenAlex — INFORMS journals
# ---------------------------------------------------------------------------

_OPENALEX_HEADERS = {
    "User-Agent": (
        "ai-research-agent/1.0 (mailto:research@example.com)"
    ),
}


def search_openalex_informs(keywords: list[str], limit: int = 20) -> list[dict[str, Any]]:
    """
    Search OpenAlex for papers published in the three target INFORMS journals:
    Management Science, Operations Research, and MSOM.

    Uses ISSN-based filtering so every returned paper is from one of these
    journals.  Returns a normalised list matching the Semantic Scholar format.
    """
    query = " ".join(keywords)
    issn_filter = "|".join(_INFORMS_ISSNS)
    url = f"{config.OPENALEX_BASE_URL}/works"
    params = {
        "search": query,
        "filter": f"primary_location.source.issn:{issn_filter}",
        "per_page": min(limit, 200),
        "sort": "relevance_score:desc",
        "select": (
            "id,title,abstract_inverted_index,authorships,"
            "publication_year,doi,open_access,primary_location,best_oa_location"
        ),
    }

    logger.info(
        "Searching OpenAlex (INFORMS journals) for: %s (limit=%d)", query, limit
    )
    try:
        resp = requests.get(
            url,
            params=params,
            headers=_OPENALEX_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("OpenAlex search failed: %s", exc)
        return []

    results: list[dict[str, Any]] = []
    for work in resp.json().get("results", [])[:limit]:
        doi = work.get("doi") or ""
        if doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]

        abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

        authors = [
            authorship.get("author", {}).get("display_name", "")
            for authorship in (work.get("authorships") or [])
        ]

        venue = (
            ((work.get("primary_location") or {}).get("source") or {})
            .get("display_name", "")
        )

        oa_url = (
            ((work.get("best_oa_location") or {}).get("pdf_url") or "")
            or ((work.get("open_access") or {}).get("oa_url") or "")
        )

        work_id = work.get("id", "")
        paper_url = f"https://doi.org/{doi}" if doi else work_id

        results.append({
            "title": work.get("title") or "",
            "abstract": abstract,
            "year": work.get("publication_year"),
            "authors": [a for a in authors if a],
            "doi": doi,
            "url": paper_url,
            "open_access_pdf": oa_url,
            "venue": venue,
            "source": "OpenAlex",
        })

    logger.info("OpenAlex (INFORMS) returned %d papers", len(results))
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
            "venue": "",
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
            "venue": "",
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
    filter_journals: bool = True,
) -> list[dict[str, Any]]:
    """
    Search multiple sources and return a combined, optionally deduplicated list.

    Parameters
    ----------
    keywords        : list of keyword strings
    limit           : max results *per source*
    sources         : list of source names to query; defaults to
                      ["openalex_informs", "semantic_scholar"]
    deduplicate     : remove papers with the same (normalised) title
    filter_journals : when True, Semantic Scholar results are post-filtered to
                      keep only papers from the target INFORMS journals
                      (Management Science, Operations Research, MSOM).
                      ``openalex_informs`` always returns only INFORMS papers
                      regardless of this flag.

    Notes
    -----
    The default sources are intentionally restricted to INFORMS-focused
    channels.  Pass ``sources=["arxiv"]`` or ``sources=["ssrn"]`` explicitly
    if broader coverage is needed.
    """
    if sources is None:
        sources = ["openalex_informs", "semantic_scholar"]

    all_papers: list[dict[str, Any]] = []

    if "openalex_informs" in sources:
        all_papers.extend(search_openalex_informs(keywords, limit=limit))
        time.sleep(0.3)  # Be polite to the API

    if "semantic_scholar" in sources:
        # Fetch extra headroom so filtering still yields enough results
        fetch_limit = min(limit * 3, 100) if filter_journals else limit
        ss_papers = search_semantic_scholar(keywords, limit=fetch_limit)
        if filter_journals:
            filtered = filter_informs_papers(ss_papers)
            if filtered:
                ss_papers = filtered[:limit]
            else:
                logger.info(
                    "No INFORMS papers found in Semantic Scholar results for %s; "
                    "including all %d results as fallback",
                    keywords,
                    len(ss_papers),
                )
                ss_papers = ss_papers[:limit]
        all_papers.extend(ss_papers)
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
