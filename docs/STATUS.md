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

## Current stage: **Stage 1 complete → Stage 2 started** (2026-07-29 01:11 SGT)

Modular package layout + higher-recall extractors + live LLM path shipped. Offline heuristic path still works without keys.

### Stage checklist
- [x] S0 Freeze scope 1-pager for prof (problem, domain, eval, risks)
- [x] S1 Data schemas: Paper, Claim, Evidence, Gap, TopicProposal (Pydantic)
- [x] S1 Ingest 10–20 papers (Semantic Scholar + arXiv clients + fixture fallback)
- [x] S1 Claim extractor (LLM → structured JSON + quote spans; heuristic fallback)
- [x] S1 Result/evidence extractor (tables/metrics/limitations)
- [x] S1 Gap aligner + simple scorer (Jaccard+TF cosine blend)
- [x] S1 Topic suggester (3–5 candidates with experiments)
- [x] S1 CLI: `python -m src.cli run --limit 15` end-to-end
- [x] S1 Eval harness sketch (pytest — 23 tests)
- [x] S1 Notes for supervisor + next meeting agenda
- [x] **Vertical slice complete — ready for supervisor demo**
- [x] S2 Modular package split (`src/ingest`, `src/extract`, `src/gap`, `src/topics`)
- [x] S2 Claim recall lift (heuristic 6→27 on 15 papers; LLM 91 claims)
- [ ] S2 Embedding-based gap alignment (sentence-transformers / chroma)
- [ ] S2 Memorization benchmark (post-cutoff held-out papers)
- [ ] S2 Expand corpus to 50+ papers via live S2 API (currently rate-limited 429; fixture used)
- [ ] S2 HTML report export
- [ ] S2 Expand to a second domain (e.g., hybrid ncRNA)
- [ ] S2 Add eval harness with human feedback collection
- [ ] Register BG4801 when eligible

### What shipped (2026-07-29 overnight wave 2)

| Metric | Heuristic (limit 15) | LLM (limit 15) |
|--------|----------------------|----------------|
| Papers | 15 | 15 |
| Claims | 27 | **91** |
| Evidence | 56 | **102** |
| Gaps | 32 | **47** |
| Topics | 5 | 5 |
| pytest | 23 passed | 23 passed |
| CLI | `python -m src.cli run --limit 15` | same |
| Report | `reports/latest_run.md` | same |

**Package layout**
```
src/models.py
src/cli.py
src/ingest/{semantic_scholar.py, arxiv_client.py, pipeline.py}
src/extract/{claims.py, evidence.py, dispatch.py, llm_util.py}
src/gap/score.py
src/topics/suggest.py
```

**Demo command**
```bash
python -m src.cli run --limit 15 --fixture --mode heuristic   # offline
python -m src.cli run --limit 15 --fixture --mode llm         # Keychain OpenAI
python -m src.cli run --limit 15 --refetch                    # live S2+arXiv (falls back on 429)
```

### Latest LLM run (run_f2c2ec7db50c)
- Top gaps: endosomal-escape toxicity tradeoff; visualization of escape; fusion vs destabilization mechanism
- Top topics: mRNA nucleoside×LNP synergy; ligand avidity vs specificity; endosomal escape mechanism; vaccine-domain gaps; siRNA extrahepatic barrier

### Known blockers
- Semantic Scholar + arXiv returned HTTP 429 during live ingest (2026-07-29 ~01:08 SGT); pipeline correctly fell back to 18-paper fixture (truncated to `--limit 15`).
- OpenAI key resolved from Keychain `openclaw/tgcallskill/openai-api-key` (not committed).

## Next supervisor meeting: **30 July 2026, 14:00 SGT**
- Deliverable: `docs/supervisor-update-draft.md`
- Demo: Pipeline run + top gaps + topic proposals
- Questions: domain scope, eval rubric, memorization rigor, next steps

## Last automated progress
- 2026-07-29 01:11 SGT — Wave 2: modular packages, claim-recall lift, LLM end-to-end (15 papers → 91 claims → 102 evidence → 47 gaps → 5 topics), 23/23 tests, docs refreshed.

## Daily loop
- **10:00 SGT** — autonomous coding progress on next unchecked item; commit/push; update this file
- **21:00 SGT** — Telegram voice call: review progress, decisions, next day focus
