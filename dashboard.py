import json
import os
from flask import Flask, jsonify
from pathlib import Path

app = Flask(__name__)
WAGON_DIR = Path("wagon_logs")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MIMIC — CIVI Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #f5f5f7;
    color: #1a1a2e;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 13px;
    min-height: 100vh;
  }

  /* ── Header ── */
  header {
    background: #ffffff;
    border-bottom: 1px solid #e4e4ec;
    padding: 0 28px;
    height: 56px;
    display: flex;
    align-items: center;
    gap: 0;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
  }

  .logo-mark {
    width: 30px;
    height: 30px;
    flex-shrink: 0;
  }

  .logo-text {
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 0.18em;
    color: #1a1a2e;
    line-height: 1;
  }

  .logo-text span {
    color: #6d28d9;
  }

  .header-divider {
    width: 1px;
    height: 20px;
    background: #e4e4ec;
    margin: 0 18px;
  }

  .header-product {
    font-size: 13px;
    font-weight: 600;
    color: #6d28d9;
    letter-spacing: 0.06em;
  }

  .header-sub {
    font-size: 11px;
    color: #aaa;
    margin-left: 8px;
  }

  .header-right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: #bbb;
  }

  .live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* ── Layout ── */
  .layout {
    display: grid;
    grid-template-columns: 272px 1fr;
    height: calc(100vh - 56px);
  }

  /* ── Sidebar ── */
  .sidebar {
    background: #ffffff;
    border-right: 1px solid #e4e4ec;
    overflow-y: auto;
    padding: 16px 0;
  }

  .sidebar-label {
    padding: 0 18px 10px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #bbb;
    text-transform: uppercase;
  }

  .run-item {
    padding: 11px 18px;
    cursor: pointer;
    border-left: 3px solid transparent;
    transition: background 0.12s;
  }

  .run-item:hover { background: #f8f8fc; }

  .run-item.active {
    background: #f3f0ff;
    border-left-color: #6d28d9;
  }

  .run-item .run-id {
    font-size: 11px;
    font-weight: 700;
    color: #6d28d9;
    letter-spacing: 0.08em;
    margin-bottom: 3px;
  }

  .run-item .run-task {
    color: #888;
    font-size: 11px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 218px;
    margin-bottom: 6px;
  }

  .run-item .run-mode {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    letter-spacing: 0.04em;
  }

  .mode-PRIME    { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
  .mode-FRAGMENT { background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }
  .mode-unknown  { background: #f9fafb; color: #9ca3af; border: 1px solid #e5e7eb; }

  /* ── Main ── */
  .main {
    overflow-y: auto;
    padding: 32px 36px;
    background: #f5f5f7;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #ccc;
    gap: 10px;
  }

  .empty-state .big { font-size: 20px; color: #bbb; font-weight: 600; }
  .empty-state code { background: #efefef; padding: 2px 8px; border-radius: 4px; font-size: 12px; color: #888; }

  /* ── Run header ── */
  .run-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
  }

  .run-header h2 {
    font-size: 18px;
    font-weight: 700;
    color: #1a1a2e;
    letter-spacing: 0.04em;
  }

  .run-header .ts {
    margin-left: auto;
    font-size: 11px;
    color: #bbb;
  }

  /* ── Section titles ── */
  .section-title {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #bbb;
    text-transform: uppercase;
    margin-bottom: 10px;
    margin-top: 28px;
  }

  /* ── Stat cards ── */
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
    margin-bottom: 4px;
  }

  .card {
    background: #ffffff;
    border: 1px solid #e4e4ec;
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .card .label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #bbb;
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .card .value {
    font-size: 24px;
    font-weight: 700;
    color: #1a1a2e;
  }

  .card .unit {
    font-size: 12px;
    color: #bbb;
    margin-left: 2px;
    font-weight: 400;
  }

  .card.highlight { border-color: #ddd6fe; background: #faf8ff; }
  .card.highlight .value { color: #6d28d9; }

  /* ── Task block ── */
  .task-block {
    background: #ffffff;
    border: 1px solid #e4e4ec;
    border-radius: 10px;
    padding: 16px 20px;
    color: #444;
    line-height: 1.7;
    font-size: 13px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .reason {
    font-size: 11px;
    color: #aaa;
    margin-top: 8px;
    font-style: italic;
    border-top: 1px solid #f0f0f4;
    padding-top: 8px;
  }

  /* ── Execution tree ── */
  .tree {
    background: #ffffff;
    border: 1px solid #e4e4ec;
    border-radius: 10px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .tree-root {
    font-size: 12px;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f0f0f4;
  }

  .tree-call {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    font-size: 12px;
  }

  .tree-prefix { color: #ddd; white-space: pre; width: 28px; flex-shrink: 0; font-family: monospace; }
  .tree-name { font-weight: 600; color: #6d28d9; min-width: 100px; }
  .tree-bar-wrap { flex: 1; margin: 0 16px; height: 5px; background: #f0eeff; border-radius: 3px; overflow: hidden; }
  .tree-bar { height: 100%; background: linear-gradient(90deg, #6d28d9, #a78bfa); border-radius: 3px; }
  .tree-tokens { color: #aaa; min-width: 80px; text-align: right; font-size: 11px; }
  .tree-latency { color: #888; min-width: 70px; text-align: right; font-size: 11px; font-weight: 600; }

  /* ── Token bar ── */
  .token-bar-wrap {
    background: #ffffff;
    border: 1px solid #e4e4ec;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .token-bar-track {
    height: 8px;
    background: #f0f0f4;
    border-radius: 4px;
    overflow: hidden;
    display: flex;
    margin-bottom: 12px;
  }

  .token-bar-input  { background: #6d28d9; }
  .token-bar-output { background: #a78bfa; }

  .token-legend {
    display: flex;
    gap: 24px;
    font-size: 12px;
    color: #888;
  }

  .dot { width: 9px; height: 9px; border-radius: 2px; display: inline-block; margin-right: 6px; vertical-align: middle; }
  .dot-input  { background: #6d28d9; }
  .dot-output { background: #a78bfa; }

  .no-data {
    font-size: 12px;
    color: #ccc;
    font-style: italic;
    margin-top: 12px;
  }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #e0e0e8; border-radius: 4px; }
</style>
</head>
<body>

<header>
  <a class="logo" href="/">
    <!-- CIVI mark: four squares in 2×2 grid -->
    <svg class="logo-mark" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="1"  y="1"  width="12" height="12" rx="3" fill="#6d28d9"/>
      <rect x="17" y="1"  width="12" height="12" rx="3" fill="#6d28d9" opacity="0.5"/>
      <rect x="1"  y="17" width="12" height="12" rx="3" fill="#6d28d9" opacity="0.5"/>
      <rect x="17" y="17" width="12" height="12" rx="3" fill="#6d28d9"/>
    </svg>
    <span class="logo-text">CI<span>V</span>I</span>
  </a>

  <div class="header-divider"></div>
  <span class="header-product">MIMIC</span>
  <span class="header-sub">cognitive routing runtime</span>

  <div class="header-right">
    <div class="live-dot"></div>
    live · auto-refresh 5s
  </div>
</header>

<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-label">Runs</div>
    <div id="run-list"></div>
  </aside>

  <main class="main" id="main">
    <div class="empty-state">
      <div class="big">No run selected</div>
      <div>Run <code>python3 run.py</code> to generate data</div>
    </div>
  </main>
</div>

<script>
let runs = [];
let selected = null;

async function loadRuns() {
  const res = await fetch('/api/runs');
  const fresh = await res.json();
  const changed = JSON.stringify(fresh) !== JSON.stringify(runs);
  runs = fresh;
  if (changed) {
    renderSidebar();
    if (!selected && runs.length > 0) selectRun(runs[0].run_id);
  }
}

function renderSidebar() {
  const el = document.getElementById('run-list');
  if (runs.length === 0) {
    el.innerHTML = '<div style="padding:16px 18px;color:#ccc;font-size:11px;">No runs yet.</div>';
    return;
  }
  el.innerHTML = runs.map(r => {
    const mode = r.longterm?.benchmark?.value?.execution_mode || 'unknown';
    const task = r.sensory?.raw || '—';
    const active = r.run_id === selected ? ' active' : '';
    return `<div class="run-item${active}" id="item-${r.run_id}" onclick="selectRun('${r.run_id}')">
      <div class="run-id">RUN ${r.run_id}</div>
      <div class="run-task">${task}</div>
      <span class="run-mode mode-${mode}">${mode}</span>
    </div>`;
  }).join('');
}

function selectRun(id) {
  selected = id;
  document.querySelectorAll('.run-item').forEach(el => el.classList.remove('active'));
  const item = document.getElementById('item-' + id);
  if (item) item.classList.add('active');
  const run = runs.find(r => r.run_id === id);
  renderMain(run);
}

function fmt(n) { return n !== undefined ? n.toLocaleString() : '—'; }

function renderMain(run) {
  const b = run.longterm?.benchmark?.value;
  const task = run.sensory?.raw || '—';
  const ts = run.sensory?.timestamp?.replace('T', ' ').slice(0, 19) || '';

  if (!b) {
    document.getElementById('main').innerHTML = `
      <div class="run-header">
        <h2>RUN ${run.run_id}</h2>
        <span class="ts">${ts}</span>
      </div>
      <div class="section-title">Task</div>
      <div class="task-block">${task}</div>
      <p class="no-data">No benchmark data — this run predates the benchmark system.</p>
    `;
    return;
  }

  const calls = b.calls || [];
  const maxLat = Math.max(...calls.map(c => c.latency_ms), 1);

  const treeRows = calls.map((c, i) => {
    const isLast = i === calls.length - 1;
    const prefix = isLast ? '└── ' : '├── ';
    const tok = c.input_tokens + c.output_tokens;
    const pct = Math.round((c.latency_ms / maxLat) * 100);
    const cacheTag = c.cache_read ? `<span style="font-size:10px;color:#16a34a;margin-left:6px">↩ ${fmt(c.cache_read)} cached</span>`
                   : c.cache_created ? `<span style="font-size:10px;color:#9ca3af;margin-left:6px">✦ cache set</span>` : '';
    return `<div class="tree-call">
      <span class="tree-prefix">${prefix}</span>
      <span class="tree-name">${c.label}</span>${cacheTag}
      <div class="tree-bar-wrap"><div class="tree-bar" style="width:${pct}%"></div></div>
      <span class="tree-tokens">${fmt(tok)} tok</span>
      <span class="tree-latency">${Math.round(c.latency_ms)}ms</span>
    </div>`;
  }).join('');

  const inPct  = b.total_tokens ? Math.round((b.total_input_tokens  / b.total_tokens) * 100) : 50;
  const outPct = 100 - inPct;

  const score = run.longterm?.score?.value || {};
  const reason = score.reason || b.reason || '';

  document.getElementById('main').innerHTML = `
    <div class="run-header">
      <h2>RUN ${run.run_id}</h2>
      <span class="run-mode mode-${b.execution_mode}">${b.execution_mode}</span>
      <span class="ts">${ts}</span>
    </div>

    <div class="section-title">Task</div>
    <div class="task-block">
      ${task}
      ${reason ? `<div class="reason">${reason}</div>` : ''}
    </div>

    <div class="section-title">Metrics</div>
    <div class="cards">
      <div class="card highlight">
        <div class="label">Complexity</div>
        <div class="value">${b.complexity}<span class="unit">/10</span></div>
      </div>
      <div class="card">
        <div class="label">Model Calls</div>
        <div class="value">${b.model_calls}</div>
      </div>
      <div class="card">
        <div class="label">Total Tokens</div>
        <div class="value">${fmt(b.total_tokens)}</div>
      </div>
      <div class="card">
        <div class="label">Latency</div>
        <div class="value">${Math.round(b.total_latency_ms)}<span class="unit">ms</span></div>
      </div>
      ${b.fragment_count ? `<div class="card">
        <div class="label">Fragments</div>
        <div class="value">${b.fragment_count}</div>
      </div>` : ''}
      ${b.total_cache_read ? `<div class="card highlight">
        <div class="label">Cache Saved</div>
        <div class="value">${fmt(b.total_cache_read)}<span class="unit">tok</span></div>
      </div>` : ''}
    </div>

    ${calls.length ? `
    <div class="section-title">Execution Tree</div>
    <div class="tree">
      <div class="tree-root">Task</div>
      ${treeRows}
    </div>

    <div class="section-title">Token Breakdown</div>
    <div class="token-bar-wrap">
      <div class="token-bar-track">
        <div class="token-bar-input"  style="width:${inPct}%"></div>
        <div class="token-bar-output" style="width:${outPct}%"></div>
      </div>
      <div class="token-legend">
        <span><span class="dot dot-input"></span>Input — ${fmt(b.total_input_tokens)} tokens (${inPct}%)</span>
        <span><span class="dot dot-output"></span>Output — ${fmt(b.total_output_tokens)} tokens (${outPct}%)</span>
      </div>
    </div>
    ` : ''}
  `;
}

loadRuns();
setInterval(loadRuns, 5000);
</script>
</body>
</html>"""


def load_runs():
    if not WAGON_DIR.exists():
        return []
    runs = []
    for f in sorted(WAGON_DIR.glob("run_*.json"), reverse=True):
        with open(f) as fh:
            try:
                runs.append(json.load(fh))
            except json.JSONDecodeError:
                pass
    return runs


@app.route("/")
def index():
    return HTML


@app.route("/api/runs")
def api_runs():
    return jsonify(load_runs())


if __name__ == "__main__":
    print("MIMIC Dashboard → http://localhost:5001")
    app.run(port=5001, debug=False)
