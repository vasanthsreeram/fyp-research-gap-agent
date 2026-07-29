# Supervisor Update — FYP Research Gap Agent

**To:** Asst Prof Aaron Smargon (NTU CBE)

**From:** Sreeram Vasanth (U2322909K)

**Date:** 30 July 2026, 14:00 SGT

**Meeting:** BG4801 FYP progress check-in

---

## Context (from our meeting)

Following our discussion in early July about building an **AI-agentic framework for “researching about research”** — finding theory↔experiment gaps and proposing high-impact, experimentally testable biology topics, with care about **LLM memorization** of the literature — I’ve made early progress ahead of the formal August start. I’m anchoring this work to your lab’s gene-editing / nucleic-acid direction (including interest around **CBE/26/143** modelling gene editing efficiency with generative AI), using a first vertical slice in a related, experimentally rich domain.

## What I've built

I've shipped a **working end-to-end Research Gap Agent** pipeline and reorganized it into clean modules for the next stage of work.

Repo: https://github.com/vasanthsreeram/fyp-research-gap-agent

### Domain focus

Prototype scoped to **nucleic acid delivery / lipid nanoparticles (LNPs) / mRNA therapeutics** — biophysical theory vs experimental delivery outcomes is well-documented and mechanistically interesting.

### Pipeline components

| Component | Status | Notes |
|-----------|--------|-------|
| Pydantic schemas (Paper, Claim, Evidence, Gap, TopicProposal) | Done | JSON-serializable, stable IDs |
| Ingestion (`src/ingest/`) | Done | Semantic Scholar client + arXiv helper + offline fixture fallback; caches under `data/raw/` and `data/processed/` |
| Claim extractor (`src/extract/claims.py`) | Done | Heuristic (offline) + OpenAI structured JSON (Keychain-backed) |
| Evidence extractor (`src/extract/evidence.py`) | Done | Results, metrics, limitations with quote spans |
| Gap scorer (`src/gap/score.py` + `embeddings.py`) | Done | Lexical (Jaccard+TF) **and** embedding aligner (MiniLM + optional Chroma); multi-axis scores |
| Topic suggester (`src/topics/suggest.py`) | Done | 5 domain-linked proposals with hypotheses + experiments |
| CLI | Done | `python -m src.cli run --limit 15 --aligner embedding` |
| Markdown report | Done | `reports/latest_run.md` |
| Tests | Done | 30 pytest tests (all passing) |

### Latest run results (15 papers, LLM extractor, 2026-07-29)

| Metric | Count |
|--------|------:|
| Papers | 15 |
| Claims | 91 |
| Evidence items | 102 |
| Gaps scored | 47 |
| Topic proposals | 5 |

Heuristic-only offline mode (no API) on the same 15 papers: **27 claims / 56 evidence / 32 gaps / 5 topics** — so the demo still works without network keys.

Embedding aligner on the same heuristic extracts (2026-07-29 morning): **30 gaps** via MiniLM cosine + Chroma evidence index (`--aligner embedding`), with slightly tighter claim↔evidence matches than pure lexical overlap.

### Example findings (from latest report)

**High-scoring gap themes**
- Endosomal escape improvements correlating with toxicity (delivery–safety tradeoff)
- Difficulty of direct visualization of endosomal escape in living cells
- Competing models: membrane destabilization vs fusion for LNP escape
- Extrahepatic targeting still limited after systemic administration

**Example topic proposal — endosomal escape mechanism**
> **Hypothesis:** Endosomal escape of LNPs proceeds primarily through membrane destabilization (ionizable lipid-facilitated flip-flop / bilayer disruption) rather than purely fusogenic mechanisms, and can be enhanced by helper lipids that lower the lamellar-to-hexagonal transition temperature.
>
> **Experiments:** (1) lipid-mixing vs content-release assays, (2) timed cryo-ET in endosomal compartments, (3) helper-lipid titration with FRET escape readouts.
>
> **Readout:** Fraction of cargo reaching cytosol vs lysosomal loss.

Other generated topics cover ligand avidity vs specificity for extrahepatic targeting, nucleoside-modification × LNP synergy for durable mRNA expression, and siRNA delivery outside the liver.

### How to reproduce

```bash
# Offline demo (no keys) — lexical aligner
python -m src.cli run --limit 15 --fixture --mode heuristic --aligner lexical

# Embedding aligner (sentence-transformers MiniLM + Chroma)
python -m src.cli run --limit 15 --fixture --mode heuristic --aligner embedding

# LLM extraction (uses Keychain / OPENAI_API_KEY if present)
python -m src.cli run --limit 15 --fixture --mode llm --aligner auto
```

Outputs: `data/processed/*.jsonl`, `reports/latest_run.md`.

## Guarding against LLM memorization

1. **Citation-grounded extraction:** Every claim/evidence item carries `paper_id` + `quote_span`.
2. **Dual path:** Fully offline heuristic extractor for baseline; LLM path is optional and model-agnostic (OpenAI-compatible).
3. **Planned:** held-out **post-cutoff** papers as a memorization / generalization check (not yet run).

## What is not done yet (honest)

- Live Semantic Scholar / arXiv pulls hit **HTTP 429** during last refetch; corpus for the demo is the curated 18-paper fixture (15 used via `--limit`). API clients are implemented and will expand the corpus when limits clear or an S2 key is added.
- No formal human eval rubric yet for “is this gap good?”
- Second domain (e.g. hybrid ncRNA) not started.
- Memorization held-out benchmark not yet run.

## Proposed next steps

1. Memorization benchmark on post-cutoff held-out papers
2. Expand to 50+ papers once live APIs are stable
3. Lightweight HTML report for easier review
4. Draft a simple human rubric (novelty, testability, biological impact)
5. Optional second domain slice (hybrid ncRNA)

## Open questions for you, Prof

1. **Scope:** Is NA delivery / LNP the right primary demo domain, or should we pivot closer to gene-editing efficiency / CBE–relevant mechanisms?
2. **Evaluation:** Preferred way to judge gap/topic quality (rubric dimensions, gold labels, expert spot-checks)?
3. **Memorization:** How strict should citation-grounding be (no generation without source spans vs LLM-assisted then validated)?
4. **Meeting format:** Full pipeline demo vs deep-dive on 1–2 gaps/topics?

---

*Assembled from pipeline outputs (`reports/latest_run.md`, `data/processed/*.jsonl`) for the 30 July 2026 check-in.*
