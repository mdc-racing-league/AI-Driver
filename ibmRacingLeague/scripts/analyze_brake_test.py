#!/usr/bin/env python3
"""Analyze a brake-test run to measure the IBM F1 car's actual decel ceiling.

Reads frames.ndjson from a run produced by `driver_baseline.py --brake-test N`,
finds the BRAKE phase, and reports peak / mean deceleration in m/s^2 plus
stopping distance and stopping time.

Usage:
    python scripts/analyze_brake_test.py telemetry/runs/<RUN_FOLDER>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KMH_TO_MS = 1000.0 / 3600.0


def load_frames(run_dir: Path) -> list[dict]:
    fp = run_dir / "frames.ndjson"
    if not fp.exists():
        print(f"ERROR: {fp} not found", file=sys.stderr)
        sys.exit(1)
    frames = []
    with fp.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                frames.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"WARN: skipping malformed frame: {e}", file=sys.stderr)
    return frames


def brake_phase_frames(frames: list[dict]) -> list[dict]:
    return [f for f in frames if f.get("controller_reason") == "brake_test_brake"]


def smoothed_decel(brake_frames: list[dict], window: int = 5) -> list[tuple[float, float]]:
    """Return list of (time, decel_ms2) using a sliding window of `window` frames."""
    out = []
    for i in range(window, len(brake_frames)):
        a = brake_frames[i - window]
        b = brake_frames[i]
        dt = float(b["time"]) - float(a["time"])
        if dt <= 0:
            continue
        dv_kmh = float(a["speed"]) - float(b["speed"])  # positive when slowing
        decel_ms2 = (dv_kmh * KMH_TO_MS) / dt
        out.append((float(b["time"]), decel_ms2))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute brake decel from a brake-test run.")
    parser.add_argument("run_dir", type=Path, help="Run folder (telemetry/runs/<TIMESTAMP>)")
    parser.add_argument("--window", type=int, default=5,
                        help="Frame window for smoothing (default: 5 = 100ms at 50Hz)")
    args = parser.parse_args()

    frames = load_frames(args.run_dir)
    print(f"[analyze_brake_test] loaded {len(frames)} frames from {args.run_dir}")

    brake_frames = brake_phase_frames(frames)
    if not brake_frames:
        print("ERROR: no frames with controller_reason='brake_test_brake' found.")
        print("       Was this run produced with --brake-test?")
        return 1

    print(f"[analyze_brake_test] BRAKE phase: {len(brake_frames)} frames")

    v_start = float(brake_frames[0]["speed"])
    v_end   = float(brake_frames[-1]["speed"])
    t_start = float(brake_frames[0]["time"])
    t_end   = float(brake_frames[-1]["time"])
    dist_start = float(brake_frames[0].get("trackDistance", 0.0) or 0.0)
    dist_end   = float(brake_frames[-1].get("trackDistance", 0.0) or 0.0)

    duration = t_end - t_start
    delta_v_kmh = v_start - v_end
    delta_v_ms = delta_v_kmh * KMH_TO_MS
    mean_decel = delta_v_ms / duration if duration > 0 else 0.0

    decels = smoothed_decel(brake_frames, window=args.window)
    if decels:
        peak_decel = max(d for _, d in decels)
        peak_time = max(decels, key=lambda t: t[1])[0]
    else:
        peak_decel = 0.0
        peak_time = 0.0

    print()
    print("=" * 60)
    print("  BRAKE CALIBRATION RESULTS")
    print("=" * 60)
    print(f"  Brake start speed   : {v_start:7.2f} km/h ({v_start * KMH_TO_MS:5.2f} m/s)")
    print(f"  Brake end speed     : {v_end:7.2f} km/h ({v_end * KMH_TO_MS:5.2f} m/s)")
    print(f"  Stopping time       : {duration:7.2f} s")
    print(f"  Stopping distance   : {abs(dist_end - dist_start):7.2f} m")
    print()
    print(f"  Mean decel          : {mean_decel:7.2f} m/s^2")
    print(f"  Peak decel (smoothed): {peak_decel:7.2f} m/s^2  (at t={peak_time:.2f}s)")
    print()
    print("  Lookahead controller currently uses LOOKAHEAD_DECEL_MS2 default = 8.0")
    print(f"  Recommended LOOKAHEAD_DECEL_MS2 = {peak_decel * 0.85:.1f}  (peak * 0.85 safety)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
