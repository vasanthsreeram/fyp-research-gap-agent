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

## Current stage: **Stage 2** (2026-07-30 21:10 SGT)

Wave 6 — **memorization safeguards v2**: structured claims + expanded mem harness (unsupported / hallucinated cites / overconfidence / controlled suite). Docs: `docs/memorization-eval.md`.

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
- [ ] Register BG4801 when eligible
- [ ] Live S2 API key path for non-fixture 50+ refresh
- [ ] Closed-book LLM mem probe on held-out titles (optional; run with small/open model)
- [ ] Richer hybrid-specific topic ranking (pack-aware suggester)

### What shipped (2026-07-30 21:10 SGT — wave 6 mem safeguards)

| Metric | Value |
|--------|-------|
| Papers | **52** (fixture; **21** year≥2024 held-out) |
| Claims (heuristic) | **88** (structured slots filled) |
| Evidence | **160** |
| pytest | **40 passed** (was 37) |
| Mem-bench | **PASS** — ground 100%/100%, unsup 0%, cite 0%, over 0%, leak 0%, controlled 7/7 |
| Structure | hyp=62%, any=100%, full(≥3 slots)=18/88 |
| Docs | `docs/memorization-eval.md` plan + metrics + how-to-run |

**New / updated (wave 6)**
```
src/models.py              # Claim: hypothesis, evidence, mechanism, assumptions, uncertainty
src/extract/claims.py      # structure_claim_fields + grounded quote_span + LLM schema
src/eval/memorization.py   # unsupported / citation / overconfidence / structure / controlled suite
src/cli.py                 # mem-bench --controlled; richer mem metrics in run
tests/test_pipeline.py     # +3 mem/structure tests
docs/memorization-eval.md  # plan, test cases, recommended metrics
```

**Demo commands**
```bash
python -m src.cli mem-bench --fixture --limit 52 --cutoff-year 2024
python -m src.cli run --limit 52 --fixture --mode heuristic --aligner embedding --format both
python -m pytest tests/ -q
# optional closed-book (API key; prefer small model):
# OPENAI_MODEL=gpt-4o-mini python -m src.cli mem-bench --fixture --limit 21 --closed-book
open reports/memorization_bench.md
```

### Latest mem-bench (wave 6)
- Cutoff 2024 · pre=31 · post=21
- Claim grounding 88/88 · Evidence 160/160
- Unsupported 0 · Hallucinated citations 0 · Overconfidence 0 · Leakage 0
- Controlled synthetic suite 7/7 PASS
- Structure coverage: hypothesis 62%, any slot 100%

### Known blockers / honesty notes
- **Prototype stage** — heuristic extractor + fixture corpus for reliable offline demos; not a production lit-mining system.
- Live Semantic Scholar / arXiv still fragile without API key (429s); fixture path is demo-reliable. Backoff/retry added.
- OpenAI key resolved from Keychain `openclaw/tgcallskill/openai-api-key` (not committed) for LLM extract / optional closed-book probe.
- Closed-book LLM memorization probe not run in default cron path (offline-first); enable with `mem-bench --closed-book`. Prefer open/small models.
- Detectors are **proxy safeguards**, not proof of non-memorization — see `docs/memorization-eval.md`.
- Hybrid pack still shares many LNP-tagged topics — pack-aware topic ranking is next polish.
- Do not claim wet-lab results; software/methods/prototype only.

## Next supervisor meeting: **30 July 2026, 14:00 SGT**
- Deliverable: `docs/EMAIL_TO_SUPERVISOR.md` + `docs/supervisor-update-draft.md`
- Demo: Pipeline run (52) + dual-domain pack + HTML report + **mem-bench v2** + feedback CLI
- Board: https://fyp.vasanth.my
- Questions: domain scope (LNP vs hybrid ncRNA weight), eval rubric labels, memorization rigor, next steps

## Last automated progress
- 2026-07-30 21:10 SGT — Wave 6 memorization safeguards: structured claims + unsupported/citation/overconfidence detectors + controlled suite; mem PASS; 40 tests; `docs/memorization-eval.md`.

## Daily loop
- **10:00 SGT** — autonomous coding progress on next unchecked item; commit/push; update this file
- **21:00 SGT** — Telegram voice call: review progress, decisions, next day focus
