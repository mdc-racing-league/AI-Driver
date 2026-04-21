# Baseline lap times

First-cut timing reference for `src/driver_baseline.py` on Corkscrew. Subsequent Phase 3 tuned controllers are benchmarked against these numbers.

## Run index

### Run 001 — 2026-04-21 PM (driver_baseline.py v1, commit `379c7bb`)

| Field | Value |
|---|---|
| Track | Corkscrew (road) |
| Race mode | Quick Race, solo (no AI opponents) |
| Start | Standing start, grid pole |
| Driver | `scr_server 1` → `src/driver_baseline.py` |
| Target speed | 55 km/h (set in constants) |
| Finishing order | **P1** (solo, but race completed cleanly) |
| Race duration (sim) | ~210 sim-seconds |
| Steps until `scr_server` ended race | 10,200 |
| Laps completed | 2–3 (exact count not logged yet — add in Run 002) |
| Peak `trackPos` | +0.66 |
| Min `trackPos` | −0.66 |
| Left the track? | No |
| Observed speed range | 55–65 km/h |

### Known limitations of Run 001

1. **Per-lap time not captured.** Driver logs `curLapTime` per tick but not `lastLapTime` — we know total sim duration but not individual lap times. Fix planned before Run 002.
2. **Loop doesn't exit on race end.** Python driver kept iterating 90k empty ticks after `scr_server` shut down. Doesn't affect race validity, but makes log noisy.
3. **Off-track recovery never triggered.** `|trackPos|` stayed ≤ 0.66 — car never reached the recovery threshold (1.0). Recovery code is untested in-anger.

### Why 55 km/h as baseline target

Chosen to guarantee track-keeping on the Corkscrew hairpin at the expense of lap time. Attempted 80 km/h first (commit `d9aeb4f`) — under-damped steering sent `trackPos` to ±7.58, car left the track. 55 km/h is slow but valid; Phase 3 work will raise this per-segment.

---

## How to add a new run

1. Race finishes; copy terminal output from Window C to `telemetry/runs/<ISO-timestamp>/stdout.log`
2. Add a new `### Run NNN` section above, matching this schema
3. Commit: `git add telemetry/baseline.md telemetry/runs/... && git commit -m "run NNN: <headline>"`
4. Run `scripts/validate_run.py telemetry/runs/<ISO-timestamp>/` (Phase 2 item)
