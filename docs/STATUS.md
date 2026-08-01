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

## Current stage: **Stage 2** (2026-08-01 10:05 SGT)

Wave 8 — **cross-paper claim tension** + **live S2 key path** (env/Keychain, year filter, hybrid/gene queries).

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
- [x] **S2 Cross-paper claim tension gaps** — multi-paper dialectics (`src/gap/tension.py`; GapKind.CROSS_PAPER_TENSION)
- [x] **S2 Live S2 API key path** — env + Keychain resolve, year filter, hybrid/gene query pack, `s2-status` CLI *(key itself still missing on this machine)*
- [ ] Register BG4801 when eligible
- [ ] Store S2 API key (`S2_API_KEY` or Keychain `openclaw/fyp/s2-api-key`) and refresh live 50+ corpus
- [ ] Closed-book LLM mem probe on held-out titles (optional; run with small/open model)

### What shipped (2026-08-01 10:05 SGT — wave 8 cross-paper + live S2 path)

| Metric | Value |
|--------|-------|
| Papers | **52** (fixture; **21** year≥2024 held-out) |
| Claims (heuristic) | **88** |
| Evidence | **160** |
| Gaps | **104** (incl. **1** cross-paper tension; was 103) |
| Topics (balanced) | **5** — packs: hybrid + gene_editing + lnp_core |
| Domain pack | **PASS** |
| pytest | **46 passed** (was 42) |
| Mem-bench | **PASS** — ground 100%/100%, unsup/cite/over/leak 0% |
| S2 key on host | **absent** (path ready; use `python -m src.cli s2-status`) |

**New / updated (wave 8)**
```
src/gap/tension.py          # cross-paper stance clusters → tension gaps
src/gap/score.py            # wires tension pass; CROSS_PAPER scoring
src/models.py               # GapKind.CROSS_PAPER_TENSION
src/ingest/keys.py          # S2 env + Keychain resolver
src/ingest/semantic_scholar.py  # hybrid/gene queries, year filter, auth pacing
src/ingest/pipeline.py      # year_min/max + key resolve
src/cli.py                  # --year-min, --cross-paper, s2-status, fetch year flags
src/report.py               # multi-paper gap tags
tests/test_pipeline.py      # +4 tests (tension + s2 status)
```

**Top gap demo signal:** #1 is now a multi-paper dialectic on bilayer-disruption / endosomal-escape mechanism controversy (not single-paper template).

**Demo commands**
```bash
python -m src.cli run --limit 52 --fixture --mode heuristic --aligner lexical --format both
python -m src.cli domain-pack --limit 52 --fixture
python -m src.cli mem-bench --fixture --limit 52 --cutoff-year 2024
python -m src.cli s2-status
# after key is stored:
# python -m src.cli fetch-papers --limit 40 --year-min 2024
# python -m src.cli run --refetch --limit 40 --year-min 2024 --mode heuristic
python -m pytest tests/ -q
```

### Known blockers / honesty notes
- **Prototype stage** — heuristic extractor + fixture corpus for reliable offline demos; not a production lit-mining system.
- Live Semantic Scholar still needs an API key for reliable 50+ refresh; path is wired (`s2-status` → absent on this host). Unauthenticated mode keeps backoff/retry + fixture fallback.
- OpenAI key resolved from Keychain `openclaw/tgcallskill/openai-api-key` (not committed) for LLM extract / optional closed-book probe.
- Closed-book LLM memorization probe not run in default cron path (offline-first); enable with `mem-bench --closed-book`. Prefer open/small models.
- Cross-paper tension uses abstract-level stance cues (support vs limit lexicon) — proxy dialectic, not full argument mining.
- Detectors are **proxy safeguards**, not proof of non-memorization — see `docs/memorization-eval.md`.
- Pack balance is a ranking policy (reserved slots + soft boosts), not wet-lab priority truth.
- Do not claim wet-lab results; software/methods/prototype only.

## Next supervisor meeting: **30 July 2026, 14:00 SGT**
- Deliverable: `docs/EMAIL_TO_SUPERVISOR.md` + `docs/supervisor-update-draft.md`
- Demo: Pipeline run (52) + dual-domain pack + HTML report + **mem-bench v2** + **pack-aware topics** + **cross-paper tension** + feedback CLI
- Board: https://fyp.vasanth.my
- Questions: domain scope (LNP vs hybrid ncRNA weight), eval rubric labels, memorization rigor, next steps

## Last automated progress
- 2026-08-01 10:05 SGT — Wave 8: cross-paper claim tension gaps (GapKind.CROSS_PAPER_TENSION) + live S2 key path (Keychain/env, year filter, hybrid/gene queries, `s2-status`). E2E 52→88c/160e/104g/5 topics; domain pack PASS; mem-bench PASS; 46 tests. S2 key still missing on host.

## Daily loop
- **10:00 SGT** — autonomous coding progress on next unchecked item; commit/push; update this file
- **21:00 SGT** — Telegram voice call: review progress, decisions, next day focus
