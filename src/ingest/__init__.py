"""Paper ingestion package: Semantic Scholar + arXiv + fixture fallback."""

from __future__ import annotations

from src.ingest.pipeline import ingest_papers, load_fixture
from src.ingest.keys import resolve_s2_api_key, s2_key_status

__all__ = ["ingest_papers", "load_fixture", "resolve_s2_api_key", "s2_key_status"]
