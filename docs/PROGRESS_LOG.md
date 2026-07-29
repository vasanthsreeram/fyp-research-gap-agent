# FYP Research Gap Agent — PROGRESS LOG

## Build log

| Date (SGT) | Commits / wave | Milestone |
|------------|----------------|-----------|
| 2026-06-29 | `25d3eec`, `ed90329` | Initial docs stub: README, fyp-brief, initial-plan |
| 2026-07-01 | `3e7ccc7` | Prof meeting docs + STATUS board |
| 2026-07-29 00:24 | `cfc2d9d` | Daily cron + call loop notes |
| 2026-07-29 00:34 | `484194f` | Stage 1 vertical slice (flat modules) |
| 2026-07-29 01:11 | wave 2 | Modular packages + claim recall + LLM run |
| 2026-07-29 10:05 | wave 3 | Embedding gap alignment (MiniLM + Chroma) |
| 2026-07-30 07:38 | **wave 4 (this)** | Memorization bench + HTML report + corpus 30 |

### Wave 4 summary (2026-07-30 07:38 SGT)

**Goal:** Ship supervisor-facing memorization guard + HTML report + thicker fixture corpus before 14:00 SGT meeting.

**New / updated:**
| Path | Role |
|------|------|
| `src/eval/memorization.py` | Quote grounding, year held-out split, cross-era leakage, optional closed-book LLM |
| `src/eval/__init__.py` | Package export |
| `src/report.py` | Markdown + self-contained HTML report builders |
| `src/cli.py` | `--format`, `--mem-bench`, `mem-bench` command |
| `src/ingest/semantic_scholar.py` | Exponential backoff on 429/5xx + Retry-After |
| `src/fixtures/papers_fixture.jsonl` | 18 → **30** papers (7× year≥2024 held-out; hybrid ncRNA / editing) |
| `src/gap/score.py` | Domain tags: hybrid_ncrna, circRNA, SORT, complement |
| `src/topics/suggest.py` | Templates for hybrid_ncrna + gene_therapy |
| `tests/test_pipeline.py` | 30 → **34** tests |
| `reports/latest_run.html` | HTML export |
| `reports/memorization_bench.md` | Bench artifact |

**Pipeline counts (heuristic extract, limit 30, embedding aligner):**

| Metric | Value |
|--------|-------|
| Papers | 30 |
| Claims | 50 |
| Evidence | 105 |
| Gaps | 56 |
| Topics | 5 |
| Mem-bench | PASS (grounding 100% / 100%, leakage 0%, post-cutoff n=7) |
| pytest | 34 passed |

### Wave 3 summary (2026-07-29 10:05 SGT)

Embedding gap alignment (MiniLM + Chroma). See prior STATUS / git history.

### Live API note
- S2 + arXiv previously returned **HTTP 429**; backoff/retry now in client. Fixture fallback remains default for demos without key.

### Next coding session
- [ ] Live corpus expansion toward 50+ (S2 API key + sustained backoff)
- [ ] Run closed-book LLM probe on held-out titles and log risk
- [ ] Human feedback collection UI/schema on gap/topic quality
- [ ] Deeper hybrid ncRNA second-domain eval pack
- [ ] Optional: deploy refreshed `site/public/data` bundle to fyp.vasanth.my
