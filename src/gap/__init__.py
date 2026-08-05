"""Gap detection package."""

from src.gap.score import find_gaps, resolve_aligner, score_gap, tag_domains
from src.gap.tension import find_cross_paper_gaps, stance_score
from src.gap.novelty import apply_corpus_novelty, novelty_report_markdown
from src.gap.argue import (
    build_argument_graph,
    find_argument_relations,
    graph_to_gaps,
    mine_argument_units,
)

__all__ = [
    "find_gaps",
    "resolve_aligner",
    "score_gap",
    "tag_domains",
    "find_cross_paper_gaps",
    "stance_score",
    "apply_corpus_novelty",
    "novelty_report_markdown",
    "build_argument_graph",
    "find_argument_relations",
    "graph_to_gaps",
    "mine_argument_units",
]
