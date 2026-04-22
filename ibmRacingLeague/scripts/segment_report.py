#!/usr/bin/env python3
"""
Post-process a run archive into a per-segment performance table.

For each segment in segments.yaml we compute, over the lap-1 frames
whose trackDistance falls inside [start_m, end_m):

    * frame count
    * elapsed time (seconds, from first-in to first-after)
    * speed min / mean / max (km/h)
    * peak |trackPosition| (safety margin proxy — 1.0 = track edge)
    * peak |steer| (curvature demand proxy)

Output: markdown table written to <run_dir>/segment_report.md and
echoed to stdout.

Usage
-----
    python scripts/segment_report.py telemetry/runs/2026-04-21T22-42-18
    python scripts/segment_report.py telemetry/runs/<ts> \\
        --segments telemetry/segments.yaml
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))


def load_lap_frames(run_dir: Path, lap: int = 1):
    """Return lap-`lap` frames in time order, dropping grid-rollout stragglers.

    On Corkscrew the car is spawned behind the start-finish line at
    trackDistance≈3598 (inside the final segment). Any frame with time>=0 but
    before the car has actually crossed the line still reports that grid
    distance, so those frames inflate the final segment's totals. We drop
    everything before the first trackDistance<100 sample (the moment the car
    finishes the start-line crossing and begins segment 0).
    """
    frames = []
    with (run_dir / "frames.ndjson").open() as f:
        for line in f:
            d = json.loads(line)
            if d.get("lap_number") != lap:
                continue
            if d.get("time") is None or d["time"] < 0:
                continue
            if d.get("trackDistance") is None:
                continue
            frames.append(d)
    frames.sort(key=lambda d: d["time"])
    for i, f in enumerate(frames):
        if f["trackDistance"] < 100.0:
            return frames[i:]
    return frames


def segment_stats(frames: list[dict], start_m: float, end_m: float) -> dict:
    inside = [f for f in frames if start_m <= f["trackDistance"] < end_m]
    if not inside:
        return {"frames": 0}
    speeds = [f["speed"] for f in inside if f.get("speed") is not None]
    tpos = [abs(f["trackPosition"]) for f in inside if f.get("trackPosition") is not None]
    steer = [abs(f["steer"]) for f in inside if f.get("steer") is not None]
    t0 = inside[0]["time"]
    t1 = inside[-1]["time"]
    return {
        "frames": len(inside),
        "elapsed_s": round(t1 - t0, 3),
        "v_min": round(min(speeds), 1) if speeds else None,
        "v_mean": round(sum(speeds) / len(speeds), 1) if speeds else None,
        "v_max": round(max(speeds), 1) if speeds else None,
        "peak_abs_trackPos": round(max(tpos), 3) if tpos else None,
        "peak_abs_steer": round(max(steer), 3) if steer else None,
    }


def parse_segments_yaml(path: Path) -> list[dict]:
    """Tolerant parser that keeps id, kind, start_m, end_m, target_speed_kmh."""
    out: list[dict] = []
    in_segments = False
    cur: dict = {}

    def _flush():
        if {"start_m", "end_m"} <= cur.keys():
            out.append(dict(cur))

    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" "):
            in_segments = line.strip() == "segments:"
            if not in_segments:
                _flush()
                cur = {}
            continue
        if not in_segments:
            continue
        stripped = line.lstrip()
        if stripped.startswith("- "):
            _flush()
            cur = {}
            stripped = stripped[2:]
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key, value = key.strip(), value.strip()
        if not value:
            continue
        if key in ("start_m", "end_m", "target_speed_kmh"):
            try:
                cur[key] = float(value)
            except ValueError:
                pass
        elif key in ("id", "kind"):
            cur[key] = value
    _flush()
    out.sort(key=lambda s: s["start_m"])
    return out


def format_report(run_dir: Path, segments: list[dict], rows: list[dict]) -> str:
    lines = [
        f"# Segment report — {run_dir.name}",
        "",
        "Per-segment performance aggregates for lap 1 of this run, bucketed by "
        "`trackDistance` into the segments defined in `telemetry/segments.yaml`.",
        "",
        "| # | id | kind | range (m) | target v (km/h) | t (s) | v min/avg/max | peak \\|trackPos\\| | peak \\|steer\\| | frames |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    total_t = 0.0
    for i, (seg, stat) in enumerate(zip(segments, rows)):
        rng = f"{seg['start_m']:.0f}–{seg['end_m']:.0f}"
        target = seg.get("target_speed_kmh", "—")
        if stat.get("frames", 0) == 0:
            lines.append(
                f"| {i} | {seg.get('id','?')} | {seg.get('kind','?')} | {rng} | "
                f"{target} | — | — | — | — | 0 |"
            )
            continue
        total_t += stat["elapsed_s"]
        v_fmt = f"{stat['v_min']}/{stat['v_mean']}/{stat['v_max']}"
        lines.append(
            f"| {i} | {seg.get('id','?')} | {seg.get('kind','?')} | {rng} | "
            f"{target} | {stat['elapsed_s']} | {v_fmt} | "
            f"{stat['peak_abs_trackPos']} | {stat['peak_abs_steer']} | {stat['frames']} |"
        )
    lines += [
        "",
        f"_Sum of per-segment elapsed time: **{total_t:.3f} s** "
        "(≠ lap time — each segment's elapsed counts from first-frame-in to "
        "last-frame-in, so inter-segment gaps are not double-counted but the "
        "very last tick of each segment is dropped)._",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("run_dir", type=Path, help="Run archive (contains frames.ndjson)")
    ap.add_argument(
        "--segments",
        type=Path,
        default=_REPO / "telemetry" / "segments.yaml",
        help="Segment map YAML (default: telemetry/segments.yaml)",
    )
    ap.add_argument("--lap", type=int, default=1, help="Lap number (default: 1)")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output markdown path (default: <run_dir>/segment_report.md)",
    )
    args = ap.parse_args()

    segments = parse_segments_yaml(args.segments)
    frames = load_lap_frames(args.run_dir, args.lap)
    if not frames:
        sys.exit(f"no lap-{args.lap} frames in {args.run_dir}")

    rows = [segment_stats(frames, s["start_m"], s["end_m"]) for s in segments]
    report = format_report(args.run_dir, segments, rows)
    out_path = args.out or (args.run_dir / "segment_report.md")
    out_path.write_text(report)
    print(report)
    print(f"wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
