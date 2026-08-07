"""Full-text PDF depth: extract, section-split, attach to Paper objects.

Offline-first: fixture full-text JSONL ships with the repo so demos never
depend on live PDF download. Optional live path resolves arXiv PDF URLs
and downloads into data/raw/pdfs/ (gitignored).
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.models import Paper, PaperSection, PaperSectionKind

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data"
RAW_PDF_DIR = DATA_DIR / "raw" / "pdfs"
FIXTURE_FULLTEXT = (
    Path(__file__).resolve().parent.parent / "fixtures" / "fulltext_fixture.jsonl"
)

USER_AGENT = "FYP-ResearchGapAgent/0.6 (NTU; fulltext; research use)"

# Heading patterns → section kind (order matters: first match wins per line)
_SECTION_HEADING_RE = re.compile(
    r"^\s*(?:"
    r"(?P<abstract>abstract)\b|"
    r"(?P<intro>(?:\d+[\.\)]\s*)?(?:introduction|background))\b|"
    r"(?P<methods>(?:\d+[\.\)]\s*)?(?:materials?\s+and\s+methods|methods?|experimental(?:\s+section)?|experimental\s+procedures))\b|"
    r"(?P<results>(?:\d+[\.\)]\s*)?(?:results?(?:\s+and\s+discussion)?))\b|"
    r"(?P<discussion>(?:\d+[\.\)]\s*)?(?:discussion))\b|"
    r"(?P<conclusion>(?:\d+[\.\)]\s*)?(?:conclusions?|summary|concluding\s+remarks))\b|"
    r"(?P<limitations>(?:\d+[\.\)]\s*)?(?:limitations?|caveats?|study\s+limitations))\b|"
    r"(?P<sup>(?:\d+[\.\)]\s*)?(?:supplementary(?:\s+information)?|supporting\s+information|appendix))\b"
    r")\s*:?\s*$",
    re.IGNORECASE,
)

_KIND_FROM_GROUP = {
    "abstract": PaperSectionKind.ABSTRACT,
    "intro": PaperSectionKind.INTRODUCTION,
    "methods": PaperSectionKind.METHODS,
    "results": PaperSectionKind.RESULTS,
    "discussion": PaperSectionKind.DISCUSSION,
    "conclusion": PaperSectionKind.CONCLUSION,
    "limitations": PaperSectionKind.LIMITATIONS,
    "sup": PaperSectionKind.SUPPLEMENTARY,
}


@dataclass
class FullTextAttachStats:
    n_input: int = 0
    n_attached: int = 0
    n_from_fixture: int = 0
    n_from_pdf: int = 0
    n_from_download: int = 0
    n_from_europe_pmc: int = 0
    n_failed: int = 0
    sources: dict[str, int] = field(default_factory=dict)
    attached_ids: list[str] = field(default_factory=list)

    def bump_source(self, src: str) -> None:
        self.sources[src] = self.sources.get(src, 0) + 1


def extract_text_from_pdf(path: Path | str, *, max_pages: int = 40) -> str:
    """Extract plain text from a PDF via PyMuPDF, with pdfplumber fallback."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    text = _extract_pymupdf(path, max_pages=max_pages)
    if text and len(text.strip()) > 80:
        return _normalize_whitespace(text)
    text2 = _extract_pdfplumber(path, max_pages=max_pages)
    if text2 and len(text2.strip()) > 80:
        return _normalize_whitespace(text2)
    return _normalize_whitespace(text or text2 or "")


def _extract_pymupdf(path: Path, *, max_pages: int) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.debug("PyMuPDF not installed")
        return ""
    try:
        doc = fitz.open(path)
    except Exception as e:
        logger.warning("PyMuPDF open failed for %s: %s", path, e)
        return ""
    parts: list[str] = []
    try:
        n = min(len(doc), max_pages)
        for i in range(n):
            page = doc.load_page(i)
            parts.append(page.get_text("text") or "")
    finally:
        doc.close()
    return "\n".join(parts)


def _extract_pdfplumber(path: Path, *, max_pages: int) -> str:
    try:
        import pdfplumber
    except ImportError:
        logger.debug("pdfplumber not installed")
        return ""
    parts: list[str] = []
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= max_pages:
                    break
                parts.append(page.extract_text() or "")
    except Exception as e:
        logger.warning("pdfplumber failed for %s: %s", path, e)
        return ""
    return "\n".join(parts)


