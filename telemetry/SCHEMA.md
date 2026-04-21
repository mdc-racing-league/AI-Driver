# Telemetry Schema

> Strategic goal: make our telemetry our **competitive moat**. Every other team has the same sim, same Granite models, same track. What we own is the density and labeling of our own run data. See "Data advantage" section in `docs/roadmap.md` for the why.

This file is the **single source of truth** for what we log and how. Lock it in Phase 1; enforce it via a validator in Phase 2. Every teammate's logger must conform so runs are comparable across machines.

---

## Design principles

1. **Log more than you think you need.** Disk is cheap; re-running laps isn't.
2. **Every signal is timestamped and segment-tagged.** So we can slice any run by track section.
3. **Never overwrite a run.** Archive under `telemetry/runs/<timestamp>/`.
4. **Machine-readable first, human-readable second.** Newline-delimited JSON for raw; CSV for derived frames.
5. **Schema versioned.** Bump `schema_version` on any change so old runs stay interpretable.

---

## Current schema version: `v0.2` (draft)

`v0.1` = the 9 fields currently emitted by the starter logger
(`time, speed, rpm, trackPosition, trackDistance, opponentMinDistance, throttle, brake, steer`).
`v0.2` extends this — **additions only, no removals** — so v0.1 data stays valid.

---

## Per-frame fields (newline-delimited JSON, one object per sim tick)

### Core kinematics (inherited from v0.1)

| Field | Type | Unit | Notes |
|---|---|---|---|
| `time` | float | seconds | Sim time since lap start |
| `speed` | float | m/s or km/h (document which) | Forward speed |
| `rpm` | int | rev/min | Engine RPM |
| `trackPosition` | float | unitless, `-1..1` | Lateral offset from track centerline |
| `trackDistance` | float | meters | Distance traveled along centerline |
| `opponentMinDistance` | float | meters | Closest opponent; `null` if solo run |
| `throttle` | float | `0..1` | |
| `brake` | float | `0..1` | |
| `steer` | float | `-1..1` | Positive = left (confirm with TORCS docs) |

### Extended signals (new in v0.2)

| Field | Type | Unit | Why we're adding it |
|---|---|---|---|
| `schema_version` | string | — | e.g. `"v0.2"`. First frame of every run. |
| `run_id` | string | — | UUID per lap run; same value on every frame of that run |
| `segment_id` | string | — | Track-segment label (see segment map below) |
| `lap_number` | int | — | 1-indexed; supports multi-lap runs |
| `gear` | int | — | Current gear |
| `tire_slip_fl` | float | unitless | Slip ratio front-left |
| `tire_slip_fr` | float | unitless | Front-right |
| `tire_slip_rl` | float | unitless | Rear-left |
| `tire_slip_rr` | float | unitless | Rear-right |
| `wheel_spin_velocity_avg` | float | rad/s | Averaged across 4 wheels |
| `z_accel` | float | m/s² | Vertical accel — catches elevation events on Corkscrew |
| `lateral_g` | float | g | For cornering load analysis |
| `angle_to_track_axis` | float | rad | Car yaw vs. track tangent |
| `damage` | float | — | TORCS damage counter |
| `fuel` | float | liters | |
| `distance_to_edge_left` | float | meters | Track-edge sensor |
| `distance_to_edge_right` | float | meters | |
| `track_sensors` | array[float] | meters | Full 19-beam rangefinder array (if available) |

### Controller decision metadata (new in v0.2)

Every controller action carries *why* it chose that action. This is what lets Granite reason over our history.

| Field | Type | Notes |
|---|---|---|
| `controller_type` | string | `"baseline"`, `"pid"`, `"lookup"`, `"granite_suggested"`, etc. |
| `controller_variant_id` | string | Git commit SHA or semver of the controller code |
| `controller_reason` | string | Short tag, e.g. `"apex_brake"`, `"exit_throttle"`, `"recovery"` |
| `pid_terms` | object | `{p: float, i: float, d: float}` if PID controller |
| `lookup_hit` | string? | Segment-table key that fired, if lookup-based |

---

## Per-run manifest (one JSON file per run)

Path: `telemetry/runs/<timestamp>/manifest.json`

```json
{
  "run_id": "uuid-v4",
  "schema_version": "v0.2",
  "started_at": "2026-05-04T14:22:13-04:00",
  "ended_at":   "2026-05-04T14:24:01-04:00",
  "track": "corkscrew",
  "car": "car1-trb1",
  "weather": "clear",
  "driver": "louis",
  "controller_type": "pid",
  "controller_variant_id": "abc1234",
  "baseline_ref": "runs/2026-05-01T12-00-00/",
  "outcome": {
    "completed": true,
    "crashed": false,
    "laps_completed": 1,
    "best_lap_seconds": 87.42,
    "total_time_seconds": 87.42,
    "final_damage": 0
  },
  "notes": "Granite suggested widening entry on turn 6; applied."
}
```

---

## Per-run derived artifacts

| File | Purpose |
|---|---|
| `frames.ndjson` | Raw per-tick frames, schema above |
| `frames.csv` | Flattened CSV for quick spreadsheet/pandas work |
| `segments.csv` | One row per segment traversal: segment_id, time_in, time_out, delta_vs_baseline_s, max_lateral_g, min_speed, crashed_in_segment |
| `summary.md` | Human-readable: lap time, segment-by-segment deltas, notes |

---

## Track segment map (Corkscrew)

Lock this list in Phase 2. Suggested starter IDs:

| segment_id | Description |
|---|---|
| `s00_start_straight` | Start/finish straight |
| `s01_turn1_entry` | Approach to turn 1 |
| `s02_turn1_apex` | Turn 1 apex |
| `s03_exit_to_turn2` | Short chute |
| ... | (fill in from track map during Phase 3) |
| `s14_corkscrew_entry` | Namesake sequence entry |
| `s15_corkscrew_drop` | Elevation drop |
| `s16_corkscrew_exit` | Recovery |
| `s17_final_straight` | Back to start |

A helper in `scripts/segment_tagger.py` should assign `segment_id` per frame by distance-along-centerline bucketing. Write this once; every teammate uses the same tagger.

---

## Labeling rules (the "engagement metrics" layer)

After a run completes, auto-compute and write to `segments.csv`:

- **`delta_vs_baseline_s`** — time in segment minus baseline mean for same segment
- **`improvement`** — boolean, true if delta is negative (faster)
- **`confidence`** — stddev of steering output in segment; low stddev = smoother control
- **`crashed_in_segment`** — boolean
- **`granite_influenced`** — boolean, true if the controller variant used a Granite-suggested change, linking back to `docs/granite-suggestions.md`

This turns the `runs/` folder from a log archive into a **labeled dataset**. Granite code-review sessions in Phase 3 can then ingest `segments.csv` across many runs and find patterns — which is exactly the "own your own training data" advantage the strategy is built around.

---

## Validation

`scripts/validate_run.py` (to be written in Phase 2) should check:

1. Every frame has `schema_version`, `run_id`, `time`, `segment_id`
2. `run_id` is consistent across all frames in a file
3. `time` is monotonically non-decreasing
4. `segment_id` values all exist in the canonical segment map
5. Required fields per schema version are present (null is allowed where marked)

CI hook: running `validate_run.py` on a new `runs/<timestamp>/` directory must pass before the run gets merged into the leaderboard.

---

## Changelog

- **v0.2 (2026-04-20, draft)** — Added extended sensors, controller decision metadata, per-run manifest, segment labeling, validation rules.
- **v0.1 (starter)** — 9 fields emitted by `scripts/log_telemetry.py`.
