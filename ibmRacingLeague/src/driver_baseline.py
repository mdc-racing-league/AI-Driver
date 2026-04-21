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

import os
import sys
from pathlib import Path

DEFAULT_GYM_TORCS_DIR = os.environ.get(
    "GYM_TORCS_DIR", r"C:\torcs\gym_torcs"
)
sys.path.insert(0, DEFAULT_GYM_TORCS_DIR)

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


TARGET_SPEED_KMH = 55.0
STEER_LOCK = 0.785398
TRACK_POS_BIAS = 0.5
OFFTRACK_RECOVERY_STEER = 0.5
GEAR_UP_RPM = 7000
GEAR_DOWN_RPM = 3000
MAX_STEPS = 20000
STALE_LAP_LIMIT = 400


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

    if speed_x < TARGET_SPEED_KMH:
        accel = 0.3
        brake = 0.0
    elif speed_x > TARGET_SPEED_KMH + 10:
        accel = 0.0
        brake = 0.05
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


def main() -> int:
    print(f"[driver_baseline] snakeoil3 path: {DEFAULT_GYM_TORCS_DIR}")
    print(f"[driver_baseline] target speed: {TARGET_SPEED_KMH} km/h")
    print("[driver_baseline] connecting to scr_server on 3001...")

    client = snakeoil.Client(p=3001)
    client.MAX_STEPS = MAX_STEPS

    step = 0
    race_started = False
    stale_lap_ticks = 0
    lap_splits: list[float] = []
    last_lap_seen = 0.0
    last_cur_lap = 0.0
    stop_reason = "maxSteps reached"

    try:
        for step in range(MAX_STEPS):
            client.get_servers_input()
            sensors = {k: first_scalar(v) for k, v in client.S.d.items()}

            cur_lap = float(sensors.get("curLapTime", 0.0) or 0.0)
            last_lap = float(sensors.get("lastLapTime", 0.0) or 0.0)
            speed_x = float(sensors.get("speedX", 0.0) or 0.0)

            if last_lap > 0 and abs(last_lap - last_lap_seen) > 1e-3:
                lap_splits.append(last_lap)
                print(f"[driver_baseline] LAP {len(lap_splits)} complete (lastLapTime): {last_lap:.3f}s")
                last_lap_seen = last_lap

            if last_cur_lap > 30.0 and cur_lap < 2.0 and cur_lap < last_cur_lap - 10.0:
                lap_splits.append(last_cur_lap)
                print(f"[driver_baseline] LAP {len(lap_splits)} complete (curLapTime reset): {last_cur_lap:.3f}s")

            if cur_lap > 0.1:
                race_started = True

            if race_started:
                if abs(cur_lap - last_cur_lap) < 1e-4:
                    stale_lap_ticks += 1
                    if stale_lap_ticks >= STALE_LAP_LIMIT:
                        if not lap_splits or abs(lap_splits[-1] - cur_lap) > 0.5:
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
