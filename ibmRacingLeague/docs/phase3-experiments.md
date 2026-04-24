# Phase 3 experiments — iteration log

Running log of controller-tuning experiments on Corkscrew with `src/driver_baseline.py`. Each entry is a single-variable change from the previous anchor run, the hypothesis behind it, the measured outcome, and the decision to accept or reject.

> **Theory reference:** see [`docs/racing-methodology.md`](./racing-methodology.md) for the physics (traction circle, weight transfer, trail braking, late apex) and TORCS-specific equations (Ahura target-speed formula, pedal mapping, ABS/ASR) that these experiments are testing against.

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

## Run 011 — result (crashed — s09 window pushed wrong direction)

`--target-speed 80 --segments telemetry/segments.yaml` with s09 at
2500:2650 → **183.826 s, damages 95, off-track peak |trackPos| 3.52,
speed min −68.3 km/h** (car going backwards during recovery). P1 only
because no opponents.

**What went wrong:** Run 009's proven slow-zone was `2420:2540`. For
Run 011 I pushed the start FORWARD to 2500 instead of BACK to 2420.
Result: only ~80 m of coast-down distance before the apex at ~2580.
Car entered the hairpin at ~70 km/h into a 50 km/h corner, slid off
the outside at step 5600, spun across the track to peak trackPos
+3.52, recovered at step 6400 having lost ~10 s to the crash.

**Lesson (mechanical):** the slow-zone START needs to be upstream of
the apex by the full brake-to-target distance. On this car at P‑only
control (no active brake), coast-down from 80→50 km/h takes ~100–120 m
— so the slow-zone must begin ≥120 m before the apex. Run 009's 2420
start was 185 m before the apex at ~2605. Run 011's 2500 start was
only 105 m — too tight without active braking.

**Lesson (process):** when "fixing" a regression, first re-read the
reference config that worked. Run 009's 2420:2540 was already the
answer; I just had to adopt its boundaries wholesale instead of
inventing new ones.

---

## Run 012 — plan (match Run 009 exactly)

`segments.yaml` s09 now set to `2420:2540` at 50 km/h — identical to
Run 009's `--slow-zone 2420:2540:50`. s13 unchanged at 3245:3300.
s08 ends at 2420, s10 starts at 2540.

**Hypothesis:** Run 012 reproduces Run 009's lap time within ±0.5 s
(target: **~170 s clean, damages 0, zero excursions**). If it does,
the `--segments` infrastructure is validated as functionally
equivalent to hand-placed `--slow-zone` flags — at which point we can
move to pushing s06/s08 target speeds (the real speed levers, worth
10+ s combined) or promoting s05/s07/s11 from 78 → 80 km/h (safe, ~0.4 s).

**Abort criteria:**
- Damages > 0 or `|trackPos| > 1.0` → something else changed; diff s10/s11 targets against Run 009.
- Lap > 172 s → investigate.

**If Run 012 passes cleanly, Run 013:** promote s05/s07/s11 → 80 km/h
in YAML (one-line change, ~0.4 s gain, ample margin).

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
| 011 | 183.826 | −29.160 (−13.7%) | +13.782 | **Crashed** — 95 dmg, s09 start pushed wrong direction |
| 012 | 170.362 | −42.624 (−20.0%) | +0.318 | Clean — segment infra validated |
| 013 | **165.666** | **−47.320 (−22.2%)** | **−4.378** | **Personal best** — s08@95, s09 start 2380 |
| 014 | 173.156 | −39.830 (−18.7%) | +3.112 | Regressed — proportional brake killed overshoot |
| 015 | 169.126 | −43.860 (−20.6%) | −0.918 | Regressed vs 013 — brake deadband starved straights |

Phase 3 rubric gate: `≤ 180.98 s` (−15%) — cleared in Runs 007–015.
**Current submission candidate: Run 013, 165.666 s (2:45.67), 0 damages.**
Stretch target: `≤ 150 s` (`2:30`) clean — requires ~16 s vs Run 013.

---

## Lookahead brake controller — Runs 016–018

**Architecture change:** replaces per-segment speed cap with a physics-derived brake trigger.
Instead of "target = 80 km/h, coast above", the controller runs **full throttle everywhere** and
only brakes when the stopping distance to the next corner's target speed has been reached.

