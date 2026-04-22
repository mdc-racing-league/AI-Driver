"""Unit tests for src/driver_baseline.py slow-zone + target-speed helpers.

Covers the pure functions that don't need a running TORCS / scr_server:
    - target_speed_for(state)
    - _parse_slow_zones(argv_list)
"""
from __future__ import annotations

import sys
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
