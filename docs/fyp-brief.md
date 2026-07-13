# FYP Brief: Research Gap Agent

## Working Idea

Build an AI-agentic framework for "researching about research": finding gaps between theory and practice, then turning those gaps into high-impact research topic candidates.

The core value is not just literature search. The system should compare what papers claim, assume, or predict against what experiments, deployments, benchmarks, or replications actually show.

After the professor meeting on 2026-07-01, the sharper framing is: identify scientifically surprising ideas that are plausible, high-impact, and experimentally testable, while separating genuine surprise from unsupported claims, model memorization, or fraud-like signals.

## Call Context

Vas said his FYP direction is decided and that a professor invited him to join this research. The project framing from the call:

- Find gaps between theoretical research and practical/experimental outcomes.
- Use an agentic framework to discover research topics worth pursuing.
- Prioritize topics that can lead to high-impact papers.
- Treat the system as a research-assistant pipeline, not a one-shot paper summarizer.
- First target domain is likely biology, especially protein/nucleic-acid chemistry, molecular engineering, and experimentally testable mechanisms.
- The professor asked Vas to write notes from the meeting and propose approaches as the next follow-up.

## First Research Questions

1. How can theoretical claims and assumptions be extracted from research papers in a structured, comparable format?
2. How can experimental evidence, benchmark results, and real-world deployment observations be extracted and normalized?
3. What signals indicate a meaningful theory-practice gap rather than ordinary noise or incomplete reporting?
4. How should the framework rank gaps by novelty, feasibility, expected impact, and evidence quality?
5. What human-in-the-loop workflow lets a supervisor or student validate candidate topics quickly?
6. How can the system measure "surprise" without rewarding implausible or fraudulent claims?
7. How can evaluation avoid leakage from LLM memorization of scientific literature?

## Initial System Shape

The first prototype should be a narrow end-to-end vertical slice:

1. Pick one research area and collect a small corpus of papers.
2. Extract theoretical claims, assumptions, predicted outcomes, and limitations.
3. Extract experimental results, benchmark evidence, failure cases, and practical constraints.
4. Align theory/practice pairs and produce gap records.
5. Cluster gaps and generate candidate research topics with rationale and suggested experiments.
6. Review candidates with the professor and refine the scoring rubric.

## Meeting-Derived Constraints

- Include a memorization-control strategy: use recent post-training-cutoff papers, smaller models, or open models with transparent training data.
- Include a retrospective benchmark, but do not rely on it alone because many models may have seen the papers already.
- Consider retracted papers as a negative/suspicious benchmark set.
- Make every generated idea traceable to source papers, assumptions, and explicit uncertainty.
- Prefer ideas that a biology lab can plausibly test, not just computationally interesting gaps.

## Early Success Criteria

- Produces traceable gap records with paper citations and evidence snippets.
- Separates weak/unsupported claims from experimentally contradicted claims.
- Generates research topic candidates that are specific enough to discuss with a professor.
- Supports human review and correction of extracted claims and scores.
- Can explain why a topic is likely high impact, not just "interesting."

## Related Notes

- [Meeting notes: 2026-07-01 professor discussion](meeting-2026-07-01-professor.md)
