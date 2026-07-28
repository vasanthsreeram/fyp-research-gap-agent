"""Gap scorer + topic suggester — align claims vs evidence, score, propose topics."""

from __future__ import annotations

import itertools
import logging
import re
from collections import Counter
from typing import Optional

from src.models import (
    Claim,
    Evidence,
    EvidenceType,
    Gap,
    GapKind,
    Paper,
    TopicProposal,
)

logger = logging.getLogger(__name__)

# ── Keyword clues for domain tagging ─────────────────────────────

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "lnp": ["lipid nanoparticle", "lnp", "ionizable lipid", "lipidoid", "LNP"],
    "mrna": ["mRNA", "messenger RNA", "in vitro transcript", "nucleoside-modified"],
    "sirna": ["siRNA", "small interfering", "RNAi", "gene silencing"],
    "endosomal_escape": ["endosom", "endosomal escape", "endocytosis", "intracellular traff"],
    "targeting": ["targeted delivery", "extrahepatic", "tissue-specific", "ligand-target"],
    "delivery_efficiency": ["delivery efficiency", "encapsulation", "transfection", "transfection efficiency"],
    "vaccine": ["vaccine", "immunization", "adjuvant", "neutralizing antibody"],
    "gene_therapy": ["gene therapy", "gene editing", "CRISPR", "therapeutic gene"],
    "pks": ["pharmacokinetic", "biodistribution", "clearance", "half-life"],
    "immunogenicity": ["immunogenicity", "immune response", "innate immune", "reactogenic"],
}

DEFAULT_DOMAINS = list(DOMAIN_KEYWORDS.keys())


def _tag_domain(text: str) -> list[str]:
    """Tag text with relevant domain keywords."""
    text_lower = text.lower()
    tags: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(domain)
    return tags


# ── Gap detection ────────────────────────────────────────────────


def _embed_similarity(text_a: str, text_b: str) -> float:
    """
    Simple word-overlap similarity (Jaccard). A real system would use embeddings.
    This is a heuristic — good enough for the vertical slice.
    """
    words_a = set(re.findall(r"[a-z]{3,}", text_a.lower()))
    words_b = set(re.findall(r"[a-z]{3,}", text_b.lower()))
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union) if union else 0.0


def find_gaps(
    claims: list[Claim],
    evidence: list[Evidence],
    papers: list[Paper],
    similarity_threshold: float = 0.08,
) -> list[Gap]:
    """
    Align claims with evidence. Score as gaps where:
    - A claim has no matching evidence (untested claim)
    - Evidence reports limitations (acknowledged gap)
    - Mechanism claims with no experimental support
    """
    paper_map = {p.id: p for p in papers}

    # Index evidence by paper
    ev_by_paper: dict[str, list[Evidence]] = {}
    for e in evidence:
        ev_by_paper.setdefault(e.paper_id, []).append(e)

    gaps: list[Gap] = []
    seen_gap_sigs: set[tuple[str, str]] = set()

    for claim in claims:
        paper = paper_map.get(claim.paper_id)
        paper_title = paper.title[:80] if paper else "unknown"
        ev_for_paper = ev_by_paper.get(claim.paper_id, [])

        # Find closest evidence
        best_ev = None
        best_sim = 0.0
        for ev in ev_for_paper:
            sim = _embed_similarity(claim.text, ev.text)
            if sim > best_sim:
                best_sim = sim
                best_ev = ev

        # Determine gap kind
        if best_ev is None or best_sim < similarity_threshold:
            gap_kind = GapKind.UNTESTED_CLAIM
        elif best_ev.evidence_type.value in ("limitation",):
            gap_kind = GapKind.THEORY_VS_EXPERIMENT
        elif claim.claim_type.value == "mechanism":
            gap_kind = GapKind.MECHANISM_UNKNOWN
        else:
            continue  # well-supported claim, skip

        # Build gap description
        if gap_kind == GapKind.UNTESTED_CLAIM:
            description = (
                f"Claim without matching experimental evidence: "
                f"\"{claim.text[:150]}\" [{paper_title}]"
            )
            title = f"Untested: {claim.text[:80]}"
        else:
            description = (
                f"Claim vs limitation mismatch: "
                f"\"{claim.text[:100]}\" vs \"{best_ev.text[:100]}\" [{paper_title}]"
            )
            title = f"Gap: {claim.text[:60]} vs {best_ev.text[:60]}"

        sig = (claim.paper_id, claim.id)
        if sig in seen_gap_sigs:
            continue
        seen_gap_sigs.add(sig)

        domain_tags = _tag_domain(claim.text)
        if best_ev is not None:
            domain_tags.extend(_tag_domain(best_ev.text))
        domain_tags = list(set(domain_tags))

        # Multi-axis scores (heuristic for v0)
        magnitude = round(1.0 - best_sim, 2) if best_ev else 0.8
        novelty = 0.5 + abs(hash(claim.text[:40])) % 30 / 100  # pseudo-random
        novelty = round(min(novelty, 0.95), 2)
        testability = 0.6 if gap_kind == GapKind.UNTESTED_CLAIM else 0.4
        impact = 0.5 + (1 if "delivery" in claim.text.lower() or "therapeutic" in claim.text.lower() else 0)
        impact = round(min(impact, 0.95), 2)
        overall = round((magnitude + novelty + testability + impact) / 4, 2)

        related_ev_ids = [best_ev.id] if best_ev else []

        gap = Gap(
            kind=gap_kind,
            title=title[:200],
            description=description[:500],
            claim_ids=[claim.id],
            evidence_ids=related_ev_ids,
            paper_ids=[claim.paper_id],
            magnitude=magnitude,
            novelty=novelty,
            testability=testability,
            impact=impact,
            overall=overall,
            domain_tags=domain_tags,
            rationale=(
                f"Claim confidence {claim.confidence:.2f}, "
                f"best evidence similarity {best_sim:.2f}. "
                f"Claim type: {claim.claim_type.value}, Gap kind: {gap_kind.value}"
            ),
        )
        gaps.append(gap)

    # Also find evidence-only limitations not matched to any claim
    for ev in evidence:
        if ev.evidence_type != EvidenceType.LIMITATION:
            continue
        # Check if any claim references this limitation
        already_matched = any(ev.id in g.evidence_ids for g in gaps)
        if already_matched:
            continue
        paper = paper_map.get(ev.paper_id)
        paper_title = paper.title[:80] if paper else "unknown"

        domain_tags = _tag_domain(ev.text)
        gap = Gap(
            kind=GapKind.DELIVERY_BARRIER if "delivery" in ev.text.lower() else GapKind.OTHER,
            title=f"Limitation: {ev.text[:80]}",
            description=f"Acknowledged limitation: \"{ev.text[:200]}\" [{paper_title}]",
            evidence_ids=[ev.id],
            paper_ids=[ev.paper_id],
            magnitude=0.5,
            novelty=0.4,
            testability=0.7,
            impact=0.5,
            overall=round((0.5 + 0.4 + 0.7 + 0.5) / 4, 2),
            domain_tags=domain_tags,
            rationale="Unmatched limitation — potential gap acknowledged by authors.",
        )
        gaps.append(gap)

    # Sort by overall score descending
    gaps.sort(key=lambda g: g.overall, reverse=True)
    logger.info("Found %d gaps from %d claims + %d evidence", len(gaps), len(claims), len(evidence))
    return gaps


