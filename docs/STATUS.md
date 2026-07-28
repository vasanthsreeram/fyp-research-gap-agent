# FYP STATUS — living board
Updated by daily progress cron + human/call notes.

## Identity
- Supervisor: **Asst Prof Aaron Andrew Smargon** <aaron.smargon@ntu.edu.sg>
- Portal interest: **CBE/26/143** Modelling gene editing efficiency with generative AI
- Meeting notes: docs/MEETING_SMARGON.md (always cite this meeting in supervisor emails)
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

## Current stage: **0 → 1 foundation** (as of 2026-07-29)
Repo is still a **docs-only stub** (2 commits on 2026-07-01). No pipeline code yet.

### Stage checklist
- [ ] S0 Freeze scope 1-pager for prof (problem, domain, eval, risks)
- [ ] S1 Data schemas: Paper, Claim, Evidence, Gap, TopicProposal (Pydantic)
- [ ] S1 Ingest 10–20 papers (Semantic Scholar + arXiv) in fixed domain slice
- [ ] S1 Claim extractor (LLM → structured JSON + quote spans)
- [ ] S1 Result/evidence extractor (tables/metrics/limitations)
- [ ] S1 Gap aligner + simple scorer
- [ ] S1 Topic suggester (3–5 candidates with experiments)
- [ ] S1 CLI: `python -m src run --corpus data/...` end-to-end on sample
- [ ] S1 Eval harness sketch (memorization check + human rubric)
- [ ] S1 Notes for supervisor + next meeting agenda
- [ ] S2 Expand corpus, better scoring, UI or report export
- [ ] Register BG4801 when eligible

## Last automated progress
- 2026-07-29: STATUS board committed (`7e1610c`); daily progress cron 10:00 SGT + daily voice call 21:00 SGT created. No code slice yet.

## Open questions for Vas (call)
1. Supervisor locked: Smargon <aaron.smargon@ntu.edu.sg>; CBE/26/143 anchor
2. v0 corpus: gene-editing efficiency / structure-function / NA delivery (flexible)
3. Stack: OpenAI available via keychain; local optional later
4. Call 2026-07-30 **10:30 SGT** email prep; daily 21:00 still on

## Daily loop
- **10:00 SGT** — autonomous coding progress on next unchecked item; commit/push; update this file
- **21:00 SGT** — Telegram voice call: review progress, decisions, next day focus
