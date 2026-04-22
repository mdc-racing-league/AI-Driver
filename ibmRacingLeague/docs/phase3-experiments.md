# Phase 3 experiments — iteration log

Running log of controller-tuning experiments on Corkscrew with `src/driver_baseline.py`. Each entry is a single-variable change from the previous anchor run, the hypothesis behind it, the measured outcome, and the decision to accept or reject.

**Anchor runs** (for A/B comparisons):
- **Baseline (clean):** Run 006, 55 km/h everywhere, `212.986 s`, damages 0, off-tracks 0.
- **Clean fast:** Run 008, `--target-speed 80 --slow-zone 2366:2596:50 --slow-zone 3170:3434:50`, `175.106 s`, damages 0, off-tracks 0. **← current reference for Phase 3 tuning.**
- **Dirty fast (unsafe):** Run 007, `--target-speed 80` (no zones), `170.566 s`, damages 41, off-tracks 2 (peak −3.77). Reference for *lap-time ceiling* at 80 km/h, not for legal performance.

## Path A progression so far

| Run | Config | Lap (s) | Damages | Off-tracks | Decision |
|---|---|---|---|---|---|
| 006 | 55 km/h everywhere | 212.986 | 0 | 0 | Clean baseline |
| 007 | 80 km/h everywhere | 170.566 | 41 | 2 (peak −3.77) | Reject — unsafe |
| 008 | 80 km/h + two 50 km/h slow zones, ±100 m padding | 175.106 | 0 | 0 | **Accepted** — clean fast reference |

## Margin analysis of Run 008 (input to Run 009)

`scripts/find_offtracks.py telemetry/runs/2026-04-21T22-28-24 --threshold 0.5` reports all Run 008 windows where `|trackPos|` ≥ 0.5. Interpretation: these are the regions where the car swung furthest toward the track edge, so they tell us *how much margin we have left* against the 1.0 safety floor.

| # | trackDistance | Peak trackPos | Inside which Run 008 zone? | Margin to 1.0 |
|---|---|---|---|---|
| 1 | 1946–1953 m | −0.53 | No — taken at 80 km/h (not zoned) | 0.47 |
| 2 | 2462–2479 m | **−0.68** | Inside `2366:2596:50` | 0.32 |
| 3 | 2497–2511 m | +0.60 | Inside `2366:2596:50` (rebound) | 0.40 |
| 4 | 3267–3291 m | −0.61 | Inside `3170:3434:50` | 0.39 |

Two takeaways:

1. **The 50 km/h slow zones have ≥ 0.32 of margin left.** The car barely wobbles through the hairpins at 50 km/h. 50 is almost certainly more conservative than needed.
2. **Real-corner widths are much smaller than our zones.** The actual `|trackPos| > 0.5` windows are 17 m and 24 m wide; our zones are 230 m and 264 m wide. We added ±100 m padding at both ends in Run 008 — roughly 10× the actual corner width.

## Where the +4.540 s cost comes from

Run 008 is +4.540 s vs Run 007. Decomposing:

- **Zone A** (`2366:2596`, 230 m wide) at 50 km/h vs 80 km/h: ~230 m × (1/50 − 1/80) × 3.6 = **~1.72 s** added time.
- **Zone B** (`3170:3434`, 264 m wide) at 50 km/h vs 80 km/h: ~264 m × (1/50 − 1/80) × 3.6 = **~1.98 s** added time.
- **Ramping** (decel entering, accel exiting each zone): ~0.8 s.
- **Total accounted:** ~4.5 s ← matches observed +4.540 s.

This confirms the +4.540 s is entirely "time spent driving 50 instead of 80 through 494 m of track plus ramps." Every metre we shave off the zones translates directly to lap time saved.

---

## Run 009 — narrow the zones (plan)

**Hypothesis:** Shrinking the padding from ±100 m to ±60 m around each corner's actual `|trackPos| > 0.5` window keeps damages at 0 while recovering **~1.5–2.0 s**.

**Config:**

```
python src\driver_baseline.py \
  --target-speed 80 \
  --slow-zone 2420:2540:50 \
  --slow-zone 3220:3320:50 \
  --notes "Run 009 Path A - narrow zones, same 50 km/h speed"
```

**Zone math:**

| Zone | Run 008 | Run 009 | Width saved | Time saved |
|---|---|---|---|---|
| Hairpin A | `2366:2596` (230 m) | `2420:2540` (120 m) | 110 m | ~0.82 s |
| Hairpin B | `3170:3434` (264 m) | `3220:3320` (100 m) | 164 m | ~1.23 s |
| **Total** | 494 m | 220 m | **274 m** | **~2.05 s** |

**Expected outcome:** lap ≈ `173.06 s` (`2:53.06`), damages 0, zero excursions > 1.0.

**Abort criteria:**

- Damages > 0 → Run 009 is not a clean baseline. Back off to Run 008 zones and reject.
- Any `|trackPos| > 1.0` → car left the track. Back off.
- Lap time worse than Run 008 (`> 175.106`) → something else regressed; investigate before next iteration.

**If Run 009 passes cleanly, Run 010 options:**

- **A — narrow further** (±30 m padding): zones `2450:2510` and `3250:3305`. Another ~1.5 s.
- **B — raise zone speed** to 60 km/h: fewer metres at the slow target. Another ~0.5 s.
- **C — move to PD steering** to eliminate the need for slow zones entirely.

---

## Tracked deltas

Running tally vs Run 006 (the 55 km/h clean baseline):

| Run | Lap (s) | Δ vs Run 006 | Δ vs Run 008 | Status |
|---|---|---|---|---|
| 006 | 212.986 | — | +37.880 | Clean baseline |
| 007 | 170.566 | −42.420 (−19.9%) | −4.540 | Unsafe — 41 dmg |
| 008 | 175.106 | −37.880 (−17.8%) | — | **Clean reference** |
| 009 | *target ~173.06* | *target ~−39.9 s* | *target ~−2.0 s* | Pending |

Phase 3 rubric gate: `≤ 180.98 s` (−15%) — already cleared in Runs 007/008.
Stretch target: `≤ 150 s` (`2:30`) clean — ~25 s below current clean reference.
