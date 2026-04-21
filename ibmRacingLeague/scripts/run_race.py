#!/usr/bin/env python3
"""Launch a TORCS race with our driver and archive a validated run.

Status: SKELETON (Phase 1 Track A). Full implementation is a Phase 2 deliverable.

What this script will do when finished:

  1. Generate a run_id (UUID v4)
  2. Create telemetry/runs/<timestamp>/ directory
  3. Write manifest.json (schema_version, controller variant, git SHA,
     track, car, weather, driver name — see telemetry/SCHEMA.md)
  4. Start the upgraded telemetry tailer (v0.2 fields, segment IDs)
  5. Launch TORCS headless (via wtorcs --T or equivalent)
  6. Block until race completes or timeout
  7. Run scripts/validate_run.py on the resulting archive
  8. Run scripts/label_segments.py to produce segments.csv
  9. Write summary.md with lap times and segment deltas

Usage (eventual):

  python scripts/run_race.py --driver baseline --track corkscrew --laps 1
  python scripts/run_race.py --driver pid_v2   --track corkscrew --laps 5 --headless
  python scripts/run_race.py --variant-id $(git rev-parse --short HEAD)

See:
  - docs/simulation-guide/03-running-our-driver.md
  - docs/simulation-guide/04-capturing-telemetry.md
  - telemetry/SCHEMA.md
"""

from __future__ import annotations

import argparse
import sys


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch a TORCS race with our driver and archive a validated run. "
                    "SKELETON — implementation lands in Phase 2.",
    )
    parser.add_argument("--driver", required=True,
                        help="Driver name (e.g., 'baseline', 'pid_v2'). Must match a module in src/drivers/.")
    parser.add_argument("--track", default="corkscrew",
                        help="Track name (default: corkscrew).")
    parser.add_argument("--car", default="car1-trb1",
                        help="Car model (default: car1-trb1).")
    parser.add_argument("--laps", type=int, default=1,
                        help="Number of laps (default: 1; use 5 for stability averaging).")
    parser.add_argument("--headless", action="store_true",
                        help="Launch TORCS in text mode (no GUI).")
    parser.add_argument("--variant-id", default=None,
                        help="Controller variant ID (typically git short SHA). Defaults to git HEAD.")
    parser.add_argument("--runs-dir", default="telemetry/runs",
                        help="Parent directory for run archives (default: telemetry/runs).")
    parser.add_argument("--torcs-bin", default="wtorcs",
                        help="Path to TORCS binary (default: wtorcs on PATH).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    # TODO (Phase 2): implement the full pipeline. See module docstring.
    #   1. Confirm args.torcs_bin resolves
    #   2. uuid4() -> run_id
    #   3. Build run_dir = <runs-dir>/<ISO8601-local-timestamp>/
    #   4. Write manifest.json per telemetry/SCHEMA.md "Per-run manifest"
    #   5. subprocess.Popen the telemetry tailer (see scripts/log_telemetry.py)
    #   6. subprocess.run TORCS headless; capture stdout/stderr
    #   7. On race end: import and call scripts/validate_run.py; fail if non-zero
    #   8. import and call scripts/label_segments.py
    #   9. Write summary.md

    print("run_race.py: SKELETON — not yet implemented.", file=sys.stderr)
    print(f"  Would launch: driver={args.driver} track={args.track} "
          f"laps={args.laps} headless={args.headless}", file=sys.stderr)
    print("  Phase 2 will implement this. See docstring for the plan.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
