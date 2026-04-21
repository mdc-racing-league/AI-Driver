#!/usr/bin/env python3
"""A/B test a controller variant against the current baseline.

Status: SKELETON (Phase 1 Track A). Full implementation is a Phase 3 deliverable.

What this script will do when finished:

  1. Resolve baseline run archive (from telemetry/baseline.md or --baseline)
  2. Invoke scripts/run_race.py --driver <variant> --laps N
  3. Invoke scripts/label_segments.py to compute deltas
  4. Emit a diff report: total lap-time delta, segment-by-segment deltas,
     crash count, top-3 biggest improvements, top-3 regressions
  5. If variant is an improvement (lap time lower, zero crashes):
       - Append to telemetry/leaderboard.md (top-N)
       - Optionally tag the run manifest as a new candidate baseline
  6. Exit code 0 = variant wins, 1 = variant loses, 2 = error

See docs/roadmap.md "Data advantage" — this is the flywheel.

Usage (eventual):

  python scripts/ab_run.py --variant pid_v2 --laps 5
  python scripts/ab_run.py --variant pid_v2 --laps 5 --baseline runs/2026-05-10T14-00-00/
  python scripts/ab_run.py --variant pid_v2 --promote   # set as new baseline if wins

Reads:  baseline run archive, variant run archive
Writes: A/B diff report to stdout; optional leaderboard update
"""

from __future__ import annotations

import argparse
import sys


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="A/B test a controller variant vs. current baseline. "
                    "SKELETON — implementation lands in Phase 3.",
    )
    parser.add_argument("--variant", required=True,
                        help="Controller variant name (driver module in src/drivers/).")
    parser.add_argument("--laps", type=int, default=5,
                        help="Laps per side of the A/B (default: 5).")
    parser.add_argument("--baseline", default=None,
                        help="Path to baseline run archive. "
                             "Default: read from telemetry/baseline.md.")
    parser.add_argument("--promote", action="store_true",
                        help="If variant wins, update telemetry/baseline.md to point at the variant run.")
    parser.add_argument("--leaderboard", default="telemetry/leaderboard.md",
                        help="Leaderboard file to update (default: telemetry/leaderboard.md).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    # TODO (Phase 3): implement the A/B flywheel.
    #   1. Resolve baseline run (from arg or telemetry/baseline.md pointer)
    #   2. scripts/run_race.py --driver <variant> --laps <laps> -> new_run_dir
    #   3. scripts/label_segments.py new_run_dir --baseline baseline_run
    #   4. Compute aggregate diff:
    #      - total_delta_s (sum of segment deltas)
    #      - crashes (count segments with crashed_in_segment=True)
    #      - top 3 improvements, top 3 regressions
    #   5. Print diff report
    #   6. If total_delta_s < 0 and crashes == 0:
    #      - Update leaderboard.md (maintain top-N sorted by lap time)
    #      - If --promote: rewrite telemetry/baseline.md to point at new run
    #      - exit 0
    #      else: exit 1

    print("ab_run.py: SKELETON — not yet implemented.", file=sys.stderr)
    print(f"  Would A/B: variant={args.variant} laps={args.laps} "
          f"promote={args.promote}", file=sys.stderr)
    print("  Phase 3 will implement this. See docstring for the plan.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
