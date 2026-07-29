"""Memorization / grounding safeguards for LLM-heavy literature pipelines.

Supervisor concern (2026-07-01): retrospective eval can be fooled if the model
already memorized the literature. This module provides offline-first probes:

1. **Quote grounding** — extracted claim/evidence quote_spans must appear in
   the source paper text (substring or high token overlap).
2. **Held-out year split** — papers with year >= cutoff are treated as
   post-cutoff; we report extract/gap stats on that slice alone.
3. **Cross-era leakage** — post-cutoff claim texts should not be near-duplicates
   of pre-cutoff abstracts (fixture contamination / regurgitated canon).
4. **Optional closed-book LLM probe** — given only a held-out title, ask the
   model for the abstract; high n-gram overlap with the real abstract flags
   memorization risk. Skipped when no API key.

Usage:
  from src.eval.memorization import run_memorization_benchmark
  report = run_memorization_benchmark(papers, claims, evidence, cutoff_year=2024)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models import Claim, Evidence, Paper

logger = logging.getLogger(__name__)

DEFAULT_CUTOFF = 2024


def _norm(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", _norm(text)) if len(w) > 2}


def token_jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def quote_is_grounded(quote: Optional[str], paper_text: str, min_jaccard: float = 0.55) -> bool:
    """True if quote is a substring of paper text or highly overlapping."""
    if not quote or not quote.strip():
        return False
    q = _norm(quote)
    blob = _norm(paper_text)
    if len(q) < 12:
        return False
    if q in blob:
        return True
    # Allow light punctuation drift: sliding window on sentence-ish chunks
    if token_jaccard(q, blob) >= 0.85 and len(q) < len(blob):
        # Still require a substantial contiguous fragment
        frag = q[: max(40, len(q) // 3)]
        if frag in blob:
            return True
    return token_jaccard(q, blob) >= min_jaccard and any(
        _norm(sent) in blob or token_jaccard(sent, blob) > 0.7
        for sent in re.split(r"(?<=[.!?])\s+", quote)
        if len(sent) > 30
    )


@dataclass
class GroundingStats:
    n_items: int = 0
    n_grounded: int = 0
    n_missing_quote: int = 0
    rate: float = 0.0
    ungrounded_ids: list[str] = field(default_factory=list)

    def finalize(self) -> None:
        self.rate = (self.n_grounded / self.n_items) if self.n_items else 1.0


@dataclass
class LeakageHit:
    claim_id: str
    paper_id: str
    best_pre_paper_id: str
    jaccard: float
    claim_preview: str


@dataclass
class ClosedBookResult:
    paper_id: str
    title: str
    overlap: float
    flagged: bool
    note: str = ""


@dataclass
class MemorizationReport:
    cutoff_year: int
    n_papers_total: int
    n_pre_cutoff: int
    n_post_cutoff: int
    claim_grounding: GroundingStats
    evidence_grounding: GroundingStats
    leakage_hits: list[LeakageHit]
    leakage_rate: float
    closed_book: list[ClosedBookResult]
    closed_book_flagged: int
    pass_grounding: bool
    pass_leakage: bool
    overall_pass: bool
    notes: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def to_markdown(self) -> str:
        lines = [
            "# Memorization / Grounding Benchmark",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| **Cutoff year** | {self.cutoff_year} |",
            f"| **Papers** | {self.n_papers_total} (pre={self.n_pre_cutoff}, post={self.n_post_cutoff}) |",
            f"| **Claim grounding** | {self.claim_grounding.n_grounded}/{self.claim_grounding.n_items} ({self.claim_grounding.rate:.0%}) |",
            f"| **Evidence grounding** | {self.evidence_grounding.n_grounded}/{self.evidence_grounding.n_items} ({self.evidence_grounding.rate:.0%}) |",
            f"| **Cross-era leakage hits** | {len(self.leakage_hits)} (rate={self.leakage_rate:.0%}) |",
            f"| **Closed-book flagged** | {self.closed_book_flagged}/{len(self.closed_book)} |",
            f"| **Pass grounding** | {'yes' if self.pass_grounding else 'NO'} |",
            f"| **Pass leakage** | {'yes' if self.pass_leakage else 'NO'} |",
            f"| **Overall** | {'PASS' if self.overall_pass else 'FAIL'} |",
            "",
        ]
        if self.notes:
            lines += ["## Notes", ""]
            for n in self.notes:
                lines.append(f"- {n}")
            lines.append("")
        if self.leakage_hits:
            lines += ["## Leakage hits (post-cutoff claims ≈ pre-cutoff abstracts)", ""]
            for h in self.leakage_hits[:10]:
                lines.append(
                    f"- `{h.claim_id}` j={h.jaccard:.2f} vs `{h.best_pre_paper_id}`: {h.claim_preview[:120]}"
                )
            lines.append("")
        if self.closed_book:
            lines += ["## Closed-book LLM probe", ""]
            for r in self.closed_book:
                flag = "FLAG" if r.flagged else "ok"
                lines.append(f"- [{flag}] {r.title[:80]} — overlap={r.overlap:.2f} {r.note}")
            lines.append("")
        lines.append(f"*Generated {self.generated_at}*")
        return "\n".join(lines)


def _grounding_for_items(
    items: list,
    papers_by_id: dict[str, Paper],
    *,
    id_attr: str = "id",
) -> GroundingStats:
    stats = GroundingStats()
    for it in items:
        stats.n_items += 1
        pid = getattr(it, "paper_id", None)
        paper = papers_by_id.get(pid) if pid else None
        quote = getattr(it, "quote_span", None) or getattr(it, "text", None)
        if not quote:
            stats.n_missing_quote += 1
            stats.ungrounded_ids.append(getattr(it, id_attr, "?"))
            continue
        if paper is None:
            stats.ungrounded_ids.append(getattr(it, id_attr, "?"))
            continue
        if quote_is_grounded(quote, paper.text_blob()):
            stats.n_grounded += 1
        else:
            stats.ungrounded_ids.append(getattr(it, id_attr, "?"))
    stats.finalize()
    return stats


def find_cross_era_leakage(
    post_claims: list[Claim],
    pre_papers: list[Paper],
    threshold: float = 0.72,
) -> list[LeakageHit]:
    """Flag post-cutoff claims that heavily overlap any pre-cutoff abstract."""
    hits: list[LeakageHit] = []
    pre_blobs = [(p.id, p.text_blob()) for p in pre_papers if p.text_blob()]
    for c in post_claims:
        best_j, best_id = 0.0, ""
        for pid, blob in pre_blobs:
            j = token_jaccard(c.text, blob)
            if j > best_j:
                best_j, best_id = j, pid
        if best_j >= threshold:
            hits.append(
                LeakageHit(
                    claim_id=c.id,
                    paper_id=c.paper_id,
                    best_pre_paper_id=best_id,
                    jaccard=round(best_j, 3),
                    claim_preview=c.text[:200],
                )
            )
    return hits


def closed_book_llm_probe(
    papers: list[Paper],
    overlap_flag: float = 0.45,
    max_papers: int = 5,
) -> list[ClosedBookResult]:
    """Ask LLM for abstract given title only; measure overlap with true abstract."""
    try:
        from src.extract.llm_util import get_client, llm_available

        if not llm_available():
            return []
        client = get_client()
    except Exception as e:
        logger.info("Closed-book probe skipped: %s", e)
        return []

    import os

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    results: list[ClosedBookResult] = []
    for p in papers[:max_papers]:
        if not (p.abstract or "").strip():
            continue
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You recall scientific paper abstracts from memory if you know them. "
                            "If you do not know the paper, say UNKNOWN and do not invent details. "
                            "Return only the abstract text or UNKNOWN."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Title: {p.title}\nYear: {p.year or 'unknown'}\nDOI: {p.doi or 'unknown'}",
                    },
                ],
                temperature=0.0,
                max_tokens=400,
            )
            guess = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            results.append(
                ClosedBookResult(
                    paper_id=p.id,
                    title=p.title,
                    overlap=0.0,
                    flagged=False,
                    note=f"error: {e}",
                )
            )
            continue

        if guess.upper().startswith("UNKNOWN") or len(guess) < 40:
            results.append(
                ClosedBookResult(
                    paper_id=p.id, title=p.title, overlap=0.0, flagged=False, note="unknown/abstain"
                )
            )
            continue
        ov = token_jaccard(guess, p.abstract)
        results.append(
            ClosedBookResult(
                paper_id=p.id,
                title=p.title,
                overlap=round(ov, 3),
                flagged=ov >= overlap_flag,
                note="high overlap" if ov >= overlap_flag else "low overlap",
            )
        )
    return results


def run_memorization_benchmark(
    papers: list[Paper],
    claims: list[Claim],
    evidence: list[Evidence],
    *,
    cutoff_year: int = DEFAULT_CUTOFF,
    leakage_threshold: float = 0.72,
    min_grounding_rate: float = 0.85,
    max_leakage_rate: float = 0.15,
    run_closed_book: bool = False,
) -> MemorizationReport:
    """Run offline memorization/grounding probes and return a structured report."""
    papers_by_id = {p.id: p for p in papers}
    pre = [p for p in papers if (p.year or 0) and p.year < cutoff_year]
    post = [p for p in papers if (p.year or 0) >= cutoff_year]
    # Papers missing year count as pre (conservative: don't put unknowns in held-out)
    undated = [p for p in papers if not p.year]
    pre = pre + undated

    claim_g = _grounding_for_items(claims, papers_by_id)
    evid_g = _grounding_for_items(evidence, papers_by_id)

    post_ids = {p.id for p in post}
    post_claims = [c for c in claims if c.paper_id in post_ids]
    leakage = find_cross_era_leakage(post_claims, pre, threshold=leakage_threshold)
    leakage_rate = (len(leakage) / len(post_claims)) if post_claims else 0.0

    closed: list[ClosedBookResult] = []
    if run_closed_book and post:
        closed = closed_book_llm_probe(post)

    notes: list[str] = []
    if not post:
        notes.append(
            f"No post-cutoff papers (year>={cutoff_year}) in corpus; "
            "expand fixtures/live ingest for a stronger held-out set."
        )
    if claim_g.n_missing_quote:
        notes.append(f"{claim_g.n_missing_quote} claims missing quote_span.")
    if evid_g.n_missing_quote:
        notes.append(f"{evid_g.n_missing_quote} evidence items missing quote_span.")

    pass_g = claim_g.rate >= min_grounding_rate and evid_g.rate >= min_grounding_rate
    pass_l = leakage_rate <= max_leakage_rate
    # Closed-book is informational unless majority flagged
    closed_flagged = sum(1 for r in closed if r.flagged)
    if closed and closed_flagged > max(1, len(closed) // 2):
        notes.append("Closed-book probe flagged majority of held-out titles — high memorization risk.")
        overall = False
    else:
        overall = pass_g and pass_l

    return MemorizationReport(
        cutoff_year=cutoff_year,
        n_papers_total=len(papers),
        n_pre_cutoff=len(pre),
        n_post_cutoff=len(post),
        claim_grounding=claim_g,
        evidence_grounding=evid_g,
        leakage_hits=leakage,
        leakage_rate=round(leakage_rate, 3),
        closed_book=closed,
        closed_book_flagged=closed_flagged,
        pass_grounding=pass_g,
        pass_leakage=pass_l,
        overall_pass=overall,
        notes=notes,
    )


def save_report(report: MemorizationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.to_markdown())
    json_path = path.with_suffix(".json")
    json_path.write_text(json.dumps(report.to_dict(), indent=2))
    logger.info("Memorization report → %s (+ %s)", path, json_path)
