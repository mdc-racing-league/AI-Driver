# Baseline lap times

First-cut timing reference for `src/driver_baseline.py` on Corkscrew. Subsequent Phase 3 tuned controllers are benchmarked against these numbers.

## Run index

### Run 001 — 2026-04-21 PM (driver_baseline.py v1, commit `379c7bb`)

**Baseline lap time: `3:32.92` (212.92 s) on Corkscrew, no damages, no pit stops.** Evidence: `docs/screenshots/2026-04-21_phase2-day1-p1-finish.png` (TORCS Race Results screen).

| Field | Value |
|---|---|
| Track | Corkscrew (road) |
| Race mode | Quick Race, solo (no AI opponents) |
| Start | Standing start, grid pole |
| Driver | `scr_server 1` → `src/driver_baseline.py` |
| Target speed | 55 km/h (set in constants) |
| Finishing order | **P1** |
| **Lap time (best = total)** | **`3:32.92`** |
| Laps completed | **1** |
| Top speed observed | 65 km/h |
| Damages | **0** |
| Pit stops | 0 |
| Peak `trackPos` (per driver log) | +0.66 |
| Min `trackPos` (per driver log) | −0.66 |
| Left the track? | No |

### Known limitations of Run 001

1. **Per-lap time captured via TORCS scoreboard, not driver log.** Driver logs `curLapTime` per tick but not `lastLapTime`. Ground truth came from the Race Results screen. ✅ Fixed in Run 002.
2. **Loop doesn't exit on race end.** Python driver kept iterating ~90k empty ticks after `scr_server` shut down. Doesn't affect race validity, but makes the log noisy. ✅ Fixed in Run 002.
3. **Off-track recovery never triggered.** `|trackPos|` stayed ≤ 0.66 — car never reached the recovery threshold (1.0). Recovery code is untested in-anger.

### Run 002 — 2026-04-22 AM (driver_baseline.py v2, commit `9e1d1c3`)

First run with per-lap timing captured from the **driver log** (not the scoreboard) and clean race-end exit. Evidence: `docs/screenshots/2026-04-22_phase2-day1-run002-clean.png`.

| Field | Value |
|---|---|
| Track | Corkscrew (road) |
| Race mode | Quick Race, solo |
| Start | Standing start, grid pole |
| Driver | `scr_server 1` → `src/driver_baseline.py` |
| Target speed | 55 km/h |
| Finishing order | **P1** |
| **Lap time (driver log, `final-on-race-end`)** | **`212.806 s` (`3:32.81`)** |
| Lap time (TORCS scoreboard) | `3:32.81` — matches driver log to 0.01 s |
| Laps completed | **1** |
| Top speed observed | 65 km/h |
| Damages | **0** |
| Pit stops | 0 |
| Loop exit | `race ended (curLapTime frozen at 212.81s for 400 ticks)` at step 10,697 |
| Ghost ticks after race end | **0** (was ~90k in Run 001) |

### Cross-run determinism check

Lap-time stability across the Phase 2 Day 1 instrumentation iterations (same controller, same track, same settings):

| Run | Controller commit | Lap time (s) | Source |
|---|---|---|---|
| 001 | `379c7bb` | 212.92 | scoreboard |
| 002-r1 | `7fcfab3` | 212.95 | scoreboard + driver (uninstrumented) |
| 002-r2 | `1d2b003` | 212.882 | driver log (`lastLapTime`) |
| **002 (canonical)** | `9e1d1c3` | **212.806** | driver log (`final-on-race-end`) |

Spread: 0.144 s across 4 runs (0.068%). TORCS + `scr_server` + our driver are effectively deterministic on this controller. Phase 3 A/B comparisons can trust single-run deltas down to ~0.1 s.

### Run 005 — 2026-04-22 (driver_baseline.py, commit `df41e63`) — FAILED VALIDATION

First attempt at a SCHEMA v0.2 archive. Driver wrote `frames.ndjson` + `manifest.json` correctly, but `validate_run.py` flagged **1 schema violation**:

```
line 10299: time went backwards: 0.00199487 < previous 212.806
```

Root cause: after the lap completes, `scr_server` keeps sending UDP frames with `curLapTime` reset to ≈0.00 (Run 005's behavior; Run 002 had it frozen at 212.81 — the post-race state is **non-deterministic between runs**). The driver was logging those frames into the archive, breaking SCHEMA Rule 3 (time monotonically non-decreasing). Lap time itself: `212.824 s` — within 0.018 s of Run 002, so the controller is fine; only the logger gating was wrong.

Fix: commit `487c6de` adds a `race_finalized` flag set from both lap-detection paths; subsequent ticks skip `logger.log_frame()`. Stale-tick exit detector still runs to break out of the loop cleanly.

### Run 006 — 2026-04-22 (driver_baseline.py, commit `487c6de`) — CANONICAL v0.2 ARCHIVE

**First SCHEMA v0.2 archive that passes `validate_run.py` (10,706 frames, 0 errors).**

| Field | Value |
|---|---|
| Track | Corkscrew (road) |
| Race mode | Quick Race, solo |
| Start | Standing start, grid pole |
| Driver | `scr_server 1` → `src/driver_baseline.py` |
| Target speed | 55 km/h |
| Finishing order | **P1** |
| **Lap time (driver log, `final-on-race-end`)** | **`212.986 s` (`3:32.99`)** |
| Laps completed | **1** |
| Top speed observed | 65 km/h |
| Damages | **0** |
| Pit stops | 0 |
| Loop exit | `race ended (curLapTime frozen at 212.99s for 400 ticks)` at step 10,706 |
| Frames captured | **10,706** |
| Validator | **PASS** (`schema v0.2`) |
| Archive | `telemetry/runs/2026-04-21T20-43-35/` |

**Architectural note — passed by luck.** This run's race-end behavior was the *frozen* variant (Run 002-style), not the *zero-reset* variant (Run 005-style). Frozen-equal frames satisfy "non-decreasing" by exact equality. If a future run lands the zero-reset variant **and** the lap completes via the `final-on-race-end` path (so `race_finalized` doesn't flip until after 400 stale ticks have already been logged), validation will fail again. The robust fix is to flip `race_finalized` after ~10 stale ticks instead of waiting 400. Deferred — will land if/when the next failure forces it.

### Target for Phase 3 tuning

Mission brief requires a **-15% improvement vs. baseline** before Phase 4. That means Phase 3 must deliver **≤ 3:00.98** on Corkscrew (≤ 180.98 s). Current headroom: raise target speed, segment-aware braking/throttle, possibly a PID on heading instead of pure P.

### Why 55 km/h as baseline target

Chosen to guarantee track-keeping on the Corkscrew hairpin at the expense of lap time. Attempted 80 km/h first (commit `d9aeb4f`) — under-damped steering sent `trackPos` to ±7.58, car left the track. 55 km/h is slow but valid; Phase 3 work will raise this per-segment.

---

## How to add a new run

1. Race finishes; copy terminal output from Window C to `telemetry/runs/<ISO-timestamp>/stdout.log`
2. Add a new `### Run NNN` section above, matching this schema
3. Commit: `git add telemetry/baseline.md telemetry/runs/... && git commit -m "run NNN: <headline>"`
4. Run `scripts/validate_run.py telemetry/runs/<ISO-timestamp>/` (Phase 2 item)
