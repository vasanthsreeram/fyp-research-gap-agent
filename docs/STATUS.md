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

## Current stage: **Stage 3** (2026-08-06 10:00 SGT)

Wave 12 — **Full-text PDF depth** (sectioned body text → extract/argue; offline fixture + PDF extract path).

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
- [x] **S2 OpenAlex free live ingest** — no-key Works API, year filter, abstract rebuild, `openalex-status` *(verified 20× ≥2024)*
- [x] **S2 Experiment protocol cards** — controls, assay panel, success/stop rules, timeline (`ExperimentProtocol`; `protocols` CLI)
- [x] **S3 Novelty-vs-corpus scoring** — `src/gap/novelty.py`; nearest papers; redundancy penalty; `novelty` CLI; report `novelty_corpus.md`
- [x] **S3 Cite-grounded argument mining** — `src/gap/argue.py`; quote-grounded units w/ roles + citation cues; cross-paper support/attack relations; `ARGUE_MINED_CONFLICT` gaps; `argue` CLI; report `argument_graph.md`
- [x] **S3 Full-text PDF depth** — `src/ingest/pdf_text.py`; Paper.full_text/sections; fixture bodies (9 papers); PyMuPDF extract; IMRaD split; `fulltext` CLI; run `--fulltext` (default on)
- [ ] Register BG4801 when eligible
- [ ] Optional: store S2 API key for dual-source live refresh (OpenAlex already unblocks live path)
- [ ] Closed-book LLM mem probe on held-out titles (optional; run with small/open model)
- [ ] Optional: bulk OA PDF download + more fixture full-texts beyond seed 9

### What shipped (2026-08-06 10:00 SGT — wave 12 full-text PDF depth)

| Metric | Value |
|--------|-------|
| Papers | **52** (fixture; **21** year≥2024 held-out) |
| Full-text attached | **9** (offline fixture bodies w/ IMRaD sections) |
| Claims (heuristic) | **123** (was 88 abstract-only) |
| Evidence | **197** (was 160) |
| Gaps | **128** (incl. **1** cross-paper tension + **9** argue-mined conflict) |
| Argument units | **412** (was 329) |
| Argument relations | **40** (**13** attack, **27** support) |
| Topics (balanced) | **5** — packs: hybrid + gene_editing + lnp_core |
| Protocols | **5** |
| Corpus novelty mean | **0.78** (lexical; own papers excluded) |
| Domain pack | **PASS** |
| pytest | **63 passed** (was 58) |
| Mem-bench | **PASS** — ground 100%/100%, unsup/cite/over/leak 0% |

**New / updated (wave 12)**
```
src/ingest/pdf_text.py           # PDF extract (PyMuPDF→pdfplumber), IMRaD split, fixture attach, download hook
src/fixtures/fulltext_fixture.jsonl  # 9 sectioned bodies (LNP core + hybrid/gene seed)
src/models.py                    # PaperSection(+Kind); Paper.full_text/sections/pdf_*; text_blob prefers body
src/extract/claims.py + evidence.py  # higher caps + LLM prompt use full text when present
src/gap/argue.py                 # section-priority mining; raised unit budget on full-text papers
src/cli.py                       # run --fulltext/--fulltext-download; `fulltext` command
src/report.py                    # full-text count in md/html
tests/test_pipeline.py           # +5 TestFullTextDepth (incl. mini-PDF roundtrip)
reports/fulltext_coverage.md
```

**Demo commands**
```bash
python -m src.cli run --limit 52 --fixture --mode heuristic --aligner lexical --format both
python -m src.cli fulltext --limit 52 --fixture
python -m src.cli argue --limit 52 --fixture --top 12
python -m src.cli novelty --limit 52 --fixture --backend lexical
python -m src.cli protocols --limit 52 --fixture
python -m src.cli domain-pack --limit 52 --fixture
python -m src.cli mem-bench --fixture --limit 52 --cutoff-year 2024
python -m pytest tests/ -q
```

### Known blockers / honesty notes
- **Prototype stage** — heuristic extractor + fixture corpus for reliable offline demos; not a production lit-mining system.
- Live Semantic Scholar still prefers an API key for reliable bulk refresh; **OpenAlex now provides a free no-key live path** (verified). Unauthenticated S2 remains rate-limit sensitive.
- OpenAI key resolved from Keychain `openclaw/tgcallskill/openai-api-key` (not committed) for LLM extract / optional closed-book probe.
- Closed-book LLM memorization probe not run in default cron path (offline-first); enable with `mem-bench --closed-book`. Prefer open/small models.
- Cross-paper tension uses abstract-level stance cues (support vs limit lexicon) — proxy dialectic, not full argument mining.
- **Argument mining is surface mining** (sentence roles + citation cues + token-similarity relations); roles/relations are heuristic labels, not RST. Units are literal quotes, so grounding/mem-safety holds.
- **Full-text depth is seed coverage (9/52)** via synthetic sectioned bodies aligned to fixture titles + real PDF extract path (PyMuPDF). Not bulk publisher OA harvest; live `--fulltext-download` is opt-in (arXiv). Fixture bodies are demo-grade reconstructions for offline pipeline depth — not substitutes for licensed full PDFs in a real lit review.
- Protocol cards are **design sketches** (controls/assays/stop rules), not wet-lab SOPs or safety approvals.
- Corpus novelty is **text-distance to other abstracts/bodies** (own sources excluded) — proxy for “surprising vs this corpus”, not global literature novelty or expert judgment.
- Detectors are **proxy safeguards**, not proof of non-memorization — see `docs/memorization-eval.md`.
- Pack balance is a ranking policy (reserved slots + soft boosts), not wet-lab priority truth.
- Do not claim wet-lab results; software/methods/prototype only.

## Next supervisor meeting: **30 July 2026, 14:00 SGT**
- Deliverable: `docs/EMAIL_TO_SUPERVISOR.md` + `docs/supervisor-update-draft.md`
- Demo: Pipeline run (52) + dual-domain pack + HTML report + **mem-bench v2** + **pack-aware topics** + **cross-paper tension** + **protocol cards** + **OpenAlex live** + **novelty-vs-corpus** + **argue mining** + **full-text depth (9 bodies)** + feedback CLI
- Board: https://fyp.vasanth.my
- Questions: domain scope (LNP vs hybrid ncRNA weight), eval rubric labels, memorization rigor, next steps

## Last automated progress
- 2026-08-06 10:00 SGT — Wave 12: Full-text PDF depth (`src/ingest/pdf_text.py`). Paper.full_text + IMRaD sections; 9 fixture bodies attached offline; PyMuPDF extract + optional arXiv download. E2E 52→**123c/197e/128g**, units **412**, full-text **9/52**; mem-bench PASS; domain pack PASS; **63 tests**.
- 2026-08-05 10:00 SGT — Wave 11: Cite-grounded argument mining (`src/gap/argue.py`). 329 quote-grounded units w/ roles + citation cues, 40 cross-paper relations (11 attack / 29 support), 8 ARGUE_MINED_CONFLICT gaps. `argue` CLI + report; **58 tests**.
- 2026-08-03 10:03 SGT — Wave 10: Novelty-vs-corpus scoring (`src/gap/novelty.py`). Gaps rescored with corpus_novelty + redundancy penalty. E2E mean_cn=0.79; **52 tests**.

## Daily loop
- **10:00 SGT** — autonomous coding progress on next unchecked item; commit/push; update this file
- **21:00 SGT** — Telegram voice call: review progress, decisions, next day focus
