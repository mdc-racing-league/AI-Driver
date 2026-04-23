#!/usr/bin/env python3
"""Elevation profile + grip-event correlator.

Reads frames.ndjson and prints:
  1. Elevation (z) vs trackDistance as a binned ASCII sparkline.
  2. Top N grip-pressure events (high |steer| or high |trackPos|) with the
     elevation at that point — proving or rejecting the hypothesis that the
     s08 kink at ~1950 m coincides with a crest/drop.

Usage:
  python scripts/elevation_profile.py telemetry/runs/<timestamp>/
  python scripts/elevation_profile.py telemetry/runs/<timestamp>/ --zoom 1800 2100

Non-zero exit if frames have no z field (pre-schema-change archive).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def load_frames(run_dir: Path) -> list[dict]:
    path = run_dir / "frames.ndjson"
    frames: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            frames.append(json.loads(line))
    return frames


def sparkline(values: list[float | None]) -> str:
    bars = " ▁▂▃▄▅▆▇█"
    finite = [v for v in values if v is not None and math.isfinite(v)]
    if not finite:
        return "(no data)"
    lo, hi = min(finite), max(finite)
    if hi - lo < 1e-9:
        return bars[0] * len(values)
    out = []
    for v in values:
        if v is None or not math.isfinite(v):
            out.append(" ")
        else:
            idx = int((v - lo) / (hi - lo) * (len(bars) - 1))
            out.append(bars[idx])
    return "".join(out)


def bin_profile(frames: list[dict], bin_m: float, lo: float, hi: float) -> list[tuple[float, float | None]]:
    """Return [(bin_center_m, mean_z)] across [lo, hi] in bin_m increments."""
    n_bins = int(math.ceil((hi - lo) / bin_m))
    sums = [0.0] * n_bins
    counts = [0] * n_bins
    for f in frames:
        d = f.get("trackDistance")
        z = f.get("z")
        if d is None or z is None:
            continue
        if d < lo or d >= hi:
            continue
        idx = int((d - lo) / bin_m)
        if 0 <= idx < n_bins:
            sums[idx] += z
            counts[idx] += 1
    out: list[tuple[float, float | None]] = []
    for i in range(n_bins):
        center = lo + (i + 0.5) * bin_m
        mean = (sums[i] / counts[i]) if counts[i] > 0 else None
        out.append((center, mean))
    return out


def top_grip_events(frames: list[dict], k: int) -> list[dict]:
    """Rank frames by max(|steer|, |trackPos|). Returns top k by distinct distance bucket."""
    scored: list[tuple[float, dict]] = []
    for f in frames:
        steer = f.get("steer")
        pos = f.get("trackPosition")
        if steer is None and pos is None:
            continue
        score = max(abs(steer or 0.0), abs(pos or 0.0))
        scored.append((score, f))
    scored.sort(key=lambda x: x[0], reverse=True)
    seen: set[int] = set()
    out: list[dict] = []
    for score, f in scored:
        d = f.get("trackDistance")
        if d is None:
            continue
        bucket = int(d // 30)  # dedupe within 30 m
        if bucket in seen:
            continue
        seen.add(bucket)
        f["_score"] = score
        out.append(f)
        if len(out) >= k:
            break
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", help="Path to telemetry/runs/<timestamp>/")
    parser.add_argument("--bin", type=float, default=25.0, help="Bin width in metres for the full-lap profile (default 25)")
    parser.add_argument("--zoom", nargs=2, type=float, metavar=("LO", "HI"),
                        default=[1850, 2100], help="Zoom window for high-resolution profile (default 1850 2100)")
    parser.add_argument("--zoom-bin", type=float, default=5.0, help="Bin width in the zoom window (default 5)")
    parser.add_argument("--events", type=int, default=8, help="Top N grip events to report (default 8)")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir).resolve()
    frames = load_frames(run_dir)
    if not frames:
        print(f"no frames in {run_dir}", file=sys.stderr)
        return 2

    has_z = any(f.get("z") is not None for f in frames)
    if not has_z:
        print(
            f"FAIL: frames in {run_dir.name} have no 'z' field.\n"
            "  This archive was recorded before the schema change.\n"
            "  Re-run with the current logger to capture elevation.",
            file=sys.stderr,
        )
        return 3

    dists = [f.get("trackDistance") for f in frames if f.get("trackDistance") is not None]
    lap_end = max(dists) if dists else 3610.0

    print(f"# Elevation profile — {run_dir.name}")
    print(f"frames: {len(frames)}, trackDistance max: {lap_end:.1f} m\n")

    # Full lap at coarse resolution
    print(f"## Full lap (bin = {args.bin:.0f} m)")
    prof = bin_profile(frames, args.bin, 0.0, lap_end)
    z_vals = [z for _, z in prof]
    finite_z = [v for v in z_vals if v is not None]
    if finite_z:
        print(f"  z range: {min(finite_z):.2f} m → {max(finite_z):.2f} m "
              f"(Δ {max(finite_z) - min(finite_z):.2f} m)")
    print(f"  {sparkline(z_vals)}")
    print(f"  |{'0m':<{len(z_vals)//2 - 2}}"
          f"{int(lap_end/2)}m".ljust(len(z_vals) // 2) +
          f"{int(lap_end)}m|")

    # Zoom window (s08 kink suspect area)
    lo, hi = args.zoom
    print(f"\n## Zoom {lo:.0f}–{hi:.0f} m (bin = {args.zoom_bin:.0f} m)")
    zprof = bin_profile(frames, args.zoom_bin, lo, hi)
    z_only = [z for _, z in zprof]
    finite = [v for v in z_only if v is not None]
    if finite:
        print(f"  z range: {min(finite):.2f} m → {max(finite):.2f} m "
              f"(Δ {max(finite) - min(finite):.2f} m)")
        first = next((v for v in z_only if v is not None), None)
        last = next((v for v in reversed(z_only) if v is not None), None)
        if first is not None and last is not None:
            delta = last - first
            direction = "rising" if delta > 0.5 else "falling" if delta < -0.5 else "flat"
            print(f"  net entry→exit: {delta:+.2f} m ({direction})")
    print(f"  {sparkline(z_only)}")
    for center, z in zprof:
        if z is None:
            print(f"  {center:7.1f} m: (no data)")
        else:
            print(f"  {center:7.1f} m: z = {z:7.2f}")

    # Top grip events with elevation
    print(f"\n## Top {args.events} grip-pressure events (ranked by max(|steer|, |trackPos|))")
    print(f"  {'distance':>10}  {'z':>8}  {'|trackPos|':>10}  {'|steer|':>8}  {'speed':>7}")
    for f in top_grip_events(frames, args.events):
        d = f.get("trackDistance") or 0.0
        z = f.get("z")
        tp = abs(f.get("trackPosition") or 0.0)
        st = abs(f.get("steer") or 0.0)
        sp = f.get("speed") or 0.0
        zs = f"{z:8.2f}" if z is not None else "    n/a "
        print(f"  {d:10.1f}  {zs}  {tp:10.3f}  {st:8.3f}  {sp:7.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
