"""Claim and evidence extraction package."""

from __future__ import annotations

from src.extract.claims import extract_claims, extract_claims_heuristic, extract_claims_llm
from src.extract.evidence import extract_evidence, extract_evidence_heuristic, extract_evidence_llm
from src.extract.dispatch import extract_all, resolve_openai_api_key

__all__ = [
    "extract_all",
    "extract_claims",
    "extract_claims_heuristic",
    "extract_claims_llm",
    "extract_evidence",
    "extract_evidence_heuristic",
    "extract_evidence_llm",
    "resolve_openai_api_key",
]
