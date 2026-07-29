function pageShell(active, title, bodyHtml, extraHead = "") {
  const nav = (id, href, label, svg) =>
    `<a href="${href}" class="${active === id ? "active" : ""}">${svg}<span>${label}</span></a>`;
  const homeSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 10.5L12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-9.5z"/></svg>`;
  const timeSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>`;
  // timeline is on overview; bottom: Home Results Topics Method Docs
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<meta name="robots" content="noindex,nofollow"/>
<meta name="theme-color" content="#141413"/>
<title>${title} · Research Gap Agent</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,500;0,600;1,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="/css/board.css"/>
${extraHead}
</head>
<body>
<div class="app">
  <header class="topbar">
    <div class="brand">
      <strong>Research Gap Agent</strong>
      <span id="top-sub">Loading…</span>
    </div>
    <nav class="top-links">
      <a href="/" class="${active === "index" ? "active" : ""}">Overview</a>
      <a href="/results.html" class="${active === "results" ? "active" : ""}">Results</a>
      <a href="/topics.html" class="${active === "topics" ? "active" : ""}">Topics</a>
      <a href="/method.html" class="${active === "method" ? "active" : ""}">Method</a>
      <a href="/docs.html" class="${active === "docs" ? "active" : ""}">Docs</a>
    </nav>
    <a class="icon-btn" href="/logout">Lock</a>
  </header>
  ${bodyHtml}
  <nav class="bottom-nav" aria-label="Primary">
    <a href="/" class="${active === "index" ? "active" : ""}">${homeSvg}Home</a>
    <a href="/results.html" class="${active === "results" ? "active" : ""}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 19V5M4 19h16M8 16V9m4 7V7m4 9v-5"/></svg>Results</a>
    <a href="/topics.html" class="${active === "topics" ? "active" : ""}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l2.2 6.6H21l-5.4 4 2.1 6.4L12 16.5 6.3 20l2.1-6.4L3 9.6h6.8L12 3z"/></svg>Topics</a>
    <a href="/method.html" class="${active === "method" ? "active" : ""}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 9h8M8 12h8M8 15h5"/></svg>Method</a>
    <a href="/docs.html" class="${active === "docs" ? "active" : ""}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3zm0 6c0 1.7 3.6 3 8 3s8-1.3 8-3M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/></svg>Docs</a>
  </nav>
</div>
<script src="/js/common.js"></script>
`;
}

// We'll write HTML files as static content with their own scripts — not using this helper at runtime.
console.log('helper only');
