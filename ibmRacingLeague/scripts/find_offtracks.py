#!/usr/bin/env python3
"""Scan a telemetry run archive and report track-position excursions.

Emits one line per contiguous segment where |trackPosition| >= threshold, with
the trackDistance range and worst trackPos reached. Useful for picking
`--slow-zone START:END:SPEED` arguments for the next run.

    python scripts/find_offtracks.py telemetry/runs/<run-id> [--threshold 1.0]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir")
    ap.add_argument("--threshold", type=float, default=1.0,
                    help="|trackPosition| must reach this value to be reported (default: 1.0).")
    ap.add_argument("--pad", type=float, default=100.0,
                    help="Meters to pad each zone before/after the excursion (default: 100).")
    args = ap.parse_args(argv)

    frames_path = Path(args.run_dir) / "frames.ndjson"
    if not frames_path.exists():
        print(f"ERROR: no frames.ndjson in {args.run_dir}", file=sys.stderr)
        return 1

    in_zone = False
    zone_start = 0.0
    zone_min_dist = 0.0
    zone_max_dist = 0.0
    zone_peak = 0.0
    zones: list[tuple[float, float, float]] = []

    with frames_path.open() as fh:
        for line in fh:
            if not line.strip():
                continue
            frame = json.loads(line)
            pos = frame.get("trackPosition")
            dist = frame.get("trackDistance")
            if pos is None or dist is None:
                continue
            if abs(pos) >= args.threshold:
                if not in_zone:
                    in_zone = True
                    zone_min_dist = dist
                    zone_peak = pos
                zone_max_dist = dist
                if abs(pos) > abs(zone_peak):
                    zone_peak = pos
            elif in_zone:
                zones.append((zone_min_dist, zone_max_dist, zone_peak))
                in_zone = False

    if in_zone:
        zones.append((zone_min_dist, zone_max_dist, zone_peak))

    if not zones:
        print(f"No excursions with |trackPosition| >= {args.threshold} in {args.run_dir}")
        return 0

    print(f"Excursions in {args.run_dir} (threshold=|{args.threshold}|):")
    for i, (start, end, peak) in enumerate(zones, 1):
        padded_start = max(0.0, start - args.pad)
        padded_end = end + args.pad
        print(
            f"  #{i}: trackDistance {start:.0f}-{end:.0f}m, "
            f"peak trackPos={peak:+.2f}  "
            f"-> suggested --slow-zone {padded_start:.0f}:{padded_end:.0f}:<speed>"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
