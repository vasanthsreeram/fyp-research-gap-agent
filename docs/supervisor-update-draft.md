# Supervisor brief — Research Gap Agent

**To:** Asst Prof Aaron Smargon · **From:** Sreeram Vasanth (U2322909K) · **Date:** 30 Jul 2026 (14:00 SGT)

---

## Email (short)

**Subject:** Early FYP progress — Research Gap Agent (demo-ready slice)

Dear Prof Smargon,

Following our early-July discussion on an AI framework for finding theory↔experiment gaps (with care about LLM memorization), I’ve shipped a working vertical slice ahead of the formal August start and refreshed it for today’s check-in.

**Board (private):** https://fyp.vasanth.my  
**Passphrase:** `TheoryMeetsBench-LNP-26`  
**Code:** https://github.com/vasanthsreeram/fyp-research-gap-agent  

**In short:** pipeline ingests papers → extracts claims/evidence (with quote spans) → aligns gaps (lexical or MiniLM embeddings) → proposes testable topics. Domain slice: NA delivery / LNP / mRNA, with early hybrid ncRNA / gene-editing fixture papers.

**Latest offline demo run (30 papers):** **50 claims, 105 evidence, 56 gaps, 5 topics** · extractor heuristic · aligner embedding · **34 tests green**.

**Memorization safeguards (your July note):** quote-span grounding **100%** on claims and evidence; **7 post-2024 held-out** papers; cross-era leakage **0%**; overall mem-bench **PASS**. Optional closed-book LLM probe is wired but off by default for offline demos.

**Still open:** live API rate limits (fixture corpus for reliable demos; S2 backoff/retry added), human eval rubric, deeper second-domain pack, BG4801 registration when eligible.

Happy to adjust domain scope or evaluation criteria today.

Best regards,  
Sreeram Vasanth (U2322909K)

---

## Talking points (meeting)

1. **Not a search engine** — outputs are scored gaps + experiment-backed topic proposals.
2. **Grounding** — every extract keeps a quote span; bench fails if spans don’t match source text.
3. **Held-out years** — 2024–2025 fixtures used as post-cutoff slice for leakage checks.
4. **Alignment** — show embedding vs lexical if useful (`--aligner embedding|lexical`).
5. **Ask:** weight on pure LNP delivery vs hybrid/bifunctional ncRNA; preferred eval rubric for “surprising / high-impact”.
