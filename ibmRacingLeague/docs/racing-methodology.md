# Racing methodology — reference

Practical physics and TORCS-specific engineering notes used to guide per-lap
experiments. Cross-referenced from `docs/phase3-experiments.md` and
`telemetry/baseline.md`.

Sources at the bottom.

---

## 1. Tire physics — the fundamentals

### Understeer vs oversteer
- **Understeer:** front tires lose grip first. Car pushes wide. Lift throttle
  or *reduce* steering input to let the front re-grip. Adding more steering
  here makes it worse.
- **Oversteer:** rear tires lose grip first. Tail swings out. Counter-steer
  and modulate throttle. Panic-braking makes it worse.

For a FR/MR car with big lateral load (IBM F1 on Corkscrew), the default
failure mode at corner entry under trail-braking is **oversteer**; on corner
exit under power it's **power-on oversteer**. Both show up in telemetry as
`|trackPos|` spiking past ±1.0.

### The traction circle — the central constraint
A tire has a single pool of grip (~100% total capacity). That pool is split
between **lateral** (turning) and **longitudinal** (braking/accelerating)
force. Demanding 70% lateral + 70% longitudinal exceeds 100% total and the
tire slides.

Operational consequence:
- **Straight-line braking:** spend 100% of grip on deceleration → max brake.
- **Cornering:** as you add steering, subtract longitudinal demand.
- **Corner exit:** as you straighten the wheel, you can add throttle.

This is why `--full-pedal-brake` is correct for straight hairpin approach
(s09, s13 in our map) but **wrong for a kink mid-straight** (s08 at ~1950 m):
at a kink you need lateral grip from tires that are already at 100% long.

### Weight transfer
Weight shifts in three axes and unloads/loads tires accordingly:
- **Forward under braking** → more front grip, less rear (rear can lift)
- **Rearward under acceleration** → more rear grip, less front
- **Sideways in corners** → outside tires loaded, inside unloaded
- **Vertical over crests/dips** → unloaded at top, loaded at bottom

Crest → tires lose vertical load → lose grip → same steering input now exceeds
traction capacity. This is the mechanism behind the **s08 elevation
hypothesis** (see §5).

### Trail braking
Release brake progressively as steering increases so the sum (lateral demand +
longitudinal demand) stays inside the traction circle through corner entry.
Contrast with full-pedal-release: you're 0% braking at the same moment you're
100% turning, which wastes braking distance you could have spent trail-braking
deeper into the corner.

### The cornering line — "slow in, fast out"
- **Geometric apex:** hits the middle of the turn. Wastes exit speed.
- **Late apex:** enter wide, turn in later, clip the curb after the geometric
  apex. Lets you **straighten the wheel earlier on exit → earlier throttle →
  higher speed down the following straight.**

For Corkscrew, this matters most for s09 (the slow hairpin at 2500 m, exit
leads onto the long s10 straight) and s13 (leads onto s14 straight).

### Multiple corners as one
A sequence of closely-spaced corners (an "esses" complex) is solved as a
single problem: sacrifice apex speed on the first to set up optimal exit
through the last. Applicable to Corkscrew's s01+s03 chain and s05+s07 chain.

---

## 2. TORCS sensors and physics

### Available sensors (from Ahura §II-A and TORCS-Keras)

| Sensor | Range | What we use |
|---|---|---|
| `track[0..18]` proximity (19 rays, ±90°) | 0–200 m | `distance_to_edge_left/right` (rays 0 and 18); full ray set logged as `track_sensors` |
| `opponents[0..35]` (every 10°, full 360°) | 0–200 m | `opponentMinDistance` |
| `trackPos` (−∞..+∞; ±1 = edge) | — | `trackPosition` |
| `distFromStart` | 0..lap length | `trackDistance` — **primary index** for segment lookup |
| `angle` (car heading vs track axis, radians) | −π..+π | `angle_to_track_axis` |
| `speedX / speedY / speedZ` (m/s) | — | `speed` (longitudinal only) |
| `wheelSpinVel[0..3]` | — | `wheel_spin_velocity_avg` |
| `rpm` | 0..10000 | `rpm` |
| `gear` | −1..6 | `gear` |
| `damage` | 0..10000 | `damage` |
| `fuel` | — | `fuel` |
| `z` (altitude, m) | — | **added 2026-04-22 for elevation hypothesis** |

Control loop runs at a fixed **22 ms tick** in TORCS 1.3.4 (Ahura §II-A).
A slow controller causes delayed actuation, which desyncs the control law
from the plant.

### Turn-angle estimation from proximity sensors (Ahura §III-A-1)
Three rays are enough to estimate the angle of the turn ahead:

