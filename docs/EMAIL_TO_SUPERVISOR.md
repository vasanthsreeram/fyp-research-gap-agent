# Ready-to-send email — FYP supervisor

**Send by:** 2026-07-30 14:00 SGT  
**To:** Asst Prof Aaron Andrew Smargon \<aaron.smargon@ntu.edu.sg\>  
**From:** Sreeram Vasanth (U2322909K)  
**Tone:** short, formal, first-person

---

**Subject:** Early FYP progress — Research Gap Agent (demo-ready prototype slice)

Dear Prof Smargon,

Following our early-July discussion on building an agentic framework to surface theory–experiment gaps and high-impact nucleic-acid / gene-editing research directions (related to CBE/26/143 and your lab’s modelling and gene-editing efficiency work), I wanted to share early progress ahead of the formal August start, and before our check-in today.

I have built a working vertical-slice **prototype** (software/methods only — not wet-lab results):

**Private board:** https://fyp.vasanth.my  
**Passphrase:** `TheoryMeetsBench-LNP-26`  
**Code:** https://github.com/vasanthsreeram/fyp-research-gap-agent  

**What it does:** ingest papers → extract claims and evidence with quote spans → align theory↔experiment gaps (lexical or MiniLM embeddings + Chroma) → propose a small set of testable topic ideas. Domain focus so far is nucleic-acid delivery / LNP / mRNA, with a second evaluation pack on hybrid/bifunctional ncRNA and gene-editing delivery.

**Latest offline demo run (re-verified this morning, 52-paper fixture corpus):** 88 claims, 160 evidence items, 89 scored gaps, 5 topic proposals; heuristic extractor + embedding aligner; 37 automated tests passing.

**Dual-domain pack gates (PASS):** LNP-core 33 papers / 75 gaps; hybrid ncRNA 23 / 34; gene editing 10 / 19 (16 of the 23 hybrid papers are post-2024).

**Memorization safeguards (per your July guidance):** quote-span grounding 100% on claims and evidence; 21 post-2024 held-out papers; cross-era leakage 0% on the current bench (overall PASS). An optional closed-book LLM probe is wired but left off for offline demos.

**Human feedback harness:** CLI to rate gaps/topics (1–5 plus labels such as surprising, testable, high_impact) into a JSONL store with a summary report — ready if we want a shared evaluation rubric.

**Open items / honest limits:** live Semantic Scholar refresh is still rate-limit sensitive without an API key (fixture path is what I use for reliable demos); topic ranking is not yet fully pack-aware for hybrid gaps; BG4801 registration when eligible. This remains an early prototype, not a finished system.

I would value your guidance today on (1) relative weight of pure LNP delivery vs hybrid/bifunctional ncRNA, (2) which evaluation labels matter most for “scientifically surprising,” and (3) how rigorous you want the memorization checks before we expand further.

Best regards,  
Sreeram Vasanth  
U2322909K  
