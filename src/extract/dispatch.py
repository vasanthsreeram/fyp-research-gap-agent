"""Unified extraction dispatch."""

from __future__ import annotations

import logging

from src.models import Claim, Evidence, Paper
from src.extract.claims import extract_claims
from src.extract.evidence import extract_evidence
from src.extract.llm_util import llm_available, resolve_openai_api_key

logger = logging.getLogger(__name__)

__all__ = ["extract_all", "resolve_openai_api_key", "llm_available"]


def extract_all(
    papers: list[Paper],
    mode: str = "auto",
) -> tuple[list[Claim], list[Evidence]]:
    """Run claim + evidence extraction. mode = heuristic | llm | auto."""
    if mode == "auto":
        mode = "llm" if llm_available() else "heuristic"
    logger.info("Extraction mode: %s", mode)

    all_claims: list[Claim] = []
    all_evidence: list[Evidence] = []

    for paper in papers:
        try:
            all_claims.extend(extract_claims(paper, mode=mode))
            all_evidence.extend(extract_evidence(paper, mode=mode))
        except Exception as e:
            logger.warning("Extraction failed for %r: %s", (paper.title or "")[:50], e)

    logger.info(
        "Extracted %d claims, %d evidence items from %d papers",
        len(all_claims),
        len(all_evidence),
        len(papers),
    )
    return all_claims, all_evidence
