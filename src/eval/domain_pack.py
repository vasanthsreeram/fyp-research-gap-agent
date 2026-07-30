"""Second-domain evaluation pack (hybrid / bifunctional ncRNA).

Computes slice coverage and gap/topic yield for a domain keyword pack so
supervisor demos can show LNP-core vs hybrid-ncRNA balance — not just bulk counts.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from src.models import Claim, Evidence, Gap, Paper, TopicProposal
from src.gap.score import tag_domains

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = REPO_ROOT / "reports"

# Primary domain packs for Stage-2 dual-slice eval
DOMAIN_PACKS: dict[str, dict] = {
    "lnp_core": {
        "label": "LNP / mRNA delivery (core)",
        "paper_keywords": {
            "nucleic_acid_delivery",
            "lnp",
            "mrna",
            "sirna",
        },
        # Exclude pure hybrid-first papers from "core-only" view when exclusive=True
        "exclude_keywords": {"hybrid_ncrna"},
        "text_markers": (
            "lipid nanoparticle",
            "ionizable lipid",
            "endosomal escape",
            "extrahepatic",
            "mrna",
        ),
        "min_papers": 15,
        "min_gaps": 5,
    },
    "hybrid_ncrna": {
        "label": "Hybrid / bifunctional ncRNA",
        "paper_keywords": {
            "hybrid_ncrna",
            "ncrna",
            "gene_editing",
        },
        "exclude_keywords": set(),
        "text_markers": (
            "ncrna",
            "non-coding",
            "bifunctional",
            "hybrid nucleic",
            "circrna",
            "lncrna",
            "mirna",
            "guide rna",
            "ribozyme",
            "adar",
            "risc",
            "rna origami",
            "pna",
        ),
        "min_papers": 8,
        "min_gaps": 3,
    },
    "gene_editing": {
        "label": "Gene editing / CRISPR delivery",
        "paper_keywords": {"gene_editing", "gene_therapy"},
        "exclude_keywords": set(),
        "text_markers": ("crispr", "cas9", "cas13", "base edit", "gene editing", "indel"),
        "min_papers": 4,
        "min_gaps": 2,
    },
}


def _paper_kw_set(p: Paper) -> set[str]:
    return {k.lower() for k in (p.keywords or [])}


def paper_in_pack(paper: Paper, pack_id: str, exclusive: bool = False) -> bool:
    pack = DOMAIN_PACKS[pack_id]
    kws = _paper_kw_set(paper)
    want = {k.lower() for k in pack["paper_keywords"]}
    excl = {k.lower() for k in pack.get("exclude_keywords") or set()}
    text = paper.text_blob().lower()
    kw_hit = bool(kws & want)
    text_hit = any(m in text for m in pack["text_markers"])
    in_pack = kw_hit or text_hit
    if exclusive and excl and (kws & excl):
        # still keep if pack is hybrid itself
        if pack_id != "hybrid_ncrna":
            return False
    return in_pack


def filter_papers(papers: list[Paper], pack_id: str, exclusive: bool = False) -> list[Paper]:
    if pack_id not in DOMAIN_PACKS:
        raise KeyError(f"Unknown domain pack: {pack_id}. Choose from {list(DOMAIN_PACKS)}")
    return [p for p in papers if paper_in_pack(p, pack_id, exclusive=exclusive)]


def _ids(papers: Iterable[Paper]) -> set[str]:
    return {p.id for p in papers}


@dataclass
class PackSliceMetrics:
    pack_id: str
    label: str
    n_papers: int = 0
    n_claims: int = 0
    n_evidence: int = 0
    n_gaps: int = 0
    n_topics: int = 0
    post_cutoff_papers: int = 0
    top_gap_titles: list[str] = field(default_factory=list)
    top_topic_titles: list[str] = field(default_factory=list)
    domain_tag_hist: dict[str, int] = field(default_factory=dict)
    pass_min_papers: bool = False
    pass_min_gaps: bool = False
    overall_pass: bool = False
    notes: str = ""


@dataclass
class DomainPackReport:
    n_papers_total: int
    cutoff_year: int
    packs: list[PackSliceMetrics] = field(default_factory=list)
    overall_pass: bool = False

    def to_markdown(self) -> str:
        lines = [
            "# Domain pack evaluation",
            "",
            f"- Total papers in run: **{self.n_papers_total}**",
            f"- Cutoff year (held-out count): **{self.cutoff_year}**",
            f"- Overall pack gate: **{'PASS' if self.overall_pass else 'FAIL'}**",
            "",
            "| Pack | Papers | Claims | Evidence | Gaps | Topics | Post-cutoff | Gate |",
            "|------|--------|--------|----------|------|--------|-------------|------|",
        ]
        for p in self.packs:
            gate = "PASS" if p.overall_pass else "FAIL"
            lines.append(
                f"| {p.pack_id} | {p.n_papers} | {p.n_claims} | {p.n_evidence} | "
                f"{p.n_gaps} | {p.n_topics} | {p.post_cutoff_papers} | {gate} |"
            )
        lines.append("")
        for p in self.packs:
            lines += [
                f"## {p.label} (`{p.pack_id}`)",
                "",
                f"- Min papers/gaps: {DOMAIN_PACKS[p.pack_id]['min_papers']}/"
                f"{DOMAIN_PACKS[p.pack_id]['min_gaps']} → "
                f"{'ok' if p.overall_pass else 'below threshold'}",
                f"- Domain tag hist: `{p.domain_tag_hist}`",
                "",
                "Top gaps:",
            ]
            for t in p.top_gap_titles[:5]:
                lines.append(f"- {t}")
            if not p.top_gap_titles:
                lines.append("- _(none)_")
            lines.append("")
            lines.append("Top topics:")
            for t in p.top_topic_titles[:5]:
                lines.append(f"- {t}")
            if not p.top_topic_titles:
                lines.append("- _(none)_")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "n_papers_total": self.n_papers_total,
            "cutoff_year": self.cutoff_year,
            "overall_pass": self.overall_pass,
            "packs": [asdict(p) for p in self.packs],
        }


def run_domain_pack_eval(
    papers: list[Paper],
    claims: list[Claim],
    evidence: list[Evidence],
    gaps: list[Gap],
    topics: list[TopicProposal],
    *,
    cutoff_year: int = 2024,
    pack_ids: Optional[list[str]] = None,
) -> DomainPackReport:
    """Evaluate coverage + yield for each configured domain pack."""
    chosen = pack_ids or list(DOMAIN_PACKS.keys())
    report = DomainPackReport(n_papers_total=len(papers), cutoff_year=cutoff_year)

    claims_by_paper: dict[str, list[Claim]] = {}
    for c in claims:
        claims_by_paper.setdefault(c.paper_id, []).append(c)
    evid_by_paper: dict[str, list[Evidence]] = {}
    for e in evidence:
        evid_by_paper.setdefault(e.paper_id, []).append(e)

    for pid in chosen:
        if pid not in DOMAIN_PACKS:
            logger.warning("Skipping unknown pack %s", pid)
            continue
        meta = DOMAIN_PACKS[pid]
        exclusive = pid == "lnp_core"
        slice_papers = filter_papers(papers, pid, exclusive=exclusive)
        pids = _ids(slice_papers)
        slice_claims = [c for c in claims if c.paper_id in pids]
        slice_evid = [e for e in evidence if e.paper_id in pids]
        # Gaps that touch any paper in the slice OR carry pack domain tags
        pack_tags = set(meta["paper_keywords"]) | {pid}
        if pid == "hybrid_ncrna":
            pack_tags |= {"hybrid_ncrna", "ncrna"}
        slice_gaps = [
            g
            for g in gaps
            if (set(g.paper_ids or []) & pids)
            or (set(g.domain_tags or []) & pack_tags)
            or any(t in pack_tags for t in tag_domains(g.title + " " + g.description))
        ]
        slice_topics = [
            t
            for t in topics
            if (set(t.domain_tags or []) & pack_tags)
            or any(gid in {g.id for g in slice_gaps} for gid in (t.gap_ids or []))
        ]

        tag_hist: Counter[str] = Counter()
        for g in slice_gaps:
            for t in g.domain_tags or []:
                tag_hist[t] += 1

        m = PackSliceMetrics(
            pack_id=pid,
            label=meta["label"],
            n_papers=len(slice_papers),
            n_claims=len(slice_claims),
            n_evidence=len(slice_evid),
            n_gaps=len(slice_gaps),
            n_topics=len(slice_topics),
            post_cutoff_papers=sum(1 for p in slice_papers if (p.year or 0) >= cutoff_year),
            top_gap_titles=[g.title for g in sorted(slice_gaps, key=lambda x: x.overall, reverse=True)[:5]],
            top_topic_titles=[t.title for t in sorted(slice_topics, key=lambda x: x.priority, reverse=True)[:5]],
            domain_tag_hist=dict(tag_hist.most_common(12)),
        )
        m.pass_min_papers = m.n_papers >= int(meta["min_papers"])
        m.pass_min_gaps = m.n_gaps >= int(meta["min_gaps"])
        m.overall_pass = m.pass_min_papers and m.pass_min_gaps
        if not m.overall_pass:
            m.notes = (
                f"need ≥{meta['min_papers']} papers and ≥{meta['min_gaps']} gaps; "
                f"got {m.n_papers}/{m.n_gaps}"
            )
        report.packs.append(m)

    # Require core + hybrid packs if both present
    required = [p for p in report.packs if p.pack_id in ("lnp_core", "hybrid_ncrna")]
    report.overall_pass = bool(required) and all(p.overall_pass for p in required)
    return report


def save_domain_pack_report(report: DomainPackReport, path: Optional[Path] = None) -> Path:
    out = path or (REPORTS_DIR / "domain_pack.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report.to_markdown())
    json_path = out.with_suffix(".json")
    json_path.write_text(json.dumps(report.to_dict(), indent=2))
    logger.info("Domain pack report → %s", out)
    return out