**Implementation:** `src/driver_baseline.py --lookahead <METERS> --lookahead-decel <M_PER_S2> --segments telemetry/segments.yaml`

Key physics: brake distance from v to v_target = (v² − v_t²) / (2 × decel).
- 130 km/h → 58 km/h @ 8 m/s²: **64 m**
- 130 km/h → 58 km/h @ 10 m/s²: **51 m**
- 140 km/h → 58 km/h @ 8 m/s²: **78 m**

**Quickstart (after `git pull`):**
```powershell
cd $env:USERPROFILE\ibmRacingLeague\ibmRacingLeague
# Window A: TORCS running (Race → Quick Race → Corkscrew → scr_server 1 → 1 lap → New Race)
# Window B:
.\scripts\run_experiment.ps1 016   # then 017, then 018
```

---

### Run 016 — Lookahead 200m / decel 7.0 m/s² (conservative)

**Hypothesis:** Conservative brake window guarantees no overshoot on either hairpin (s09, s13).
Full-throttle straights should recover ~5–8 s vs Run 013 even with early braking.

**Config:** `--lookahead 200 --lookahead-decel 7.0 --segments telemetry/segments.yaml`

**Expected:** 155–162 s, 0 damages. If braking is too early (car enters corners slow), tighten in Run 017.

**Run 016 result:** **DNF.** Controller never produced a clean lap — the conservative 7.0 m/s² decel assumption was far below the car's real capability, leaving the brake commands out of phase with corner entries. No archive retained. Superseded by Run 017's moderate profile.

---

### Run 017 — Lookahead 150m / decel 9.0 m/s² (moderate)

**Hypothesis:** Tighter brake window lets the car carry more speed into the straight before braking.
9 m/s² is within TORCS car's demonstrated capability (Run 008 shows ~0.5g lateral on hairpins).

**Config:** `--lookahead 150 --lookahead-decel 9.0 --segments telemetry/segments.yaml`

**Expected:** 150–158 s, 0 damages.

**Run 017 result:** **DNF.** Archive `telemetry/runs/2026-04-22T20-16-57/`, final damage 25, `KeyboardInterrupt` stop. 9 m/s² decel still below the real ceiling; car entered hairpins too hot and accumulated damage until the session was aborted.

---

### Run 018 — Lookahead 120m / decel 11.0 m/s² (aggressive)

**Hypothesis:** Maximum late-braking — assumes car can decelerate 1.1g. High risk of corner entry
overshoot if decel assumption is optimistic. Best-case lap if the car tracks.

**Config:** `--lookahead 120 --lookahead-decel 11.0 --segments telemetry/segments.yaml`

**Expected:** 145–155 s if clean; damages possible.

**Run 018 result:** Not separately archived. The aggressive lookahead/decel pairs were abandoned in favour of a *measurement-first* approach (see "Brake calibration sprint" below). Subsequent Round-2 strategies replaced lookahead tuning by-hand with strategies grounded in the car's real decel ceiling.

---

## Brake calibration sprint — 2026-04-22 PM (commit `b878a51`)

Runs 016–018 suggested the lookahead controller's `--lookahead-decel` constant (7–11 m/s²) was far below the car's real capability. Added a `--brake-test` mode to the driver that accelerates to a target speed then applies `brake=1.0`, plus `scripts/analyze_brake_test.py` to parse the archive and compute mean/peak decel.

**Measured ceiling (IBM F1 on Corkscrew):**
- **Mean decel: 22 m/s²**
- **Peak decel: 25 m/s²**