```
given θ = 1° (angle between adjacent rays), and rays dist_{-1}, dist_0, dist_1:

if dist_1 > dist_0:
    k = sin(θ)·dist_1 / (dist_0 − cos(θ)·dist_1)
else:
    k = sin(θ)·dist_0 / (dist_{-1} − cos(θ)·dist_0)

estimatedTurn = atan(k)
```

This is a cheap alternative to a pre-built segment table. We don't use it
(we use `segments.yaml`), but it's the right fallback if we ever want a
track-agnostic driver.

### Target-speed formula (Ahura Eq. 4)
```
targetSpeed = (dist_0 / maxD)^λ · (maxS − minS) + minS
```
- `dist_0` = center ray distance (m)
- `maxD` = 200 (TORCS proximity range)
- `maxS, minS` = car-specific max/min (Ahura uses 360 / 25 km/h)
- `λ` = curve exponent (sharper turn → higher λ → more cautious ramp)

λ is a function of `estimatedTurn` (Ahura §III-B-1): sharp turns → large λ.

We currently use a hard-coded per-segment `target_speed_kmh`. The Ahura
formula would let us derive target speed from look-ahead distance alone —
useful if segment-table maintenance becomes painful.

### Pedal mapping from one variable (Ahura Eq. 5)
```
p = 2 / (1 + e^(b·(xSpeed − targetSpeed))) − 1
```
- `p < 0`: `brakePedal = |p|`, throttle = 0
- `p ≥ 0`: throttle = `p`, brake = 0

One smooth signal controls both pedals, with `b=1.0` by default. Avoids the
"simultaneous brake + throttle" pathology that TORCS-Keras had to fight with
Ornstein-Uhlenbeck noise.

### ABS / ASR (Ahura §III-B-2)
Computed wheel-slip residual:
```
d = | xSpeed − Σ r_i · wheelSpinVel[i] / 4 |
```
(r_i = wheel radius; 0.3179 m front, 0.3276 m rear for the reference cars)

- **ABS** (during brake, `d > ABSSlip`):
  `brakePedal −= (d − ABSSlip) / ABSrange`
- **ASR** (during throttle, `d > ASRSlip`):
  `accelPedal += (ASRSlip − d) / ASRrange` *(note: Ahura's Eq.
  for ASR drives `p` toward smaller; same effect)*

If we ever see wheel spin blowing up on corner exit, this is the fix — and
it's three lines.

### Opposite sliding (Ahura §III-A-3) — the TORCS name for late apex
> "To minimize the steer angle ... the vehicle needs to take the largest
> curve that in fact requires starting the turn from the further edge of the
> track." — Ahura, Fig. 3

Set the **tentative position** α > 1 (or < 1) before the turn to drift the
car to the outside, then turn in late. Directly maps to GT2's late-apex
advice.

---

## 3. Controller architecture (Ahura's 5 modules)

Useful as a reference blueprint — our `driver_baseline.py` is a simpler
variant of this with most of modules 3–5 unimplemented.

| Module | Purpose | Our analogue |
|---|---|---|
| **Steer controller** | Weighted average of proximity rays to choose steer angle | `_segment_steer_target()` with per-segment override |
| **Speed controller** | Target-speed curve + ABS/ASR pedal mapping | `segments.yaml` `target_speed_kmh` + lookahead brake |
| **Opponent manager** | Build spatial map of opponents, find vacant slots, overtake | **not implemented** (solo timed lap — not needed for Phase 3) |
| **Dynamic adjuster** | Estimate friction from wheel-slip residual during run; revise λ/targets | **not implemented** (Corkscrew has constant friction) |
| **Stuck handler** | Detect off-track stuck; reverse + re-orient | Partial — `DNF` currently, no recovery logic |

**Decision:** we do not need the opponent manager or dynamic adjuster for a
single standing-start lap on a fixed dry track. Parking that complexity keeps
the driver readable.

Tuning strategy Ahura uses: **CMA-ES** (Covariance Matrix Adaptation
Evolutionary Strategy) for 23 parameters. We use manual per-segment search
because our parameter space is smaller (one speed per segment) and an
evolutionary run would exceed our testing budget (hundreds of laps).

---

## 4. Learning from TORCS-Keras (DDPG)

Not our approach — but the paper documents TORCS dynamics we can borrow:

- **Reward pathology:** pure longitudinal-velocity reward is unstable →
  agent slides sideways fast rather than driving forward. **Fix: penalize
  lateral velocity and off-center position.** Applicable to our objective
  function if we ever run parameter search (`lap_time + α·damage + β·peak|trackPos|`).
- **Simultaneous brake+throttle:** emerges from naive exploration. We
  structurally rule this out by using the Ahura single-variable pedal
  mapping (§2) rather than two independent pedals.
