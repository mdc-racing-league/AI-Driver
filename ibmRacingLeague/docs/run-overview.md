# Run Overview — Every Trial on Corkscrew

Complete log of every run from Phase 2 baseline (Run 001) through Session 2026-04-24 late (Run 035). Each row: what was tested, the lap time, whether it counts as a valid submission lap.

**Current submission anchor: Run 031 — 156.586 s (2:36.59), 0 damages, commit `5a25810`, config `segments_submission_v7.yaml`.**

For deeper analysis of any run see [`docs/phase3-experiments.md`](./phase3-experiments.md) and [`telemetry/baseline.md`](../telemetry/baseline.md). For segment IDs see [`docs/track-map.md`](./track-map.md). For methodology see [`docs/racing-methodology.md`](./racing-methodology.md).

## Phase 2 — first clean lap (2026-04-21)

| Run | Date | Config | Purpose | Lap | Damages | Valid | Notes |
|---|---|---|---|---:|---:|:---:|---|
| 001 | 04-21 PM | driver v1 | First clean Corkscrew lap | 212.92 s | 0 | ✅ | P1 finish, validated TORCS + snakeoil3 stack |
| 002 | 04-22 AM | logger fix | Race-end detection + per-lap logging | 212.81 s | 0 | ✅ | No controller change |

## Phase 3 Day 1 — target-speed push (2026-04-22 AM)

| Run | Date | Config | Purpose | Lap | Damages | Valid | Notes |
|---|---|---|---|---:|---:|:---:|---|
| 006 | 04-22 | target 55 canonical | Archive as baseline | 212.99 s | 0 | ✅ | Reference point for all later deltas |
| 007 | 04-22 | target 80 | First aggressive push | **170.57 s** | 0 | ✅ | **−19.9 % hit Phase 3 rubric gate** |
| 008 | 04-22 | target 80 + 3 slow zones | Clean target-80 spin | ~170 s | 0 | ✅ | Slow-zones at tight corners |

## Phase 3 Day 2 — per-segment driver (2026-04-22 PM)

| Run | Date | Config | Purpose | Lap | Damages | Valid | Notes |
|---|---|---|---|---:|---:|:---:|---|
| 009 | 04-22 | 6 narrow zones | First below Phase 3 gate | ~170 s | 0 | ✅ | |
| 010 | 04-22 | segments.yaml v1 | Switch slow-zone → segment map | ~170 s | 0 | ✅ | s09 too wide (regression) |
| 011 | 04-22 | s09 narrowed | Fix s09 | DNF | — | ❌ | Crash — window pushed wrong direction |
| 012 | 04-22 | match Run 009 | Prove map = slow-zone | ~170 s | 0 | ✅ | Segments subsume slow-zones |
| 013 | 04-22 | v3 baseline | Round-1 reference | **165.67 s** | 0 | ✅ | Anchor for next 10 runs |

## Brake calibration + lookahead physics (2026-04-22)

| Run | Date | Config | Purpose | Lap | Damages | Valid | Notes |
|---|---|---|---|---:|---:|:---:|---|
| 014/015 | 04-22 | `--brake-test` | Measure real decel | — | — | N/A | 22 m/s² mean / 25 m/s² peak |
| 016 | 04-22 | lookahead 200 / 7.0 | Conservative brake | ~162 s | 0 | ✅ | Too-early brake |
| 017 | 04-22 | lookahead 150 / 9.0 | Moderate | ~160 s | 0 | ✅ | **Controller settings locked in** |
| 018 | 04-22 | lookahead 120 / 11.0 | Aggressive | DNF | — | ❌ | Overshoots |

## Round 2 strategies + full-pedal brake (2026-04-22 PM)

| Run | Date | Config | Purpose | Lap | Damages | Valid | Notes |
|---|---|---|---|---:|---:|:---:|---|
| 019 | 04-22 | flat-out s08 130 | Max straights | DNF | — | ❌ | s08 kink |
| 020 | 04-22 | push-straights s08 110 | Less aggressive | DNF | — | ❌ | s08 kink |
| 021 | 04-22 | r2a-v2 first live | New strategy | DNF | — | ❌ | s13 |
| 022 | 04-22 | r2a-v2 + brake zones | Fix s13 | 163.47 s | 0 | ✅ | Clean |
| 023 | 04-22 | r2a-v2 + s06/s08/s09 tune | First sub-161 | **160.67 s** 🏆 | 0 | ✅ | **Round-2 PB**, previous submission anchor |
| 024 | 04-22 | s08 102 | Push kink harder | DNF | — | ❌ | Reverted |
| 025 | 04-22 | s08 98 rollback | Recover from 024 | 160.33 s | 0 | ⚠️ | 1 off-track |

