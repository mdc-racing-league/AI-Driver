# Simulation Guide

Day-to-day runbook for working with the TORCS sim and our Granite-assisted driver.

> **Prerequisite:** first-time environment setup is covered separately in `../setup.md`. This guide assumes you already have VSCode, Ollama + Granite, continue.dev, and TORCS installed.

---

## When to use which doc

| If you want to... | Read |
|---|---|
| Run a lap right now, nothing fancy | `01-quickstart.md` |
| Understand how to launch and configure TORCS | `02-launching-torcs.md` |
| Load our custom driver (not the built-in ones) | `03-running-our-driver.md` |
| Capture telemetry from a run | `04-capturing-telemetry.md` |
| Use Granite to review code or interpret a run | `05-granite-workflow.md` |
| Fix something that broke at runtime | `06-troubleshooting.md` |

---

## Reading order for a new teammate

1. `../setup.md` — one-time install (covers install once)
2. `01-quickstart.md` — prove the sim runs
3. `02-launching-torcs.md` — learn the TORCS UI and config
4. `03-running-our-driver.md` — swap in our controller
5. `04-capturing-telemetry.md` — capture your first labeled run
6. `05-granite-workflow.md` — use Granite for code review

Docs 02–05 can be read in any order once you've done quickstart.

---

## Status of this guide

Some sections depend on code that doesn't exist yet. Each doc flags its dependencies at the top. Rough map:

| Doc | Ready | Depends on |
|---|---|---|
| 01-quickstart | ✅ Usable | TORCS install only |
| 02-launching-torcs | ✅ Usable | TORCS install only |
| 03-running-our-driver | ✅ Architecture confirmed; 🟡 `src/driver_baseline.py` (Phase 2) |
| 04-capturing-telemetry | 🟡 Partial | `scripts/log_telemetry.py` (exists) + extended logger (Phase 2) |
| 05-granite-workflow | ✅ Usable | Granite + continue.dev |
| 06-troubleshooting | ✅ Usable | — |

Fill in the 🟡 sections during Phase 2. Each has explicit TODO markers showing what to add.

---

## Cross-references

- Project roadmap: `../roadmap.md`
- One-time environment setup: `../setup.md`
- Granite validation + model-selection rules: `../granite-validation.md`
- Telemetry schema: `../../telemetry/SCHEMA.md`
- Mission brief: `../TORCSRegtoSubmission0901-Mission Brief-Detailed (1).pdf`
- Wtorcs + Ollama integration notes: `../Wtorcs-ollama-instructions.pdf`
