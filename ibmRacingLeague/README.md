# IBM Racing League — TORCS / Granite Team Repo

Our entry for the IBM Racing League TORCS competition. Autonomous driver for the Corkscrew track, developed with IBM Granite via Ollama + continue.dev.

- **Submission deadline:** 2026-07-01
- **Team registration:** https://ibm.biz/RegistrationTORCS
- **Official submission form:** https://ibm.biz/TORCSForm

---

## Where to start

| You are... | Read |
|---|---|
| A new teammate setting up for the first time | `docs/setup.md` |
| Ready to run the sim (already set up) | `docs/simulation-guide/` |
| Trying to understand the project plan | `docs/roadmap.md` |
| Looking for our competitive strategy | `docs/roadmap.md` → "Data advantage" section |
| Wondering which Granite model to use | `docs/granite-validation.md` |
| Writing or reading telemetry code | `telemetry/SCHEMA.md` |

---

## Repo layout

```
ibmRacingLeague/
├── README.md                  # You are here
├── docs/
│   ├── roadmap.md             # Phase plan, risks, strategy
│   ├── setup.md               # One-time environment setup
│   ├── granite-validation.md  # Granite model test results + selection rules
│   ├── simulation-guide/      # Day-to-day runbook
│   │   ├── README.md          # Guide index
│   │   ├── 01-quickstart.md
│   │   ├── 02-launching-torcs.md
│   │   ├── 03-running-our-driver.md
│   │   ├── 04-capturing-telemetry.md
│   │   ├── 05-granite-workflow.md
│   │   └── 06-troubleshooting.md
│   ├── TORCSRegtoSubmission0901-Mission Brief-Detailed (1).pdf
│   └── Wtorcs-ollama-instructions.pdf
├── src/                       # Our driver code (populated in Phase 2)
├── scripts/                   # Race / telemetry / validation / A-B scripts
├── telemetry/
│   ├── SCHEMA.md              # Canonical telemetry schema (v0.2)
│   ├── raw.log                # Live tailed output (ephemeral)
│   └── runs/                  # Archived, labeled per-run datasets
├── blog/                      # Phase 4 blog drafts
├── videos/                    # Phase 4 video assets
├── assets/                    # Images, backgrounds, etc.
└── web/                       # Team-name poll + any web assets
```

---

## Strategy in one paragraph

Every team has the same TORCS sim, the same starter code, and the same IBM Granite models. Public data is a level playing field. Our moat is the **density and labeling** of telemetry we generate from our own laps — we log more signals, archive every run, and use Granite to reason over our accumulated history. See `docs/roadmap.md` → "Data advantage — our competitive strategy" for the full argument.

---

## Team

Roster + team name are resolved via `web/team-name-poll/` (results in `poll-data.json`). Final team name goes on the fastest-lap video overlay in Phase 4.

---

## Current phase

See `docs/roadmap.md` for the authoritative phase tracker. At repo-initialization time: Phase 0 closing, Phase 1 ahead of schedule (Zo-side environment already validated).
