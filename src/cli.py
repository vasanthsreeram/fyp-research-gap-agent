"""CLI entry point for the Research Gap Agent.

Usage:
  python -m src.cli run --limit 15
  python -m src run --limit 15
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import typer

from src.models import Paper, RunManifest
from src.report import build_html_report, build_markdown_report

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


@app.command()
def run(
    papers_path: Optional[Path] = typer.Option(None, "--papers", "-p", help="Path to papers.jsonl"),
    domain: str = typer.Option("nucleic_acid_delivery", "--domain", "-d", help="Research domain"),
    mode: str = typer.Option("auto", "--mode", "-m", help="Extraction mode: heuristic | llm | auto"),
    aligner: str = typer.Option(
        "auto",
        "--aligner",
        "-a",
        help="Gap aligner: auto | lexical | embedding (sentence-transformers + chroma)",
    ),
    use_fixture: bool = typer.Option(False, "--fixture", "-f", help="Force fixture (offline) mode"),
    limit: int = typer.Option(15, "--limit", "-n", help="Max papers to process"),
    refetch: bool = typer.Option(False, "--refetch", help="Force re-ingest even if cache exists"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output report path"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save intermediate JSONL artifacts"),
    no_chroma: bool = typer.Option(False, "--no-chroma", help="Skip Chroma persistence for embeddings"),
    report_format: str = typer.Option(
        "both",
        "--format",
        help="Report format: md | html | both",
    ),
    mem_bench: bool = typer.Option(
        True,
        "--mem-bench/--no-mem-bench",
        help="Run memorization/grounding benchmark after extract",
    ),
    cutoff_year: int = typer.Option(2024, "--cutoff-year", help="Post-cutoff year for mem bench"),
    domain_pack: bool = typer.Option(
        True,
        "--domain-pack/--no-domain-pack",
        help="Run LNP-core vs hybrid-ncRNA domain pack eval",
    ),
    pack_balance: bool = typer.Option(
        True,
        "--pack-balance/--no-pack-balance",
        help="Pack-aware topic ranking (reserve hybrid/gene slots so LNP mass does not monopolize top-k)",
    ),
    year_min: Optional[int] = typer.Option(
        None,
        "--year-min",
        help="Prefer papers with year >= this (live S2 filter; fixture soft-filter)",
    ),
    cross_paper: bool = typer.Option(
        True,
        "--cross-paper/--no-cross-paper",
        help="Detect multi-paper claim tensions (supportive vs limiting dialectics)",
    ),
    protocols: bool = typer.Option(
        True,
        "--protocols/--no-protocols",
        help="Build structured experiment protocol cards from topics",
    ),
    corpus_novelty: bool = typer.Option(
        True,
        "--corpus-novelty/--no-corpus-novelty",
        help="Rescore gap novelty vs rest of paper corpus (Stage 3 novelty-vs-corpus)",
    ),
    argue_mining: bool = typer.Option(
        True,
        "--argue-mining/--no-argue-mining",
        help="Quote-grounded argument mining: units + cross-paper support/attack relations (Stage 3)",
    ),
    novelty_backend: str = typer.Option(
        "lexical",
        "--novelty-backend",
        help="Corpus novelty backend: lexical | embedding | auto (default lexical for offline demos)",
    ),
    fulltext: bool = typer.Option(
        True,
        "--fulltext/--no-fulltext",
        help="Attach full text (fixture JSONL / local PDF / optional download) before extract",
    ),
    fulltext_download: bool = typer.Option(
        False,
        "--fulltext-download",
        help="Allow live PDF download (arXiv) when attaching full text",
    ),
):
    """End-to-end pipeline: ingest → extract → gap-score → suggest → report."""
    # Eager keychain resolve for auto/llm mode
    if mode in ("auto", "llm"):
        try:
            from src.extract.llm_util import resolve_openai_api_key

            resolve_openai_api_key()
        except Exception:
            pass
    # Resolve S2 key early so live ingest sees it
    if not use_fixture:
        try:
            from src.ingest.keys import resolve_s2_api_key

            resolve_s2_api_key()
        except Exception:
            pass

    started_sgt = _now_sgt()
    manifest = RunManifest(
        domain=domain,
        extractor_mode=mode,
        aligner_mode=aligner,
        # Store naive SGT wall-clock for readable reports (labeled in markdown).
        started_at=started_sgt.replace(tzinfo=None),
    )
    logger.info("=== FYP Research Gap Agent — run %s ===", manifest.run_id)
    logger.info(
        "Domain=%s mode=%s aligner=%s fixture=%s limit=%d year_min=%s cross_paper=%s novelty=%s",
        domain,
        mode,
        aligner,
        use_fixture,
        limit,
        year_min,
        cross_paper,
        corpus_novelty,
    )

    # 1. Papers
    loaded_papers: list[Paper] = []
    if papers_path:
        loaded_papers = _load_papers(papers_path)
    elif not refetch and not use_fixture:
        loaded_papers = _load_papers()

    if not loaded_papers or refetch or use_fixture:
        from src.ingest import ingest_papers

        logger.info(
            "Running ingestion (fixture=%s limit=%d year_min=%s)...",
            use_fixture,
            limit,
            year_min,
        )
        loaded_papers = ingest_papers(
            use_fixture=use_fixture,
            save=save,
            limit=limit,
            year_min=year_min,
        )
    else:
        loaded_papers = loaded_papers[: max(1, limit)]
        if year_min is not None:
            filt = [p for p in loaded_papers if (p.year or 0) >= year_min]
            if filt:
                loaded_papers = filt

    manifest.n_papers = len(loaded_papers)
    logger.info("Papers: %d", len(loaded_papers))
    if not loaded_papers:
        logger.error("No papers available. Aborting.")
        raise typer.Exit(1)

    # 1b. Full-text PDF depth (fixture offline path by default)
    ft_stats = None
    if fulltext:
        from src.ingest.pdf_text import attach_fulltext_to_papers, fulltext_markdown_report

        loaded_papers, ft_stats = attach_fulltext_to_papers(
            loaded_papers,
            use_fixture=True,
            download=fulltext_download,
            skip_existing=True,
        )
        manifest.n_fulltext = sum(1 for p in loaded_papers if p.has_full_text())
        logger.info(
            "Full-text: %d/%d papers (fixture=%d pdf=%d download=%d)",
            manifest.n_fulltext,
            len(loaded_papers),
            ft_stats.n_from_fixture,
            ft_stats.n_from_pdf,
            ft_stats.n_from_download,
        )
        if save:
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            (REPORTS_DIR / "fulltext_coverage.md").write_text(
                fulltext_markdown_report(loaded_papers, ft_stats)
            )

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
    from src.gap.score import find_gaps, resolve_aligner

    try:
        resolved_aligner = resolve_aligner(aligner)  # type: ignore[arg-type]
    except RuntimeError as e:
        logger.error("%s", e)
        raise typer.Exit(1) from e
    manifest.aligner_mode = resolved_aligner

    all_gaps = find_gaps(
        all_claims,
        all_evidence,
        loaded_papers,
        aligner=resolved_aligner,  # type: ignore[arg-type]
        use_chroma=not no_chroma,
        chroma_dir=(PROC_DIR / "chroma_gap_index") if save and not no_chroma else None,
        cross_paper=cross_paper,
    )
    novelty_report = None
    if corpus_novelty and all_gaps:
        from src.gap.novelty import apply_corpus_novelty, save_novelty_report

        try:
            all_gaps, novelty_report = apply_corpus_novelty(
                all_gaps,
                loaded_papers,
                backend=novelty_backend,  # type: ignore[arg-type]
                mutate=True,
            )
            if save:
                npath = save_novelty_report(
                    novelty_report, REPORTS_DIR / "novelty_corpus.md"
                )
                logger.info(
                    "Corpus novelty: mean=%.2f high=%d redundant=%d → %s",
                    novelty_report.mean_corpus_novelty,
                    novelty_report.n_high_novelty,
                    novelty_report.n_redundant,
                    npath,
                )
        except Exception as e:
            logger.warning("Corpus novelty pass failed (non-fatal): %s", e)
    manifest.n_gaps = len(all_gaps)
    if save:
        with open(PROC_DIR / "gaps.jsonl", "w") as f:
            for g in all_gaps:
                f.write(g.model_dump_json() + "\n")
        logger.info("Saved %d gaps (aligner=%s)", len(all_gaps), resolved_aligner)

    # 4. Topics (pack-aware ranking by default)
    from src.topics.suggest import suggest_topics

    all_topics = suggest_topics(all_gaps, pack_balance=pack_balance)
    manifest.n_topics = len(all_topics)
    if save:
        with open(PROC_DIR / "topics.jsonl", "w") as f:
            for t in all_topics:
                f.write(t.model_dump_json() + "\n")
        logger.info("Saved %d topics", len(all_topics))

    # 4b. Experiment protocol cards
    all_protocols: list = []
    if protocols:
        from src.topics.protocols import build_protocols, protocols_to_markdown

        all_protocols = build_protocols(all_topics, gaps=all_gaps)
        manifest.n_protocols = len(all_protocols)
        if save:
            with open(PROC_DIR / "protocols.jsonl", "w") as f:
                for pr in all_protocols:
                    f.write(pr.model_dump_json() + "\n")
            proto_md = REPORTS_DIR / "protocols_latest.md"
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            proto_md.write_text(protocols_to_markdown(all_protocols))
            logger.info("Saved %d protocols → %s + %s", len(all_protocols), PROC_DIR, proto_md)

    # 5. Memorization / grounding benchmark
    mem_report = None
    if mem_bench:
        from src.eval.memorization import run_memorization_benchmark, save_report

        mem_report = run_memorization_benchmark(
            loaded_papers,
            all_claims,
            all_evidence,
            cutoff_year=cutoff_year,
            run_closed_book=False,
            run_controlled=True,
        )
        mem_path = REPORTS_DIR / "memorization_bench.md"
        save_report(mem_report, mem_path)
        logger.info(
            "Mem bench: ground c=%.0f%% e=%.0f%% unsup=%.0f%% cite=%.0f%% over=%.0f%% leak=%.0f%% overall=%s",
            100 * mem_report.claim_grounding.rate,
            100 * mem_report.evidence_grounding.rate,
            100 * mem_report.unsupported_rate,
            100 * mem_report.citation_hallucination_rate,
            100 * mem_report.overconfidence_rate,
            100 * mem_report.leakage_rate,
            "PASS" if mem_report.overall_pass else "FAIL",
        )

    # 5b. Cite-grounded argument mining (Stage 3)
    argue_graph = None
    if argue_mining:
        from src.gap.argue import build_argument_graph, graph_to_gaps, save_argument_report

        try:
            argue_graph = build_argument_graph(
                loaded_papers,
                all_claims,
                all_evidence,
            )
            arg_gaps = graph_to_gaps(argue_graph, loaded_papers, max_gaps=10)
            if arg_gaps:
                existing_titles = {re.sub(r"\s+", " ", g.title.lower())[:60] for g in all_gaps}
                added = 0
                for g in arg_gaps:
                    key = re.sub(r"\s+", " ", g.title.lower())[:60]
                    if key in existing_titles:
                        continue
                    all_gaps.append(g)
                    existing_titles.add(key)
                    added += 1
                all_gaps.sort(key=lambda g: g.overall, reverse=True)
                logger.info("Added %d argue-mined conflict gaps", added)
            if save:
                with open(PROC_DIR / "argument_units.jsonl", "w") as f:
                    for u in argue_graph.units:
                        f.write(u.model_dump_json() + "\n")
                with open(PROC_DIR / "argument_relations.jsonl", "w") as f:
                    for r in argue_graph.relations:
                        f.write(r.model_dump_json() + "\n")
                save_argument_report(argue_graph, loaded_papers, REPORTS_DIR / "argument_graph.md")
            logger.info(
                "Argue mining: units=%d relations=%d attacks=%d supports=%d",
                argue_graph.n_units,
                argue_graph.n_relations,
                argue_graph.n_attack,
                argue_graph.n_support,
            )
        except Exception as e:
            logger.warning("Argue-mining pass failed (non-fatal): %s", e)

    # 6. Report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest.finished_at = _now_sgt().replace(tzinfo=None)
    fmt = (report_format or "both").lower().strip()
    report_path = output or (REPORTS_DIR / "latest_run.md")
    written: list[Path] = []

    if fmt in ("md", "both", "markdown"):
        md_path = report_path if report_path.suffix.lower() in {".md", ".markdown"} else report_path.with_suffix(".md")
        md_path.write_text(
            build_markdown_report(
                manifest,
                loaded_papers,
                all_claims,
                all_evidence,
                all_gaps,
                all_topics,
                protocols=all_protocols,
            )
        )
        written.append(md_path)
        logger.info("Report → %s", md_path)

    if fmt in ("html", "both"):
        if output and str(output).lower().endswith(".html"):
            html_path = output
        else:
            html_path = REPORTS_DIR / "latest_run.html"
        html_path.write_text(
            build_html_report(
                manifest,
                loaded_papers,
                all_claims,
                all_evidence,
                all_gaps,
                all_topics,
                protocols=all_protocols,
            )
        )
        written.append(html_path)
        logger.info("HTML report → %s", html_path)

    # Manifest
    if save:
        with open(PROC_DIR / "run_manifest.json", "w") as f:
            f.write(manifest.model_dump_json(indent=2))

    print(f"\n{'=' * 60}")
    print(f"RUN COMPLETE — {manifest.run_id}")
    print(
        f"  Papers: {len(loaded_papers)} | Full-text: {getattr(manifest, 'n_fulltext', 0)} | "
        f"Claims: {len(all_claims)} | Evidence: {len(all_evidence)}"
    )
    print(f"  Gaps: {len(all_gaps)} | Topics: {len(all_topics)} | Protocols: {len(all_protocols)}")
    n_x = sum(1 for g in all_gaps if getattr(g.kind, "value", "") == "cross_paper_tension")
    if n_x:
        print(f"  Cross-paper tension gaps: {n_x}")
    n_arg = sum(1 for g in all_gaps if getattr(g.kind, "value", "") == "argue_mined_conflict")
    if n_arg:
        print(f"  Argue-mined conflict gaps: {n_arg}")
    if argue_graph is not None:
        print(
            f"  Argument graph: units={argue_graph.n_units} "
            f"relations={argue_graph.n_relations} "
            f"attacks={argue_graph.n_attack} supports={argue_graph.n_support}"
        )
    if novelty_report is not None:
        print(
            f"  Corpus novelty: mean={novelty_report.mean_corpus_novelty:.2f} "
            f"high≥0.55={novelty_report.n_high_novelty} "
            f"redundant≥0.55={novelty_report.n_redundant} "
            f"({novelty_report.backend})"
        )
    print(f"  Extractor: {manifest.extractor_mode} | Aligner: {manifest.aligner_mode}")
    if mem_report is not None:
        print(
            f"  Mem-bench: {'PASS' if mem_report.overall_pass else 'FAIL'} "
            f"(ground {mem_report.claim_grounding.rate:.0%}, "
            f"unsup {mem_report.unsupported_rate:.0%}, "
            f"cite {mem_report.citation_hallucination_rate:.0%}, "
            f"post-cutoff n={mem_report.n_post_cutoff})"
        )
    print(f"  Reports: {', '.join(str(p) for p in written)}")
    print(f"{'=' * 60}\n")

    # 7. Domain pack eval (LNP core vs hybrid ncRNA)
    if domain_pack:
        from src.eval.domain_pack import run_domain_pack_eval, save_domain_pack_report

        dreport = run_domain_pack_eval(
            loaded_papers,
            all_claims,
            all_evidence,
            all_gaps,
            all_topics,
            cutoff_year=cutoff_year,
        )
        dpath = save_domain_pack_report(dreport, REPORTS_DIR / "domain_pack.md")
        logger.info(
            "Domain pack: overall=%s | %s",
            "PASS" if dreport.overall_pass else "FAIL",
            ", ".join(f"{p.pack_id}:{p.n_papers}p/{p.n_gaps}g" for p in dreport.packs),
        )
        print(f"  Domain-pack: {'PASS' if dreport.overall_pass else 'FAIL'} → {dpath}")

    print("── Top 5 Gaps ──")
    for i, g in enumerate(all_gaps[:5], 1):
        print(f"  {i}. [{g.overall:.2f}] {g.title[:100]}")
    print("\n── Topic Proposals ──")
    for i, t in enumerate(all_topics, 1):
        print(f"  {i}. [{t.priority:.2f}] {t.title[:100]}")
    if all_protocols:
        print("\n── Experiment Protocols ──")
        for i, pr in enumerate(all_protocols, 1):
            print(f"  {i}. [{pr.pack_id or '—'}] {pr.title[:100]}")


@app.command()
def status():
    """Print docs/STATUS.md."""
    status_path = REPO_ROOT / "docs" / "STATUS.md"
    if status_path.exists():
        print(status_path.read_text())
    else:
        print("STATUS.md not found.")


@app.command("fulltext")
def fulltext_cmd(
    papers_path: Optional[Path] = typer.Option(None, "--papers", "-p", help="papers.jsonl"),
    use_fixture_papers: bool = typer.Option(True, "--fixture/--no-fixture", help="Load fixture papers if no cache"),
    limit: int = typer.Option(52, "--limit", "-n"),
    download: bool = typer.Option(False, "--download", help="Allow live arXiv/OA PDF download"),
    max_attach: Optional[int] = typer.Option(None, "--max-attach", help="Cap number of full-text attaches"),
    save: bool = typer.Option(True, "--save/--no-save"),
):
    """Attach full text (offline fixture body / local PDF / optional download) and report coverage."""
    from src.ingest import ingest_papers
    from src.ingest.pdf_text import attach_fulltext_to_papers, fulltext_markdown_report

    papers = _load_papers(papers_path) if papers_path else _load_papers()
    if not papers:
        papers = ingest_papers(use_fixture=use_fixture_papers, save=False, limit=limit)
    else:
        papers = papers[: max(1, limit)]

    papers, stats = attach_fulltext_to_papers(
        papers,
        use_fixture=True,
        download=download,
        max_attach=max_attach,
        skip_existing=True,
    )
    md = fulltext_markdown_report(papers, stats)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "fulltext_coverage.md"
    out.write_text(md)
    if save:
        PROC_DIR.mkdir(parents=True, exist_ok=True)
        with open(PROC_DIR / "papers.jsonl", "w") as f:
            for p in papers:
                f.write(p.model_dump_json() + "\n")
        # Also dump section index for inspection
        with open(PROC_DIR / "fulltext_sections.jsonl", "w") as f:
            for p in papers:
                if not p.has_full_text():
                    continue
                f.write(
                    json.dumps(
                        {
                            "paper_id": p.id,
                            "title": p.title,
                            "full_text_source": p.full_text_source,
                            "n_chars": len(p.full_text or ""),
                            "sections": [s.model_dump() for s in p.sections],
                        }
                    )
                    + "\n"
                )
    n_ft = sum(1 for p in papers if p.has_full_text())
    print(f"Full-text attached: {n_ft}/{len(papers)}")
    print(f"  fixture={stats.n_from_fixture} local_pdf={stats.n_from_pdf} download={stats.n_from_download} failed={stats.n_failed}")
    print(f"Report → {out}")
    for p in papers:
        if p.has_full_text():
            kinds = ",".join(s.kind.value for s in p.sections[:8])
            print(f"  - {p.title[:70]} [{p.full_text_source}] secs={kinds}")


@app.command("fetch-papers")
def fetch_papers(
    use_fixture: bool = typer.Option(False, "--fixture", "-f", help="Use bundled fixture papers"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max papers"),
    year_min: Optional[int] = typer.Option(None, "--year-min", help="Min publication year"),
    year_max: Optional[int] = typer.Option(None, "--year-max", help="Max publication year"),
    no_openalex: bool = typer.Option(False, "--no-openalex", help="Skip OpenAlex live source"),
):
    """Fetch papers from Semantic Scholar / OpenAlex / arXiv and cache locally."""
    from src.ingest import ingest_papers
    from src.ingest.keys import resolve_s2_api_key, s2_key_status

    if not use_fixture:
        resolve_s2_api_key()
        st = s2_key_status()
        print(f"S2 key present: {st['present']} (source={st['source']})")
        print("OpenAlex: enabled (no key; free polite pool)" if not no_openalex else "OpenAlex: skipped")
    papers = ingest_papers(
        use_fixture=use_fixture,
        save=True,
        limit=limit,
        year_min=year_min,
        year_max=year_max,
        include_openalex=not no_openalex,
    )
    print(f"Ingested {len(papers)} papers")
    from collections import Counter

    src_counts = Counter(p.source for p in papers)
    print(f"  sources: {dict(src_counts)}")
    for p in papers[:8]:
        y = p.year or "?"
        print(f"  - [{p.source}|{y}] {p.title[:90]}")


@app.command("s2-status")
def s2_status_cmd():
    """Show whether a Semantic Scholar API key is resolvable (no secret printed)."""
    from src.ingest.keys import resolve_s2_api_key, s2_key_status

    resolve_s2_api_key()
    st = s2_key_status()
    print("Semantic Scholar API key status")
    print(f"  present: {st['present']}")
    print(f"  source:  {st['source']}")
    print(f"  hint:    {st['hint']}")
    raise typer.Exit(0 if st["present"] else 1)


@app.command("openalex-status")
def openalex_status_cmd(
    probe: bool = typer.Option(True, "--probe/--no-probe", help="Hit OpenAlex with a tiny search"),
):
    """Show OpenAlex live-ingest path status (no API key required)."""
    from src.ingest.openalex import openalex_status

    st = openalex_status(probe=probe)
    print("OpenAlex status")
    print(f"  endpoint: {st['endpoint']}")
    print(f"  mailto:   {st['mailto']}")
    print(f"  reachable:{st['reachable']}")
    print(f"  sample:   {st['sample_count']}")
    print(f"  hint:     {st['hint']}")
    ok = st["reachable"] is True or st["reachable"] is None
    raise typer.Exit(0 if ok else 1)


@app.command("protocols")
def protocols_cmd(
    papers_path: Optional[Path] = typer.Option(None, "--papers", "-p"),
    mode: str = typer.Option("heuristic", "--mode", "-m"),
    aligner: str = typer.Option("lexical", "--aligner", "-a"),
    limit: int = typer.Option(52, "--limit", "-n"),
    use_fixture: bool = typer.Option(True, "--fixture/--no-fixture"),
    max_protocols: int = typer.Option(5, "--max", help="Max protocol cards"),
):
    """Build experiment protocol cards from fixture/live pipeline (offline-first)."""
    from src.extract import extract_all
    from src.gap.score import find_gaps, resolve_aligner
    from src.ingest import ingest_papers
    from src.topics.protocols import build_protocols, protocols_to_markdown
    from src.topics.suggest import suggest_topics

    if papers_path:
        papers = _load_papers(papers_path)[:limit]
    elif use_fixture:
        papers = ingest_papers(use_fixture=True, save=False, limit=limit)
    else:
        papers = _load_papers()[:limit] or ingest_papers(use_fixture=True, save=False, limit=limit)

    if not papers:
        raise typer.Exit(1)

    claims, evidence = extract_all(papers, mode=mode)
    resolved = resolve_aligner(aligner)  # type: ignore[arg-type]
    gaps = find_gaps(claims, evidence, papers, aligner=resolved, use_chroma=False)  # type: ignore[arg-type]
    topics = suggest_topics(gaps, pack_balance=True)
    protos = build_protocols(topics, gaps=gaps, max_protocols=max_protocols)
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROC_DIR / "protocols.jsonl", "w") as f:
        for pr in protos:
            f.write(pr.model_dump_json() + "\n")
    out = REPORTS_DIR / "protocols_latest.md"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md = protocols_to_markdown(protos)
    out.write_text(md)
    print(md)
    print(f"\nSaved {len(protos)} protocols → {out}")
    raise typer.Exit(0)


@app.command("novelty")
def novelty_cmd(
    papers_path: Optional[Path] = typer.Option(None, "--papers", "-p"),
    mode: str = typer.Option("heuristic", "--mode", "-m"),
    aligner: str = typer.Option("lexical", "--aligner", "-a"),
    limit: int = typer.Option(52, "--limit", "-n"),
    use_fixture: bool = typer.Option(True, "--fixture/--no-fixture"),
    backend: str = typer.Option(
        "lexical",
        "--backend",
        "-b",
        help="lexical | embedding | auto",
    ),
    top: int = typer.Option(12, "--top", help="Top surprising gaps in report"),
):
    """Score gaps for novelty vs rest of paper corpus (offline-first)."""
    from src.extract import extract_all
    from src.gap.novelty import apply_corpus_novelty, novelty_report_markdown, save_novelty_report
    from src.gap.score import find_gaps, resolve_aligner
    from src.ingest import ingest_papers

    if papers_path:
        papers = _load_papers(papers_path)[:limit]
    elif use_fixture:
        papers = ingest_papers(use_fixture=True, save=False, limit=limit)
    else:
        papers = _load_papers()[:limit] or ingest_papers(use_fixture=True, save=False, limit=limit)

    if not papers:
        raise typer.Exit(1)

    claims, evidence = extract_all(papers, mode=mode)
    resolved = resolve_aligner(aligner)  # type: ignore[arg-type]
    gaps = find_gaps(claims, evidence, papers, aligner=resolved, use_chroma=False)  # type: ignore[arg-type]
    gaps, report = apply_corpus_novelty(gaps, papers, backend=backend, mutate=True)  # type: ignore[arg-type]

    PROC_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROC_DIR / "gaps.jsonl", "w") as f:
        for g in gaps:
            f.write(g.model_dump_json() + "\n")
    out = REPORTS_DIR / "novelty_corpus.md"
    save_novelty_report(report, out, top_n=top)
    print(novelty_report_markdown(report, top_n=top))
    print(
        f"\nCorpus novelty mean={report.mean_corpus_novelty:.2f} "
        f"high={report.n_high_novelty} redundant={report.n_redundant} backend={report.backend}"
    )
    print(f"Saved → {out} (+ gaps.jsonl rescored)")
    raise typer.Exit(0)


@app.command("argue")
def argue_cmd(
    papers_path: Optional[Path] = typer.Option(None, "--papers", "-p"),
    mode: str = typer.Option("heuristic", "--mode", "-m"),
    limit: int = typer.Option(52, "--limit", "-n"),
    use_fixture: bool = typer.Option(True, "--fixture/--no-fixture"),
    sim_threshold: float = typer.Option(0.22, "--sim-threshold", help="Min token similarity for relations"),
    top: int = typer.Option(12, "--top", help="Top relations in report"),
):
    """Quote-grounded argument mining: units + cross-paper support/attack relations."""
    from src.extract import extract_all
    from src.gap.argue import (
        argument_markdown,
        build_argument_graph,
        graph_to_gaps,
        save_argument_report,
    )
    from src.ingest import ingest_papers

    if papers_path:
        papers = _load_papers(papers_path)[:limit]
    elif use_fixture:
        papers = ingest_papers(use_fixture=True, save=False, limit=limit)
    else:
        papers = _load_papers()[:limit] or ingest_papers(use_fixture=True, save=False, limit=limit)

    if not papers:
        raise typer.Exit(1)

    claims, evidence = extract_all(papers, mode=mode)
    graph = build_argument_graph(papers, claims, evidence, sim_threshold=sim_threshold)
    gaps = graph_to_gaps(graph, papers, max_gaps=10)

    PROC_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROC_DIR / "argument_units.jsonl", "w") as f:
        for u in graph.units:
            f.write(u.model_dump_json() + "\n")
    with open(PROC_DIR / "argument_relations.jsonl", "w") as f:
        for r in graph.relations:
            f.write(r.model_dump_json() + "\n")
    out = REPORTS_DIR / "argument_graph.md"
    save_argument_report(graph, papers, out)

    print(
        f"Argument graph: units={graph.n_units} relations={graph.n_relations} "
        f"attacks={graph.n_attack} supports={graph.n_support}"
    )
    print(f"Argue-mined conflict gaps: {len(gaps)}")
    print(argument_markdown(graph, papers, top_relations=top))
    print(f"\nSaved → {out} (+ argument_units/relations.jsonl)")
    raise typer.Exit(0)


@app.command("mem-bench")
def mem_bench_cmd(
    papers_path: Optional[Path] = typer.Option(None, "--papers", "-p", help="Path to papers.jsonl"),
    mode: str = typer.Option("heuristic", "--mode", "-m", help="Extraction mode"),
    cutoff_year: int = typer.Option(2024, "--cutoff-year"),
    closed_book: bool = typer.Option(False, "--closed-book", help="Run optional LLM closed-book probe"),
    controlled: bool = typer.Option(True, "--controlled/--no-controlled", help="Run synthetic controlled cases"),
    limit: int = typer.Option(50, "--limit", "-n"),
    use_fixture: bool = typer.Option(True, "--fixture/--no-fixture", help="Load fixture corpus"),
):
    """Run memorization/grounding benchmark (offline-first)."""
    from src.eval.memorization import run_memorization_benchmark, save_report
    from src.extract import extract_all
    from src.ingest import ingest_papers

    if papers_path:
        papers = _load_papers(papers_path)[:limit]
    elif use_fixture:
        papers = ingest_papers(use_fixture=True, save=False, limit=limit)
    else:
        papers = _load_papers()[:limit]
        if not papers:
            papers = ingest_papers(use_fixture=True, save=False, limit=limit)

    if not papers:
        raise typer.Exit(1)

    claims, evidence = extract_all(papers, mode=mode)
    report = run_memorization_benchmark(
        papers,
        claims,
        evidence,
        cutoff_year=cutoff_year,
        run_closed_book=closed_book,
        run_controlled=controlled,
    )
    out = REPORTS_DIR / "memorization_bench.md"
    save_report(report, out)
    print(report.to_markdown())
    print(f"\nSaved → {out}")
    raise typer.Exit(0 if report.overall_pass else 2)


@app.command("domain-pack")
def domain_pack_cmd(
    papers_path: Optional[Path] = typer.Option(None, "--papers", "-p"),
    mode: str = typer.Option("heuristic", "--mode", "-m"),
    aligner: str = typer.Option("lexical", "--aligner", "-a"),
    limit: int = typer.Option(50, "--limit", "-n"),
    cutoff_year: int = typer.Option(2024, "--cutoff-year"),
    use_fixture: bool = typer.Option(True, "--fixture/--no-fixture"),
):
    """Run second-domain pack coverage eval (LNP core vs hybrid ncRNA)."""
    from src.eval.domain_pack import run_domain_pack_eval, save_domain_pack_report
    from src.extract import extract_all
    from src.gap.score import find_gaps, resolve_aligner
    from src.ingest import ingest_papers
    from src.topics.suggest import suggest_topics

    if papers_path:
        papers = _load_papers(papers_path)[:limit]
    elif use_fixture:
        papers = ingest_papers(use_fixture=True, save=False, limit=limit)
    else:
        papers = _load_papers()[:limit] or ingest_papers(use_fixture=True, save=False, limit=limit)

    if not papers:
        raise typer.Exit(1)

    claims, evidence = extract_all(papers, mode=mode)
    resolved = resolve_aligner(aligner)  # type: ignore[arg-type]
    gaps = find_gaps(claims, evidence, papers, aligner=resolved, use_chroma=False)  # type: ignore[arg-type]
    topics = suggest_topics(gaps, pack_balance=True)
    report = run_domain_pack_eval(
        papers, claims, evidence, gaps, topics, cutoff_year=cutoff_year
    )
    out = save_domain_pack_report(report)
    print(report.to_markdown())
    print(f"\nSaved → {out}")
    raise typer.Exit(0 if report.overall_pass else 2)


@app.command("feedback-add")
def feedback_add_cmd(
    target_type: str = typer.Option(..., "--type", "-t", help="gap|topic|claim|evidence|run"),
    target_id: str = typer.Option(..., "--id", help="Artifact id"),
    rating: Optional[int] = typer.Option(None, "--rating", "-r", min=1, max=5),
    labels: str = typer.Option("", "--labels", "-l", help="Comma-separated labels"),
    notes: str = typer.Option("", "--notes", "-n"),
    reviewer: str = typer.Option("vas", "--reviewer"),
    run_id: Optional[str] = typer.Option(None, "--run-id"),
):
    """Append a human feedback record (JSONL under data/processed/feedback.jsonl)."""
    from src.eval.feedback import SUGGESTED_LABELS, add_rating

    label_list = [x.strip() for x in labels.split(",") if x.strip()]
    try:
        rec = add_rating(
            target_type=target_type,
            target_id=target_id,
            rating=rating,
            labels=label_list,
            notes=notes,
            reviewer=reviewer,
            run_id=run_id,
        )
    except Exception as e:
        logger.error("%s", e)
        print(f"Suggested labels: {', '.join(SUGGESTED_LABELS)}")
        raise typer.Exit(1) from e
    print(f"Saved {rec.id} type={rec.target_type.value} target={rec.target_id} rating={rec.rating}")


@app.command("feedback-summary")
def feedback_summary_cmd(
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
):
    """Summarize collected human feedback."""
    from src.eval.feedback import summary_markdown

    md = summary_markdown()
    out = output or (REPORTS_DIR / "feedback_summary.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md)
    print(md)
    print(f"\nSaved → {out}")


def main() -> None:
    app()


if __name__ == "__main__":
    app()