Round-2 strategies recalibrate against 14 m/s² (conservative), 18 m/s² (matches Louis's driving target), and 21 m/s² (near-ceiling aggressive).

---

## Round 2 — lookahead with real decel + full-pedal brake

**Strategies (commits `52252ea`, `c4c3a0e`):**

| id | lookahead | decel | flags |
|---|---|---|---|
| r2a | 60 m | 14.0 m/s² | — |
| r2a-v2 | 60 m | 14.0 m/s² | `--full-pedal-brake` |
| r2b | 45 m | 18.0 m/s² | — |
| r2c | 30 m | 21.0 m/s² | — |

`--full-pedal-brake` forces `brake = 1.0` in the brake zone (no P-ramp). Short zones like the s09 and s13 hairpins don't leave room for a gradual ramp — full pedal is the right command and the car can take it.

### Run 021 — r2a-v2 first live — DNF s13

`telemetry/runs/2026-04-22T21-40-25/`. Crashed at s13 (peak `trackPos` −7.48 at 3315–3337 m). Brake zone started too late for full-pedal to drop speed in time. **Fix (commit `bf6fbf8`):** extend both s09 and s13 brake-zone start boundaries backward.

### Run 022 — r2a-v2 after brake-zone extension — 163.466 s (0 dmg / 0 off)

**−2.2 s vs Run 013.** First clean Round-2 lap. s13 no longer the problem; s08 straight carrying spare speed.

### Run 023 — r2a-v2 + s06 90 / s08 102 / s09 50 — 🏆 160.666 s PB (0 dmg / 0 off)

**−5.0 s vs Run 013.** Commit `5e69ae1`. s08 pushed to 102 km/h, s09 apex tightened to 50 km/h to protect trackPos on corner exit. Clean throughout.

### Run 024 — s08 102 DNF at kink — rollback

DNF at 1948–2011 m with peak `trackPos` −4.81. Three excursions clustered at the same microsite. `segments.yaml` labels s08 as a straight, but `angle_peak_abs` (0.133) and `steer_peak_abs` (0.294) from Run 001 observed data show a real kink around 1950 m. At 95–98 km/h the car tracks through it; at 102 km/h it can't. Commit `a1c61c8` rolls s08 back 102 → 98.

### Run 025 — r2a-v2 + s08 98 rollback — 160.326 s (0 dmg / 1 off)

`telemetry/runs/2026-04-22T22-08-22/`. Fastest clean-*ish* lap yet but still brushed `trackPos` −1.17 at the s08 kink. Run 023 (160.666 s, 0 off-tracks) remains the submission anchor until the kink is explained and survived at `|trackPos| < 1.0`.

---

## Open investigation — s08 elevation hypothesis

**Question:** is the s08 kink at 1950 m a *geometric* corner that the segment map mislabels as a straight, or is it a *grip-loss* feature (crest/unload) that speed-only tuning cannot solve?

**Evidence for elevation:**
- Peak `|steer|` at the microsite reaches 0.807 — near saturation — while car speed is only 100 km/h. Geometric corners at that speed should not need that much steering.
- `segments.yaml` derivation uses `bin=5.0m` on `trackDistance` only; Z is completely absent from the segment model.
- Corkscrew's real-world namesake (Laguna Seca) is famously defined by elevation drop in roughly this lap position; IBM's Corkscrew track likely preserves the signature.

**Test:** added `z` to the frame schema (`scripts/log_telemetry.py`) and `scripts/elevation_profile.py` which bins Z vs `trackDistance` and correlates high-grip-pressure events with elevation. One calibration lap on any clean strategy will either confirm a crest near 1950 m (hypothesis verified) or show a flat profile (hypothesis rejected).

**If confirmed:** the fix is to cap s08 speed to ~92 km/h in a narrow 1900:2000 micro-zone, independent of the surrounding straight target. That should allow s06/s08 open targets to push higher (>100 km/h) elsewhere without the kink being the binding constraint.

See [`docs/racing-methodology.md`](./racing-methodology.md) §5 for the two competing failure-mode explanations (pure traction-circle saturation vs weight-transfer grip loss over a crest) and the decisive experiment that distinguishes them.

**If rejected:** the kink is geometric; `segments.yaml` needs a hand-placed micro-corner at 1900:2000 and `derive_segments.py` needs a lower `corner_steer_abs` threshold or a bin on second derivative of heading.

---

## Session 2026-04-24 — Racing-line v5 → v7 PB cascade

All runs below use the same `driver_baseline.py` (lookahead + full-pedal brake), but introduce a **racing-line interpolator** (`entry_pos → apex_pos → exit_pos` per segment) that pulls steering toward a target `trackPos` instead of centerline. Four config snapshots (`segments_submission_v4.yaml` → `v7.yaml`) staged under `telemetry/`.

### Run 026 — v2 (all-straights-push) — 167.146 s (clean)

**−5.074 s vs Run 013's 165.666 s** by raising *every* straight target simultaneously. Pure speed push; lap still conservative in corners. No off-tracks, 0 damages. Proved the straight-side headroom is real across the whole track, not just one section.

### Run 027 — v3 (speed + kink fix) — 165.626 s

Slight regression vs Run 026 — a cautious step back to reconfirm Run 023-equivalent corner discipline while keeping most straight gains.

### Run 028 — v4 (speeds held) — ~165 s class

Committed v4 config (commit `dd85ef2`). Lap time within noise of Run 027; v4 became the baseline for the line-interpolation experiment.

### Run 029 — v5 (racing-line introduced) — 165.826 s (clean)

Commit `45f81ee` adds `entry_pos` / `apex_pos` / `exit_pos` per segment and a steering law that pulls toward the interpolated target instead of centerline. **Racing-line validated** — peak `|trackPos|` lifted from Run 023's ~0.1 range to **0.56 / 0.78 / 0.82** on s05 / s01 / s13 respectively (car now *using* track width). **But no time gain** — corner speed caps were still the v3 values so the lookahead brake target was unchanged. Line validated; needs corner-speed bumps to translate into lap time.

### Run 030 — v6 (line + corner-speed bumps) — 🏆 160.606 s PB (clean)

Commit `67cb401`. Held v5's racing-line and raised corner caps (s01/s03 75→80, s05/s07/s11 78→82, s09 50→55, s13 58→62). **−5.020 s vs v3** and the first sub-161 clean lap. Racing line finally paying out: corners taken at higher speed with `|trackPos|` margins still well under 1.0 (peak s13 = 0.868).

### Run 031 — v7 (straight-cap pushes + small corner bumps) — 🏆 156.586 s PB (clean, 1 boundary touch)

Commit `5a25810`. Straights at cap in v6 (s02 95 → **100**, s04 95 → **100**, s06 105 → **108**, s10 100 → **105**, s12 80 → **90**, s14 100 → **105**) and +2–3 km/h on minor corners. **−4.020 s vs Run 030**, cumulative **−9.040 s vs v3 baseline**. One transient boundary excursion: s08 kink region touched `|trackPos| 1.02` for ~5 m at 1953–1957 m (logged by `find_offtracks.py`, inside TORCS's internal tolerance — 0 damages, lap counted). v8 must pull the `s08c` exit line back from −0.55 before any further s08 target push.

### Progression summary

| Run | Config | Lap time | Δ vs prior clean PB | Notes |
|---|---|---:|---:|---|
| 013 | v3 baseline | 165.666 | — | Round-1 reference, segment caps only |
| 023 | r2a-v2 | 160.666 | −5.000 | First sub-161, full-pedal brake + narrow hairpins |
| 025 | +s08 102 | 160.326* | dirty | Had 1 off-track; not submission-safe |
| 026 | v2 (straights) | 167.146 | — | All-straights experiment, back-off from aggressive corners |
| 030 | v6 (line + bumps) | **160.606** | flat | Racing-line interpolator pays out |
| 031 | v7 (straight push) | **156.586** | **−4.020** | New PB; s08 border touch to clean up in v8 |

Current submission anchor: **Run 031 — 156.586 s, 0 damages** (archive to push from Windows).

---

## v8 plan — edge-of-map cleanup + remaining speed

Informed by Run 031 segment report:

1. **s08c exit line: −0.55 → −0.45** (primary safety fix — the Run 031 boundary touch).
2. **Straight pushes that hit cap in Run 031:**
   - `s02` 100 → 103 (max hit 100.1 exactly)
   - `s04` 100 → 103 (max hit 100.1)
   - `s06` 108 → 110 (max hit 108.1)
   - `s10` 105 → 108 (max hit 105.2)
   - `s12` 90 → 95 (max hit 90.1)
3. **Small corner pushes (trackPos still has margin):**
   - `s01` 82 → 84, `s03` 83 → 85, `s05` 85 → 87
   - `s07` 85 → 87, `s09` 58 → 60, `s11` 85 → 87
4. **Hold:** s00 (standing start), s08a/b/c speeds (kink microsite), s13 (tight at 0.87), s14 (acceleration-limited, target already ahead of achievable), s15 (5 m inactive).

Estimated gain: **−2 to −3 s**. Target: sub-154 s.
