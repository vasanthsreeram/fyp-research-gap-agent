"""HTML + markdown report builders for pipeline runs."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from src.models import Paper, RunManifest

SGT = ZoneInfo("Asia/Singapore")


def _esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def build_markdown_report(
    manifest: RunManifest,
    papers: list[Paper],
    claims: list,
    evidence: list,
    gaps: list,
    topics: list,
    *,
    protocols: Optional[list] = None,
    now: Optional[datetime] = None,
) -> str:
    now = now or datetime.now(tz=SGT)
    protocols = protocols or []
    lines: list[str] = []
    started = manifest.started_at
    if started.tzinfo is None:
        started_s = started.strftime("%Y-%m-%d %H:%M") + " SGT"
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
        f"| **Full-text** | {getattr(manifest, 'n_fulltext', sum(1 for p in papers if getattr(p, 'has_full_text', lambda: False)()))} |",
        f"| **Claims** | {len(claims)} |",
        f"| **Evidence** | {len(evidence)} |",
        f"| **Gaps** | {len(gaps)} |",
        f"| **Topics** | {len(topics)} |",
        f"| **Protocols** | {len(protocols)} |",
        f"| **Extractor** | {manifest.extractor_mode} |",
        f"| **Aligner** | {manifest.aligner_mode} |",
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
        if getattr(p, "has_full_text", lambda: False)():
            nsec = len(getattr(p, "sections", None) or [])
            lines.append(
                f"   - Full text: `{p.full_text_source or 'yes'}` · {len(p.full_text or '')} chars · {nsec} sections"
            )
        if p.doi:
            lines.append(f"   - DOI: [{p.doi}](https://doi.org/{p.doi})")
        if p.arxiv_id:
            lines.append(f"   - arXiv: [{p.arxiv_id}](https://arxiv.org/abs/{p.arxiv_id})")
        lines.append("")

    lines += [f"## Top Gaps ({len(gaps)})", ""]
    n_cross = sum(
        1 for g in gaps if getattr(getattr(g, "kind", None), "value", "") == "cross_paper_tension"
    )
    n_arg = sum(
        1 for g in gaps if getattr(getattr(g, "kind", None), "value", "") == "argue_mined_conflict"
    )
    if n_cross or n_arg:
        bits = []
        if n_cross:
            bits.append(f"**{n_cross}** cross-paper tension gaps (multi-paper dialectics)")
        if n_arg:
            bits.append(f"**{n_arg}** argue-mined conflict gaps (quote-grounded support/attack)")
        lines += [f"_Including {', '.join(bits)}._", ""]
    for i, g in enumerate(gaps[:12], 1):
        n_papers = len(getattr(g, "paper_ids", None) or [])
        cn = getattr(g, "corpus_novelty", None)
        red = getattr(g, "gap_redundancy", None)
        corp_bits = []
        if cn is not None:
            corp_bits.append(f"corpus_novelty={cn:.2f}")
        if red is not None:
            corp_bits.append(f"redundancy={red:.2f}")
        corp_line = f"- **Corpus**: {', '.join(corp_bits)}" if corp_bits else ""
        quote_bits = []
        quotes = getattr(g, "grounded_quotes", None) or []
        if quotes:
            for q in quotes[:2]:
                quote_bits.append(f"> {q}")
        lines += [
            f"### {i}. {g.title}",
            f"- **Kind**: `{g.kind.value}`"
            + (f" · **papers**: {n_papers}" if n_papers > 1 else ""),
            (
                f"- **Score**: overall={g.overall:.2f} magnitude={g.magnitude:.2f} "
                f"novelty={g.novelty:.2f} testability={g.testability:.2f} impact={g.impact:.2f}"
            ),
        ]
        if corp_line:
            lines.append(corp_line)
        lines += [
            f"- **Domains**: {', '.join(g.domain_tags) if g.domain_tags else '—'}",
            f"- **Description**: {g.description[:350]}",
            f"- **Rationale**: {g.rationale}",
        ]
        if quote_bits:
            lines += [""] + quote_bits
        lines += ["", ""]

    lines += [f"## Research Topic Proposals ({len(topics)})", ""]
    for i, t in enumerate(topics, 1):
        lines += [
            f"### {i}. {t.title}",
            f"- **Priority**: {t.priority:.2f}"
            + (
                f" · rank={getattr(t, 'rank_score', t.priority):.2f}"
                if getattr(t, "rank_score", None) is not None
                else ""
            ),
            f"- **Pack**: {getattr(t, 'pack_id', None) or '—'}",
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

    if protocols:
        lines += [f"## Experiment Protocol Cards ({len(protocols)})", ""]
        lines += [
            "_Structured mini-protocols (controls, assays, success/stop rules). "
            "Prototype design aids — not wet-lab SOPs._",
            "",
        ]
        for i, pr in enumerate(protocols, 1):
            lines += [
                f"### {i}. {pr.title}",
                f"- **Pack**: {getattr(pr, 'pack_id', None) or '—'} · **topic**: `{getattr(pr, 'topic_id', '')}`",
                f"- **Primary aim**: {getattr(pr, 'primary_aim', '')}",
                f"- **Hypothesis**: {getattr(pr, 'hypothesis', '')}",
                "- **Controls**:",
            ]
            for c in getattr(pr, "controls", None) or []:
                lines.append(f"  - {c}")
            lines.append("- **Assay panel**:")
            for a in getattr(pr, "assay_panel", None) or []:
                lines.append(f"  - {a}")
            lines.append("- **Success criteria**:")
            for s in getattr(pr, "success_criteria", None) or []:
                lines.append(f"  - {s}")
            lines.append("- **Stop rules**:")
            for s in getattr(pr, "stop_rules", None) or []:
                lines.append(f"  - {s}")
            lines += [
                f"- **Readout**: {getattr(pr, 'expected_readout', '') or '—'}",
                f"- **Feasibility**: {getattr(pr, 'feasibility_notes', '') or '—'}",
                "",
            ]

    lines += [
        "---",
        f"*Report generated at {now.strftime('%Y-%m-%d %H:%M %Z')}*",
    ]
    return "\n".join(lines)


def build_html_report(
    manifest: RunManifest,
    papers: list[Paper],
    claims: list,
    evidence: list,
    gaps: list,
    topics: list,
    *,
    protocols: Optional[list] = None,
    now: Optional[datetime] = None,
) -> str:
    """Self-contained HTML report for offline viewing / supervisor demo."""
    now = now or datetime.now(tz=SGT)
    protocols = protocols or []
    started = manifest.started_at
    if started.tzinfo is None:
        started_s = started.strftime("%Y-%m-%d %H:%M") + " SGT"
    else:
        started_s = started.astimezone(SGT).strftime("%Y-%m-%d %H:%M %Z")

    kind_counts: dict[str, int] = {}
    for g in gaps:
        k = g.kind.value if hasattr(g.kind, "value") else str(g.kind)
        kind_counts[k] = kind_counts.get(k, 0) + 1

    def bar_row(label: str, n: int, max_n: int) -> str:
        pct = int(100 * n / max_n) if max_n else 0
        return (
            f'<div class="bar-row"><span class="bar-label">{_esc(label)}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>'
            f'<span class="bar-n">{n}</span></div>'
        )

    max_kind = max(kind_counts.values()) if kind_counts else 1
    kind_bars = "\n".join(bar_row(k, n, max_kind) for k, n in sorted(kind_counts.items(), key=lambda x: -x[1]))

    paper_items = []
    for i, p in enumerate(papers, 1):
        meta = []
        if p.year:
            meta.append(str(p.year))
        if p.venue:
            meta.append(p.venue)
        if p.source:
            meta.append(p.source)
        doi = (
            f'<a href="https://doi.org/{_esc(p.doi)}" target="_blank" rel="noopener">{_esc(p.doi)}</a>'
            if p.doi
            else ""
        )
        paper_items.append(
            f"<li><strong>{_esc(p.title)}</strong>"
            f"<div class='meta'>{_esc(' · '.join(meta))} {doi}</div></li>"
        )

    gap_blocks = []
    for i, g in enumerate(gaps[:12], 1):
        n_p = len(getattr(g, "paper_ids", None) or [])
        multi = f'<span class="tag">{n_p} papers</span>' if n_p > 1 else ""
        cn = getattr(g, "corpus_novelty", None)
        red = getattr(g, "gap_redundancy", None)
        corp_tags = ""
        if cn is not None:
            corp_tags += f'<span class="tag">corpus_nov {cn:.2f}</span>'
        if red is not None:
            corp_tags += f'<span class="tag">redund {red:.2f}</span>'
        gap_blocks.append(
            f"""<article class="card">
  <h3>{i}. {_esc(g.title)}</h3>
  <div class="tags"><span class="tag">{_esc(g.kind.value)}</span>
  {multi}
  {corp_tags}
  <span class="score">overall {g.overall:.2f}</span></div>
  <p>{_esc(g.description[:400])}</p>
  <p class="muted">{_esc(g.rationale)}</p>
