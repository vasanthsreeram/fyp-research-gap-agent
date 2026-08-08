"""Paper ingestion package: Semantic Scholar + OpenAlex + Europe PMC + arXiv + Unpaywall + fixture + full-text PDF."""

from __future__ import annotations

from src.ingest.pipeline import ingest_papers, load_fixture
from src.ingest.keys import resolve_s2_api_key, s2_key_status
from src.ingest.pdf_text import (
    attach_fulltext_to_papers,
    extract_text_from_pdf,
    fulltext_markdown_report,
    split_sections,
)

__all__ = [
    "ingest_papers",
    "load_fixture",
    "resolve_s2_api_key",
    "s2_key_status",
    "attach_fulltext_to_papers",
    "extract_text_from_pdf",
    "split_sections",
    "fulltext_markdown_report",
]
