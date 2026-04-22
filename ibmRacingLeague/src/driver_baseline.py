#!/usr/bin/env python3
"""
Phase 2 Day 1 baseline driver for TORCS via the SCR / snakeoil3 UDP protocol.

Connects to a running `scr_server` instance and drives a Corkscrew lap using a
minimum-viable policy:

    steering  = proportional to (angle - trackPos * bias)
    throttle  = open loop until target speed, then coast
    brake     = only if we overshoot the target
    gear      = RPM-based shift table

No Granite, no PID tuning, no segment awareness. Those are Phase 3.

Run order:
    1. Start TORCS with `scr_server 1` as the only selected driver on Corkscrew.
    2. In a separate shell: `python src/driver_baseline.py`
    3. TORCS unfreezes and the car drives a lap.

Assumes `C:\\torcs\\gym_torcs\\snakeoil3_gym.py` is on the machine. Override
the path with `GYM_TORCS_DIR` env var if your layout differs.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

DEFAULT_GYM_TORCS_DIR = os.environ.get(
    "GYM_TORCS_DIR", r"C:\torcs\gym_torcs"
)
sys.path.insert(0, DEFAULT_GYM_TORCS_DIR)

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

try:
    import snakeoil3_gym as snakeoil
except ImportError as exc:
    print(
        f"ERROR: could not import snakeoil3_gym from {DEFAULT_GYM_TORCS_DIR}.\n"
        f"       Set GYM_TORCS_DIR to the folder containing snakeoil3_gym.py.\n"
        f"       Details: {exc}",
        file=sys.stderr,
    )
    sys.exit(1)

from log_telemetry import TelemetryLogger


TARGET_SPEED_KMH = 55.0
STEER_LOCK = 0.785398
TRACK_POS_BIAS = 0.5
OFFTRACK_RECOVERY_STEER = 0.5
GEAR_UP_RPM = 7000
GEAR_DOWN_RPM = 3000
MAX_STEPS = 20000
STALE_LAP_LIMIT = 400

# List of (start_m, end_m, speed_kmh). If the car's trackDistance falls inside
# a window, the controller uses that speed instead of TARGET_SPEED_KMH.
# Populated from --slow-zone CLI flags. First match wins.
SLOW_ZONES: list[tuple[float, float, float]] = []

# Full segment map: list of (start_m, end_m, speed_kmh) covering the whole lap.
# Populated from --segments PATH (derived by scripts/derive_segments.py).
# Takes precedence over SLOW_ZONES when set.
SEGMENTS: list[tuple[float, float, float]] = []


def target_speed_for(state: dict) -> float:
    dist = float(state.get("distFromStart", state.get("distRaced", 0.0)) or 0.0)
    for start, end, speed in SEGMENTS:
        if start <= dist <= end:
            return speed
    for start, end, speed in SLOW_ZONES:
        if start <= dist <= end:
            return speed
    return TARGET_SPEED_KMH


def pick_gear(state: dict) -> int:
    gear = int(state.get("gear", 1)) or 1
    rpm = float(state.get("rpm", 0.0))
    if rpm > GEAR_UP_RPM and gear < 6:
        return gear + 1
    if rpm < GEAR_DOWN_RPM and gear > 1:
        return gear - 1
    return max(gear, 1)


def drive(state: dict) -> dict:
    angle = float(state.get("angle", 0.0))
    track_pos = float(state.get("trackPos", 0.0))
    speed_x = float(state.get("speedX", 0.0))

    if abs(track_pos) > 1.0:
        steer = -OFFTRACK_RECOVERY_STEER if track_pos > 0 else OFFTRACK_RECOVERY_STEER
    else:
        steer = (angle - track_pos * TRACK_POS_BIAS) / STEER_LOCK
    steer = max(-1.0, min(1.0, steer))

    target = target_speed_for(state)
    err = speed_x - target
    # Proportional brake: 6% per km/h overshoot, capped at 0.8, with a 1 km/h
    # deadband so we don't pump the pedal at target. Below target: full accel
    # (matches the original behavior — Run 014 regressed because this branch
    # was gated on `< target - 1.0` which starved straights of throttle).
    if err > 1.0:
        accel = 0.0
        brake = min(0.8, (err - 1.0) * 0.06)
    elif speed_x < target:
        accel = 0.3
        brake = 0.0
    else:
        accel = 0.1
        brake = 0.0

    gear = pick_gear(state)

    return {
        "steer": steer,
        "accel": accel,
        "brake": brake,
        "gear": gear,
        "clutch": 0.0,
        "focus": [-90, -45, 0, 45, 90],
        "meta": 0,
    }


def first_scalar(value):
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    return value


def _controller_reason(sensors: dict, action: dict) -> str:
    if abs(float(sensors.get("trackPos", 0.0) or 0.0)) > 1.0:
        return "off_track_recovery"
    if float(action.get("brake", 0.0) or 0.0) > 0.0:
        return "braking"
    if float(action.get("accel", 0.0) or 0.0) >= 0.3:
        return "accelerating"
    return "coasting"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TORCS baseline driver (SCR/snakeoil3).")
    parser.add_argument("--no-log", action="store_true",
                        help="Disable per-tick telemetry archive under telemetry/runs/.")
    parser.add_argument("--run-dir", default=None,
                        help="Override run output directory (default: auto timestamp under telemetry/runs/).")
    parser.add_argument("--notes", default="",
                        help="Free-text note recorded in manifest.json.")
    parser.add_argument("--target-speed", type=float, default=TARGET_SPEED_KMH,
                        help=f"Controller target speed in km/h (default: {TARGET_SPEED_KMH}).")
    parser.add_argument("--slow-zone", action="append", default=[],
                        metavar="START:END:SPEED",
                        help="Per-segment slow zone keyed on trackDistance, e.g. "
                             "'2400:2800:40'. Repeat for multiple zones.")
    parser.add_argument("--segments", type=Path, default=None,
                        metavar="PATH",
                        help="Path to a segments.yaml produced by scripts/derive_segments.py. "
                             "Each segment contributes a (start_m, end_m, target_speed_kmh) "
                             "window to the speed lookup; takes precedence over --slow-zone.")
    return parser.parse_args(argv)


def _parse_slow_zones(raw: list[str]) -> list[tuple[float, float, float]]:
    zones = []
    for spec in raw:
        parts = spec.split(":")
        if len(parts) != 3:
            raise ValueError(f"--slow-zone expects START:END:SPEED, got {spec!r}")
        start, end, speed = (float(p) for p in parts)
        if end <= start:
            raise ValueError(f"--slow-zone {spec!r}: end ({end}) must be > start ({start})")
        zones.append((start, end, speed))
    return zones


def _load_segments(path: Path) -> list[tuple[float, float, float]]:
    """Parse the narrow subset of segments.yaml we care about.

    We avoid a PyYAML dependency because the file is machine-generated by
    derive_segments.py in a fixed shape: each segment is an item under
    `segments:` with at least `start_m`, `end_m`, and `target_speed_kmh`
    scalar children. Anything else (kind, id, observed: ...) is ignored.
    """
    text = path.read_text()
    segments: list[tuple[float, float, float]] = []
    in_segments = False
    current: dict[str, float] = {}

    def _flush():
        if {"start_m", "end_m", "target_speed_kmh"} <= current.keys():
            segments.append((current["start_m"], current["end_m"], current["target_speed_kmh"]))

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" "):
            in_segments = line.strip() == "segments:"
            if not in_segments:
                _flush()
                current = {}
            continue
        if not in_segments:
            continue
        stripped = line.lstrip()
        if stripped.startswith("- "):
            _flush()
            current = {}
            stripped = stripped[2:]
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if key in ("start_m", "end_m", "target_speed_kmh") and value:
            try:
                current[key] = float(value)
            except ValueError:
                pass

    _flush()
    segments.sort(key=lambda s: s[0])
    return segments


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    # drive() reads TARGET_SPEED_KMH at module scope, so override here when
    # --target-speed is passed. Keeps the experiment-sweep workflow one-line.
    global TARGET_SPEED_KMH, SLOW_ZONES, SEGMENTS
    TARGET_SPEED_KMH = args.target_speed
    SLOW_ZONES = _parse_slow_zones(args.slow_zone)
    SEGMENTS = _load_segments(args.segments) if args.segments else []

    print(f"[driver_baseline] snakeoil3 path: {DEFAULT_GYM_TORCS_DIR}")
    print(f"[driver_baseline] target speed: {TARGET_SPEED_KMH} km/h")
    if SEGMENTS:
        print(f"[driver_baseline] segments: {len(SEGMENTS)} from {args.segments}")
    for start, end, speed in SLOW_ZONES:
        print(f"[driver_baseline] slow zone: {start:.0f}-{end:.0f}m @ {speed} km/h")
    print("[driver_baseline] connecting to scr_server on 3001...")

    logger: TelemetryLogger | None = None
    if not args.no_log:
        manifest_kwargs = dict(
            track="corkscrew",
            car="unknown",
            driver="louis",
            notes=args.notes,
        )
        if args.run_dir:
            import uuid as _uuid
            from log_telemetry import _git_sha
            logger = TelemetryLogger(
                Path(args.run_dir),
                run_id=str(_uuid.uuid4()),
                controller_type="baseline",
                controller_variant_id=_git_sha(),
                **manifest_kwargs,
            )
        else:
            logger = TelemetryLogger.for_new_run(
                controller_type="baseline",
                **manifest_kwargs,
            )
        print(f"[driver_baseline] telemetry archive: {logger.run_dir}")

    # snakeoil3_gym's Client() constructor re-parses sys.argv via getopt and
    # rejects any flag it doesn't know (e.g. our --notes). Our args have
    # already been consumed above, so neuter argv before handing off.
    sys.argv = [sys.argv[0]]
    client = snakeoil.Client(p=3001)
    client.MAX_STEPS = MAX_STEPS

    step = 0
    race_started = False
    stale_lap_ticks = 0
    lap_splits: list[float] = []
    last_lap_seen = 0.0
    last_cur_lap = 0.0
    current_lap_number = 1
    race_finalized = False
    stop_reason = "maxSteps reached"

    try:
        for step in range(MAX_STEPS):
            client.get_servers_input()
            sensors = {k: first_scalar(v) for k, v in client.S.d.items()}

            cur_lap = float(sensors.get("curLapTime", 0.0) or 0.0)
            last_lap = float(sensors.get("lastLapTime", 0.0) or 0.0)
            speed_x = float(sensors.get("speedX", 0.0) or 0.0)

            def _is_duplicate(candidate: float) -> bool:
                return bool(lap_splits) and abs(lap_splits[-1] - candidate) < 1.0

            if last_lap > 0 and abs(last_lap - last_lap_seen) > 1e-3:
                if not _is_duplicate(last_lap):
                    lap_splits.append(last_lap)
                    print(f"[driver_baseline] LAP {len(lap_splits)} complete (lastLapTime): {last_lap:.3f}s")
                    current_lap_number = len(lap_splits) + 1
                    race_finalized = True
                last_lap_seen = last_lap

            if last_cur_lap > 30.0 and cur_lap < 2.0 and cur_lap < last_cur_lap - 10.0:
                if not _is_duplicate(last_cur_lap):
                    lap_splits.append(last_cur_lap)
                    print(f"[driver_baseline] LAP {len(lap_splits)} complete (curLapTime reset): {last_cur_lap:.3f}s")
                    current_lap_number = len(lap_splits) + 1
                    race_finalized = True

            if cur_lap > 0.1:
                race_started = True

            if race_started:
                if abs(cur_lap - last_cur_lap) < 1e-4:
                    stale_lap_ticks += 1
                    if stale_lap_ticks >= STALE_LAP_LIMIT:
                        if cur_lap > 10.0 and not _is_duplicate(cur_lap):
                            lap_splits.append(cur_lap)
                            print(f"[driver_baseline] LAP {len(lap_splits)} complete (final, on race-end): {cur_lap:.3f}s")
                        stop_reason = f"race ended (curLapTime frozen at {cur_lap:.2f}s for {stale_lap_ticks} ticks)"
                        break
                else:
                    stale_lap_ticks = 0

            last_cur_lap = cur_lap

            action = drive(sensors)
            for k, v in action.items():
                client.R.d[k] = v
            client.respond_to_server()

            # Stop logging once the race is over: scr_server keeps sending
            # post-race frames with curLapTime reset/frozen, which would
            # violate the schema's monotonic-time rule.
            if logger is not None and not race_finalized:
                logger.log_frame(
                    sensors=sensors,
                    action=action,
                    controller_reason=_controller_reason(sensors, action),
                    lap_number=current_lap_number,
                )
            if step % 200 == 0:
                print(
                    f"[driver_baseline] step={step} "
                    f"speed={speed_x:.1f} "
                    f"trackPos={sensors.get('trackPos', 0):.2f} "
                    f"lapTime={cur_lap:.2f}"
                )
    except KeyboardInterrupt:
        stop_reason = "KeyboardInterrupt"
        print("\n[driver_baseline] interrupted by user")
    finally:
        try:
            client.shutdown()
        except Exception:
            pass
        if logger is not None:
            best_lap = min(lap_splits) if lap_splits else None
            total_time = sum(lap_splits) if lap_splits else None
            final_damage = None
            try:
                final_damage = float(sensors.get("damage", 0.0) or 0.0)
            except (NameError, TypeError, ValueError):
                final_damage = None
            outcome = {
                "completed": bool(lap_splits),
                "crashed": False,
                "laps_completed": len(lap_splits),
                "best_lap_seconds": best_lap,
                "total_time_seconds": total_time,
                "final_damage": final_damage,
                "stop_reason": stop_reason,
                "steps": step,
            }
            try:
                logger.close(outcome=outcome)
            except Exception as exc:
                print(f"[driver_baseline] warning: telemetry close failed: {exc}", file=sys.stderr)
        print(f"[driver_baseline] finished after {step} steps — {stop_reason}")
        if lap_splits:
            best = min(lap_splits)
            total = sum(lap_splits)
            print(f"[driver_baseline] laps completed: {len(lap_splits)}")
            for i, t in enumerate(lap_splits, 1):
                marker = " (best)" if t == best else ""
                print(f"[driver_baseline]   lap {i}: {t:.3f}s{marker}")
            print(f"[driver_baseline] total: {total:.3f}s  best: {best:.3f}s")
        else:
            print("[driver_baseline] no laps recorded (lastLapTime never advanced)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
