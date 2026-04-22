#!/usr/bin/env python3
"""
Cross-run track index: aggregates all archived runs into per-segment baselines.

For each track segment, shows:
  - Best avg speed achieved (and which run)
  - Worst avg speed (most conservative)
  - Speed variance across runs  →  optimization headroom
  - Peak |trackPos| (corner stress indicator)
  - Best segment time (seconds through that section)

Usage:
    python scripts/track_index.py
    python scripts/track_index.py --runs-dir telemetry/runs --segments telemetry/segments.yaml
    python scripts/track_index.py --clean-only   (exclude runs with damage > 0)
    python scripts/track_index.py --out track_index.md
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from collections import defaultdict


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_segments(path: Path) -> list[dict]:
    """Parse segments.yaml into a list of dicts with start_m, end_m, id, kind, target."""
    text = path.read_text()
    segments = []
    in_seg = False
    cur: dict = {}

    def flush():
        if {"id", "start_m", "end_m"} <= cur.keys():
            segments.append(dict(cur))

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" "):
            in_seg = line.strip() == "segments:"
            if not in_seg:
                flush(); cur = {}
            continue
        if not in_seg:
            continue
        stripped = line.lstrip()
        if stripped.startswith("- "):
            flush(); cur = {}
            stripped = stripped[2:]
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key = key.strip(); val = val.strip()
        if key in ("id", "kind"):
            cur[key] = val
        elif key in ("start_m", "end_m", "target_speed_kmh"):
            try:
                cur[key] = float(val)
            except ValueError:
                pass

    flush()
    segments.sort(key=lambda s: s["start_m"])
    return segments


def segment_for(dist: float, segments: list[dict]) -> dict | None:
    for seg in segments:
        if seg["start_m"] <= dist <= seg["end_m"]:
            return seg
    return None


def load_run(run_dir: Path, segments: list[dict]) -> dict | None:
    """
    Returns {
        "label": str,
        "lap_s": float,
        "damage": float,
        "segments": { seg_id: {"speeds": [...], "track_pos": [...], "times": [...]} }
    }
    """
    manifest_path = run_dir / "manifest.json"
    frames_path   = run_dir / "frames.ndjson"
    if not manifest_path.exists() or not frames_path.exists():
        return None

    manifest = json.loads(manifest_path.read_text())
    outcome  = manifest.get("outcome", {})
    if not outcome.get("completed"):
        return None

    lap_s  = outcome.get("best_lap_seconds") or 0.0
    damage = outcome.get("final_damage") or 0.0
    notes  = manifest.get("notes", run_dir.name)
    # derive a short label like "Run 013"
    label = notes.split(" - ")[0].strip() if " - " in notes else run_dir.name

    seg_data: dict[str, dict] = {s["id"]: {"speeds": [], "track_pos": [], "times": []}
                                  for s in segments}

    prev_time: float | None = None
    for raw_line in frames_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw_line.strip():
            continue
        try:
            f = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        lap_num = f.get("lap_number", 1)
        if lap_num != 1:
            continue

        dist  = float(f.get("trackDistance") or 0.0)
        speed = float(f.get("speed") or 0.0)
        tpos  = float(f.get("trackPosition") or 0.0)
        t     = float(f.get("time") or 0.0)

        if speed < 0 or t < 0:
            continue  # pre-race standing-start frames

        seg = segment_for(dist, segments)
        if seg is None:
            continue

        sid = seg["id"]
        seg_data[sid]["speeds"].append(speed)
        seg_data[sid]["track_pos"].append(abs(tpos))
        if prev_time is not None and t > prev_time:
            seg_data[sid]["times"].append(t - prev_time)
        prev_time = t

    return {"label": label, "lap_s": lap_s, "damage": damage, "segments": seg_data}


def build_index(runs: list[dict], segments: list[dict]) -> list[dict]:
    """Per-segment cross-run aggregation."""
    rows = []
    for seg in segments:
        sid = seg["id"]
        target = seg.get("target_speed_kmh", 0.0)

        run_avgs: list[tuple[str, float, float]] = []  # (label, avg_speed, lap_s)
        all_speeds: list[float] = []
        all_tp: list[float] = []
        best_seg_t: float | None = None
        worst_seg_t: float | None = None

        for run in runs:
            sdata = run["segments"].get(sid, {})
            speeds = sdata.get("speeds", [])
            if not speeds:
                continue
            avg_v = statistics.mean(speeds)
            max_v = max(speeds)
            run_avgs.append((run["label"], avg_v, run["lap_s"]))
            all_speeds.extend(speeds)
            all_tp.extend(sdata.get("track_pos", []))

            seg_t = sum(sdata.get("times", [])) or None
            if seg_t:
                if best_seg_t is None or seg_t < best_seg_t:
                    best_seg_t = seg_t
                if worst_seg_t is None or seg_t > worst_seg_t:
                    worst_seg_t = seg_t

        if not run_avgs:
            continue

        run_avgs.sort(key=lambda x: x[1], reverse=True)
        fastest_label, fastest_avg, _ = run_avgs[0]
        slowest_label, slowest_avg, _ = run_avgs[-1]
        overall_max = max(all_speeds) if all_speeds else 0.0
        overall_avg = statistics.mean(all_speeds) if all_speeds else 0.0
        speed_variance = fastest_avg - slowest_avg
        peak_tp = max(all_tp) if all_tp else 0.0
        time_gap = (worst_seg_t - best_seg_t) if (best_seg_t and worst_seg_t) else None

        rows.append({
            "id": sid,
            "kind": seg.get("kind", "?"),
            "range": f"{seg['start_m']:.0f}–{seg['end_m']:.0f}m",
            "target_kmh": target,
            "overall_avg": overall_avg,
            "overall_max": overall_max,
            "fastest_avg": fastest_avg,
            "fastest_run": fastest_label,
            "slowest_avg": slowest_avg,
            "slowest_run": slowest_label,
            "speed_variance": speed_variance,
            "peak_tp": peak_tp,
            "best_seg_t": best_seg_t,
            "worst_seg_t": worst_seg_t,
            "time_gap": time_gap,
            "n_runs": len(run_avgs),
        })
    return rows


def fmt(v: float | None, decimals: int = 1) -> str:
    return f"{v:.{decimals}f}" if v is not None else "—"


def render_markdown(rows: list[dict], runs: list[dict], clean_only: bool) -> str:
    run_labels = [r["label"] for r in runs]
    run_str = ", ".join(run_labels)
    clean_note = " (clean runs only — damage > 0 excluded)" if clean_only else ""

    lines = [
        "# Track Index — Corkscrew Cross-Run Baseline",
        "",
        f"**Runs included ({len(runs)}):** {run_str}{clean_note}",
        "",
        "## Per-segment baseline table",
        "",
        "| Segment | Kind | Range | Target | Avg speed | Max speed | Best avg | Best run | Variance | Peak \\|tPos\\| | Time gap |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['kind']} | {r['range']} "
            f"| {fmt(r['target_kmh'])} "
            f"| {fmt(r['overall_avg'])} "
            f"| {fmt(r['overall_max'])} "
            f"| {fmt(r['fastest_avg'])} "
            f"| {r['fastest_run']} "
            f"| {fmt(r['speed_variance'])} "
            f"| {fmt(r['peak_tp'], 3)} "
            f"| {fmt(r['time_gap'], 2) + 's' if r['time_gap'] else '—'} |"
        )

    # Opportunity analysis
    lines += [
        "",
        "## Optimization opportunities",
        "",
        "Segments ranked by **speed variance** (= gap between best and worst run through that section).",
        "High variance = we've explored different speeds here and know there's room to push.",
        "",
        "| Rank | Segment | Variance (km/h) | Best avg | Target | Headroom vs target |",
        "|---|---|---|---|---|---|",
    ]
    ranked = sorted(rows, key=lambda x: x["speed_variance"], reverse=True)
    for i, r in enumerate(ranked[:8], 1):
        headroom = r["fastest_avg"] - r["target_kmh"]
        lines.append(
            f"| {i} | {r['id']} | {fmt(r['speed_variance'])} "
            f"| {fmt(r['fastest_avg'])} "
            f"| {fmt(r['target_kmh'])} "
            f"| {'+' if headroom >= 0 else ''}{fmt(headroom)} |"
        )

    # Corner stress
    lines += [
        "",
        "## Corner stress index",
        "",
        "Segments with highest peak `|trackPosition|` across all runs — corners where the car came closest to the edge.",
        "Values > 0.7 are high-risk; > 1.0 = off-track.",
        "",
        "| Segment | Kind | Peak \\|tPos\\| | Target (km/h) | Best avg speed |",
        "|---|---|---|---|---|",
    ]
    stressed = sorted(rows, key=lambda x: x["peak_tp"], reverse=True)
    for r in stressed[:6]:
        risk = " ⚠️" if r["peak_tp"] > 0.7 else ""
        lines.append(
            f"| {r['id']} | {r['kind']} | {fmt(r['peak_tp'], 3)}{risk} "
            f"| {fmt(r['target_kmh'])} "
            f"| {fmt(r['fastest_avg'])} |"
        )

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Cross-run track index for Corkscrew.")
    parser.add_argument("--runs-dir", type=Path,
                        default=REPO_ROOT / "telemetry" / "runs")
    parser.add_argument("--segments", type=Path,
                        default=REPO_ROOT / "telemetry" / "segments.yaml")
    parser.add_argument("--clean-only", action="store_true",
                        help="Exclude runs with damage > 0.")
    parser.add_argument("--out", type=Path, default=None,
                        help="Write markdown output to this file (default: print to stdout).")
    args = parser.parse_args()

    segments = load_segments(args.segments)
    print(f"Loaded {len(segments)} segments from {args.segments}", flush=True)

    run_dirs = sorted(args.runs_dir.iterdir()) if args.runs_dir.is_dir() else []
    runs = []
    for d in run_dirs:
        if not d.is_dir():
            continue
        r = load_run(d, segments)
        if r is None:
            continue
        if args.clean_only and r["damage"] > 0:
            print(f"  skip {r['label']} — damage {r['damage']:.0f}", flush=True)
            continue
        print(f"  loaded {r['label']} — {r['lap_s']:.3f}s, damage {r['damage']:.0f}", flush=True)
        runs.append(r)

    if not runs:
        print("No completed runs found.")
        return

    rows = build_index(runs, segments)
    md = render_markdown(rows, runs, args.clean_only)

    if args.out:
        args.out.write_text(md, encoding="utf-8")
        print(f"\nWrote {args.out}")
    else:
        print("\n" + md)

    # also always write to telemetry/
    out_path = REPO_ROOT / "telemetry" / "track_index.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
