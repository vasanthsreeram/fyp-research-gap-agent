const state = {
  gaps: { q: "", kind: "", sort: "overall", dir: -1, page: 0 },
  claims: { q: "", type: "", sort: "confidence", dir: -1, page: 0 },
  papers: { q: "", sort: "year", dir: -1, page: 0 },
  pageSize: 8,
};

function renderGaps() {
  const st = state.gaps;
  let rows = DATA.gaps || [];
  if (st.kind) rows = rows.filter((g) => g.kind === st.kind);
  if (st.q) {
    const q = st.q.toLowerCase();
    rows = rows.filter((g) => ((g.title || "") + (g.description || "") + (g.kind || "")).toLowerCase().includes(q));
  }
  rows = sortRows(rows, st.sort, st.dir);
  const { slice, total, pages } = paginate(rows, st.page, state.pageSize);
  const kinds = [...new Set((DATA.gaps || []).map((g) => g.kind).filter(Boolean))].sort();
  return `
  <div class="toolbar">
    <input class="search" id="gap-q" placeholder="Search gaps…" value="${esc(st.q)}"/>
    <select class="select" id="gap-kind">
      <option value="">All kinds</option>
      ${kinds.map((k) => `<option value="${esc(k)}" ${k === st.kind ? "selected" : ""}>${esc(k.replaceAll("_", " "))}</option>`).join("")}
    </select>
  </div>
  <div class="table-wrap"><table>
    <thead><tr>
      <th data-sort="overall">Score</th><th data-sort="kind">Kind</th><th data-sort="title">Gap</th>
      <th data-sort="novelty">Nov</th><th data-sort="testability">Test</th><th data-sort="impact">Imp</th>
    </tr></thead>
    <tbody>
      ${
        slice
          .map(
            (g) => `<tr>
        <td class="num"><b>${Number(g.overall || 0).toFixed(2)}</b></td>
        <td><span class="badge orange">${esc((g.kind || "").replaceAll("_", " "))}</span></td>
        <td><div class="clamp"><b>${esc(g.title || "")}</b><br/><span style="color:var(--muted)">${esc(g.description || "")}</span></div></td>
        <td class="num">${pct(g.novelty)}</td>
        <td class="num">${pct(g.testability)}</td>
        <td class="num">${pct(g.impact)}</td>
      </tr>`
          )
          .join("") || '<tr><td colspan="6" class="empty">No gaps match.</td></tr>'
      }
    </tbody>
  </table></div>
  <div class="pager"><span>${total} gaps · page ${st.page + 1}/${pages}</span>
    <div class="btns">
      <button id="gap-prev" ${st.page <= 0 ? "disabled" : ""}>Prev</button>
      <button id="gap-next" ${st.page >= pages - 1 ? "disabled" : ""}>Next</button>
    </div>
  </div>`;
}

function renderClaims() {
  const st = state.claims;
  let rows = DATA.claims || [];
  if (st.type) rows = rows.filter((c) => c.claim_type === st.type);
  if (st.q) {
    const q = st.q.toLowerCase();
    rows = rows.filter((c) => ((c.text || "") + (c.paper_title || "") + (c.claim_type || "")).toLowerCase().includes(q));
  }
  rows = sortRows(rows, st.sort, st.dir);
  const { slice, total, pages } = paginate(rows, st.page, state.pageSize);
  const types = [...new Set((DATA.claims || []).map((c) => c.claim_type).filter(Boolean))].sort();
  return `
  <div class="toolbar">
    <input class="search" id="claim-q" placeholder="Search claims…" value="${esc(st.q)}"/>
    <select class="select" id="claim-type">
      <option value="">All types</option>
      ${types.map((t) => `<option value="${esc(t)}" ${t === st.type ? "selected" : ""}>${esc(t)}</option>`).join("")}
    </select>
  </div>
  <div class="table-wrap"><table>
    <thead><tr>
      <th data-sort="confidence">Conf</th><th data-sort="claim_type">Type</th>
      <th data-sort="text">Claim</th><th data-sort="extractor">Src</th>
    </tr></thead>
    <tbody>
      ${
        slice
          .map(
            (c) => `<tr>
        <td class="num">${pct(c.confidence)}%</td>
        <td><span class="badge blue">${esc(c.claim_type || "")}</span></td>
        <td><div class="clamp">${esc(c.text || "")}<br/><span style="color:var(--muted);font-size:.78rem">${esc(c.paper_title || "")}</span></div></td>
        <td><span class="badge">${esc(c.extractor || "")}</span></td>
      </tr>`
          )
          .join("") || '<tr><td colspan="4" class="empty">No claims match.</td></tr>'
      }
    </tbody>
  </table></div>
  <div class="pager"><span>${total} claims · page ${st.page + 1}/${pages}</span>
    <div class="btns">
      <button id="claim-prev" ${st.page <= 0 ? "disabled" : ""}>Prev</button>
      <button id="claim-next" ${st.page >= pages - 1 ? "disabled" : ""}>Next</button>
    </div>
  </div>`;
}

