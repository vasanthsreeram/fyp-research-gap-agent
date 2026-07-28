"""CLI entry point for the Research Gap Agent."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

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

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROC_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR.parent / "reports"


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _load_papers(path: Optional[Path] = None) -> list[Paper]:
    if path and path.exists():
        papers: list[Paper] = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        papers.append(Paper(**json.loads(line)))
                    except Exception as e:
                        logger.warning("Skipping paper line: %s", e)
        if papers:
            logger.info("Loaded %d papers from %s", len(papers), path)
            return papers

    # Try default processed path
    default_path = PROC_DIR / "papers.jsonl"
    if default_path.exists():
        return _load_papers(default_path)
    return []


def _build_markdown_report(
    manifest: RunManifest,
    papers: list[Paper],
    claims: list,
    evidence: list,
    gaps: list,
    topics: list,
) -> str:
    """Write a self-contained markdown report."""
    lines: list[str] = []

    lines.append(f"# Research Gap Agent — Run Report")
    lines.append(f"")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| **Run ID** | `{manifest.run_id}` |")
    lines.append(f"| **Domain** | {manifest.domain} |")
    lines.append(f"| **Date** | {manifest.started_at.strftime('%Y-%m-%d %H:%M SGT')} |")
    lines.append(f"| **Papers** | {len(papers)} |")
    lines.append(f"| **Claims** | {len(claims)} |")
    lines.append(f"| **Evidence** | {len(evidence)} |")
    lines.append(f"| **Gaps** | {len(gaps)} |")
    lines.append(f"| **Topics** | {len(topics)} |")
    lines.append(f"| **Extractor** | {manifest.extractor_mode} |")
    lines.append(f"")

    lines.append(f"## Papers ({len(papers)})")
    lines.append(f"")
    for i, p in enumerate(papers, 1):
        lines.append(f"{i}. **{p.title}**")
        if p.authors:
            lines.append(f"   - Authors: {', '.join(p.authors[:5])}{' et al.' if len(p.authors) > 5 else ''}")
        if p.year:
            lines.append(f"   - Year: {p.year}")
        if p.doi:
            lines.append(f"   - DOI: [{p.doi}](https://doi.org/{p.doi})")
        lines.append(f"")

    lines.append(f"## Top Gaps ({len(gaps)})")
    lines.append(f"")
    for i, g in enumerate(gaps[:10], 1):
        lines.append(f"### {i}. {g.title}")
        lines.append(f"- **Kind**: `{g.kind.value}`")
        lines.append(f"- **Score**: overall={g.overall:.2f} magnitude={g.magnitude:.2f} novelty={g.novelty:.2f} testability={g.testability:.2f} impact={g.impact:.2f}")
        lines.append(f"- **Domains**: {', '.join(g.domain_tags) if g.domain_tags else '—'}")
        lines.append(f"- **Description**: {g.description[:300]}")
        lines.append(f"- **Rationale**: {g.rationale}")
        lines.append(f"")

    lines.append(f"## Research Topic Proposals ({len(topics)})")
    lines.append(f"")
    for i, t in enumerate(topics, 1):
        lines.append(f"### {i}. {t.title}")
        lines.append(f"- **Priority**: {t.priority:.2f}")
        lines.append(f"- **Domains**: {', '.join(t.domain_tags) if t.domain_tags else '—'}")
        lines.append(f"- **Hypothesis**: {t.hypothesis}")
        lines.append(f"- **Experiments**:")
        for j, exp in enumerate(t.proposed_experiments, 1):
            lines.append(f"  {j}. {exp}")
        lines.append(f"- **Expected Readout**: {t.expected_readout}")
        lines.append(f"- **Feasibility**: {t.feasibility_notes}")
        lines.append(f"- **Impact Rationale**: {t.impact_rationale}")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"*Report generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")
    return "\n".join(lines)


@app.command()
def run(
    papers_path: Optional[Path] = typer.Option(None, "--papers", "-p", help="Path to papers.jsonl"),
    domain: str = typer.Option("nucleic_acid_delivery", "--domain", "-d", help="Research domain name"),
    mode: str = typer.Option("auto", "--mode", "-m", help="Extraction mode: heuristic | llm | auto"),
    use_fixture: bool = typer.Option(False, "--fixture", "-f", help="Force fixture (offline) mode"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output report path"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save intermediate results"),
):
    """End-to-end pipeline: ingest → extract → gap-score → suggest → report."""
    manifest = RunManifest(domain=domain, extractor_mode=mode)
    logger.info("=== FYP Research Gap Agent — run %s ===", manifest.run_id)
    logger.info("Domain: %s | Extractor: %s | Fixture: %s", domain, mode, use_fixture)

    # 1. Papers
    loaded_papers = _load_papers(papers_path)
    if not loaded_papers:
        from src.ingest import ingest_papers
        logger.info("No pre-loaded papers found; running ingestion...")
        loaded_papers = ingest_papers(use_fixture=use_fixture)
    manifest.n_papers = len(loaded_papers)
    logger.info("Papers: %d", len(loaded_papers))

    if not loaded_papers:
        logger.error("No papers available. Aborting.")
        raise typer.Exit(1)

    # 2. Extract claims + evidence
    from src.extractors import extract_all
    all_claims, all_evidence = extract_all(loaded_papers, mode=mode)
    manifest.n_claims = len(all_claims)
    manifest.n_evidence = len(all_evidence)

    if save:
        out_dir = PROC_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "claims.jsonl", "w") as f:
            for c in all_claims:
                f.write(c.model_dump_json() + "\n")
        with open(out_dir / "evidence.jsonl", "w") as f:
            for e in all_evidence:
                f.write(e.model_dump_json() + "\n")
        logger.info("Saved claims and evidence to %s", out_dir)

    # 3. Gap scoring
    from src.gap_scorer import find_gaps, suggest_topics
    all_gaps = find_gaps(all_claims, all_evidence, loaded_papers)
    manifest.n_gaps = len(all_gaps)

    if save:
        with open(out_dir / "gaps.jsonl", "w") as f:
            for g in all_gaps:
                f.write(g.model_dump_json() + "\n")
        logger.info("Saved %d gaps to %s", len(all_gaps), out_dir / "gaps.jsonl")

    # 4. Topic suggestion
    all_topics = suggest_topics(all_gaps)
    manifest.n_topics = len(all_topics)

    if save:
        with open(out_dir / "topics.jsonl", "w") as f:
            for t in all_topics:
                f.write(t.model_dump_json() + "\n")
        logger.info("Saved %d topics to %s", len(all_topics), out_dir / "topics.jsonl")

    # 5. Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest.finished_at = datetime.utcnow()
    markdown = _build_markdown_report(manifest, loaded_papers, all_claims, all_evidence, all_gaps, all_topics)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = output or (REPORTS_DIR / "latest_run.md")
    with open(report_path, "w") as f:
        f.write(markdown)
    logger.info("Report written to %s", report_path)

    # Summary line for stdout
    print(f"\n{'='*60}")
    print(f"RUN COMPLETE — {manifest.run_id}")
    print(f"  Papers: {len(loaded_papers)} | Claims: {len(all_claims)} | Evidence: {len(all_evidence)}")
    print(f"  Gaps: {len(all_gaps)} | Topics: {len(all_topics)}")
    print(f"  Report: {report_path}")
    print(f"{'='*60}\n")

    # Also print top gaps + topics to stdout
    print("\n── Top 5 Gaps ──")
    for i, g in enumerate(all_gaps[:5], 1):
        print(f"  {i}. [{g.overall:.2f}] {g.title[:100]}")
    print("\n── Topic Proposals ──")
    for i, t in enumerate(all_topics, 1):
        print(f"  {i}. [{t.priority:.2f}] {t.title[:100]}")


@app.command()
def status():
    """Print current project status."""
    repo = _resolve_repo_root()
    status_path = repo / "docs" / "STATUS.md"
    if status_path.exists():
        print(status_path.read_text())
    else:
        print("STATUS.md not found.")


@app.command()
def fetch_papers(
    use_fixture: bool = typer.Option(False, "--fixture", "-f", help="Use bundled fixture papers"),
):
    """Fetch papers from Semantic Scholar and cache locally."""
    from src.ingest import ingest_papers
    papers = ingest_papers(use_fixture=use_fixture, save=True)
    print(f"Ingested {len(papers)} papers")
    for p in papers[:5]:
        print(f"  - {p.title}")


def main():
    app()


if __name__ == "__main__":
    app()
