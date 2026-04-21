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

## What's next

1. **Tonight (Apr 21):** start writing `src/driver_baseline.py` — a proper Python class that replaces snakeoil3's demo controller and drives a clean Corkscrew lap using sensor-threshold rules. (Smoke test was supposed to be tonight's goal; instead it ran this morning ahead of schedule.)
2. **Phase 2 core work** (originally May 4–14, now starting Apr 21): extended telemetry logger that reads from the `snakeoil3.state` dict per tick; wire `scripts/run_race.py` full impl to orchestrate both processes; 5-lap average baseline time recorded.
3. **Then:** first labeled run archives → validator enforces schema → `telemetry/runs/` becomes a dataset we can show Granite for Phase 3 tuning.

---

## Schedule status

- **Velocity buffer: +7 days** ahead of original plan (was +6; Phase 2 Day 1 smoke test came in ~9 days early, banked 1 extra buffer day)
- **Phase 1 Track A** (solo code prep): shipped in one session, all 7 items complete (validator + tests, segment map, 3 script skeletons, kickoff doc)
- **Phase 1 local env**: TORCS + Granite + Continue + repo + Python deps + end-to-end smoke test all verified on the dev machine as of 2026-04-21 AM. Fully closed.
- **Phase 2 Day 1**: smoke test passed pre-schedule. Real work (writing `driver_baseline.py`) starts tonight.

Target submission: **2026-07-01** · Internal buffer target: submit by **2026-06-28**.

---

## Why it matters (the strategy angle, if you care)

Every team in this competition gets the same sim, same starter code, same Granite models. Our edge isn't compute or a better model — **it's the richness and labeling of the telemetry we capture from our own laps.** Every run gets archived with full sensor data, tire slip, lateral g, segment-by-segment deltas, and smoothness scores. Then we feed that dataset back to Granite for review sessions.

Not a model race. A data-density race.

Full strategy writeup: `docs/roadmap.md` → "Data advantage" section.
