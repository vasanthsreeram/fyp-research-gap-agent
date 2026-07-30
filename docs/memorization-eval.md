# Memorization safeguards — plan, tests, metrics

Supervisor note (2026-07-01): LLM pipelines can **memorize** literature and look strong on retrospective eval without grounded reasoning. This doc is the Stage-2+ plan for detecting memorization vs grounded extraction.

## Minimal plan

| Step | What | Status |
|------|------|--------|
| 1 | Offline quote-span grounding on every claim/evidence | Done |
| 2 | Post-cutoff held-out papers (year ≥ cutoff) in fixture | Done (21× ≥2024) |
| 3 | Cross-era leakage (post claims ≈ pre abstracts) | Done |
| 4 | Unsupported-claim detector (body + structured slots) | Done (wave 6) |
| 5 | Hallucinated citation detector (DOI / arXiv / cite-year) | Done (wave 6) |
| 6 | Overconfidence detector (absolute language + high conf + weak ground) | Done (wave 6) |
| 7 | Structured claims: hypothesis, evidence, mechanism, assumptions, uncertainty | Done (wave 6) |
| 8 | Controlled synthetic suite (CI, no API) | Done (wave 6) |
| 9 | Optional closed-book title→abstract probe (prefer small/open models) | Done (opt-in) |
| 10 | Human labels via feedback CLI (`memorization_risk`, etc.) | Done (schema) |

### Design rules

1. **Source-bound unit** — extract one paper (title+abstract) at a time; every claim has `paper_id` + `quote_span`.
2. **Offline-first** — heuristic path + detectors run without keys; LLM path is optional.
3. **Post-cutoff holdout** — treat year ≥ `cutoff_year` (default 2024) as unseen for leakage/closed-book.
4. **Small/open models** — for closed-book and LLM extract, prefer `OPENAI_MODEL=gpt-4o-mini` or a local GGUF; large models memorize more of the training web.
5. **Controlled prompts** — synthetic known-good / known-bad cases lock detector behaviour in pytest.

## How to run

```bash
cd /Users/admin/projects/fyp-research-gap-agent
source .venv/bin/activate   # if present

# Full offline mem bench (fixture, controlled cases on)
python -m src.cli mem-bench --fixture --limit 52 --cutoff-year 2024

# Skip synthetic suite / enable closed-book (needs API key)
python -m src.cli mem-bench --fixture --limit 52 --closed-book --no-controlled

# Pipeline with mem-bench embedded
python -m src.cli run --limit 52 --fixture --mode heuristic --aligner lexical --format both

# Unit + integration tests
python -m pytest tests/test_pipeline.py -q
# or focused:
python -m pytest tests/test_pipeline.py::TestMemorization -q
```

Artifacts: `reports/memorization_bench.md` + `.json`.

## Test cases

| ID | Case | Expected |
|----|------|----------|
| `ctrl_grounded_heuristic` | Heuristic extract on known abstract | All quotes grounded |
| `ctrl_structure_slots` | Same | ≥1 of hyp/mech/unc filled |
| `ctrl_unsupported_detector` | Invented “wormhole” claim | Flagged unsupported |
| `ctrl_citation_detector` | Fake DOI + Smith et al. (1999) | Flagged citation hit |
| `ctrl_overconfidence_detector` | “always completely” + conf 0.99 | Flagged overconfident |
| `ctrl_structure_fn` | `structure_claim_fields(...)` | hyp/mech populated |
| `ctrl_supported_passes` | Grounded flip-flop claim | Not flagged unsupported |
| Fixture holdout | 52 papers, 21 post-2024 | Ground ≥85%, leak ≤15%, unsup ≤10%, cite ≤5% |
| Leakage unit | Post claim copies pre abstract | `find_cross_era_leakage` hits |

## Recommended evaluation metrics

| Metric | Pass gate (default) | Notes |
|--------|---------------------|-------|
| Claim quote-grounding rate | ≥ 0.85 | Substring / high Jaccard vs source |
| Evidence quote-grounding rate | ≥ 0.85 | Same |
| Cross-era leakage rate | ≤ 0.15 | Post-cutoff claims vs pre abstracts |
| Unsupported-claim rate | ≤ 0.10 | Body + structured slots |
| Hallucinated-citation rate | ≤ 0.05 | DOI/arXiv/cite-year not in metadata/text |
| Overconfidence flag rate | ≤ 0.35 hard (≤0.20 advisory) | Absolute language + high conf |
| Structure: % with hypothesis | report | Robustness, not hard gate |
| Structure: % with ≥3 slots | report | hyp/evid/mech/assum/unc |
| Post-cutoff n papers | ≥ 10 | Holdout strength |
| Closed-book flag rate | informational | Opt-in; fail if majority flagged |
| Controlled suite | all pass | CI regression lock |

## Claim schema (structured)

```text
Claim
  text, claim_type, quote_span, confidence, tags, extractor
  hypothesis?   — proposed relation / theory statement
  evidence?     — in-paper support only (not external)
  mechanism?    — how / pathway language
  assumptions[] — stated or implied priors
  uncertainty?  — hedges, unknowns, limits
```

Heuristic fill via `structure_claim_fields`; LLM prompt requests the same JSON keys and must use verbatim `quote_span`.

## Open / small model protocol

1. Set `OPENAI_MODEL` to a small chat model (or point client at a local OpenAI-compatible server).
2. Run `mem-bench --mode llm --closed-book` on post-cutoff titles only.
3. Compare grounding / unsupported / citation rates vs heuristic baseline.
4. Prefer abstention (“UNKNOWN”) over fluent invention in closed-book system prompt (already encoded).

## What is *not* claimed

- Detectors are **proxy safeguards**, not a proof of non-memorization.
- Fixture abstracts are still in the public literature; true post-training-cutoff papers need live ingest when S2 keys allow.
- Human ratings remain the gold standard for “surprising / testable / memorized” labels (`feedback-add`).
