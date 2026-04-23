#!/usr/bin/env python3
"""SCHEMA v0.2 telemetry archiver. Imported by driver code; writes per-run archives.

Usage (from a driver module):

    from log_telemetry import TelemetryLogger

    logger = TelemetryLogger.for_new_run(
        controller_type="baseline",
        controller_variant_id="<git-sha>",
        track="corkscrew",
        car="car1-trb1",
        driver="louis",
    )
    try:
        while racing:
            sensors = client.S.d           # snakeoil3 sensor dict
            action = drive(sensors)         # controller output
            logger.log_frame(
                sensors=sensors,
                action=action,
                controller_reason="cruise",
                lap_number=lap_n,
            )
    finally:
        logger.close(outcome={
            "completed": True,
            "crashed": False,
            "laps_completed": 1,
            "best_lap_seconds": 212.806,
            "total_time_seconds": 212.806,
            "final_damage": 0.0,
        })

Schema reference: `telemetry/SCHEMA.md`. Validator: `scripts/validate_run.py`.
Segment IDs: `telemetry/segments.txt` — currently stubbed to `s00_start_straight`
until `scripts/segment_tagger.py` (Phase 2) computes proper distance-bucketed
IDs.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "v0.2"

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUNS_DIR = _REPO_ROOT / "telemetry" / "runs"

DEFAULT_SEGMENT_ID = "s00_start_straight"


def _git_sha(short: bool = True) -> str:
    try:
        args = ["git", "rev-parse", "--short", "HEAD"] if short else ["git", "rev-parse", "HEAD"]
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=2, cwd=_REPO_ROOT
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def _iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _iso_for_path() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H-%M-%S")


def _first_scalar(v: Any) -> Any:
    if isinstance(v, (list, tuple)) and v:
        return v[0]
    return v


def _as_float(v: Any) -> float | None:
    v = _first_scalar(v)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _as_int(v: Any) -> int | None:
    v = _first_scalar(v)
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _as_float_list(v: Any) -> list[float] | None:
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        out: list[float] = []
        for item in v:
            f = _as_float(item)
            if f is None:
                return None
            out.append(f)
        return out
    return None


def _opponent_min(opponents: Any) -> float | None:
    vals = _as_float_list(opponents)
    if not vals:
        return None
    finite = [x for x in vals if x < 200.0]
    return min(finite) if finite else None


def _map_sensors_to_frame(sensors: dict[str, Any]) -> dict[str, Any]:
    """snakeoil3 S.d → SCHEMA v0.2 fields. Unknown signals are emitted as null."""
    track_sensors = _as_float_list(sensors.get("track"))
    edge_left = track_sensors[0] if track_sensors and len(track_sensors) >= 1 else None
    edge_right = track_sensors[-1] if track_sensors and len(track_sensors) >= 1 else None

    wheel_spin = _as_float_list(sensors.get("wheelSpinVel"))
    wheel_spin_avg = sum(wheel_spin) / len(wheel_spin) if wheel_spin else None

    return {
        "time": _as_float(sensors.get("curLapTime")),
        "speed": _as_float(sensors.get("speedX")),
        "rpm": _as_int(sensors.get("rpm")),
        "trackPosition": _as_float(sensors.get("trackPos")),
        "trackDistance": _as_float(sensors.get("distFromStart")),
        "z": _as_float(sensors.get("z")),
        "opponentMinDistance": _opponent_min(sensors.get("opponents")),
        "angle_to_track_axis": _as_float(sensors.get("angle")),
        "damage": _as_float(sensors.get("damage")),
        "fuel": _as_float(sensors.get("fuel")),
        "distance_to_edge_left": edge_left,
        "distance_to_edge_right": edge_right,
        "track_sensors": track_sensors,
        "wheel_spin_velocity_avg": wheel_spin_avg,
        "tire_slip_fl": None,
        "tire_slip_fr": None,
        "tire_slip_rl": None,
        "tire_slip_rr": None,
        "z_accel": None,
        "lateral_g": None,
    }


class TelemetryLogger:
    """Writes SCHEMA v0.2 NDJSON frames + a manifest to telemetry/runs/<ts>/."""

    def __init__(
        self,
        run_dir: Path,
        *,
        run_id: str,
        controller_type: str,
        controller_variant_id: str,
        track: str = "corkscrew",
        car: str = "unknown",
        driver: str = "louis",
        weather: str = "clear",
        baseline_ref: str | None = None,
        notes: str = "",
    ) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.frames_path = self.run_dir / "frames.ndjson"
        self.manifest_path = self.run_dir / "manifest.json"
        self.run_id = run_id
        self.controller_type = controller_type
        self.controller_variant_id = controller_variant_id
        self._started_at = _iso_now()
        self._frames_file = self.frames_path.open("w", encoding="utf-8")
        self._frame_count = 0
        self._segment_ids_seen: set[str] = set()
        self._manifest_extras = {
            "track": track,
            "car": car,
            "driver": driver,
            "weather": weather,
            "baseline_ref": baseline_ref,
            "notes": notes,
        }
        self._closed = False

    @classmethod
    def for_new_run(
        cls,
        *,
        controller_type: str,
        controller_variant_id: str | None = None,
        runs_dir: Path | None = None,
        **manifest_kwargs: Any,
    ) -> "TelemetryLogger":
        runs_dir = Path(runs_dir) if runs_dir else DEFAULT_RUNS_DIR
        ts = _iso_for_path()
        run_dir = runs_dir / ts
        i = 1
        while run_dir.exists():
            run_dir = runs_dir / f"{ts}_{i}"
            i += 1
        return cls(
            run_dir,
            run_id=str(uuid.uuid4()),
            controller_type=controller_type,
            controller_variant_id=controller_variant_id or _git_sha(),
            **manifest_kwargs,
        )

    def log_frame(
        self,
        *,
        sensors: dict[str, Any],
        action: dict[str, Any] | None = None,
        controller_reason: str = "cruise",
        lap_number: int = 1,
        segment_id: str = DEFAULT_SEGMENT_ID,
        extra: dict[str, Any] | None = None,
    ) -> None:
        if self._closed:
            raise RuntimeError("TelemetryLogger is closed")

        frame = _map_sensors_to_frame(sensors)
        act = action or {}
        frame.update({
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "segment_id": segment_id,
            "lap_number": lap_number,
            "gear": _as_int(act.get("gear") if "gear" in act else sensors.get("gear")),
            "throttle": _as_float(act.get("accel")),
            "brake": _as_float(act.get("brake")),
            "steer": _as_float(act.get("steer")),
            "controller_type": self.controller_type,
            "controller_variant_id": self.controller_variant_id,
            "controller_reason": controller_reason,
        })
        if extra:
            frame.update(extra)

        self._frames_file.write(json.dumps(frame, separators=(",", ":")) + "\n")
        self._frame_count += 1
        self._segment_ids_seen.add(segment_id)

        # Periodic flush so a crashed driver still leaves usable data.
        if self._frame_count % 200 == 0:
            self._frames_file.flush()
            try:
                os.fsync(self._frames_file.fileno())
            except OSError:
                pass

    def close(self, outcome: dict[str, Any] | None = None) -> None:
        if self._closed:
            return
        try:
            self._frames_file.flush()
            self._frames_file.close()
        except Exception:
            pass
        manifest = {
            "run_id": self.run_id,
            "schema_version": SCHEMA_VERSION,
            "started_at": self._started_at,
            "ended_at": _iso_now(),
            "controller_type": self.controller_type,
            "controller_variant_id": self.controller_variant_id,
            "frame_count": self._frame_count,
            "segment_ids_seen": sorted(self._segment_ids_seen),
            "outcome": outcome or {},
            **{k: v for k, v in self._manifest_extras.items() if v is not None},
        }
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        self._closed = True

    def __enter__(self) -> "TelemetryLogger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close(outcome={"completed": exc_type is None, "crashed": False})


def _cli(argv: list[str]) -> int:
    """No-op CLI. This module is meant to be imported, not run directly.

    The old tail-a-JSON-logfile CLI (v0.1 scaffold) is removed. Driver code now
    writes SCHEMA v0.2 frames directly via TelemetryLogger — no sidecar process
    needed. Kept as a script entry so `python scripts/log_telemetry.py --help`
    shows this message rather than a stale interface.
    """
    msg = (
        "log_telemetry.py is a library, not a standalone CLI.\n"
        "Import TelemetryLogger from a driver module. See docstring for usage.\n"
    )
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
