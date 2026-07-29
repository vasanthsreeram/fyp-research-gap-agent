# FYP Research Gap Agent — architecture diagrams (Mermaid)

Accurate to code in `src/` as of 2026-07-29.  
Repo: https://github.com/vasanthsreeram/fyp-research-gap-agent

---

## 1. End-to-end pipeline (Stage 1 vertical slice)

```mermaid
flowchart LR
  subgraph Sources
    S2[Semantic Scholar API]
    AX[arXiv API]
    FX[fixtures/papers_fixture.jsonl]
  end

  subgraph Ingest["src/ingest/"]
    IP[pipeline.ingest_papers]
    DD[dedupe + limit]
    IP --> DD
  end

  S2 --> IP
  AX --> IP
  FX -. fallback on 429 / empty .-> IP

  P[(data/processed/papers.jsonl<br/>Paper: title+abstract)]
  DD --> P

  subgraph Extract["src/extract/"]
    DISP[dispatch.extract_all]
    CL[claims.py]
    EV[evidence.py]
    DISP --> CL
    DISP --> EV
  end

  P --> DISP

  C[(claims.jsonl)]
  E[(evidence.jsonl)]
  CL --> C
  EV --> E

  subgraph Gap["src/gap/"]
    SC[score.py<br/>Jaccard + TF-cosine<br/>multi-axis scores]
  end

  C --> SC
  E --> SC
  G[(gaps.jsonl)]
  SC --> G

  subgraph Topics["src/topics/"]
    TS[suggest.py]
  end

  G --> TS
  T[(topics.jsonl)]
  TS --> T

  R[reports/latest_run.md]
  M[run_manifest.json]
  C --> R
  E --> R
  G --> R
  T --> R
  P --> R
```

---

## 2. How claims / “effects” are pulled (not full-PDF dump)

```mermaid
flowchart TB
  Paper["Paper object<br/>title + abstract<br/>(text_blob)"]

  Paper --> Mode{mode}

  Mode -->|heuristic| H["Sentence split<br/>regex triggers:<br/>theory / mechanism / domain"]
  Mode -->|llm| L["OpenAI chat.completions<br/>model = OPENAI_MODEL or gpt-4o-mini<br/>response_format = json_object"]
  Mode -->|auto| A{API key?}
  A -->|yes| L
  A -->|no| H

  H --> ClaimH["Claim<br/>paper_id, claim_type, text,<br/>quote_span, confidence, tags<br/>extractor=heuristic"]

  L --> Prompt["System: extract theory/mechanism claims<br/>User: Title + Abstract≤4000"]
  Prompt --> JSON['{"claims":[{text, claim_type, confidence, tags}]}']
  JSON --> ClaimL["Claim<br/>same schema<br/>extractor=llm"]
  L -. fail .-> H

  Paper --> ModeE{evidence mode}
  ModeE -->|heuristic / llm| Ev["Evidence<br/>result / metric / limitation<br/>+ quote_span"]

  ClaimH --> Align
  ClaimL --> Align
  Ev --> Align

  Align["gap/score.py<br/>align claim ↔ evidence<br/>lexical similarity"]
  Align --> Gap["Gap scored on<br/>magnitude · novelty · testability · impact"]
  Gap --> Topics["topics/suggest.py<br/>3–5 TopicProposal<br/>hypothesis + experiments"]
```

**LLM call shape (exact):** one paper at a time — **not** the whole corpus JSON.

```
POST chat.completions
  model: gpt-4o-mini (default) or $OPENAI_MODEL
  messages: [system extraction instructions, user: Title + Abstract]
  response_format: { type: "json_object" }
→ parse claims[] / evidence[] → Pydantic → jsonl
```

Key: every extract keeps `paper_id` + `quote_span` (citation grounding / anti-hallucination hook).

---

## 3. Data model (Pydantic)

```mermaid
erDiagram
  PAPER ||--o{ CLAIM : has
  PAPER ||--o{ EVIDENCE : has
  CLAIM ||--o{ GAP : aligned_to
  EVIDENCE ||--o{ GAP : supports
  GAP ||--o{ TOPIC : clusters_into

  PAPER {
    string id
    string title
    string abstract
    string source
    string doi
  }
  CLAIM {
    string id
    string paper_id
    enum claim_type
    string text
    string quote_span
    float confidence
    string extractor
  }
  EVIDENCE {
    string id
    string paper_id
    enum evidence_type
    string text
    string quote_span
  }
  GAP {
    string id
    enum kind
    float novelty
    float testability
    float impact
  }
  TOPIC {
    string id
    string hypothesis
    list experiments
  }
```

---

## 4. Stage 1 vs Stage 2

```mermaid
flowchart TB
  subgraph S1["Stage 1 — vertical slice ✅"]
    s1a[Schemas Paper/Claim/Evidence/Gap/Topic]
    s1b[Ingest S2+arXiv+fixture]
    s1c[Heuristic + LLM extractors]
    s1d[Lexical gap scorer]
    s1e[Topic suggester]
    s1f[CLI + markdown report + 23 tests]
    s1a --> s1b --> s1c --> s1d --> s1e --> s1f
  end

  subgraph S2["Stage 2 — packaging + quality"]
    s2a[✅ Modular packages src/ingest|extract|gap|topics]
    s2b[✅ Claim recall lift + LLM E2E]
    s2c[⬜ Embedding gap alignment]
    s2d[⬜ Memorization / post-cutoff held-out]
    s2e[⬜ Corpus 50+ live]
    s2f[⬜ HTML report + 2nd domain]
  end

  S1 --> S2
```

---

## 5. Runtime sequence (one `cli run`)

```mermaid
sequenceDiagram
  participant U as You / CLI
  participant C as src/cli.py
  participant I as ingest
  participant X as extract
  participant LLM as OpenAI gpt-4o-mini
  participant G as gap/score
  participant T as topics
  participant FS as data/ + reports/

  U->>C: run --limit 15 --mode llm
  C->>I: ingest_papers(fixture|live)
  alt live APIs OK
    I-->>C: Paper[] from S2/arXiv
  else 429 / empty
    I-->>C: Paper[] from fixture
  end
  C->>FS: papers.jsonl
  loop each Paper
    C->>X: extract_claims + extract_evidence
    X->>LLM: title+abstract → JSON
    LLM-->>X: claims[] / evidence[]
  end
  C->>FS: claims.jsonl, evidence.jsonl
  C->>G: align + multi-axis score
  G-->>C: Gap[]
  C->>FS: gaps.jsonl
  C->>T: suggest topics
  T-->>C: TopicProposal[]
  C->>FS: topics.jsonl + latest_run.md
```

---

## 6. Latest numbers (LLM, limit 15)

| Metric | Count |
|--------|------:|
| Papers | 15 |
| Claims | 91 |
| Evidence | 102 |
| Gaps | 47 |
| Topics | 5 |
| pytest | 23/23 |

Demo:

```bash
cd ~/projects/fyp-research-gap-agent
python -m src.cli run --limit 15 --fixture --mode llm
```

Supervisor draft: `docs/supervisor-update-draft.md`  
Machine YAML: `docs/architecture.yaml`
