"""arXiv API helper for nucleic-acid / LNP / mRNA delivery preprints."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from src.models import Paper

logger = logging.getLogger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

DEFAULT_QUERY = (
    '(all:"lipid nanoparticle" OR all:LNP OR all:"mRNA delivery" '
    'OR all:"nucleic acid delivery" OR all:"ionizable lipid")'
)


def search(
    query: str = DEFAULT_QUERY,
    max_results: int = 15,
) -> list[dict]:
    """
    Query arXiv Atom API. Returns list of raw entry dicts
    (title, abstract, authors, arxiv_id, year, url, doi).
    """
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": min(max_results, 50),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    )
    url = f"{ARXIV_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "FYP-ResearchGapAgent/0.2 (NTU)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        logger.warning("arXiv search failed: %s", e)
        return []

    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        logger.warning("arXiv XML parse failed: %s", e)
        return []

    entries: list[dict] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title_el = entry.find("atom:title", ATOM_NS)
        summary_el = entry.find("atom:summary", ATOM_NS)
        id_el = entry.find("atom:id", ATOM_NS)
        published_el = entry.find("atom:published", ATOM_NS)

        title = re.sub(r"\s+", " ", (title_el.text or "").strip()) if title_el is not None else ""
        abstract = re.sub(r"\s+", " ", (summary_el.text or "").strip()) if summary_el is not None else ""
        arxiv_url = (id_el.text or "").strip() if id_el is not None else ""
        arxiv_id = arxiv_url.rsplit("/abs/", 1)[-1] if "/abs/" in arxiv_url else ""
        year = None
        if published_el is not None and published_el.text:
            try:
                year = int(published_el.text[:4])
            except ValueError:
                year = None

        authors: list[str] = []
        for a in entry.findall("atom:author", ATOM_NS):
            name_el = a.find("atom:name", ATOM_NS)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        doi = None
        for link in entry.findall("atom:link", ATOM_NS):
            if link.attrib.get("title") == "doi":
                doi = link.attrib.get("href", "").replace("http://dx.doi.org/", "").replace(
                    "https://doi.org/", ""
                )
                break

        if title:
            entries.append(
                {
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "year": year,
                    "arxiv_id": arxiv_id,
                    "url": arxiv_url or None,
                    "doi": doi,
                    "venue": "arXiv",
                    "source": "arxiv",
                }
            )

    logger.info("arXiv: %d entries", len(entries))
    return entries


def to_paper(d: dict) -> Optional[Paper]:
    """Convert arXiv entry dict → Paper."""
    try:
        title = (d.get("title") or "").strip()
        if not title:
            return None
        return Paper(
            title=title,
            abstract=(d.get("abstract") or "").strip(),
            authors=list(d.get("authors") or []),
            year=d.get("year"),
            doi=d.get("doi"),
            arxiv_id=d.get("arxiv_id"),
            venue=d.get("venue") or "arXiv",
            url=d.get("url"),
            source="arxiv",
            keywords=["nucleic_acid_delivery", "lnp", "mrna", "preprint"],
        )
    except Exception as e:
        logger.debug("Failed to convert arXiv entry: %s", e)
        return None


def save_raw(raw: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(raw, f, indent=2)
    logger.info("Wrote raw arXiv cache → %s (%d records)", path, len(raw))
