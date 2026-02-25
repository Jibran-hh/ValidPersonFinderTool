const API_BASE = "http://127.0.0.1:8000";

const form = document.getElementById("search-form");
const statusEl = document.getElementById("status");
const bestResultEl = document.getElementById("best-result");
const candidatesEl = document.getElementById("candidates");
const jsonOutputEl = document.getElementById("json-output");
const toggleJsonBtn = document.getElementById("toggle-json");
const resetBtn = document.getElementById("reset-btn");

function setStatus(message, type = "info") {
  statusEl.textContent = message;
  statusEl.classList.remove("loading", "error");
  if (type === "loading") statusEl.classList.add("loading");
  if (type === "error") statusEl.classList.add("error");
}

function confidenceClass(score) {
  if (score >= 0.7) return "";
  if (score >= 0.4) return "low";
  return "very-low";
}

function renderBest(result, message) {
  if (!result) {
    bestResultEl.classList.add("empty-state");
    bestResultEl.innerHTML = "<p>" + (message || "No strong match was found.") + "</p>";
    return;
  }
  bestResultEl.classList.remove("empty-state");

  const pillClass = confidenceClass(result.confidence);
  const confidencePct = (result.confidence * 100).toFixed(1);
  const title = result.current_title || "Title unavailable";

  bestResultEl.innerHTML = `
    <div class="best-title">
      ${result.full_name}
      <span class="confidence-pill ${pillClass}">${confidencePct}% confidence</span>
    </div>
    <div class="best-meta">
      <div>${title}</div>
      <div>Source: <a href="${result.source_url}" target="_blank" rel="noopener noreferrer">${result.source_type}</a></div>
      <div>Search provider: ${result.search_provider}</div>
      <div style="margin-top:4px;color:#9ca3af;">${message || ""}</div>
    </div>
  `;
}

function renderCandidates(candidates) {
  candidatesEl.innerHTML = "";
  if (!candidates || !candidates.length) {
    return;
  }

  candidates.forEach((c, index) => {
    const pillClass = confidenceClass(c.confidence);
    const confidencePct = (c.confidence * 100).toFixed(1);
    const evidence = c.evidence_snippet || "";
    const el = document.createElement("article");
    el.className = "candidate-row";
    el.innerHTML = `
      <header>
        <div class="name">${index + 1}. ${c.full_name}</div>
        <span class="confidence-pill ${pillClass}">${confidencePct}%</span>
      </header>
      <div>${c.current_title || "Title unavailable"}</div>
      <div class="provider">Source: <a href="${c.source_url}" target="_blank" rel="noopener noreferrer">${c.source_type}</a> · via ${c.search_provider}</div>
      <div style="margin-top:3px;color:#9ca3af;">${evidence}</div>
    `;
    candidatesEl.appendChild(el);
  });
}

async function performSearch(company, designation) {
  setStatus("Searching across public sources…", "loading");
  bestResultEl.classList.add("empty-state");
  bestResultEl.innerHTML = "<p>Running search…</p>";
  candidatesEl.innerHTML = "";
  jsonOutputEl.textContent = "";

  try {
    const res = await fetch(API_BASE + "/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company, designation }),
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || "Request failed");
    }

    const data = await res.json();
    setStatus("Search completed.");

    renderBest(data.best_match, data.message);
    renderCandidates(data.candidates);
    jsonOutputEl.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    console.error(err);
    setStatus("Something went wrong while searching. Please try again.", "error");
    bestResultEl.classList.add("empty-state");
    bestResultEl.innerHTML = "<p>Unable to fetch results. Check if the backend is running.</p>";
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const company = form.company.value.trim();
  const designation = form.designation.value.trim();
  if (!company || !designation) {
    setStatus("Please provide both a company and a designation.", "error");
    return;
  }
  performSearch(company, designation);
});

resetBtn.addEventListener("click", () => {
  setStatus("");
  bestResultEl.classList.add("empty-state");
  bestResultEl.innerHTML = "<p>Run a search to see the most likely person for the given role.</p>";
  candidatesEl.innerHTML = "";
  jsonOutputEl.textContent = "";
});

toggleJsonBtn.addEventListener("click", () => {
  const details = document.querySelector(".raw-json");
  details.open = !details.open;
});
