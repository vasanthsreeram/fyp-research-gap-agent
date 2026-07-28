"""Minimal test suite for the Research Gap Agent (schemas + offline pipeline)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

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
from src.extract.claims import extract_claims_heuristic
from src.extract.evidence import extract_evidence_heuristic
from src.extract import extract_all
from src.gap.score import find_gaps, jaccard, similarity, score_gap, tag_domains
from src.topics.suggest import suggest_topics
from src.ingest.pipeline import load_fixture


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


class TestExtractors:
    def test_extract_claims_heuristic(self, sample_papers):
        claims = extract_claims_heuristic(sample_papers[0])
        assert isinstance(claims, list)
        assert len(claims) >= 1
        c = claims[0]
        assert c.paper_id == "paper_1"
        assert c.extractor == "heuristic"

    def test_extract_evidence_heuristic(self, sample_papers):
        evidence = extract_evidence_heuristic(sample_papers[0])
        assert isinstance(evidence, list)
        assert len(evidence) >= 1
        assert evidence[0].paper_id == "paper_1"

    def test_empty_paper(self):
        p = Paper(title="Empty")
        assert extract_claims_heuristic(p) == []
        assert extract_evidence_heuristic(p) == []

    def test_extract_all_heuristic(self, sample_papers):
        claims, evidence = extract_all(sample_papers, mode="heuristic")
        assert len(claims) >= 1
        assert len(evidence) >= 1

    def test_claim_recall_improved(self, sample_papers):
        """v0.2 heuristics should find multiple claims across the two fixture abstracts."""
        all_c = []
        for p in sample_papers:
            all_c.extend(extract_claims_heuristic(p))
        assert len(all_c) >= 2


class TestGapScorer:
    def test_jaccard_and_similarity(self):
        assert jaccard("endosomal escape lipid", "endosomal escape lipid") == 1.0
        assert similarity("endosomal escape of LNPs", "LNP endosomal escape mechanism") > 0.2

    def test_tag_domains(self):
        tags = tag_domains("lipid nanoparticle endosomal escape extrahepatic targeting")
        assert "lnp" in tags
        assert "endosomal_escape" in tags
        assert "targeting" in tags

    def test_score_gap_bounds(self):
        c = Claim(paper_id="p", text="mechanism of endosomal escape", claim_type=ClaimType.MECHANISM)
        s = score_gap(kind=GapKind.MECHANISM_UNKNOWN, claim=c, evidence=None, sim=0.0, domain_tags=["endosomal_escape"])
        for k in ("magnitude", "novelty", "testability", "impact", "overall"):
            assert 0.0 <= s[k] <= 1.0

    def test_find_gaps_returns_sorted_list(self, sample_papers):
        claims, evidence = extract_all(sample_papers, mode="heuristic")
        gaps = find_gaps(claims, evidence, sample_papers)
        assert isinstance(gaps, list)
        assert len(gaps) >= 1
        scores = [g.overall for g in gaps]
        assert scores == sorted(scores, reverse=True)

    def test_suggest_topics_returns_topics(self, sample_papers):
        claims, evidence = extract_all(sample_papers, mode="heuristic")
        gaps = find_gaps(claims, evidence, sample_papers)
        topics = suggest_topics(gaps)
        assert isinstance(topics, list)
        if topics:
            t = topics[0]
            assert t.hypothesis
            assert t.proposed_experiments

    def test_empty_gaps_no_topics(self):
        assert suggest_topics([]) == []


class TestFixture:
    def test_fixture_papers_loadable(self):
        fixture_path = REPO_ROOT / "src" / "fixtures" / "papers_fixture.jsonl"
        assert fixture_path.exists()
        papers = []
        with open(fixture_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    papers.append(Paper(**json.loads(line)))
        assert len(papers) >= 10
        for p in papers:
            assert p.title
            assert p.source == "fixture"

    def test_load_fixture_helper(self):
        papers = load_fixture()
        assert len(papers) >= 10

    def test_offline_pipeline_one_paper(self):
        """End-to-end offline path on a single fixture paper."""
        papers = load_fixture()[:1]
        assert papers
        claims, evidence = extract_all(papers, mode="heuristic")
        gaps = find_gaps(claims, evidence, papers)
        topics = suggest_topics(gaps, max_topics=3)
        # Soft assertions — abstract quality varies
        assert isinstance(claims, list)
        assert isinstance(evidence, list)
        assert isinstance(gaps, list)
        assert isinstance(topics, list)
