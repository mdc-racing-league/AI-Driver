# Dev Environment Setup — Shareable Summary

*Plain-language write-up for sharing in chat. Last updated 2026-04-21 AM.*

---

## What I'm working on

**IBM Racing League** — a competition where teams build an AI driver for TORCS (The Open Racing Car Simulator) and try to win laps on the Corkscrew track. IBM's twist: we have to use their **Granite** AI models (via a local tool called Ollama) to help write and review the driver's code. Submission deadline is **July 1, 2026**.

Repo: https://github.com/LouisRodriguez12101815/ibmRacingLeague

---

## What got set up tonight (2026-04-20 / 21)

On my Windows desktop (RTX 3050, 6 GB VRAM):

- ✅ **Ollama 0.21.0** running locally at `http://localhost:11434`
- ✅ **Three IBM Granite models** pulled and verified:
  - `granite4:tiny-h` (4.2 GB) — chat + code review
  - `granite4:350m-h` (366 MB) — fast autocomplete while typing
  - `granite-embedding:30m` (62 MB) — semantic code search
- ✅ **VSCode + Continue extension** wired up, pointed at local Ollama
- ✅ **Granite responds through Continue chat** with coherent, domain-correct answers
- ✅ **TORCS installed** (IBM Quick Start bundle) at `C:\torcs\`
- ✅ **TORCS launches, Corkscrew track loads** — simulator is healthy
- ✅ **Repo cloned locally** to `%USERPROFILE%\ibmRacingLeague\`, opened in VSCode
- ✅ **Python 3.12.10** + `gym==0.26.2` installed — all Phase 2 dependencies in place
- ✅ **Key finding:** `snakeoil3_gym.py` (the TORCS UDP client) imports **only Python stdlib** — no third-party package needed for the core client
- ✅ **End-to-end smoke test PASSED** — `python snakeoil3_gym.py` connected to live TORCS Corkscrew race on first try; car drove around the track under snakeoil3's demo controller. Screenshot evidence in `docs/screenshots/2026-04-21_phase1-smoke-test-success.png`.

**Net result:** full local dev environment ready **and verified end-to-end**. Phase 2 Day 1 goal (prove the Python→TORCS loop works) already achieved — ~9 days ahead of original plan. Next working session writes actual driver code.

---

## Two findings worth calling out

### 1. Granite 4 runs CPU-only in Ollama 0.21.0

Even with a working CUDA GPU and plenty of free VRAM, `granite4:tiny-h` loads onto CPU. Root cause: Granite 4's `-h` suffix = **hybrid Mamba/transformer** architecture (40 Mamba layers + 4 transformer layers). Ollama 0.21.0 doesn't yet have GPU kernels for the Mamba recurrent state, so those layers run on CPU — and with 40/44 layers forced to CPU, Ollama reports 100% CPU.

**Not a config issue. Architectural runtime limitation.** Expected to land upstream in a future Ollama release.

**Takeaway:** accept ~15 tokens/sec for chat on local CPU, and offload heavy batch inference (segment analysis of many run archives) to Zo where RAM + cores are plentiful. Documented in `docs/granite-validation.md` so the next person doesn't burn an hour chasing VRAM.

### 2. The IBM bundle uses the SCR (Simulated Car Racing) architecture — our driver is a Python UDP client

This one reshapes Phase 2 planning. Originally I thought we'd write a C++ robot and compile it into TORCS's `drivers/` folder (the classic TORCS path). The IBM bundle is different:

- TORCS ships with a built-in robot called `scr_server`
- `scr_server` opens a UDP socket on port 3001 and **waits** for a client
- We write a **Python client** (using `snakeoil3_gym.py` from the bundle) that sends steering/throttle/brake actions and receives sensor data at 50 Hz

Diagram:

```
┌────────────────────┐    UDP :3001    ┌──────────────────────────┐
│ wtorcs.exe         │ <─────────────> │ Python client            │
│   + scr_server     │  sensors +      │ (our driver_baseline.py) │
│     (built in)     │  actions        │ via snakeoil3 protocol   │
└────────────────────┘                 └──────────────────────────┘
```

**Why this is good news:**
- No C++ toolchain needed
- Our driver is pure Python (Granite can read and review it naturally)
- Integrates cleanly with the existing Python tooling (validator, segment labeler, A/B harness)

Also explains a quirk: when you launch TORCS with `scr_server` as the driver, the window shows "Not Responding" on the loading screen. That's **expected** — it's blocked on a UDP `recvfrom()` waiting for our Python client. Looks like a crash; actually the happy path.

Fully documented in `docs/simulation-guide/03-running-our-driver.md`.

---

## Update — Apr 21 PM: `driver_baseline.py` done

Shipped the first real custom driver tonight. Three commits (`d9aeb4f`, `7091c72`, `379c7bb`) to get it from "crashes on first tick" → "finishes the race in P1 with 2–3 clean laps on Corkscrew."

What it does:
- Opens a UDP session to `scr_server` on port 3001
- Reads sensor dict (`angle`, `trackPos`, `speedX`, `rpm`) per tick
- Steers using canonical SCR formula: `(angle - trackPos * 0.5) / STEER_LOCK`, with an explicit off-track recovery mode for `|trackPos| > 1.0`
- Holds target speed ~55 km/h (conservative — Corkscrew has a hairpin)
- RPM-based gear shift (up at 7000, down at 3000)

Run 001 numbers (`telemetry/baseline.md`): **lap time `3:32.92`**, damages **0**, top speed 65 km/h, finished **P1**. `trackPos` stayed in ±0.66 the full race (never left the track). Phase 3 target is now concrete — we need to beat `3:00.98` (-15% of baseline) to hit the rubric. Evidence: `docs/screenshots/2026-04-21_phase2-day1-p1-finish.png` (TORCS Race Results screen).

Still TODO after Run 001: per-lap time logging (currently only total) and fixing the ghost-tick loop after race end. Both are next-session items, not correctness bugs.

## Update — Apr 22 AM: Run 001 soft bugs closed

Three iterations across 4 runs (`7fcfab3`, `1d2b003`, `9e1d1c3`) replaced both instrumentation gaps:

- **Per-lap timing now from the driver log.** Three-path capture: `lastLapTime` (primary), `curLapTime` reset (fallback), final-on-race-end (catches single-lap races where `scr_server` stops mid-lap). All three paths deduped against a 1 s tolerance so the same crossing can't double-count.
- **Race-end detection works.** Keyed on **stale `curLapTime`**, not on speed/lapTime zeros. Learned the hard way that after a race ends, `scr_server` keeps sending the **final frame frozen** (speed 64.8 km/h, lapTime 212.81 s) forever — zeros never come. With the new detector, loop exits at step ~10,700 instead of running to 99,999.
- **Run 002 (canonical):** `3:32.81` (`212.806 s`) from the driver log, matches scoreboard to 0.01 s. **Cross-run check across 4 runs: 0.144 s spread (0.068%)** — TORCS + our controller are effectively deterministic, so Phase 3 A/B comparisons can trust single-run deltas down to ~0.1 s. Evidence: `docs/screenshots/2026-04-22_phase2-day1-run002-clean.png`.

## Submission format — resolved 2026-04-22

Walked the live form at `https://forms.office.com/r/gD0gMZaTwP`. Field #6 is verbatim: **`"Standing start lap time - used to determine who qualifies"`**. So:

