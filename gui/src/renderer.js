const navItems = document.querySelectorAll(".nav-item");
const views = document.querySelectorAll(".view");
const aiContext = document.getElementById("ai-context");

let currentProject = null;

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function switchView(target) {
  navItems.forEach((n) => n.classList.toggle("active", n.dataset.view === target));
  views.forEach((v) => v.classList.toggle("active", v.id === `view-${target}`));
  aiContext.style.display = target === "scan" ? "flex" : "none";
}

navItems.forEach((item) => {
  item.addEventListener("click", () => switchView(item.dataset.view));
});

document.querySelectorAll(".action-btn[data-nav]").forEach((btn) => {
  btn.addEventListener("click", () => switchView(btn.dataset.nav));
});

// ---------- Project selection ----------

document.getElementById("project-card").addEventListener("click", async () => {
  const folder = await window.prismAPI.pickFolder();
  if (!folder) return;

  currentProject = folder;
  const name = folder.split("/").filter(Boolean).pop();

  document.getElementById("project-name").textContent = name;
  document.getElementById("project-sub").textContent = folder;
  document.getElementById("project-dot").style.background = "var(--accent)";
  document.getElementById("project-dot").style.boxShadow = "0 0 6px var(--accent)";

  document.getElementById("scan-command-text").textContent = `prism scan ${folder} --json`;
  document.getElementById("env-command-text").textContent = `prism env ${folder} --json`;
});

// ---------- Scan ----------

document.getElementById("run-scan-btn").addEventListener("click", async () => {
  if (!currentProject) {
    alert("Choose a project folder first (click the project card, bottom-left).");
    return;
  }

  const output = document.getElementById("scan-output");
  output.innerHTML = `<div class="placeholder"><h2>Scanning…</h2><p>Running prism scan, this can take a few seconds while the AI summary is generated.</p></div>`;

  const result = await window.prismAPI.scan(currentProject);

  if (!result.ok) {
    output.innerHTML = `<div class="placeholder"><h2>Scan failed</h2><p>${escapeHtml(result.error)}</p></div>`;
    return;
  }

  renderScanResult(result.data);
});

function renderScanResult(data) {
  const output = document.getElementById("scan-output");

  const languages = Object.entries(data.languages || {})
    .slice(0, 5)
    .map(([lang, n]) => `${lang} (${n})`)
    .join(", ") || "—";

  const keyFilesRows = Object.entries(data.key_files || {})
    .map(([file, role]) => `<div class="env-row"><span></span><span class="mono">${escapeHtml(file)}</span><span>${escapeHtml(role)}</span><span></span></div>`)
    .join("");

  output.innerHTML = `
    <div class="panel">
      <div class="metric-row">
        <span class="lead">Project type</span>
        <span>${escapeHtml((data.project_types || []).join(", ") || "Unknown")}</span>
        <span class="lead" style="margin-top: 8px;">Tech stack</span>
        <span>${escapeHtml((data.tech_stack || []).join(", ") || "—")}</span>
        <span class="lead" style="margin-top: 8px;">Files scanned</span>
        <span>${data.file_count}</span>
        <span class="lead" style="margin-top: 8px;">Top languages</span>
        <span>${escapeHtml(languages)}</span>
      </div>
    </div>
    <div class="panel panel-accent">
      <div class="panel-title"><span>✦</span> AI SUMMARY <span class="badge">BETA</span></div>
      <div class="summary-text">${data.ai_summary ? escapeHtml(data.ai_summary) : "No AI provider configured. Run `prism setup` in a terminal to enable AI summaries."}</div>
    </div>
    ${Object.keys(data.key_files || {}).length ? `
    <div class="panel">
      <div class="panel-title" style="color: var(--text);">KEY FILES</div>
      <div class="env-table mono">${keyFilesRows}</div>
    </div>` : ""}
  `;

  document.getElementById("scan-summary-metrics").innerHTML = `
    <span class="lead">Scan Summary</span>
    <span>${data.file_count} files analyzed</span>
    <span>Main language: ${escapeHtml((data.languages && Object.keys(data.languages)[0]) || "—")}</span>
  `;

  const keyFilesList = document.getElementById("key-files-list");
  const entries = Object.entries(data.key_files || {});
  keyFilesList.innerHTML = entries.length
    ? entries.map(([file, role]) => `<li><span class="mono">${escapeHtml(file)}</span> — ${escapeHtml(role)}</li>`).join("")
    : "<li>No recognized key files found</li>";
}

// ---------- Env ----------

document.getElementById("run-env-btn").addEventListener("click", async () => {
  if (!currentProject) {
    alert("Choose a project folder first (click the project card, bottom-left).");
    return;
  }

  const output = document.getElementById("env-output");
  output.innerHTML = `<div class="placeholder"><h2>Auditing…</h2><p>Checking installed tool versions.</p></div>`;

  const result = await window.prismAPI.env(currentProject);

  if (!result.ok) {
    output.innerHTML = `<div class="placeholder"><h2>Audit failed</h2><p>${escapeHtml(result.error)}</p></div>`;
    return;
  }

  renderEnvResult(result.data);
});

function renderEnvResult(data) {
  const output = document.getElementById("env-output");
  const rows = data.checks
    .map((c) => {
      const icon = c.found ? '<span class="env-ok">✓</span>' : c.required_by ? '<span class="severity high">✗</span>' : '<span class="env-missing">·</span>';
      const version = c.found ? c.version : "not found";
      const note = c.required_by ? "required by this project" : c.found ? "" : "not used here";
      return `<div class="env-row">${icon}<span>${escapeHtml(c.name)}</span><span>${escapeHtml(version)}</span><span>${escapeHtml(note)}</span></div>`;
    })
    .join("");

  output.innerHTML = `
    <div class="env-table mono">
      <div class="env-row head"><span></span><span>Tool</span><span>Version</span><span>Notes</span></div>
      ${rows}
    </div>
    ${!data.ai_configured ? '<div class="panel" style="margin-top: 16px;"><div class="summary-text">No AI provider configured. Run <span class="mono">prism setup</span> in a terminal to enable AI-backed commands.</div></div>' : ""}
  `;
}

// ---------- Explain ----------

const explainThread = document.getElementById("explain-thread");
const explainInput = document.getElementById("explain-input");

async function runExplain() {
  const query = explainInput.value.trim();
  if (!query) return;

  if (!currentProject) {
    alert("Choose a project folder first (click the project card, bottom-left).");
    return;
  }

  explainThread.innerHTML += `<div class="qa-bubble user">${escapeHtml(query)}</div>`;
  explainInput.value = "";
  explainThread.scrollTop = explainThread.scrollHeight;

  const fullPath = `${currentProject}/${query}`.replace(/\/{2,}/g, "/");
  const result = await window.prismAPI.explain(fullPath);

  let answer;
  if (!result.ok) {
    answer = `Error: ${result.error}`;
  } else if (result.data.error) {
    answer = result.data.error;
  } else if (result.data.kind === "file") {
    const symbolList = (result.data.symbols || []).join(", ") || "none found";
    const explanation = result.data.ai_explanation || "No AI provider configured — run 'prism setup' in a terminal.";
    answer = `${explanation}\n\nSymbols: ${symbolList}`;
  } else {
    answer = result.data.ai_explanation || "No AI provider configured — run 'prism setup' in a terminal.";
  }

  explainThread.innerHTML += `<div class="qa-bubble ai">${escapeHtml(answer)}</div>`;
  explainThread.scrollTop = explainThread.scrollHeight;
}

document.getElementById("explain-send-btn").addEventListener("click", runExplain);
explainInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runExplain();
});
