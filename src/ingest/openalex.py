"""OpenAlex Works API client — free live ingest without Semantic Scholar key.

Polite pool: include mailto in User-Agent / query per OpenAlex guidance.
Docs: https://docs.openalex.org/
"""

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

OPENALEX_BASE = "https://api.openalex.org"
# Contact for polite pool (no personal email committed)
DEFAULT_MAILTO = "fyp-research-gap-agent@users.noreply.github.com"
USER_AGENT = f"FYP-ResearchGapAgent/0.5 (NTU; mailto:{DEFAULT_MAILTO})"

# Aligned with S2 domain pack (LNP core / hybrid ncRNA / gene editing)
DEFAULT_QUERIES = [
    "lipid nanoparticle mRNA delivery",
    "ionizable lipid nanoparticle endosomal escape",
    "extrahepatic targeting lipid nanoparticles",
    "mRNA LNP protein corona biodistribution",
    "siRNA lipid nanoparticle non-hepatic delivery",
    "bifunctional noncoding RNA nanoparticle",
    "circular RNA LNP therapeutics delivery",
    "hybrid mRNA siRNA co-delivery",
    "CRISPR Cas9 lipid nanoparticle in vivo",
    "base editing non-viral delivery LNP",
]


def _year_from_work(w: dict) -> Optional[int]:
    y = w.get("publication_year")
    if isinstance(y, int):
        return y
    if isinstance(y, str) and y.isdigit():
        return int(y)
    return None


def _abstract_from_inverted(inv: Optional[dict]) -> str:
    """Reconstruct abstract text from OpenAlex inverted index."""
    if not inv or not isinstance(inv, dict):
        return ""
    # positions → token
    max_pos = -1
    for positions in inv.values():
        if positions:
            max_pos = max(max_pos, max(positions))
    if max_pos < 0:
        return ""
    tokens: list[str] = [""] * (max_pos + 1)
    for word, positions in inv.items():
        for pos in positions:
            if 0 <= pos <= max_pos:
                tokens[pos] = word
    return " ".join(t for t in tokens if t).strip()


