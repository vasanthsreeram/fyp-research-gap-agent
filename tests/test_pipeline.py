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
from src.gap.score import (
    find_gaps,
    jaccard,
    resolve_aligner,
    similarity,
    score_gap,
    tag_domains,
)
from src.gap.embeddings import embeddings_available, cosine_sim
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

    def test_find_gaps_lexical_explicit(self, sample_papers):
        claims, evidence = extract_all(sample_papers, mode="heuristic")
        gaps = find_gaps(claims, evidence, sample_papers, aligner="lexical")
        assert len(gaps) >= 1
        assert any("lexical" in g.rationale for g in gaps)

    def test_resolve_aligner_lexical(self):
        assert resolve_aligner("lexical") == "lexical"


class TestEmbeddings:
    def test_cosine_sim_identical(self):
        v = [1.0, 0.0, 0.0]
        assert abs(cosine_sim(v, v) - 1.0) < 1e-6

    def test_cosine_sim_orthogonal(self):
        assert abs(cosine_sim([1.0, 0.0], [0.0, 1.0])) < 1e-6

    @pytest.mark.skipif(not embeddings_available(), reason="sentence-transformers not installed")
    def test_embed_and_match_related_texts(self):
        from src.gap.embeddings import embed_texts, pairwise_best_matches

        a = embed_texts(["endosomal escape of lipid nanoparticles"])
        b = embed_texts(["LNP endosomal escape is inefficient"])
        c = embed_texts(["stock market volatility and interest rates"])
        assert cosine_sim(a[0], b[0]) > cosine_sim(a[0], c[0])

        matches = pairwise_best_matches(
            ["ionizable lipids promote endosomal escape"],
            [
                "stock prices rose today",
                "endosomal escape via ionizable lipid protonation",
                "weather forecast cloudy",
            ],
        )
        assert matches[0][0] == 1
        assert matches[0][1] > 0.3

    @pytest.mark.skipif(not embeddings_available(), reason="sentence-transformers not installed")
    def test_find_gaps_embedding(self, sample_papers, tmp_path):
        claims, evidence = extract_all(sample_papers, mode="heuristic")
        gaps = find_gaps(
            claims,
            evidence,
            sample_papers,
            aligner="embedding",
            use_chroma=True,
            chroma_dir=tmp_path / "chroma",
        )
        assert isinstance(gaps, list)
        assert len(gaps) >= 1
        assert any("embedding" in g.rationale for g in gaps)
        scores = [g.overall for g in gaps]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.skipif(not embeddings_available(), reason="sentence-transformers not installed")
    def test_resolve_aligner_auto_prefers_embedding(self):
        assert resolve_aligner("auto") == "embedding"


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
        assert len(papers) >= 50
        for p in papers:
            assert p.title
            assert p.source == "fixture"
        # Held-out post-cutoff set for memorization bench
        assert sum(1 for p in papers if (p.year or 0) >= 2024) >= 10
        hybrid = sum(
            1
            for p in papers
            if any(k in (p.keywords or []) for k in ("hybrid_ncrna", "ncrna"))
        )
        assert hybrid >= 12

    def test_load_fixture_helper(self):
        papers = load_fixture()
        assert len(papers) >= 50

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


