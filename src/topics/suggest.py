"""Research topic proposals from scored gaps (pack-aware ranking)."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass

from src.models import Gap, TopicProposal

logger = logging.getLogger(__name__)

DEFAULT_DOMAIN = "lnp"

# Domain-tag → supervisor dual-slice pack. Order in PACK_PRIORITY is selection order
# for diversity slots (secondary packs first so hybrid is not starved by LNP mass).
PACK_TAG_MEMBERSHIP: dict[str, set[str]] = {
    "hybrid_ncrna": {
        "hybrid_ncrna",
        "ncrna",
        "async_escape",
    },
    "gene_editing": {
        "gene_therapy",
        "gene_editing",
    },
    "lnp_core": {
        "lnp",
        "mrna",
        "sirna",
        "endosomal_escape",
        "targeting",
        "delivery_efficiency",
        "corona",
        "pks",
        "immunogenicity",
        "vaccine",
        "nucleic_acid_delivery",
    },
}

# Prefer underrepresented packs when filling diversity slots
PACK_PRIORITY: tuple[str, ...] = ("hybrid_ncrna", "gene_editing", "lnp_core")

# Template keys that are pack-native (used for affinity scoring)
PACK_NATIVE_TEMPLATES: dict[str, set[str]] = {
    "hybrid_ncrna": {"hybrid_ncrna", "ncrna", "async_escape"},
    "gene_editing": {"gene_therapy", "gene_editing"},
    "lnp_core": {
        "lnp",
        "mrna",
        "sirna",
        "endosomal_escape",
        "targeting",
        "delivery_efficiency",
        "corona",
        "pks",
        "immunogenicity",
        "vaccine",
    },
}

# Preferred seed tag when a pack has gaps but no matching template cluster yet
PACK_SEED_TAG: dict[str, str] = {
    "hybrid_ncrna": "hybrid_ncrna",
    "gene_editing": "gene_therapy",
    "lnp_core": "lnp",
}

# Soft priority boost for secondary packs so they can surface in top-k without
# drowning LNP (which has more fixture mass). Applied only when pack_balance=True.
PACK_SCORE_BOOST: dict[str, float] = {
    "hybrid_ncrna": 0.08,
    "gene_editing": 0.05,
    "lnp_core": 0.0,
}

TEMPLATES: dict[str, dict] = {
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
            "with targeted LNPs extends mRNA translation duration beyond the current 3–7 day window, "
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
        "title": "Mechanistic understanding of LNP endosomal escape: fusion vs destabilization",
        "hypothesis": (
            "Endosomal escape of LNPs proceeds primarily through membrane destabilization "
            "(ionizable lipid-facilitated flip-flop and bilayer disruption) rather than "
            "fusogenic mechanisms, and can be enhanced by helper lipids that lower the "
            "lamellar-to-hexagonal phase transition temperature."
        ),
        "experiments": [
            "Labelled lipid mixing vs content release assays to distinguish fusion from destabilization",
            "Cryo-ET of LNPs in endosomal compartments at timed intervals after uptake",
            "Vary helper lipid ratios and correlate with endosomal escape efficiency via FRET",
        ],
        "readout": "Quantitative fraction of delivered cargo reaching cytosol vs lysosomal degradation.",
        "feasibility": "Requires advanced microscopy (cryo-ET) — moderate; FRET assays are accessible.",
    },
    "targeting": {
        "title": "Ligand-displaying LNPs for extrahepatic targeting: avidity vs specificity",
        "hypothesis": (
            "Multivalent display of low-affinity targeting ligands (e.g., mannose, transferrin, "
            "or anti-CD3 scFv) on LNP surfaces achieves higher tissue selectivity than "
            "high-affinity monovalent targeting, due to reduced off-target uptake by liver macrophages."
        ),
        "experiments": [
            "Synthesize LNPs with controlled densities of selected ligands (0–100% surface coverage)",
            "Quantify uptake in target vs off-target cells with flow cytometry",
            "Test in vivo biodistribution with reporter mRNAs in xenograft or disease models",
        ],
        "readout": "Target-to-liver uptake ratio; ≥5× improvement over non-targeted LNPs.",
        "feasibility": "Lipid-PEG-ligand chemistry is standard; main risk is synthesis scale-up.",
    },
    "sirna": {
        "title": "Overcoming the endosomal barrier for siRNA-LNP therapeutics in non-hepatic tissues",
        "hypothesis": (
            "Efficient siRNA delivery to extrahepatic tissues requires LNPs with higher "
            "fusogenicity than those optimized for hepatocyte delivery, achievable by tuning "
            "the lipid-to-helper ratio and incorporating pH-sensitive zwitterionic lipids."
        ),
        "experiments": [
            "Design and synthesize pH-sensitive zwitterionic helper lipids",
            "Formulate LNPs with varying fusogenic character and measure siRNA activity in vitro",
            "Evaluate biodistribution and gene silencing in a mouse model",
        ],
        "readout": "≥50% gene silencing in target extrahepatic tissue at ≤1 mg/kg siRNA dose.",
        "feasibility": "Lipid synthesis is specialized but doable; zwitterionic lipids are an active area.",
    },
    "corona": {
        "title": "Engineering the LNP protein corona to control biodistribution",
        "hypothesis": (
            "Pre-coating LNPs with defined protein coronas (or corona-minimizing polymers) "
            "can redirect tropism away from hepatocytes by altering apolipoprotein E recruitment."
        ),
        "experiments": [
            "Characterize hard corona composition of standard vs modified LNPs via proteomics",
            "Pre-adsorb candidate corona proteins and measure shifts in in vivo organ uptake",
            "Correlate ApoE binding with LDLR-dependent liver uptake across formulations",
        ],
        "readout": "≥30% absolute reduction in liver accumulation with preserved transfection potency.",
        "feasibility": "Proteomics + standard mouse biodistribution; moderate resource need.",
    },
    "pks": {
        "title": "Pharmacokinetic determinants of repeat-dose LNP nucleic acid delivery",
        "hypothesis": (
            "PEG-lipid desorption kinetics and anti-PEG IgM jointly dominate accelerated blood "
            "clearance on redosing; tunable PEG-lipid anchors can restore multi-dose exposure."
        ),
        "experiments": [
            "Vary PEG-lipid anchor length and measure circulation half-life over 3 weekly doses",
            "Quantify anti-PEG antibodies and correlate with clearance",
            "Test alternative stealth polymers (e.g., polysarcosine) as PEG replacements",
        ],
        "readout": "Dose 3 exposure ≥70% of dose 1 AUC for lead formulation.",
        "feasibility": "Standard PK study design; antibody assays commercially available.",
    },
    "immunogenicity": {
        "title": "Decoupling innate immune activation from LNP delivery potency",
        "hypothesis": (
            "Ionizable lipid structure independently drives TLR/inflammasome activation versus "
            "endosomal escape; lipids can be optimized for high delivery with low reactogenicity."
        ),
        "experiments": [
            "Screen ionizable lipids for IL-6/IFN reporter activation in vitro",
            "Correlate innate activation with endosomal escape efficiency",
            "Validate low-inflammation high-potency candidates in mice",
        ],
        "readout": "≥2× potency/inflammation ratio vs SM-102 or MC3 reference LNPs.",
        "feasibility": "Cell reporter assays are accessible; in vivo cytokine panels standard.",
    },
    "delivery_efficiency": {
        "title": "Quantitative bottleneck analysis of the LNP delivery cascade",
        "hypothesis": (
            "Endosomal escape—not uptake or encapsulation—is the dominant loss term in the "
            "delivery cascade for most clinical-like LNP compositions, and 10× escape gains "
            "are necessary and sufficient for transformative dose reduction."
        ),
        "experiments": [
            "Build a quantitative cascade map (injection→uptake→escape→translation) with barcoded mRNA",
            "Perturb each step independently and measure sensitivity of protein output",
            "Identify the step with highest elasticity for dose reduction",
        ],
        "readout": "Ranked elasticities per cascade step; validated 5× dose reduction via top lever.",
        "feasibility": "Requires careful assay development; high scientific payoff.",
    },
    "hybrid_ncrna": {
        "title": "Payload competition in bifunctional ncRNA–mRNA co-delivery nanoparticles",
        "hypothesis": (
            "When ncRNA and mRNA share a single LNP, endosomal escape capacity is a zero-sum resource; "
            "optimizing mass ratio and staggered release chemistry can restore translation without "
            "sacrificing silencing."
        ),
        "experiments": [
            "Titrate ncRNA:mRNA mass ratios in matched LNPs and measure translation vs knockdown",
            "Use orthogonal barcodes to quantify cytosolic arrival of each payload",
            "Test delayed-release linker designs that temporally separate escape events",
        ],
        "readout": "Identify a ratio/chemistry window with ≥70% of single-payload translation and ≥50% target knockdown.",
        "feasibility": "Standard formulation + reporter assays; moderate complexity.",
    },
    "gene_therapy": {
        "title": "Non-hepatic gene editing via serum-stable hybrid DNA–LNP scaffolds",
        "hypothesis": (
            "DNA-organized ionizable lipid domains improve serum stability and spleen/immune-cell editing "
            "without proportional increases in off-target genomic injury."
        ),
        "experiments": [
            "Vary DNA scaffold fraction and measure serum stability + organ editing rates",
            "Profile off-target indels and innate activation vs standard LNPs",
            "Image endosomal membrane contacts with and without scaffold",
        ],
        "readout": "≥2× extrahepatic editing at matched liver exposure and ≤baseline off-target rate.",
        "feasibility": "Requires editing readouts and careful scaffold manufacturing.",
    },
    "ncrna": {
        "title": "Kinetic gating of bifunctional ncRNA activity until cytosolic arrival",
        "hypothesis": (
            "Structure-switching ncRNA modules that remain inert in endosomes and unfold only in "
            "cytosol can reduce off-target RISC/ADAR engagement and payload interference."
        ),
        "experiments": [
            "Design pH- or redox-gated ncRNA folds and verify switching in vitro",
            "Measure bystander editing/silencing with gated vs static guides after LNP delivery",
            "Correlate single-molecule unfold kinetics with functional on-target rates",
        ],
        "readout": "≥2× on-target/off-target activity ratio vs static bifunctional guides at matched dose.",
        "feasibility": "RNA design + standard delivery assays; structural probing adds moderate complexity.",
    },
    "async_escape": {
        "title": "Cargo-selective endosomal escape timing for co-encapsulated nucleic acids",
        "hypothesis": (
            "mRNA and ncRNA exit endosomes asynchronously because lipid–cargo affinity differs; "
            "tuning affinity can enforce intentional staggered cytosolic arrival for combination therapies."
        ),
        "experiments": [
            "Orthogonal fluorogenic aptamer reporters for dual-cargo cytosolic arrival",
            "Vary ionizable lipid chemistry and measure median arrival-time offsets",
            "Test whether enforced stagger improves bifunctional efficacy windows",
        ],
        "readout": "Controlled arrival offset (≥3 min) with improved dual-payload efficacy vs unsorted co-delivery.",
        "feasibility": "Advanced imaging required; high mechanistic payoff for hybrid designs.",
    },
    "vaccine": {
        "title": "Innate sensing thresholds for multi-antigen nucleic acid vaccines",
        "hypothesis": (
            "Co-formulated multi-antigen mRNA/saRNA vaccines hit an innate activation cliff that "
            "blunts adaptive responses; antigen splitting across particles or staged release can "
            "raise the effective antigen load without exceeding that cliff."
        ),
        "experiments": [
            "Titrate antigen count per LNP vs split multi-particle regimens and measure IFN/IL-6",
            "Correlate innate markers with neutralizing titers across regimens",
            "Test delayed-release co-delivery of adjuvant vs antigen RNA",
        ],
        "readout": "≥2× neutralizing titer at matched total RNA dose without higher systemic cytokines.",
        "feasibility": "Standard vaccine immunology panels; moderate formulation complexity.",
    },
}


def gap_primary_pack(gap: Gap) -> str:
    """Assign a single primary pack so hybrid gaps are not absorbed into LNP mass.

    Priority: hybrid_ncrna > gene_editing > lnp_core > (fallback lnp_core).
    """
    tags = {t.lower() for t in (gap.domain_tags or [])}
    blob = f"{gap.title} {gap.description}".lower()
    # Text cues for hybrid even if tagger missed
    hybrid_cues = (
        "ncrna",
        "non-coding",
        "noncoding",
        "bifunctional",
        "circrna",
        "lncrna",
        "mirna",
        "ribozyme",
        "adar",
        "risc",
        "rna origami",
        "guide rna",
    )
    gene_cues = ("crispr", "cas9", "cas13", "base edit", "gene edit", "indel")

    if tags & PACK_TAG_MEMBERSHIP["hybrid_ncrna"] or any(c in blob for c in hybrid_cues):
        return "hybrid_ncrna"
    if tags & PACK_TAG_MEMBERSHIP["gene_editing"] or any(c in blob for c in gene_cues):
        return "gene_editing"
    if tags & PACK_TAG_MEMBERSHIP["lnp_core"]:
        return "lnp_core"
    return "lnp_core"


def tag_to_pack(tag: str) -> str:
    t = (tag or "").lower()
    for pack, members in PACK_TAG_MEMBERSHIP.items():
        if t in members or t == pack:
            return pack
    return "lnp_core"


def _fallback_template(tag: str) -> dict:
    return {
        "title": f"Addressing open gaps in {tag} for nucleic acid delivery",
        "hypothesis": (
            f"Systematic investigation of {tag}-linked mechanisms will reveal "
            "testable intervention points for improving nucleic acid delivery."
        ),
        "experiments": [
            f"Map literature claims vs evidence for {tag} in LNP/mRNA delivery",
            "Design and test candidate approaches in relevant in vitro models",
            "Validate top candidates in vivo with clear quantitative readouts",
        ],
        "readout": "Pre-registered quantitative improvement over a defined baseline formulation.",
        "feasibility": "Feasible with standard molecular biology and nanoparticle characterization tools.",
    }


@dataclass
class _Candidate:
    tag: str
    pack_id: str
    gaps: list[Gap]
    mean_overall: float
    rank_score: float
    template: dict


def _build_candidates(
    gaps: list[Gap],
    *,
    pack_balance: bool,
) -> list[_Candidate]:
    """Build one candidate topic per domain tag that appears on gaps."""
    # Primary pack assignment reduces hybrid→LNP leakage
    pack_gaps: dict[str, list[Gap]] = defaultdict(list)
    for g in gaps:
        pack_gaps[gap_primary_pack(g)].append(g)

    # Tag clusters: prefer tags that match the gap's primary pack
    domain_clusters: dict[str, list[Gap]] = defaultdict(list)
    for g in gaps:
        pack = gap_primary_pack(g)
        tags = [t.lower() for t in (g.domain_tags or []) if t]
        if not tags:
            tags = [DEFAULT_DOMAIN]
        # Keep only tags belonging to this gap's primary pack; if none, use pack-native default
        pack_members = PACK_TAG_MEMBERSHIP.get(pack, set())
        filtered = [t for t in tags if t in pack_members or tag_to_pack(t) == pack]
        if not filtered:
            # synthetic anchor tag so pack still produces a topic
            filtered = [PACK_SEED_TAG.get(pack, DEFAULT_DOMAIN)]
        for t in filtered:
            domain_clusters[t].append(g)

    # Ensure each non-empty pack has at least one native template cluster
    for pack, gs in pack_gaps.items():
        if not gs:
            continue
        natives = PACK_NATIVE_TEMPLATES.get(pack, set())
        if not any(t in domain_clusters for t in natives):
            seed = PACK_SEED_TAG.get(pack) or (sorted(natives)[0] if natives else DEFAULT_DOMAIN)
            domain_clusters[seed].extend(gs)

    candidates: list[_Candidate] = []
    for tag, gs in domain_clusters.items():
        if not gs:
            continue
        mean_ov = sum(g.overall for g in gs) / len(gs)
        # Coverage term: more supporting gaps → slightly higher rank (capped)
        coverage = min(0.12, 0.02 * len(gs))
        pack = tag_to_pack(tag)
        boost = PACK_SCORE_BOOST.get(pack, 0.0) if pack_balance else 0.0
        # Native-template affinity: hybrid templates get full boost; generic LNP less so
        native = tag in PACK_NATIVE_TEMPLATES.get(pack, set())
        affinity = 0.03 if (pack_balance and native and pack != "lnp_core") else 0.0
        # Novelty/testability blend from gap axes
        mean_nov = sum(g.novelty for g in gs) / len(gs)
        mean_test = sum(g.testability for g in gs) / len(gs)
        axis = 0.15 * mean_nov + 0.10 * mean_test
        rank = mean_ov + coverage + boost + affinity + 0.05 * (axis - 0.5)
        rank = max(0.0, min(1.0, rank))
        tmpl = TEMPLATES.get(tag)
        if tmpl is None and tag == "gene_editing":
            tmpl = TEMPLATES.get("gene_therapy")
        if tmpl is None and tag == "ncrna":
            tmpl = TEMPLATES.get("hybrid_ncrna")
        tmpl = tmpl or _fallback_template(tag)
        candidates.append(
            _Candidate(
                tag=tag,
                pack_id=pack,
                gaps=sorted(gs, key=lambda x: x.overall, reverse=True),
                mean_overall=mean_ov,
                rank_score=rank,
                template=tmpl,
            )
        )
    return candidates


def _select_balanced(
    candidates: list[_Candidate],
    max_topics: int,
    *,
    pack_balance: bool,
    min_per_pack: dict[str, int] | None,
) -> list[_Candidate]:
    """Greedy pack-diverse selection then fill by rank_score."""
    if not candidates:
        return []
    if not pack_balance:
        return sorted(candidates, key=lambda c: c.rank_score, reverse=True)[:max_topics]

    mins = {"hybrid_ncrna": 1, "gene_editing": 0, "lnp_core": 1}
    if min_per_pack:
        mins.update(min_per_pack)

    by_pack: dict[str, list[_Candidate]] = defaultdict(list)
    for c in candidates:
        by_pack[c.pack_id].append(c)
    for pack in by_pack:
        by_pack[pack].sort(key=lambda c: c.rank_score, reverse=True)

    selected: list[_Candidate] = []
    used_titles: set[str] = set()
    used_tags: set[str] = set()

    def _take(c: _Candidate) -> bool:
        title = c.template["title"]
        if title in used_titles or c.tag in used_tags:
            return False
        if len(selected) >= max_topics:
            return False
        used_titles.add(title)
        used_tags.add(c.tag)
        selected.append(c)
        return True

    # Diversity pass: reserve slots for packs that have evidence
    for pack in PACK_PRIORITY:
        need = mins.get(pack, 0)
        if need <= 0:
            continue
        if pack not in by_pack or not by_pack[pack]:
            continue
        taken = 0
        for c in by_pack[pack]:
            if taken >= need:
                break
            if _take(c):
                taken += 1

    # Global fill by rank
    remaining = sorted(candidates, key=lambda c: c.rank_score, reverse=True)
    for c in remaining:
        if len(selected) >= max_topics:
            break
        _take(c)

    return selected


def suggest_topics(
    gaps: list[Gap],
    max_topics: int = 5,
    *,
    pack_balance: bool = True,
    min_per_pack: dict[str, int] | None = None,
) -> list[TopicProposal]:
    """Generate research topic proposals from top gaps with pack-aware ranking.

    When ``pack_balance`` is True (default), hybrid/bifunctional ncRNA and gene-editing
    packs get reserved representation so LNP-core mass does not monopolize top-k.
    """
    if not gaps:
        return []

    candidates = _build_candidates(gaps, pack_balance=pack_balance)
    chosen = _select_balanced(
        candidates,
        max_topics=max_topics,
        pack_balance=pack_balance,
        min_per_pack=min_per_pack,
    )

    proposals: list[TopicProposal] = []
    for c in chosen:
        gap_ids = [g.id for g in c.gaps[:3]]
        # Display priority stays on scientific score (mean overall), not boost
        display_priority = round(min(1.0, c.mean_overall), 2)
        pack_note = f"pack={c.pack_id}"
        balance_note = (
            f"rank={c.rank_score:.2f} (pack-balanced)"
            if pack_balance
            else f"rank={c.rank_score:.2f}"
        )
        domain_tags = [c.tag]
        if c.pack_id not in domain_tags:
            domain_tags.append(c.pack_id)

        proposals.append(
            TopicProposal(
                title=c.template["title"][:200],
                hypothesis=c.template["hypothesis"],
                gap_ids=gap_ids,
                proposed_experiments=list(c.template["experiments"]),
                expected_readout=c.template["readout"],
                feasibility_notes=c.template["feasibility"],
                impact_rationale=(
                    f"Addresses {len(gap_ids)} scored gaps in '{c.tag}' "
                    f"({pack_note}, cluster mean overall={c.mean_overall:.2f}, {balance_note}). "
                    "Success would advance therapeutically relevant nucleic acid delivery "
                    "and/or hybrid ncRNA mechanisms."
                ),
                priority=display_priority,
                domain_tags=domain_tags,
                pack_id=c.pack_id,
                rank_score=round(c.rank_score, 4),
            )
        )

    # Stable sort: rank_score desc, then priority, then title
    proposals.sort(key=lambda t: (t.rank_score, t.priority, t.title), reverse=True)
    logger.info(
        "Generated %d topic proposals from %d gaps (pack_balance=%s; packs=%s)",
        len(proposals),
        len(gaps),
        pack_balance,
        {p.pack_id: 1 for p in proposals},
    )
    return proposals
