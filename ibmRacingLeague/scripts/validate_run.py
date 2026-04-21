#!/usr/bin/env python3
"""Validate a telemetry run archive against telemetry/SCHEMA.md.

Enforces the five validation rules from SCHEMA.md:

  1. Every frame has schema_version, run_id, time, segment_id (non-null).
  2. run_id is consistent across all frames in a file.
  3. time is monotonically non-decreasing.
  4. segment_id values all exist in the canonical segment map.
  5. Required fields per schema version are present (null allowed where marked).

Additional structural checks:

  - The run directory contains manifest.json (valid JSON).
  - The run directory contains frames.ndjson (every line is valid JSON).
  - manifest.run_id matches the run_id in frames.

Usage:
  python scripts/validate_run.py <runs/timestamp-dir>
  python scripts/validate_run.py <runs/timestamp-dir> --segments-file <path>

Exit codes:
  0 = pass
  1 = validation failures found
  2 = bad usage / unreadable input
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SUPPORTED_SCHEMAS = {"v0.1", "v0.2"}

# Rule 1: these four fields must be present AND non-null in every frame.
REQUIRED_NON_NULL = ("schema_version", "run_id", "time", "segment_id")

# Rule 5: required field presence by schema version.
# (nulls are allowed — we only check that the KEY is present)
REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    "v0.1": frozenset({
        "time", "speed", "rpm",
        "trackPosition", "trackDistance", "opponentMinDistance",
        "throttle", "brake", "steer",
    }),
    "v0.2": frozenset({
        # v0.1 core
        "time", "speed", "rpm",
        "trackPosition", "trackDistance", "opponentMinDistance",
        "throttle", "brake", "steer",
        # v0.2 additions
        "schema_version", "run_id", "segment_id", "lap_number",
        "gear",
        "tire_slip_fl", "tire_slip_fr", "tire_slip_rl", "tire_slip_rr",
        "wheel_spin_velocity_avg",
        "z_accel", "lateral_g", "angle_to_track_axis",
        "damage", "fuel",
        "distance_to_edge_left", "distance_to_edge_right",
        "track_sensors",
        "controller_type", "controller_variant_id", "controller_reason",
    }),
}


def load_segment_map(segments_path: Path) -> set[str]:
    """Read canonical segment IDs, one per line. Comments (#) and blank lines ignored."""
    if not segments_path.exists():
        return set()
    ids: set[str] = set()
    for line in segments_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ids.add(stripped)
    return ids


def validate_manifest(run_dir: Path, errors: list[str]) -> dict[str, Any] | None:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        errors.append(f"missing manifest.json at {manifest_path}")
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"manifest.json is not valid JSON: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append("manifest.json must be a JSON object")
        return None
    for required_key in ("run_id", "schema_version"):
        if required_key not in data:
            errors.append(f"manifest.json missing required key: {required_key}")
    schema_version = data.get("schema_version")
    if schema_version is not None and schema_version not in SUPPORTED_SCHEMAS:
        errors.append(
            f"manifest.schema_version={schema_version!r} not in supported set {sorted(SUPPORTED_SCHEMAS)}"
        )
    return data


def validate_frames(
    run_dir: Path,
    segment_map: set[str],
    manifest: dict[str, Any] | None,
    errors: list[str],
) -> int:
    """Validate frames.ndjson. Returns the number of frames checked."""
    frames_path = run_dir / "frames.ndjson"
    if not frames_path.exists():
        errors.append(f"missing frames.ndjson at {frames_path}")
        return 0

    expected_run_id = manifest.get("run_id") if manifest else None
    expected_schema: str | None = manifest.get("schema_version") if manifest else None

    prev_time: float | None = None
    seen_run_id: str | None = None
    frame_count = 0

    with frames_path.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            raw = raw.rstrip("\n")
            if not raw.strip():
                continue
            try:
                frame = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"line {lineno}: invalid JSON: {exc}")
                continue
            if not isinstance(frame, dict):
                errors.append(f"line {lineno}: frame must be a JSON object")
                continue

            frame_count += 1

            # Rule 1 — required non-null fields
            for key in REQUIRED_NON_NULL:
                if key not in frame:
                    errors.append(f"line {lineno}: missing required field '{key}'")
                elif frame[key] is None:
                    errors.append(f"line {lineno}: required field '{key}' is null")

            # Rule 2 — run_id consistency across all frames, and match manifest
            run_id = frame.get("run_id")
            if run_id is not None:
                if seen_run_id is None:
                    seen_run_id = run_id
                elif run_id != seen_run_id:
                    errors.append(
                        f"line {lineno}: run_id '{run_id}' differs from first-seen run_id '{seen_run_id}'"
                    )
                if expected_run_id is not None and run_id != expected_run_id:
                    errors.append(
                        f"line {lineno}: run_id '{run_id}' does not match manifest.run_id '{expected_run_id}'"
                    )

            # Rule 3 — time monotonically non-decreasing
            t = frame.get("time")
            if isinstance(t, (int, float)):
                if prev_time is not None and t < prev_time:
                    errors.append(
                        f"line {lineno}: time went backwards: {t} < previous {prev_time}"
                    )
                prev_time = t
            else:
                if "time" in frame and frame.get("time") is not None:
                    errors.append(f"line {lineno}: time must be a number, got {type(t).__name__}")

            # Rule 4 — segment_id must exist in canonical map (skip check if map empty)
            segment_id = frame.get("segment_id")
            if segment_map and segment_id is not None and segment_id not in segment_map:
                errors.append(
                    f"line {lineno}: segment_id '{segment_id}' not in canonical segment map"
                )

            # Rule 5 — required fields per schema version (presence, null ok)
            frame_schema = frame.get("schema_version") or expected_schema
            if frame_schema in REQUIRED_FIELDS:
                required = REQUIRED_FIELDS[frame_schema]
                missing = required - frame.keys()
                if missing:
                    errors.append(
                        f"line {lineno}: missing {sorted(missing)} for schema {frame_schema}"
                    )
            elif frame_schema is not None and frame_schema not in SUPPORTED_SCHEMAS:
                errors.append(
                    f"line {lineno}: unsupported schema_version '{frame_schema}'"
                )

    if frame_count == 0:
        errors.append("frames.ndjson contained no frames")

    return frame_count


