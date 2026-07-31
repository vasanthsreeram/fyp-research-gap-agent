# FYP STATUS — living board

Updated by daily progress cron + human/call notes.

## Identity
- Student: Sreeram Vasanth (U2322909K)
- Repo: https://github.com/vasanthsreeram/fyp-research-gap-agent
- Local: /Users/admin/projects/fyp-research-gap-agent
- Module: BG4801 (not registered yet; audit “Project Not Eligible”)
- Working title: Research Gap Agent — AI agents that find theory↔experiment gaps and propose high-impact biology topics

## Supervisor notes (2026-07-01 meeting)
- Not generic lit-search — scientifically surprising, high-impact biology ideas
- Safeguard LLM memorization (post-cutoff papers, open/small models, memorization tests)
- Candidate domain: protein/nucleic-acid chemistry, hybrid/bifunctional ncRNA, molecular engineering, NA delivery, testable mechanisms
- Write notes + propose approaches; formal start ~August; early progress welcome
- Audio/transcript: ~/.openclaw/workspace/tmp/fyp-prof-meeting/

## Current stage: **Stage 2** (2026-07-31 10:05 SGT)

Wave 7 — **pack-aware topic ranking**: hybrid/gene packs reserved in top-k; primary-pack gap assignment stops LNP mass from absorbing hybrid topics.

### Stage checklist
- [x] S0 Freeze scope 1-pager for prof (problem, domain, eval, risks)
- [x] S1 Data schemas: Paper, Claim, Evidence, Gap, TopicProposal (Pydantic)
- [x] S1 Ingest 10–20 papers (Semantic Scholar + arXiv clients + fixture fallback)
- [x] S1 Claim extractor (LLM → structured JSON + quote spans; heuristic fallback)
- [x] S1 Result/evidence extractor (tables/metrics/limitations)
- [x] S1 Gap aligner + simple scorer (Jaccard+TF cosine blend)
- [x] S1 Topic suggester (3–5 candidates with experiments)
- [x] S1 CLI: `python -m src.cli run --limit 15` end-to-end
- [x] S1 Eval harness sketch (pytest)
- [x] S1 Notes for supervisor + next meeting agenda
- [x] **Vertical slice complete — ready for supervisor demo**
- [x] S2 Modular package split (`src/ingest`, `src/extract`, `src/gap`, `src/topics`)
- [x] S2 Claim recall lift (heuristic 6→27 on 15 papers; LLM 91 claims)
- [x] **S2 Embedding-based gap alignment (sentence-transformers / chroma)**
- [x] **S2 Memorization benchmark (quote grounding + post-cutoff leakage + optional closed-book)**
- [x] **S2 HTML report export** (`reports/latest_run.html`)
- [x] S2 Fixture corpus expanded to 30 (7 post-2024 held-out; hybrid ncRNA / gene-editing slices)
- [x] **S2 Expand corpus to 50+ papers** (fixture offline path; 52 papers, 21 post-2024) — live S2 still rate-limit sensitive without key
- [x] **S2 Full second-domain eval pack** (`src/eval/domain_pack.py`; LNP core / hybrid ncRNA / gene editing gates)
- [x] **S2 Add eval harness with human feedback collection** (`feedback-add` / `feedback-summary`; JSONL store)
- [x] **S2 Memorization safeguards v2** — unsupported claims, hallucinated citations, overconfidence, structured claim slots, controlled suite (`docs/memorization-eval.md`)
- [x] **S2 Richer hybrid-specific topic ranking (pack-aware suggester)** — primary pack + reserved slots + rank_score
- [ ] Register BG4801 when eligible
- [ ] Live S2 API key path for non-fixture 50+ refresh
- [ ] Closed-book LLM mem probe on held-out titles (optional; run with small/open model)

### What shipped (2026-07-31 10:05 SGT — wave 7 pack-aware topics)

| Metric | Value |
|--------|-------|
| Papers | **52** (fixture; **21** year≥2024 held-out) |
| Claims (heuristic) | **88** |
| Evidence | **160** |
| Gaps | **103** |
| Topics (balanced) | **5** — packs: hybrid + gene_editing + lnp_core |
| Domain pack | **PASS** (hybrid topics now **2** dedicated) |
| pytest | **42 passed** (was 40) |
| Mem-bench | **PASS** — ground 100%/100%, unsup/cite/over/leak 0% |

**New / updated (wave 7)**
```
src/topics/suggest.py   # pack-aware ranking, primary pack, diversity slots
src/models.py           # TopicProposal.pack_id + rank_score
src/cli.py              # --pack-balance/--no-pack-balance
src/eval/domain_pack.py # match topics by pack_id
src/report.py           # pack + rank in md/html
tests/test_pipeline.py  # +2 pack-aware tests
```

**Before → after (topic top-k):** LNP-only lists → hybrid ncRNA + gene editing + LNP co-ranked.

**Demo commands**
```bash
python -m src.cli run --limit 52 --fixture --mode heuristic --aligner lexical --format both
python -m src.cli domain-pack --limit 52 --fixture
python -m src.cli mem-bench --fixture --limit 52 --cutoff-year 2024
python -m pytest tests/ -q
# disable pack balance to compare:
# python -m src.cli run --limit 52 --fixture --no-pack-balance --mode heuristic
```

### Known blockers / honesty notes
- **Prototype stage** — heuristic extractor + fixture corpus for reliable offline demos; not a production lit-mining system.
- Live Semantic Scholar / arXiv still fragile without API key (429s); fixture path is demo-reliable. Backoff/retry added.
- OpenAI key resolved from Keychain `openclaw/tgcallskill/openai-api-key` (not committed) for LLM extract / optional closed-book probe.
- Closed-book LLM memorization probe not run in default cron path (offline-first); enable with `mem-bench --closed-book`. Prefer open/small models.
- Detectors are **proxy safeguards**, not proof of non-memorization — see `docs/memorization-eval.md`.
- Pack balance is a ranking policy (reserved slots + soft boosts), not wet-lab priority truth.
- Do not claim wet-lab results; software/methods/prototype only.

## Next supervisor meeting: **30 July 2026, 14:00 SGT**
- Deliverable: `docs/EMAIL_TO_SUPERVISOR.md` + `docs/supervisor-update-draft.md`
- Demo: Pipeline run (52) + dual-domain pack + HTML report + **mem-bench v2** + **pack-aware topics** + feedback CLI
- Board: https://fyp.vasanth.my
- Questions: domain scope (LNP vs hybrid ncRNA weight), eval rubric labels, memorization rigor, next steps

## Last automated progress
- 2026-07-31 10:05 SGT — Wave 7 pack-aware topic ranking: hybrid/gene reserved in top-k; primary-pack assignment; TopicProposal.pack_id/rank_score; 42 tests; domain pack PASS with hybrid topics.

## Daily loop
- **10:00 SGT** — autonomous coding progress on next unchecked item; commit/push; update this file
- **21:00 SGT** — Telegram voice call: review progress, decisions, next day focus
