#!/usr/bin/env python3
"""
Derive Corkscrew segment boundaries from a clean uniform-speed run's telemetry.

Strategy
--------
A corner is a contiguous range of trackDistance where the driver's |steer|
output stays above a small threshold for at least MIN_CORNER_METRES;
everything else is a straight. We bin telemetry by BIN_M metres along
trackDistance, smooth |steer| over WINDOW_M, then run a hysteresis state
machine and fold tiny runs into their neighbours.

Why `steer`, not `angle_to_track_axis`
--------------------------------------
`angle_to_track_axis` is the car's yaw error relative to the track tangent —
i.e. driver tracking error, not track curvature. A well-tracking driver
keeps it near zero on straights *and* corners, so it's a poor curvature
proxy. The driver's own `steer` output is a cleaner signal: it's ~0 on
straights by construction and has sustained magnitude through real corners.

Usage
-----
    python scripts/derive_segments.py \\
        --source-run telemetry/runs/2026-04-21T20-43-35 \\
        --out telemetry/segments.yaml

Defaults target Run 006 (55 km/h clean baseline), which is the best source
available for geometry extraction (uniform speed + zero off-tracks).
"""
import argparse
import json
import pathlib
import sys
from collections import defaultdict

# Tunables
BIN_M = 5.0              # 5 m bins (smoother than 1 m, enough resolution)
CORNER_STEER_ABS = 0.08  # mean |steer| over bin; above this = actively cornering
MIN_CORNER_METRES = 50   # corners shorter than this get merged into neighbor
MIN_STRAIGHT_METRES = 80 # straights shorter than this get merged into neighbor
WINDOW_M = 25            # smoothing window for steer magnitude


def load_lap(path: pathlib.Path, lap_number: int = 1):
    frames = []
    with path.open() as f:
        for line in f:
            d = json.loads(line)
            if d.get("lap_number") == lap_number and d.get("trackDistance") is not None:
                frames.append(d)
    frames.sort(key=lambda f: f["trackDistance"])
    return frames


