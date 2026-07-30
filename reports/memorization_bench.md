# Memorization / Grounding Benchmark

| Field | Value |
|-------|-------|
| **Cutoff year** | 2024 |
| **Papers** | 52 (pre=31, post=21) |
| **Claim grounding** | 88/88 (100%) |
| **Evidence grounding** | 160/160 (100%) |
| **Cross-era leakage** | 0 (rate=0%) |
| **Unsupported claims** | 0 (rate=0%) |
| **Hallucinated citations** | 0 (rate=0%) |
| **Overconfidence flags** | 0 (rate=0%) |
| **Structure coverage** | hyp=62% any=100% full(≥3)=18/88 |
| **Closed-book flagged** | 0/0 |
| **Controlled cases** | PASS (7/7) |
| **Pass grounding** | yes |
| **Pass leakage** | yes |
| **Pass unsupported** | yes |
| **Pass citations** | yes |
| **Pass overconfidence** | yes |
| **Overall** | PASS |

## Notes

- Prefer open/small models (e.g. gpt-4o-mini, local GGUF) for closed-book probes; set OPENAI_MODEL. Offline path stays model-free.

## Recommended evaluation metrics

- Claim quote-grounding rate (≥85% pass)
- Evidence quote-grounding rate (≥85% pass)
- Cross-era leakage rate on post-cutoff claims (≤15% pass)
- Unsupported-claim rate (≤10% pass)
- Hallucinated-citation rate (≤5% pass)
- Overconfidence flag rate (≤20% advisory; ≤35% hard fail)
- Structure coverage: % claims with hypothesis; % with ≥3 slots
- Post-cutoff slice size (n papers year≥cutoff; target ≥10)
- Closed-book title→abstract overlap flag rate (optional; open/small models preferred)
- Controlled synthetic suite pass (all cases)

## Controlled prompt / synthetic cases

- [ok] `ctrl_grounded_heuristic` heuristic claims grounded in source: n_claims=2
- [ok] `ctrl_structure_slots` structured hypothesis/mechanism/uncertainty present: hyp=1 mech=2 unc=1
- [ok] `ctrl_unsupported_detector` flags invented unsupported claim: hits=1
- [ok] `ctrl_citation_detector` flags hallucinated DOI/cite: hits=3 kinds=['doi', 'year', 'cite']
- [ok] `ctrl_overconfidence_detector` flags absolute + high-confidence claim: hits=1
- [ok] `ctrl_structure_fn` structure_claim_fields fills hypothesis/mechanism: {'hypothesis': 'We propose that ionizable lipids promote', 'evidence': None, 'mechanism': 'We propose that ionizable lipids promote', 'assumptions': [], 'uncertainty': None}
- [ok] `ctrl_supported_passes` grounded claim not flagged unsupported: hits=0

*Generated 2026-07-30T13:09:39.263988Z*