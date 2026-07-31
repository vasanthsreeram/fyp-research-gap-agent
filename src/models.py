"""Core Pydantic schemas for the Research Gap Agent pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class ClaimType(str, Enum):
    THEORY = "theory"
    MECHANISM = "mechanism"
    PREDICTION = "prediction"
    ASSUMPTION = "assumption"
    OTHER = "other"


class EvidenceType(str, Enum):
    EXPERIMENT = "experiment"
    RESULT = "result"
    METRIC = "metric"
    LIMITATION = "limitation"
    OBSERVATION = "observation"
    OTHER = "other"


class GapKind(str, Enum):
    THEORY_VS_EXPERIMENT = "theory_vs_experiment"
    PREDICTION_MISS = "prediction_miss"
    UNTESTED_CLAIM = "untested_claim"
    REPRODUCIBILITY = "reproducibility"
    SCALABILITY = "scalability"
    MECHANISM_UNKNOWN = "mechanism_unknown"
    DELIVERY_BARRIER = "delivery_barrier"
    OTHER = "other"


class Paper(BaseModel):
    """Ingested paper / preprint metadata + abstract text."""

    id: str = Field(default_factory=lambda: _id("paper"))
    title: str
    abstract: str = ""
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    s2_id: Optional[str] = None
    venue: Optional[str] = None
    url: Optional[str] = None
    source: str = "unknown"  # semantic_scholar | arxiv | fixture
    keywords: list[str] = Field(default_factory=list)
    citation_count: Optional[int] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    def text_blob(self) -> str:
        parts = [self.title or "", self.abstract or ""]
        return "\n\n".join(p for p in parts if p).strip()


class Claim(BaseModel):
    """A theoretical / mechanistic claim extracted from a paper.

    Structured fields (hypothesis / evidence / mechanism / assumptions /
    uncertainty) support grounded gap reasoning and memorization audits.
    `text` remains the primary free-form claim string for scoring.
    """

    id: str = Field(default_factory=lambda: _id("claim"))
    paper_id: str
    claim_type: ClaimType = ClaimType.THEORY
    text: str
    quote_span: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    extractor: str = "heuristic"  # heuristic | llm
    # Structured claim decomposition (optional; empty when not filled)
    hypothesis: Optional[str] = None
    evidence: Optional[str] = None  # supporting evidence stated in-paper
    mechanism: Optional[str] = None
    assumptions: list[str] = Field(default_factory=list)
    uncertainty: Optional[str] = None  # hedges, unknowns, limits of claim


class Evidence(BaseModel):
    """Experimental result, metric, limitation, or observation."""

    id: str = Field(default_factory=lambda: _id("evid"))
    paper_id: str
    evidence_type: EvidenceType = EvidenceType.RESULT
    text: str
    quote_span: Optional[str] = None
    metric_name: Optional[str] = None
    metric_value: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    extractor: str = "heuristic"


class Gap(BaseModel):
    """Scored theory↔experiment (or related) gap."""

    id: str = Field(default_factory=lambda: _id("gap"))
    kind: GapKind = GapKind.THEORY_VS_EXPERIMENT
    title: str
    description: str
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    paper_ids: list[str] = Field(default_factory=list)
    # Multi-axis scores in [0, 1]
    magnitude: float = Field(default=0.5, ge=0.0, le=1.0)
    novelty: float = Field(default=0.5, ge=0.0, le=1.0)
    testability: float = Field(default=0.5, ge=0.0, le=1.0)
    impact: float = Field(default=0.5, ge=0.0, le=1.0)
    overall: float = Field(default=0.5, ge=0.0, le=1.0)
    domain_tags: list[str] = Field(default_factory=list)
    rationale: str = ""


class TopicProposal(BaseModel):
    """Actionable research topic suggested from one or more gaps."""

    id: str = Field(default_factory=lambda: _id("topic"))
    title: str
    hypothesis: str
    gap_ids: list[str] = Field(default_factory=list)
    proposed_experiments: list[str] = Field(default_factory=list)
    expected_readout: str = ""
    feasibility_notes: str = ""
    impact_rationale: str = ""
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    domain_tags: list[str] = Field(default_factory=list)
    # Pack-aware ranking metadata (lnp_core | hybrid_ncrna | gene_editing)
    pack_id: Optional[str] = None
    rank_score: float = Field(default=0.5, ge=0.0, le=1.0)


class RunManifest(BaseModel):
    """Metadata for one end-to-end pipeline run."""

    run_id: str = Field(default_factory=lambda: _id("run"))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    domain: str = "nucleic_acid_delivery"
    n_papers: int = 0
    n_claims: int = 0
    n_evidence: int = 0
    n_gaps: int = 0
    n_topics: int = 0
    extractor_mode: str = "heuristic"
    aligner_mode: str = "auto"  # auto | lexical | embedding (resolved value recorded at finish)
    notes: str = ""


class FeedbackTargetType(str, Enum):
    GAP = "gap"
    TOPIC = "topic"
    CLAIM = "claim"
    EVIDENCE = "evidence"
    RUN = "run"


class FeedbackRecord(BaseModel):
    """Human rating for a gap, topic, or other pipeline artifact."""

    id: str = Field(default_factory=lambda: _id("fb"))
    target_type: FeedbackTargetType
    target_id: str
    # Likert 1–5 (None if only labels/notes)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    # Free-form labels e.g. surprising, testable, low_impact, memorized, unclear
    labels: list[str] = Field(default_factory=list)
    notes: str = ""
    reviewer: str = "vas"
    run_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
