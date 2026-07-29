const diagState = { name: "pipeline", scale: 1 };

async function renderMermaid(name) {
  const src = (DATA.diagrams && DATA.diagrams[name]) || "flowchart TB\nA[Missing diagram]";
  diagState.name = name;
  $$(".diag-tabs button").forEach((b) => b.classList.toggle("active", b.dataset.diag === name));
  const el = $("#diag-mermaid");
  if (!el) return;
  if (!window.mermaid) {
    el.textContent = "Loading diagram engine…";
    return;
  }
  el.removeAttribute("data-processed");
  el.className = "mermaid";
  el.textContent = src;
  try {
    await mermaid.run({ nodes: [el] });
  } catch (e) {
    el.textContent = "Diagram error: " + (e.message || e);
  }
  diagState.scale = 1;
  applyDiagTransform();
  setTimeout(fitDiagram, 80);
}

function applyDiagTransform() {
  const canvas = $("#diag-canvas");
  const label = $("#zoom-label");
  if (!canvas) return;
  canvas.style.transform = "scale(" + diagState.scale + ")";
  canvas.style.transformOrigin = "top center";
  if (label) label.textContent = Math.round(diagState.scale * 100) + "%";
}

function fitDiagram() {
  const vp = $("#diag-viewport");
  const canvas = $("#diag-canvas");
  if (!vp || !canvas) return;
  const svg = canvas.querySelector("svg");
  if (!svg) return;
  let sw = 800,
    sh = 600;
  try {
    if (svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width) {
      sw = svg.viewBox.baseVal.width;
      sh = svg.viewBox.baseVal.height;
    } else {
      const bb = svg.getBBox();
      sw = bb.width || sw;
      sh = bb.height || sh;
    }
  } catch (_) {}
  const pad = 48;
  const sx = (vp.clientWidth - pad) / Math.max(sw, 1);
  const sy = (vp.clientHeight - pad) / Math.max(sh, 1);
  diagState.scale = Math.min(1.35, Math.max(0.4, Math.min(sx, sy)));
  applyDiagTransform();
}

function wireDiagrams() {
  if (window.mermaid) {
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "base",
      themeVariables: {
        primaryColor: "#efe8df",
        primaryTextColor: "#141413",
        primaryBorderColor: "#c4c2b8",
        lineColor: "#5c5b57",
        secondaryColor: "#e8eef5",
        tertiaryColor: "#faf9f5",
        background: "#faf9f5",
        mainBkg: "#faf9f5",
        nodeBorder: "#c4c2b8",
        clusterBkg: "#f7f6f1",
        titleColor: "#141413",
        edgeLabelBackground: "#faf9f5",
        fontFamily: "Inter, system-ui, sans-serif",
        fontSize: "15px",
      },
      flowchart: { curve: "basis", padding: 18, htmlLabels: true, nodeSpacing: 28, rankSpacing: 42 },
    });
  }
  $$(".diag-tabs button").forEach((b) => {
    b.onclick = () => renderMermaid(b.dataset.diag);
  });
  const zin = $("#zoom-in"),
    zout = $("#zoom-out"),
    zre = $("#zoom-reset"),
    zfit = $("#zoom-fit");
  if (zin)
    zin.onclick = () => {
      diagState.scale = Math.min(2.8, diagState.scale * 1.18);
      applyDiagTransform();
    };
  if (zout)
    zout.onclick = () => {
      diagState.scale = Math.max(0.35, diagState.scale / 1.18);
      applyDiagTransform();
    };
  if (zre)
    zre.onclick = () => {
      diagState.scale = 1;
      applyDiagTransform();
    };
  if (zfit) zfit.onclick = () => fitDiagram();
  const vp = $("#diag-viewport");
  if (vp) {
    let dragging = false,
      lx = 0,
      ly = 0;
    vp.addEventListener("pointerdown", (e) => {
      if (e.target.closest("button")) return;
      dragging = true;
      lx = e.clientX;
      ly = e.clientY;
      try {
        vp.setPointerCapture(e.pointerId);
      } catch (_) {}
    });
    vp.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      vp.scrollLeft -= e.clientX - lx;
      vp.scrollTop -= e.clientY - ly;
      lx = e.clientX;
      ly = e.clientY;
    });
    const end = () => {
      dragging = false;
    };
    vp.addEventListener("pointerup", end);
    vp.addEventListener("pointercancel", end);
    vp.addEventListener(
      "wheel",
      (e) => {
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          const f = e.deltaY > 0 ? 1 / 1.08 : 1.08;
          diagState.scale = Math.min(2.8, Math.max(0.35, diagState.scale * f));
          applyDiagTransform();
        }
      },
      { passive: false }
    );
  }
  renderMermaid("pipeline");
}

(async function () {
  try {
    await loadBundle();
    shellReady("method");
    wireDiagrams();
  } catch (e) {
    const el = $("#diag-mermaid");
    if (el) el.textContent = "Failed: " + e.message;
  }
})();
