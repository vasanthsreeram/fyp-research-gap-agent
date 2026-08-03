"""Novelty-vs-corpus scoring for gaps (Stage 3 / wave 10).

Measures how *surprising* a gap is relative to the ingested paper corpus:
  - corpus_novelty: 1 − max similarity of gap text to *other* paper abstracts
    (own paper_ids excluded so self-source does not collapse novelty)
  - gap_redundancy: max similarity to other gap texts (near-duplicate penalty)
  - blended into Gap.novelty + overall, with nearest papers for cite-grounding

Default backend is lexical (Jaccard+TF cosine) so offline demos stay reliable.
Optional embedding backend when sentence-transformers is available.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from src.models import Gap, Paper

logger = logging.getLogger(__name__)

NoveltyBackend = Literal["auto", "lexical", "embedding"]


@dataclass
class NearestPaper:
    paper_id: str
    title: str
    year: Optional[int]
    similarity: float


@dataclass
class GapNoveltyRecord:
    gap_id: str
    title: str
    prior_novelty: float
    corpus_novelty: float
    nearest_sim: float
    gap_redundancy: float
    blended_novelty: float
    overall_before: float
    overall_after: float
    nearest: list[NearestPaper] = field(default_factory=list)
    kind: str = ""
    domain_tags: list[str] = field(default_factory=list)


@dataclass
class NoveltyReport:
    backend: str
    n_papers: int
    n_gaps: int
    mean_corpus_novelty: float
    mean_redundancy: float
    n_high_novelty: int  # corpus_novelty >= 0.55
    n_redundant: int  # gap_redundancy >= 0.55
    records: list[GapNoveltyRecord] = field(default_factory=list)
    notes: str = ""

    @property
    def top_surprising(self) -> list[GapNoveltyRecord]:
        return sorted(self.records, key=lambda r: r.blended_novelty, reverse=True)


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", (text or "").lower()))


def _tf_cosine(text_a: str, text_b: str) -> float:
    ta = Counter(re.findall(r"[a-z]{3,}", (text_a or "").lower()))
    tb = Counter(re.findall(r"[a-z]{3,}", (text_b or "").lower()))
    if not ta or not tb:
        return 0.0
    keys = set(ta) | set(tb)
    dot = sum(ta[k] * tb[k] for k in keys)
    na = math.sqrt(sum(v * v for v in ta.values()))
    nb = math.sqrt(sum(v * v for v in tb.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _jaccard(text_a: str, text_b: str) -> float:
    a, b = _token_set(text_a), _token_set(text_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def similarity_lexical(text_a: str, text_b: str) -> float:
    return 0.45 * _jaccard(text_a, text_b) + 0.55 * _tf_cosine(text_a, text_b)


def paper_blob(paper: Paper) -> str:
    return f"{paper.title or ''}\n{paper.abstract or ''}".strip()


def gap_blob(gap: Gap) -> str:
    tags = " ".join(gap.domain_tags or [])
    return f"{gap.title or ''}\n{gap.description or ''}\n{tags}".strip()


def resolve_novelty_backend(mode: NoveltyBackend = "auto") -> str:
    if mode == "lexical":
        return "lexical"
    if mode == "embedding":
        from src.gap.embeddings import embeddings_available

        if not embeddings_available():
            raise RuntimeError(
                "novelty backend=embedding requested but sentence-transformers is not installed"
            )
        return "embedding"
    try:
        from src.gap.embeddings import embeddings_available

        if embeddings_available():
            return "embedding"
    except Exception:
        pass
    return "lexical"


def _pairwise_sims_lexical(queries: list[str], docs: list[str]) -> list[list[float]]:
    return [[similarity_lexical(q, d) for d in docs] for q in queries]


def _pairwise_sims_embedding(queries: list[str], docs: list[str]) -> list[list[float]]:
    from src.gap.embeddings import cosine_sim, embed_texts

    if not queries or not docs:
        return [[] for _ in queries]
    q_vecs = embed_texts(queries)
    d_vecs = embed_texts(docs)
    out: list[list[float]] = []
    for qv in q_vecs:
        row = [float(max(0.0, cosine_sim(qv, dv))) for dv in d_vecs]
        out.append(row)
    return out


def apply_corpus_novelty(
    gaps: list[Gap],
    papers: list[Paper],
    *,
    backend: NoveltyBackend = "auto",
    top_k_nearest: int = 3,
    prior_weight: float = 0.4,
    corpus_weight: float = 0.6,
    redundancy_penalty: float = 0.15,
    exclude_own_papers: bool = True,
    mutate: bool = True,
) -> tuple[list[Gap], NoveltyReport]:
    """
    Score gaps against corpus abstracts and (optionally) rewrite novelty/overall.

    Returns (gaps, report). When mutate=True, Gap fields are updated in place:
      corpus_novelty, nearest_paper_ids, nearest_sim, gap_redundancy, novelty, overall, rationale
    """
    if not gaps:
        return gaps, NoveltyReport(
            backend="none",
            n_papers=len(papers),
            n_gaps=0,
            mean_corpus_novelty=0.0,
            mean_redundancy=0.0,
            n_high_novelty=0,
            n_redundant=0,
            notes="No gaps to score.",
        )

    concrete = resolve_novelty_backend(backend)
    logger.info(
        "Corpus novelty: backend=%s papers=%d gaps=%d",
        concrete,
        len(papers),
        len(gaps),
    )

    paper_ids = [p.id for p in papers]
    paper_texts = [paper_blob(p) for p in papers]
    gap_texts = [gap_blob(g) for g in gaps]

    if concrete == "embedding":
        try:
            gap_paper_sims = _pairwise_sims_embedding(gap_texts, paper_texts)
            gap_gap_sims = _pairwise_sims_embedding(gap_texts, gap_texts)
        except Exception as e:
            logger.warning("Embedding novelty failed, falling back to lexical: %s", e)
            concrete = "lexical"
            gap_paper_sims = _pairwise_sims_lexical(gap_texts, paper_texts)
            gap_gap_sims = _pairwise_sims_lexical(gap_texts, gap_texts)
    else:
        gap_paper_sims = _pairwise_sims_lexical(gap_texts, paper_texts)
        gap_gap_sims = _pairwise_sims_lexical(gap_texts, gap_texts)

    paper_by_id = {p.id: p for p in papers}
    records: list[GapNoveltyRecord] = []
    pw = max(0.0, min(1.0, prior_weight))
    cw = max(0.0, min(1.0, corpus_weight))
    if pw + cw <= 0:
        pw, cw = 0.4, 0.6
    norm = pw + cw
    pw, cw = pw / norm, cw / norm

    for i, gap in enumerate(gaps):
        own = set(gap.paper_ids or [])
        sims = gap_paper_sims[i] if i < len(gap_paper_sims) else []
        ranked: list[tuple[int, float]] = []
        for j, s in enumerate(sims):
            pid = paper_ids[j] if j < len(paper_ids) else ""
            if exclude_own_papers and pid in own:
                continue
            ranked.append((j, float(s)))
        ranked.sort(key=lambda t: t[1], reverse=True)

        if ranked:
            nearest_sim = ranked[0][1]
            corpus_nov = round(max(0.0, min(1.0, 1.0 - nearest_sim)), 4)
        else:
            # No other papers to compare — treat as moderately novel
            nearest_sim = 0.0
            corpus_nov = 0.7

        nearest: list[NearestPaper] = []
        for j, s in ranked[: max(1, top_k_nearest)]:
            p = papers[j]
            nearest.append(
                NearestPaper(
                    paper_id=p.id,
                    title=(p.title or "")[:120],
                    year=p.year,
                    similarity=round(float(s), 4),
                )
            )

        # Redundancy vs other gaps
        gg = gap_gap_sims[i] if i < len(gap_gap_sims) else []
        red = 0.0
        for k, s in enumerate(gg):
            if k == i:
                continue
            red = max(red, float(s))
        red = round(max(0.0, min(1.0, red)), 4)

        prior = float(gap.novelty)
        blended = pw * prior + cw * corpus_nov
        # Soft penalty when near-duplicate of another gap
        blended = blended * (1.0 - redundancy_penalty * red)
        blended = round(max(0.05, min(0.98, blended)), 4)

        overall_before = float(gap.overall)
        # Recompute overall with updated novelty, keep other axes
        overall_after = round(
            (float(gap.magnitude) + blended + float(gap.testability) + float(gap.impact)) / 4.0,
            4,
        )

        rec = GapNoveltyRecord(
            gap_id=gap.id,
            title=gap.title[:120],
            prior_novelty=prior,
            corpus_novelty=corpus_nov,
            nearest_sim=round(nearest_sim, 4),
            gap_redundancy=red,
            blended_novelty=blended,
            overall_before=overall_before,
            overall_after=overall_after,
            nearest=nearest,
            kind=getattr(gap.kind, "value", str(gap.kind)),
            domain_tags=list(gap.domain_tags or []),
        )
        records.append(rec)

        if mutate:
            gap.corpus_novelty = corpus_nov
            gap.nearest_sim = round(nearest_sim, 4)
            gap.nearest_paper_ids = [n.paper_id for n in nearest]
            gap.gap_redundancy = red
            gap.novelty = blended
            gap.overall = overall_after
            near_bits = []
            for n in nearest[:2]:
                y = f" ({n.year})" if n.year else ""
                near_bits.append(f'"{n.title[:60]}"{y} sim={n.similarity:.2f}')
            near_s = "; ".join(near_bits) if near_bits else "none"
            extra = (
                f" Corpus novelty={corpus_nov:.2f} (1−nearest_other_paper; backend={concrete}); "
                f"redundancy={red:.2f}; nearest: {near_s}."
            )
            if gap.rationale and "Corpus novelty=" not in gap.rationale:
                gap.rationale = (gap.rationale.rstrip() + extra)[:900]
            elif not gap.rationale:
                gap.rationale = extra.strip()[:900]

    if mutate:
        gaps.sort(key=lambda g: g.overall, reverse=True)

    mean_cn = sum(r.corpus_novelty for r in records) / len(records)
    mean_rd = sum(r.gap_redundancy for r in records) / len(records)
    report = NoveltyReport(
        backend=concrete,
        n_papers=len(papers),
        n_gaps=len(gaps),
        mean_corpus_novelty=round(mean_cn, 4),
        mean_redundancy=round(mean_rd, 4),
        n_high_novelty=sum(1 for r in records if r.corpus_novelty >= 0.55),
        n_redundant=sum(1 for r in records if r.gap_redundancy >= 0.55),
        records=records,
        notes=(
            "Own source papers excluded from nearest match. "
            "High corpus_novelty ≈ gap text distant from rest of corpus; "
            "high gap_redundancy ≈ near-duplicate of another gap."
        ),
    )
    logger.info(
        "Corpus novelty done: mean_cn=%.2f mean_red=%.2f high=%d redundant=%d",
        report.mean_corpus_novelty,
        report.mean_redundancy,
        report.n_high_novelty,
        report.n_redundant,
    )
    return gaps, report


def novelty_report_markdown(report: NoveltyReport, *, top_n: int = 12) -> str:
    lines = [
        "# Novelty-vs-corpus report",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **Backend** | `{report.backend}` |",
        f"| **Papers** | {report.n_papers} |",
        f"| **Gaps** | {report.n_gaps} |",
        f"| **Mean corpus novelty** | {report.mean_corpus_novelty:.2f} |",
        f"| **Mean gap redundancy** | {report.mean_redundancy:.2f} |",
        f"| **High novelty (≥0.55)** | {report.n_high_novelty} |",
        f"| **Redundant gaps (≥0.55)** | {report.n_redundant} |",
        "",
        f"_{report.notes}_",
        "",
        f"## Top surprising gaps (by blended novelty, n={min(top_n, len(report.records))})",
        "",
    ]
    for i, r in enumerate(report.top_surprising[:top_n], 1):
        lines += [
            f"### {i}. {r.title}",
            f"- **Gap ID**: `{r.gap_id}` · kind=`{r.kind}`",
            (
                f"- **Scores**: blended_novelty={r.blended_novelty:.2f} "
                f"corpus={r.corpus_novelty:.2f} prior={r.prior_novelty:.2f} "
                f"redundancy={r.gap_redundancy:.2f}"
            ),
            f"- **Overall**: {r.overall_before:.2f} → {r.overall_after:.2f}",
            f"- **Domains**: {', '.join(r.domain_tags) if r.domain_tags else '—'}",
            "- **Nearest corpus papers** (excluded own sources):",
        ]
        if r.nearest:
            for n in r.nearest:
                y = f" ({n.year})" if n.year else ""
                lines.append(f"  - [{n.similarity:.2f}] {n.title}{y} (`{n.paper_id}`)")
        else:
            lines.append("  - —")
        lines.append("")
    return "\n".join(lines) + "\n"


def save_novelty_report(report: NoveltyReport, path: Path, *, top_n: int = 12) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(novelty_report_markdown(report, top_n=top_n))
    return path
