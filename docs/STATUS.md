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

## Current stage: **Stage 2** (2026-07-30 07:38 SGT)

Memorization/grounding bench + HTML report + expanded fixture corpus (30 papers, 7 post-2024 held-out). Embedding aligner remains default when deps present.

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
- [ ] S2 Expand corpus to 50+ papers via live S2 API (backoff/retry shipped; still rate-limit sensitive without key)
- [ ] S2 Full second-domain eval pack (hybrid ncRNA templates started)
- [ ] S2 Add eval harness with human feedback collection
- [ ] Register BG4801 when eligible

### What shipped (2026-07-30 morning — mem-bench + HTML + corpus)

| Metric | Value |
|--------|-------|
| Papers | **30** (fixture; 7 year≥2024 held-out) |
| Claims | **50** |
| Evidence | **105** |
| Gaps | **56** |
| Topics | **5** |
| pytest | **34 passed** |
| Aligner | MiniLM cosine + Chroma |
| Mem-bench | **PASS** — claim/evidence grounding 100%, leakage 0% |
| Reports | `reports/latest_run.md`, `reports/latest_run.html`, `reports/memorization_bench.md` |

**New modules**
```
src/eval/memorization.py   # quote grounding, year held-out, cross-era leakage, optional closed-book LLM
src/report.py              # markdown + self-contained HTML builders
CLI: run --format md|html|both --mem-bench --cutoff-year
CLI: mem-bench             # standalone benchmark command
S2 client: exponential backoff on 429/5xx + Retry-After
```

**Demo commands**
```bash
python -m src.cli run --limit 30 --fixture --mode heuristic --aligner embedding --format both
python -m src.cli mem-bench --fixture --limit 30 --cutoff-year 2024
python -m pytest tests/ -q
open reports/latest_run.html
```

### Latest run (`run_382657f2bd94`)
- Top gaps: extrahepatic + endosomal escape co-limitation; bulk extrahepatic targeting; nano-bio interaction fundamentals; brain delivery barrier; untested bifunctional ncRNA co-delivery claim
- Top topics: ligand avidity vs specificity; innate immune decoupling; endosomal escape mechanism; cascade bottleneck analysis; rational ionizable lipids for extrahepatic delivery
- Mem-bench: 23 pre / 7 post cutoff; grounding 50/50 claims, 105/105 evidence

### Known blockers
- Live Semantic Scholar / arXiv still fragile without API key (429s); fixture path is demo-reliable. Backoff/retry added.
- OpenAI key resolved from Keychain `openclaw/tgcallskill/openai-api-key` (not committed) for LLM extract / optional closed-book probe.
- Closed-book LLM memorization probe not run in default cron path (offline-first); enable with `mem-bench --closed-book`.

## Next supervisor meeting: **30 July 2026, 14:00 SGT**
- Deliverable: `docs/supervisor-update-draft.md`
- Demo: Pipeline run + top gaps + topics + HTML report + memorization bench PASS
- Board: https://fyp.vasanth.my
- Questions: domain scope (LNP vs hybrid ncRNA weight), eval rubric, memorization rigor, next steps

## Last automated progress
- 2026-07-30 07:38 SGT — S2 mem-bench + HTML report + fixture 18→30; E2E 30→50→105→56 gaps→5 topics; 34 tests; mem PASS.

## Daily loop
- **10:00 SGT** — autonomous coding progress on next unchecked item; commit/push; update this file
- **21:00 SGT** — Telegram voice call: review progress, decisions, next day focus
