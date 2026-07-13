# Initial Component Plan

## 1. Ingestion Pipeline
- Sources: arXiv, Semantic Scholar, ACL Anthology, NeurIPS/ICML proceedings, GitHub (for code/experiments)
- Output: Normalized paper objects with sections, figures, tables, citations
- Tools: arxiv Python lib + Semantic Scholar API + PDF parsers

## 2. Theory vs Experiment Comparison
- Theory extractor: LLM prompts for claims, assumptions, predicted metrics
- Experiment extractor: Result tables, reported metrics, setup parameters, failure modes
- Alignment: Embedding similarity + structured JSON matching + LLM judge

## 3. Gap Scoring
- Dimensions: Performance gap, Assumption violation, Scalability gap, Reproducibility issues, Domain shift
- Score: Weighted composite (0-1) + confidence
- Storage: Vector DB + relational metadata

## 4. Topic Suggestion Agent
- Input: High-scoring gaps + related literature
- Output: Research question, hypothesis, proposed experiments, expected impact, feasibility notes
- Style: Structured JSON + natural language rationale

## 5. Orchestration
- Agent framework: LangGraph state machine with nodes for each stage
- Memory: Short-term (conversation) + long-term (vector store of past gaps)
- Human loop: Review UI or Telegram/CLI approval gates

## 6. Memorization Controls
- Use recent papers that are unlikely to be in the model training data.
- Test smaller models against larger models to separate reasoning from memorized knowledge.
- Include a paper-continuation or withheld-section test where practical.
- Keep provenance for every claim, score, and generated research idea.

## 7. Biology First Slice
- Start with one narrow biology subfield aligned to the professor's lab.
- Candidate areas: protein/nucleic-acid chemistry, hybrid non-coding RNA mechanisms, molecular engineering, nucleic acid delivery, aging-related molecular mechanisms.
- Output should be suitable for professor review: research question, why surprising, why plausible, evidence base, risks, and suggested experiment.

Next milestone: write a short project memo from the professor meeting, then run a tiny end-to-end experiment on 10-20 recent biology papers.
