"""Research topic proposals from scored gaps."""

from __future__ import annotations

import logging

from src.models import Gap, TopicProposal

logger = logging.getLogger(__name__)

DEFAULT_DOMAIN = "lnp"

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
}


def suggest_topics(gaps: list[Gap], max_topics: int = 5) -> list[TopicProposal]:
    """Generate research topic proposals from top gaps, clustered by domain tags."""
    if not gaps:
        return []

    domain_clusters: dict[str, list[Gap]] = {}
    for gap in gaps:
        tags = gap.domain_tags or [DEFAULT_DOMAIN]
        for tag in tags:
            domain_clusters.setdefault(tag, []).append(gap)

    cluster_scores = {
        tag: sum(g.overall for g in gs) / len(gs) for tag, gs in domain_clusters.items()
    }
    sorted_clusters = sorted(cluster_scores.items(), key=lambda x: x[1], reverse=True)

    proposals: list[TopicProposal] = []
    used_titles: set[str] = set()

    for tag, avg_score in sorted_clusters:
        if len(proposals) >= max_topics:
            break
        template = TEMPLATES.get(
            tag,
            {
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
            },
        )
        title = template["title"]
        if title in used_titles:
            continue
        used_titles.add(title)

        gap_ids = [g.id for g in domain_clusters[tag][:3]]
        proposals.append(
            TopicProposal(
                title=title[:200],
                hypothesis=template["hypothesis"],
                gap_ids=gap_ids,
                proposed_experiments=list(template["experiments"]),
                expected_readout=template["readout"],
                feasibility_notes=template["feasibility"],
                impact_rationale=(
                    f"Addresses {len(gap_ids)} scored gaps in '{tag}' "
                    f"(cluster mean overall={avg_score:.2f}). "
                    "Success would advance therapeutically relevant nucleic acid delivery."
                ),
                priority=round(avg_score, 2),
                domain_tags=[tag],
            )
        )

    proposals.sort(key=lambda t: t.priority, reverse=True)
    logger.info("Generated %d topic proposals from %d gaps", len(proposals), len(gaps))
    return proposals
