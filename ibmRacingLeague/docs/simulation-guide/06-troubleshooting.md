# 06 — Troubleshooting (runtime)

Problems that happen **while running the sim** or Granite — not during install. For install problems see `../setup.md`.

---

## TORCS issues

| Symptom | Cause | Fix |
|---|---|---|
| Sim locks up mid-race | Our driver got stuck in a blocking call | Kill TORCS; look for `time.sleep` or blocking `input()` in the driver |
| Car spawns and immediately crashes | Controller returning `None` or out-of-range actions | Clamp throttle/brake to `[0,1]`, steer to `[-1,1]` |
| Car drives straight off the track | Steering input inverted | TORCS convention: positive steer = left; verify sign in controller |
| Huge lap-time variance run-to-run | Weather or opponent variability not locked | Review `config/raceman/quickrace.xml` — lock all stochastic settings |
| "Opponent not found" error | Opponent driver name typo in race config | Match exactly against TORCS's built-in drivers list |

---

## Telemetry issues

| Symptom | Cause | Fix |
|---|---|---|
| `frames.csv` is empty | Tailer started after TORCS; missed `seek(0, 2)` tail position | Start tailer **before** TORCS (see `04-capturing-telemetry.md`) |
| `frames.csv` has nulls in all extended fields | Driver still emitting v0.1 schema | Upgrade driver to v0.2 schema per `telemetry/SCHEMA.md` |
| Different teammates' runs aren't comparable | Field order, units, or schema version drift | Run `scripts/validate_run.py` on each run archive before merging |
| Run archive missing `manifest.json` | Used raw `log_telemetry.py` instead of `run_race.py` | Use the Phase 2 wrapper (`scripts/run_race.py`) |

---

## Granite / Ollama issues

| Symptom | Cause | Fix |
|---|---|---|
| `curl: (7) Failed to connect to localhost port 11434` | Ollama not running | `ollama serve` or restart the service |
| Continue.dev shows "no models" in VSCode | `config.yaml` path or YAML syntax error | Validate YAML; restart VSCode; confirm file location per `../setup.md` |
| Granite responses are very slow on laptop | 4 GB model on limited RAM | Use Zo for this call; or switch to `granite4:350m-h` for context-bounded tasks |
| Granite confidently states something false | You asked `350m-h` for context-free knowledge | Switch to `granite4:tiny-h`; or put the facts in the prompt |
| Continue.dev autocomplete feels wrong | `350m-h` hallucinating in low-context spots | Expected for domain terms; accept with judgment |

---

## When to escalate to the team chat

- TORCS crashes with the same error on multiple machines → likely a repo / config issue, not personal env
- Same controller code produces wildly different lap times on different teammates' machines → sim config drift, investigate `quickrace.xml` deltas
- Granite outputs identical hallucinations across multiple teammates → model regression after an Ollama upgrade; pin the model version

---

## Diagnostics to collect before asking for help

1. Exact command you ran
2. Last 50 lines of TORCS stderr
3. `manifest.json` of the failing run (if it got that far)
4. Your OS + TORCS bundle source (IBM quickstart, wine, etc.)
5. `ollama --version` and `ollama list` output

Post these in the team Discord — with this info, someone else can usually reproduce in minutes.