</article>"""
        )

    topic_blocks = []
    for i, t in enumerate(topics, 1):
        exps = "".join(f"<li>{_esc(e)}</li>" for e in t.proposed_experiments)
        pack_label = getattr(t, "pack_id", None) or "—"
        rank = getattr(t, "rank_score", None)
        rank_bit = f" · rank {rank:.2f}" if rank is not None else ""
        topic_blocks.append(
            f"""<article class="card highlight">
  <h3>{i}. {_esc(t.title)}</h3>
  <div class="tags"><span class="score">priority {t.priority:.2f}{rank_bit}</span>
  <span class="tag">pack:{_esc(pack_label)}</span>
  <span class="tag">{_esc(', '.join(t.domain_tags) or '—')}</span></div>
  <p><strong>Hypothesis.</strong> {_esc(t.hypothesis)}</p>
  <p><strong>Experiments</strong></p>
  <ol>{exps}</ol>
  <p><strong>Readout.</strong> {_esc(t.expected_readout)}</p>
</article>"""
        )

    proto_blocks = []
    for i, pr in enumerate(protocols, 1):
        ctrls = "".join(f"<li>{_esc(c)}</li>" for c in (getattr(pr, "controls", None) or [])[:6])
        assays = "".join(f"<li>{_esc(a)}</li>" for a in (getattr(pr, "assay_panel", None) or [])[:6])
        success = "".join(
            f"<li>{_esc(s)}</li>" for s in (getattr(pr, "success_criteria", None) or [])[:4]
        )
        pack_label = getattr(pr, "pack_id", None) or "—"
        proto_blocks.append(
            f"""<article class="card">
  <h3>{i}. {_esc(getattr(pr, 'title', ''))}</h3>
  <div class="tags"><span class="tag">protocol</span>
  <span class="tag">pack:{_esc(pack_label)}</span></div>
  <p><strong>Aim.</strong> {_esc(getattr(pr, 'primary_aim', ''))}</p>
  <p><strong>Controls</strong></p><ul>{ctrls}</ul>
  <p><strong>Assays</strong></p><ul>{assays}</ul>
  <p><strong>Success</strong></p><ul>{success}</ul>
  <p class="muted">{_esc((getattr(pr, 'expected_readout', None) or '')[:240])}</p>
