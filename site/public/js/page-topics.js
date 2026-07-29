(async function () {
  try {
    await loadBundle();
    shellReady("topics");
    const items = DATA.topics || [];
    $("#topics").innerHTML = `<div class="topics">${items
      .map(
        (t, i) => `
      <article class="topic">
        <div class="chip" style="margin-bottom:10px">Priority ${Number(t.priority || 0).toFixed(2)} · ${esc((t.domain_tags || []).join(", ") || "domain")}</div>
        <h3>${i + 1}. ${esc(t.title || "")}</h3>
        <p class="hyp"><b>Hypothesis.</b> ${esc(t.hypothesis || "")}</p>
        <div style="font-size:.8rem;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.06em;font-weight:600">Proposed experiments</div>
        <ul>${(t.proposed_experiments || []).map((e) => `<li>${esc(e)}</li>`).join("")}</ul>
        <div class="foot">
          <span class="badge blue">Readout: ${esc(t.expected_readout || "—")}</span>
          <span class="badge">${esc(t.feasibility_notes || "")}</span>
        </div>
      </article>`
      )
      .join("")}</div>`;
  } catch (e) {
    $("#topics").textContent = "Failed: " + e.message;
  }
})();