class TestMemorization:
    def test_quote_grounding_substring(self):
        from src.eval.memorization import quote_is_grounded

        blob = "Endosomal escape remains poorly understood in LNP delivery systems."
        assert quote_is_grounded("Endosomal escape remains poorly understood", blob)
        assert not quote_is_grounded("completely unrelated quantum finance claim", blob)

    def test_benchmark_pass_on_heuristic_fixture(self):
        from src.eval.memorization import run_memorization_benchmark

        papers = load_fixture()  # full fixture includes 2024–2025 held-out set
        claims, evidence = extract_all(papers, mode="heuristic")
        report = run_memorization_benchmark(
            papers, claims, evidence, cutoff_year=2024, run_closed_book=False
        )
        assert report.n_papers_total == len(papers)
        assert report.n_post_cutoff >= 10
        assert report.claim_grounding.rate >= 0.85
        assert report.evidence_grounding.rate >= 0.85
        assert report.unsupported_rate <= 0.10
        assert report.citation_hallucination_rate <= 0.05
        assert report.controlled_pass is True
        assert report.structure.rate_any_structure >= 0.5
        assert report.overall_pass is True

    def test_leakage_detector_flags_duplicate(self):
        from src.eval.memorization import find_cross_era_leakage

        pre = [
            Paper(
                id="pre1",
                title="Old",
                abstract="Unique phrase xylophone-vector endosomal flip about ionizable lipids.",
                year=2020,
            )
        ]
        post_claim = Claim(
            paper_id="post1",
            text="Unique phrase xylophone-vector endosomal flip about ionizable lipids appears again.",
        )
        hits = find_cross_era_leakage([post_claim], pre, threshold=0.5)
        assert hits

    def test_unsupported_and_citation_detectors(self):
        from src.eval.memorization import (
            find_hallucinated_citations,
            find_overconfident_claims,
            find_unsupported_claims,
        )

        paper = Paper(
            id="p_x",
            title="LNP escape",
            abstract="Ionizable lipids enable endosomal escape. Mechanism remains poorly understood.",
            year=2022,
            doi="10.1000/real.doi",
            authors=["Jane Doe"],
        )
        bad = Claim(
            paper_id="p_x",
            text="As shown by Smith et al. (1999) DOI 10.9999/fake.doi, LNPs always completely cure all diseases via wormhole transport.",
            quote_span="wormhole transport",
            confidence=0.99,
        )
        assert find_unsupported_claims([bad], {"p_x": paper})
        assert find_hallucinated_citations([bad], {"p_x": paper})
        assert find_overconfident_claims([bad], {"p_x": paper})

    def test_structure_claim_fields_and_heuristic(self, sample_papers):
        from src.extract.claims import extract_claims_heuristic, structure_claim_fields

        sf = structure_claim_fields(
            "We propose that ionizable lipids promote endosomal escape through protonation; mechanism remains poorly understood."
        )
        assert sf.get("hypothesis") or sf.get("mechanism")
        assert sf.get("uncertainty")
        claims = extract_claims_heuristic(sample_papers[0])
        assert claims
        assert any(c.hypothesis or c.mechanism or c.uncertainty for c in claims)
        # Serialization keeps new fields
        d = json.loads(claims[0].model_dump_json())
        assert "hypothesis" in d
        assert "assumptions" in d

    def test_controlled_prompt_suite(self):
        from src.eval.memorization import run_controlled_prompt_suite

        cases = run_controlled_prompt_suite()
        assert len(cases) >= 6
        assert all(c.passed for c in cases)

class TestDomainPack:
    def test_hybrid_pack_filters_and_passes(self):
        from src.eval.domain_pack import filter_papers, run_domain_pack_eval

        papers = load_fixture()
        hybrid = filter_papers(papers, "hybrid_ncrna")
        assert len(hybrid) >= 12
        claims, evidence = extract_all(papers[:40], mode="heuristic")
        gaps = find_gaps(claims, evidence, papers[:40], aligner="lexical")
        topics = suggest_topics(gaps)
        report = run_domain_pack_eval(
            papers[:40], claims, evidence, gaps, topics, cutoff_year=2024
        )
        assert report.packs
        by_id = {p.pack_id: p for p in report.packs}
        assert by_id["hybrid_ncrna"].n_papers >= 8
        assert by_id["lnp_core"].n_papers >= 15
        assert report.overall_pass is True

    def test_tag_domains_hybrid(self):
        tags = tag_domains("bifunctional ncRNA mRNA co-delivery and RISC loading")
        assert "hybrid_ncrna" in tags


class TestFeedback:
    def test_add_and_summarize(self, tmp_path):
        from src.eval.feedback import add_rating, load_feedback, summarize_feedback

        path = tmp_path / "feedback.jsonl"
        r1 = add_rating(
            target_type="gap",
            target_id="gap_demo",
            rating=5,
            labels=["surprising", "testable"],
            notes="strong",
            path=path,
        )
        r2 = add_rating(
            target_type="topic",
            target_id="topic_demo",
            rating=3,
            labels=["incremental"],
            path=path,
        )
        assert r1.id.startswith("fb_")
        loaded = load_feedback(path)
        assert len(loaded) == 2
        summary = summarize_feedback(path=path)
        assert summary["n_total"] == 2
        assert summary["by_type"]["gap"]["mean_rating"] == 5.0
        assert summary["by_type"]["topic"]["n"] == 1
        assert r2.rating == 3


class TestReport:
    def test_html_and_markdown_builders(self):
        from src.models import RunManifest
        from src.report import build_html_report, build_markdown_report

        papers = load_fixture()[:2]
        claims, evidence = extract_all(papers, mode="heuristic")
        gaps = find_gaps(claims, evidence, papers, aligner="lexical")
        topics = suggest_topics(gaps, max_topics=2)
        m = RunManifest(
            domain="nucleic_acid_delivery",
            extractor_mode="heuristic",
            aligner_mode="lexical",
            n_papers=len(papers),
            n_claims=len(claims),
            n_evidence=len(evidence),
            n_gaps=len(gaps),
            n_topics=len(topics),
        )
        md = build_markdown_report(m, papers, claims, evidence, gaps, topics)
        html = build_html_report(m, papers, claims, evidence, gaps, topics)
        assert "Research Gap Agent" in md
        assert str(len(papers)) in md
        assert "<!DOCTYPE html>" in html
        assert m.run_id in html
        assert "Topic" in html or "topic" in html.lower()
