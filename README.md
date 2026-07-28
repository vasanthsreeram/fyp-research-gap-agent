# FYP Research Gap Agent

**Project:** AI agentic framework for identifying theory↔experiment gaps in research literature and proposing high-impact, testable biology topics.

**Student:** Sreeram Vasanth (U2322909K) · **Supervisor meeting:** 30 July 2026, 14:00 SGT  
**Repo:** https://github.com/vasanthsreeram/fyp-research-gap-agent

## Status

Stage 1 vertical slice is **shipped**. Stage 2 packaging + claim-recall + LLM path landed 2026-07-29.

Latest LLM run (`--limit 15`): **15 papers → 91 claims → 102 evidence → 47 gaps → 5 topics**.  
Offline heuristic on the same set: **27 / 56 / 32 / 5**. Tests: **23 passed**.

See [`docs/STATUS.md`](docs/STATUS.md) and [`docs/supervisor-update-draft.md`](docs/supervisor-update-draft.md).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Offline end-to-end (no API keys)
python -m src.cli run --limit 15 --fixture --mode heuristic

# LLM extraction if OPENAI_API_KEY is set (or macOS Keychain service
# openclaw/tgcallskill/openai-api-key)
python -m src.cli run --limit 15 --fixture --mode llm

# Live ingest attempt (S2 + arXiv; falls back to fixture on failure)
python -m src.cli run --limit 15 --refetch

pytest -q
```

Outputs:
- `data/processed/papers.jsonl`, `claims.jsonl`, `evidence.jsonl`, `gaps.jsonl`, `topics.jsonl`
- `reports/latest_run.md`

## Architecture

```
ingest (S2 / arXiv / fixture)
    → extract claims + evidence (heuristic | llm)
    → gap align + multi-axis score
    → topic suggest
    → markdown report
```

| Package | Role |
|---------|------|
| `src/models.py` | Pydantic schemas |
| `src/ingest/` | Semantic Scholar + arXiv + pipeline |
| `src/extract/` | Claims, evidence, LLM helpers |
| `src/gap/` | Gap detection + scoring |
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
