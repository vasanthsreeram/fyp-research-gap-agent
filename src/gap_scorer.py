"""Backward-compatible shim — prefer src.gap.score + src.topics.suggest."""

from src.gap.score import find_gaps  # noqa: F401
from src.topics.suggest import suggest_topics  # noqa: F401

__all__ = ["find_gaps", "suggest_topics"]
