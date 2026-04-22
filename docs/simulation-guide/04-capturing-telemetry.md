# 04 — Capturing telemetry

How to produce a valid, labeled run archive that conforms to `telemetry/SCHEMA.md`.

**Prerequisites:** `02-launching-torcs.md`. Also read `telemetry/SCHEMA.md` once end-to-end.

**Status:** 🟡 **Partial.** The basic tailer (`scripts/log_telemetry.py`) exists and works with v0.1 fields. The v0.2 extended logger, validator, and auto-labeler are Phase 2 deliverables.

---

## The archive we want at the end of a run

```
telemetry/runs/<YYYY-MM-DDTHH-MM-SS>/
├── manifest.json        # run metadata (see telemetry/SCHEMA.md)
├── frames.ndjson        # raw per-tick frames
├── frames.csv           # flattened for pandas / spreadsheet
├── segments.csv         # per-segment labels (auto-computed post-run)
└── summary.md           # human-readable summary
```

This is our **dataset unit**. Every single run produces exactly this structure. See the "Data advantage" section in `docs/roadmap.md` for why that discipline matters.

---

## Current (v0.1) workflow

The existing tailer reads TORCS telemetry JSON lines and writes a flat CSV:

```bash
# Terminal 1 — start the tailer BEFORE launching TORCS
python scripts/log_telemetry.py \
  --source ibmRacingLeague/telemetry/raw.log \
  --output ibmRacingLeague/telemetry/frames.csv

# Terminal 2 — launch TORCS (see 02-launching-torcs.md)
```

This produces `frames.csv` with 9 fields. **That's v0.1 only.** Good enough for a smoke test, not good enough for A/B comparison.

---

## Target (v0.2) workflow — Phase 2 deliverable

> TODO (Phase 2): implement the below and update this section with the exact commands.

Planned shape:

```bash
# One command — wraps tailer + TORCS launch + manifest writing + validation
python scripts/run_race.py --driver baseline --track corkscrew --laps 1 --headless
```

What `run_race.py` will do:

1. Generate a `run_id` (UUID)
2. Create `telemetry/runs/<timestamp>/` directory
3. Write `manifest.json` with controller variant, git SHA, weather, etc.
4. Start tailer (upgraded to emit full v0.2 fields + segment IDs)
5. Launch TORCS headless
6. On race end: run `scripts/validate_run.py` to confirm schema compliance
7. Run `scripts/label_segments.py` to compute `segments.csv` deltas vs. baseline
8. Write `summary.md` with lap time, segment deltas, and crash flag

---

## What a teammate is responsible for per run

- **Always let the full run complete** before cancelling (partial runs corrupt the dataset).
- **Don't delete runs** even if they crashed — crash data is valuable training signal.
- **Add a note to `manifest.json`'s `notes` field** if you changed something between runs (e.g., "widened turn-6 entry").
- **Don't overwrite files in `runs/`** — each run has its own timestamped directory.

---

## Validating a run

Once `scripts/validate_run.py` exists (Phase 2), every run should pass validation before it's committed:

```bash
python scripts/validate_run.py ibmRacingLeague/telemetry/runs/2026-05-04T14-22-13/
```

See `telemetry/SCHEMA.md` "Validation" section for what gets checked.

---

## Leaderboard

`telemetry/leaderboard.md` is the top-N fastest clean runs, updated automatically by `scripts/ab_run.py` (Phase 3 deliverable). Don't edit it manually.

---

## Next

- `05-granite-workflow.md` — how to use Granite to analyze what you just captured
