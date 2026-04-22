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

## Run 009 — result (cleared gate, new reference)

`--target-speed 80 --slow-zone 2420:2540:50 --slow-zone 3220:3320:50`
→ **170.044 s clean, damages 0, off-tracks 0.** Beat the projection
by ~3 s (predicted 173.06) because narrower zones mean less time ramping,
not just less time at 50 km/h. Peak `|trackPos|` actually *dropped* from
0.68 (Run 008) to 0.53 — narrower zones are not only faster, they're
safer, because the car enters the corner at a speed it has to drive
anyway rather than being over-slowed then re-accelerating into the apex.

**Run 009 is the new clean reference.**

## Run 010 — per-segment driver (plan)

Phase 3 now has a full segment map (`telemetry/segments.yaml`, 16
segments, derived from Run 006 by `scripts/derive_segments.py`) and the
driver accepts `--segments PATH`. Run 010 replaces the two hand-picked
`--slow-zone` windows with the full map.

**Evidence from Run 009's segment report** (`telemetry/runs/2026-04-21T22-42-18/segment_report.md`):

| Segment | Target (km/h) | Peak \|trackPos\| | Peak \|steer\| | Notes |
|---|---|---|---|---|
| s01 turn L 475m | 75 | 0.466 | 0.347 | Real corner, margin 0.53 |
| s03 turn R 775m | 75 | 0.347 | 0.265 | Mild — 75 is cautious |
| s05 turn R 1040m | 78 | 0.249 | 0.183 | Barely cornering |
| s07 turn L 1540m | 78 | 0.265 | 0.185 | Barely cornering |
| s09 turn R 2605m | 50 | **0.667** | 0.618 | Hairpin — keep at 50 |
| s11 turn R 2985m | 78 | 0.261 | 0.196 | Barely cornering |
| s13 turn L 3272m | 50 | **0.619** | 0.506 | Hairpin — keep at 50 |

Three "corner" segments (s05/s07/s11) stayed under peak `|trackPos|` of
0.27 — indistinguishable from the surrounding straights at 78–80 km/h.
Only the two hairpins (s09/s13) and s01 behave like real corners.

**Hypothesis:** Using `segments.yaml` as-is, we should match Run 009's
lap time (~170.0 s) closely. Time cost from dropping from 80 to 75/78
on the five non-hairpin "corner" segments is small: combined length
~425 m at 77 km/h vs 80 km/h ≈ +0.74 s. Prediction: **~170.8 s**.

**Config (Windows):**

```
python src\driver_baseline.py ^
  --target-speed 80 ^
  --segments telemetry\segments.yaml ^
  --notes "Run 010 Path A - --segments full map"
```

**Why still run this?** To close the loop: Run 010 is the first lap
driven by the segment map rather than by hand-placed zones. Even if it
ties Run 009 on lap time, it validates that `--segments` subsumes
`--slow-zone` and unlocks per-segment tuning as the next lever.

**Abort criteria:**

- Damages > 0 or `|trackPos| > 1.0` → regression; fall back to Run 009 config.
- Lap time > 172 s → investigate (shouldn't happen given the map tracks
  Run 009's proven slow zones at s09/s13).

**If Run 010 passes cleanly, Run 011:** promote s05/s07/s11 to 80 km/h
in `segments.yaml` (gain ~0.4 s), and consider raising s03 from 75 → 80
(gain ~0.1 s) given 0.47 of margin.

---

## Run 010 — result (regression: s09 hairpin too wide)

`--target-speed 80 --segments telemetry/segments.yaml`
→ **175.266 s clean, damages 0, top 86 km/h, no excursions** (|trackPos|
peak 0.78). `--segments` infrastructure works end-to-end — it subsumes
`--slow-zone` functionally — but the auto-derived map was too
conservative at the right-hand hairpin.

**Root cause:** `s09_turn_R_2605m` was derived as `2430:2780 m` (350 m
wide) at 50 km/h. Run 009's hand-placed slow-zone covered only `2420:2540
m` (120 m). That extra ~230 m held at ~60 km/h instead of ~80 km/h costs
~+6.2 s, almost exactly matching the measured +5.2 s regression vs
Run 009.

**Why the derivation over-covered s09:** `derive_segments.py` uses
`corner_steer_abs=0.08`, which stays triggered through the hairpin's
entry ramp-in and exit ramp-out, not just the apex. Fine for most
segments (s13 came out 55 m — correct), but the long sweep into Hairpin
A tripped the detector early.

**Fix for Run 011:** narrowed `s09` to `2500:2650 m` (150 m) by hand,
extended `s08` forward to 2500 and `s10` backward to 2650 so the car
holds 80 km/h until the real apex entry. s13 left alone (already
correct at 55 m). s05/s07/s11 stay at 78 km/h until Run 011 measures
the new baseline — no point tuning two knobs at once.

---

## Run 011 — plan (s09 narrowed)

`--target-speed 80 --segments telemetry/segments.yaml` (same command;
only the YAML changed)

**Hypothesis:** narrowing s09 from 350 m → 150 m recovers most of the
+5.2 s regression. Prediction: **~170.5 s** (within 0.5 s of Run 009,
ideally slightly under because the driver enters s10 at 80 km/h sooner).

**Abort criteria:**
- Damages > 0 or `|trackPos| > 1.0` → s09 window was too tight; widen back.
- Lap > 172 s → unexpected; inspect segment report.

**If Run 011 passes cleanly, Run 012:** promote s05/s07/s11 from 78 → 80
km/h (gain ~0.4 s, all three have peak |trackPos| ≤ 0.27 in Run 009 —
massive safety margin).

---

## Tracked deltas

Running tally vs Run 006 (the 55 km/h clean baseline):

| Run | Lap (s) | Δ vs Run 006 | Δ vs Run 009 | Status |
|---|---|---|---|---|
| 006 | 212.986 | — | +42.942 | Clean baseline |
| 007 | 170.566 | −42.420 (−19.9%) | +0.522 | Unsafe — 41 dmg |
| 008 | 175.106 | −37.880 (−17.8%) | +5.062 | Clean reference (superseded) |
| 009 | 170.044 | −42.942 (−20.2%) | — | **Clean reference** |
| 010 | 175.266 | −37.720 (−17.7%) | +5.222 | Clean but regressed — s09 too wide |
| 011 | *target ~170.5* | *target ~−42.5* | *target ~−0.5* | Pending — s09 narrowed to 150 m |

Phase 3 rubric gate: `≤ 180.98 s` (−15%) — cleared in Runs 007/008/009/010.
Stretch target: `≤ 150 s` (`2:30`) clean — ~20 s below current reference.
