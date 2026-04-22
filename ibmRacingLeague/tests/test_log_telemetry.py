"""Unit tests for scripts/log_telemetry.py.

Each test drives TelemetryLogger with synthetic sensor dicts and then asserts
the resulting archive via the real validate_run validator — so the logger and
validator are exercised together end-to-end.

Run with:

    python -m unittest tests.test_log_telemetry -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import log_telemetry  # type: ignore  # noqa: E402
import validate_run  # type: ignore  # noqa: E402


def _sensors(t: float, *, track_pos: float = 0.0, speed: float = 50.0) -> dict:
    """Synthetic snakeoil3-style sensor dict (scalars; no list-wrapping)."""
    return {
        "curLapTime": t,
        "speedX": speed,
        "rpm": 5200,
        "trackPos": track_pos,
        "distFromStart": t * 50.0,
        "angle": 0.01,
        "damage": 0.0,
        "fuel": 48.0,
        "gear": 3,
        "track": [10.0] * 19,
        "wheelSpinVel": [110.0, 112.0, 108.0, 109.0],
        "opponents": [200.0] * 36,
    }


def _action(*, steer: float = 0.0, accel: float = 0.4, brake: float = 0.0, gear: int = 3) -> dict:
    return {
        "steer": steer,
        "accel": accel,
        "brake": brake,
        "gear": gear,
        "clutch": 0.0,
        "meta": 0,
    }


class TelemetryLoggerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._td.name)
        # Copy the real canonical segment list into tmpdir so validate_run
        # can enforce Rule 4 against a realistic map.
        self.segments_path = self.tmpdir / "segments.txt"
        real_segments = _REPO_ROOT / "telemetry" / "segments.txt"
        self.segments_path.write_text(real_segments.read_text(encoding="utf-8"), encoding="utf-8")

    def tearDown(self) -> None:
        self._td.cleanup()

    def _new_logger(self) -> log_telemetry.TelemetryLogger:
        run_dir = self.tmpdir / "runs" / "2026-05-04T14-22-13"
        return log_telemetry.TelemetryLogger(
            run_dir,
            run_id="test-run-fixed",
            controller_type="baseline",
            controller_variant_id="abc1234",
            track="corkscrew",
            car="car1-trb1",
            driver="louis",
            notes="synthetic unit-test run",
        )

    # ---------- end-to-end archive validates ----------

    def test_archive_passes_validator(self):
        logger = self._new_logger()
        for i in range(10):
            t = i * 0.05
            logger.log_frame(
                sensors=_sensors(t),
                action=_action(),
                controller_reason="cruise",
                lap_number=1,
            )
        logger.close(outcome={
            "completed": True,
            "crashed": False,
            "laps_completed": 0,
            "best_lap_seconds": None,
            "total_time_seconds": 0.5,
            "final_damage": 0.0,
        })

        frame_count, errors = validate_run.validate_run(logger.run_dir, self.segments_path)
        self.assertEqual(errors, [], f"validator reported errors: {errors}")
        self.assertEqual(frame_count, 10)

    # ---------- manifest contents ----------

    def test_manifest_has_expected_keys(self):
        logger = self._new_logger()
        logger.log_frame(sensors=_sensors(0.0), action=_action(), lap_number=1)
        logger.close(outcome={"completed": True, "crashed": False})

        manifest = json.loads((logger.run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "v0.2")
        self.assertEqual(manifest["run_id"], "test-run-fixed")
        self.assertEqual(manifest["controller_type"], "baseline")
        self.assertEqual(manifest["controller_variant_id"], "abc1234")
        self.assertEqual(manifest["track"], "corkscrew")
        self.assertEqual(manifest["driver"], "louis")
        self.assertEqual(manifest["frame_count"], 1)
        self.assertEqual(manifest["segment_ids_seen"], ["s00_start_straight"])
        self.assertIn("started_at", manifest)
        self.assertIn("ended_at", manifest)
        self.assertEqual(manifest["outcome"]["completed"], True)

    # ---------- sensor → frame mapping ----------

    def test_frame_mapping_captures_key_signals(self):
        logger = self._new_logger()
        logger.log_frame(
            sensors=_sensors(0.123, track_pos=-0.5, speed=62.0),
            action=_action(steer=0.07, accel=0.8, brake=0.0, gear=4),
            controller_reason="accelerating",
            lap_number=2,
        )
        logger.close()

        frames = [
            json.loads(line)
            for line in (logger.run_dir / "frames.ndjson").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(frames), 1)
        frame = frames[0]
        self.assertEqual(frame["schema_version"], "v0.2")
        self.assertEqual(frame["run_id"], "test-run-fixed")
        self.assertAlmostEqual(frame["time"], 0.123)
        self.assertAlmostEqual(frame["speed"], 62.0)
        self.assertEqual(frame["rpm"], 5200)
        self.assertAlmostEqual(frame["trackPosition"], -0.5)
        self.assertAlmostEqual(frame["angle_to_track_axis"], 0.01)
        self.assertEqual(frame["gear"], 4)
        self.assertAlmostEqual(frame["throttle"], 0.8)
        self.assertAlmostEqual(frame["brake"], 0.0)
        self.assertAlmostEqual(frame["steer"], 0.07)
        self.assertEqual(frame["controller_type"], "baseline")
        self.assertEqual(frame["controller_reason"], "accelerating")
        self.assertEqual(frame["lap_number"], 2)
        self.assertEqual(len(frame["track_sensors"]), 19)
        self.assertAlmostEqual(frame["distance_to_edge_left"], 10.0)
        self.assertAlmostEqual(frame["distance_to_edge_right"], 10.0)
        self.assertAlmostEqual(frame["wheel_spin_velocity_avg"], (110 + 112 + 108 + 109) / 4)
        # Opponents all at sentinel 200.0 → no live opponent → null.
        self.assertIsNone(frame["opponentMinDistance"])
        # Not-yet-derivable signals must be present as keys with null value.
        for k in ("tire_slip_fl", "tire_slip_fr", "tire_slip_rl", "tire_slip_rr",
                  "z_accel", "lateral_g"):
            self.assertIn(k, frame)
            self.assertIsNone(frame[k])

    def test_opponent_min_picks_closest_non_sentinel(self):
        sensors = _sensors(0.0)
        sensors["opponents"] = [200.0, 42.5, 200.0, 17.2, 200.0]
        logger = self._new_logger()
        logger.log_frame(sensors=sensors, action=_action(), lap_number=1)
        logger.close()
        frame = json.loads(
            (logger.run_dir / "frames.ndjson").read_text(encoding="utf-8").splitlines()[0]
        )
        self.assertAlmostEqual(frame["opponentMinDistance"], 17.2)

    # ---------- list-wrapped sensors (snakeoil3 real format) ----------

    def test_list_wrapped_scalar_sensors_are_unwrapped(self):
        """snakeoil3 wraps most scalar sensors as single-element lists."""
        sensors = {
            "curLapTime": [1.5],
            "speedX": [44.0],
            "rpm": [6000],
            "trackPos": [0.1],
            "distFromStart": [75.0],
            "angle": [0.0],
            "damage": [0.0],
            "fuel": [40.0],
            "gear": [3],
            "track": [5.0] * 19,
            "wheelSpinVel": [100.0, 101.0, 102.0, 103.0],
            "opponents": [200.0] * 36,
        }
        logger = self._new_logger()
        logger.log_frame(sensors=sensors, action=_action(), lap_number=1)
        logger.close()
        frame = json.loads(
            (logger.run_dir / "frames.ndjson").read_text(encoding="utf-8").splitlines()[0]
        )
        self.assertAlmostEqual(frame["time"], 1.5)
        self.assertAlmostEqual(frame["speed"], 44.0)
        self.assertEqual(frame["rpm"], 6000)

    # ---------- context manager ----------

    def test_context_manager_closes_and_writes_manifest(self):
        run_dir = self.tmpdir / "runs" / "ctxmgr"
        with log_telemetry.TelemetryLogger(
            run_dir,
            run_id="ctx-run",
            controller_type="baseline",
            controller_variant_id="v",
        ) as logger:
            logger.log_frame(sensors=_sensors(0.0), action=_action(), lap_number=1)
        self.assertTrue((run_dir / "manifest.json").exists())
        frame_count, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertEqual(errors, [])
        self.assertEqual(frame_count, 1)

    def test_cannot_log_after_close(self):
        logger = self._new_logger()
        logger.log_frame(sensors=_sensors(0.0), action=_action(), lap_number=1)
        logger.close()
        with self.assertRaises(RuntimeError):
            logger.log_frame(sensors=_sensors(0.1), action=_action(), lap_number=1)

    # ---------- for_new_run factory ----------

    def test_for_new_run_creates_timestamped_dir(self):
        runs_dir = self.tmpdir / "runs"
        logger = log_telemetry.TelemetryLogger.for_new_run(
            controller_type="baseline",
            controller_variant_id="abc",
            runs_dir=runs_dir,
            track="corkscrew",
            driver="louis",
        )
        self.assertTrue(logger.run_dir.exists())
        self.assertEqual(logger.run_dir.parent, runs_dir)
        logger.log_frame(sensors=_sensors(0.0), action=_action(), lap_number=1)
        logger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
