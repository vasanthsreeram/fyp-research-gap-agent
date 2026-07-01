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

Next milestone: End-to-end run on 50 papers in one subfield (e.g., your Digital Twin or facility intelligence work).