const API = ""; // same origin

const els = {
  modePre: document.getElementById("mode-pre"),
  modeMd: document.getElementById("mode-md"),
  panelPre: document.getElementById("panel-pre"),
  panelMd: document.getElementById("panel-md"),
  formPre: document.getElementById("form-pre"),
  formMd: document.getElementById("form-md"),
  result: document.getElementById("result"),
  team1Pre: document.getElementById("team1-pre"),
  team2Pre: document.getElementById("team2-pre"),
  venuePre: document.getElementById("venue-pre"),
  datePre: document.getElementById("date-pre"),
  team1Md: document.getElementById("team1-md"),
  team2Md: document.getElementById("team2-md"),
  venueMd: document.getElementById("venue-md"),
  dateMd: document.getElementById("date-md"),
  tossWinner: document.getElementById("toss-winner"),
  tossDecision: document.getElementById("toss-decision"),
};

function setMode(mode) {
  const pre = mode === "pre";
  els.modePre.classList.toggle("active", pre);
  els.modeMd.classList.toggle("active", !pre);
  els.panelPre.classList.toggle("active", pre);
  els.panelMd.classList.toggle("active", !pre);
  els.result.classList.remove("show");
}

els.modePre.addEventListener("click", () => setMode("pre"));
els.modeMd.addEventListener("click", () => setMode("md"));

function showResult(data, isError) {
  els.result.classList.add("show");
  els.result.classList.toggle("err", isError);
  els.result.classList.toggle("ok", !isError);
  els.result.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

async function loadMeta() {
  try {
    const [teamsRes, venuesRes] = await Promise.all([
      fetch(`${API}/api/meta/teams`),
      fetch(`${API}/api/meta/venues`),
    ]);
    if (!teamsRes.ok || !venuesRes.ok) return;
    const teams = (await teamsRes.json()).teams || [];
    const venues = (await venuesRes.json()).venues || [];
    fillDatalist("teams-list", teams);
    fillDatalist("venues-list", venues);
  } catch (_) {
    /* offline / no models */
  }
}

function fillDatalist(id, items) {
  const dl = document.getElementById(id);
  if (!dl) return;
  dl.innerHTML = items.map((t) => `<option value="${escapeAttr(t)}">`).join("");
}

function escapeAttr(s) {
  return String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
}

async function predict(endpoint, body) {
  const res = await fetch(`${API}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || res.statusText || "Request failed");
  }
  return data;
}

els.formPre.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const out = await predict("/api/predict/pre", {
      team1: els.team1Pre.value,
      team2: els.team2Pre.value,
      venue: els.venuePre.value,
      date: els.datePre.value,
    });
    showResult(formatPrediction(out), false);
  } catch (err) {
    showResult(err.message, true);
  }
});

els.formMd.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const out = await predict("/api/predict/matchday", {
      team1: els.team1Md.value,
      team2: els.team2Md.value,
      venue: els.venueMd.value,
      date: els.dateMd.value,
      toss_winner: els.tossWinner.value,
      toss_decision: els.tossDecision.value,
    });
    showResult(formatPrediction(out), false);
  } catch (err) {
    showResult(err.message, true);
  }
});

function formatPrediction(o) {
  const p1 = (o.p_team1_win * 100).toFixed(1);
  const p2 = (o.p_team2_win * 100).toFixed(1);
  return [
    `Predicted winner: ${o.predicted_winner}`,
    ``,
    `${o.team1}: ${p1}%`,
    `${o.team2}: ${p2}%`,
    o.data_through_season ? `\n(model trained through season ${o.data_through_season})` : "",
  ].join("\n");
}

loadMeta();
setMode("pre");

// default date = today
const today = new Date().toISOString().slice(0, 10);
if (els.datePre) els.datePre.value = today;
if (els.dateMd) els.dateMd.value = today;
