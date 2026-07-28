# FYP Research Gap Agent — PROGRESS LOG

## Build log for overnight vertical slice (2026-07-23 → 2026-07-29)

| Date | Commits | Milestone |
|------|---------|-----------|
| 2026-06-29 | `25d3eec`, `ed90329` | Initial docs stub: README, fyp-brief, initial-plan |
| 2026-07-01 | `3e7ccc7` | Prof meeting docs + STATUS board |
| 2026-07-29 00:24 | `cfc2d9d` | Daily cron + call loop notes |
| 2026-07-29 00:34 | **(this build)** | **Vertical slice: full code pipeline** |

### Build summary (2026-07-29 overnight)

**Files created/modified:**

| File | Purpose |
|------|---------|
| `src/models.py` | Pydantic schemas: Paper, Claim, Evidence, Gap, TopicProposal, RunManifest |
| `src/ingest.py` | Semantic Scholar API + fixture fallback ingestion |
| `src/extractors.py` | Heuristic + LLM claim/evidence extraction |
| `src/gap_scorer.py` | Gap detection/scoring + topic suggestion |
| `src/cli.py` | Typer CLI: run, status, fetch-papers commands |
| `src/__main__.py` | `python -m src` entry point |
| `src/fixtures/papers_fixture.jsonl` | 18 real-world papers on NA delivery/LNP/mRNA |
| `tests/test_pipeline.py` | 18 pytest tests (models, extractors, scorer, fixture) |
| `data/processed/papers.jsonl` | (cached after ingest) |
| `data/processed/claims.jsonl` | (cached after extraction) |
| `data/processed/evidence.jsonl` | (cached after extraction) |
| `data/processed/gaps.jsonl` | (cached after gap scoring) |
| `data/processed/topics.jsonl` | (cached after topic suggestion) |
| `reports/latest_run.md` | (cached after pipeline run) |

### Pipeline results

| Metric | Heuristic mode | LLM mode |
|--------|----------------|----------|
| Papers ingested | 18 | 18 |
| Claims extracted | 6 | — (running) |
| Evidence extracted | 63 | — |
| Gaps identified | 31 | — |
| Topics proposed | 5 | — |

### Next coding session
- [ ] Reduce false-positive claims (heuristic triggers too conservative → only 6 claims from 18 papers)
- [ ] Improve gap domain clustering with embedding similarity
- [ ] Add memorization guard: citation-grounded extracts only
- [ ] Web-based report viewer or HTML export
