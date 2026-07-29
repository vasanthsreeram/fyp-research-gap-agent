(async function () {
  try {
    await loadBundle();
    shellReady("index");
    const m = DATA.meta,
      c = m.counts;
    $("#meta-row").innerHTML = `
      <span class="chip"><b>Author</b> ${esc(m.student)}</span>
      <span class="chip"><b>Supervisor</b> ${esc(m.supervisor)}</span>
      <span class="chip"><b>Domain</b> ${esc(m.domain)}</span>
      <span class="chip"><b>Model</b> ${esc(m.model_default)} · ${esc(m.extractor_mode)}</span>`;
    $("#stats").innerHTML = `
      <div class="stat"><b>${c.papers}</b><span>Papers</span></div>
      <div class="stat"><b>${c.claims}</b><span>Claims</span></div>
      <div class="stat"><b>${c.evidence}</b><span>Evidence</span></div>
      <div class="stat"><b>${c.gaps}</b><span>Gaps</span></div>
      <div class="stat"><b>${c.topics}</b><span>Topics</span></div>
      <div class="stat"><b>${c.tests_passed}/23</b><span>Tests</span></div>`;
    $("#timeline").innerHTML = renderTimeline(DATA.timeline);
    $("#checklist").innerHTML =
      (DATA.checklist.done || [])
        .map((x) => `<div class="check done"><div class="dot">✓</div><span>${esc(x)}</span></div>`)
        .join("") +
      (DATA.checklist.todo || [])
        .map((x) => `<div class="check todo"><div class="dot">·</div><span>${esc(x)}</span></div>`)
        .join("");
  } catch (e) {
    $("#timeline").textContent = "Failed to load: " + e.message;
  }
})();
