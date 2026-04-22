# IBM AI Racing League — TORCS Driver

Team **mdc-racing-league** entry for the IBM AI Racing League. Autonomous Python driver for TORCS that runs a single timed standing-start lap on **Corkscrew** with the IBM F1 car.

- **Submission deadline:** 2026-07-01
- **Submission form:** https://ibm.biz/TORCSForm
- **Competition rules & setup:** https://ibm.biz/TORCSQuickStart · https://ibm.biz/TORCSReference

---

## Current status (2026-04-22)

| Run | Config | Lap time | Damages | Status |
|---|---|---|---|---|
| 006 | 55 km/h everywhere (clean baseline) | 212.986 s | 0 | Geometry reference run |
| 007 | 80 km/h everywhere | 170.566 s | 41 | **Unsafe** — reference only |
| 008 | 80 km/h + two hand-placed 50 km/h slow zones (±100 m padding) | 175.106 s | 0 | Clean (superseded by 009) |
| 009 | 80 km/h + narrowed slow zones (±60 m padding) | **170.044 s** | 0 | **Clean reference** |
| 010 | 80 km/h + full 16-segment map | pending (predicted ~170.8 s) | — | First `--segments` run |

**Phase 3 rubric gate** (`≤ 180.98 s`, −15% vs clean baseline): **cleared**.
**Stretch target** (`≤ 150 s`, 2:30 clean): ~20 s below current reference.

Full iteration log: [`docs/phase3-experiments.md`](docs/phase3-experiments.md)
Phase plan + risks: [`docs/roadmap.md`](docs/roadmap.md)
Run 009 per-segment breakdown: [`telemetry/runs/2026-04-21T22-42-18/segment_report.md`](telemetry/runs/2026-04-21T22-42-18/segment_report.md)

---

## What's in this repo

```
.
├── src/
│   └── driver_baseline.py        # P-controller driver, SCR/snakeoil3 UDP client
├── scripts/
│   ├── run_race.py               # Launch driver against a running scr_server
│   ├── log_telemetry.py          # TelemetryLogger library (schema v0.2)
│   ├── validate_run.py           # Validator for archived runs
│   ├── find_offtracks.py         # Report trackPos excursions ≥ threshold
│   ├── derive_segments.py        # Build segments.yaml from a clean run
│   ├── segment_report.py         # Per-segment table for a run
│   └── ab_run.py / label_segments.py / baseline_controller.py
├── tests/                        # pytest — 19 passing
├── telemetry/
│   ├── SCHEMA.md                 # Telemetry v0.2 frame schema
│   ├── segments.yaml             # 16-segment Corkscrew map (derived from Run 006)
│   ├── baseline.md               # Run ledger (006–009 archived)
│   └── runs/<timestamp>/         # Per-run frames.ndjson + manifest.json
├── docs/
│   ├── roadmap.md                # Phase plan, deadlines, velocity buffer
│   ├── phase3-experiments.md     # Controller tuning log, Run 010 plan
│   ├── setup.md / dev-environment-summary.md
│   ├── simulation-guide/         # Day-to-day runbook
│   ├── competition-plan.md / driver-architecture.md / action-items.md
│   └── telemetry-integration.md / granite-validation.md
├── web/team-name-poll/           # Anonymous ranked-choice team-name poll
└── NAVIGATION.md                 # Full file-by-file index
```

---

## Getting started (new teammate)

1. **Read first, in this order (~20 min):**
   1. This README
   2. [`docs/roadmap.md`](docs/roadmap.md) — phase plan and where we are
   3. [`docs/phase3-experiments.md`](docs/phase3-experiments.md) — what we've tried, what's next
2. **Set up your environment:** [`docs/setup.md`](docs/setup.md) · [`docs/dev-environment-summary.md`](docs/dev-environment-summary.md)
3. **Run the sim once end-to-end:** [`docs/simulation-guide/01-quickstart.md`](docs/simulation-guide/01-quickstart.md)
4. **Look at one full run archive:** `telemetry/runs/2026-04-21T22-42-18/` (Run 009) — open `manifest.json`, glance at `frames.ndjson`, read `segment_report.md`.

Unsure where a file lives? [`NAVIGATION.md`](NAVIGATION.md) is a file-by-file index.

---

## Running the driver

On the Windows machine, with TORCS already loaded and `scr_server 1` as the selected driver:

```
# Simple run (legacy — 55 km/h everywhere)
python src\driver_baseline.py

# With a target speed + hand-placed slow zones (how Runs 008/009 were driven)
python src\driver_baseline.py ^
  --target-speed 80 ^
  --slow-zone 2420:2540:50 ^
  --slow-zone 3220:3320:50 ^
  --notes "Run 009 - narrow zones"

# With the full segment map (Run 010 and onward)
python src\driver_baseline.py ^
  --target-speed 80 ^
  --segments telemetry\segments.yaml ^
  --notes "Run 010 - --segments full map"
```

Each run auto-archives telemetry to `telemetry/runs/<timestamp>/`. After the run:

```
python scripts\validate_run.py telemetry\runs\<timestamp>
python scripts\find_offtracks.py telemetry\runs\<timestamp>
python scripts\segment_report.py telemetry\runs\<timestamp>
```

---

## Submission requirements tracked

Reference: https://ibm.biz/TORCSForm (12 fields, incl. livery + SkillsBuild badges slides).

- [x] GitHub repository (this repo)
- [x] Clean lap on Corkscrew (Run 009, 2:50.04)
- [ ] Fastest-lap video with university + team name overlay
- [ ] Team intro video (roles, approach, Granite + SkillsBuild usage)
- [ ] Livery assets
- [ ] SkillsBuild badges slides

---

## Useful links

- **TORCS reference bundle:** https://ibm.box.com/v/TORCSReference
- **Quick start guide:** https://ibm.biz/TORCSQuickStart
- **Ollama/Granite install:** https://ibm.biz/TORCSnewGraniteSW · https://ibm.box.com/v/TorcsOllamaInstructions
- **Submission form:** https://ibm.biz/TORCSForm
- **Team Discord:** https://discord.gg/KXhqwKqnB2
- **Team-name poll (in-repo):** [`web/team-name-poll/`](web/team-name-poll/)
