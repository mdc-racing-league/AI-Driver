# IBM Racing League — File Navigation Guide

> **Submission deadline: 2026-07-01** | Registration: https://ibm.biz/RegistrationTORCS | Submission form: https://ibm.biz/TORCSForm

This document is your single entry point for navigating the project. Everything lives inside this folder — nothing related to the IBM Racing League should exist outside `ibmRacingLeague/`.

---

## Quick-start by intent

| I want to… | Go here |
|---|---|
| Set up the environment for the first time | `docs/setup.md` |
| Run the sim today (already set up) | `docs/simulation-guide/01-quickstart.md` |
| Check current phase and what's next | `docs/roadmap.md` |
| See open action items / blockers | `docs/action-items.md` |
| Understand the full competition plan | `docs/competition-plan.md` |
| Read the driver architecture | `docs/driver-architecture.md` |
| Wire up telemetry end-to-end | `docs/telemetry-integration.md` |
| Know which Granite model to use | `docs/granite-validation.md` |
| Read the telemetry field schema | `telemetry/SCHEMA.md` |
| Look at past run data | `telemetry/` |
| Debug a runtime issue | `docs/simulation-guide/06-troubleshooting.md` |
| View the Phase 1 smoke-test screenshot | `docs/screenshots/` |

---

## Full folder map

```
ibmRacingLeague/
│
├── NAVIGATION.md              ← YOU ARE HERE
├── README.md                  ← Project overview + repo layout + strategy summary
├── poll-data.json             ← Team name poll results (drives web/team-name-poll/)
│
├── docs/                      ── All written documentation
│   ├── roadmap.md             ← Phase tracker + velocity buffer + risks (update frequently)
│   ├── setup.md               ← One-time environment setup (TORCS, Python, Ollama, Granite)
│   ├── granite-validation.md  ← Granite model test results + which model to use when
│   ├── dev-environment-summary.md  ← Snapshot of confirmed working environment
│   ├── phase1-kickoff.md      ← Apr 27 team sync agenda (strategy + SCHEMA walk-through)
│   ├── action-items.md        ← Live blockers + owner + due date (check daily)
│   ├── competition-plan.md    ← Phase-by-phase strategy: Phase 1 → Phase 3
│   ├── driver-architecture.md ← Perception → Planning → Control pipeline + RL setup notes
│   ├── telemetry-integration.md ← Step-by-step: TORCS → log → controller → RL agent
│   │
│   ├── simulation-guide/      ── Day-to-day sim runbook (read in order once, then reference)
│   │   ├── README.md          ← Guide index + when to use each section
│   │   ├── 01-quickstart.md   ← Fastest path from cold boot to car on track
│   │   ├── 02-launching-torcs.md
│   │   ├── 03-running-our-driver.md  ← SCR/snakeoil3 Python UDP client setup
│   │   ├── 04-capturing-telemetry.md
│   │   ├── 05-granite-workflow.md    ← Using Granite via Ollama + continue.dev in VSCode
│   │   └── 06-troubleshooting.md
│   │
│   ├── screenshots/           ← Evidence archive (smoke tests, milestone proofs)
│   │   └── 2026-04-21_phase1-smoke-test-success.png
│   │
│   ├── TORCSRegtoSubmission0901-Mission Brief-Detailed (1).pdf  ← Official IBM brief
│   └── Wtorcs-ollama-instructions.pdf  ← IBM Ollama integration instructions
│
├── src/                       ── Driver source code (Phase 2+)
│   └── (driver_baseline.py goes here — Phase 2 deliverable)
│
├── scripts/                   ── Race orchestration + data pipeline scripts
│   ├── run_race.py            ← Orchestrates TORCS + Python client (Phase 2 impl pending)
│   ├── log_telemetry.py       ← Reads raw.log → normalized frames.csv
│   ├── validate_run.py        ← ✅ Full impl — validates a run against SCHEMA v0.2
│   ├── label_segments.py      ← Skeleton — tags telemetry frames with Corkscrew segment IDs
│   ├── ab_run.py              ← Skeleton — A/B comparison harness for two drivers
│   ├── baseline_controller.py ← Early heuristic controller (pre-snakeoil3 baseline)
│   └── env_check.sh           ← Diagnoses TORCS + Python + Ollama environment, writes to logs/
│
├── telemetry/                 ── All race data (never delete, never overwrite)
│   ├── SCHEMA.md              ← Canonical field definitions v0.2 — read before logging anything
│   ├── raw.log                ← Live TORCS telemetry output (ephemeral, tailed by scripts)
│   ├── baseline-commands.log  ← Actions logged by baseline controller (seed for RL warm-start)
│   └── segments.txt           ← Corkscrew segment map draft (18 segment IDs — Phase 3 will tune)
│
├── tests/                     ── Test suite
│   ├── test_validate_run.py   ← ✅ 20 unit tests for validate_run.py (all passing)
│   └── fixtures/              ← Synthetic run data used by tests
│
├── logs/                      ── Runtime process logs (for debugging, not submission)
│   ├── torcs-run.log
│   ├── torcs-headless.log
│   ├── telemetry-logger.log
│   ├── baseline-controller.log
│   └── env-check-*.log        ← Environment diagnostic snapshots
│
├── web/                       ── Web assets
│   └── team-name-poll/        ← React + Hono voting app (team name resolver)
│       ├── README.md
│       ├── pages/team-name.tsx
│       └── api/               ← team-name.ts / team-name-vote.ts / team-name-add.ts
│
├── assets/                    ── Static images and media
│   └── racing-bg.png
│
├── blog/                      ── Phase 4 blog drafts (empty until Phase 4)
│
├── videos/                    ── Submission video assets (Phase 4)
│   └── (store as <timestamp>-<description>.mp4)
│
└── backups/                   ── Archived snapshots (do not use for active work)
    └── ibmRacingLeague-zip-latest.zip
```

