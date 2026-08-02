"""Unified ingestion pipeline: live APIs → fixture fallback → cache."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from src.models import Paper
from src.ingest import arxiv_client, openalex, semantic_scholar as s2
from src.ingest.keys import resolve_s2_api_key

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIXTURE_FILE = Path(__file__).resolve().parent.parent / "fixtures" / "papers_fixture.jsonl"


def load_fixture(path: Optional[Path] = None) -> list[Paper]:
    """Load bundled fixture papers (offline, always works)."""
    fixture = path or FIXTURE_FILE
    if not fixture.exists():
        logger.warning("No fixture file at %s", fixture)
        return []
    papers: list[Paper] = []
    with open(fixture) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                papers.append(Paper(**d))
            except Exception as e:
                logger.debug("Skipping fixture line: %s", e)
    logger.info("Loaded %d papers from fixture", len(papers))
    return papers


def _dedupe_papers(papers: list[Paper]) -> list[Paper]:
    """Dedupe by normalized title + DOI/arXiv id."""
    seen: set[str] = set()
    out: list[Paper] = []
    for p in papers:
        keys = []
        if p.doi:
            keys.append(f"doi:{p.doi.lower()}")
        if p.arxiv_id:
            keys.append(f"arxiv:{p.arxiv_id.lower()}")
        if p.s2_id:
            keys.append(f"s2:{p.s2_id}")
        keys.append("title:" + " ".join((p.title or "").lower().split()))
        if any(k in seen for k in keys):
            continue
        for k in keys:
            seen.add(k)
        out.append(p)
    return out


def ingest_papers(
    use_fixture: bool = False,
    save: bool = True,
    limit: int = 20,
    include_arxiv: bool = True,
    include_openalex: bool = True,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    prefer_recent: bool = True,
) -> list[Paper]:
    """
    Ingest pipeline:
      1. If use_fixture → load fixture only
      2. Else resolve S2 API key (env/Keychain), try Semantic Scholar
      3. Always try OpenAlex (free, no key) when include_openalex — fills gaps if S2 is rate-limited
      4. Optional arXiv
      5. If live APIs yield 0 → fixture fallback
      6. Truncate to `limit`, cache under data/raw + data/processed

    year_min/year_max: prefer post-cutoff / recent literature.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if use_fixture:
        papers = load_fixture()
        if year_min is not None:
            filtered = [p for p in papers if (p.year or 0) >= year_min]
            # Keep fixture usable even if filter is aggressive
            if filtered:
                papers = filtered
            else:
                logger.warning(
                    "Fixture year_min=%s matched 0 papers; keeping full fixture",
                    year_min,
                )
    else:
        papers = []
        api_key = resolve_s2_api_key()
        source_counts: dict[str, int] = {}

        raw_s2 = s2.search_all(
            limit_per_query=max(5, min(15, limit)),
            max_papers=max(limit * 2, 40),
            api_key=api_key,
            year_min=year_min,
            year_max=year_max,
        )
        if raw_s2:
            s2.save_raw(raw_s2, RAW_DIR / "semantic_scholar.json")
            for r in raw_s2:
                m = s2.to_paper(r)
                if m and (m.abstract or "").strip():
                    papers.append(m)
            source_counts["semantic_scholar"] = sum(
                1 for p in papers if p.source == "semantic_scholar"
            )

        # OpenAlex: free path that works without S2 key (primary live fallback)
        need_more = len(papers) < max(limit, 10)
        if include_openalex and (need_more or not api_key):
            try:
                raw_oa = openalex.search_all(
                    limit_per_query=max(5, min(15, limit)),
                    max_papers=max(limit * 2, 40),
                    year_min=year_min,
                    year_max=year_max,
                )
                if raw_oa:
                    openalex.save_raw(raw_oa, RAW_DIR / "openalex.json")
                    n_oa = 0
                    for r in raw_oa:
                        m = openalex.to_paper(r)
                        if m and (m.abstract or "").strip():
                            papers.append(m)
                            n_oa += 1
                    source_counts["openalex"] = n_oa
            except Exception as e:
                logger.warning("OpenAlex ingest failed: %s", e)

        if include_arxiv:
            raw_ax = arxiv_client.search(max_results=min(20, max(limit, 10)))
            if raw_ax:
                arxiv_client.save_raw(raw_ax, RAW_DIR / "arxiv.json")
                n_ax = 0
                for r in raw_ax:
                    m = arxiv_client.to_paper(r)
                    if not m or not (m.abstract or "").strip():
                        continue
                    if year_min is not None and (m.year or 0) < year_min:
                        continue
                    if year_max is not None and m.year and m.year > year_max:
                        continue
                    papers.append(m)
                    n_ax += 1
                source_counts["arxiv"] = n_ax

        papers = _dedupe_papers(papers)
        # Prefer abstracts, recent years, citation mass
        if prefer_recent:
            papers.sort(
                key=lambda p: (bool(p.abstract), p.year or 0, p.citation_count or 0),
                reverse=True,
            )
        else:
            papers.sort(
                key=lambda p: (bool(p.abstract), p.citation_count or 0, p.year or 0),
                reverse=True,
            )

        if not papers:
            logger.warning("Live APIs returned 0 usable papers; falling back to fixtures")
            papers = load_fixture()
        else:
            logger.info(
                "Live ingest produced %d papers before limit "
                "(S2 key=%s year_min=%s sources=%s)",
                len(papers),
                "yes" if api_key else "no",
                year_min,
                source_counts,
            )

    papers = papers[: max(1, limit)]

    if save and papers:
        out_path = PROCESSED_DIR / "papers.jsonl"
        with open(out_path, "w") as f:
            for p in papers:
                f.write(p.model_dump_json() + "\n")
        # Also mirror a slim raw snapshot of the chosen set
        slim_raw = RAW_DIR / "papers_selected.jsonl"
        with open(slim_raw, "w") as f:
            for p in papers:
                f.write(p.model_dump_json() + "\n")
        logger.info("Saved %d papers → %s", len(papers), out_path)

    return papers
