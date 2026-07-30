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

## Current stage: **Stage 2** (2026-07-30 11:01 SGT)

Corpus 52 + dual-domain pack eval (LNP core vs hybrid ncRNA) + human feedback harness. Mem-bench still PASS on expanded held-out set (21 post-2024). **Re-verified E2E before 14:00 supervisor email** (`run_d4b35242b895`).

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
- [ ] Register BG4801 when eligible
- [ ] Live S2 API key path for non-fixture 50+ refresh
- [ ] Closed-book LLM mem probe on held-out titles (optional)
- [ ] Richer hybrid-specific topic ranking (pack-aware suggester)

### What shipped (2026-07-30 11:01 SGT — pre-meeting re-verify)

| Metric | Value |
|--------|-------|
| Papers | **52** (fixture; **21** year≥2024 held-out) |
| Claims | **88** |
| Evidence | **160** |
| Gaps | **89** |
| Topics | **5** |
| pytest | **37 passed** |
| Aligner | MiniLM cosine + Chroma |
| Mem-bench | **PASS** — grounding 100%/100%, leakage 0% |
| Domain pack | **PASS** — lnp_core 33p/75g · hybrid_ncrna 23p/34g · gene_editing 10p/19g |
| Feedback | schema + CLI; 2 demo seed ratings |
| Reports | `latest_run.md/html`, `memorization_bench.md`, `domain_pack.md`, `feedback_summary.md` |
| Latest run | `run_d4b35242b895` (heuristic extract, embedding aligner) |

**New modules (Stage 2)**
```
src/eval/domain_pack.py   # dual/triple domain coverage gates
src/eval/feedback.py      # Likert + labels JSONL harness
src/eval/memorization.py  # quote grounding + leakage + optional closed-book
models.FeedbackRecord     # feedback schema
CLI: domain-pack | feedback-add | feedback-summary | mem-bench
CLI run: --domain-pack/--no-domain-pack --aligner embedding|lexical
fixtures: 30 → 52 (hybrid ncRNA / editing / async escape focus)
site/: passphrase-gated multi-page board → https://fyp.vasanth.my
```

**Demo commands**
```bash
python -m src.cli run --limit 52 --fixture --mode heuristic --aligner embedding --format both
python -m src.cli domain-pack --limit 52 --fixture --aligner lexical
python -m src.cli mem-bench --fixture --limit 52 --cutoff-year 2024
python -m src.cli feedback-add --type gap --id gap_xxx --rating 5 --labels surprising,testable
python -m src.cli feedback-summary
python -m pytest tests/ -q
open reports/latest_run.html
```

### Latest run (`run_d4b35242b895`)
- Top gaps: extrahepatic + endosomal escape co-limitation; bulk extrahepatic targeting; minimal extrahepatic after ADAR guides; nano-bio fundamentals; brain delivery barrier
- Hybrid pack gaps: payload co-delivery untested sync claim; PNA endosomal entrapment; structured RNA manufacturing; RNP competition under-tested
- Top topics: ligand avidity; innate immune decoupling; endosomal escape mechanism; cascade bottleneck; multi-dose PK
- Mem-bench: 31 pre / 21 post cutoff; grounding 88/88 claims, 160/160 evidence; leakage 0%

### Known blockers / honesty notes
- **Prototype stage** — heuristic extractor + fixture corpus for reliable offline demos; not a production lit-mining system.
- Live Semantic Scholar / arXiv still fragile without API key (429s); fixture path is demo-reliable. Backoff/retry added.
- OpenAI key resolved from Keychain `openclaw/tgcallskill/openai-api-key` (not committed) for LLM extract / optional closed-book probe.
- Closed-book LLM memorization probe not run in default cron path (offline-first); enable with `mem-bench --closed-book`.
- Hybrid pack still shares many LNP-tagged topics — pack-aware topic ranking is next polish.
- Do not claim wet-lab results; software/methods/prototype only.

## Next supervisor meeting: **30 July 2026, 14:00 SGT**
- Deliverable: `docs/EMAIL_TO_SUPERVISOR.md` + `docs/supervisor-update-draft.md`
- Demo: Pipeline run (52) + dual-domain pack PASS + HTML report + mem-bench PASS + feedback CLI
- Board: https://fyp.vasanth.my
- Questions: domain scope (LNP vs hybrid ncRNA weight), eval rubric labels, memorization rigor, next steps

## Last automated progress
- 2026-07-30 11:01 SGT — Pre-meeting E2E re-run `run_d4b35242b895`: 52→88→160→89 gaps→5 topics; mem PASS; domain pack PASS; 37 tests; email draft written for 14:00 send.

## Daily loop
- **10:00 SGT** — autonomous coding progress on next unchecked item; commit/push; update this file
- **21:00 SGT** — Telegram voice call: review progress, decisions, next day focus
