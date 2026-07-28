"""Paper ingestion: Semantic Scholar + arXiv APIs with local cache fallback."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import urllib.parse
import urllib.request
import urllib.error

from src.models import Paper

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

FIXTURE_FILE = Path(__file__).resolve().parent / "fixtures" / "papers_fixture.jsonl"
S2_BASE = "https://api.semanticscholar.org/graph/v1"

# Core query: nucleic acid / LNP / mRNA delivery — the supervisor's domain slice
DEFAULT_QUERIES = [
    "nucleic acid delivery lipid nanoparticle mRNA vaccine",
    "LNP ionizable lipid structure activity delivery",
    "mRNA delivery extrahepatic targeting nanoparticles",
    "LNPs endosomal escape mechanism nucleic acid",
    "LNPs targeted delivery extrahepatic siRNA mRNA",
    "tissue specific lipid nanoparticles gene therapy",
    "lipid nanoparticles delivery efficiency determinants",
    "endosomal escape lipid nanoparticles delivery",
    "LNPs mRNA COVID beyond vaccine applications",
    "non-viral delivery nucleic acid therapeutics",
]


def _s2_search(query: str, limit: int = 20) -> list[dict]:
    """Search Semantic Scholar and return paper dicts."""
    url = f"{S2_BASE}/paper/search"
    params = urllib.parse.urlencode({
        "query": query,
        "limit": min(limit, 100),
        "fields": "title,abstract,authors,year,externalIds,venue,citationCount,url",
    })
    full_url = f"{url}?{params}"
    req = urllib.request.Request(full_url, headers={"User-Agent": "FYP-ResearchGapAgent/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as e:
        logger.warning("S2 search failed for %r: %s", query[:40], e)
        return []
    return data.get("data", [])


def _s2_search_all(limit_per_query: int = 20) -> list[dict]:
    """Run all queries, deduplicate by paperId."""
    seen: set[str] = set()
    results: list[dict] = []
    for q in DEFAULT_QUERIES:
        hits = _s2_search(q, limit=limit_per_query)
        for h in hits:
            pid = h.get("paperId") or h.get("externalIds", {}).get("DOI", "")
            if pid and pid not in seen:
                seen.add(pid)
                results.append(h)
        time.sleep(1.0)  # polite rate-limit
    logger.info("S2: got %d unique papers from %d queries", len(results), len(DEFAULT_QUERIES))
    return results


def s2_to_paper(p: dict) -> Optional[Paper]:
    """Convert Semantic Scholar paper dict → Paper model."""
    try:
        title = (p.get("title") or "").strip()
        if not title:
            return None
        abstract = (p.get("abstract") or "").strip()
        authors = []
        for a in (p.get("authors") or []):
            name = a.get("name") or ""
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
            url=(p.get("url") or ""),
            source="semantic_scholar",
            citation_count=citations,
        )
    except Exception as e:
        logger.debug("Failed to convert S2 paper: %s", e)
        return None


def load_fixture() -> list[Paper]:
    """Load bundled fixture papers (always works, no network)."""
    if not FIXTURE_FILE.exists():
        logger.warning("No fixture file at %s", FIXTURE_FILE)
        return []
    papers: list[Paper] = []
    with open(FIXTURE_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    d = json.loads(line)
                    papers.append(Paper(**d))
                except Exception as e:
                    logger.debug("Skipping fixture line: %s", e)
    logger.info("Loaded %d papers from fixture", len(papers))
    return papers


def ingest_papers(use_fixture: bool = False, save: bool = True) -> list[Paper]:
    """Ingest pipeline: try S2, fall back to fixture."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if use_fixture:
        papers = load_fixture()
    else:
        raw = _s2_search_all(limit_per_query=20)
        papers: list[Paper] = []
        for p in raw:
            m = s2_to_paper(p)
            if m:
                papers.append(m)
        if not papers:
            logger.warning("S2 returned 0 papers; falling back to fixtures")
            papers = load_fixture()

    if save and papers:
        out_path = PROCESSED_DIR / "papers.jsonl"
        with open(out_path, "w") as f:
            for p in papers:
                f.write(p.model_dump_json() + "\n")
        logger.info("Saved %d papers to %s", len(papers), out_path)

    return papers
