"""Unit tests for scripts/validate_run.py.

Each test builds a synthetic run archive in a tempdir, then asserts
the validator's behavior. Run with:

    python -m unittest tests.test_validate_run -v

(from the repo root).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Make scripts/ importable as a package-less module.
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import validate_run  # type: ignore  # noqa: E402


def _frame(
    *,
    time: float,
    segment_id: str = "s00_start_straight",
    run_id: str = "test-run-1",
    schema_version: str = "v0.2",
    **overrides,
) -> dict:
    """Build a frame that is valid for schema v0.2 by default."""
    track_distance = time * 50.0 if isinstance(time, (int, float)) else 0.0
    base = {
        "schema_version": schema_version,
        "run_id": run_id,
        "time": time,
        "segment_id": segment_id,
        "lap_number": 1,
        "speed": 50.0,
        "rpm": 5000,
        "trackPosition": 0.0,
        "trackDistance": track_distance,
        "opponentMinDistance": None,
        "throttle": 0.5,
        "brake": 0.0,
        "steer": 0.0,
        "gear": 3,
        "tire_slip_fl": 0.01,
        "tire_slip_fr": 0.01,
        "tire_slip_rl": 0.01,
        "tire_slip_rr": 0.01,
        "wheel_spin_velocity_avg": 120.0,
        "z_accel": 0.0,
        "lateral_g": 0.2,
        "angle_to_track_axis": 0.0,
        "damage": 0.0,
        "fuel": 50.0,
        "distance_to_edge_left": 5.0,
        "distance_to_edge_right": 5.0,
        "track_sensors": [10.0] * 19,
        "controller_type": "baseline",
        "controller_variant_id": "abc1234",
        "controller_reason": "cruise",
    }
    base.update(overrides)
    return base


def _make_run(
    tmpdir: Path,
    frames: list[dict],
    *,
    run_id: str = "test-run-1",
    schema_version: str = "v0.2",
    manifest_overrides: dict | None = None,
    omit_manifest: bool = False,
) -> Path:
    """Create a run archive at tmpdir/runs/ts/ and return the run dir."""
    run_dir = tmpdir / "runs" / "2026-05-04T14-22-13"
    run_dir.mkdir(parents=True)
    (run_dir / "frames.ndjson").write_text(
        "\n".join(json.dumps(f) for f in frames) + "\n",
        encoding="utf-8",
    )
    if not omit_manifest:
        manifest = {
            "run_id": run_id,
            "schema_version": schema_version,
            "started_at": "2026-05-04T14:22:13-04:00",
            "track": "corkscrew",
            "driver": "louis",
            "outcome": {"completed": True, "crashed": False},
        }
        if manifest_overrides:
            manifest.update(manifest_overrides)
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
    return run_dir


def _make_segments_file(tmpdir: Path, ids: list[str] | None = None) -> Path:
    if ids is None:
        ids = [
            "s00_start_straight",
            "s01_turn1_entry",
            "s02_turn1_apex",
            "s14_corkscrew_entry",
            "s15_corkscrew_drop",
            "s16_corkscrew_exit",
            "s17_final_straight",
        ]
    segments_path = tmpdir / "segments.txt"
    segments_path.write_text("\n".join(ids) + "\n", encoding="utf-8")
    return segments_path


class ValidateRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._td.name)
        self.segments_path = _make_segments_file(self.tmpdir)

    def tearDown(self) -> None:
        self._td.cleanup()

    # ---------- passing cases ----------

    def test_happy_path_v02_passes(self):
        frames = [_frame(time=0.0), _frame(time=0.1), _frame(time=0.2)]
        run_dir = _make_run(self.tmpdir, frames)
        count, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertEqual(errors, [], f"unexpected errors: {errors}")
        self.assertEqual(count, 3)

    def test_equal_timestamps_allowed_non_decreasing(self):
        frames = [_frame(time=0.0), _frame(time=0.0), _frame(time=0.1)]
        run_dir = _make_run(self.tmpdir, frames)
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertEqual(errors, [])

    # ---------- Rule 1: required non-null fields ----------

    def test_missing_schema_version_fails(self):
        frames = [_frame(time=0.0)]
        del frames[0]["schema_version"]
        run_dir = _make_run(self.tmpdir, frames)
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("schema_version" in e for e in errors), errors)

    def test_null_run_id_fails(self):
        frames = [_frame(time=0.0, run_id=None)]
        run_dir = _make_run(self.tmpdir, frames)
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("run_id" in e and "null" in e for e in errors), errors)

    def test_missing_segment_id_fails(self):
        frames = [_frame(time=0.0)]
        del frames[0]["segment_id"]
        run_dir = _make_run(self.tmpdir, frames)
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("segment_id" in e for e in errors), errors)

    # ---------- Rule 2: run_id consistency ----------

    def test_inconsistent_run_id_across_frames_fails(self):
        frames = [
            _frame(time=0.0, run_id="run-A"),
            _frame(time=0.1, run_id="run-B"),
        ]
        run_dir = _make_run(self.tmpdir, frames, run_id="run-A")
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("differs from first-seen" in e for e in errors), errors)

    def test_frame_run_id_not_matching_manifest_fails(self):
        frames = [_frame(time=0.0, run_id="frames-run")]
        run_dir = _make_run(self.tmpdir, frames, run_id="manifest-run")
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("does not match manifest.run_id" in e for e in errors), errors)

    # ---------- Rule 3: time monotonic non-decreasing ----------

    def test_time_going_backwards_fails(self):
        frames = [_frame(time=0.0), _frame(time=0.2), _frame(time=0.1)]
        run_dir = _make_run(self.tmpdir, frames)
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("time went backwards" in e for e in errors), errors)

    def test_non_numeric_time_fails(self):
        frames = [_frame(time="oops")]  # type: ignore[arg-type]
        run_dir = _make_run(self.tmpdir, frames)
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("time must be a number" in e for e in errors), errors)

    # ---------- Rule 4: segment_id in canonical map ----------

    def test_unknown_segment_id_fails(self):
        frames = [_frame(time=0.0, segment_id="s99_bogus")]
        run_dir = _make_run(self.tmpdir, frames)
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("not in canonical segment map" in e for e in errors), errors)

    def test_missing_segments_file_still_reports_other_errors(self):
        frames = [_frame(time=0.0)]
        run_dir = _make_run(self.tmpdir, frames)
        bogus_path = self.tmpdir / "does-not-exist.txt"
        _, errors = validate_run.validate_run(run_dir, bogus_path)
        # Missing segment map is itself flagged
        self.assertTrue(any("segment map is empty" in e for e in errors), errors)

    # ---------- Rule 5: required fields per schema version ----------

    def test_v02_frame_missing_required_extended_field_fails(self):
        frames = [_frame(time=0.0)]
        del frames[0]["tire_slip_fl"]
        run_dir = _make_run(self.tmpdir, frames)
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("tire_slip_fl" in e for e in errors), errors)

    def test_null_optional_value_allowed(self):
        """Null values are allowed for fields not in REQUIRED_NON_NULL."""
        frames = [_frame(time=0.0, opponentMinDistance=None, damage=None)]
        run_dir = _make_run(self.tmpdir, frames)
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertEqual(errors, [])

    def test_unsupported_schema_version_fails(self):
        frames = [_frame(time=0.0, schema_version="v9.9")]
        run_dir = _make_run(self.tmpdir, frames, schema_version="v9.9")
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(
            any("unsupported schema_version" in e or "not in supported set" in e for e in errors),
            errors,
        )

    # ---------- Structural ----------

    def test_missing_manifest_fails(self):
        frames = [_frame(time=0.0)]
        run_dir = _make_run(self.tmpdir, frames, omit_manifest=True)
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("missing manifest.json" in e for e in errors), errors)

    def test_invalid_json_frame_fails_gracefully(self):
        run_dir = self.tmpdir / "runs" / "broken"
        run_dir.mkdir(parents=True)
        (run_dir / "frames.ndjson").write_text(
            json.dumps(_frame(time=0.0)) + "\n{not json}\n",
            encoding="utf-8",
        )
        (run_dir / "manifest.json").write_text(
            json.dumps({"run_id": "test-run-1", "schema_version": "v0.2"}),
            encoding="utf-8",
        )
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("invalid JSON" in e for e in errors), errors)

    def test_not_a_directory_fails(self):
        bogus = self.tmpdir / "does-not-exist"
        _, errors = validate_run.validate_run(bogus, self.segments_path)
        self.assertTrue(any("not a directory" in e for e in errors), errors)

    def test_empty_frames_file_fails(self):
        run_dir = self.tmpdir / "runs" / "empty"
        run_dir.mkdir(parents=True)
        (run_dir / "frames.ndjson").write_text("", encoding="utf-8")
        (run_dir / "manifest.json").write_text(
            json.dumps({"run_id": "test-run-1", "schema_version": "v0.2"}),
            encoding="utf-8",
        )
        _, errors = validate_run.validate_run(run_dir, self.segments_path)
        self.assertTrue(any("no frames" in e for e in errors), errors)

    # ---------- CLI exit codes ----------

    def test_cli_exits_zero_on_pass(self):
        frames = [_frame(time=0.0), _frame(time=0.1)]
        run_dir = _make_run(self.tmpdir, frames)
        exit_code = validate_run.main([
            str(run_dir),
            "--segments-file", str(self.segments_path),
        ])
        self.assertEqual(exit_code, 0)

    def test_cli_exits_one_on_fail(self):
        frames = [_frame(time=0.0, segment_id="s99_bogus")]
        run_dir = _make_run(self.tmpdir, frames)
        exit_code = validate_run.main([
            str(run_dir),
            "--segments-file", str(self.segments_path),
        ])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
