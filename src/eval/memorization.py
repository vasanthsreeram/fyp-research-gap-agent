"""Memorization / grounding safeguards for LLM-heavy literature pipelines.

Supervisor concern (2026-07-01): retrospective eval can be fooled if the model
already memorized the literature. This module provides offline-first probes:

1. **Quote grounding** — extracted claim/evidence quote_spans must appear in
   the source paper text (substring or high token overlap).
2. **Held-out year split** — papers with year >= cutoff are treated as
   post-cutoff; we report extract/gap stats on that slice alone.
3. **Cross-era leakage** — post-cutoff claim texts should not be near-duplicates
   of pre-cutoff abstracts (fixture contamination / regurgitated canon).
4. **Unsupported claims** — claim body (and structured slots) must be grounded
   in the source; else flagged as unsupported / likely hallucinated.
5. **Hallucinated citations** — DOIs, arXiv ids, years, author-year cites in
   claim text that do not match the source paper metadata.
6. **Overconfidence** — high confidence + absolute language + missing
   uncertainty / weak grounding.
7. **Structured-slot coverage** — fraction of claims with hypothesis /
   mechanism / assumptions / uncertainty filled (robustness metric).
8. **Optional closed-book LLM probe** — given only a held-out title, ask the
   model for the abstract; high n-gram overlap flags memorization risk.
9. **Controlled prompt suite** — synthetic known-good / known-bad cases for
   regression (no network).

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

# Absolute / overconfident surface forms
ABSOLUTE_RE = re.compile(
    r"\b("
    r"always|never|all\s+cases|completely|entirely|definitively|"
    r"proves?\s+that|irrefutable|without\s+exception|guarantees?|"
    r"undeniably|certainly\s+causes?"
    r")\b",
    re.IGNORECASE,
)

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
ARXIV_RE = re.compile(r"\barxiv:\s*\d{4}\.\d{4,5}(v\d+)?\b", re.IGNORECASE)
# Author-year style: (Smith et al., 2019) or Smith et al. (2019)
CITE_YEAR_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+et\s+al\.)?)\s*[,\s]*\(?((?:19|20)\d{2})\)?",
)
YEAR_MENTION_RE = re.compile(r"\b((?:19|20)\d{2})\b")


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


def text_supported_by_paper(text: Optional[str], paper_text: str, min_jaccard: float = 0.28) -> bool:
    """Softer support check for paraphrased claim bodies / structured slots."""
    if not text or not text.strip():
        return False
    if quote_is_grounded(text, paper_text, min_jaccard=0.5):
        return True
    return token_jaccard(text, paper_text) >= min_jaccard


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
class UnsupportedClaimHit:
    claim_id: str
    paper_id: str
    reason: str
    claim_preview: str
    support_jaccard: float = 0.0


@dataclass
class CitationHallucinationHit:
    claim_id: str
    paper_id: str
    kind: str  # doi | arxiv | year | cite
    value: str
    claim_preview: str


@dataclass
class OverconfidenceHit:
    claim_id: str
    paper_id: str
    confidence: float
    reasons: list[str]
    claim_preview: str


@dataclass
class StructureCoverage:
    n_claims: int = 0
    n_with_hypothesis: int = 0
    n_with_evidence: int = 0
    n_with_mechanism: int = 0
    n_with_assumptions: int = 0
    n_with_uncertainty: int = 0
    n_fully_slotted: int = 0  # >=3 of 5 slots filled
    rate_hypothesis: float = 0.0
    rate_any_structure: float = 0.0

    def finalize(self) -> None:
        n = self.n_claims or 1
        self.rate_hypothesis = self.n_with_hypothesis / n if self.n_claims else 1.0
        any_n = sum(
            1
            for filled in []  # placeholder; recomputed in analyzer
        )
        # rate_any_structure set by caller


@dataclass
class ControlledCaseResult:
    case_id: str
    name: str
    passed: bool
    detail: str = ""


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
    unsupported_hits: list[UnsupportedClaimHit]
    unsupported_rate: float
    citation_hits: list[CitationHallucinationHit]
    citation_hallucination_rate: float
    overconfidence_hits: list[OverconfidenceHit]
    overconfidence_rate: float
    structure: StructureCoverage
    closed_book: list[ClosedBookResult]
    closed_book_flagged: int
    controlled_cases: list[ControlledCaseResult]
    controlled_pass: bool
    pass_grounding: bool
    pass_leakage: bool
    pass_unsupported: bool
    pass_citations: bool
    pass_overconfidence: bool
    overall_pass: bool
    notes: list[str] = field(default_factory=list)
    recommended_metrics: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        return asdict(self)

    def to_markdown(self) -> str:
        lines = [
            "# Memorization / Grounding Benchmark",
            "",
            "| Field | Value |",
            "|-------|-------|",
            f"| **Cutoff year** | {self.cutoff_year} |",
            f"| **Papers** | {self.n_papers_total} (pre={self.n_pre_cutoff}, post={self.n_post_cutoff}) |",
            f"| **Claim grounding** | {self.claim_grounding.n_grounded}/{self.claim_grounding.n_items} ({self.claim_grounding.rate:.0%}) |",
            f"| **Evidence grounding** | {self.evidence_grounding.n_grounded}/{self.evidence_grounding.n_items} ({self.evidence_grounding.rate:.0%}) |",
            f"| **Cross-era leakage** | {len(self.leakage_hits)} (rate={self.leakage_rate:.0%}) |",
            f"| **Unsupported claims** | {len(self.unsupported_hits)} (rate={self.unsupported_rate:.0%}) |",
            f"| **Hallucinated citations** | {len(self.citation_hits)} (rate={self.citation_hallucination_rate:.0%}) |",
            f"| **Overconfidence flags** | {len(self.overconfidence_hits)} (rate={self.overconfidence_rate:.0%}) |",
            (
                f"| **Structure coverage** | hyp={self.structure.rate_hypothesis:.0%} "
                f"any={self.structure.rate_any_structure:.0%} "
                f"full(≥3)={self.structure.n_fully_slotted}/{self.structure.n_claims} |"
            ),
            f"| **Closed-book flagged** | {self.closed_book_flagged}/{len(self.closed_book)} |",
            f"| **Controlled cases** | {'PASS' if self.controlled_pass else 'FAIL'} "
            f"({sum(1 for c in self.controlled_cases if c.passed)}/{len(self.controlled_cases)}) |",
            f"| **Pass grounding** | {'yes' if self.pass_grounding else 'NO'} |",
            f"| **Pass leakage** | {'yes' if self.pass_leakage else 'NO'} |",
            f"| **Pass unsupported** | {'yes' if self.pass_unsupported else 'NO'} |",
            f"| **Pass citations** | {'yes' if self.pass_citations else 'NO'} |",
            f"| **Pass overconfidence** | {'yes' if self.pass_overconfidence else 'NO'} |",
            f"| **Overall** | {'PASS' if self.overall_pass else 'FAIL'} |",
            "",
        ]
        if self.notes:
            lines += ["## Notes", ""]
            for n in self.notes:
                lines.append(f"- {n}")
            lines.append("")
        if self.recommended_metrics:
            lines += ["## Recommended evaluation metrics", ""]
            for m in self.recommended_metrics:
                lines.append(f"- {m}")
            lines.append("")
        if self.unsupported_hits:
            lines += ["## Unsupported claims (sample)", ""]
            for h in self.unsupported_hits[:8]:
                lines.append(
                    f"- `{h.claim_id}` j={h.support_jaccard:.2f} ({h.reason}): {h.claim_preview[:120]}"
                )
            lines.append("")
        if self.citation_hits:
            lines += ["## Hallucinated citations (sample)", ""]
            for h in self.citation_hits[:8]:
                lines.append(
                    f"- `{h.claim_id}` {h.kind}={h.value}: {h.claim_preview[:100]}"
                )
            lines.append("")
        if self.overconfidence_hits:
            lines += ["## Overconfidence flags (sample)", ""]
            for h in self.overconfidence_hits[:8]:
                lines.append(
                    f"- `{h.claim_id}` conf={h.confidence:.2f} [{', '.join(h.reasons)}]: "
                    f"{h.claim_preview[:100]}"
                )
            lines.append("")
        if self.leakage_hits:
            lines += ["## Leakage hits (post-cutoff claims ≈ pre-cutoff abstracts)", ""]
            for h in self.leakage_hits[:10]:
                lines.append(
                    f"- `{h.claim_id}` j={h.jaccard:.2f} vs `{h.best_pre_paper_id}`: {h.claim_preview[:120]}"
                )
            lines.append("")
        if self.controlled_cases:
            lines += ["## Controlled prompt / synthetic cases", ""]
            for c in self.controlled_cases:
                flag = "ok" if c.passed else "FAIL"
                lines.append(f"- [{flag}] `{c.case_id}` {c.name}: {c.detail}")
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


def find_unsupported_claims(
    claims: list[Claim],
    papers_by_id: dict[str, Paper],
    *,
    min_jaccard: float = 0.22,
) -> list[UnsupportedClaimHit]:
    """Flag claims whose body is not supported by the assigned paper text."""
    hits: list[UnsupportedClaimHit] = []
    for c in claims:
        paper = papers_by_id.get(c.paper_id)
        if paper is None:
            hits.append(
                UnsupportedClaimHit(
                    claim_id=c.id,
                    paper_id=c.paper_id,
                    reason="missing_paper",
                    claim_preview=c.text[:200],
                )
            )
            continue
        blob = paper.text_blob()
        blob_toks = _tokens(blob)
        j = token_jaccard(c.text, blob)
        quote_ok = quote_is_grounded(c.quote_span or c.text, blob)
        body_ok = text_supported_by_paper(c.text, blob, min_jaccard=min_jaccard)

        def _slot_unsupported(val: str) -> bool:
            """True only for longer prose that shares almost no content tokens."""
            if not val or not str(val).strip():
                return False
            s = str(val).strip()
            if text_supported_by_paper(s, blob, min_jaccard=0.15):
                return False
            st = _tokens(s)
            if not st:
                return False
            # Token coverage: most content words appear in the paper
            coverage = len(st & blob_toks) / len(st)
            if coverage >= 0.5:
                return False
            # Only flag substantial invented prose
            return len(s) > 48 and token_jaccard(s, blob) < 0.12

        slot_fail = False
        for slot_name in ("hypothesis", "evidence", "mechanism", "uncertainty"):
            val = getattr(c, slot_name, None)
            if val and _slot_unsupported(val):
                slot_fail = True
                break
        if not slot_fail:
            for a in c.assumptions or []:
                if _slot_unsupported(a):
                    slot_fail = True
                    break

        if not quote_ok and not body_ok:
            hits.append(
                UnsupportedClaimHit(
                    claim_id=c.id,
                    paper_id=c.paper_id,
                    reason="ungrounded_body_and_quote",
                    claim_preview=c.text[:200],
                    support_jaccard=round(j, 3),
                )
            )
        elif slot_fail:
            hits.append(
                UnsupportedClaimHit(
                    claim_id=c.id,
                    paper_id=c.paper_id,
                    reason="ungrounded_structured_slot",
                    claim_preview=c.text[:200],
                    support_jaccard=round(j, 3),
                )
            )
    return hits


def find_hallucinated_citations(
    claims: list[Claim],
    papers_by_id: dict[str, Paper],
) -> list[CitationHallucinationHit]:
    """Detect citation-like tokens in claims that disagree with paper metadata."""
    hits: list[CitationHallucinationHit] = []
    for c in claims:
        paper = papers_by_id.get(c.paper_id)
        text = " ".join(
            filter(
                None,
                [
                    c.text,
                    c.hypothesis,
                    c.evidence,
                    c.mechanism,
                    c.uncertainty,
                    " ".join(c.assumptions or []),
                ],
            )
        )
        # DOI
        for m in DOI_RE.findall(text):
            doi = m.rstrip(").,;")
            paper_doi = (paper.doi or "").lower() if paper else ""
            if not paper_doi or doi.lower() not in paper_doi and paper_doi not in doi.lower():
                # Also ok if DOI appears in abstract
                blob = paper.text_blob().lower() if paper else ""
                if doi.lower() not in blob:
                    hits.append(
                        CitationHallucinationHit(
                            claim_id=c.id,
                            paper_id=c.paper_id,
                            kind="doi",
                            value=doi,
                            claim_preview=c.text[:160],
                        )
                    )
        # arXiv
        for m in ARXIV_RE.findall(text):
            # findall with group may return tuples; normalize
            pass
        for m in re.finditer(r"\barxiv:\s*(\d{4}\.\d{4,5}(?:v\d+)?)\b", text, re.I):
            aid = m.group(1)
            paper_aid = (paper.arxiv_id or "") if paper else ""
            blob = paper.text_blob().lower() if paper else ""
            if aid not in paper_aid and aid.lower() not in blob:
                hits.append(
                    CitationHallucinationHit(
                        claim_id=c.id,
                        paper_id=c.paper_id,
                        kind="arxiv",
                        value=aid,
                        claim_preview=c.text[:160],
                    )
                )
        # Explicit foreign years only when paired with citation-like context
        # (bare years in prose are too noisy for offline heuristics).
        if paper and paper.year:
            blob = paper.text_blob()
            cite_ctx = re.compile(
                r"\b(doi|arxiv|et\s+al\.?|cited|according\s+to|reported\s+in|"
                r"previously\s+shown|ref\.?)\b",
                re.I,
            )
            for ym in YEAR_MENTION_RE.findall(text):
                y = int(ym)
                if y == paper.year or ym in blob:
                    continue
                # Require nearby citation cue within ±40 chars of the year
                for m in re.finditer(rf"\b{y}\b", text):
                    window = text[max(0, m.start() - 40) : m.end() + 40]
                    if cite_ctx.search(window) and abs(y - paper.year) >= 2 and y >= 1990:
                        hits.append(
                            CitationHallucinationHit(
                                claim_id=c.id,
                                paper_id=c.paper_id,
                                kind="year",
                                value=ym,
                                claim_preview=c.text[:160],
                            )
                        )
                        break
        # Author-year cites not reflected in paper authors/abstract
        if paper:
            author_lnames = {
                (a.split()[-1]).lower()
                for a in (paper.authors or [])
                if a and a.split()
            }
            blob_l = paper.text_blob().lower()
            for m in CITE_YEAR_RE.finditer(text):
                name, year_s = m.group(1), m.group(2)
                lname = name.replace("et al.", "").strip().split()[-1].lower()
                if lname in author_lnames:
                    continue
                if lname in blob_l and year_s in blob_l:
                    continue
                # High-precision: only flag "et al." forms or paren years with capital name
                if "et al" in m.group(0).lower() or f"({year_s})" in m.group(0):
                    hits.append(
                        CitationHallucinationHit(
                            claim_id=c.id,
                            paper_id=c.paper_id,
                            kind="cite",
                            value=m.group(0).strip(),
                            claim_preview=c.text[:160],
                        )
                    )
    return hits


def find_overconfident_claims(
    claims: list[Claim],
    papers_by_id: dict[str, Paper],
    *,
    conf_threshold: float = 0.85,
) -> list[OverconfidenceHit]:
    """High confidence + absolute language and/or missing uncertainty + weak ground."""
    hits: list[OverconfidenceHit] = []
    for c in claims:
        reasons: list[str] = []
        paper = papers_by_id.get(c.paper_id)
        blob = paper.text_blob() if paper else ""
        abs_lang = bool(ABSOLUTE_RE.search(c.text or ""))
        high_conf = (c.confidence or 0) >= conf_threshold
        no_unc = not (c.uncertainty and str(c.uncertainty).strip())
        weak_ground = bool(blob) and not quote_is_grounded(c.quote_span or c.text, blob)

        if abs_lang and high_conf:
            reasons.append("absolute_language+high_conf")
        if high_conf and no_unc and abs_lang:
            reasons.append("no_uncertainty_slot")
        if high_conf and weak_ground:
            reasons.append("high_conf_weak_grounding")
        if abs_lang and no_unc and (c.confidence or 0) >= 0.7:
            reasons.append("absolute_without_hedge")

        if reasons:
            hits.append(
                OverconfidenceHit(
                    claim_id=c.id,
                    paper_id=c.paper_id,
                    confidence=float(c.confidence or 0),
                    reasons=reasons,
                    claim_preview=c.text[:200],
                )
            )
    return hits


def measure_structure_coverage(claims: list[Claim]) -> StructureCoverage:
    sc = StructureCoverage(n_claims=len(claims))
    any_struct = 0
    for c in claims:
        slots = 0
        if c.hypothesis:
            sc.n_with_hypothesis += 1
            slots += 1
        if c.evidence:
            sc.n_with_evidence += 1
            slots += 1
        if c.mechanism:
            sc.n_with_mechanism += 1
            slots += 1
        if c.assumptions:
            sc.n_with_assumptions += 1
            slots += 1
        if c.uncertainty:
            sc.n_with_uncertainty += 1
            slots += 1
        if slots >= 3:
            sc.n_fully_slotted += 1
        if slots >= 1:
            any_struct += 1
    sc.finalize()
    sc.rate_any_structure = (any_struct / sc.n_claims) if sc.n_claims else 1.0
    return sc


def run_controlled_prompt_suite() -> list[ControlledCaseResult]:
    """Synthetic offline cases: known-good grounding vs known-bad hallucinations.

    These do not call an LLM. They validate detector logic with controlled inputs
    so CI can catch regressions without API keys. For open/small models, run the
    same cases through extract_claims_llm when a key is available.
    """
    from src.extract.claims import extract_claims_heuristic, structure_claim_fields

    results: list[ControlledCaseResult] = []

    good_paper = Paper(
        id="ctrl_good",
        title="Ionizable lipids and endosomal escape",
        abstract=(
            "We propose that ionizable lipids in LNPs promote endosomal escape "
            "through a pH-dependent flip-flop mechanism. Results show less than "
            "2% of mRNA reaches the cytosol. The exact molecular mechanism remains "
            "poorly understood and may depend on helper lipid composition."
        ),
        year=2023,
        doi="10.1000/ctrl.good",
        authors=["Ada Lovelace", "Alan Turing"],
    )

    # Case 1: heuristic extract is grounded
    claims = extract_claims_heuristic(good_paper)
    g_ok = bool(claims) and all(
        quote_is_grounded(c.quote_span or c.text, good_paper.text_blob()) for c in claims
    )
    results.append(
        ControlledCaseResult(
            case_id="ctrl_grounded_heuristic",
            name="heuristic claims grounded in source",
            passed=g_ok,
            detail=f"n_claims={len(claims)}",
        )
    )

    # Case 2: structured slots populated
    struct_ok = bool(claims) and any(
        c.hypothesis or c.mechanism or c.uncertainty for c in claims
    )
    results.append(
        ControlledCaseResult(
            case_id="ctrl_structure_slots",
            name="structured hypothesis/mechanism/uncertainty present",
            passed=struct_ok,
            detail=f"hyp={sum(1 for c in claims if c.hypothesis)} "
            f"mech={sum(1 for c in claims if c.mechanism)} "
            f"unc={sum(1 for c in claims if c.uncertainty)}",
        )
    )

    # Case 3: unsupported claim detector catches invented text
    bad = Claim(
        id="claim_bad_unsup",
        paper_id="ctrl_good",
        text=(
            "Quantum teleportation of lipid nanoparticles enables faster-than-light "
            "hepatic clearance via wormhole-assisted endocytosis in all patients."
        ),
        quote_span="Quantum teleportation of lipid nanoparticles",
        confidence=0.95,
    )
    unsup = find_unsupported_claims([bad], {"ctrl_good": good_paper})
    results.append(
        ControlledCaseResult(
            case_id="ctrl_unsupported_detector",
            name="flags invented unsupported claim",
            passed=len(unsup) >= 1,
            detail=f"hits={len(unsup)}",
        )
    )

    # Case 4: hallucinated DOI / foreign cite
    bad_cite = Claim(
        id="claim_bad_cite",
        paper_id="ctrl_good",
        text=(
            "As shown by Smith et al. (1999) and DOI 10.9999/fake.doi.xyz, "
            "endosomal escape is always complete."
        ),
        quote_span="endosomal escape",
        confidence=0.99,
    )
    cites = find_hallucinated_citations([bad_cite], {"ctrl_good": good_paper})
    results.append(
        ControlledCaseResult(
            case_id="ctrl_citation_detector",
            name="flags hallucinated DOI/cite",
            passed=len(cites) >= 1,
            detail=f"hits={len(cites)} kinds={[h.kind for h in cites]}",
        )
    )

    # Case 5: overconfidence detector
    over = Claim(
        id="claim_over",
        paper_id="ctrl_good",
        text="Ionizable lipids always completely prove that endosomal escape never fails.",
        quote_span="endosomal escape",
        confidence=0.99,
        uncertainty=None,
    )
    ohits = find_overconfident_claims([over], {"ctrl_good": good_paper})
    results.append(
        ControlledCaseResult(
            case_id="ctrl_overconfidence_detector",
            name="flags absolute + high-confidence claim",
            passed=len(ohits) >= 1,
            detail=f"hits={len(ohits)}",
        )
    )

    # Case 6: structure_claim_fields on mechanism sentence
    sf = structure_claim_fields(
        "We propose that ionizable lipids promote endosomal escape through protonation.",
    )
    results.append(
        ControlledCaseResult(
            case_id="ctrl_structure_fn",
            name="structure_claim_fields fills hypothesis/mechanism",
            passed=bool(sf.get("hypothesis") or sf.get("mechanism")),
            detail=str({k: (v[:40] if isinstance(v, str) else v) for k, v in sf.items()}),
        )
    )

    # Case 7: good claim should NOT be unsupported
    good_claim = Claim(
        id="claim_good",
        paper_id="ctrl_good",
        text="ionizable lipids in LNPs promote endosomal escape through a pH-dependent flip-flop mechanism",
        quote_span="ionizable lipids in LNPs promote endosomal escape through a pH-dependent flip-flop mechanism",
        confidence=0.55,
        uncertainty="mechanism remains poorly understood",
        hypothesis="ionizable lipids promote endosomal escape",
        mechanism="pH-dependent flip-flop mechanism",
    )
    unsup_good = find_unsupported_claims([good_claim], {"ctrl_good": good_paper})
    results.append(
        ControlledCaseResult(
            case_id="ctrl_supported_passes",
            name="grounded claim not flagged unsupported",
            passed=len(unsup_good) == 0,
            detail=f"hits={len(unsup_good)}",
        )
    )

    return results


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


DEFAULT_METRICS = [
    "Claim quote-grounding rate (≥85% pass)",
    "Evidence quote-grounding rate (≥85% pass)",
    "Cross-era leakage rate on post-cutoff claims (≤15% pass)",
    "Unsupported-claim rate (≤10% pass)",
    "Hallucinated-citation rate (≤5% pass)",
    "Overconfidence flag rate (≤20% advisory; ≤35% hard fail)",
    "Structure coverage: % claims with hypothesis; % with ≥3 slots",
    "Post-cutoff slice size (n papers year≥cutoff; target ≥10)",
    "Closed-book title→abstract overlap flag rate (optional; open/small models preferred)",
    "Controlled synthetic suite pass (all cases)",
]


def run_memorization_benchmark(
    papers: list[Paper],
    claims: list[Claim],
    evidence: list[Evidence],
    *,
    cutoff_year: int = DEFAULT_CUTOFF,
    leakage_threshold: float = 0.72,
    min_grounding_rate: float = 0.85,
    max_leakage_rate: float = 0.15,
    max_unsupported_rate: float = 0.10,
    max_citation_rate: float = 0.05,
    max_overconfidence_rate: float = 0.35,
    run_closed_book: bool = False,
    run_controlled: bool = True,
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

    unsupported = find_unsupported_claims(claims, papers_by_id)
    unsupported_rate = (len(unsupported) / len(claims)) if claims else 0.0

    citations = find_hallucinated_citations(claims, papers_by_id)
    citation_rate = (len(citations) / len(claims)) if claims else 0.0

    overconf = find_overconfident_claims(claims, papers_by_id)
    overconf_rate = (len(overconf) / len(claims)) if claims else 0.0

    structure = measure_structure_coverage(claims)

    closed: list[ClosedBookResult] = []
    if run_closed_book and post:
        closed = closed_book_llm_probe(post)

    controlled: list[ControlledCaseResult] = []
    if run_controlled:
        controlled = run_controlled_prompt_suite()
    controlled_pass = all(c.passed for c in controlled) if controlled else True

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
    if structure.n_claims and structure.rate_any_structure < 0.5:
        notes.append(
            f"Low structure coverage ({structure.rate_any_structure:.0%}); "
            "claim decomposer may need tuning."
        )
    notes.append(
        "Prefer open/small models (e.g. gpt-4o-mini, local GGUF) for closed-book "
        "probes; set OPENAI_MODEL. Offline path stays model-free."
    )

    pass_g = claim_g.rate >= min_grounding_rate and evid_g.rate >= min_grounding_rate
    pass_l = leakage_rate <= max_leakage_rate
    pass_u = unsupported_rate <= max_unsupported_rate
    pass_c = citation_rate <= max_citation_rate
    pass_o = overconf_rate <= max_overconfidence_rate

    closed_flagged = sum(1 for r in closed if r.flagged)
    overall = pass_g and pass_l and pass_u and pass_c and pass_o and controlled_pass
    if closed and closed_flagged > max(1, len(closed) // 2):
        notes.append(
            "Closed-book probe flagged majority of held-out titles — high memorization risk."
        )
        overall = False

    return MemorizationReport(
        cutoff_year=cutoff_year,
        n_papers_total=len(papers),
        n_pre_cutoff=len(pre),
        n_post_cutoff=len(post),
        claim_grounding=claim_g,
        evidence_grounding=evid_g,
        leakage_hits=leakage,
        leakage_rate=round(leakage_rate, 3),
        unsupported_hits=unsupported,
        unsupported_rate=round(unsupported_rate, 3),
        citation_hits=citations,
        citation_hallucination_rate=round(citation_rate, 3),
        overconfidence_hits=overconf,
        overconfidence_rate=round(overconf_rate, 3),
        structure=structure,
        closed_book=closed,
        closed_book_flagged=closed_flagged,
        controlled_cases=controlled,
        controlled_pass=controlled_pass,
        pass_grounding=pass_g,
        pass_leakage=pass_l,
        pass_unsupported=pass_u,
        pass_citations=pass_c,
        pass_overconfidence=pass_o,
        overall_pass=overall,
        notes=notes,
        recommended_metrics=list(DEFAULT_METRICS),
    )


def save_report(report: MemorizationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.to_markdown())
    json_path = path.with_suffix(".json")
    json_path.write_text(json.dumps(report.to_dict(), indent=2))
    logger.info("Memorization report → %s (+ %s)", path, json_path)
