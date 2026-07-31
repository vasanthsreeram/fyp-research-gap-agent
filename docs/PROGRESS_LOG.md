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
| 2026-07-30 10:06 | wave 5 | Corpus 52 + domain pack + human feedback |
| 2026-07-30 11:01 | pre-meeting | E2E re-verify `run_d4b35242b895` + supervisor email draft |
| 2026-07-30 21:10 | **wave 6** | Mem safeguards v2: structured claims + detectors + controlled suite |
| 2026-07-31 10:05 | **wave 7** | Pack-aware topic ranking (hybrid/gene reserved slots) |

### Wave 7 summary (2026-07-31 10:05 SGT)

**Goal:** Stop LNP-core mass from monopolizing top-k topics; surface hybrid/bifunctional ncRNA proposals for supervisor dual-slice demos.

**New / updated:**
| Path | Role |
|------|------|
| `src/topics/suggest.py` | Primary pack assignment, pack score boosts, diversity slots, vaccine template |
| `src/models.py` | `TopicProposal.pack_id`, `rank_score` |
| `src/cli.py` | `--pack-balance/--no-pack-balance` |
| `src/eval/domain_pack.py` | Topic slice match via `pack_id` |
| `src/report.py` | Pack + rank in markdown/HTML |
| `tests/test_pipeline.py` | 40 → **42** tests |

**Topic top-k (balanced, n=52 fixture):** hybrid ncRNA payload competition · gene-editing DNA–LNP scaffolds · LNP targeting · endosomal escape · immunogenicity.

### Wave 6 summary (2026-07-30 21:10 SGT)

**Goal:** Memorization safeguards depth — distinguish memorization vs grounded reasoning; structured claims; eval metrics doc.

**New / updated:**
| Path | Role |
|------|------|
| `src/models.py` | Claim slots: hypothesis, evidence, mechanism, assumptions, uncertainty |
| `src/extract/claims.py` | `structure_claim_fields`, better quote grounding, LLM JSON schema |
| `src/eval/memorization.py` | unsupported / citation / overconfidence / structure / controlled suite |
| `src/cli.py` | `mem-bench --controlled/--no-controlled`; richer run logs |
| `tests/test_pipeline.py` | 37 → **40** tests |
| `docs/memorization-eval.md` | Plan, test cases, recommended metrics, how-to-run |
| `reports/memorization_bench.md` | Expanded report |

**Mem-bench (heuristic, limit 52, cutoff 2024):**

| Metric | Value |
|--------|-------|
| Papers | 52 (pre 31 / post 21) |
| Claim / evidence grounding | 100% / 100% |
| Unsupported / cite / over / leak | 0% / 0% / 0% / 0% |
| Structure | hyp 62% · any 100% · full≥3 18/88 |
| Controlled suite | 7/7 PASS |
| Overall | **PASS** |
| pytest | 40 passed |

**How to run:**
```bash
python -m src.cli mem-bench --fixture --limit 52 --cutoff-year 2024
python -m pytest tests/test_pipeline.py::TestMemorization -q
```

### Wave 5 summary (2026-07-30 10:06 SGT)

Corpus 52 + domain pack + feedback harness. See prior STATUS.

### Live API note
- S2 + arXiv previously returned **HTTP 429**; backoff/retry now in client. Fixture fallback remains default for demos without key.

### Next coding session
- [ ] Live corpus expansion with S2 API key
- [ ] Run closed-book LLM probe on held-out titles with small/open model and log risk
- [ ] Pack-aware topic ranking (prefer hybrid templates on hybrid gaps)
- [ ] Optional: deploy refreshed `site/public/data` bundle to fyp.vasanth.my
- [ ] Collect real supervisor ratings via feedback CLI after meeting
