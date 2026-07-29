"""Gap aligner + multi-axis scorer (theory ↔ experiment).

Alignment backends:
  - lexical: Jaccard + TF-cosine blend (always available)
  - embedding: sentence-transformers cosine (+ optional Chroma index)
  - auto: embedding if deps present, else lexical
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from pathlib import Path
from typing import Literal, Optional

from src.models import (
    Claim,
    Evidence,
    EvidenceType,
    Gap,
    GapKind,
    Paper,
)

logger = logging.getLogger(__name__)

AlignerMode = Literal["auto", "lexical", "embedding"]

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "lnp": ["lipid nanoparticle", "lnp", "ionizable lipid", "lipidoid"],
    "mrna": ["mrna", "messenger rna", "in vitro transcript", "nucleoside-modified"],
    "sirna": ["sirna", "small interfering", "rnai", "gene silencing"],
    "endosomal_escape": ["endosom", "endosomal escape", "endocytosis", "intracellular traff"],
    "targeting": ["targeted delivery", "extrahepatic", "tissue-specific", "tissue specific", "ligand-target"],
    "delivery_efficiency": ["delivery efficiency", "encapsulation", "transfection"],
    "vaccine": ["vaccine", "immunization", "adjuvant", "neutralizing antibody"],
    "gene_therapy": ["gene therapy", "gene editing", "crispr", "therapeutic gene"],
    "pks": ["pharmacokinetic", "biodistribution", "clearance", "half-life"],
    "immunogenicity": ["immunogenicity", "immune response", "innate immune", "reactogenic"],
    "corona": ["protein corona", "opsonization", "serum protein"],
}


def tag_domains(text: str) -> list[str]:
    text_lower = (text or "").lower()
    tags: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(domain)
    return tags


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", (text or "").lower()))


def jaccard(text_a: str, text_b: str) -> float:
    a, b = _token_set(text_a), _token_set(text_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _tf_cosine(text_a: str, text_b: str) -> float:
    """Lightweight bag-of-words cosine (no sklearn dependency at runtime)."""
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


def similarity_lexical(text_a: str, text_b: str) -> float:
    """Blend Jaccard + TF cosine for stabler alignment than Jaccard alone."""
    j = jaccard(text_a, text_b)
    c = _tf_cosine(text_a, text_b)
    return 0.45 * j + 0.55 * c


# Back-compat alias used by tests / older imports
def similarity(text_a: str, text_b: str) -> float:
    return similarity_lexical(text_a, text_b)


def resolve_aligner(mode: AlignerMode = "auto") -> str:
    """Return concrete aligner name: 'embedding' or 'lexical'."""
    if mode == "lexical":
        return "lexical"
    if mode == "embedding":
        from src.gap.embeddings import embeddings_available

        if not embeddings_available():
            raise RuntimeError(
                "aligner=embedding requested but sentence-transformers is not installed"
            )
        return "embedding"
    # auto
    try:
        from src.gap.embeddings import embeddings_available

        if embeddings_available():
            return "embedding"
    except Exception:
        pass
    return "lexical"


def score_gap(
    *,
    kind: GapKind,
    claim: Claim | None,
    evidence: Evidence | None,
    sim: float,
    domain_tags: list[str],
) -> dict[str, float]:
    """Multi-axis scores in [0, 1]."""
    if evidence is None:
        magnitude = 0.82
    elif evidence.evidence_type == EvidenceType.LIMITATION:
        magnitude = round(min(0.95, 0.55 + (1.0 - sim) * 0.4), 2)
    else:
        magnitude = round(min(0.95, 1.0 - sim), 2)

    # Novelty: higher for mechanism-unknown + less common domains
    novelty = 0.5
    if kind == GapKind.MECHANISM_UNKNOWN:
        novelty += 0.15
    if kind == GapKind.DELIVERY_BARRIER:
        novelty += 0.1
    if "endosomal_escape" in domain_tags or "targeting" in domain_tags:
        novelty += 0.1
    if claim and claim.claim_type.value == "mechanism":
        novelty += 0.05
    novelty = round(min(0.95, novelty), 2)

    testability = {
        GapKind.UNTESTED_CLAIM: 0.72,
        GapKind.THEORY_VS_EXPERIMENT: 0.65,
        GapKind.MECHANISM_UNKNOWN: 0.55,
        GapKind.DELIVERY_BARRIER: 0.7,
        GapKind.PREDICTION_MISS: 0.6,
        GapKind.REPRODUCIBILITY: 0.5,
        GapKind.SCALABILITY: 0.45,
        GapKind.OTHER: 0.5,
    }.get(kind, 0.5)

    impact = 0.45
    blob = " ".join(
        [
            claim.text if claim else "",
            evidence.text if evidence else "",
            " ".join(domain_tags),
        ]
    ).lower()
    for kw, bump in (
        ("delivery", 0.12),
        ("therapeutic", 0.1),
        ("in vivo", 0.08),
        ("clinical", 0.1),
        ("extrahepatic", 0.12),
        ("endosomal", 0.1),
        ("vaccine", 0.08),
    ):
        if kw in blob:
            impact += bump
    impact = round(min(0.95, impact), 2)

    overall = round((magnitude + novelty + testability + impact) / 4.0, 2)
    return {
        "magnitude": magnitude,
        "novelty": novelty,
        "testability": testability,
        "impact": impact,
        "overall": overall,
    }


def _best_evidence_matches_lexical(
    claims: list[Claim],
    ev_by_paper: dict[str, list[Evidence]],
) -> dict[str, tuple[Optional[Evidence], float]]:
    """claim_id → (best Evidence | None, sim)."""
    out: dict[str, tuple[Optional[Evidence], float]] = {}
    for claim in claims:
        ev_for_paper = ev_by_paper.get(claim.paper_id, [])
        best_ev: Evidence | None = None
        best_sim = 0.0
        for ev in ev_for_paper:
            sim = similarity_lexical(claim.text, ev.text)
            if sim > best_sim:
                best_sim = sim
                best_ev = ev
        out[claim.id] = (best_ev, best_sim)
    return out


def _best_evidence_matches_embedding(
    claims: list[Claim],
    evidence: list[Evidence],
    ev_by_paper: dict[str, list[Evidence]],
    *,
    use_chroma: bool = True,
    persist_dir: Optional[Path] = None,
) -> dict[str, tuple[Optional[Evidence], float]]:
    """
    Embed all claims + evidence once; match each claim to best same-paper evidence.
    Optionally also build a Chroma index of all evidence for inspectability / reuse.
    """
    from src.gap.embeddings import (
        build_chroma_index,
        cosine_sim,
        default_persist_dir,
        embed_texts,
    )

    out: dict[str, tuple[Optional[Evidence], float]] = {
        c.id: (None, 0.0) for c in claims
    }
    if not claims:
        return out

    # Optional persistent index of *all* evidence (cross-paper retrieval later)
    if use_chroma and evidence:
        try:
            pdir = Path(persist_dir) if persist_dir else Path(default_persist_dir())
            build_chroma_index(
                texts=[e.text for e in evidence],
                ids=[e.id for e in evidence],
                metadatas=[
                    {"paper_id": e.paper_id, "evidence_type": e.evidence_type.value}
                    for e in evidence
                ],
                collection_name="evidence",
                persist_dir=pdir,
                reset=True,
            )
        except Exception as e:  # non-fatal
            logger.warning("Chroma index build failed (non-fatal): %s", e)

    # Per-paper batch encode for same-paper alignment (primary path)
    # Group claims by paper for efficient encoding
    claims_by_paper: dict[str, list[Claim]] = {}
    for c in claims:
        claims_by_paper.setdefault(c.paper_id, []).append(c)

    for paper_id, paper_claims in claims_by_paper.items():
        paper_ev = ev_by_paper.get(paper_id, [])
        if not paper_ev:
            continue
        c_texts = [c.text for c in paper_claims]
        e_texts = [e.text for e in paper_ev]
        try:
            c_vecs = embed_texts(c_texts)
            e_vecs = embed_texts(e_texts)
        except Exception as e:
            logger.warning(
                "Embedding failed for paper %s, falling back to lexical: %s",
                paper_id,
                e,
            )
            for c in paper_claims:
                best_ev, best_sim = None, 0.0
                for ev in paper_ev:
                    sim = similarity_lexical(c.text, ev.text)
                    if sim > best_sim:
                        best_sim, best_ev = sim, ev
                out[c.id] = (best_ev, best_sim)
            continue

        for ci, claim in enumerate(paper_claims):
            best_i, best_s = -1, -1.0
            for ei, ev_vec in enumerate(e_vecs):
                s = cosine_sim(c_vecs[ci], ev_vec)
                if s > best_s:
                    best_s, best_i = s, ei
            if best_i >= 0:
                out[claim.id] = (paper_ev[best_i], float(max(0.0, best_s)))

    return out


def find_gaps(
    claims: list[Claim],
    evidence: list[Evidence],
    papers: list[Paper],
    similarity_threshold: float = 0.12,
    *,
    aligner: AlignerMode = "auto",
    embedding_threshold: Optional[float] = None,
    use_chroma: bool = True,
    chroma_dir: Optional[Path] = None,
) -> list[Gap]:
    """
    Align claims with evidence and surface:
      - untested claims
      - claim vs limitation mismatches
      - mechanism claims lacking support
      - unmatched author-stated limitations

    `aligner`: auto | lexical | embedding
    Embedding cosine sims run higher than lexical blends; default embedding
    threshold is 0.35 (override via embedding_threshold).
    """
    paper_map = {p.id: p for p in papers}
    ev_by_paper: dict[str, list[Evidence]] = {}
    for e in evidence:
        ev_by_paper.setdefault(e.paper_id, []).append(e)

    concrete = resolve_aligner(aligner)
    logger.info("Gap aligner: %s (requested=%s)", concrete, aligner)

    if concrete == "embedding":
        thr = (
            embedding_threshold
            if embedding_threshold is not None
            else max(similarity_threshold, 0.35)
        )
        matches = _best_evidence_matches_embedding(
            claims,
            evidence,
            ev_by_paper,
            use_chroma=use_chroma,
            persist_dir=chroma_dir,
        )
        # Mechanism weak-support cutoff scales with embedding sims
        mech_weak = 0.55
    else:
        thr = similarity_threshold
        matches = _best_evidence_matches_lexical(claims, ev_by_paper)
        mech_weak = 0.35

    gaps: list[Gap] = []
    seen_sigs: set[tuple[str, str]] = set()

    for claim in claims:
        paper = paper_map.get(claim.paper_id)
        paper_title = paper.title[:80] if paper else "unknown"
        best_ev, best_sim = matches.get(claim.id, (None, 0.0))

        if best_ev is None or best_sim < thr:
            gap_kind = GapKind.UNTESTED_CLAIM
        elif best_ev.evidence_type == EvidenceType.LIMITATION:
            gap_kind = GapKind.THEORY_VS_EXPERIMENT
        elif claim.claim_type.value == "mechanism":
            # Mechanism claim with only weak/non-limitation evidence still a gap
            if best_sim < mech_weak or best_ev.evidence_type in (
                EvidenceType.OBSERVATION,
                EvidenceType.OTHER,
            ):
                gap_kind = GapKind.MECHANISM_UNKNOWN
            else:
                continue
        else:
            continue

        sig = (claim.paper_id, claim.id)
        if sig in seen_sigs:
            continue
        seen_sigs.add(sig)

        domain_tags = list(
            set(tag_domains(claim.text) + (tag_domains(best_ev.text) if best_ev else []))
        )
        scores = score_gap(
            kind=gap_kind, claim=claim, evidence=best_ev, sim=best_sim, domain_tags=domain_tags
        )

        if gap_kind == GapKind.UNTESTED_CLAIM:
            title = f"Untested: {claim.text[:80]}"
            description = (
                f'Claim without matching experimental evidence: "{claim.text[:150]}" [{paper_title}]'
            )
        elif gap_kind == GapKind.MECHANISM_UNKNOWN:
            title = f"Mechanism gap: {claim.text[:80]}"
            description = (
                f'Mechanism claim lacks strong experimental support: "{claim.text[:120]}" [{paper_title}]'
            )
        else:
            title = f"Gap: {claim.text[:55]} vs {(best_ev.text if best_ev else '')[:55]}"
            description = (
                f'Claim vs limitation: "{claim.text[:100]}" vs '
                f'"{(best_ev.text if best_ev else "")[:100]}" [{paper_title}]'
            )

        gaps.append(
            Gap(
                kind=gap_kind,
                title=title[:200],
                description=description[:500],
                claim_ids=[claim.id],
                evidence_ids=[best_ev.id] if best_ev else [],
                paper_ids=[claim.paper_id],
                magnitude=scores["magnitude"],
                novelty=scores["novelty"],
                testability=scores["testability"],
                impact=scores["impact"],
                overall=scores["overall"],
                domain_tags=domain_tags,
                rationale=(
                    f"Claim confidence {claim.confidence:.2f}, best evidence sim {best_sim:.2f} "
                    f"({concrete}). Claim type={claim.claim_type.value}, kind={gap_kind.value}."
                ),
            )
        )

    for ev in evidence:
        if ev.evidence_type != EvidenceType.LIMITATION:
            continue
        if any(ev.id in g.evidence_ids for g in gaps):
            continue
        paper = paper_map.get(ev.paper_id)
        paper_title = paper.title[:80] if paper else "unknown"
        domain_tags = tag_domains(ev.text)
        kind = (
            GapKind.DELIVERY_BARRIER
            if any(
                k in ev.text.lower()
                for k in ("delivery", "endosom", "target", "barrier", "bottleneck")
            )
            else GapKind.OTHER
        )
        scores = score_gap(kind=kind, claim=None, evidence=ev, sim=0.0, domain_tags=domain_tags)
        gaps.append(
            Gap(
                kind=kind,
                title=f"Limitation: {ev.text[:80]}",
                description=f'Acknowledged limitation: "{ev.text[:200]}" [{paper_title}]',
                evidence_ids=[ev.id],
                paper_ids=[ev.paper_id],
                magnitude=scores["magnitude"],
                novelty=scores["novelty"],
                testability=scores["testability"],
                impact=scores["impact"],
                overall=scores["overall"],
                domain_tags=domain_tags,
                rationale="Unmatched author-stated limitation — candidate open problem.",
            )
        )

    gaps.sort(key=lambda g: g.overall, reverse=True)
    logger.info(
        "Found %d gaps from %d claims + %d evidence (aligner=%s)",
        len(gaps),
        len(claims),
        len(evidence),
        concrete,
    )
    return gaps