def bin_by_distance(frames, bin_m=BIN_M):
    bins = defaultdict(list)
    for f in frames:
        key = int(f["trackDistance"] // bin_m)
        bins[key].append(f)
    out = []
    for key in sorted(bins):
        chunk = bins[key]
        def _mean(field):
            vals = [f.get(field) for f in chunk if f.get(field) is not None]
            return sum(vals) / len(vals) if vals else 0.0
        def _mean_abs(field):
            vals = [abs(f.get(field) or 0) for f in chunk]
            return sum(vals) / len(vals) if vals else 0.0
        out.append({
            "dist": key * bin_m,
            "angle": _mean("angle_to_track_axis"),
            "speed": _mean("speed"),
            "steer_abs_mean": _mean_abs("steer"),
            "steer_signed_mean": _mean("steer"),
            "n": len(chunk),
        })
    return out


def smooth(bins, field, window_m=WINDOW_M):
    w = max(1, int(window_m / BIN_M / 2))
    for i, b in enumerate(bins):
        lo = max(0, i - w)
        hi = min(len(bins), i + w + 1)
        vals = [bb[field] for bb in bins[lo:hi]]
        b[field + "_smooth"] = sum(vals) / len(vals)
    return bins


def segment_run(bins):
    if not bins:
        return []
    def kind_of(b):
        return "corner" if b["steer_abs_mean_smooth"] > CORNER_STEER_ABS else "straight"
    runs = []
    cur_kind = kind_of(bins[0])
    cur_start = bins[0]["dist"]
    for b in bins[1:]:
        k = kind_of(b)
        if k != cur_kind:
            runs.append((cur_kind, cur_start, b["dist"]))
            cur_kind = k
            cur_start = b["dist"]
    runs.append((cur_kind, cur_start, bins[-1]["dist"] + BIN_M))
    return runs


def merge_short(runs, min_corner=MIN_CORNER_METRES, min_straight=MIN_STRAIGHT_METRES):
    changed = True
    while changed and len(runs) > 1:
        changed = False
        for i, (k, s, e) in enumerate(runs):
            length = e - s
            too_short = (k == "corner" and length < min_corner) or (
                k == "straight" and length < min_straight
            )
            if too_short and 0 < i < len(runs) - 1:
                prev_k, prev_s, prev_e = runs[i - 1]
                next_k, next_s, next_e = runs[i + 1]
                if prev_k == next_k:
                    runs = (
                        runs[: i - 1]
                        + [(prev_k, prev_s, next_e)]
                        + runs[i + 2:]
                    )
                    changed = True
                    break
        if not changed:
            break
    return runs


def summarize_segment(bins, start, end):
    section = [b for b in bins if start <= b["dist"] < end]
    if not section:
        return {}
    speeds = [b["speed"] for b in section]
    angles = [b["angle"] for b in section]
    steer_abs = [b["steer_abs_mean"] for b in section]
    steer_signed = [b["steer_signed_mean"] for b in section]
    return {
        "len_m": round(end - start, 1),
        "speed_avg": round(sum(speeds) / len(speeds), 1),
        "speed_min": round(min(speeds), 1),
        "speed_max": round(max(speeds), 1),
        "angle_peak_abs": round(max(abs(a) for a in angles), 3),
        "steer_peak_abs": round(max(steer_abs), 3),
        "steer_mean_signed": round(sum(steer_signed) / len(steer_signed), 3),
    }


def name_segment(kind, idx, angle_peak, start, end):
    if kind == "straight":
        return f"s{idx:02d}_straight"
    sign = "L" if angle_peak > 0 else "R"
    mid = int((start + end) / 2)
    return f"s{idx:02d}_turn_{sign}_{mid}m"


def seed_target_speed(kind, summary):
    """Seed per-segment target_speed from Run 008/009-proven numbers.

    Calibrated against Path A: hairpins (steer_peak >= ~0.5) took 50 km/h
    cleanly; 80 km/h was safe everywhere else. Treat this as a starting
    point for per-segment tuning, not a final answer.
    """
    if kind == "straight":
        return 80.0
    steer_peak = summary.get("steer_peak_abs", 0.0)
    if steer_peak >= 0.5:
        return 50.0
    if steer_peak >= 0.35:
        return 60.0
    if steer_peak >= 0.2:
        return 75.0
    return 78.0


def build_yaml(runs, bins, source_run: pathlib.Path):
    out = [
        "# Corkscrew segment map",
        f"# Derived from {source_run.name} telemetry.",
        "# Each segment is a contiguous trackDistance range with behavior aggregates.",
        "# Tune target_speed per segment; driver looks up target by distFromStart.",
        "#",
        "# Schema version: v1",
        "#",
        f"# Source run: {source_run}",
        f"# Derivation: bin={BIN_M}m, corner_steer_abs={CORNER_STEER_ABS},",
        f"#             min_corner={MIN_CORNER_METRES}m, min_straight={MIN_STRAIGHT_METRES}m",
        "",
        "schema_version: v1",
        f"lap_length_m: {runs[-1][2]:.1f}",
        "segments:",
    ]
    for i, (k, s, e) in enumerate(runs):
        summary = summarize_segment(bins, s, e)
        seed_speed = seed_target_speed(k, summary)
        section = [b for b in bins if s <= b["dist"] < e]
        angle_sign = max(section, key=lambda b: abs(b["angle"]))["angle"] if section else 0.0
        name = name_segment(k, i, angle_sign, s, e)
        out.append(f"  - id: {name}")
        out.append(f"    kind: {k}")
        out.append(f"    start_m: {s:.1f}")
        out.append(f"    end_m: {e:.1f}")
        out.append(f"    target_speed_kmh: {seed_speed:.1f}")
        out.append(f"    observed:")
        for key, val in summary.items():
            out.append(f"      {key}: {val}")
        out.append("")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument(
        "--source-run",
        type=pathlib.Path,
        default=pathlib.Path("telemetry/runs/2026-04-21T20-43-35"),
        help="Run archive directory (contains frames.ndjson). Default: Run 006.",
    )
    ap.add_argument(
        "--out",
        type=pathlib.Path,
        default=pathlib.Path("telemetry/segments.yaml"),
        help="Path to write segment map YAML.",
    )
    ap.add_argument(
        "--lap",
        type=int,
        default=1,
        help="Lap number to extract (default: 1 — first timed lap).",
    )
    args = ap.parse_args()

    frames_path = args.source_run / "frames.ndjson"
    print(f"reading: {frames_path}", file=sys.stderr)
    frames = load_lap(frames_path, args.lap)
    print(f"{len(frames)} lap-{args.lap} frames", file=sys.stderr)
    bins = bin_by_distance(frames, BIN_M)
    print(f"{len(bins)} distance bins of {BIN_M} m", file=sys.stderr)
    bins = smooth(bins, "steer_abs_mean", WINDOW_M)
    runs = segment_run(bins)
    print(f"{len(runs)} raw segments", file=sys.stderr)
    runs = merge_short(runs)
    print(f"{len(runs)} merged segments", file=sys.stderr)

    args.out.write_text(build_yaml(runs, bins, args.source_run))
    print(f"wrote {args.out}", file=sys.stderr)

    for k, s, e in runs:
        summary = summarize_segment(bins, s, e)
        print(
            f"  {k:9s} {s:7.1f} -> {e:7.1f}  "
            f"len={summary['len_m']:6.1f}  "
            f"v_avg={summary['speed_avg']:5.1f}  "
            f"v_min={summary['speed_min']:5.1f}  "
            f"|steer|={summary['steer_peak_abs']:.3f}"
        )


if __name__ == "__main__":
    main()
