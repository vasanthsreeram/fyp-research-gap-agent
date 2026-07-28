"""Paper ingestion package: Semantic Scholar + arXiv + fixture fallback."""

from __future__ import annotations

from src.ingest.pipeline import ingest_papers, load_fixture

__all__ = ["ingest_papers", "load_fixture"]