function renderPapers() {
  const st = state.papers;
  let rows = DATA.papers || [];
  if (st.q) {
    const q = st.q.toLowerCase();
    rows = rows.filter((p) => ((p.title || "") + (p.venue || "") + (p.authors || []).join(" ")).toLowerCase().includes(q));
  }
  rows = sortRows(rows, st.sort, st.dir);
  const { slice, total, pages } = paginate(rows, st.page, state.pageSize);
  return `
  <div class="toolbar">
    <input class="search" id="paper-q" placeholder="Search papers…" value="${esc(st.q)}"/>
  </div>
  <div class="table-wrap"><table>
    <thead><tr><th data-sort="year">Year</th><th data-sort="title">Title</th><th data-sort="source">Source</th></tr></thead>
    <tbody>
      ${slice
        .map(
          (p) => `<tr>
        <td class="num">${esc(p.year ?? "—")}</td>
        <td><div class="clamp"><b>${esc(p.title || "")}</b><br/><span style="color:var(--muted);font-size:.78rem">${esc((p.authors || []).slice(0, 4).join(", "))}${(p.authors || []).length > 4 ? " et al." : ""}</span></div></td>
        <td><span class="badge">${esc(p.source || "")}</span></td>
      </tr>`
        )
        .join("")}
    </tbody>
  </table></div>
  <div class="pager"><span>${total} papers · page ${st.page + 1}/${pages}</span>
    <div class="btns">
      <button id="paper-prev" ${st.page <= 0 ? "disabled" : ""}>Prev</button>
      <button id="paper-next" ${st.page >= pages - 1 ? "disabled" : ""}>Next</button>
    </div>
  </div>`;
}

function bindSort(panel, key, refresh) {
  $$(panel + " th[data-sort]").forEach((th) => {
    th.onclick = () => {
      const k = th.dataset.sort;
      if (state[key].sort === k) state[key].dir *= -1;
      else {
        state[key].sort = k;
        state[key].dir = -1;
      }
      state[key].page = 0;
      refresh();
    };
  });
}

function refreshGaps() {
  $("#gaps-panel").innerHTML = renderGaps();
  bindSort("#gaps-panel", "gaps", refreshGaps);
  $("#gap-q").oninput = debounce((e) => {
    state.gaps.q = e.target.value;
    state.gaps.page = 0;
    const v = e.target.value;
    refreshGaps();
    const el = $("#gap-q");
    if (el) {
      el.value = v;
      el.focus();
      el.setSelectionRange(v.length, v.length);
    }
  }, 180);
  $("#gap-kind").onchange = (e) => {
    state.gaps.kind = e.target.value;
    state.gaps.page = 0;
    refreshGaps();
  };
  $("#gap-prev").onclick = () => {
    state.gaps.page--;
    refreshGaps();
  };
  $("#gap-next").onclick = () => {
    state.gaps.page++;
    refreshGaps();
  };
}
function refreshClaims() {
  $("#claims-panel").innerHTML = renderClaims();
  bindSort("#claims-panel", "claims", refreshClaims);
  $("#claim-q").oninput = debounce((e) => {
    state.claims.q = e.target.value;
    state.claims.page = 0;
    const v = e.target.value;
    refreshClaims();
    const el = $("#claim-q");
    if (el) {
      el.value = v;
      el.focus();
      el.setSelectionRange(v.length, v.length);
    }
  }, 180);
  $("#claim-type").onchange = (e) => {
    state.claims.type = e.target.value;
    state.claims.page = 0;
    refreshClaims();
  };
  $("#claim-prev").onclick = () => {
    state.claims.page--;
    refreshClaims();
  };
  $("#claim-next").onclick = () => {
    state.claims.page++;
    refreshClaims();
  };
}
function refreshPapers() {
  $("#papers-panel").innerHTML = renderPapers();
  bindSort("#papers-panel", "papers", refreshPapers);
  $("#paper-q").oninput = debounce((e) => {
    state.papers.q = e.target.value;
    state.papers.page = 0;
    const v = e.target.value;
    refreshPapers();
    const el = $("#paper-q");
    if (el) {
      el.value = v;
      el.focus();
      el.setSelectionRange(v.length, v.length);
    }
  }, 180);
  $("#paper-prev").onclick = () => {
    state.papers.page--;
    refreshPapers();
  };
  $("#paper-next").onclick = () => {
    state.papers.page++;
    refreshPapers();
  };
}

(async function () {
  try {
    await loadBundle();
    shellReady("results");
    const ch = DATA.charts;
    $("#run-label").textContent = "Latest run " + (DATA.meta.run_id || "");
    $("#charts").innerHTML = `
      <div class="card"><div class="chart-title">Pipeline funnel</div>${funnel(ch.pipeline_funnel)}</div>
      <div class="card"><div class="chart-title">Gap score distribution</div>${barChart(ch.gap_score_bins, "green")}</div>
      <div class="card"><div class="chart-title">Gap kinds</div>${barChart(ch.gap_kinds, "orange")}</div>
      <div class="card"><div class="chart-title">Claim types</div>${barChart(ch.claim_types, "blue")}</div>`;
    refreshGaps();
    refreshClaims();
    refreshPapers();
  } catch (e) {
    $("#charts").textContent = "Failed: " + e.message;
  }
})();