</article>"""
        )

    funnel = [
        ("Papers", len(papers)),
        ("Claims", len(claims)),
        ("Evidence", len(evidence)),
        ("Gaps", len(gaps)),
        ("Topics", len(topics)),
        ("Protocols", len(protocols)),
    ]
    fmax = max(n for _, n in funnel) or 1
    funnel_html = "\n".join(bar_row(l, n, fmax) for l, n in funnel)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Research Gap Agent — {_esc(manifest.run_id)}</title>
<style>
  :root {{
    --bg: #0b1220; --card: #121a2b; --text: #e7eefc; --muted: #9db0d0;
    --accent: #6ea8fe; --accent2: #3dd6c6; --line: #243047;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    background: radial-gradient(1200px 600px at 10% -10%, #1a2744, var(--bg));
    color: var(--text); line-height: 1.55;
  }}
  main {{ max-width: 960px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 .25rem; }}
  h2 {{ margin-top: 2rem; border-bottom: 1px solid var(--line); padding-bottom: .4rem; }}
  h3 {{ margin: 0 0 .5rem; font-size: 1.05rem; }}
  .sub {{ color: var(--muted); margin-bottom: 1.25rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: .75rem; }}
  .stat {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: .9rem 1rem; }}
  .stat b {{ display: block; font-size: 1.4rem; color: var(--accent2); }}
  .stat span {{ color: var(--muted); font-size: .85rem; }}
  .card {{
    background: var(--card); border: 1px solid var(--line); border-radius: 14px;
    padding: 1rem 1.1rem; margin: .75rem 0;
  }}
  .card.highlight {{ border-color: #2a4d6f; box-shadow: inset 0 0 0 1px rgba(110,168,254,.15); }}
  .tags {{ display: flex; gap: .5rem; flex-wrap: wrap; margin-bottom: .5rem; }}
  .tag, .score {{
    font-size: .75rem; padding: .15rem .55rem; border-radius: 999px;
    background: #1b283f; color: var(--accent); border: 1px solid #2a3d5c;
  }}
  .score {{ color: var(--accent2); }}
  .muted {{ color: var(--muted); font-size: .92rem; }}
  .meta {{ color: var(--muted); font-size: .85rem; margin-top: .15rem; }}
  a {{ color: var(--accent); }}
  ol.papers {{ padding-left: 1.1rem; }}
  ol.papers li {{ margin: .55rem 0; }}
  .bar-row {{ display: grid; grid-template-columns: 140px 1fr 40px; gap: .5rem; align-items: center; margin: .35rem 0; }}
  .bar-label {{ color: var(--muted); font-size: .85rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .bar-track {{ background: #1b283f; border-radius: 999px; height: 8px; overflow: hidden; }}
  .bar-fill {{ background: linear-gradient(90deg, var(--accent2), var(--accent)); height: 100%; }}
  .bar-n {{ text-align: right; font-variant-numeric: tabular-nums; font-size: .85rem; }}
  footer {{ margin-top: 2.5rem; color: var(--muted); font-size: .85rem; }}
</style>
</head>
<body>
<main>
  <h1>Research Gap Agent — Run Report</h1>
  <p class="sub">Run <code>{_esc(manifest.run_id)}</code> · {_esc(started_s)} · domain {_esc(manifest.domain)}</p>

  <div class="grid">
    <div class="stat"><b>{len(papers)}</b><span>Papers</span></div>
    <div class="stat"><b>{getattr(manifest, 'n_fulltext', sum(1 for p in papers if getattr(p, 'has_full_text', lambda: False)()))}</b><span>Full-text</span></div>
    <div class="stat"><b>{len(claims)}</b><span>Claims</span></div>
    <div class="stat"><b>{len(evidence)}</b><span>Evidence</span></div>
    <div class="stat"><b>{len(gaps)}</b><span>Gaps</span></div>
    <div class="stat"><b>{len(topics)}</b><span>Topics</span></div>
    <div class="stat"><b>{len(protocols)}</b><span>Protocols</span></div>
    <div class="stat"><b>{_esc(manifest.extractor_mode)}</b><span>Extractor</span></div>
    <div class="stat"><b>{_esc(manifest.aligner_mode)}</b><span>Aligner</span></div>
  </div>

  <h2>Pipeline funnel</h2>
  <div class="card">{funnel_html}</div>

  <h2>Gap kinds</h2>
  <div class="card">{kind_bars or '<p class="muted">No gaps</p>'}</div>

  <h2>Papers ({len(papers)})</h2>
  <ol class="papers">
    {''.join(paper_items)}
  </ol>

  <h2>Top gaps</h2>
  {''.join(gap_blocks) or '<p class="muted">No gaps</p>'}

  <h2>Topic proposals</h2>
  {''.join(topic_blocks) or '<p class="muted">No topics</p>'}

  <h2>Experiment protocols</h2>
  {''.join(proto_blocks) or '<p class="muted">No protocols</p>'}

  <footer>Generated { _esc(now.strftime('%Y-%m-%d %H:%M %Z')) } · FYP Research Gap Agent</footer>
</main>
</body>
</html>
"""
