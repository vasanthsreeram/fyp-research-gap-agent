"""Europe PMC open-access full-text client (bulk OA path).

Free REST API — no key required. Resolves DOI → PMCID → fullTextXML for the
open-access subset, then converts JATS XML body into plain IMRaD-ish text
for quote-grounded extract/argue.

Docs: https://europepmc.org/RestfulWebService
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional

from src.models import Paper

logger = logging.getLogger(__name__)

EUROPE_PMC_REST = "https://www.ebi.ac.uk/europepmc/webservices/rest"
USER_AGENT = "FYP-ResearchGapAgent/0.7 (NTU; europe-pmc; research use)"
DEFAULT_MAILTO = "fyp-research-gap-agent@users.noreply.github.com"

# Drop non-body back-matter sections from plain text
_SKIP_SEC_TITLE_RE = re.compile(
    r"^(references|acknowledg|author\s+contributions|funding|competing|"
    r"conflict\s+of\s+interest|data\s+availability|supplementary\s+material|"
    r"supporting\s+information|ethics|abbreviations)\b",
    re.IGNORECASE,
)


@dataclass
class EuropePMCHit:
    doi: Optional[str] = None
    pmcid: Optional[str] = None
    pmid: Optional[str] = None
    title: str = ""
    is_open_access: bool = False
    has_pdf: bool = False
    journal: str = ""
    year: Optional[int] = None
    raw: dict = field(default_factory=dict)


@dataclass
class EuropePMCFullText:
    pmcid: str
    text: str
    source: str = "europe_pmc"
    n_sections: int = 0
    doi: Optional[str] = None
    title: str = ""


def _local(tag: str) -> str:
    return tag.split("}")[-1] if tag else ""


def _request_json(url: str, *, timeout: float = 30.0, max_retries: int = 3) -> dict:
    last_err: Optional[Exception] = None
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
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise
    if last_err:
        raise last_err
    return {}


def _request_bytes(url: str, *, timeout: float = 45.0, max_retries: int = 3) -> bytes:
    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise
    if last_err:
        raise last_err
    return b""


def _truthy(val) -> bool:
    if isinstance(val, bool):
        return val
    s = str(val or "").strip().upper()
    return s in {"Y", "YES", "TRUE", "1"}


def search_by_doi(doi: str, *, page_size: int = 3) -> Optional[EuropePMCHit]:
    """Resolve a DOI to a Europe PMC core result (prefer OA full text)."""
    doi = (doi or "").strip()
    if not doi:
        return None
    # Europe PMC query syntax
    q = f'DOI:"{doi}"'
    params = urllib.parse.urlencode(
        {
            "query": q,
            "format": "json",
            "resultType": "core",
            "pageSize": str(page_size),
            "email": DEFAULT_MAILTO,
        }
    )
    url = f"{EUROPE_PMC_REST}/search?{params}"
    data = _request_json(url)
    results = (data.get("resultList") or {}).get("result") or []
    if not results:
        # Fallback without quotes
        params = urllib.parse.urlencode(
            {
                "query": f"DOI:{doi}",
                "format": "json",
                "resultType": "core",
                "pageSize": str(page_size),
                "email": DEFAULT_MAILTO,
            }
        )
        data = _request_json(f"{EUROPE_PMC_REST}/search?{params}")
        results = (data.get("resultList") or {}).get("result") or []
    if not results:
        return None

    # Prefer open-access with PMCID
    def rank(r: dict) -> tuple:
        oa = 1 if _truthy(r.get("isOpenAccess")) else 0
        pmc = 1 if r.get("pmcid") else 0
        return (oa, pmc)

    best = sorted(results, key=rank, reverse=True)[0]
    year = best.get("pubYear")
    try:
        year_i = int(year) if year is not None else None
    except (TypeError, ValueError):
        year_i = None
    return EuropePMCHit(
        doi=best.get("doi") or doi,
        pmcid=best.get("pmcid"),
        pmid=str(best.get("pmid")) if best.get("pmid") else None,
        title=(best.get("title") or "").strip(),
        is_open_access=_truthy(best.get("isOpenAccess")),
        has_pdf=_truthy(best.get("hasPDF")),
        journal=(best.get("journalTitle") or "").strip(),
        year=year_i,
        raw=best,
    )


def fetch_fulltext_xml(pmcid: str, *, timeout: float = 45.0) -> str:
    """Fetch JATS fullTextXML for a PMCID (e.g. PMC7745181)."""
    pmcid = (pmcid or "").strip().upper()
    if not pmcid:
        raise ValueError("empty pmcid")
    if not pmcid.startswith("PMC"):
        pmcid = f"PMC{pmcid}"
    url = f"{EUROPE_PMC_REST}/{pmcid}/fullTextXML"
    data = _request_bytes(url, timeout=timeout)
    return data.decode("utf-8", errors="replace")


def _element_text(el: ET.Element) -> str:
    parts: list[str] = []
    if el.text:
        parts.append(el.text)
    for child in el:
        ln = _local(child.tag)
        if ln in {"table-wrap", "fig", "supplementary-material", "inline-formula", "disp-formula"}:
            # Keep captions only
            for cap in child.iter():
                if _local(cap.tag) == "caption":
                    parts.append(" ".join("".join(cap.itertext()).split()))
            if child.tail:
                parts.append(child.tail)
            continue
        if ln in {"ref-list", "fn-group", "ack"}:
            if child.tail:
                parts.append(child.tail)
            continue
        parts.append(_element_text(child))
        if child.tail:
            parts.append(child.tail)
    return " ".join(p for p in parts if p and p.strip())


def _normalize_plain(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def jats_xml_to_plain(xml_text: str, *, max_chars: int = 120_000) -> tuple[str, int]:
    """Convert Europe PMC / JATS fullTextXML into plain text with section headings.

    Returns (plain_text, n_sections_emitted).
    """
    if not (xml_text or "").strip():
        return "", 0
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning("JATS parse failed: %s", e)
        # crude strip tags fallback
        crude = re.sub(r"<[^>]+>", " ", xml_text)
        crude = _normalize_plain(crude)
        return crude[:max_chars], 0

    chunks: list[str] = []
    n_sec = 0

    # Abstract (front matter) — helpful when body is methods-heavy
    for abs_el in root.iter():
        if _local(abs_el.tag) == "abstract":
            abs_txt = _normalize_plain(_element_text(abs_el))
            if abs_txt and len(abs_txt) > 40:
                chunks.append("Abstract")
                chunks.append(abs_txt)
                n_sec += 1
            break

    body = None
    for el in root.iter():
        if _local(el.tag) == "body":
            body = el
            break

    def walk_sec(sec: ET.Element, depth: int = 0) -> None:
        nonlocal n_sec
        title = ""
        paras: list[str] = []
        child_secs: list[ET.Element] = []
        for child in sec:
            ln = _local(child.tag)
            if ln == "title" and not title:
                title = _normalize_plain("".join(child.itertext()))
            elif ln == "sec":
                child_secs.append(child)
            elif ln == "p":
                t = _normalize_plain(_element_text(child))
                if t:
                    paras.append(t)
            elif ln in {"list", "disp-quote", "boxed-text"}:
                t = _normalize_plain(_element_text(child))
                if t:
                    paras.append(t)

        if title and _SKIP_SEC_TITLE_RE.match(title):
            return

        if title and (paras or child_secs):
            # Promote common aliases to IMRaD headings our splitter knows
            heading = title
            low = title.lower()
            if depth == 0:
                if "method" in low or "material" in low or "experimental" in low:
                    heading = "Methods"
                elif low.startswith("result") or "results and discussion" in low:
                    heading = "Results"
                elif "discussion" in low and "result" not in low:
                    heading = "Discussion"
                elif "conclusion" in low or low in {"summary", "concluding remarks"}:
                    heading = "Conclusions"
                elif "introduction" in low or low == "background":
                    heading = "Introduction"
                elif "limitation" in low:
                    heading = "Limitations"
            chunks.append(heading)
            n_sec += 1
        for p in paras:
            chunks.append(p)
        for cs in child_secs:
            walk_sec(cs, depth + 1)

    if body is not None:
        # Top-level mix of sec and p
        top_paras: list[str] = []
        for child in body:
            ln = _local(child.tag)
            if ln == "sec":
                if top_paras:
                    chunks.extend(top_paras)
                    top_paras = []
                walk_sec(child, 0)
            elif ln == "p":
                t = _normalize_plain(_element_text(child))
                if t:
                    top_paras.append(t)
        if top_paras:
            # Orphan body paragraphs (some PMC articles lack nested <sec>)
            heading = "Introduction"
            if any(c == "Introduction" for c in chunks):
                heading = "Results"
            chunks.append(heading)
            n_sec += 1
            chunks.extend(top_paras)
    else:
        # No body — fall back to all paragraph text
        paras = []
        for el in root.iter():
            if _local(el.tag) == "p":
                t = _normalize_plain(_element_text(el))
                if t and len(t) > 40:
                    paras.append(t)
        chunks.extend(paras[:80])

    plain = _normalize_plain("\n\n".join(chunks))
    if len(plain) > max_chars:
        plain = plain[:max_chars].rsplit("\n", 1)[0].strip()
    return plain, n_sec


def fetch_fulltext_by_doi(
    doi: str,
    *,
    require_oa: bool = True,
    min_chars: int = 400,
) -> Optional[EuropePMCFullText]:
    """DOI → Europe PMC OA full text (plain). None if unavailable."""
    hit = search_by_doi(doi)
    if not hit or not hit.pmcid:
        return None
    if require_oa and not hit.is_open_access:
        # Still try — some records mis-flag; fullTextXML 404s cleanly
        logger.debug("Europe PMC hit for %s not flagged OA (pmcid=%s); trying XML anyway", doi, hit.pmcid)
    try:
        xml_text = fetch_fulltext_xml(hit.pmcid)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.debug("No fullTextXML for %s (%s)", hit.pmcid, doi)
            return None
        raise
    plain, n_sec = jats_xml_to_plain(xml_text)
    if len(plain) < min_chars:
        return None
    return EuropePMCFullText(
        pmcid=hit.pmcid,
        text=plain,
        source="europe_pmc",
        n_sections=n_sec,
        doi=hit.doi or doi,
        title=hit.title,
    )


def fetch_fulltext_for_paper(
    paper: Paper,
    *,
    require_oa: bool = True,
    min_chars: int = 400,
) -> Optional[EuropePMCFullText]:
    """Best-effort Europe PMC full text for a Paper (DOI preferred)."""
    if paper.doi:
        try:
            return fetch_fulltext_by_doi(paper.doi, require_oa=require_oa, min_chars=min_chars)
        except Exception as e:
            logger.warning("Europe PMC fetch failed for DOI %s: %s", paper.doi, e)
            return None
    return None


def europe_pmc_status() -> dict:
    """Lightweight connectivity probe (no key needed)."""
    status = {
        "ok": False,
        "endpoint": EUROPE_PMC_REST,
        "sample_doi": "10.1056/NEJMoa2034577",
        "pmcid": None,
        "is_open_access": None,
        "error": None,
    }
    try:
        hit = search_by_doi(status["sample_doi"])
        if hit:
            status["ok"] = True
            status["pmcid"] = hit.pmcid
            status["is_open_access"] = hit.is_open_access
            status["title"] = hit.title[:120]
        else:
            status["error"] = "no hit for sample DOI"
    except Exception as e:
        status["error"] = f"{type(e).__name__}: {e}"
    return status
