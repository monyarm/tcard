"use strict";

const state = {
  system: "",
  kind: "",
  q: "",
  filters: {},
  offset: 0,
  rows: [],
  selected: new Set(),
  card: null,
  cols: 32,
  brief: false,
  systems: [],
};

const $ = (id) => document.getElementById(id);
const escape = (text) => String(text).replace(/[&<>"']/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[c]));

async function api(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json().catch(() => ({ error: response.statusText }));
  if (!response.ok) throw new Error(payload.error || response.statusText);
  return payload;
}

function setStatus(text, bad) {
  const status = $("status");
  status.textContent = text;
  status.className = "status " + (bad ? "bad" : "ok");
}

// -- url state -----------------------------------------------------------
function readHash() {
  const params = new URLSearchParams(location.hash.slice(1));
  state.system = params.get("system") || state.system;
  state.kind = params.get("kind") || state.kind;
  state.q = params.get("q") || "";
  state.filters = {};
  for (const [key, value] of params) {
    if (["system", "kind", "q"].includes(key)) continue;
    state.filters[key] = value.split(",").filter(Boolean);
  }
}

function writeHash() {
  const params = new URLSearchParams();
  if (state.system) params.set("system", state.system);
  if (state.kind) params.set("kind", state.kind);
  if (state.q) params.set("q", state.q);
  for (const [key, values] of Object.entries(state.filters)) {
    if (values.length) params.set(key, values.join(","));
  }
  history.replaceState(null, "", "#" + params.toString());
}

// -- render --------------------------------------------------------------
function renderSystems() {
  $("systems").innerHTML = state.systems.map((system) => {
    const active = system.id === state.system ? " active" : "";
    return `<button class="${active.trim()}" data-system="${escape(system.id)}">
      ${escape(system.id)} <small>${system.kinds.length}</small></button>`;
  }).join("");
}

function currentKinds() {
  const found = state.systems.find((system) => system.id === state.system);
  return found ? found.kinds : [];
}

function renderKinds() {
  $("kinds").innerHTML = currentKinds().map((kind) => {
    const active = kind === state.kind ? " active" : "";
    return `<button class="${active.trim()}" data-kind="${escape(kind)}">${escape(kind)}</button>`;
  }).join("");
}

function renderFacets(facets) {
  const parts = [];
  for (const [key, values] of Object.entries(facets)) {
    const picked = state.filters[key] || [];
    const open = picked.length ? " open" : "";
    const items = values.map(({ value, count, label }) => {
      const checked = picked.includes(value) ? " checked" : "";
      return `<label><input type="checkbox" data-facet="${escape(key)}"
        value="${escape(value)}"${checked}>
        <span>${escape(label || value)}</span><span>${count}</span></label>`;
    }).join("");
    parts.push(`<details${open}><summary>${escape(key)} ${picked.length ? `(${picked.length})` : ""}</summary>${items}</details>`);
  }
  $("facets").innerHTML = parts.join("");
}

function chips(row) {
  return row.chips || "";
}

function renderRows() {
  $("rows").innerHTML = state.rows.map((row, index) => {
    const active = state.card && state.card.name === row.name ? " active" : "";
    const checked = state.selected.has(row.name) ? " checked" : "";
    return `<li class="${active.trim()}" data-index="${index}">
      <input type="checkbox" data-pick="${index}"${checked}>
      <span class="name">${escape(row.label)}</span>
      <span class="chips">${escape(chips(row))}</span></li>`;
  }).join("");
  $("print-selected").disabled = state.selected.size === 0;
  $("print-selected").textContent = state.selected.size
    ? `print ${state.selected.size}` : "print selected";
}

// -- data ----------------------------------------------------------------
async function loadIndex(more) {
  if (!state.system || !state.kind) return;
  setStatus("loading " + state.kind + "…");
  if (!more) {
    state.offset = 0;
    state.rows = [];
  }
  const params = new URLSearchParams({
    system: state.system, kind: state.kind, q: state.q,
    offset: String(state.offset), limit: "100",
  });
  for (const [key, values] of Object.entries(state.filters)) {
    if (values.length) params.set(key, values.join(","));
  }
  try {
    const payload = await api("/api/index?" + params);
    state.rows = more ? state.rows.concat(payload.rows) : payload.rows;
    state.offset = payload.offset + payload.rows.length;
    $("count").textContent = `${payload.total} of ${payload.count}`;
    $("more").hidden = state.offset >= payload.total;
    renderFacets(payload.facets);
    renderRows();
    setStatus(state.rows.length ? "" : "no matches");
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function preview(row) {
  state.card = row;
  renderRows();
  $("preview-name").textContent = row.label;
  $("card").textContent = "…";
  $("print").disabled = true;
  const params = new URLSearchParams({
    system: state.system, kind: state.kind, name: row.name,
    cols: String(state.cols), brief: state.brief ? "1" : "0",
  });
  if (row.source) params.set("source", row.source);
  try {
    const payload = await api("/api/card?" + params);
    state.card.text = payload.text;
    $("card").textContent = payload.text;
    $("preview-size").textContent = `${payload.lines} lines`;
    $("preview").classList.toggle("too-wide", payload.text.split("\n").some((line) => line.length > state.cols));
    $("print").disabled = false;
    setStatus("ready");
  } catch (error) {
    $("card").textContent = error.message;
    $("preview-size").textContent = "";
    setStatus(error.message, true);
  }
}

function cardParams(row) {
  const params = {
    system: state.system, kind: state.kind, name: row.name,
    cols: state.cols, brief: state.brief,
  };
  if (row.source) params.source = row.source;
  return params;
}

async function printRows(rows) {
  for (const row of rows) {
    $("preview-name").textContent = row.label;
    setStatus("printing " + row.name + "…");
    try {
      const payload = await api("/api/print", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cardParams(row)),
      });
      $("card").textContent = payload.text;
      $("preview-size").textContent = `${payload.lines} lines`;
      setStatus(payload.dry_run ? "dry run (nothing sent)" : "printed " + row.name);
    } catch (error) {
      setStatus(error.message, true);
      return;
    }
  }
}

// -- wiring --------------------------------------------------------------
function selectSystem(id) {
  state.system = id;
  const kinds = currentKinds();
  state.kind = kinds.includes(state.kind) ? state.kind : kinds[0] || "";
  state.filters = {};
  state.selected.clear();
  state.card = null;
  $("card").textContent = "";
  $("preview-name").textContent = "pick a card";
  $("print").disabled = true;
  renderSystems();
  renderKinds();
  writeHash();
  loadIndex();
}

function toggleFacet(key, value, on) {
  const values = new Set(state.filters[key] || []);
  if (on) values.add(value); else values.delete(value);
  state.filters[key] = [...values];
  if (!state.filters[key].length) delete state.filters[key];
  writeHash();
  loadIndex();
}

document.addEventListener("click", (event) => {
  const system = event.target.closest("[data-system]");
  if (system) { selectSystem(system.dataset.system); return; }

  const kind = event.target.closest("[data-kind]");
  if (kind) {
    state.kind = kind.dataset.kind;
    state.filters = {};
    state.selected.clear();
    renderKinds();
    writeHash();
    loadIndex();
    return;
  }

  const pick = event.target.closest("[data-pick]");
  if (pick) {
    event.stopPropagation();
    const row = state.rows[Number(pick.dataset.pick)];
    if (state.selected.has(row.name)) state.selected.delete(row.name);
    else state.selected.add(row.name);
    renderRows();
    return;
  }

  const row = event.target.closest("li[data-index]");
  if (row) { preview(state.rows[Number(row.dataset.index)]); }
});

document.addEventListener("change", (event) => {
  const facet = event.target.closest("[data-facet]");
  if (facet) toggleFacet(facet.dataset.facet, facet.value, facet.checked);
});

$("search").addEventListener("input", (event) => {
  state.q = event.target.value.trim();
  writeHash();
  clearTimeout(state.timer);
  state.timer = setTimeout(() => loadIndex(), 180);
});

$("cols").addEventListener("change", (event) => {
  state.cols = Math.min(200, Math.max(8, Number(event.target.value) || 32));
  event.target.value = state.cols;
  if (state.card) preview(state.card);
});

$("brief").addEventListener("change", (event) => {
  state.brief = event.target.checked;
  if (state.card) preview(state.card);
});

$("clear").addEventListener("click", () => {
  state.q = "";
  state.filters = {};
  $("search").value = "";
  writeHash();
  loadIndex();
});

$("more").addEventListener("click", () => loadIndex(true));

$("print").addEventListener("click", () => {
  if (state.card) printRows([state.card]);
});

$("print-selected").addEventListener("click", () => {
  const rows = state.rows.filter((row) => state.selected.has(row.name));
  printRows(rows);
});

$("refresh").addEventListener("click", async () => {
  const params = new URLSearchParams({ system: state.system, kind: state.kind, refresh: "1" });
  try {
    await api("/api/index?" + params);
    await loadIndex();
    setStatus("reloaded " + state.kind);
  } catch (error) {
    setStatus(error.message, true);
  }
});

// Back/forward and pasted links change only the hash; refetch to match.
window.addEventListener("hashchange", () => {
  const before = JSON.stringify([state.system, state.kind, state.q, state.filters]);
  readHash();
  if (!state.system) state.system = state.systems[0]?.id || "";
  if (!state.kind) state.kind = currentKinds()[0] || "";
  $("search").value = state.q;
  const after = JSON.stringify([state.system, state.kind, state.q, state.filters]);
  renderSystems();
  renderKinds();
  if (before !== after) loadIndex();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "/" && document.activeElement !== $("search")) {
    event.preventDefault();
    $("search").focus();
  }
});

async function boot() {
  try {
    const health = await api("/api/health");
    state.cols = health.cols || 32;
    $("cols").value = state.cols;
    setStatus(health.tp ? "" : "no tp on PATH", !health.tp);
    if (health.view_only) {
      $("print").disabled = true;
      $("print-selected").disabled = true;
    }
  } catch (error) {
    setStatus(error.message, true);
  }
  try {
    const payload = await api("/api/systems");
    state.systems = payload.systems;
  } catch (error) {
    setStatus(error.message, true);
    return;
  }
  readHash();
  if (!state.system) state.system = state.systems[0].id;
  if (!state.kind) state.kind = currentKinds()[0] || "";
  renderSystems();
  renderKinds();
  $("search").value = state.q;
  writeHash();
  loadIndex();
}

boot();
