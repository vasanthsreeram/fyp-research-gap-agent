# FYP Brief: Research Gap Agent

## Working Idea

Build an AI-agentic framework for "researching about research": finding gaps between theory and practice, then turning those gaps into high-impact research topic candidates.

The core value is not just literature search. The system should compare what papers claim, assume, or predict against what experiments, deployments, benchmarks, or replications actually show.

## Call Context

Vas said his FYP direction is decided and that a professor invited him to join this research. The project framing from the call:

- Find gaps between theoretical research and practical/experimental outcomes.
- Use an agentic framework to discover research topics worth pursuing.
- Prioritize topics that can lead to high-impact papers.
- Treat the system as a research-assistant pipeline, not a one-shot paper summarizer.

## First Research Questions

1. How can theoretical claims and assumptions be extracted from research papers in a structured, comparable format?
2. How can experimental evidence, benchmark results, and real-world deployment observations be extracted and normalized?
3. What signals indicate a meaningful theory-practice gap rather than ordinary noise or incomplete reporting?
4. How should the framework rank gaps by novelty, feasibility, expected impact, and evidence quality?
5. What human-in-the-loop workflow lets a supervisor or student validate candidate topics quickly?

## Initial System Shape

The first prototype should be a narrow end-to-end vertical slice:

1. Pick one research area and collect a small corpus of papers.
2. Extract theoretical claims, assumptions, predicted outcomes, and limitations.
3. Extract experimental results, benchmark evidence, failure cases, and practical constraints.
4. Align theory/practice pairs and produce gap records.
5. Cluster gaps and generate candidate research topics with rationale and suggested experiments.
6. Review candidates with the professor and refine the scoring rubric.

## Early Success Criteria

- Produces traceable gap records with paper citations and evidence snippets.
- Separates weak/unsupported claims from experimentally contradicted claims.
- Generates research topic candidates that are specific enough to discuss with a professor.
- Supports human review and correction of extracted claims and scores.
- Can explain why a topic is likely high impact, not just "interesting."
