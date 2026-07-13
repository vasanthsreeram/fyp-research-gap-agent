# Proposed Approaches

These are initial approaches Vas can send to the professor for discussion.

## Approach 1: Surprise Scoring On Recent Papers

Use recent biology papers that are unlikely to be in major model training sets. Extract each paper's main claim, mechanism, assumptions, and experimental evidence, then ask several models to estimate:

- How surprising the result is relative to prior literature
- Whether the mechanism is plausible
- What experiment would most directly test the claim
- What evidence would falsify it

This is the cleanest first slice because it reduces memorization leakage and gives the professor a concrete review set.

## Approach 2: Retraction And Fraud-Signal Benchmark

Build a retrospective benchmark from retracted or disputed papers, paired with strong non-retracted papers in similar domains. The goal is not to accuse papers directly, but to train the system to recognize patterns where "surprise" may actually mean weak evidence, inconsistent assumptions, or implausible claims.

This can become a negative-control benchmark for the surprise scorer.

## Approach 3: Biology-Lab Idea Generator

Focus on the professor's lab strengths: protein/nucleic-acid chemistry, molecular engineering, sequencing, microscopy, bioimaging, nucleic acid delivery, and molecular mechanisms.

For each candidate idea, generate:

- Research question
- Why it is surprising
- Why it is biologically plausible
- Source evidence
- Minimal experiment
- Feasibility and risk
- Expected impact if true

This approach makes the output directly useful for lab discussion and possible experimental follow-up.

## Suggested First Milestone

Run a tiny end-to-end pipeline on 10-20 recent biology papers:

1. Ingest metadata and abstracts.
2. Extract claims and mechanisms.
3. Score surprise, plausibility, feasibility, and impact.
4. Generate 3-5 candidate project ideas.
5. Review with the professor and refine the scoring rubric.
