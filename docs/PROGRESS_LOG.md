# FYP Research Gap Agent — PROGRESS LOG

## Build log

| Date (SGT) | Commits / wave | Milestone |
|------------|----------------|-----------|
| 2026-06-29 | `25d3eec`, `ed90329` | Initial docs stub: README, fyp-brief, initial-plan |
| 2026-07-01 | `3e7ccc7` | Prof meeting docs + STATUS board |
| 2026-07-29 00:24 | `cfc2d9d` | Daily cron + call loop notes |
| 2026-07-29 00:34 | `484194f` | Stage 1 vertical slice (flat modules) |
| 2026-07-29 01:11 | wave 2 | Modular packages + claim recall + LLM run |
| 2026-07-29 10:05 | **wave 3 (this)** | Embedding gap alignment (MiniLM + Chroma) |

### Wave 3 summary (2026-07-29 10:05 SGT)

**Goal:** Ship S2 embedding-based claim↔evidence alignment.

**New / updated:**
| Path | Role |
|------|------|
| `src/gap/embeddings.py` | ST encode, cosine, pairwise match, Chroma build/query |
| `src/gap/score.py` | `aligner=auto\|lexical\|embedding`; embedding thresholds |
| `src/cli.py` | `--aligner`, `--no-chroma`; report + manifest fields |
| `src/models.py` | `RunManifest.aligner_mode` |
| `tests/test_pipeline.py` | 30 tests (embedding suite skip-safe if deps missing) |

**Pipeline counts (heuristic extract, limit 15):**

| Aligner | Papers | Claims | Evidence | Gaps | Topics |
|---------|--------|--------|----------|------|--------|
| lexical | 15 | 27 | 56 | 32 | 5 |
| **embedding** | **15** | **27** | **56** | **30** | **5** |

Model: `sentence-transformers/all-MiniLM-L6-v2` · Index: `data/processed/chroma_gap_index/` (gitignored)

### Wave 2 summary (2026-07-29 01:11 SGT)

See git history / prior STATUS. Heuristic 27 claims / LLM 91 claims on 15 papers.

### Live API note
- S2 + arXiv both returned **HTTP 429** during refetch; fixture fallback engaged automatically.

### Next coding session
- [ ] Memorization guard benchmark on post-cutoff papers
- [ ] Backoff/retry + S2 API key for live corpus expansion to 50+
- [ ] HTML report export
- [ ] Second domain slice (hybrid ncRNA)
- [ ] Human feedback collection on gap/topic quality