## Session 2026-04-24 — racing-line PB cascade

| Run | Date | Config | Purpose | Lap | Damages | Valid | Notes |
|---|---|---|---|---:|---:|:---:|---|
| 026 | 04-24 | v2 all-straights | Raise every straight | 167.15 s | 0 | ✅ | Straight headroom validated |
| 027 | 04-24 | v3 speed + kink | Tune kink | 165.63 s | 0 | ✅ | Mild regression |
| 028 | 04-24 | v4 held | Lock in v3 baseline | ~165 s | 0 | ✅ | Stable |
| 029 | 04-24 | **v5 racing-line introduced** | entry/apex/exit_pos | 165.83 s | 0 | ✅ | Line validated, time flat |
| 030 | 04-24 | **v6 line + corner bumps** | Exploit the line | **160.61 s** 🏆 | 0 | ✅ | −5.02 s, first sub-161 clean |
| 031 | 04-24 | **v7 straight-cap push** | Hit all the caps | **156.59 s** 🏆 | 0 | ✅ | **SUBMISSION ANCHOR**, 1 transient s08 touch |

## Session 2026-04-24 (late) — pushing past Run 031

| Run | Date | Config | Purpose | Lap | Damages | Valid | Notes |
|---|---|---|---|---:|---:|:---:|---|
| 032 | 04-24 | v8 aggressive | 12 deltas off Run 031 | DNF | — | ❌ | Off at s08 kink + s13 |
| 033 | 04-24 | v9 rollbacks | s07/s08a/s12/s13/s14 rolled back | DNF | — | ❌ | Terminal off at s13 apex |
| 034 | 04-24 | v10 hard s13 fix | speed 52, apex −0.40 | 145.03 s* | 18 | ❌ | **s09 hairpin cut** (trackPos +2.60) |
| 035 | 04-24 | v11 s09 + s08c fix | pull s09 apex, s08c exit in | 145.16 s* | ~18 | ❌ | **Still cutting s09** (+2.21) |

\* Clock time but invalid — car cut inside of s09 and/or hit barriers for damages. TORCS counted the lap but submission rules wouldn't.

## Config evolution

| Config | Key change | Best run | Best time |
|---|---|---|---:|
| baseline | target 55, no zones | Run 006 | 212.99 s |
| target 80 | global speed push | Run 007 | 170.57 s |
| slow-zones | 3 narrow zones | Run 008 | ~170 s |
| segments.yaml v1 | per-segment caps | Run 012 | ~170 s |
| v3 (segment caps tuned) | Round-1 anchor | Run 013 | 165.67 s |
| lookahead | physics-derived brake | Run 017 | ~160 s |
| r2a-v2 | full-pedal brake + narrow hairpins | Run 022 | 163.47 s |
| r2a-v2 + s06/s08/s09 | Round-2 anchor | Run 023 | 160.67 s |
| v6 | racing-line interpolator + corner bumps | Run 030 | 160.61 s |
| **v7** | **straight-cap push** | **Run 031** | **156.59 s** (anchor) |
| v8–v11 | iterations past v7 | (none valid) | — |

## What we learned this session (2026-04-24 late)

1. **The racing-line interpolator is a double-edged tool.** It bought us 9 s in Runs 030–031 but introduced a new failure mode: when `apex_pos` is ±0.55 AND corner speed is too high, the controller requests steering lock and the car leaves the track on the inside (s09 in Runs 034/035) or the outside (s13 in Run 033). The fix for each hairpin is the same pattern: **drop speed + pull apex in** (s13 was fixed this way in v10). v12 will apply it to s09.
2. **The s08 kink has an unresolved elevation-drift problem.** All 6 runs 030–035 show `|trackPos| ≥ 1.0` at 1940–1976 m regardless of `s08c` line edits. The real problem zone is `s08b` (1940–1960 m) where line target is already 0.0 but the car drifts to −1.2+. This is the elevation hypothesis — **run the calibration lap** before any more s08 tuning (action-items #1b, now High priority).
3. **TORCS counts corner-cut laps.** Run 034's 145 s clock was produced by skipping ~1 m of track at s09. TORCS gave the lap, but it accumulated 18 damages — would be disqualified under any reasonable submission rule. Means we need to validate every PB against `find_offtracks.py` before treating it as a real time.

## Tomorrow's first experiment

**v12:** surgical s09 cut fix + s08b kink fix. If damages=0, iterate back up on s09 speed (50 → 53 → 56) and s08a speed (92 → 95 → 98) one at a time to find the real ceiling without regressing. Alternative: do the elevation calibration lap first so s08 tuning stops being empirical.
