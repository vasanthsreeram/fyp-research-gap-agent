"""Quote-grounded argument mining (Stage 3): extract argumentative units with
citation cues from paper text and detect explicit cross-paper support/attack
relations — beyond the stance-lexicon proxy in `tension.py`.

Every mined unit carries a `quote_span` that must literally appear in the
source paper text (memorization-safe) plus `cite_markers` for grounding cues
(author-year, DOI, arXiv, bracket numbers, "prior work" phrases).

This is a deterministic, dependency-light pass designed to run offline on
fixture abstracts (and later full-text). It complements (not replaces) the
LLM claim extractor and the heuristic tension pass.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional

from src.models import (
    ArgumentRelation,
    ArgumentRelationKind,
    ArgumentRole,
    ArgumentUnit,
    CiteMarker,
    CiteMarkerKind,
    Claim,
    Evidence,
    Gap,
    GapKind,
    Paper,
)

logger = logging.getLogger(__name__)

# Role cue lexicons -----------------------------------------------------------
_SUPPORT_VERBS = {
    "demonstrat",
    "show",
    "confirm",
    "establish",
    "prove",
    "achieve",
    "enable",
    "improve",
    "increase",
    "reduce",
    "reveal",
    "indicate",
    "support",
}
_LIMIT_VERBS = {
    "limit",
    "limitation",
    "bottleneck",
    "fail",
    "hinder",
    "impede",
    "prevent",
    "remain",
    "poorly",
    "unknown",
    "unclear",
    "elusive",
    "challenging",
    "challenge",
    "obstacle",
    "barrier",
    "insufficient",
    "unable",
    "cannot",
    "modest",
    "partial",
    "incomplete",
    "controversial",
    "inconsisten",
    "contradict",
    "debate",
    "hedge",
}
_MECH_VERBS = {
    "mechanism",
    "via",
    "through",
    "mediated",
    "dependent",
    "pathway",
    "machinery",
    "binds",
    "binding",
    "interaction",
    "uptake",
    "trafficking",
    "kinetics",
    "conformation",
    "structural",
    "stability",
}
_WARRANT_WORDS = {
    "assume",
    "assuming",
    "assumption",
    "in principle",
    "if",
    "provided that",
    "underlying",
    "bridge",
}
_HEDGE_WORDS = {
    "may",
    "might",
    "could",
    "suggest",
    "possibly",
    "likely",
    "potentially",
    "suggests that",
}

# Citation / prior-work cue patterns ------------------------------------------
_DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.I)
_ARXIV_RE = re.compile(
    r"\barXiv\s*:\s*(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?", re.I
)
_AUTHOR_YEAR_RE = re.compile(
    r"\b([A-Z][A-Za-z'`-]+(?:\s+et\s+al\.?)?)\s*\((\d{4}[a-z]?)\)", re.I
)
_BRACKET_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
_ET_AL_RE = re.compile(r"\bet\s+al\.?", re.I)
_PRIOR_WORK_RE = re.compile(
    r"\b(prior work|previous (?:studies?|work|reports?)|earlier (?:studies?|reports?)|"
    r"as reported|as shown|as described|it has been (?:shown|reported|demonstrated)|"
    r"recent studies?)\b",
    re.I,
)

# Explicit relational connectors (sentence-level heuristics)
_ATTACK_CONNECTORS = [
    "however",
    "in contrast",
    "contrary to",
    "conflicts with",
    "contradicts",
    "disputes",
    "challenges",
    "but",
    "yet",
    "nevertheless",
    "whereas",
    "refutes",
    "questions",
]
_SUPPORT_CONNECTORS = [
    "consistent with",
    "in agreement with",
    "supports",
    "support",
    "corroborates",
    "aligns with",
    "confirming",
    "as shown by",
    "in line with",
    "evidence for",
    "in support of",
    "lends support",
]

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Lower-cased connector match (avoids "but" at sentence start accidentally
# triggering when scanning; we still require the token to appear).
_ATTACK_TOKENS = {c: c.lower() for c in _ATTACK_CONNECTORS}
_SUPPORT_TOKENS = {c: c.lower() for c in _SUPPORT_CONNECTORS}


def _norm_quote(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _contains_any(text: str, cues: Iterable[str]) -> bool:
    low = text.lower()
    return any(cue.lower() in low for cue in cues)


def role_from_text(text: str) -> ArgumentRole:
    """Pick a role from surface cues: limitation > mechanism > warrant > assertion."""
    low = text.lower()
    if _contains_any(text, _HEDGE_WORDS) and _contains_any(text, _LIMIT_VERBS):
        return ArgumentRole.LIMITATION
    if _contains_any(text, _LIMIT_VERBS):
        return ArgumentRole.LIMITATION
    if _contains_any(text, _MECH_VERBS):
        return ArgumentRole.MECHANISM
    if _contains_any(text, _WARRANT_WORDS):
        return ArgumentRole.WARRANT
    if _contains_any(text, _SUPPORT_VERBS):
        return ArgumentRole.SUPPORT
    return ArgumentRole.ASSERTION


def find_cite_markers(sentence: str) -> list[CiteMarker]:
    """Extract lightweight citation cues from a sentence (no resolution)."""
    markers: list[CiteMarker] = []
    for m in _DOI_RE.finditer(sentence):
        markers.append(
            CiteMarker(kind=CiteMarkerKind.DOI, text=m.group(0), target=m.group(0))
        )
    for m in _ARXIV_RE.finditer(sentence):
        markers.append(
            CiteMarker(
                kind=CiteMarkerKind.ARXIV,
                text=m.group(0),
                target=m.group(0).split(":", 1)[-1].strip(),
            )
        )
    for m in _AUTHOR_YEAR_RE.finditer(sentence):
        markers.append(
            CiteMarker(
                kind=CiteMarkerKind.AUTHOR_YEAR,
                text=m.group(0),
                target=m.group(0),
            )
        )
    for m in _BRACKET_RE.finditer(sentence):
        markers.append(
            CiteMarker(
                kind=CiteMarkerKind.BRACKET_NUM,
                text=m.group(0),
                target=m.group(1),
            )
        )
    if _ET_AL_RE.search(sentence):
        markers.append(CiteMarker(kind=CiteMarkerKind.ET_AL, text="et al."))
    if _PRIOR_WORK_RE.search(sentence):
        markers.append(CiteMarker(kind=CiteMarkerKind.PRIOR_WORK, text="prior work"))
    return markers


def _sentence_role(sentence: str) -> ArgumentRole:
    return role_from_text(sentence)


def mine_argument_units(
    papers: list[Paper],
    claims: Optional[list[Claim]] = None,
    evidence: Optional[list[Evidence]] = None,
    *,
    min_sentence_chars: int = 40,
    max_units_per_paper: int = 8,
) -> list[ArgumentUnit]:
    """Split each paper's text into sentences and mine argument units.

    Uses Paper.text_blob() (full text when attached, else abstract). Full-text
    papers automatically allow more units so body sections contribute.
    Units are quote-grounded (quote_span is the normalized sentence) and carry
    role + citation markers. Claim/evidence provenance is attached when an
    exact quote match exists.
    """
    units: list[ArgumentUnit] = []
    if claims:
        claim_by_quote: dict[str, list[Claim]] = defaultdict(list)
        for c in claims:
            if c.quote_span:
                claim_by_quote[_norm_quote(c.quote_span)].append(c)
    else:
        claim_by_quote = {}
    if evidence:
        ev_by_quote: dict[str, list[Evidence]] = defaultdict(list)
        for e in evidence:
            if e.quote_span:
                ev_by_quote[_norm_quote(e.quote_span)].append(e)
    else:
        ev_by_quote = {}

    for p in papers:
        blob = p.text_blob()
        if not blob:
            continue
        # Full-text body is denser — raise unit budget so Methods/Results/Limitations appear.
        paper_cap = max_units_per_paper
        if p.has_full_text() and max_units_per_paper <= 8:
            paper_cap = 16
        # Work paragraph-wise so the title never merges with abstract sentences.
        paragraphs = [para.strip() for para in re.split(r"\n+", blob) if para.strip()]
        title = (p.title or "").strip()
        # Prefer body section order when available (results/limitations first for dialectic density)
        if p.sections:
            priority = {
                "limitations": 0,
                "discussion": 1,
                "results": 2,
                "conclusion": 3,
                "introduction": 4,
                "methods": 5,
                "abstract": 6,
            }
            ordered = sorted(
                [s for s in p.sections if (s.text or "").strip()],
                key=lambda s: priority.get(s.kind.value, 9),
            )
            if ordered:
                paragraphs = [s.text.strip() for s in ordered]
        taken = 0
        for para in paragraphs:
            if taken >= paper_cap:
                break
            if para == title:
                continue  # titles are not argumentative units with citation cues
            for sent in [s.strip() for s in _SENT_SPLIT.split(para) if s.strip()]:
                if taken >= paper_cap:
                    break
                if len(sent) < min_sentence_chars:
                    continue
                role = _sentence_role(sent)
                markers = find_cite_markers(sent)
                q = _norm_quote(sent)
                unit = ArgumentUnit(
                    paper_id=p.id,
                    role=role,
                    text=sent,
                    quote_span=q,
                    confidence=0.6 if markers else 0.45,
                    tags=[],
                    cite_markers=markers,
                    extractor="argmine",
                )
                matches = claim_by_quote.get(q, [])
                if matches:
                    unit.claim_id = matches[0].id
                ev_matches = ev_by_quote.get(q, [])
                if ev_matches:
                    unit.evidence_id = ev_matches[0].id
                units.append(unit)
                taken += 1
    logger.info("Mined %d argument units from %d papers", len(units), len(papers))
    return units


def _tokens(text: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-z]{3,}", (text or "").lower())
        if len(t) > 2
    }


def _unit_similarity(a: ArgumentUnit, b: ArgumentUnit) -> float:
    """Token Jaccard between unit texts (cheap; offline-first)."""
    ta, tb = _tokens(a.text), _tokens(b.text)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _unit_has_polarity(unit: ArgumentUnit) -> bool:
    """True for LIMITATION / REBUTTAL (negative pole) or SUPPORT (positive)."""
    return unit.role in (ArgumentRole.LIMITATION, ArgumentRole.REBUTTAL) or unit.role in (
        ArgumentRole.SUPPORT,
    )


def _connector_kind(a: ArgumentUnit, b: ArgumentUnit) -> Optional[ArgumentRelationKind]:
    """Guess support vs attack from connector cues in the *attacking* unit text."""
    low = (a.text or "").lower()
    for tok in _SUPPORT_TOKENS.values():
        if tok in low:
            return ArgumentRelationKind.SUPPORT
    for tok in _ATTACK_TOKENS.values():
        if tok in low:
            return ArgumentRelationKind.ATTACK
    return None


_CONTRADICTION_VERBS = (
    "contradict",
    "refute",
    "dispute",
    "challenge",
    "conflict with",
    "in contrast",
    "contrary to",
    "disagrees",
)


def _has_contradiction(text: str) -> bool:
    """Explicit contradiction cues (stronger than generic 'however')."""
    low = (text or "").lower()
    return any(v in low for v in _CONTRADICTION_VERBS)


def find_argument_relations(
    units: list[ArgumentUnit],
    *,
    sim_threshold: float = 0.22,
    same_paper_ok: bool = False,
    max_relations: int = 40,
) -> list[ArgumentRelation]:
    """Pair units (cross-paper by default) that share topic tokens and show a
    role polarity difference or explicit connector — producing support/attack
    edges with a similarity and rationale.
    """
    relations: list[ArgumentRelation] = []
    n = len(units)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = units[i], units[j]
            if not same_paper_ok and a.paper_id == b.paper_id:
                continue
            sim = _unit_similarity(a, b)
            if sim < sim_threshold:
                continue
            # Require at least one polarity-bearing unit
            if not (_unit_has_polarity(a) or _unit_has_polarity(b)):
                continue
            kind = None
            conn = None
            a_neg = a.role in (ArgumentRole.LIMITATION, ArgumentRole.REBUTTAL)
            b_neg = b.role in (ArgumentRole.LIMITATION, ArgumentRole.REBUTTAL)
            a_pos = a.role in (ArgumentRole.SUPPORT, ArgumentRole.ASSERTION)
            b_pos = b.role in (ArgumentRole.SUPPORT, ArgumentRole.ASSERTION)
            if a_neg and b_neg:
                # Both limitations on the same topic: corroboration, unless an
                # explicit contradiction verb is present.
                if _has_contradiction(a.text) or _has_contradiction(b.text):
                    kind = ArgumentRelationKind.ATTACK
                else:
                    kind = ArgumentRelationKind.SUPPORT
            elif a_pos and b_pos:
                # Both positive on the same topic: agreement/support.
                kind = ArgumentRelationKind.SUPPORT
            else:
                # Opposite poles (limitation vs support/assertion): tension,
                # unless an explicit agreement connector is present.
                conn = _connector_kind(a, b) or _connector_kind(b, a)
                if conn == ArgumentRelationKind.SUPPORT:
                    kind = ArgumentRelationKind.SUPPORT
                else:
                    kind = ArgumentRelationKind.ATTACK
            if kind is None:
                continue
            # Source = the unit doing the attacking/supporting (connector side)
            if conn and _connector_kind(a, b) is not None:
                src, tgt = a, b
            elif conn and _connector_kind(b, a) is not None:
                src, tgt = b, a
            elif a_neg and not b_neg:
                src, tgt = a, b
            elif b_neg and not a_neg:
                src, tgt = b, a
            else:
                src, tgt = a, b
            if src.paper_id == tgt.paper_id and not same_paper_ok:
                continue
            rationale = (
                f"{src.role.value} unit '{src.text[:70]}…' "
                f"{'attacks' if kind == ArgumentRelationKind.ATTACK else 'supports'} "
                f"'{tgt.text[:70]}…' (sim={sim:.2f})"
            )
            relations.append(
                ArgumentRelation(
                    source_id=src.id,
                    target_id=tgt.id,
                    kind=kind,
                    similarity=round(sim, 3),
                    rationale=rationale,
                    paper_ids=sorted({src.paper_id, tgt.paper_id}),
                )
            )
            if len(relations) >= max_relations:
                break
        if len(relations) >= max_relations:
            break
    relations.sort(key=lambda r: r.similarity, reverse=True)
    logger.info("Argument relations: %d (sim>=%.2f)", len(relations), sim_threshold)
    return relations


@dataclass
class ArgumentGraph:
    units: list[ArgumentUnit] = field(default_factory=list)
    relations: list[ArgumentRelation] = field(default_factory=list)
    attacks: list[ArgumentRelation] = field(default_factory=list)
    supports: list[ArgumentRelation] = field(default_factory=list)

    @property
    def n_units(self) -> int:
        return len(self.units)

    @property
    def n_relations(self) -> int:
        return len(self.relations)

    @property
    def n_attack(self) -> int:
        return len(self.attacks)

    @property
    def n_support(self) -> int:
        return len(self.supports)


def build_argument_graph(
    papers: list[Paper],
    claims: Optional[list[Claim]] = None,
    evidence: Optional[list[Evidence]] = None,
    *,
    sim_threshold: float = 0.22,
    max_units_per_paper: int = 8,
    max_relations: int = 40,
) -> ArgumentGraph:
    """Mine units, then relations, and partition by kind."""
    units = mine_argument_units(
        papers,
        claims,
        evidence,
        max_units_per_paper=max_units_per_paper,
    )
    relations = find_argument_relations(
        units,
        sim_threshold=sim_threshold,
        max_relations=max_relations,
    )
    attacks = [r for r in relations if r.kind == ArgumentRelationKind.ATTACK]
    supports = [r for r in relations if r.kind == ArgumentRelationKind.SUPPORT]
    return ArgumentGraph(units=units, relations=relations, attacks=attacks, supports=supports)


def graph_to_gaps(
    graph: ArgumentGraph,
    papers: list[Paper],
    *,
    max_gaps: int = 10,
) -> list[Gap]:
    """Convert attack relations into gap records (ARGUE_MINED_CONFLICT)."""
    if not graph.attacks:
        return []
    paper_map = {p.id: p for p in papers}
    unit_map = {u.id: u for u in graph.units}
    gaps: list[Gap] = []

    for rel in list(graph.attacks)[:max_gaps]:
        src = unit_map.get(rel.source_id)
        tgt = unit_map.get(rel.target_id)
        if not src or not tgt:
            continue
        src_paper = paper_map.get(src.paper_id)
        tgt_paper = paper_map.get(tgt.paper_id)
        src_title = (src_paper.title or "unknown")[:60] if src_paper else "unknown"
        tgt_title = (tgt_paper.title or "unknown")[:60] if tgt_paper else "unknown"
        years = sorted(
            y
            for y in (
                src_paper.year if src_paper else None,
                tgt_paper.year if tgt_paper else None,
            )
            if y
        )
        year_span = ""
        if years:
            year_span = f" ({min(years)}–{max(years)})" if len(years) == 2 and years[0] != years[1] else f" ({years[0]})"

        title = f"Cite-grounded conflict: {src.text[:70]}"
        description = (
            f"Mined argument units{year_span}: attack by '{src.role.value}' unit in "
            f"[{src_title}] on '{tgt.role.value}' unit in [{tgt_title}]. "
            f"Similarity={rel.similarity:.2f}. "
            f"Source quote: \"{src.quote_span[:220]}\". "
            f"Target quote: \"{tgt.quote_span[:220]}\"."
        )
        domain_tags: list[str] = []
        # Reuse domain tagger if available (keeps consistency with gap pipeline)
        try:
            from src.gap.score import tag_domains

            blob = f"{src.text} {tgt.text}"
            domain_tags = tag_domains(blob)
        except Exception:
            pass
        gaps.append(
            Gap(
                kind=GapKind.ARGUE_MINED_CONFLICT,
                title=title[:200],
                description=description[:700],
                claim_ids=[c for c in (src.claim_id, tgt.claim_id) if c],
                evidence_ids=[],
                paper_ids=list(rel.paper_ids),
                magnitude=0.8,
                novelty=0.85,
                testability=0.7,
                impact=0.7,
                overall=0.76,
                domain_tags=domain_tags,
                rationale=(
                    f"Argue-mined conflict: {src.role.value} unit (paper {src.paper_id}) "
                    f"attacks {tgt.role.value} unit (paper {tgt.paper_id}); "
                    f"sim={rel.similarity:.2f}, grounded quotes attached."
                ),
                argument_unit_ids=[src.id, tgt.id],
                argument_relation_ids=[rel.id],
                grounded_quotes=[src.quote_span, tgt.quote_span],
            )
        )
    return gaps


def argument_markdown(
    graph: ArgumentGraph,
    papers: list[Paper],
    *,
    top_relations: int = 8,
) -> str:
    """Human-readable report section for the mined argument graph."""
    paper_map = {p.id: p for p in papers}
    lines: list[str] = []
    lines += [
        "## Cite-grounded argument mining",
        "",
        f"- **Units**: {graph.n_units} · **Relations**: {graph.n_relations} "
        f"(**{graph.n_attack}** attack, **{graph.n_support}** support)",
        f"- Roles: " + ", ".join(
            f"{r}={sum(1 for u in graph.units if u.role == r)}" for r in ArgumentRole
        ),
        "",
        "### Top relations",
        "",
    ]
    for rel in graph.relations[:top_relations]:
        src = next((u for u in graph.units if u.id == rel.source_id), None)
        tgt = next((u for u in graph.units if u.id == rel.target_id), None)
        if not src or not tgt:
            continue
        sp = paper_map.get(src.paper_id)
        tp = paper_map.get(tgt.paper_id)
        lines += [
            f"- **{rel.kind.value.upper()}** (sim={rel.similarity:.2f}): "
            f"[{sp.title[:40] if sp else src.paper_id}] "
            f"'{src.text[:110]}' → "
            f"[{tp.title[:40] if tp else tgt.paper_id}] "
            f"'{tgt.text[:110]}'",
            f"  - Quotes: `{src.quote_span[:100]}` / `{tgt.quote_span[:100]}`",
            "",
        ]
    return "\n".join(lines)


def save_argument_report(graph: ArgumentGraph, papers: list[Paper], path) -> None:
    """Write the argument report markdown to a path (reports/argument_graph.md)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    md = argument_markdown(graph, papers)
    md += "\n### All mined units\n\n"
    for u in graph.units:
        cites = ", ".join(f"{m.kind.value}:{m.text}" for m in u.cite_markers[:4])
        lines = [f"- `{u.id}` **{u.role.value}** ({u.paper_id}): {u.text[:160]}"]
        if cites:
            lines.append(f"  - cites: {cites}")
        md += "\n".join(lines) + "\n"
    path.write_text(md)