- Judging metric = **one standing-start lap on Corkscrew with the IBM F1 car** (form wording: *"Once your Corkscrew time trial is complete with the IBM F1 car"*). Not a race, not an N-lap average.
- Our 1-lap Quick Race setup is exactly the right regime. No 5-lap harness needed.
- **Three previously-unscoped deliverables** surfaced from the form fields and are now in the roadmap: verify the IBM F1 car is what `scr_server` uses, create a bespoke F1 livery (uni logo + team identifier), and assemble a presentation deck of completed SkillsBuild badges.

## What's next

1. **Phase 2 core work** (originally May 4–14, now active): extended SCHEMA v0.2 telemetry logger (`scripts/log_telemetry.py`) that reads from `snakeoil3.state` per tick; wire `scripts/run_race.py` to orchestrate both processes. 1-lap baseline stays canonical.
2. **Then:** first labeled run archives → validator enforces schema → `telemetry/runs/` becomes a dataset we feed Granite for Phase 3 tuning.
3. **Phase 4 pre-work (parallel):** verify the IBM F1 car in TORCS; sketch a livery concept in Paint/GIMP; start banking SkillsBuild badges.

---

## Schedule status

- **Velocity buffer: +9 days** ahead of original plan (was +7; tonight's driver_baseline.py ship banks 2 more days — the main Phase 2 deliverable landed on Apr 21 instead of May 4)
- **Phase 1 Track A** (solo code prep): shipped in one session, all 7 items complete (validator + tests, segment map, 3 script skeletons, kickoff doc)
- **Phase 1 local env**: TORCS + Granite + Continue + repo + Python deps + end-to-end smoke test all verified on the dev machine as of 2026-04-21 AM. Fully closed.
- **Phase 2 Day 1**: smoke test passed pre-schedule, then `driver_baseline.py` v1 written, tuned, and raced to a P1 finish on Corkscrew — all in one evening.

Target submission: **2026-07-01** · Internal buffer target: submit by **2026-06-28**.

---

## Why it matters (the strategy angle, if you care)

Every team in this competition gets the same sim, same starter code, same Granite models. Our edge isn't compute or a better model — **it's the richness and labeling of the telemetry we capture from our own laps.** Every run gets archived with full sensor data, tire slip, lateral g, segment-by-segment deltas, and smoothness scores. Then we feed that dataset back to Granite for review sessions.

Not a model race. A data-density race.

Full strategy writeup: `docs/roadmap.md` → "Data advantage" section.
