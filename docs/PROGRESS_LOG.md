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
| 2026-07-30 07:38 | wave 4 | Memorization bench + HTML report + corpus 30 |
| 2026-07-30 10:06 | **wave 5 (this)** | Corpus 52 + domain pack + human feedback |

### Wave 5 summary (2026-07-30 10:06 SGT)

**Goal:** Close remaining Stage-2 checklist items before 14:00 supervisor meeting — 50+ corpus, second-domain pack, feedback harness.

**New / updated:**
| Path | Role |
|------|------|
| `src/fixtures/papers_fixture.jsonl` | 30 → **52** (21× year≥2024; 19 hybrid/ncRNA-tagged) |
| `src/eval/domain_pack.py` | LNP core / hybrid ncRNA / gene editing coverage gates |
| `src/eval/feedback.py` | Likert 1–5 + labels JSONL store + summary |
| `src/models.py` | `FeedbackRecord`, `FeedbackTargetType` |
| `src/cli.py` | `domain-pack`, `feedback-add`, `feedback-summary`; run `--domain-pack` |
| `src/extract/claims.py` | Domain tags: hybrid_ncrna, sirna, gene_therapy, immunogenicity |
| `src/gap/score.py` | Expanded hybrid_ncrna keyword list |
| `src/topics/suggest.py` | Templates: ncrna kinetic gating, async_escape |
| `tests/test_pipeline.py` | 34 → **37** tests |
| `reports/domain_pack.md` | Pack eval artifact |
| `reports/feedback_summary.md` | Feedback aggregate |

**Pipeline counts (heuristic extract, limit 52, embedding aligner):**

| Metric | Value |
|--------|-------|
| Papers | 52 |
| Claims | 88 |
| Evidence | 160 |
| Gaps | 89 |
| Topics | 5 |
| Mem-bench | PASS (100%/100% ground, 0% leak, post-cutoff n=21) |
| Domain pack | PASS (core 33/75, hybrid 23/34, editing 10/19) |
| pytest | 37 passed |

### Wave 4 summary (2026-07-30 07:38 SGT)

Memorization bench + HTML report + corpus 18→30. See prior STATUS.

### Live API note
- S2 + arXiv previously returned **HTTP 429**; backoff/retry now in client. Fixture fallback remains default for demos without key.

### Next coding session
- [ ] Live corpus expansion with S2 API key
- [ ] Run closed-book LLM probe on held-out titles and log risk
- [ ] Pack-aware topic ranking (prefer hybrid templates on hybrid gaps)
- [ ] Optional: deploy refreshed `site/public/data` bundle to fyp.vasanth.my
- [ ] Collect real supervisor ratings via feedback CLI after meeting
