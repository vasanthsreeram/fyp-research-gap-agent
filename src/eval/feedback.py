"""Human feedback collection for gaps / topics (eval harness).

Stores JSONL under data/processed/feedback.jsonl for offline aggregation.
CLI: `python -m src.cli feedback-add` / `feedback-summary`.
"""

from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

from src.models import FeedbackRecord, FeedbackTargetType

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_FEEDBACK_PATH = REPO_ROOT / "data" / "processed" / "feedback.jsonl"

# Suggested labels for supervisor / student scoring rubric
SUGGESTED_LABELS = (
    "surprising",
    "high_impact",
    "testable",
    "incremental",
    "unclear",
    "low_impact",
    "not_novel",
    "memorization_risk",
    "wrong_domain",
    "strong_evidence_link",
    "weak_evidence_link",
)


def feedback_path(path: Optional[Path] = None) -> Path:
    return path or DEFAULT_FEEDBACK_PATH


def load_feedback(path: Optional[Path] = None) -> list[FeedbackRecord]:
    p = feedback_path(path)
    if not p.exists():
        return []
    out: list[FeedbackRecord] = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(FeedbackRecord(**json.loads(line)))
            except Exception as e:
                logger.debug("Skip feedback line: %s", e)
    return out


def append_feedback(record: FeedbackRecord, path: Optional[Path] = None) -> Path:
    p = feedback_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(record.model_dump_json() + "\n")
    logger.info("Appended feedback %s → %s", record.id, p)
    return p


def add_rating(
    *,
    target_type: str | FeedbackTargetType,
    target_id: str,
    rating: Optional[int] = None,
    labels: Optional[list[str]] = None,
    notes: str = "",
    reviewer: str = "vas",
    run_id: Optional[str] = None,
    path: Optional[Path] = None,
) -> FeedbackRecord:
    if isinstance(target_type, str):
        target_type = FeedbackTargetType(target_type.lower().strip())
    if rating is not None and not (1 <= int(rating) <= 5):
        raise ValueError("rating must be 1–5")
    clean_labels = []
    for lb in labels or []:
        lb = str(lb).strip().lower().replace(" ", "_")
        if lb:
            clean_labels.append(lb)
    rec = FeedbackRecord(
        target_type=target_type,
        target_id=target_id,
        rating=int(rating) if rating is not None else None,
        labels=clean_labels,
        notes=notes or "",
        reviewer=reviewer,
        run_id=run_id,
    )
    append_feedback(rec, path=path)
    return rec


def summarize_feedback(records: Optional[list[FeedbackRecord]] = None, path: Optional[Path] = None) -> dict:
    """Aggregate ratings/labels for reporting."""
    recs = records if records is not None else load_feedback(path)
    by_type: dict[str, list[FeedbackRecord]] = defaultdict(list)
    for r in recs:
        by_type[r.target_type.value].append(r)

    def _block(items: list[FeedbackRecord]) -> dict:
        ratings = [r.rating for r in items if r.rating is not None]
        label_c = Counter(lb for r in items for lb in r.labels)
        return {
            "n": len(items),
            "n_rated": len(ratings),
            "mean_rating": round(sum(ratings) / len(ratings), 3) if ratings else None,
            "rating_hist": dict(Counter(ratings)),
            "top_labels": label_c.most_common(12),
        }

    summary = {
        "n_total": len(recs),
        "by_type": {k: _block(v) for k, v in sorted(by_type.items())},
        "reviewers": dict(Counter(r.reviewer for r in recs)),
        "suggested_labels": list(SUGGESTED_LABELS),
    }
    return summary


def summary_markdown(summary: Optional[dict] = None, path: Optional[Path] = None) -> str:
    s = summary if summary is not None else summarize_feedback(path=path)
    lines = [
        "# Human feedback summary",
        "",
        f"- Total records: **{s['n_total']}**",
        f"- Reviewers: {s.get('reviewers') or '{}'}",
        "",
    ]
    if not s["n_total"]:
        lines += [
            "_No feedback yet._ Use:",
            "```bash",
            "python -m src.cli feedback-add --type gap --id gap_xxx --rating 4 --labels surprising,testable",
            "```",
            "",
        ]
        return "\n".join(lines)

    lines += ["| Type | n | rated | mean | top labels |", "|------|---|-------|------|------------|"]
    for t, block in s.get("by_type", {}).items():
        labels = ", ".join(f"{k}({v})" for k, v in (block.get("top_labels") or [])[:5]) or "—"
        mean = block.get("mean_rating")
        mean_s = f"{mean:.2f}" if mean is not None else "—"
        lines.append(
            f"| {t} | {block['n']} | {block['n_rated']} | {mean_s} | {labels} |"
        )
    lines += [
        "",
        "Suggested labels: " + ", ".join(s.get("suggested_labels") or SUGGESTED_LABELS),
        "",
    ]
    return "\n".join(lines)