def validate_run(run_dir: Path, segments_path: Path) -> tuple[int, list[str]]:
    """Run all validation. Returns (frame_count, errors)."""
    errors: list[str] = []
    if not run_dir.is_dir():
        errors.append(f"not a directory: {run_dir}")
        return 0, errors
    segment_map = load_segment_map(segments_path)
    if not segment_map:
        errors.append(f"segment map is empty or missing at {segments_path} (Rule 4 cannot enforce)")
    manifest = validate_manifest(run_dir, errors)
    frame_count = validate_frames(run_dir, segment_map, manifest, errors)
    return frame_count, errors


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a TORCS telemetry run archive against telemetry/SCHEMA.md."
    )
    parser.add_argument("run_dir", help="Path to runs/<timestamp>/ directory")
    parser.add_argument(
        "--segments-file",
        default=None,
        help="Path to canonical segment ID list (default: telemetry/segments.txt relative to the run_dir)",
    )
    parser.add_argument(
        "--max-errors-shown",
        type=int,
        default=25,
        help="Max error lines to print (rest are counted). Default: 25",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    run_dir = Path(args.run_dir).resolve()
    if args.segments_file:
        segments_path = Path(args.segments_file).resolve()
    else:
        # Default: telemetry/segments.txt two levels up from runs/<ts>/
        segments_path = run_dir.parent.parent / "segments.txt"

    frame_count, errors = validate_run(run_dir, segments_path)

    if errors:
        print(f"FAIL: {run_dir}")
        print(f"  Frames checked: {frame_count}")
        print(f"  Errors: {len(errors)}")
        for err in errors[: args.max_errors_shown]:
            print(f"    - {err}")
        if len(errors) > args.max_errors_shown:
            print(f"    ... and {len(errors) - args.max_errors_shown} more")
        return 1

    print(f"PASS: {run_dir}")
    print(f"  Frames checked: {frame_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
