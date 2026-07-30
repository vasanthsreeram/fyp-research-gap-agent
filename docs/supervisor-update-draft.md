# Supervisor brief — Research Gap Agent

**To:** Asst Prof Aaron Smargon · **From:** Sreeram Vasanth (U2322909K) · **Date:** 30 Jul 2026 (14:00 SGT)

---

## Email (short)

See ready-to-send file: [`docs/EMAIL_TO_SUPERVISOR.md`](EMAIL_TO_SUPERVISOR.md)

**Subject:** Early FYP progress — Research Gap Agent (demo-ready prototype slice)

Dear Prof Smargon,

Following our early-July discussion on an AI framework for finding theory↔experiment gaps (with care about LLM memorization), and related to CBE/26/143 / gene-editing modelling directions, I’ve shipped a working vertical-slice **prototype** ahead of the formal August start and re-verified it this morning for today’s check-in.

**Board (private):** https://fyp.vasanth.my  
**Passphrase:** `TheoryMeetsBench-LNP-26`  
**Code:** https://github.com/vasanthsreeram/fyp-research-gap-agent  

**In short:** pipeline ingests papers → extracts claims/evidence (with quote spans) → aligns gaps (lexical or MiniLM embeddings) → proposes testable topics. Domain slice: NA delivery / LNP / mRNA **plus** a second-domain pack on hybrid/bifunctional ncRNA and gene-editing delivery.

**Latest offline demo run (52 papers, re-run 30 Jul ~11:00 SGT):** **88 claims, 160 evidence, 89 gaps, 5 topics** · extractor heuristic · aligner embedding · **37 tests green**.

**Dual-domain pack (PASS):** LNP-core 33 papers / 75 gaps · hybrid ncRNA 23 / 34 · gene editing 10 / 19 (16 of 23 hybrid papers are post-2024).

**Memorization safeguards (your July note):** quote-span grounding **100%** on claims and evidence; **21 post-2024 held-out** papers; cross-era leakage **0%**; overall mem-bench **PASS**. Optional closed-book LLM probe is wired but off by default for offline demos.

**Human eval harness:** CLI to rate gaps/topics (1–5 + labels like `surprising`, `testable`, `high_impact`) → JSONL + summary report — ready for a shared rubric today.

**Honest scope:** this is a software/methods prototype (fixture corpus + heuristic extract for reliable demos). Live API refresh still rate-limit sensitive without an S2 key; pack-aware topic ranking and BG4801 registration remain open.

Happy to adjust domain scope or evaluation criteria today.

Best regards,  
Sreeram Vasanth (U2322909K)

---

## Talking points (meeting)

1. **Not a search engine** — outputs are scored gaps + experiment-backed topic proposals.
2. **Grounding** — every extract keeps a quote span; bench fails if spans don’t match source text.
3. **Held-out years** — 21 papers from 2024–2025 used as post-cutoff slice for leakage checks.
4. **Two domain packs** — show `reports/domain_pack.md`: core LNP vs hybrid ncRNA yield.
5. **Feedback labels** — propose rubric: surprising / high_impact / testable / incremental / memorization_risk.
6. **Ask:** weight on pure LNP delivery vs hybrid/bifunctional ncRNA; which labels matter for “surprising”.
7. **Don’t overclaim** — prototype, not wet-lab; fixture path for demos; LLM path optional.

## Verified counts (2026-07-30 11:01 SGT)

| Item | Value |
|------|-------|
| Run ID | `run_d4b35242b895` |
| Papers / claims / evidence / gaps / topics | 52 / 88 / 160 / 89 / 5 |
| pytest | 37 passed |
| Mem-bench | PASS (100%/100% ground, 0% leak, n_post=21) |
| Domain pack | PASS (lnp 33/75, hybrid 23/34, editing 10/19) |
| Commits (recent Stage 2) | `01091ab` corpus52+pack+feedback · `eb176fe` mem-bench+HTML · `de71001` embeddings · `2c202b7`/`b736c41` site board |
