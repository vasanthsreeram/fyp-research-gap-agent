# Supervisor brief — Research Gap Agent

**To:** Asst Prof Aaron Smargon · **From:** Sreeram Vasanth (U2322909K) · **Date:** 29 Jul 2026

---

## Email (short)

**Subject:** Early FYP progress — Research Gap Agent

Dear Prof Smargon,

Following our early-July discussion on an AI framework for finding theory↔experiment gaps (with care about LLM memorization), I’ve shipped a first working vertical slice ahead of the formal August start.

**Board (private):** https://fyp.vasanth.my  
**Passphrase:** `TheoryMeetsBench-LNP-26`  
**Code:** https://github.com/vasanthsreeram/fyp-research-gap-agent  

**In short:** pipeline ingests papers → extracts claims/evidence (with quote spans) → scores gaps → proposes testable topics. First domain slice: NA delivery / LNP / mRNA. Latest run on 15 papers: **91 claims, 102 evidence, 47 gaps, 5 topics** (tests green; offline path also works).

**Still open:** live API rate limits (fixture corpus for now), memorization held-out bench, human eval rubric, second domain.

I’ll keep the board updated as Stage 2 lands. Happy to adjust domain scope or evaluation criteria whenever you prefer.

Best regards,  
Sreeram Vasanth (U2322909K)
