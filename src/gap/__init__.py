"""Gap detection package."""

from src.gap.score import find_gaps, resolve_aligner, score_gap, tag_domains
from src.gap.tension import find_cross_paper_gaps, stance_score

__all__ = [
    "find_gaps",
    "resolve_aligner",
    "score_gap",
    "tag_domains",
    "find_cross_paper_gaps",
    "stance_score",
]
