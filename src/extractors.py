"""Backward-compatible shim — prefer src.extract package."""

from src.extract.claims import extract_claims_heuristic, extract_claims_llm  # noqa: F401
from src.extract.evidence import extract_evidence_heuristic, extract_evidence_llm  # noqa: F401
from src.extract.dispatch import extract_all  # noqa: F401

__all__ = [
    "extract_all",
    "extract_claims_heuristic",
    "extract_claims_llm",
    "extract_evidence_heuristic",
    "extract_evidence_llm",
]
