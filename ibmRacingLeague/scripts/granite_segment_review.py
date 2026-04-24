#!/usr/bin/env python3
"""
Offline Granite-assisted analysis of a TORCS run.

Reads a run archive (manifest.json + segment_report.md), grounds the prompt
in those artifacts, and asks IBM Granite (granite4:tiny-h via Ollama) to
recommend specific segment-tuning changes for the next iteration.

Per docs/granite-validation.md, Granite is NOT in the runtime control loop
(Mamba/SSM layers are CPU-only at 10-20 tok/sec, incompatible with the
20 ms tick rate). Use it offline like this — between runs, on grounded
inputs that are entirely in the prompt.

Usage
-----
    python scripts/granite_segment_review.py telemetry/runs/2026-04-22T20-49-34
    python scripts/granite_segment_review.py <run_dir> --baseline <other_run_dir>
    python scripts/granite_segment_review.py <run_dir> --model granite4:tiny-h \\
        --ollama-host http://localhost:11434

Output: <run_dir>/granite_review.md (overwritten if exists).

Exit codes: 0 success, 1 missing artifacts, 2 Ollama unreachable, 3 Granite error.
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
import time
import urllib.error
import urllib.request
from pathlib import Path


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load_run(run_dir: Path) -> tuple[dict, str]:
    manifest_path = run_dir / "manifest.json"
    report_path = run_dir / "segment_report.md"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing {manifest_path}")
    if not report_path.exists():
        raise FileNotFoundError(
            f"missing {report_path} — run scripts/segment_report.py first"
        )
    manifest = json.loads(_read_text(manifest_path))
    report = _read_text(report_path)
    return manifest, report


def _manifest_summary(manifest: dict) -> str:
    outcome = manifest.get("outcome", {})
    lines = [
        f"- run_id: {manifest.get('run_id', 'unknown')}",
        f"- controller_variant_id: {manifest.get('controller_variant_id', 'unknown')}",
        f"- track: {manifest.get('track', 'unknown')}",
        f"- car: {manifest.get('car', 'unknown')}",
        f"- best_lap_seconds: {outcome.get('best_lap_seconds', 'n/a')}",
        f"- total_time_seconds: {outcome.get('total_time_seconds', 'n/a')}",
        f"- laps_completed: {outcome.get('laps_completed', 0)}",
        f"- crashed: {outcome.get('crashed', False)}",
        f"- final_damage: {outcome.get('final_damage', 0.0)}",
        f"- stop_reason: {outcome.get('stop_reason', 'n/a')}",
    ]
    notes = manifest.get("notes")
    if notes:
        lines.append(f"- notes: {notes}")
    return "\n".join(lines)


def _build_prompt(
    manifest: dict,
    report: str,
    baseline_manifest: dict | None,
    baseline_report: str | None,
) -> str:
    target_summary = _manifest_summary(manifest)

    parts = [
        "You are reviewing a single lap of a TORCS race on the Corkscrew track,",
        "driven by a segment-based deterministic Python controller (PID steering,",
        "lookahead braking, per-segment throttle caps from segments.yaml).",
        "",
        "TARGET RUN MANIFEST",
        "-------------------",
        target_summary,
        "",
        "TARGET RUN SEGMENT REPORT",
        "-------------------------",
        report.strip(),
    ]

    if baseline_manifest is not None and baseline_report is not None:
        parts += [
            "",
            "BASELINE RUN MANIFEST (for comparison)",
            "--------------------------------------",
            _manifest_summary(baseline_manifest),
            "",
            "BASELINE RUN SEGMENT REPORT",
            "---------------------------",
            baseline_report.strip(),
        ]

    parts += [
        "",
        "TASK",
        "----",
        "Using ONLY the data above (do not invent segments, sensors, or numbers",
        "that are not in the prompt), answer the following. Be concise and",
        "specific — name segment ids and exact target_speed_kmh changes.",
        "",
        "1. Top 3 segments where the controller is leaving the most time on the",
        "   table (slow vs. its own target_speed_kmh, or wide safety margin).",
        "2. Top 3 segments where the controller is closest to losing the car",
        "   (peak |trackPos| approaching 1.0, or HOT ENTRY flagged).",
        "3. For each of the 6 segments above, propose ONE concrete tuning change",
        "   in the form: 'set <segment_id> target_speed_kmh from X to Y because Z.'",
        "4. One overall risk to watch on the next run.",
        "",
        "If the data does not support an answer to a question, say so plainly",
        "rather than guessing.",
    ]
    return "\n".join(parts)


def _call_ollama(
    prompt: str, model: str, host: str, timeout_seconds: int = 600
) -> str:
    url = f"{host.rstrip('/')}/api/generate"
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                # Lower temperature for grounded analysis; we want the model
                # to lean on what's in the prompt, not improvise.
                "temperature": 0.2,
                "num_ctx": 8192,
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(f"Ollama unreachable at {url}: {e}") from e
    if "response" not in body:
        raise RuntimeError(f"Granite returned no 'response' field: {body!r}")
    return body["response"].strip()


def _format_review(
    target_dir: Path,
    target_manifest: dict,
    baseline_dir: Path | None,
    baseline_manifest: dict | None,
    model: str,
    granite_response: str,
    elapsed_seconds: float,
) -> str:
    parts = [
        f"# Granite review — {target_dir.name}",
        "",
        f"**Model:** `{model}`  ",
        f"**Generated:** {time.strftime('%Y-%m-%dT%H:%M:%S%z')}  ",
        f"**Inference time:** {elapsed_seconds:.1f} s  ",
        f"**Run lap time:** "
        f"{target_manifest.get('outcome', {}).get('best_lap_seconds', 'n/a')} s  ",
    ]
    if baseline_dir is not None and baseline_manifest is not None:
        parts.append(
            f"**Compared against baseline:** `{baseline_dir.name}` "
            f"({baseline_manifest.get('outcome', {}).get('best_lap_seconds', 'n/a')} s)  "
        )
    parts += [
        "",
        "> Granite was prompted with the manifest + segment_report only — no",
        "> raw frames, no segments.yaml. Treat its suggestions as hypotheses",
        "> to validate against telemetry, not directives.",
        "",
        "---",
        "",
        granite_response,
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Path to a run directory (must contain manifest.json + segment_report.md).",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Optional second run dir to include for comparison context.",
    )
    parser.add_argument(
        "--model",
        default="granite4:tiny-h",
        help="Ollama model id. Default: granite4:tiny-h. Per granite-validation.md, "
        "do NOT use 350m-h here — it hallucinates on domain-specific facts.",
    )
    parser.add_argument(
        "--ollama-host",
        default="http://localhost:11434",
        help="Ollama base URL. Default: http://localhost:11434.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=600,
        help="HTTP timeout for the Granite call (default 600s — Mamba CPU "
        "inference can be slow on cold start).",
    )
    parser.add_argument(
        "--print-prompt",
        action="store_true",
        help="Print the constructed prompt and exit without calling Granite.",
    )
    args = parser.parse_args()

    try:
        target_manifest, target_report = _load_run(args.run_dir)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    baseline_manifest = None
    baseline_report = None
    if args.baseline is not None:
        try:
            baseline_manifest, baseline_report = _load_run(args.baseline)
        except FileNotFoundError as e:
            print(f"error (baseline): {e}", file=sys.stderr)
            return 1

    prompt = _build_prompt(
        target_manifest, target_report, baseline_manifest, baseline_report
    )

    if args.print_prompt:
        print(prompt)
        return 0

    print(
        f"calling {args.model} at {args.ollama_host} "
        f"(prompt: {len(prompt)} chars)...",
        file=sys.stderr,
    )
    t0 = time.monotonic()
    try:
        response = _call_ollama(
            prompt, args.model, args.ollama_host, args.timeout_seconds
        )
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2 if "unreachable" in str(e) else 3
    elapsed = time.monotonic() - t0
    print(f"granite responded in {elapsed:.1f}s", file=sys.stderr)

    review = _format_review(
        args.run_dir,
        target_manifest,
        args.baseline,
        baseline_manifest,
        args.model,
        response,
        elapsed,
    )
    out_path = args.run_dir / "granite_review.md"
    out_path.write_text(review, encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
