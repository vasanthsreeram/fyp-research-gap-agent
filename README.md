# FYP Research Gap Agent

**Project:** AI agentic framework for identifying theory↔experiment gaps in research literature and proposing high-impact, testable biology topics.

**Student:** Sreeram Vasanth (U2322909K) · **Supervisor meeting:** 30 July 2026, 14:00 SGT  
**Repo:** https://github.com/vasanthsreeram/fyp-research-gap-agent

## Status

Stage 2: modular packages, claim-recall, LLM path, embedding gap alignment, **memorization safeguards v2**, **pack-aware topic ranking**, **52-paper corpus**, **dual-domain pack eval**, **human feedback harness**.

Latest heuristic extract on fixture: **52 papers → 88 structured claims → 160 evidence → 103 gaps → 5 pack-balanced topics**.  
Mem-bench **PASS** (ground 100%, unsup/cite/over/leak 0%, controlled 7/7). Domain pack **PASS**. Tests: **42 passed**.

See [`docs/STATUS.md`](docs/STATUS.md), [`docs/memorization-eval.md`](docs/memorization-eval.md), and [`docs/supervisor-update-draft.md`](docs/supervisor-update-draft.md).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Offline end-to-end (full fixture corpus)
python -m src.cli run --limit 52 --fixture --mode heuristic --aligner embedding --format both

# Domain pack eval (LNP core vs hybrid ncRNA)
python -m src.cli domain-pack --limit 52 --fixture

# Memorization / grounding bench (expanded)
python -m src.cli mem-bench --fixture --limit 52 --cutoff-year 2024
# optional closed-book with small model:
# OPENAI_MODEL=gpt-4o-mini python -m src.cli mem-bench --fixture --closed-book

# Human feedback on a gap/topic
python -m src.cli feedback-add --type gap --id gap_xxx --rating 5 --labels surprising,testable
python -m src.cli feedback-summary

# Live ingest attempt (S2 + arXiv; falls back to fixture on failure)
python -m src.cli run --limit 15 --refetch

pytest -q
```

Outputs:
- `data/processed/papers.jsonl`, `claims.jsonl`, `evidence.jsonl`, `gaps.jsonl`, `topics.jsonl`
- `data/processed/feedback.jsonl` (human ratings)
- `data/processed/chroma_gap_index/` (embedding runs; gitignored)
- `reports/latest_run.md`, `latest_run.html`, `domain_pack.md`, `memorization_bench.md`

## Architecture

```
ingest (S2 / arXiv / fixture)
    → extract claims + evidence (heuristic | llm)
    → gap align (lexical | embedding) + multi-axis score
    → topic suggest
    → mem-bench + domain-pack eval
    → markdown/HTML report
    → optional human feedback JSONL
```

| Package | Role |
|---------|------|
| `src/models.py` | Pydantic schemas (+ FeedbackRecord; TopicProposal pack_id/rank_score) |
| `src/ingest/` | Semantic Scholar + arXiv + fixture pipeline |
| `src/extract/` | Claims, evidence, LLM helpers |
| `src/gap/` | Lexical + embedding alignment, scoring, Chroma index |
| `src/topics/` | Pack-aware research topic proposals (hybrid/LNP/gene balance) |
| `src/eval/` | Memorization bench, domain packs, feedback |
| `src/cli.py` | Typer CLI |

## Domain slice

Primary: nucleic acid delivery / lipid nanoparticles / mRNA.  
Second pack: hybrid/bifunctional ncRNA, gene-editing delivery — experimentally rich, mechanism-heavy, aligned with supervisor guidance.

## Memorization safeguards

- All extracts carry `paper_id` + `quote_span`
- Claims structured into **hypothesis / evidence / mechanism / assumptions / uncertainty**
- Offline heuristic path requires no LLM
- Post-cutoff held-out papers (21× ≥2024 in fixture) + cross-era leakage check
- Detectors: unsupported claims, hallucinated citations (DOI/arXiv/cite-year), overconfidence
- Controlled synthetic suite locked in pytest (7 cases)
- Optional closed-book LLM probe: `mem-bench --closed-book` (prefer open/small models via `OPENAI_MODEL`)
- Plan + metrics: [`docs/memorization-eval.md`](docs/memorization-eval.md)

## Docs

- [`docs/fyp-brief.md`](docs/fyp-brief.md) — original framing
- [`docs/STATUS.md`](docs/STATUS.md) — living board
- [`docs/PROGRESS_LOG.md`](docs/PROGRESS_LOG.md) — build log
- [`docs/memorization-eval.md`](docs/memorization-eval.md) — mem safeguards plan, tests, metrics
- [`docs/supervisor-update-draft.md`](docs/supervisor-update-draft.md) — email/meeting bullets
