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

## Current stage: **Stage 2** (2026-07-29 10:05 SGT)

Embedding-based gap alignment shipped (sentence-transformers MiniLM + optional Chroma). Lexical path remains default fallback.

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
- [x] **S2 Embedding-based gap alignment (sentence-transformers / chroma)**
- [ ] S2 Memorization benchmark (post-cutoff held-out papers)
- [ ] S2 Expand corpus to 50+ papers via live S2 API (currently rate-limited 429; fixture used)
- [ ] S2 HTML report export
- [ ] S2 Expand to a second domain (e.g., hybrid ncRNA)
- [ ] S2 Add eval harness with human feedback collection
- [ ] Register BG4801 when eligible

### What shipped (2026-07-29 morning — embedding aligner)

| Metric | Heuristic + lexical | Heuristic + embedding |
|--------|---------------------|------------------------|
| Papers | 15 | 15 |
| Claims | 27 | 27 |
| Evidence | 56 | 56 |
| Gaps | 32 | **30** |
| Topics | 5 | 5 |
| pytest | 30 passed | 30 passed |
| Aligner | Jaccard+TF | MiniLM cosine + Chroma index |
| Report | `reports/latest_run.md` | same |

**Embedding stack**
```
src/gap/embeddings.py   # ST encode, cosine, optional Chroma persist
src/gap/score.py          # aligner=auto|lexical|embedding
CLI: --aligner auto|lexical|embedding  [--no-chroma]
Model: sentence-transformers/all-MiniLM-L6-v2
Index: data/processed/chroma_gap_index/ (gitignored)
```

**Demo command**
```bash
python -m src.cli run --limit 15 --fixture --mode heuristic --aligner embedding
python -m src.cli run --limit 15 --fixture --mode heuristic --aligner lexical
python -m src.cli run --limit 15 --fixture --mode llm --aligner auto
```

### Latest embedding run (run_6f4509f60aa4)
- Top gaps: extrahepatic targeting barrier; fundamental advances needed; <2% cargo to cytosol; non-hepatic delivery; scale-up efficiency drop
- Top topics: innate immune decoupling; ligand avidity vs specificity; PK of repeat-dose LNP; endosomal escape mechanism; cascade bottleneck analysis
- Kind mix (embedding): 15 theory_vs_experiment, 7 delivery_barrier, 6 other, 1 mechanism_unknown, 1 untested_claim

### Known blockers
- Semantic Scholar + arXiv returned HTTP 429 during live ingest (2026-07-29 ~01:08 SGT); pipeline correctly fell back to fixture.
- OpenAI key resolved from Keychain `openclaw/tgcallskill/openai-api-key` (not committed).
- First embedding run downloads MiniLM weights (~90MB) via HuggingFace.

## Next supervisor meeting: **30 July 2026, 14:00 SGT**
- Deliverable: `docs/supervisor-update-draft.md`
- Demo: Pipeline run + top gaps + topic proposals (+ show embedding vs lexical)
- Questions: domain scope, eval rubric, memorization rigor, next steps

## Last automated progress
- 2026-07-29 10:05 SGT — S2 embedding gap alignment: `src/gap/embeddings.py` (MiniLM + Chroma), CLI `--aligner`, 30/30 tests, E2E fixture run 15→27→56→30 gaps→5 topics.

## Daily loop
- **10:00 SGT** — autonomous coding progress on next unchecked item; commit/push; update this file
- **21:00 SGT** — Telegram voice call: review progress, decisions, next day focus
