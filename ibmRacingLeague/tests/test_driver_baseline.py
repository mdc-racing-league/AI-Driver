"""Unit tests for src/driver_baseline.py slow-zone + target-speed helpers.

Covers the pure functions that don't need a running TORCS / scr_server:
    - target_speed_for(state)
    - _parse_slow_zones(argv_list)
    - _load_segments(path)
"""
from __future__ import annotations

import sys
import textwrap
import types
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "scripts"))

# driver_baseline imports snakeoil3_gym at import time; stub it so the module
# loads cleanly in CI without the real gym_torcs install.
sys.modules.setdefault("snakeoil3_gym", types.ModuleType("snakeoil3_gym"))

import driver_baseline as db  # noqa: E402


def _reset():
    db.SLOW_ZONES = []
    db.SEGMENTS = []
    db.TARGET_SPEED_KMH = 55.0


def test_target_speed_default_when_no_zones():
    _reset()
    assert db.target_speed_for({"distFromStart": 1234.5}) == 55.0


def test_target_speed_inside_zone():
    _reset()
    db.TARGET_SPEED_KMH = 80.0
    db.SLOW_ZONES = [(2400.0, 2800.0, 40.0)]
    assert db.target_speed_for({"distFromStart": 2600.0}) == 40.0


def test_target_speed_outside_zone_falls_back():
    _reset()
    db.TARGET_SPEED_KMH = 80.0
    db.SLOW_ZONES = [(2400.0, 2800.0, 40.0)]
    assert db.target_speed_for({"distFromStart": 100.0}) == 80.0
    assert db.target_speed_for({"distFromStart": 3000.0}) == 80.0


def test_target_speed_first_match_wins():
    _reset()
    db.TARGET_SPEED_KMH = 80.0
    db.SLOW_ZONES = [(100.0, 300.0, 40.0), (200.0, 400.0, 20.0)]
    assert db.target_speed_for({"distFromStart": 250.0}) == 40.0


def test_target_speed_boundary_inclusive():
    _reset()
    db.TARGET_SPEED_KMH = 80.0
    db.SLOW_ZONES = [(100.0, 200.0, 40.0)]
    assert db.target_speed_for({"distFromStart": 100.0}) == 40.0
    assert db.target_speed_for({"distFromStart": 200.0}) == 40.0


def test_target_speed_falls_back_to_distRaced():
    _reset()
    db.TARGET_SPEED_KMH = 80.0
    db.SLOW_ZONES = [(100.0, 200.0, 40.0)]
    assert db.target_speed_for({"distRaced": 150.0}) == 40.0


def test_parse_slow_zones_empty():
    assert db._parse_slow_zones([]) == []


def test_parse_slow_zones_multiple():
    zones = db._parse_slow_zones(["2400:2800:40", "100:200:50"])
    assert zones == [(2400.0, 2800.0, 40.0), (100.0, 200.0, 50.0)]


def test_parse_slow_zones_bad_format():
    import pytest
    with pytest.raises(ValueError, match="expects"):
        db._parse_slow_zones(["bogus"])


def test_parse_slow_zones_end_before_start():
    import pytest
    with pytest.raises(ValueError, match="end"):
        db._parse_slow_zones(["300:100:40"])


# --- _load_segments / SEGMENTS precedence ----------------------------------

_SEGMENTS_YAML = textwrap.dedent(
    """\
    # Corkscrew segment map
    schema_version: v1
    lap_length_m: 3610.0
    segments:
      - id: s00_straight
        kind: straight
        start_m: 0.0
        end_m: 405.0
        target_speed_kmh: 80.0
        observed:
          len_m: 405.0
          speed_avg: 60.5
      - id: s01_turn_L_475m
        kind: corner
        start_m: 405.0
        end_m: 545.0
        target_speed_kmh: 75.0
        observed:
          len_m: 140.0
      - id: s09_turn_R_2605m
        kind: corner
        start_m: 2430.0
        end_m: 2780.0
        target_speed_kmh: 50.0
        observed:
          len_m: 350.0
    """
)


def test_load_segments_basic(tmp_path):
    p = tmp_path / "segments.yaml"
    p.write_text(_SEGMENTS_YAML)
    segs = db._load_segments(p)
    assert [(s["start_m"], s["end_m"], s["target_speed_kmh"]) for s in segs] == [
        (0.0, 405.0, 80.0),
        (405.0, 545.0, 75.0),
        (2430.0, 2780.0, 50.0),
    ]
    assert all(s["entry_pos"] == 0.0 and s["apex_pos"] == 0.0 and s["exit_pos"] == 0.0
               for s in segs)


def test_load_segments_ignores_unrelated_top_level(tmp_path):
    p = tmp_path / "segments.yaml"
    p.write_text(_SEGMENTS_YAML + "\nother_key: 42\n")
    segs = db._load_segments(p)
    assert len(segs) == 3


def test_segments_drive_target_speed(tmp_path):
    _reset()
    p = tmp_path / "segments.yaml"
    p.write_text(_SEGMENTS_YAML)
    db.SEGMENTS = [(s["start_m"], s["end_m"], s["target_speed_kmh"])
                   for s in db._load_segments(p)]
    db.TARGET_SPEED_KMH = 55.0  # should be shadowed by segment coverage
    assert db.target_speed_for({"distFromStart": 200.0}) == 80.0
    assert db.target_speed_for({"distFromStart": 500.0}) == 75.0
    assert db.target_speed_for({"distFromStart": 2600.0}) == 50.0


def test_segments_take_precedence_over_slow_zones():
    _reset()
    db.TARGET_SPEED_KMH = 80.0
    db.SEGMENTS = [(2430.0, 2780.0, 50.0)]
    db.SLOW_ZONES = [(2400.0, 2800.0, 30.0)]
    assert db.target_speed_for({"distFromStart": 2600.0}) == 50.0


def test_target_speed_fallback_when_outside_all_segments():
    _reset()
    db.TARGET_SPEED_KMH = 60.0
    db.SEGMENTS = [(100.0, 200.0, 80.0)]
    assert db.target_speed_for({"distFromStart": 500.0}) == 60.0
