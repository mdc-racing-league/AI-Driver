#!/usr/bin/env python3
"""Compute segments.csv — the "engagement metrics" layer for a run.

Status: SKELETON (Phase 1 Track A). Full implementation is a Phase 3 deliverable
(requires baseline laps to compute deltas against).

What this script will do when finished:

  For each segment_id traversed in frames.ndjson, emit one row:

    - segment_id
    - time_in           (first frame.time where segment_id entered)
    - time_out          (last frame.time where segment_id seen)
    - duration_s        (time_out - time_in)
    - delta_vs_baseline_s   (this run's duration minus baseline mean for same segment)
    - improvement       (bool, delta < 0)
    - min_speed, max_lateral_g, max_tire_slip (aggregate stats)
    - confidence        (1 - stddev(steer) — smooth control = high confidence)
    - crashed_in_segment (bool, heuristic from damage delta)
    - granite_influenced (bool, from manifest.notes or controller_reason)

See telemetry/SCHEMA.md "Labeling rules" for the authoritative spec.

Usage (eventual):

  python scripts/label_segments.py telemetry/runs/<timestamp>/
  python scripts/label_segments.py telemetry/runs/<timestamp>/ --baseline telemetry/runs/<baseline-ts>/

Reads:  <run_dir>/frames.ndjson, <run_dir>/manifest.json, optional baseline run
Writes: <run_dir>/segments.csv
"""

from __future__ import annotations

import argparse
import sys


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute segments.csv for a run archive. "
                    "SKELETON — implementation lands in Phase 3.",
    )
    parser.add_argument("run_dir",
                        help="Path to runs/<timestamp>/ directory")
    parser.add_argument("--baseline", default=None,
                        help="Path to baseline run archive for delta computation. "
                             "If omitted, delta columns will be null.")
    parser.add_argument("--output", default=None,
                        help="Output path (default: <run_dir>/segments.csv)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    # TODO (Phase 3): implement segment labeling.
    #   1. Load frames.ndjson, group by segment_id (preserving first-seen order)
    #   2. For each segment traversal: compute time_in, time_out, duration, stats
    #   3. If --baseline: load baseline segments.csv; compute delta_vs_baseline_s
    #   4. Compute confidence = 1 - stddev(steer) normalized
    #   5. crashed_in_segment: compare frame.damage at segment start vs end
    #   6. granite_influenced: check manifest.notes for Granite references
    #   7. Write segments.csv with these columns

    print("label_segments.py: SKELETON — not yet implemented.", file=sys.stderr)
    print(f"  Would label: {args.run_dir}", file=sys.stderr)
    if args.baseline:
        print(f"  Against baseline: {args.baseline}", file=sys.stderr)
    print("  Phase 3 will implement this. See docstring for the plan.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
