# FYP Research Gap Agent — PROGRESS LOG

## Build log

| Date (SGT) | Commits / wave | Milestone |
|------------|----------------|-----------|
| 2026-06-29 | `25d3eec`, `ed90329` | Initial docs stub: README, fyp-brief, initial-plan |
| 2026-07-01 | `3e7ccc7` | Prof meeting docs + STATUS board |
| 2026-07-29 00:24 | `cfc2d9d` | Daily cron + call loop notes |
| 2026-07-29 00:34 | `484194f` | Stage 1 vertical slice (flat modules) |
| 2026-07-29 01:11 | **wave 2 (this)** | Modular packages + claim recall + LLM run |

### Wave 2 summary (2026-07-29 01:11 SGT)

**Goal:** Maximize shipped code before supervisor email deadline 2026-07-30 14:00 SGT.

**Code structure (matches planned modules):**

| Path | Role |
|------|------|
| `src/models.py` | Paper, Claim, Evidence, Gap, TopicProposal, RunManifest |
| `src/ingest/semantic_scholar.py` | S2 Graph API search + convert + raw cache |
| `src/ingest/arxiv_client.py` | arXiv Atom API helper |
| `src/ingest/pipeline.py` | Live merge → dedupe → fixture fallback → `data/processed/papers.jsonl` |
| `src/extract/claims.py` | Higher-recall heuristic + LLM claims |
| `src/extract/evidence.py` | Results / metrics / limitations |
| `src/extract/llm_util.py` | Keychain `openclaw/tgcallskill/openai-api-key` + OpenAI client |
| `src/extract/dispatch.py` | `extract_all(mode=auto\|llm\|heuristic)` |
| `src/gap/score.py` | Align + multi-axis score (Jaccard + TF-cosine) |
| `src/topics/suggest.py` | Domain-clustered topic proposals |
| `src/cli.py` | `run --limit N`, `fetch-papers`, `status` |
| `tests/test_pipeline.py` | 23 tests (schemas, extractors, scorer, fixture offline path) |

**Compatibility shims:** `src/extractors.py`, `src/gap_scorer.py` re-export new packages.

### Pipeline counts

| Mode | Papers | Claims | Evidence | Gaps | Topics |
|------|--------|--------|----------|------|--------|
| Heuristic (v0.1 overnight) | 18 | 6 | 63 | 31 | 5 |
| Heuristic (v0.2, limit 15) | 15 | **27** | 56 | 32 | 5 |
| **LLM (v0.2, limit 15)** | **15** | **91** | **102** | **47** | **5** |

Artifacts:
- `data/processed/{papers,claims,evidence,gaps,topics}.jsonl`
- `data/processed/run_manifest.json`
- `data/raw/papers_selected.jsonl`
- `reports/latest_run.md`

### Live API note
- S2 + arXiv both returned **HTTP 429** during refetch; fixture fallback engaged automatically. Clients + raw-cache paths are implemented and ready when rate limits clear / API key added (`S2_API_KEY`).

### Next coding session
- [ ] Embedding similarity for gap alignment (sentence-transformers optional extra)
- [ ] Memorization guard benchmark on post-cutoff papers
- [ ] Backoff/retry + S2 API key for live corpus expansion to 50+
- [ ] HTML report export
- [ ] Second domain slice (hybrid ncRNA)