def _normalize_whitespace(text: str) -> str:
    # Keep paragraph breaks; collapse runaway spaces / form feeds
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_sections(text: str) -> list[PaperSection]:
    """Heuristic IMRaD section split from plain full text.

    Looks for common heading lines. If no headings found, returns a single
    OTHER section covering the whole body.
    """
    if not (text or "").strip():
        return []

    lines = text.split("\n")
    # Collect (line_index, kind, heading_title)
    hits: list[tuple[int, PaperSectionKind, str]] = []
    for i, line in enumerate(lines):
        m = _SECTION_HEADING_RE.match(line.strip())
        if not m:
            continue
        kind = PaperSectionKind.OTHER
        for gname, k in _KIND_FROM_GROUP.items():
            if m.group(gname):
                kind = k
                break
        hits.append((i, kind, line.strip()))

    if not hits:
        body = text.strip()
        return [
            PaperSection(
                kind=PaperSectionKind.OTHER,
                title="",
                text=body,
                start_char=0,
                end_char=len(body),
            )
        ]

    # Build char offsets via cumulative line lengths (+ newlines)
    line_starts: list[int] = []
    pos = 0
    for ln in lines:
        line_starts.append(pos)
        pos += len(ln) + 1  # + newline

    sections: list[PaperSection] = []
    # Preamble before first heading
    first_i = hits[0][0]
    if first_i > 0:
        pre = "\n".join(lines[:first_i]).strip()
        if pre:
            start = 0
            end = line_starts[first_i] if first_i < len(line_starts) else len(text)
            sections.append(
                PaperSection(
                    kind=PaperSectionKind.OTHER,
                    title="",
                    text=pre,
                    start_char=start,
                    end_char=min(end, len(text)),
                )
            )

    for hi, (line_i, kind, heading) in enumerate(hits):
        start_line = line_i + 1  # content after heading
        end_line = hits[hi + 1][0] if hi + 1 < len(hits) else len(lines)
        chunk_lines = lines[start_line:end_line]
        chunk = "\n".join(chunk_lines).strip()
        if not chunk:
            continue
        start_char = line_starts[start_line] if start_line < len(line_starts) else 0
        if end_line < len(line_starts):
            end_char = line_starts[end_line]
        else:
            end_char = len(text)
        sections.append(
            PaperSection(
                kind=kind,
                title=heading,
                text=chunk,
                start_char=start_char,
                end_char=min(end_char, len(text)),
            )
        )
    return sections


def arxiv_pdf_url(arxiv_id: str) -> str:
    aid = (arxiv_id or "").strip()
    # Strip version suffix optionally kept
    aid = aid.replace("arxiv:", "").replace("https://arxiv.org/abs/", "")
    aid = aid.replace("http://arxiv.org/abs/", "").strip()
    return f"https://arxiv.org/pdf/{aid}.pdf"


def resolve_pdf_url(paper: Paper) -> Optional[str]:
    """Best-effort PDF URL from paper metadata (arXiv first)."""
    if paper.pdf_url:
        return paper.pdf_url
    if paper.arxiv_id:
        return arxiv_pdf_url(paper.arxiv_id)
    url = (paper.url or "").strip()
    if not url:
        return None
    if "arxiv.org/abs/" in url:
        aid = url.rsplit("/abs/", 1)[-1]
        return arxiv_pdf_url(aid)
    if url.lower().endswith(".pdf"):
        return url
    return None


