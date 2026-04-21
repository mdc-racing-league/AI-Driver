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


TARGET_SPEED_KMH = 80.0
STEERING_GAIN = 0.10
TRACK_POS_BIAS = 0.5
GEAR_UP_RPM = 7000
GEAR_DOWN_RPM = 3000
MAX_STEPS = 2000


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

    steer = STEERING_GAIN * (angle - track_pos * TRACK_POS_BIAS)
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
    try:
        for step in range(client.maxSteps if hasattr(client, "maxSteps") else MAX_STEPS):
            client.get_servers_input()
            sensors = {k: first_scalar(v) for k, v in client.S.d.items()}
            action = drive(sensors)
            for k, v in action.items():
                client.R.d[k] = v
            client.respond_to_server()
            if step % 200 == 0:
                print(
                    f"[driver_baseline] step={step} "
                    f"speed={sensors.get('speedX', 0):.1f} "
                    f"trackPos={sensors.get('trackPos', 0):.2f} "
                    f"lapTime={sensors.get('curLapTime', 0):.2f}"
                )
    except KeyboardInterrupt:
        print("\n[driver_baseline] interrupted by user")
    finally:
        try:
            client.shutdown()
        except Exception:
            pass
        print(f"[driver_baseline] finished after {step} steps")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
