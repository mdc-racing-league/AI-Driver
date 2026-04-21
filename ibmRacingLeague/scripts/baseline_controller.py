#!/usr/bin/env python3
"""Simple TORCS baseline controller that reads telemetry and emits fixed throttle/brake/steer choices."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Listen to TORCS telemetry and write simple commands.")
    parser.add_argument("--source", "-s", default="/home/workspace/ibmRacingLeague/telemetry/raw.log", help="Path to newline-delimited JSON telemetry data.")
    parser.add_argument("--commands", "-c", default="/home/workspace/ibmRacingLeague/telemetry/baseline-commands.log", help="Path to append controller commands to.")
    parser.add_argument("--poll-interval", type=float, default=0.1, help="Seconds to wait for new telemetry lines.")
    return parser.parse_args()


def follow(path: Path, interval: float) -> Iterable[str]:
    while not path.exists():
        print(f"Waiting for telemetry at {path}...", file=sys.stderr)
        time.sleep(interval)
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        fh.seek(0, 2)
        while True:
            line = fh.readline()
            if not line:
                time.sleep(interval)
                continue
            yield line.strip()


def make_command(frame: dict[str, float]) -> dict[str, float]:
    speed = float(frame.get("speed", 0.0))
    track_pos = float(frame.get("trackPosition", 0.0))
    target_throttle = 0.85 if speed < 60 else 0.65 if speed < 120 else 0.4
    if track_pos > 0.25:
        steer = -0.2
    elif track_pos < -0.25:
        steer = 0.2
    else:
        steer = 0.05 * (track_pos * -1)
    brake = 0.0
    if speed > 130 and abs(track_pos) > 0.5:
        brake = 0.15
        target_throttle *= 0.6
    return {"time": frame.get("time", time.time()), "throttle": round(target_throttle, 3), "brake": round(brake, 3), "steer": round(steer, 3)}


def main() -> None:
    args = parse_args()
    source = Path(args.source)
    commands_path = Path(args.commands)
    commands_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Listening for telemetry at {source} and writing baseline commands to {commands_path}")
    with commands_path.open("a", encoding="utf-8") as cmd_fh:
        for raw in follow(source, args.poll_interval):
            if not raw:
                continue
            try:
                frame_raw = json.loads(raw)
            except json.JSONDecodeError:
                print("Skipping invalid telemetry line", raw, file=sys.stderr)
                continue
            frame = {k: (float(v) if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).lstrip('-').isdigit()) else 0.0) for k, v in frame_raw.items()}
            command = make_command(frame)
            cmd_fh.write(json.dumps(command) + "\n")
            cmd_fh.flush()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Baseline controller stopped", file=sys.stderr)
