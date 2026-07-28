"""CLI entry point for the Research Gap Agent.

Usage:
  python -m src.cli run --limit 15
  python -m src run --limit 15
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import typer

from src.models import Paper, RunManifest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cli")

app = typer.Typer(
    name="fyp-rga",
    help="FYP Research Gap Agent: find theory↔experiment gaps in biology literature.",
    no_args_is_help=True,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
PROC_DIR = DATA_DIR / "processed"
REPORTS_DIR = REPO_ROOT / "reports"
SGT = ZoneInfo("Asia/Singapore")


def _now_sgt() -> datetime:
    return datetime.now(tz=SGT)


def _load_papers(path: Optional[Path] = None) -> list[Paper]:
    candidates: list[Path] = []
    if path:
        candidates.append(path)
    candidates.append(PROC_DIR / "papers.jsonl")

    for p in candidates:
        if not p or not p.exists():
            continue
        papers: list[Paper] = []
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    papers.append(Paper(**json.loads(line)))
                except Exception as e:
                    logger.warning("Skipping paper line: %s", e)
        if papers:
            logger.info("Loaded %d papers from %s", len(papers), p)
            return papers
    return []


def _build_markdown_report(
    manifest: RunManifest,
    papers: list[Paper],
    claims: list,
    evidence: list,
    gaps: list,
    topics: list,
) -> str:
    lines: list[str] = []
    started = manifest.started_at
    if started.tzinfo is None:
        started_s = started.strftime("%Y-%m-%d %H:%M") + " UTC"
    else:
        started_s = started.astimezone(SGT).strftime("%Y-%m-%d %H:%M %Z")

    lines += [
        "# Research Gap Agent — Run Report",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **Run ID** | `{manifest.run_id}` |",
        f"| **Domain** | {manifest.domain} |",
        f"| **Date** | {started_s} |",
        f"| **Papers** | {len(papers)} |",
        f"| **Claims** | {len(claims)} |",
        f"| **Evidence** | {len(evidence)} |",
        f"| **Gaps** | {len(gaps)} |",
        f"| **Topics** | {len(topics)} |",
        f"| **Extractor** | {manifest.extractor_mode} |",
        "",
        f"## Papers ({len(papers)})",
        "",
    ]
    for i, p in enumerate(papers, 1):
        lines.append(f"{i}. **{p.title}**")
        if p.authors:
            auth = ", ".join(p.authors[:5]) + (" et al." if len(p.authors) > 5 else "")
            lines.append(f"   - Authors: {auth}")
        if p.year:
            lines.append(f"   - Year: {p.year}")
        if p.source:
            lines.append(f"   - Source: `{p.source}`")
        if p.doi:
            lines.append(f"   - DOI: [{p.doi}](https://doi.org/{p.doi})")
        if p.arxiv_id:
            lines.append(f"   - arXiv: [{p.arxiv_id}](https://arxiv.org/abs/{p.arxiv_id})")
        lines.append("")

    lines += [f"## Top Gaps ({len(gaps)})", ""]
    for i, g in enumerate(gaps[:12], 1):
        lines += [
            f"### {i}. {g.title}",
            f"- **Kind**: `{g.kind.value}`",
            (
                f"- **Score**: overall={g.overall:.2f} magnitude={g.magnitude:.2f} "
                f"novelty={g.novelty:.2f} testability={g.testability:.2f} impact={g.impact:.2f}"
            ),
            f"- **Domains**: {', '.join(g.domain_tags) if g.domain_tags else '—'}",
            f"- **Description**: {g.description[:350]}",
            f"- **Rationale**: {g.rationale}",
            "",
        ]

    lines += [f"## Research Topic Proposals ({len(topics)})", ""]
    for i, t in enumerate(topics, 1):
        lines += [
            f"### {i}. {t.title}",
            f"- **Priority**: {t.priority:.2f}",
            f"- **Domains**: {', '.join(t.domain_tags) if t.domain_tags else '—'}",
            f"- **Hypothesis**: {t.hypothesis}",
            "- **Experiments**:",
        ]
        for j, exp in enumerate(t.proposed_experiments, 1):
            lines.append(f"  {j}. {exp}")
        lines += [
            f"- **Expected Readout**: {t.expected_readout}",
            f"- **Feasibility**: {t.feasibility_notes}",
            f"- **Impact Rationale**: {t.impact_rationale}",
            "",
        ]

    lines += [
        "---",
        f"*Report generated at {_now_sgt().strftime('%Y-%m-%d %H:%M %Z')}*",
    ]
    return "\n".join(lines)


@app.command()
def run(
    papers_path: Optional[Path] = typer.Option(None, "--papers", "-p", help="Path to papers.jsonl"),
    domain: str = typer.Option("nucleic_acid_delivery", "--domain", "-d", help="Research domain"),
    mode: str = typer.Option("auto", "--mode", "-m", help="Extraction mode: heuristic | llm | auto"),
    use_fixture: bool = typer.Option(False, "--fixture", "-f", help="Force fixture (offline) mode"),
    limit: int = typer.Option(15, "--limit", "-n", help="Max papers to process"),
    refetch: bool = typer.Option(False, "--refetch", help="Force re-ingest even if cache exists"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output report path"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save intermediate JSONL artifacts"),
):
    """End-to-end pipeline: ingest → extract → gap-score → suggest → report."""
    # Eager keychain resolve for auto/llm mode
    if mode in ("auto", "llm"):
        try:
            from src.extract.llm_util import resolve_openai_api_key

            resolve_openai_api_key()
        except Exception:
            pass

    started_sgt = _now_sgt()
    manifest = RunManifest(
        domain=domain,
        extractor_mode=mode,
        # Store naive SGT wall-clock for readable reports (labeled in markdown).
        started_at=started_sgt.replace(tzinfo=None),
    )
    logger.info("=== FYP Research Gap Agent — run %s ===", manifest.run_id)
    logger.info("Domain=%s mode=%s fixture=%s limit=%d", domain, mode, use_fixture, limit)

    # 1. Papers
    loaded_papers: list[Paper] = []
    if papers_path:
        loaded_papers = _load_papers(papers_path)
    elif not refetch and not use_fixture:
        loaded_papers = _load_papers()

    if not loaded_papers or refetch or use_fixture:
        from src.ingest import ingest_papers

        logger.info("Running ingestion (fixture=%s limit=%d)...", use_fixture, limit)
        loaded_papers = ingest_papers(use_fixture=use_fixture, save=save, limit=limit)
    else:
        loaded_papers = loaded_papers[: max(1, limit)]

    manifest.n_papers = len(loaded_papers)
    logger.info("Papers: %d", len(loaded_papers))
    if not loaded_papers:
        logger.error("No papers available. Aborting.")
        raise typer.Exit(1)

    if save:
        PROC_DIR.mkdir(parents=True, exist_ok=True)
        with open(PROC_DIR / "papers.jsonl", "w") as f:
            for p in loaded_papers:
                f.write(p.model_dump_json() + "\n")

    # 2. Extract
    from src.extract import extract_all

    all_claims, all_evidence = extract_all(loaded_papers, mode=mode)
    # Record actual mode used
    if mode == "auto":
        from src.extract.llm_util import llm_available

        manifest.extractor_mode = "llm" if llm_available() else "heuristic"
    else:
        manifest.extractor_mode = mode

    manifest.n_claims = len(all_claims)
    manifest.n_evidence = len(all_evidence)

    if save:
        with open(PROC_DIR / "claims.jsonl", "w") as f:
            for c in all_claims:
                f.write(c.model_dump_json() + "\n")
        with open(PROC_DIR / "evidence.jsonl", "w") as f:
            for e in all_evidence:
                f.write(e.model_dump_json() + "\n")
        logger.info("Saved claims/evidence → %s", PROC_DIR)

    # 3. Gaps
    from src.gap.score import find_gaps

    all_gaps = find_gaps(all_claims, all_evidence, loaded_papers)
    manifest.n_gaps = len(all_gaps)
    if save:
        with open(PROC_DIR / "gaps.jsonl", "w") as f:
            for g in all_gaps:
                f.write(g.model_dump_json() + "\n")
        logger.info("Saved %d gaps", len(all_gaps))

    # 4. Topics
    from src.topics.suggest import suggest_topics

    all_topics = suggest_topics(all_gaps)
    manifest.n_topics = len(all_topics)
    if save:
        with open(PROC_DIR / "topics.jsonl", "w") as f:
            for t in all_topics:
                f.write(t.model_dump_json() + "\n")
        logger.info("Saved %d topics", len(all_topics))

    # 5. Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest.finished_at = _now_sgt().replace(tzinfo=None)
    markdown = _build_markdown_report(
        manifest, loaded_papers, all_claims, all_evidence, all_gaps, all_topics
    )
    report_path = output or (REPORTS_DIR / "latest_run.md")
    report_path.write_text(markdown)
    logger.info("Report → %s", report_path)

    # Manifest
    if save:
        with open(PROC_DIR / "run_manifest.json", "w") as f:
            f.write(manifest.model_dump_json(indent=2))

    print(f"\n{'=' * 60}")
    print(f"RUN COMPLETE — {manifest.run_id}")
    print(
        f"  Papers: {len(loaded_papers)} | Claims: {len(all_claims)} | "
        f"Evidence: {len(all_evidence)}"
    )
    print(f"  Gaps: {len(all_gaps)} | Topics: {len(all_topics)}")
    print(f"  Extractor: {manifest.extractor_mode}")
    print(f"  Report: {report_path}")
    print(f"{'=' * 60}\n")

    print("── Top 5 Gaps ──")
    for i, g in enumerate(all_gaps[:5], 1):
        print(f"  {i}. [{g.overall:.2f}] {g.title[:100]}")
    print("\n── Topic Proposals ──")
    for i, t in enumerate(all_topics, 1):
        print(f"  {i}. [{t.priority:.2f}] {t.title[:100]}")


@app.command()
def status():
    """Print docs/STATUS.md."""
    status_path = REPO_ROOT / "docs" / "STATUS.md"
    if status_path.exists():
        print(status_path.read_text())
    else:
        print("STATUS.md not found.")


@app.command("fetch-papers")
def fetch_papers(
    use_fixture: bool = typer.Option(False, "--fixture", "-f", help="Use bundled fixture papers"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max papers"),
):
    """Fetch papers from Semantic Scholar / arXiv and cache locally."""
    from src.ingest import ingest_papers

    papers = ingest_papers(use_fixture=use_fixture, save=True, limit=limit)
    print(f"Ingested {len(papers)} papers")
    for p in papers[:8]:
        print(f"  - [{p.source}] {p.title[:90]}")


def main() -> None:
    app()


if __name__ == "__main__":
    app()