---

## Phase status at a glance

See `docs/roadmap.md` for the authoritative tracker. Summary as of **2026-04-21**:

| Phase | Window | Status |
|---|---|---|
| Phase 0 — Foundation | Apr 19–26 | ✅ Nearly complete (team registration pending Friday) |
| Phase 1 — Env setup & code prep | Apr 21 – May 3 | ✅ Track A done · Track B done · +7 days ahead of original plan |
| Phase 2 — Baseline AI driver | Apr 30 – May 14 | ⬜ Day 1 smoke test ✅ — `src/driver_baseline.py` is next |
| Phase 3 — Performance tuning | May 15 – Jun 4 | ⬜ Not started |
| Phase 4 — Polish & differentiate | Jun 5 – Jun 21 | ⬜ Not started |
| Phase 5 — Dry run & submit | Jun 22 – Jul 1 | ⬜ Not started |

---

## Key rules

1. **Telemetry is never overwritten.** Every run goes in `telemetry/` with a timestamped name. See `telemetry/SCHEMA.md` for required fields.
2. **Every run must pass validation before commit.** Run `python scripts/validate_run.py <run-folder>` — it must exit 0.
3. **`docs/action-items.md` is the blocker list.** If something is broken, log it there with an owner and due date.
4. **`docs/roadmap.md` is the schedule.** All phase-boundary decisions go there.
5. **Nothing IBM Racing League-related lives outside this folder.** If you find orphaned files in the workspace root, move them here.

---

## Submission checklist (Phase 5 reference)

- [ ] `src/driver_baseline.py` completes a clean Corkscrew lap
- [ ] 5-lap average run passes `scripts/validate_run.py`
- [ ] Fastest-lap video recorded (uni + team name overlay for full duration)
- [ ] Team intro video recorded
- [ ] Blog published (Medium or WordPress) hitting all 9 rubric points
- [ ] Submission form filled: https://ibm.biz/TORCSForm — **by June 28**
