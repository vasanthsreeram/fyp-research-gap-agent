"""Semantic Scholar Graph API client for paper search."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from src.models import Paper

logger = logging.getLogger(__name__)

S2_BASE = "https://api.semanticscholar.org/graph/v1"

DEFAULT_QUERIES = [
    "nucleic acid delivery lipid nanoparticle mRNA vaccine",
    "LNP ionizable lipid structure activity delivery",
    "mRNA delivery extrahepatic targeting nanoparticles",
    "LNPs endosomal escape mechanism nucleic acid",
    "LNPs targeted delivery extrahepatic siRNA mRNA",
    "tissue specific lipid nanoparticles gene therapy",
    "lipid nanoparticles delivery efficiency determinants",
    "endosomal escape lipid nanoparticles delivery",
    "non-viral delivery nucleic acid therapeutics",
    "mRNA LNP protein corona biodistribution",
]


def search(
    query: str,
    limit: int = 20,
    api_key: Optional[str] = None,
) -> list[dict]:
    """Search Semantic Scholar; return raw paper dicts."""
    url = f"{S2_BASE}/paper/search"
    params = urllib.parse.urlencode(
        {
            "query": query,
            "limit": min(limit, 100),
            "fields": "title,abstract,authors,year,externalIds,venue,citationCount,url",
        }
    )
    full_url = f"{url}?{params}"
    headers = {"User-Agent": "FYP-ResearchGapAgent/0.2 (NTU)"}
    if api_key:
        headers["x-api-key"] = api_key
    req = urllib.request.Request(full_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as e:
        logger.warning("S2 search failed for %r: %s", query[:50], e)
        return []
    return data.get("data") or []


def search_all(
    queries: Optional[list[str]] = None,
    limit_per_query: int = 10,
    max_papers: int = 40,
    api_key: Optional[str] = None,
    sleep_s: float = 1.1,
) -> list[dict]:
    """Run multiple queries, dedupe by paperId/DOI, cap at max_papers."""
    queries = queries or DEFAULT_QUERIES
    seen: set[str] = set()
    results: list[dict] = []
    for q in queries:
        if len(results) >= max_papers:
            break
        hits = search(q, limit=limit_per_query, api_key=api_key)
        for h in hits:
            pid = h.get("paperId") or (h.get("externalIds") or {}).get("DOI") or ""
            if not pid or pid in seen:
                continue
            seen.add(pid)
            results.append(h)
            if len(results) >= max_papers:
                break
        time.sleep(sleep_s)
    logger.info("S2: %d unique papers from %d queries", len(results), len(queries))
    return results


def to_paper(p: dict) -> Optional[Paper]:
    """Convert Semantic Scholar paper dict → Paper model."""
    try:
        title = (p.get("title") or "").strip()
        if not title:
            return None
        abstract = (p.get("abstract") or "").strip()
        authors: list[str] = []
        for a in p.get("authors") or []:
            name = (a.get("name") or "").strip()
            if name:
                authors.append(name)
        ex = p.get("externalIds") or {}
        citations = p.get("citationCount")
        if citations is not None:
            try:
                citations = int(citations)
            except (ValueError, TypeError):
                citations = None
        return Paper(
            title=title,
            abstract=abstract,
            authors=authors,
            year=p.get("year"),
            doi=ex.get("DOI"),
            arxiv_id=ex.get("ArXiv"),
            s2_id=p.get("paperId"),
            venue=p.get("venue"),
            url=(p.get("url") or "") or None,
            source="semantic_scholar",
            citation_count=citations,
            keywords=["nucleic_acid_delivery", "lnp", "mrna"],
        )
    except Exception as e:
        logger.debug("Failed to convert S2 paper: %s", e)
        return None


def save_raw(raw: list[dict], path: Path) -> None:
    """Cache raw S2 JSON responses."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(raw, f, indent=2)
    logger.info("Wrote raw S2 cache → %s (%d records)", path, len(raw))