# ── Topic suggestion ──────────────────────────────────────────────


def suggest_topics(gaps: list[Gap], max_topics: int = 5) -> list[TopicProposal]:
    """Generate research topic proposals from top gaps."""
    if not gaps:
        return []

    # Cluster by domain tags
    domain_clusters: dict[str, list[Gap]] = {}
    for gap in gaps:
        for tag in gap.domain_tags or DEFAULT_DOMAINS[:1]:
            domain_clusters.setdefault(tag, []).append(gap)

    # Sort clusters by average gap score
    cluster_scores: dict[str, float] = {}
    for tag, cluster_gaps in domain_clusters.items():
        cluster_scores[tag] = sum(g.overall for g in cluster_gaps) / len(cluster_gaps)

    sorted_clusters = sorted(cluster_scores.items(), key=lambda x: x[1], reverse=True)

    proposals: list[TopicProposal] = []

    # Topic templates keyed by domain
    templates: dict[str, dict] = {
        "lnp": {
            "title": "Rational design of ionizable lipids for extrahepatic nucleic acid delivery",
            "hypothesis": (
                "Systematic variation of ionizable lipid headgroup and tail architecture "
                "can achieve tissue-specific LNP tropism beyond the liver, enabling "
                "extravascular mRNA and siRNA delivery."
            ),
            "experiments": [
                "Synthesize a focused library of 20–30 ionizable lipids varying pKa and tail unsaturation",
                "Screen LNPs for in vitro transfection across hepatocyte, endothelial, and immune cell lines",
                "Validate top 5 candidates in vivo via IV administration with luminescent reporter mRNA",
                "Quantify biodistribution by organ-specific luciferase expression and RT-qPCR",
            ],
            "readout": "Ratio of extrahepatic-to-liver protein expression; top candidate achieves ≥2× extrahepatic selectivity.",
            "feasibility": "Requires medicinal chemistry expertise (2–3 months for lipid library) and a small-animal facility.",
        },
        "mrna": {
            "title": "Nucleoside modifications and delivery vehicle synergy for durable mRNA therapeutics",
            "hypothesis": (
                "Combining specific nucleoside modifications (N1-methylpseudouridine, 5-methylcytidine) "
                "with targeted LNPs extends mRNA translation duration beyond current 3–7 day window, "
                "reducing required dosing frequency for protein replacement therapies."
            ),
            "experiments": [
                "Compare translation duration of modified mRNAs (Ψ, m1Ψ, m5C) across cell types",
                "Test synergistic effects with LNPs containing endosomal escape enhancers",
                "Measure immune activation, translation decay, and protein half-life in mice",
            ],
            "readout": "Translation half-life extension ≥2× vs m1Ψ-alone in hepatocytes.",
            "feasibility": "Uses established synthesis and formulation techniques — high feasibility.",
        },
        "endosomal_escape": {
            "title": "Mechanistic understanding of LNP endosomal escape: disentangling fusion vs. destabilization",
            "hypothesis": (
                "Endosomal escape of LNPs proceeds primarily through membrane destabilization "
                "(ionizable lipid-facilitated flip-flop and bilayer disruption) rather than "
                "fusogenic mechanisms, and can be enhanced by helper lipids that lower the "
                "lamellar-to-hexagonal phase transition temperature."
            ),
            "experiments": [
                "Labelled lipid mixing vs. content release assays to distinguish fusion from destabilization",
                "Cryo-ET of LNPs in endosomal compartments at timed intervals after uptake",
                "Vary helper lipid ratios and correlate with endosomal escape efficiency via FRET",
            ],
            "readout": "Quantitative fraction of delivered cargo reaching cytosol vs. lysosomal degradation.",
            "feasibility": "Requires advanced microscopy (cryo-ET) — moderate; FRET assays are accessible.",
        },
        "targeting": {
            "title": "Ligand-displaying LNPs for extrahepatic targeting: avidity vs. specificity tradeoffs",
            "hypothesis": (
                "Multivalent display of low-affinity targeting ligands (e.g., mannose, transferrin, "
                "or anti-CD3 scFv) on LNP surfaces achieves higher tissue selectivity than "
                "high-affinity monovalent targeting, due to reduced off-target uptake by liver macrophages."
            ),
            "experiments": [
                "Synthesize LNPs with controlled densities of selected ligands (0–100% surface coverage)",
                "Quantify uptake in target vs. off-target cells with flow cytometry",
                "Test in vivo biodistribution with reporter mRNAs in xenograft or disease models",
            ],
            "readout": "Target-to-liver uptake ratio; ≥5× improvement over non-targeted LNPs.",
            "feasibility": "Lipid-PEG-ligand chemistry is standard; main risk is synthesis scale-up.",
        },
        "sirna": {
            "title": "Overcoming the endosomal barrier for siRNA-LNP therapeutics in non-hepatic tissues",
            "hypothesis": (
                "Efficient siRNA delivery to extrahepatic tissues requires LNPs with higher "
                "fusogenicity than those optimized for hepatocyte delivery, and can be achieved "
                "by tuning the lipid-to-helper ratio and incorporating pH-sensitive zwitterionic lipids."
            ),
            "experiments": [
                "Design and synthesize pH-sensitive zwitterionic helper lipids",
                "Formulate LNPs with varying fusogenic character and measure siRNA activity in vitro",
                "Evaluate biodistribution and gene silencing in a mouse model",
            ],
            "readout": "≥50% gene silencing in target extrahepatic tissue at ≤1 mg/kg siRNA dose.",
            "feasibility": "Lipid synthesis is specialized but doable; zwitterionic lipids are an active area.",
        },
    }

    for tag, avg_score in sorted_clusters:
        if len(proposals) >= max_topics:
            break
        template = templates.get(tag, {
            "title": f"Addressing gaps in {tag} for nucleic acid delivery",
            "hypothesis": f"Systematic investigation of {tag} mechanisms will reveal novel intervention points for improving delivery.",
            "experiments": [
                f"Comprehensive literature review of {tag} in LNP delivery",
                "Design and test candidate approaches in relevant in vitro models",
                "Validate top candidates in vivo",
            ],
            "readout": "The experimental readout quantifies improvement over baseline.",
            "feasibility": "Feasible with standard molecular biology and nanoparticle characterization tools.",
        })

        gap_ids = [g.id for g in domain_clusters[tag][:3]]
        proposal = TopicProposal(
            title=template["title"][:200],
            hypothesis=template["hypothesis"],
            gap_ids=gap_ids,
            proposed_experiments=template["experiments"],
            expected_readout=template["readout"],
            feasibility_notes=template["feasibility"],
            impact_rationale=(
                f"This topic addresses {len(gap_ids)} gaps in the '{tag}' domain "
                f"with an average gap score of {avg_score:.2f}. "
                f"Success could significantly advance nucleic acid delivery for therapeutic applications."
            ),
            priority=round(avg_score, 2),
            domain_tags=[tag],
        )
        proposals.append(proposal)

    # Sort by priority descending
    proposals.sort(key=lambda t: t.priority, reverse=True)
    logger.info("Generated %d topic proposals from %d gaps", len(proposals), len(gaps))
    return proposals
