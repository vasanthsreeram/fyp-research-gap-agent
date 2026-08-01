"""Cross-paper claim tension: multi-paper dialectics beyond single-paper gaps.

Surfaces clusters where related claims across ≥2 papers pull in different
directions (support vs limitation / hedge / contradiction keywords), scoring
them as high-novelty, experimentally rich open problems.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Optional

from src.models import Claim, Evidence, EvidenceType, Gap, GapKind, Paper

logger = logging.getLogger(__name__)

# Polarizing language for crude stance detection (abstract-level proxy)
_SUPPORT_CUES = re.compile(
    r"\b("
    r"demonstrate[sd]?|show(?:s|ed|ing)?|confirm(?:s|ed|ing)?|prov(?:e|es|ed|ing)|"
    r"achieve[sd]?|enable[sd]?|successful(?:ly)?|efficien(?:t|cy)|improve[sd]?|"
    r"significant(?:ly)?|robust|effective"
    r")\b",
    re.I,
)
_LIMIT_CUES = re.compile(
    r"\b("
    r"however|nevertheless|limitation|bottleneck|poor(?:ly)?|fail(?:s|ed|ure)?|"
    r"remain(?:s|ed|ing)? (?:poorly |largely )?(?:unknown|unclear|elusive|challenging)|"
    r"not (?:yet |fully |well )?understood|insufficient|unable|cannot|elusive|"
    r"challenge|obstacle|barrier|modest|partial|incomplete|controversial|"
    r"inconsisten(?:t|cy)|contradict|debate|unclear|unknown|poorly characterized"
    r")\b",
    re.I,
)

# Shared scientific content tokens (drop ultra-common stopwords)
_STOP = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "are",
    "was",
    "were",
    "been",
    "have",
    "has",
    "had",
    "not",
    "but",
    "their",
    "our",
    "can",
    "may",
    "also",
    "using",
    "into",
    "via",
    "than",
    "such",
    "these",
    "those",
    "between",
    "among",
    "after",
    "before",
    "over",
    "under",
    "while",
    "where",
    "when",
    "which",
    "what",
    "who",
    "how",
    "why",
    "its",
    "his",
    "her",
    "they",
    "them",
    "we",
    "you",
    "your",
    "all",
    "any",
    "each",
    "other",
    "more",
    "most",
    "some",
    "only",
    "very",
    "both",
    "through",
    "during",
    "including",
    "based",
    "results",
    "result",
    "study",
    "studies",
    "paper",
    "here",
    "show",
    "shown",
    "suggest",
    "suggests",
    "proposed",
    "propose",
    "report",
    "reported",
}


def _tokens(text: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-z]{3,}", (text or "").lower())
        if t not in _STOP and len(t) > 2
    }


def stance_score(text: str) -> float:
    """Return stance in [-1, +1]: positive = supportive, negative = limiting/hedged."""
    if not text:
        return 0.0
    s = len(_SUPPORT_CUES.findall(text))
    l = len(_LIMIT_CUES.findall(text))
    if s == 0 and l == 0:
        return 0.0
    raw = (s - l) / max(1.0, float(s + l))
    return max(-1.0, min(1.0, raw))


def claim_similarity(a: Claim, b: Claim) -> float:
    """Jaccard on content tokens + small boost for shared domain-ish tags."""
    ta, tb = _tokens(a.text), _tokens(b.text)
    if not ta or not tb:
        return 0.0
    j = len(ta & tb) / len(ta | tb)
    tags_a = set(a.tags or [])
    tags_b = set(b.tags or [])
    tag_boost = 0.08 if tags_a and tags_b and tags_a & tags_b else 0.0
    return min(1.0, j + tag_boost)


@dataclass
class TensionCluster:
    claim_ids: list[str]
    paper_ids: list[str]
    support_ids: list[str]
    limit_ids: list[str]
    mean_sim: float
    stance_spread: float
    prototype_text: str
    domain_tags: list[str]


def _union_find_clusters(
    claims: list[Claim],
    *,
    sim_threshold: float = 0.28,
) -> list[list[Claim]]:
    """Greedy connected components on pairwise similarity (O(n²), fine for ≤200 claims)."""
    n = len(claims)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(n):
        for j in range(i + 1, n):
            # Only link claims from different papers
            if claims[i].paper_id == claims[j].paper_id:
                continue
            if claim_similarity(claims[i], claims[j]) >= sim_threshold:
                union(i, j)

    buckets: dict[int, list[Claim]] = defaultdict(list)
    for i, c in enumerate(claims):
        buckets[find(i)].append(c)
    # Multi-paper only
    out = []
    for group in buckets.values():
        pids = {c.paper_id for c in group}
        if len(pids) >= 2 and len(group) >= 2:
            out.append(group)
    return out


def find_tension_clusters(
    claims: list[Claim],
    evidence: Optional[list[Evidence]] = None,
    *,
    sim_threshold: float = 0.28,
    min_stance_spread: float = 0.55,
) -> list[TensionCluster]:
    """Find multi-paper claim clusters with opposing stance."""
    if len(claims) < 2:
        return []

    # Augment claim text stance with same-paper limitation evidence when present
    lim_by_paper: dict[str, list[str]] = defaultdict(list)
    if evidence:
        for e in evidence:
            if e.evidence_type == EvidenceType.LIMITATION:
                lim_by_paper[e.paper_id].append(e.text)

    clusters: list[TensionCluster] = []
    for group in _union_find_clusters(claims, sim_threshold=sim_threshold):
        stances: list[tuple[Claim, float]] = []
        for c in group:
            blob = c.text
            lims = lim_by_paper.get(c.paper_id) or []
            if lims:
                blob = blob + " " + " ".join(lims[:2])
            # uncertainty slot also pulls negative
            if c.uncertainty:
                blob = blob + " " + c.uncertainty
            stances.append((c, stance_score(blob)))

        vals = [s for _, s in stances]
        spread = max(vals) - min(vals) if vals else 0.0
        support = [c.id for c, s in stances if s > 0.15]
        limit = [c.id for c, s in stances if s < -0.15]
        # Require true polarity split OR strong spread with ≥2 papers
        if spread < min_stance_spread and not (support and limit):
            continue
        if not (support and limit) and spread < 0.9:
            # need both poles for medium spreads
            continue

        # mean pairwise sim
        sims: list[float] = []
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                if group[i].paper_id != group[j].paper_id:
                    sims.append(claim_similarity(group[i], group[j]))
        mean_sim = sum(sims) / len(sims) if sims else 0.0

        # domain tags from tokens
        from src.gap.score import tag_domains

        blob = " ".join(c.text for c in group)
        tags = tag_domains(blob)
        # prototype = longest claim text (usually more specific)
        proto = max(group, key=lambda c: len(c.text or ""))

        clusters.append(
            TensionCluster(
                claim_ids=[c.id for c in group],
                paper_ids=sorted({c.paper_id for c in group}),
                support_ids=support,
                limit_ids=limit,
                mean_sim=round(mean_sim, 3),
                stance_spread=round(spread, 3),
                prototype_text=proto.text,
                domain_tags=tags,
            )
        )

    clusters.sort(key=lambda c: (c.stance_spread, c.mean_sim, len(c.paper_ids)), reverse=True)
    logger.info("Cross-paper tension clusters: %d", len(clusters))
    return clusters


def clusters_to_gaps(
    clusters: Iterable[TensionCluster],
    claims: list[Claim],
    papers: list[Paper],
    *,
    max_gaps: int = 12,
) -> list[Gap]:
    """Convert tension clusters into Gap records."""
    claim_map = {c.id: c for c in claims}
    paper_map = {p.id: p for p in papers}
    gaps: list[Gap] = []

    for cl in list(clusters)[:max_gaps]:
        paper_titles = []
        years = []
        for pid in cl.paper_ids:
            p = paper_map.get(pid)
            if p:
                paper_titles.append((p.title or "")[:60])
                if p.year:
                    years.append(p.year)

        year_span = ""
        if years:
            year_span = f" ({min(years)}–{max(years)})" if min(years) != max(years) else f" ({years[0]})"

        short = (cl.prototype_text or "")[:80]
        title = f"Cross-paper tension: {short}"
        support_snips = [
            (claim_map[i].text[:100] if i in claim_map else "") for i in cl.support_ids[:2]
        ]
        limit_snips = [
            (claim_map[i].text[:100] if i in claim_map else "") for i in cl.limit_ids[:2]
        ]
        description = (
            f"Related claims across {len(cl.paper_ids)} papers{year_span} pull in different "
            f"directions (stance spread={cl.stance_spread:.2f}, mean sim={cl.mean_sim:.2f}). "
            f"Supportive: {'; '.join(s for s in support_snips if s) or '—'}. "
            f"Limiting/hedged: {'; '.join(s for s in limit_snips if s) or '—'}."
        )
        if paper_titles:
            description += " Papers: " + " | ".join(paper_titles[:4])

        # Multi-axis: tension is high novelty / magnitude; testability from domain richness
        magnitude = round(min(0.95, 0.55 + 0.25 * cl.stance_spread + 0.1 * min(1.0, len(cl.paper_ids) / 4)), 2)
        novelty = round(min(0.95, 0.6 + 0.2 * cl.stance_spread + (0.08 if years and max(years) - min(years) >= 2 else 0)), 2)
        testability = 0.68 if cl.domain_tags else 0.55
        impact = 0.55
        blob = (cl.prototype_text or "").lower() + " " + " ".join(cl.domain_tags)
        for kw, bump in (
            ("delivery", 0.1),
            ("endosomal", 0.1),
            ("extrahepatic", 0.12),
            ("clinical", 0.08),
            ("crispr", 0.08),
            ("ncrna", 0.08),
            ("hybrid", 0.08),
        ):
            if kw in blob:
                impact += bump
        impact = round(min(0.95, impact), 2)
        overall = round((magnitude + novelty + testability + impact) / 4.0, 2)

        gaps.append(
            Gap(
                kind=GapKind.CROSS_PAPER_TENSION,
                title=title[:200],
                description=description[:700],
                claim_ids=list(cl.claim_ids),
                evidence_ids=[],
                paper_ids=list(cl.paper_ids),
                magnitude=magnitude,
                novelty=novelty,
                testability=testability,
                impact=impact,
                overall=overall,
                domain_tags=list(cl.domain_tags),
                rationale=(
                    f"Cross-paper dialectic: {len(cl.support_ids)} supportive vs "
                    f"{len(cl.limit_ids)} limiting claims over {len(cl.paper_ids)} papers; "
                    f"stance_spread={cl.stance_spread}, mean_sim={cl.mean_sim}."
                ),
            )
        )

    return gaps


def find_cross_paper_gaps(
    claims: list[Claim],
    evidence: list[Evidence],
    papers: list[Paper],
    *,
    sim_threshold: float = 0.28,
    max_gaps: int = 12,
) -> list[Gap]:
    """Public entry: clusters → gaps."""
    clusters = find_tension_clusters(
        claims,
        evidence,
        sim_threshold=sim_threshold,
    )
    return clusters_to_gaps(clusters, claims, papers, max_gaps=max_gaps)
