"""Gap detection package."""

from src.gap.score import find_gaps, resolve_aligner, score_gap, tag_domains
from src.gap.tension import find_cross_paper_gaps, stance_score
from src.gap.novelty import apply_corpus_novelty, novelty_report_markdown

__all__ = [
    "find_gaps",
    "resolve_aligner",
    "score_gap",
    "tag_domains",
    "find_cross_paper_gaps",
    "stance_score",
    "apply_corpus_novelty",
    "novelty_report_markdown",
]
