"""Minimal test suite for the Research Gap Agent."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.models import (
    Claim,
    ClaimType,
    Evidence,
    EvidenceType,
    Gap,
    GapKind,
    Paper,
    TopicProposal,
)
from src.gap_scorer import find_gaps, suggest_topics
from src.extractors import extract_claims_heuristic, extract_evidence_heuristic


# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def sample_papers() -> list[Paper]:
    return [
        Paper(
            id="paper_1",
            title="Test paper: LNP endosomal escape mechanism",
            abstract=(
                "We propose that ionizable lipids in LNPs promote endosomal escape "
                "through a flip-flop mechanism involving pH-dependent protonation. "
                "Our results show that less than 2% of encapsulated mRNA reaches the cytosol. "
                "This endosomal escape efficiency is the major bottleneck for LNP delivery. "
                "However, the exact molecular mechanism remains poorly understood."
            ),
            authors=["Test A", "Test B"],
            year=2023,
            source="fixture",
        ),
        Paper(
            id="paper_2",
            title="Test paper: Extrahepatic targeting of LNPs",
            abstract=(
                "Lipid nanoparticles primarily accumulate in the liver after IV administration. "
                "We hypothesized that modifying the PEG-lipid composition could redirect LNPs to the spleen. "
                "Our experiments showed a reduction in liver uptake from 85% to 65% was achieved, "
                "but significant extrahepatic delivery remains elusive. "
                "The protein corona plays a critical role in LNP biodistribution."
            ),
            authors=["Test C"],
            year=2022,
            source="fixture",
        ),
    ]


# ── Model tests ─────────────────────────────────────────────────


class TestModels:
    def test_paper_defaults(self):
        p = Paper(title="Test", abstract="Abstract text")
        assert p.id.startswith("paper_")
        assert p.source == "unknown"
        assert p.citation_count is None
        assert p.text_blob() == "Test\n\nAbstract text"

    def test_paper_text_blob_no_abstract(self):
        p = Paper(title="Only title")
        assert p.text_blob() == "Only title"

    def test_claim_creation(self):
        c = Claim(paper_id="p1", text="A theoretical claim", claim_type=ClaimType.THEORY)
        assert c.id.startswith("claim_")
        assert c.extractor == "heuristic"
        assert 0.0 <= c.confidence <= 1.0

    def test_evidence_creation(self):
        e = Evidence(paper_id="p1", text="Experimental result", evidence_type=EvidenceType.RESULT)
        assert e.id.startswith("evid_")
        assert e.confidence == 0.5

    def test_gap_defaults(self):
        g = Gap(title="A gap", description="Description")
        assert g.id.startswith("gap_")
        assert g.kind == GapKind.THEORY_VS_EXPERIMENT
        assert 0.0 <= g.overall <= 1.0

    def test_topic_proposal(self):
        t = TopicProposal(title="Topic", hypothesis="H1")
        assert t.id.startswith("topic_")
        assert t.priority == 0.5

    def test_serialization_roundtrip(self):
        p = Paper(title="Test", abstract="Abstract", authors=["A"])
        d = json.loads(p.model_dump_json())
        assert d["title"] == "Test"
        assert d["authors"] == ["A"]

    def test_claim_enum_values(self):
        assert ClaimType.THEORY.value == "theory"
        assert ClaimType.MECHANISM.value == "mechanism"

    def test_evidence_enum_values(self):
        assert EvidenceType.EXPERIMENT.value == "experiment"
        assert EvidenceType.LIMITATION.value == "limitation"


# ── Extractor tests ─────────────────────────────────────────────


class TestExtractors:
    def test_extract_claims_heuristic(self, sample_papers):
        claims = extract_claims_heuristic(sample_papers[0])
        assert isinstance(claims, list)
        if claims:
            c = claims[0]
            assert c.paper_id == "paper_1"
            assert c.extractor == "heuristic"

    def test_extract_evidence_heuristic(self, sample_papers):
        evidence = extract_evidence_heuristic(sample_papers[0])
        assert isinstance(evidence, list)
        if evidence:
            e = evidence[0]
            assert e.paper_id == "paper_1"

    def test_empty_paper(self):
        p = Paper(title="Empty")
        assert extract_claims_heuristic(p) == []
        assert extract_evidence_heuristic(p) == []

    def test_extract_from_all_papers(self, sample_papers):
        all_c = []
        all_e = []
        for p in sample_papers:
            all_c.extend(extract_claims_heuristic(p))
            all_e.extend(extract_evidence_heuristic(p))
        # At least some results expected from our realistic abstracts
        assert len(all_c) > 0 or len(all_e) > 0


# ── Gap scorer tests ────────────────────────────────────────────


class TestGapScorer:
    def test_find_gaps_returns_list(self, sample_papers):
        claims = []
        evidence = []
        for p in sample_papers:
            claims.extend(extract_claims_heuristic(p))
            evidence.extend(extract_evidence_heuristic(p))
        gaps = find_gaps(claims, evidence, sample_papers)
        assert isinstance(gaps, list)

    def test_gaps_sorted_by_overall(self, sample_papers):
        claims = []
        evidence = []
        for p in sample_papers:
            claims.extend(extract_claims_heuristic(p))
            evidence.extend(extract_evidence_heuristic(p))
        gaps = find_gaps(claims, evidence, sample_papers)
        scores = [g.overall for g in gaps]
        assert scores == sorted(scores, reverse=True)

    def test_suggest_topics_returns_topics(self, sample_papers):
        claims = []
        evidence = []
        for p in sample_papers:
            claims.extend(extract_claims_heuristic(p))
            evidence.extend(extract_evidence_heuristic(p))
        gaps = find_gaps(claims, evidence, sample_papers)
        topics = suggest_topics(gaps)
        assert isinstance(topics, list)
        if topics:
            t = topics[0]
            assert hasattr(t, "hypothesis")
            assert hasattr(t, "proposed_experiments")

    def test_empty_gaps_no_topics(self):
        assert suggest_topics([]) == []


# ── Integration: fixture loading ────────────────────────────────


class TestFixture:
    def test_fixture_papers_loadable(self):
        """Verify all fixture papers deserialize from JSONL correctly."""
        fixture_path = REPO_ROOT / "src" / "fixtures" / "papers_fixture.jsonl"
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        papers = []
        with open(fixture_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    p = Paper(**json.loads(line))
                    papers.append(p)
        assert len(papers) >= 10, f"Expected >=10 papers, got {len(papers)}"
        # Check titles are non-empty
        for p in papers:
            assert p.title, f"Empty title in {p.id}"
            assert p.source == "fixture"
