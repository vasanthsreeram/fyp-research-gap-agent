# FYP Research Gap Agent

**Project:** AI agentic framework for identifying theory↔experiment gaps in research literature and proposing high-impact, testable biology topics.

**Student:** Sreeram Vasanth (U2322909K) · **Supervisor meeting:** 30 July 2026, 14:00 SGT  
**Repo:** https://github.com/vasanthsreeram/fyp-research-gap-agent

## Status

Stage 1 vertical slice shipped. Stage 2: modular packages, claim-recall, LLM path, **embedding gap alignment**.

Latest embedding run (`--limit 15 --aligner embedding`): **15 papers → 27 claims → 56 evidence → 30 gaps → 5 topics**.  
Tests: **30 passed**.

See [`docs/STATUS.md`](docs/STATUS.md) and [`docs/supervisor-update-draft.md`](docs/supervisor-update-draft.md).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Offline end-to-end (lexical aligner; no heavy model download if you skip ST)
python -m src.cli run --limit 15 --fixture --mode heuristic --aligner lexical

# Embedding aligner (sentence-transformers MiniLM + optional Chroma)
python -m src.cli run --limit 15 --fixture --mode heuristic --aligner embedding

# LLM extraction if OPENAI_API_KEY is set (or macOS Keychain service
# openclaw/tgcallskill/openai-api-key); auto picks embedding when available
python -m src.cli run --limit 15 --fixture --mode llm --aligner auto

# Live ingest attempt (S2 + arXiv; falls back to fixture on failure)
python -m src.cli run --limit 15 --refetch

pytest -q
```

Outputs:
- `data/processed/papers.jsonl`, `claims.jsonl`, `evidence.jsonl`, `gaps.jsonl`, `topics.jsonl`
- `data/processed/chroma_gap_index/` (embedding runs; gitignored)
- `reports/latest_run.md`

## Architecture

```
ingest (S2 / arXiv / fixture)
    → extract claims + evidence (heuristic | llm)
    → gap align (lexical | embedding) + multi-axis score
    → topic suggest
    → markdown report
```

| Package | Role |
|---------|------|
| `src/models.py` | Pydantic schemas |
| `src/ingest/` | Semantic Scholar + arXiv + pipeline |
| `src/extract/` | Claims, evidence, LLM helpers |
| `src/gap/` | Lexical + embedding alignment, scoring, Chroma index |
| `src/topics/` | Research topic proposals |
| `src/cli.py` | Typer CLI |

## Domain slice

Nucleic acid delivery / lipid nanoparticles / mRNA delivery — experimentally rich, mechanism-heavy, aligned with supervisor guidance on NA chemistry and testable gaps.

## Memorization safeguards (in progress)

- All extracts carry `paper_id` + `quote_span`
- Offline heuristic path requires no LLM
- Planned: post-cutoff held-out paper benchmark

## Docs

- [`docs/fyp-brief.md`](docs/fyp-brief.md) — original framing
- [`docs/STATUS.md`](docs/STATUS.md) — living board
- [`docs/PROGRESS_LOG.md`](docs/PROGRESS_LOG.md) — build log
- [`docs/supervisor-update-draft.md`](docs/supervisor-update-draft.md) — email/meeting bullets
