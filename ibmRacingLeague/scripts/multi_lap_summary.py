#!/usr/bin/env python3
"""Multi-lap summary: per-lap stats + aggregate distribution from a run's frames.ndjson.

Reads telemetry/runs/<RUN>/frames.ndjson, groups by lap_number, and produces a
markdown report with per-lap detail (time, off-tracks, max |trackPos|, top speed,
damage, frame count) plus aggregate distribution stats (best/median/mean/p10/p90/
stdev) for both all laps and clean laps.

Usage:
    python scripts/multi_lap_summary.py telemetry/runs/<RUN_FOLDER>
    python scripts/multi_lap_summary.py <RUN> --out <RUN>/multi_lap_summary.md
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("run_dir", type=Path, help="Path to telemetry/runs/<RUN_FOLDER>.")
    parser.add_argument("--out", type=Path, default=None,
                        help="Write report to this path. Default: print to stdout.")
    parser.add_argument("--off-track-threshold", type=float, default=1.0,
                        help="|trackPos| threshold counted as an off-track. Default: 1.0.")
    args = parser.parse_args(argv)

    frames_path = args.run_dir / "frames.ndjson"
    laps_csv = args.run_dir / "laps.csv"

    if not frames_path.exists():
        print(f"ERROR: {frames_path} not found", flush=True)
        return 1

    laps: dict[int, list[dict]] = {}
    for line in frames_path.open("r", encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            f = json.loads(line)
        except json.JSONDecodeError:
            continue
        lap = int(f.get("lap_number") or 1)
        laps.setdefault(lap, []).append(f)

    lap_times: dict[int, float] = {}
    if laps_csv.exists():
        for line in laps_csv.open("r", encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("lap_num"):
                continue
            parts = line.split(",")
            if len(parts) >= 2:
                try:
                    lap_times[int(parts[0])] = float(parts[1])
                except ValueError:
                    pass

    rows = []
    for lap_num in sorted(laps):
        frames = laps[lap_num]
        speeds = [float(f.get("speed") or 0.0) for f in frames]
        track_pos = [float(f.get("trackPosition") or 0.0) for f in frames]
        damages = [float(f.get("damage") or 0.0) for f in frames]
        off_tracks = sum(1 for tp in track_pos if abs(tp) > args.off_track_threshold)
        max_tp = max((abs(tp) for tp in track_pos), default=0.0)
        top_speed = max(speeds, default=0.0)
        max_damage = max(damages, default=0.0)
        rows.append({
            "lap_num": lap_num,
            "lap_time": lap_times.get(lap_num),
            "off_tracks": off_tracks,
            "max_trackpos": max_tp,
            "top_speed_kmh": top_speed,
            "max_damage": max_damage,
            "frames": len(frames),
        })

    lines: list[str] = []
    lines.append(f"# Multi-lap summary — {args.run_dir.name}")
    lines.append("")
    lines.append(f"laps detected: {len(rows)}  |  off-track threshold: |trackPos| >= {args.off_track_threshold}")
    lines.append("")
    lines.append("## Per-lap detail")
    lines.append("")
    lines.append("| lap | time (s) | off-tracks | max \\|trackPos\\| | top speed (km/h) | damage | frames |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        t = f"{r['lap_time']:.3f}" if r['lap_time'] is not None else "—"
        lines.append(
            f"| {r['lap_num']} | {t} | {r['off_tracks']} | "
            f"{r['max_trackpos']:.2f} | {r['top_speed_kmh']:.1f} | "
            f"{r['max_damage']:.1f} | {r['frames']} |"
        )
    lines.append("")

    times_all = [r['lap_time'] for r in rows if r['lap_time'] is not None]
    times_clean = [r['lap_time'] for r in rows if r['lap_time'] is not None and r['off_tracks'] == 0]

    def _stats_block(title: str, samples: list[float]) -> list[str]:
        block = [f"## {title}", ""]
        if not samples:
            block.append("(no samples)")
            block.append("")
            return block
        sorted_s = sorted(samples)
        block.append(f"- count:  {len(samples)}")
        block.append(f"- best:   {min(samples):.3f} s")
        block.append(f"- median: {statistics.median(samples):.3f} s")
        block.append(f"- mean:   {statistics.mean(samples):.3f} s")
        block.append(f"- worst:  {max(samples):.3f} s")
        if len(samples) >= 2:
            block.append(f"- stdev:  {statistics.stdev(samples):.3f} s")
        if len(samples) >= 10:
            p10_idx = max(0, int(round(len(samples) * 0.10)) - 1)
            p90_idx = min(len(samples) - 1, int(round(len(samples) * 0.90)) - 1)
            block.append(f"- p10:    {sorted_s[p10_idx]:.3f} s")
            block.append(f"- p90:    {sorted_s[p90_idx]:.3f} s")
        block.append("")
        return block

    lines += _stats_block("Distribution — all laps with a recorded time", times_all)
    lines += _stats_block("Distribution — clean laps only (0 off-tracks)", times_clean)

    out = "\n".join(lines)
    if args.out:
        args.out.write_text(out, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
