# MIMIC — Claude Reference

**What it is:** A morphic agent framework by CIVI (Kuala Lumpur). Routes tasks through complexity scoring and executes them as either a single-pass prompt (PRIME) or a split-process-merge pipeline (FRAGMENT).

---

## Architecture

```
run.py                  → Entry point / demo harness
mimic/core.py           → MimicCore — main orchestrator
mimic/scorer.py         → Heuristic complexity classifier (no AI)
mimic/wagon.py          → Three-tier memory logger (sensory / working / longterm)
mimic/benchmarks.py     → Per-run API call metrics (tokens, latency)
mimic/fragments.py      → parse_subtasks(), build_merge_prompt() helpers
dashboard.py            → Flask web UI at localhost:5001, reads wagon_logs/
wagon_logs/             → JSON run records written by Wagon.save()
```

---

## Execution flow

```
MimicCore.run(task)
  └─ Scorer.score(task)           # heuristic, no API call
       ├─ complexity < 5 or not parallelizable → PRIME
       │    └─ single Claude call
       └─ complexity ≥ 5 and parallelizable → FRAGMENT
            ├─ split call  (Claude → JSON array of subtasks)
            ├─ arm calls   (parallel via ThreadPoolExecutor)
            └─ merge call  (Claude → unified response)
```

---

## Key constants / config

| Thing | Value | Location |
|---|---|---|
| Model | `claude-sonnet-4-6` | `core.py:MODEL` |
| FRAGMENT threshold | complexity ≥ 5 | `scorer.py:Scorer.complexity_threshold` |
| Fragment count | 2 (complexity 5–7), 3 (≥8) | `scorer.py:_suggest_fragments` |
| Dashboard port | 5001 | `dashboard.py` |
| Log dir | `wagon_logs/` | `wagon.py:Wagon.wagon_dir` |

---

## Running

```bash
# Run demo (2 tasks, generates wagon_logs/run_*.json)
python3 run.py

# Launch dashboard
python3 dashboard.py   # → http://localhost:5001
```

Requires `.env` with `ANTHROPIC_API_KEY`.

---

## Design decisions

- **Scorer is pure heuristic** — keyword weights + word/sentence count, no LLM call. Fast but brittle for ambiguous phrasing.
- **Fragment arms are parallel** — `ThreadPoolExecutor` in `core.py:_run_fragments`. Benchmark lock (`_bench_lock`) keeps token recording thread-safe.
- **JSON parsing is fence-tolerant** — `fragments.parse_subtasks()` strips markdown code fences before `json.loads`.
- **Wagon memory** — three tiers mirror a cognitive model: sensory (raw), working (in-flight), longterm (consolidated). All runs persist to JSON.

---

## Known limitations / future work

- Scorer can misclassify if task phrasing is unusual — consider an LLM-backed scorer for edge cases.
- No retry logic on API calls — a failed arm aborts the entire fragment run.
- Fragment count is fixed (2 or 3) — could be dynamic based on task structure.
- No prompt caching — arms share no common prefix long enough to meet the 1024-token cache threshold.