def search(
    query: str,
    *,
    limit: int = 20,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    mailto: str = DEFAULT_MAILTO,
    max_retries: int = 3,
    backoff_s: float = 1.5,
) -> list[dict]:
    """Search OpenAlex works; return raw work dicts."""
    filters: list[str] = ["has_abstract:true"]
    if year_min is not None:
        filters.append(f"from_publication_date:{year_min}-01-01")
    if year_max is not None:
        filters.append(f"to_publication_date:{year_max}-12-31")

    params = {
        "search": query,
        "per_page": min(max(1, limit), 50),
        "filter": ",".join(filters),
        "mailto": mailto,
        "select": (
            "id,doi,title,display_name,authorships,publication_year,"
            "primary_location,abstract_inverted_index,cited_by_count,type"
        ),
    }
    url = f"{OPENALEX_BASE}/works?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    last_err: Optional[BaseException] = None
    for attempt in range(max_retries + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            return data.get("results") or []
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                sleep_for = backoff_s * (2**attempt)
                logger.warning(
                    "OpenAlex HTTP %s for %r — retry %d/%d in %.1fs",
                    e.code,
                    query[:50],
                    attempt + 1,
                    max_retries,
                    sleep_for,
                )
                time.sleep(sleep_for)
                continue
            logger.warning("OpenAlex search failed for %r: %s", query[:50], e)
            return []
        except (urllib.error.URLError, json.JSONDecodeError, OSError, TimeoutError) as e:
            last_err = e
            if attempt < max_retries:
                sleep_for = backoff_s * (2**attempt)
                logger.warning(
                    "OpenAlex error for %r (%s) — retry %d/%d in %.1fs",
                    query[:50],
                    e,
                    attempt + 1,
                    max_retries,
                    sleep_for,
                )
                time.sleep(sleep_for)
                continue
            logger.warning("OpenAlex search failed for %r: %s", query[:50], e)
            return []
    logger.warning("OpenAlex exhausted retries for %r: %s", query[:50], last_err)
    return []


def search_all(
    queries: Optional[list[str]] = None,
    *,
    limit_per_query: int = 10,
    max_papers: int = 40,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    sleep_s: float = 0.35,
    mailto: str = DEFAULT_MAILTO,
) -> list[dict]:
    """Run multiple domain queries; dedupe by OpenAlex id / DOI."""
    queries = queries or DEFAULT_QUERIES
    seen: set[str] = set()
    results: list[dict] = []
    for q in queries:
        if len(results) >= max_papers:
            break
        hits = search(
            q,
            limit=limit_per_query,
            year_min=year_min,
            year_max=year_max,
            mailto=mailto,
        )
        for h in hits:
            oid = (h.get("id") or "").strip()
            doi = (h.get("doi") or "").strip().lower()
            keys = [k for k in (oid, doi) if k]
            if not keys:
                title = (h.get("title") or h.get("display_name") or "").strip().lower()
                if not title or title in seen:
                    continue
                keys = [f"title:{title}"]
            if any(k in seen for k in keys):
                continue
            y = _year_from_work(h)
            if year_min is not None and y is not None and y < year_min:
                continue
            if year_max is not None and y is not None and y > year_max:
                continue
            # Prefer works with reconstructable abstracts
            if not h.get("abstract_inverted_index") and not h.get("abstract"):
                continue
            for k in keys:
                seen.add(k)
            results.append(h)
            if len(results) >= max_papers:
                break
        time.sleep(sleep_s)
    logger.info(
        "OpenAlex: %d unique works from %d queries (year_min=%s year_max=%s)",
        len(results),
        len(queries),
        year_min,
        year_max,
    )
    return results


def to_paper(w: dict) -> Optional[Paper]:
    """Convert OpenAlex work dict → Paper model."""
    try:
        title = (w.get("title") or w.get("display_name") or "").strip()
        if not title:
            return None
        abstract = ""
        if isinstance(w.get("abstract"), str):
            abstract = w["abstract"].strip()
        if not abstract:
            abstract = _abstract_from_inverted(w.get("abstract_inverted_index"))
        if not abstract:
            return None

        authors: list[str] = []
        for a in w.get("authorships") or []:
            author = a.get("author") or {}
            name = (author.get("display_name") or "").strip()
            if name:
                authors.append(name)

        doi_raw = (w.get("doi") or "").strip()
        doi = None
        if doi_raw:
            doi = doi_raw.replace("https://doi.org/", "").replace("http://doi.org/", "")

        venue = None
        url = None
        loc = w.get("primary_location") or {}
        src = loc.get("source") or {}
        if isinstance(src, dict):
            venue = (src.get("display_name") or None) or None
        url = loc.get("landing_page_url") or (f"https://doi.org/{doi}" if doi else None)
        if not url and w.get("id"):
            url = w["id"]

        citations = w.get("cited_by_count")
        try:
            citations = int(citations) if citations is not None else None
        except (TypeError, ValueError):
            citations = None

        oa_id = (w.get("id") or "").rstrip("/").split("/")[-1] or None

        return Paper(
            title=title,
            abstract=abstract,
            authors=authors,
            year=_year_from_work(w),
            doi=doi,
            arxiv_id=None,
            s2_id=None,
            venue=venue,
            url=url,
            source="openalex",
            citation_count=citations,
            keywords=["nucleic_acid_delivery", "openalex", oa_id or ""],
        )
    except Exception as e:
        logger.debug("Failed to convert OpenAlex work: %s", e)
        return None


def save_raw(raw: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(raw, f, indent=2)
    logger.info("Wrote raw OpenAlex cache → %s (%d records)", path, len(raw))


def openalex_status(*, probe: bool = False) -> dict:
    """Lightweight status for CLI (optional network probe)."""
    st = {
        "endpoint": f"{OPENALEX_BASE}/works",
        "mailto": DEFAULT_MAILTO,
        "reachable": None,
        "sample_count": None,
        "hint": "No API key required. Uses polite pool via mailto.",
    }
    if not probe:
        return st
    try:
        hits = search("lipid nanoparticle mRNA", limit=1)
        st["reachable"] = True
        st["sample_count"] = len(hits)
    except Exception as e:
        st["reachable"] = False
        st["hint"] = f"Probe failed: {e}"
    return st
