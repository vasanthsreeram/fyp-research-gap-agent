"""Unified ingestion pipeline: live APIs → fixture fallback → cache."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from src.models import Paper
from src.ingest import arxiv_client, semantic_scholar as s2

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
) -> list[Paper]:
    """
    Ingest pipeline:
      1. If use_fixture → load fixture only
      2. Else try Semantic Scholar (+ optional arXiv), merge, dedupe
      3. If live APIs yield 0 → fixture fallback
      4. Truncate to `limit`, cache under data/raw + data/processed
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if use_fixture:
        papers = load_fixture()
    else:
        papers = []
        api_key = os.environ.get("S2_API_KEY") or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")

        raw_s2 = s2.search_all(
            limit_per_query=max(5, min(15, limit)),
            max_papers=max(limit * 2, 30),
            api_key=api_key,
        )
        if raw_s2:
            s2.save_raw(raw_s2, RAW_DIR / "semantic_scholar.json")
            for r in raw_s2:
                m = s2.to_paper(r)
                if m and (m.abstract or "").strip():
                    papers.append(m)

        if include_arxiv:
            raw_ax = arxiv_client.search(max_results=min(15, limit))
            if raw_ax:
                arxiv_client.save_raw(raw_ax, RAW_DIR / "arxiv.json")
                for r in raw_ax:
                    m = arxiv_client.to_paper(r)
                    if m and (m.abstract or "").strip():
                        papers.append(m)

        papers = _dedupe_papers(papers)
        # Prefer papers with abstracts and more recent years
        papers.sort(key=lambda p: (bool(p.abstract), p.year or 0, p.citation_count or 0), reverse=True)

        if not papers:
            logger.warning("Live APIs returned 0 usable papers; falling back to fixtures")
            papers = load_fixture()
        else:
            logger.info("Live ingest produced %d papers before limit", len(papers))

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
