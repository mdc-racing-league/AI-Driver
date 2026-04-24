# Granite Suggestions Log

A running log of where IBM Granite directly shaped this project — model selection,
architecture decisions, and (now) offline run analysis. Per
`docs/simulation-guide/05-granite-workflow.md`, the rubric for the IBM AI Racing
League submission rewards teams that can show **how** they used IBM Granite, not
just that they had it installed.

This log is honest about scope: most day-to-day Granite usage during development
ran through `continue.dev` chat in VSCode and isn't itemized here. The entries
below capture the *load-bearing* uses — decisions that wouldn't have happened
the same way without Granite, plus the offline analysis pipeline now wired into
the run loop.

---

## 2026-04-24 — Offline run-analysis pipeline (first Granite-in-the-pipeline artifact)

- **Script:** `scripts/granite_segment_review.py`
- **Model:** `granite4:tiny-h` via Ollama on Zo (`localhost:11434`)
- **Inputs:** A run's `manifest.json` + `segment_report.md`. Optionally a baseline
  run for comparison.
- **Prompt structure:** grounded — manifest summary + full segment table embedded
  in the prompt; Granite is asked to identify (a) top-3 time-leak segments,
  (b) top-3 risk segments, (c) one concrete `target_speed_kmh` change per segment,
  and (d) one risk to watch on the next run. Prompt explicitly says "do not invent
  segments, sensors, or numbers not in the prompt" — direct application of the
  hallucination guardrail from `docs/granite-validation.md`.
- **Output:** `<run_dir>/granite_review.md`, regenerated per run.
- **First invocation:** target run `telemetry/runs/2026-04-22T20-49-34/`
  (lap time 169.206 s, regression check). Granite finished in 57.8 s on Zo's CPU
  (matches the 10–20 tok/sec ceiling documented in `granite-validation.md`).
- **Granite's notable suggestion:** flagged s09 (entry 95 → target 58) and s13
  (entry 80 → target 58) as both slowest *and* highest-risk — consistent with
  what the segment_report's HOT ENTRY markers already show. Some reasoning
  slips (e.g., recommending we *raise* s09's target speed despite the hot entry)
  — captured transparently in the output, not suppressed.
- **Applied:** the script itself is committed; specific tuning suggestions
  pending validation against fresh telemetry. Will revisit after the next
  submission lap with `segments_submission.yaml`.
- **Why this matters for the submission:** answers "did you use IBM Granite in
  your project?" with a tangible artifact — Granite is now an automated
  reviewer in the run loop, not just an IDE chatbot.

---

## 2026-04-21 — Granite 4 hybrid → CPU inference (architecture-shaping finding)

- **Source:** `docs/granite-validation.md` § "Granite 4 hybrid architecture →
  CPU inference (2026-04-21)"
- **What we learned:** `granite4:tiny-h` and `granite4:350m-h` have the `-h`
  (hybrid Mamba/SSM) suffix. Ollama 0.21.0 has no GPU kernels for the
  recurrent layers (40 of 44 layers in `tiny-h`), so `ollama ps` reports
  `100% CPU` even with `OLLAMA_NUM_GPU=999` and free VRAM.
- **Decision this drove:** Granite **does not run in the 20 ms control loop**.
  CPU throughput is 10–20 tok/sec for `tiny-h`; first-token latency 10–30 s
  cold. Real-time control on TORCS sends actions every 20 ms (50 Hz), so
  Granite is architecturally incompatible with the inner loop.
- **Where Granite goes instead:** offline / between-runs analysis (see
  2026-04-24 entry above) and IDE-time code review via `continue.dev`.
- **Applied:** yes — the entire driver_baseline architecture reflects this
  decision. Driver is pure deterministic Python; LLMs only touch artifacts
  *between* runs.
- **Result:** consistent 60–70 s lap times in early Phase-2, dropping to
  160.666 s PB (Run 023) by Phase-3 day 3 — driver hot path stayed
  predictable while Granite supported the iteration loop from outside.

---

## 2026-04-20 / 2026-04-21 — Model selection validation (the rule we live by)

- **Source:** `docs/granite-validation.md` § Tests 1–3
- **What we tested:** all three Granite models on Zo via Ollama.
- **Granite's response that mattered:** `granite4:350m-h` confidently fabricated
  *"TORCS stands for Tor over SSL Relay"* — a clean hallucination on
  domain-specific trivia.
- **Decision this drove:** **"If the answer isn't fully in the prompt, don't use
  350m-h."** Codified in `docs/simulation-guide/05-granite-workflow.md`. We use
  `tiny-h` for any Granite call that requires reasoning over our domain (incl.
  the new offline analyzer); `350m-h` is reserved for purely in-context
  reformatting tasks where it can't drift.
- **Result:** zero documented hallucinations have made it into committed
  code or docs because of this rule.

---

## Continue.dev / chat usage during development (not itemized)

Continue.dev with `granite4:tiny-h` was used throughout Phase 2 and Phase 3 for
code review, controller-strategy reasoning, and explaining diffs — per the
patterns documented in `docs/simulation-guide/05-granite-workflow.md`. These
sessions are not individually logged here (they happen too often to itemize and
the value is qualitative — better questions asked, faster reads of unfamiliar
code), but the workflow itself is the deliverable: a documented, repeatable
practice of Granite-assisted iteration.

If the team wants individual entries logged from this point forward, the format
to follow (also in `05-granite-workflow.md`) is:

```markdown
## <YYYY-MM-DD> — <short title>
- Run: `runs/<timestamp>/`
- Prompt: <short version>
- Suggestion: <what Granite said>
- Applied: yes / no / partial
- Result: <lap-time delta, crash count delta, or other measurable>
```

---

## Forward-looking — open Granite work

- **Run the offline analyzer against the submission lap** once it's recorded.
  The `granite_review.md` it produces is a strong submission-video artifact:
  "here's our final lap, and here's what IBM Granite suggests we'd tune next."
- **Explore embedding-based run similarity search** using `granite-embedding:30m`.
  We have 13+ run archives — embedding their segment reports and running
  cosine similarity could surface "this run looks like Run 020 — and Run 020
  DNF'd at s08, watch out." Defer until after submission unless cycles permit.
- **Re-check Granite GPU support** on the next Ollama minor-version bump
  (open follow-up in `granite-validation.md`). If Mamba kernels land, the
  CPU-only constraint may relax.
