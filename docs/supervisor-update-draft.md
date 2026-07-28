# Supervisor Update — FYP Research Gap Agent

**To:** Asst Prof Aaron Smargon (NTU CBE)

**From:** Sreeram Vasanth (U2322909K)

**Date:** 30 July 2026, 14:00 SGT

**Meeting:** BG4801 FYP progress check-in

---

## Context (from our meeting)

Following our discussion in early July about building an **AI-agentic framework for “researching about research”** — finding theory↔experiment gaps and proposing high-impact, experimentally testable biology topics, with care about **LLM memorization** of the literature — I’ve made early progress ahead of the formal August start. I’m anchoring this work to your lab’s gene-editing / nucleic-acid direction (including interest around **CBE/26/143** modelling gene editing efficiency with generative AI), using a first vertical slice in a related, experimentally rich domain.

## What I've built

I've shipped the first **working vertical slice** of the Research Gap Agent — an AI pipeline that ingests papers, extracts claims and experimental evidence, quantifies theory↔experiment gaps, and proposes high-impact research topics.

The code lives at: https://github.com/vasanthsreeram/fyp-research-gap-agent

### Domain focus

Per our last discussion, the prototype is scoped to **nucleic acid delivery / lipid nanoparticles (LNPs) / mRNA therapeutics** — a domain where the gap between biophysical theory and experimental delivery outcomes is well-documented and mechanistically interesting.

### Pipeline components

| Component | Status | Notes |
|-----------|--------|-------|
| Pydantic schemas (Paper, Claim, Evidence, Gap, TopicProposal) | ✅ | Extensible, JSON-serializable |
| Paper ingestion (Semantic Scholar + arXiv) | ✅ | 18 real papers cached as fixtures; S2 API ready |
| Claim extractor (heuristic + LLM) | ✅ | Heuristic mode uses regex triggers; LLM mode uses OpenAI structured output |
| Evidence/result extractor | ✅ | Metrics, limitations, observations |
| Gap scorer (multi-axis) | ✅ | Magnitude × novelty × testability × impact → overall score |
| Topic suggester | ✅ | 5 domain-specific proposals with hypotheses + experiments |
| CLI (`python -m src run`) | ✅ | End-to-end: ingest → extract → score → suggest → report |
| Report generator (Markdown) | ✅ | Self-contained `reports/latest_run.md` |
| Test suite | ✅ | 18 pytest tests |

### Results from first run (18 papers, heuristic mode)

- **31 gaps** identified across domains (LNP, endosomal escape, targeting, PK, immunogenicity)
- **5 research topic proposals** generated, including:
  1. *Rational design of ionizable lipids for extrahepatic nucleic acid delivery*
  2. *Addressing gaps in pharmacokinetics for nucleic acid delivery*
  3. *Addressing gaps in immunogenicity for nucleic acid delivery*
  4. *Mechanistic understanding of LNP endosomal escape*
  5. *Addressing gaps in delivery efficiency determinants*

Top-ranked gap: *"The pKa of ionizable lipids correlates with in vivo potency, but the precise molecular requirements for efficient endosomal escape remain unknown"* — matching a known open question in the field.

### Example topic proposal: Endosomal escape

> **Hypothesis:** Endosomal escape of LNPs proceeds primarily through membrane destabilization (ionizable lipid-facilitated flip-flop and bilayer disruption) rather than fusogenic mechanisms, and can be enhanced by helper lipids that lower the lamellar-to-hexagonal phase transition temperature.
>
> **Experiments:** (1) Labelled lipid mixing vs. content release assays, (2) Cryo-ET of LNPs in endosomal compartments, (3) Vary helper lipid ratios and correlate with escape efficiency via FRET.
>
> **Readout:** Quantitative fraction of delivered cargo reaching cytosol vs. lysosomal degradation.

## Guarding against LLM memorization

A key risk we discussed — the agent may "know" gaps from training data rather than from the papers. My mitigation strategy:

1. **Citation-grounded extraction:** Claims and evidence are tagged with `paper_id` and `quote_span` — no claim enters the pipeline without a source paper.
2. **Post-cutoff corpus:** The initial fixture set spans 2017–2022 papers. Papers published after the model's training cutoff would provide a natural memorization test.
3. **Open/small models path:** The heuristic extractor requires no API key and runs fully offline. The pipeline architecture is model-agnostic.

## Next steps (Stage 1 — this week)

- [ ] **Improve claim recall:** Heuristic mode only found 6 claims from 18 papers — need better triggers or hybrid search
- [ ] **Embedding similarity** for gap alignment (replace Jaccard overlap with sentence embeddings)
- [ ] **Memorization benchmark:** Run on a held-out post-cutoff paper and compare gap quality
- [ ] **HTML report export** for easier reading
- [ ] **Expand corpus** to 50+ papers with Semantic Scholar API (currently fixture-based)
- [ ] Expand to second domain (e.g., hybrid ncRNA or protein engineering) for cross-domain validation

## Open questions for you, Prof

1. **Scope:** Is NA delivery/LNP the right primary domain to demo, or should we pivot to something more fundamental (e.g., protein folding prediction ↔ in vivo validation)?
2. **Evaluation:** How should we measure whether a proposed gap is "good"? I'm thinking a human rubric for novelty, testability, and biological impact.
3. **Memorization:** What level of citation-grounding rigor do you want? Strict (no generation without explicit source spans) or moderate (LLM-assisted but validated)?
4. **Next meeting:** Should I present the full pipeline demo, or focus on specific gaps/topics found so far?

---

*Report generated by the Research Gap Agent pipeline and assembled for supervisor review.*
