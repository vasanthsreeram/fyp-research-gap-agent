"""Unpaywall OA PDF resolver — free live full-text PDF harvest by DOI.

No API key required: Unpaywall uses a polite pool keyed by an ``email``
query param (https://unpaywall.org/products/api). This module resolves a DOI
to the best open-access location, prefers a direct PDF URL, and hands the URL
to ``src.ingest.pdf_text.download_pdf`` so PDFs land in ``data/raw/pdfs/``.

This complements Europe PMC (JATS XML, PMC-deposited OA only) by covering
publisher-hosted OA PDFs (MDPI, PLOS, Frontiers, BMC, repositories, ...).
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

from src.models import Paper

logger = logging.getLogger(__name__)

UNPAYWALL_API = "https://api.unpaywall.org/v2"
DEFAULT_MAILTO = "fyp-research-gap-agent@users.noreply.github.com"
USER_AGENT = "FYP-ResearchGapAgent/0.8 (NTU; unpaywall; research use)"


@dataclass
class UnpaywallRecord:
    """Best-effort OA record for one DOI."""

    doi: str
    is_oa: bool = False
    best_url_for_pdf: Optional[str] = None
    best_url_for_landing: Optional[str] = None
    best_host_type: Optional[str] = None  # publisher | repository
    best_version: Optional[str] = None    # submittedVersion | acceptedVersion | publishedVersion
    best_license: Optional[str] = None
    title: str = ""
    year: Optional[int] = None
    journal: str = ""
    n_locations: int = 0
    raw: dict = field(default_factory=dict)


def _normalize_doi(doi: Optional[str]) -> str:
    return (doi or "").strip().lower()


def _request_json(url: str, *, timeout: float = 30.0, max_retries: int = 3) -> dict:
    last_err: Optional[BaseException] = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, json.JSONDecodeError, OSError, TimeoutError) as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise
    if last_err:
        raise last_err
    return {}


def _pick_pdf_url(record: dict) -> tuple[Optional[str], Optional[str]]:
    """Return (best_pdf_url, best_landing_url) from an Unpaywall record dict.

    Preference order:
      1. best_oa_location.url_for_pdf
      2. any oa_location with url_for_pdf (prefer publisher-hosted)
      3. best_oa_location.url_for_landing_page (no direct PDF)
    """
    best = record.get("best_oa_location") or {}
    if isinstance(best, dict) and best.get("url_for_pdf"):
        return best["url_for_pdf"], best.get("url_for_landing_page")

    locations = record.get("oa_locations") or []
    ordered = sorted(
        (loc for loc in locations if isinstance(loc, dict) and loc.get("url_for_pdf")),
        key=lambda loc: 0 if loc.get("host_type") == "publisher" else 1,
    )
    if ordered:
        loc = ordered[0]
        return loc["url_for_pdf"], loc.get("url_for_landing_page")

    if isinstance(best, dict) and best.get("url_for_landing_page"):
        return None, best["url_for_landing_page"]
    return None, None


def _int_or_none(val) -> Optional[int]:
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def lookup(doi: str, *, email: str = DEFAULT_MAILTO) -> Optional[UnpaywallRecord]:
    """Resolve a DOI against Unpaywall v2. None if DOI unknown / not indexed."""
    doi = _normalize_doi(doi)
    if not doi:
        return None
    url = f"{UNPAYWALL_API}/{urllib.parse.quote(doi)}?{urllib.parse.urlencode({'email': email})}"
    try:
        data = _request_json(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.debug("Unpaywall: no record for DOI %s", doi)
            return None
        logger.warning("Unpaywall lookup failed for %s: %s", doi, e)
        return None
    if not data or not data.get("doi"):
        return None

    pdf_url, landing_url = _pick_pdf_url(data)
    best = data.get("best_oa_location") or {}
    if not isinstance(best, dict):
        best = {}
    return UnpaywallRecord(
        doi=data.get("doi") or doi,
        is_oa=bool(data.get("is_oa")),
        best_url_for_pdf=pdf_url,
        best_url_for_landing=landing_url,
        best_host_type=best.get("host_type"),
        best_version=best.get("version"),
        best_license=best.get("license"),
        title=(data.get("title") or "").strip(),
        year=_int_or_none(data.get("year")),
        journal=(data.get("journal_name") or "").strip(),
        n_locations=len(data.get("oa_locations") or []),
        raw=data,
    )


def best_pdf_url(doi: str, *, email: str = DEFAULT_MAILTO) -> Optional[str]:
    """Direct OA PDF URL for a DOI, or None (no OA / no direct PDF)."""
    rec = lookup(doi, email=email)
    if rec is None or not rec.is_oa:
        return None
    return rec.best_url_for_pdf


def resolve_pdf_url_for_paper(paper: Paper, *, email: str = DEFAULT_MAILTO) -> Optional[str]:
    """Best-effort Unpaywall PDF URL for a Paper (DOI preferred)."""
    if not paper.doi:
        return None
    try:
        return best_pdf_url(paper.doi, email=email)
    except Exception as e:
        logger.warning("Unpaywall resolve failed for %s: %s", paper.doi, e)
        return None


def unpaywall_status(*, email: str = DEFAULT_MAILTO, sample_doi: str = "10.1371/journal.pbio.3002278") -> dict:
    """Lightweight connectivity probe (no key needed; one lookup)."""
    status = {
        "ok": False,
        "endpoint": f"{UNPAYWALL_API}/{{doi}}?email=...",
        "mailto": email,
        "sample_doi": sample_doi,
        "is_oa": None,
        "pdf_url": None,
        "error": None,
    }
    try:
        rec = lookup(sample_doi, email=email)
        if rec is not None:
            status["ok"] = True
            status["is_oa"] = rec.is_oa
            status["pdf_url"] = rec.best_url_for_pdf
            status["title"] = rec.title[:120]
            if not rec.is_oa:
                status["error"] = "sample DOI not OA (API reachable)"
        else:
            status["error"] = "no record for sample DOI (API reachable?)"
    except Exception as e:
        status["error"] = f"{type(e).__name__}: {e}"
    return status
