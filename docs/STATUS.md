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

## Current stage: **Stage 1 — Pipeline MVP** ✅ (as of 2026-07-30)

The vertical slice is **shipped and tested**. Full pipeline: ingest → extract → gap-score → topic-suggest → report.

### Stage checklist
- [x] S0 Freeze scope 1-pager for prof (problem, domain, eval, risks)
- [x] S1 Data schemas: Paper, Claim, Evidence, Gap, TopicProposal (Pydantic)
- [x] S1 Ingest 10–20 papers (Semantic Scholar + arXiv) in fixed domain slice
- [x] S1 Claim extractor (LLM → structured JSON + quote spans)
- [x] S1 Result/evidence extractor (tables/metrics/limitations)
- [x] S1 Gap aligner + simple scorer
- [x] S1 Topic suggester (3–5 candidates with experiments)
- [x] S1 CLI: `python -m src run` end-to-end on sample
- [x] S1 Eval harness sketch (pytest — 18 tests)
- [x] S1 Notes for supervisor + next meeting agenda
- [x] **Vertical slice complete — ready for supervisor demo**

### What shipped (2026-07-29 overnight build)

| Metric | Value |
|--------|-------|
| Papers ingested | 18 |
| Claims extracted | 6 (heuristic) |
| Evidence items | 63 |
| Gaps identified | 31 |
| Topic proposals | 5 |
| pytest tests | 18 (all passing) |
| Pipeline run time | ~0.2 seconds (heuristic, local) |
| CLI commands | `run`, `status`, `fetch-papers` |
| Report format | Markdown → `reports/latest_run.md` |

### Stage 2 roadmap
- [ ] S2 Improve claim recall (better heuristic + embedding similarity)
- [ ] S2 Embedding-based gap alignment
- [ ] S2 Memorization benchmark (post-cutoff held-out papers)
- [ ] S2 Expand corpus to 50+ papers via live S2 API
- [ ] S2 HTML report export
- [ ] S2 Expand to a second domain (e.g., hybrid ncRNA)
- [ ] S2 Add eval harness with human feedback collection
- [ ] Register BG4801 when eligible

## Next supervisor meeting: **30 July 2026, 14:00 SGT**
- Deliverable: `docs/supervisor-update-draft.md`
- Demo: Pipeline run + top gaps + topic proposals
- Questions: domain scope, eval rubric, memorization rigor, next steps

## Last automated progress
- 2026-07-29 00:34: Full code vertical slice built, tested (18/18), and committed.
- Pipeline: `python -m src run` → 18 papers → 6 claims → 63 evidence → 31 gaps → 5 topics → markdown report.
- 18 pytest tests covering models, extractors, gap scorer, and fixture loading.

## Daily loop
- **10:00 SGT** — autonomous coding progress on next unchecked item; commit/push; update this file
- **21:00 SGT** — Telegram voice call: review progress, decisions, next day focus
