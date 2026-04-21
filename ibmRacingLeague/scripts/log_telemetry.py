#!/usr/bin/env python3
"""Tails TORCS telemetry output (JSON per line) and writes a normalized CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tail a TORCS telemetry log and extract a normalized CSV.")
    parser.add_argument(
        "--source",
        "-s",
        default="/home/workspace/ibmRacingLeague/telemetry/raw.log",
        help="Path to the raw telemetry log (newline-delimited JSON).",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="/home/workspace/ibmRacingLeague/telemetry/frames.csv",
        help="Path to write the normalized CSV frames.",
    )
    parser.add_argument(
        "--fields",
        "-f",
        default="time,speed,rpm,trackPosition,trackDistance,opponentMinDistance,throttle,brake,steer",
        help="Comma-separated list of telemetry fields to persist in order.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.2,
        help="Seconds to sleep when waiting for new data.",
    )
    return parser.parse_args()


def flatten_frame(frame: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    sensors = frame.get("sensors") or frame.get("telemetry") or {}
    if isinstance(sensors, dict):
        output.update(sensors)
    elif isinstance(sensors, list):
        for sensor in sensors:
            name = sensor.get("name") or sensor.get("id")
            value = sensor.get("value") or sensor.get("val")
            if name is not None:
                output[name] = value
    output.update({k: v for k, v in frame.items() if k not in ("sensors", "telemetry")})
    return output


def follow(path: Path, interval: float) -> Iterable[str]:
    if not path.exists():
        print(f"Waiting for telemetry file to appear at {path}", file=sys.stderr)
    while not path.exists():
        time.sleep(interval)
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        fh.seek(0, 2)
        while True:
            line = fh.readline()
            if not line:
                time.sleep(interval)
                continue
            yield line.strip()


def main() -> None:
    args = parse_args()
    source_path = Path(args.source)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_fields = [field.strip() for field in args.fields.split(",") if field.strip()]

    writer = None
    print(f"Listening for telemetry on {source_path} and writing frames to {output_path}")
    for raw_line in follow(source_path, args.poll_interval):
        if not raw_line:
            continue
        try:
            data = json.loads(raw_line)
        except json.JSONDecodeError:
            print("Skipping malformed line", raw_line, file=sys.stderr)
            continue
        frame = flatten_frame(data)
        row = {field: frame.get(field) for field in normalized_fields}
        if writer is None:
            output_path.write_text("", encoding="utf-8")
            csv_file = output_path.open("a", newline="", encoding="utf-8")
            writer = csv.DictWriter(csv_file, fieldnames=normalized_fields)
            writer.writeheader()
        writer.writerow(row)
        csv_file.flush()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Telemetry logger interrupted", file=sys.stderr)
        raise SystemExit(0)
