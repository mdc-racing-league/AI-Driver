"""Render a linear track map of Corkscrew from a segments YAML file.

Usage:
    python scripts/render_track_map.py [--segments PATH] [--out PATH]

Produces a PNG strip diagram showing every segment in trackDistance order,
color-coded by kind (straight / corner / kink), with target speed labels
and racing-line markers (entry / apex / exit trackPos).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import yaml

KIND_COLORS = {
    "straight": "#2e7d32",
    "corner": "#c62828",
    "kink": "#f9a825",
}


def classify(seg: dict) -> str:
    if "kink" in seg["id"]:
        return "kink"
    return seg["kind"]


def render(segments_path: Path, out_path: Path) -> None:
    data = yaml.safe_load(segments_path.read_text())
    segs = data["segments"]
    lap_m = data.get("lap_length_m", max(s["end_m"] for s in segs))

    fig, (ax_strip, ax_line) = plt.subplots(
        2, 1, figsize=(18, 6), gridspec_kw={"height_ratios": [2, 1.6]}, sharex=True
    )

    # --- Top strip: segment bars ---
    for seg in segs:
        kind = classify(seg)
        color = KIND_COLORS[kind]
        x = seg["start_m"]
        w = seg["end_m"] - seg["start_m"]
        ax_strip.barh(0, w, left=x, height=0.8, color=color, edgecolor="black", linewidth=0.6)

        mid = x + w / 2
        label = seg["id"].split("_", 1)[0]
        ax_strip.text(mid, 0.55, label, ha="center", va="bottom", fontsize=8, fontweight="bold")
        ax_strip.text(
            mid,
            0.0,
            f"{seg['target_speed_kmh']:.0f}",
            ha="center",
            va="center",
            fontsize=9,
            color="white",
            fontweight="bold",
        )
        if w >= 150:
            ax_strip.text(
                mid, -0.55, f"{int(w)}m", ha="center", va="top", fontsize=7, color="#444"
            )

    ax_strip.set_xlim(0, lap_m)
    ax_strip.set_ylim(-0.9, 1.0)
    ax_strip.set_yticks([])
    ax_strip.set_title(
        f"Corkscrew — Segment Map ({len(segs)} segments, {lap_m:.0f} m)\n"
        f"{segments_path.name}",
        fontsize=12,
        fontweight="bold",
    )
    ax_strip.grid(axis="x", linestyle=":", alpha=0.4)

    handles = [
        mpatches.Patch(color=c, label=k) for k, c in KIND_COLORS.items()
    ]
    ax_strip.legend(handles=handles, loc="upper right", fontsize=8, framealpha=0.9)

    # --- Bottom panel: racing line (trackPos) ---
    xs = []
    ys = []
    for seg in segs:
        start = seg["start_m"]
        end = seg["end_m"]
        mid = (start + end) / 2
        ep = seg.get("entry_pos", 0.0)
        ap = seg.get("apex_pos", 0.0)
        xp = seg.get("exit_pos", 0.0)
        xs.extend([start, mid, end])
        ys.extend([ep, ap, xp])

    ax_line.plot(xs, ys, "-", color="#1565c0", linewidth=2.0, alpha=0.85, label="racing line target (trackPos)")
    ax_line.fill_between(xs, ys, 0, color="#1565c0", alpha=0.12)
    ax_line.axhline(0, color="black", linewidth=0.5, alpha=0.6)
    ax_line.axhline(1.0, color="red", linewidth=0.4, linestyle="--", alpha=0.5)
    ax_line.axhline(-1.0, color="red", linewidth=0.4, linestyle="--", alpha=0.5)
    ax_line.set_ylim(-1.1, 1.1)
    ax_line.set_ylabel("trackPos\n(−1 L … +1 R)", fontsize=9)
    ax_line.set_xlabel("trackDistance (m)", fontsize=9)
    ax_line.grid(True, linestyle=":", alpha=0.4)
    ax_line.legend(loc="upper right", fontsize=8, framealpha=0.9)

    # Segment boundary lines on both panels
    for seg in segs:
        for ax in (ax_strip, ax_line):
            ax.axvline(seg["start_m"], color="black", linewidth=0.3, alpha=0.3)

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--segments",
        default="telemetry/segments_submission_v7.yaml",
        help="Path to segments YAML",
    )
    parser.add_argument(
        "--out",
        default="docs/track-map.png",
        help="Output PNG path",
    )
    args = parser.parse_args()
    render(Path(args.segments), Path(args.out))


if __name__ == "__main__":
    main()