- **Brake-action local minimum:** an agent that never brakes eventually
  crashes; an agent that often brakes never accelerates enough to build
  reward. Manifests for us as **damage-vs-lap-time Pareto curves** — our
  Run 007 (no-zone, fast, damaged) vs Run 008 (zoned, clean, slower) is
  exactly this trade-off.
- **Generalization:** train on one track, test on another. Since our
  judging lap is Corkscrew-specific, we do not need this — but it also
  means our segment tuning **will not transfer to other IBM tracks** if the
  league ever expands.

---

## 5. Application to current Corkscrew investigation

### s08 kink at ~1950 m (Runs 024/025 off-tracks)
Observed in Run 001 (segments.yaml observed data): `angle_peak_abs` 0.133,
`steer_peak_abs` 0.294 at **55 km/h, 0 off-track**.
Observed in Run 025: `|steer|` near-saturation **0.807** at **~100 km/h, 1
off-track (trackPos −1.17)**.

Two non-exclusive explanations:

1. **Pure traction-circle saturation (§1).** Same geometry at higher speed
   needs more lateral force → tire at 100% lateral → any longitudinal
   perturbation (even rolling resistance, throttle blip) pushes outside the
   circle.
   - **Fix:** cap s08 target at ~95 km/h (the highest speed where
    `steer_peak` stayed < 0.4).

2. **Weight-transfer grip loss over a crest (§1).** If `z` drops at 1950 m,
   tires unload → grip pool shrinks → the same demand overruns it.
   - **Fix:** carve the kink out as its own mini-segment with its own lower
     target, regardless of overall s08 speed.
   - **Decisive experiment:** already instrumented. Next lap with z-logging
     → `python scripts/elevation_profile.py telemetry/runs/<ts>/` → inspect
     the 1850–2100 m zoom window. If `net entry→exit` drops by >0.5 m, the
     crest is real.

### s09 hairpin (2500 m) and s13 hairpin (3272 m)
GT2 §1 and Ahura §III-A-3 both say: **start wide, late apex, straighten
early, full throttle.** We currently brake to 50 km/h for s09 and 58 km/h
for s13 using a straight-line deceleration model. That is correct for entry
speed control but **we never modulate trajectory** (i.e. α in Ahura's
weighted-average steer formula stays ~1.0).

Low-cost experiment if s08 is resolved and we have iterations left:
- Before s09 brake zone, bias trackPos toward the outside (+0.5) so entry
  is wider.
- Let the natural steer re-attraction pull the car in toward the apex.
- Measure: does `speed_min` through s09 rise? Does `trackDistance_to_full_throttle`
  shorten on s10?

### Trail braking vs `--full-pedal-brake`
Current r2a-v2 strategy uses full pedal until the zone ends, then releases.
GT2 §1 and Ahura Eq. 5 both describe a **smooth** brake release coupled to
steering. Cost of full-pedal: we overbrake by ~0.2–0.5 s per hairpin
because the last 20 m of the zone is at 0% steering + 100% brake when it
could be 30% steering + 30% brake (both contributions within the circle).

Only worth revisiting after the s08 kink is fixed — s08 dominates the
remaining time budget.

### Brake zone as one or many
Corkscrew's s01+s03 and s05+s07 are close enough to treat as single
problems per GT2. Currently we treat them as independent; this is a
structural limit of the per-segment `target_speed_kmh` model. Not a
priority unless s08 and the hairpin lines are both solved.

---

## Sources

- **Gran Turismo 2 Reference Manual** (USA edition) — PS1 game manual,
  pp. 16–27 cover the physics primer cited in §1. Local copy:
  `/home/.z/chat-uploads/Gran Turismo 2 [Reference Manual] (USA)-400d923e10eb.pdf`
- **Ahura: A heuristic-based racer for TORCS** — Bonyadi, Michalewicz,
  Nallaperuma, Neumann. *IEEE Transactions on Computational Intelligence
  and AI in Games.* Primary source for §2 and §3 equations. Local copy:
  `/home/.z/chat-uploads/Ahura-Car-24c0db36cee1.pdf`
- **TORCS-Keras DDPG writeup** — Yan-Pan Lau, 2016.
  https://yanpanlau.github.io/2016/10/11/Torcs-Keras.html
- **Jeremy Bennett's TORCS mirror** — https://github.com/jeremybennett/torcs
  (mirror of the upstream CVS tree; no fork-specific changes, useful as a
  readable source-code reference for sensor/actuator internals)
- **TORCS man page** — https://www.venea.net/man/torcs(6)#man_download
  (see `torcs(6).txt` download for full options listing)
- **UPV F1-car tutorial** — https://personales.upv.es/vimarce1/tutorials/torcs/car.html
  (3D modeling / `.ac`→`.acc` conversion only — **not physics**, noted for
  completeness)
