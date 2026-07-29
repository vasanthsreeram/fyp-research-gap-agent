(async function () {
  try {
    await loadBundle();
    shellReady("docs");
    if (DATA.meta?.repo) {
      const a = $("#repo-link");
      if (a) a.href = DATA.meta.repo;
    }
    const load = async (id, path) => {
      try {
        const r = await fetch(path, { cache: "no-store" });
        $(id).textContent = await r.text();
      } catch (e) {
        $(id).textContent = "Failed to load " + path;
      }
    };
    await Promise.all([
      load("#doc-status", "/data/STATUS.md"),
      load("#doc-draft", "/data/supervisor-update-draft.md"),
      load("#doc-run", "/data/latest_run.md"),
    ]);
  } catch (e) {
    $("#doc-status").textContent = "Failed: " + e.message;
  }
})();