def download_pdf(
    url: str,
    dest: Path,
    *,
    timeout: float = 45.0,
) -> Path:
    """Download a PDF to dest. Raises on failure."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    if len(data) < 500 or not data[:5].startswith(b"%PDF"):
        # Some servers return HTML interstitial
        raise ValueError(f"Not a PDF response from {url} ({len(data)} bytes)")
    dest.write_bytes(data)
    return dest


def load_fulltext_fixture(path: Optional[Path] = None) -> list[dict]:
    """Load offline full-text records (title/doi/arxiv keyed)."""
    fixture = path or FIXTURE_FULLTEXT
    if not fixture.exists():
        return []
    rows: list[dict] = []
    with open(fixture) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.debug("Bad fulltext fixture line: %s", e)
    return rows


def _norm_title(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").lower()).strip()


def _fixture_index(rows: list[dict]) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for r in rows:
        if r.get("title"):
            idx[f"title:{_norm_title(r['title'])}"] = r
        if r.get("doi"):
            idx[f"doi:{str(r['doi']).lower()}"] = r
        if r.get("arxiv_id"):
            idx[f"arxiv:{str(r['arxiv_id']).lower()}"] = r
        if r.get("paper_id"):
            idx[f"id:{r['paper_id']}"] = r
    return idx


def match_fulltext_fixture(paper: Paper, index: dict[str, dict]) -> Optional[dict]:
    keys = []
    if paper.doi:
        keys.append(f"doi:{paper.doi.lower()}")
    if paper.arxiv_id:
        keys.append(f"arxiv:{paper.arxiv_id.lower()}")
    keys.append(f"id:{paper.id}")
    keys.append(f"title:{_norm_title(paper.title)}")
    for k in keys:
        if k in index:
            return index[k]
    return None


def attach_full_text(
    paper: Paper,
    text: str,
    *,
    source: str = "manual",
    pdf_path: Optional[str] = None,
    pdf_url: Optional[str] = None,
    split: bool = True,
) -> Paper:
    """Mutate + return paper with full_text + sections attached."""
    body = _normalize_whitespace(text or "")
    if not body:
        return paper
    paper.full_text = body
    paper.full_text_source = source
    if pdf_path:
        paper.pdf_path = str(pdf_path)
    if pdf_url:
        paper.pdf_url = pdf_url
    if split:
        paper.sections = split_sections(body)
    return paper


def attach_fulltext_to_papers(
    papers: list[Paper],
    *,
    use_fixture: bool = True,
    download: bool = False,
    europe_pmc: bool = False,
    pdf_dir: Optional[Path] = None,
    max_attach: Optional[int] = None,
    skip_existing: bool = True,
    fixture_path: Optional[Path] = None,
) -> tuple[list[Paper], FullTextAttachStats]:
    """Attach full text where possible (fixture → local PDF → Europe PMC → PDF URL).

    Returns (papers, stats). Papers list is the same objects (mutated in place).

    ``europe_pmc=True`` enables live DOI→PMC OA fullTextXML (no API key).
    ``download=True`` enables direct PDF URL fetch (arXiv / known pdf_url).
    """
    stats = FullTextAttachStats(n_input=len(papers))
    index = _fixture_index(load_fulltext_fixture(fixture_path)) if use_fixture else {}
    pdf_dir = Path(pdf_dir) if pdf_dir else RAW_PDF_DIR
    attached = 0
    cap = max_attach if max_attach is not None else len(papers)

    for paper in papers:
        if attached >= cap:
            break
        if skip_existing and paper.has_full_text():
            continue

        # 1) Offline fixture match
        if use_fixture and index:
            row = match_fulltext_fixture(paper, index)
            if row and (row.get("full_text") or "").strip():
                attach_full_text(
                    paper,
                    row["full_text"],
                    source=row.get("source") or "fixture",
                    pdf_path=row.get("pdf_path"),
                    pdf_url=row.get("pdf_url"),
                )
                # Prefer fixture-provided sections if present
                if row.get("sections") and isinstance(row["sections"], list):
                    try:
                        paper.sections = [PaperSection(**s) for s in row["sections"]]
                    except Exception:
                        pass  # keep split_sections output
                stats.n_attached += 1
                stats.n_from_fixture += 1
                stats.bump_source(paper.full_text_source or "fixture")
                stats.attached_ids.append(paper.id)
                attached += 1
                continue

        # 2) Local PDF path already known
        local_pdf: Optional[Path] = None
        if paper.pdf_path and Path(paper.pdf_path).exists():
            local_pdf = Path(paper.pdf_path)
        else:
            # Convention: data/raw/pdfs/{safe_id}.pdf
            safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", paper.id)[:80]
            candidate = pdf_dir / f"{safe}.pdf"
            if candidate.exists():
                local_pdf = candidate

        if local_pdf is not None:
            try:
                text = extract_text_from_pdf(local_pdf)
                if len(text) > 120:
                    attach_full_text(
                        paper,
                        text,
                        source="pdf",
                        pdf_path=str(local_pdf),
                        pdf_url=paper.pdf_url or resolve_pdf_url(paper),
                    )
                    stats.n_attached += 1
                    stats.n_from_pdf += 1
                    stats.bump_source("pdf")
                    stats.attached_ids.append(paper.id)
                    attached += 1
                    continue
            except Exception as e:
                logger.warning("PDF extract failed for %s: %s", paper.id, e)
                stats.n_failed += 1

        # 3) Europe PMC OA full text (DOI → PMCID → fullTextXML)
        if europe_pmc and paper.doi:
            try:
                from src.ingest.europe_pmc import fetch_fulltext_for_paper

                ft = fetch_fulltext_for_paper(paper)
                if ft and len(ft.text) > 120:
                    attach_full_text(
                        paper,
                        ft.text,
                        source="europe_pmc",
                        pdf_url=f"https://europepmc.org/articles/{ft.pmcid}",
                    )
                    stats.n_attached += 1
                    stats.n_from_europe_pmc += 1
                    stats.bump_source("europe_pmc")
                    stats.attached_ids.append(paper.id)
                    attached += 1
                    continue
            except Exception as e:
                logger.warning("Europe PMC attach failed for %s: %s", paper.id, e)
                stats.n_failed += 1

        # 4) Optional live PDF download (arXiv etc.)
        if download:
            url = resolve_pdf_url(paper)
            if url:
                safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", paper.id)[:80]
                dest = pdf_dir / f"{safe}.pdf"
                try:
                    download_pdf(url, dest)
                    text = extract_text_from_pdf(dest)
                    if len(text) > 120:
                        attach_full_text(
                            paper,
                            text,
                            source="arxiv_pdf" if "arxiv.org" in url else "oa_pdf",
                            pdf_path=str(dest),
                            pdf_url=url,
                        )
                        stats.n_attached += 1
                        stats.n_from_download += 1
                        stats.bump_source(paper.full_text_source or "download")
                        stats.attached_ids.append(paper.id)
                        attached += 1
                        continue
                except Exception as e:
                    logger.warning("PDF download/extract failed for %s (%s): %s", paper.id, url, e)
                    stats.n_failed += 1

    logger.info(
        "Full-text attach: %d/%d attached (fixture=%d pdf=%d europe_pmc=%d download=%d failed=%d)",
        stats.n_attached,
        stats.n_input,
        stats.n_from_fixture,
        stats.n_from_pdf,
        stats.n_from_europe_pmc,
        stats.n_from_download,
        stats.n_failed,
    )
    return papers, stats


def fulltext_markdown_report(papers: list[Paper], stats: Optional[FullTextAttachStats] = None) -> str:
    """Short markdown summary of full-text coverage."""
    lines = [
        "# Full-text PDF depth",
        "",
        "Quote-grounded extracts use `Paper.text_blob()` which prefers attached full text.",
        "",
    ]
    n_ft = sum(1 for p in papers if p.has_full_text())
    lines += [
        "| Metric | Value |",
        "|--------|-------|",
        f"| Papers | {len(papers)} |",
        f"| With full text | {n_ft} |",
        f"| Abstract-only | {len(papers) - n_ft} |",
    ]
    if stats:
        lines += [
            f"| Attached this pass | {stats.n_attached} |",
            f"| From fixture | {stats.n_from_fixture} |",
            f"| From local PDF | {stats.n_from_pdf} |",
            f"| From Europe PMC OA | {stats.n_from_europe_pmc} |",
            f"| From PDF download | {stats.n_from_download} |",
            f"| Failed | {stats.n_failed} |",
        ]
    lines += ["", "## Papers with full text", ""]
    for p in papers:
        if not p.has_full_text():
            continue
        n_sec = len(p.sections or [])
        kinds = ", ".join(sorted({s.kind.value for s in p.sections})) if p.sections else "—"
        n_chars = len(p.full_text or "")
        lines.append(
            f"- **{p.title}** — source=`{p.full_text_source or '?'}` · "
            f"{n_chars} chars · {n_sec} sections ({kinds})"
        )
    if n_ft == 0:
        lines.append("_None attached. Run with `--fulltext` or `fulltext` CLI._")
    lines.append("")
    return "\n".join(lines)
