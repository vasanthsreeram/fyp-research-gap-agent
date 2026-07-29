/* Shared helpers for multi-page board */
window.$ = (s, el = document) => el.querySelector(s);
window.$$ = (s, el = document) => [...el.querySelectorAll(s)];
window.DATA = null;

window.esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

window.pct = (n) => Math.round((n || 0) * 100);

window.debounce = (fn, ms) => {
  let t;
  return (...a) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...a), ms);
  };
};

window.barChart = (obj, color = "orange") => {
  const entries = Object.entries(obj || {}).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map((e) => e[1]));
  const cls = color === "blue" ? "blue" : color === "green" ? "green" : "";
  return `<div class="bars">${entries
    .map(
      ([k, v]) => `
    <div class="bar-row">
      <div class="bar-label" title="${esc(k)}">${esc(String(k).replaceAll("_", " "))}</div>
      <div class="bar-track"><div class="bar-fill ${cls}" style="width:${(v / max) * 100}%"></div></div>
      <div class="bar-n">${v}</div>
    </div>`
    )
    .join("")}</div>`;
};

window.funnel = (f) => {
  const order = [
    ["papers", "Papers"],
    ["claims", "Claims"],
    ["evidence", "Evidence"],
    ["gaps", "Gaps"],
    ["topics", "Topics"],
  ];
  const max = Math.max(1, ...order.map(([k]) => f[k] || 0));
  return `<div class="funnel">${order
    .map(([k, lab], i) => {
      const v = f[k] || 0;
      const h = Math.max(12, (v / max) * 100);
      const op = (0.45 + i * 0.12).toFixed(2);
      return `<div class="f"><div class="fv">${v}</div><div class="col" style="height:${h}%;opacity:${op}"></div><div class="fl">${lab}</div></div>`;
    })
    .join("")}</div>`;
};

window.sortRows = (rows, key, dir) =>
  [...rows].sort((a, b) => {
    let av = a[key],
      bv = b[key];
    if (typeof av === "string") av = av.toLowerCase();
    if (typeof bv === "string") bv = bv.toLowerCase();
    if (av == null) av = "";
    if (bv == null) bv = "";
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });

window.paginate = (rows, page, pageSize = 8) => {
  const start = page * pageSize;
  return {
    slice: rows.slice(start, start + pageSize),
    total: rows.length,
    pages: Math.max(1, Math.ceil(rows.length / pageSize)),
  };
};

window.renderTimeline = (items) => {
  if (!items?.length) return '<p class="empty">Timeline coming soon.</p>';
  return `<div class="tl">${items
    .map(
      (it) => `
    <div class="tl-item ${esc(it.status || "")}">
      <div class="tl-date">${esc(it.date || "")}</div>
      <div class="tl-rail"><div class="tl-dot"></div></div>
      <div class="tl-card">
        <div class="lab">${esc(it.label || it.status || "")}</div>
        <h3>${esc(it.title || "")}</h3>
        <p>${esc(it.body || "")}</p>
        ${
          it.metrics
            ? `<div class="tl-metrics">${Object.entries(it.metrics)
                .map(
                  ([k, v]) =>
                    `<span class="badge">${esc(k)} <b style="color:var(--ink)">${esc(v)}</b></span>`
                )
                .join("")}</div>`
            : ""
        }
      </div>
    </div>`
    )
    .join("")}</div>`;
};

window.setTopSub = () => {
  const m = DATA?.meta;
  if (!m) return;
  const el = $("#top-sub");
  if (el) el.textContent = `${m.stage} · ${m.counts.papers} papers · updated ${m.updated}`;
};

window.markActiveNav = (page) => {
  $$(".top-links a, .bottom-nav a").forEach((a) => {
    const href = a.getAttribute("href") || "";
    const file = href.split("/").pop() || "index.html";
    const key = file.replace(".html", "") || "index";
    a.classList.toggle("active", key === page || (page === "index" && (key === "" || key === "index")));
  });
};

window.loadBundle = async () => {
  const r = await fetch("/data/bundle.json", { cache: "no-store" });
  if (!r.ok) throw new Error("bundle " + r.status);
  DATA = await r.json();
  setTopSub();
  return DATA;
};

window.shellReady = (page) => {
  markActiveNav(page);
};
