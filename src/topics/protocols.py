"""Structured experiment protocol cards from topic proposals.

Turns high-level experiment bullets into a mini protocol a student/lab
could actually discuss: aim, controls, assay panel, success criteria,
timeline, risks, and stop rules — aligned with supervisor 'testable' bar.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from src.models import ExperimentProtocol, Gap, TopicProposal

logger = logging.getLogger(__name__)

# Pack-specific assay / control priors (prototype templates — not wet-lab SOPs)
_PACK_ASSAYS: dict[str, list[str]] = {
    "hybrid_ncrna": [
        "Dual-payload encapsulation efficiency (RiboGreen / fluorophore orthogonal labels)",
        "Translation (luciferase or NanoLuc) and target knockdown (RT-qPCR / western) in same wells",
        "Cytosolic arrival reporters (split-fluorophore or aptamer) for each cargo",
        "RISC loading / Ago2 IP for ncRNA arm; ribosome profiling optional for mRNA arm",
        "Cell viability + IFN/ISG panel (CXCL10, IFIT1) for innate cost",
    ],
    "gene_editing": [
        "On-target indel / base-conversion rate (NGS amplicon)",
        "Off-target panel (guided SITE-seq subset or in silico top-N NGS)",
        "Serum stability (incubation + gel / encapsulation retention)",
        "Organ editing biodistribution (qPCR of edit + cargo) at 48–72 h",
        "Innate activation (IL-6, IFN-α) vs matched empty LNP",
    ],
    "lnp_core": [
        "Size / PDI / zeta (DLS) and encapsulation efficiency",
        "In vitro transfection across ≥3 cell types (hepato, endo, immune)",
        "Endosomal escape proxy (galectin puncta or calcein release)",
        "In vivo reporter biodistribution (liver vs extrahepatic organs)",
        "Repeat-dose PK / anti-PEG IgM if multi-dose claim",
    ],
}

_PACK_CONTROLS: dict[str, list[str]] = {
    "hybrid_ncrna": [
        "Single-payload mRNA-only LNP (matched total RNA mass)",
        "Single-payload ncRNA-only LNP",
        "Scrambled ncRNA + mRNA co-LNP",
        "Vehicle / empty LNP and untreated cells",
    ],
    "gene_editing": [
        "Cas/base-editor mRNA only (no guide)",
        "Guide only (no editor)",
        "Standard clinical-like ionizable LNP reference (e.g. SM-102 or MC3 class)",
        "Isotype / non-targeting guide control",
    ],
    "lnp_core": [
        "Clinical-like reference LNP (SM-102 or MC3 class) at matched dose",
        "Non-ionizable lipid control particle",
        "Free nucleic acid (no particle)",
        "Vehicle-only",
    ],
}

_PACK_RISKS: dict[str, list[str]] = {
    "hybrid_ncrna": [
        "Payload competition confounds ratio titration if encapsulation is uneven",
        "Orthogonal reporters may themselves compete for escape capacity",
        "Innate activation from dual RNA may mask true efficacy windows",
    ],
    "gene_editing": [
        "Low edit rates in extrahepatic tissue may require large cohorts",
        "Off-target assays under-sample rare sites",
        "DNA scaffold manufacturing lot variability",
    ],
    "lnp_core": [
        "In vitro transfection poorly predicts in vivo tropism",
        "Protein corona differs across serum lots / species",
        "Microscopy endosomal-escape assays are low-throughput and operator-sensitive",
    ],
}

_DEFAULT_TIMELINE = [
    "Week 0–1: freeze hypothesis, SOPs, power calc, preregister primary readout",
    "Week 2–4: formulation library + QC (size, EE%, endotoxin)",
    "Week 5–7: in vitro screen with full control set; down-select top 3–5",
    "Week 8–11: in vivo pilot (n small) on top candidates + reference",
    "Week 12: stats, failure analysis, decide kill / expand / redesign",
]


def _pack_of(topic: TopicProposal) -> str:
    pid = (topic.pack_id or "").strip().lower()
    if pid in _PACK_ASSAYS:
        return pid
    tags = {t.lower() for t in (topic.domain_tags or [])}
    if tags & {"hybrid_ncrna", "ncrna", "async_escape"}:
        return "hybrid_ncrna"
    if tags & {"gene_editing", "gene_therapy"}:
        return "gene_editing"
    return "lnp_core"


def _primary_aim(topic: TopicProposal) -> str:
    hyp = (topic.hypothesis or "").strip()
    if hyp:
        # First clause as aim
        piece = re.split(r"[.;]", hyp, maxsplit=1)[0].strip()
        if len(piece) > 40:
            return f"Test whether {piece[0].lower()}{piece[1:]}"[:400]
    return f"Test the core claim of: {topic.title}"[:400]


def _success_criteria(topic: TopicProposal) -> list[str]:
    criteria: list[str] = []
    readout = (topic.expected_readout or "").strip()
    if readout:
        criteria.append(f"Primary: {readout}")
    # Extract simple quantitative hints (≥, ≤, ×, %)
    nums = re.findall(
        r"(?:≥|<=|≤|>=|~)?\s*\d+(?:\.\d+)?\s*(?:×|x|%|fold)?",
        readout,
        flags=re.I,
    )
    if nums:
        criteria.append(
            "Pre-register binary pass if primary numeric threshold is met "
            f"with the study's planned analysis (hints in readout: {', '.join(nums[:4])})."
        )
    else:
        criteria.append(
            "Pre-register a binary pass/fail on the primary readout vs reference LNP "
            "before unblinding in vivo arms."
        )
    criteria.append(
        "Secondary: no worse than reference on pre-specified safety panel "
        "(viability drop ≤20% in vitro; no unexpected grade of systemic cytokines in vivo)."
    )
    criteria.append(
        "Replicates: ≥3 independent formulations for in vitro; in vivo n powered for primary effect size."
    )
    return criteria


def _stop_rules(topic: TopicProposal) -> list[str]:
    return [
        "Stop expansion if lead fails primary readout in two independent formulation lots.",
        "Stop in vivo if acute reactogenicity exceeds reference by pre-set cytokine fold-change.",
        "Redesign (do not force dose escalation) if QC (PDI>0.3 or EE%<70%) is unstable across lots.",
        f"Kill criterion tied to feasibility note: {(topic.feasibility_notes or 'resource/time overrun')[:160]}",
    ]


def _materials_skeleton(topic: TopicProposal, pack: str) -> list[str]:
    base = [
        "Ionizable lipid + helper + cholesterol + PEG-lipid set (or pack-specific scaffold)",
        "Reporter / therapeutic nucleic acid cargo (sequence-verified)",
        "Reference clinical-like LNP reagents",
        "Cell lines relevant to claim + serum for corona / stability assays",
    ]
    if pack == "hybrid_ncrna":
        base.insert(1, "Orthogonal ncRNA + mRNA payloads with distinct barcodes/labels")
    if pack == "gene_editing":
        base.insert(1, "Editor mRNA + gRNA (and optional DNA scaffold)")
    # Pull any concrete chemicals mentioned in experiment bullets
    for exp in topic.proposed_experiments or []:
        if re.search(r"\b(FRET|cryo-ET|proteomics|flow cytometry|NGS)\b", exp, re.I):
            base.append(f"Capability: {exp[:120]}")
    # Dedupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for m in base:
        k = m.lower()
        if k not in seen:
            seen.add(k)
            out.append(m)
    return out[:8]


def build_protocol(
    topic: TopicProposal,
    *,
    gaps: Optional[list[Gap]] = None,
) -> ExperimentProtocol:
    """Build one structured protocol card from a topic (+ optional supporting gaps)."""
    pack = _pack_of(topic)
    gap_map = {g.id: g for g in (gaps or [])}
    linked = [gap_map[i] for i in (topic.gap_ids or []) if i in gap_map]

    rationale_bits = [
        f"Derived from topic '{topic.title}' (pack={pack}, priority={topic.priority:.2f})."
    ]
    if linked:
        top = linked[0]
        rationale_bits.append(
            f"Anchored on gap [{top.kind.value}] '{top.title[:120]}' "
            f"(overall={top.overall:.2f}, testability={top.testability:.2f})."
        )
    if topic.impact_rationale:
        rationale_bits.append(topic.impact_rationale[:240])

    steps = list(topic.proposed_experiments or [])
    if not steps:
        steps = [
            "Define primary quantitative readout and reference formulation",
            "Build focused formulation matrix and complete QC",
            "Run in vitro screen with full controls",
            "Validate top candidates in a powered in vivo pilot",
        ]

    proto = ExperimentProtocol(
        topic_id=topic.id,
        title=f"Protocol: {topic.title}"[:220],
        pack_id=pack,
        primary_aim=_primary_aim(topic),
        hypothesis=topic.hypothesis or "",
        steps=steps,
        controls=list(_PACK_CONTROLS.get(pack, _PACK_CONTROLS["lnp_core"])),
        assay_panel=list(_PACK_ASSAYS.get(pack, _PACK_ASSAYS["lnp_core"])),
        materials=_materials_skeleton(topic, pack),
        success_criteria=_success_criteria(topic),
        stop_rules=_stop_rules(topic),
        timeline_weeks=list(_DEFAULT_TIMELINE),
        risks=list(_PACK_RISKS.get(pack, _PACK_RISKS["lnp_core"])),
        gap_ids=list(topic.gap_ids or []),
        domain_tags=list(topic.domain_tags or []),
        feasibility_notes=topic.feasibility_notes or "",
        expected_readout=topic.expected_readout or "",
        rationale=" ".join(rationale_bits),
    )
    return proto


def build_protocols(
    topics: list[TopicProposal],
    *,
    gaps: Optional[list[Gap]] = None,
    max_protocols: int = 5,
) -> list[ExperimentProtocol]:
    """Build protocol cards for top topics (already rank-sorted preferred)."""
    out: list[ExperimentProtocol] = []
    for t in topics[: max(0, max_protocols)]:
        out.append(build_protocol(t, gaps=gaps))
    logger.info("Built %d experiment protocol cards from %d topics", len(out), len(topics))
    return out


def protocols_to_markdown(protocols: list[ExperimentProtocol]) -> str:
    """Standalone markdown for reports/protocols_latest.md."""
    lines = [
        "# Experiment protocol cards",
        "",
        "_Prototype structured protocols derived from topic proposals. "
        "Not wet-lab SOPs — for design discussion and preregistration sketches._",
        "",
    ]
    if not protocols:
        lines.append("_No protocols._")
        return "\n".join(lines)

    for i, p in enumerate(protocols, 1):
        lines += [
            f"## {i}. {p.title}",
            f"- **ID**: `{p.id}` · **topic**: `{p.topic_id}` · **pack**: `{p.pack_id or '—'}`",
            f"- **Primary aim**: {p.primary_aim}",
            f"- **Hypothesis**: {p.hypothesis}",
            f"- **Expected readout**: {p.expected_readout or '—'}",
            "",
            "### Steps",
        ]
        for j, s in enumerate(p.steps, 1):
            lines.append(f"{j}. {s}")
        lines += ["", "### Controls"]
        for c in p.controls:
            lines.append(f"- {c}")
        lines += ["", "### Assay panel"]
        for a in p.assay_panel:
            lines.append(f"- {a}")
        lines += ["", "### Success criteria"]
        for s in p.success_criteria:
            lines.append(f"- {s}")
        lines += ["", "### Stop rules"]
        for s in p.stop_rules:
            lines.append(f"- {s}")
        lines += ["", "### Timeline"]
        for t in p.timeline_weeks:
            lines.append(f"- {t}")
        lines += ["", "### Risks"]
        for r in p.risks:
            lines.append(f"- {r}")
        if p.materials:
            lines += ["", "### Materials (skeleton)"]
            for m in p.materials:
                lines.append(f"- {m}")
        if p.feasibility_notes:
            lines += ["", f"**Feasibility:** {p.feasibility_notes}"]
        if p.rationale:
            lines += ["", f"**Rationale:** {p.rationale}"]
        lines.append("")
    return "\n".join(lines)
