"""Unit tests for scripts/segment_report.py pure helpers."""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import segment_report as sr  # noqa: E402


def test_parse_segments_yaml(tmp_path):
    p = tmp_path / "segments.yaml"
    p.write_text(textwrap.dedent("""\
        schema_version: v1
        lap_length_m: 3610.0
        segments:
          - id: s00_straight
            kind: straight
            start_m: 0.0
            end_m: 405.0
            target_speed_kmh: 80.0
          - id: s09_turn_R_2605m
            kind: corner
            start_m: 2430.0
            end_m: 2780.0
            target_speed_kmh: 50.0
            observed:
              len_m: 350.0
    """))
    segs = sr.parse_segments_yaml(p)
    assert segs == [
        {"id": "s00_straight", "kind": "straight",
         "start_m": 0.0, "end_m": 405.0, "target_speed_kmh": 80.0},
        {"id": "s09_turn_R_2605m", "kind": "corner",
         "start_m": 2430.0, "end_m": 2780.0, "target_speed_kmh": 50.0},
    ]


def test_segment_stats_basic():
    frames = [
        {"time": 1.0, "trackDistance": 10.0, "speed": 50.0,
         "trackPosition": 0.1, "steer": 0.05},
        {"time": 2.0, "trackDistance": 200.0, "speed": 80.0,
         "trackPosition": -0.3, "steer": -0.15},
        {"time": 3.0, "trackDistance": 404.9, "speed": 75.0,
         "trackPosition": 0.5, "steer": 0.2},
        {"time": 4.0, "trackDistance": 500.0, "speed": 60.0,
         "trackPosition": 0.4, "steer": 0.4},
    ]
    stat = sr.segment_stats(frames, 0.0, 405.0)
    assert stat["frames"] == 3
    assert stat["elapsed_s"] == 2.0
    assert stat["v_min"] == 50.0
    assert stat["v_max"] == 80.0
    assert stat["peak_abs_trackPos"] == 0.5
    assert stat["peak_abs_steer"] == 0.2


def test_segment_stats_empty_when_no_frames_in_range():
    stat = sr.segment_stats([
        {"time": 0.0, "trackDistance": 1000.0, "speed": 50.0,
         "trackPosition": 0.0, "steer": 0.0},
    ], 0.0, 405.0)
    assert stat == {"frames": 0}


def test_load_lap_frames_drops_grid_stragglers(tmp_path):
    # Simulate Corkscrew grid: car parked at trackDistance~3598 with time>=0
    # before it has actually crossed the start/finish line.
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    ndjson = [
        {"time": -1.0, "trackDistance": 3598.0, "lap_number": 1,
         "speed": 0.0, "trackPosition": 0.0, "steer": 0.0},    # pre-race
        {"time": 0.0, "trackDistance": 3598.0, "lap_number": 1,
         "speed": 0.0, "trackPosition": 0.0, "steer": 0.0},    # grid straggler
        {"time": 0.5, "trackDistance": 3605.0, "lap_number": 1,
         "speed": 10.0, "trackPosition": 0.0, "steer": 0.0},   # still grid
        {"time": 1.0, "trackDistance": 20.0, "lap_number": 1,
         "speed": 40.0, "trackPosition": 0.0, "steer": 0.0},   # CROSSED LINE
        {"time": 2.0, "trackDistance": 200.0, "lap_number": 1,
         "speed": 60.0, "trackPosition": 0.1, "steer": 0.05},
    ]
    (run_dir / "frames.ndjson").write_text(
        "\n".join(json.dumps(x) for x in ndjson) + "\n"
    )
    frames = sr.load_lap_frames(run_dir, lap=1)
    assert [f["trackDistance"] for f in frames] == [20.0, 200.0]
