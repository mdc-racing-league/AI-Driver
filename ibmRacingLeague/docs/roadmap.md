# Roadmap & Phase Tracker

> Target: **2026-07-01** submission deadline. Today: 2026-04-23. Budget: ~10 weeks.
>
> **Current submission anchor:** Run 023 (commit `52252ea`) — `160.666 s` (`2:40.67`), damages 0, off-tracks 0. **−24.5% vs canonical baseline Run 006** (`212.986 s`). See `telemetry/baseline.md` and `docs/phase3-experiments.md` for the full progression.
>
> **Methodology reference:** [`docs/racing-methodology.md`](./racing-methodology.md) consolidates racing physics (GT2) + TORCS equations (Ahura) + RL insights (TORCS-Keras) into a single reference that each experiment tests against.

Legend: ✅ done · 🔄 in progress · ⬜ not started · ⚠️ blocked

---

## Phase 0 — Foundation (Apr 19–26)

- ⬜ Register team: https://ibm.biz/RegistrationTORCS *(Friday)*
- ✅ Join Discord
- 🔄 IBM SkillsBuild Granite course (Louis: ✅ done)
- ✅ GitHub repo `ibmRacingLeague` created (private)
- ✅ Branch renamed `master` → `main`
- ✅ Repo restructured for project
- ✅ Mission brief & Ollama docs stored in `docs/`
- ✅ Top-level `README.md` + `docs/simulation-guide/` runbook scaffolded (2026-04-20)

## Phase 1 — Environment setup & code prep (Apr 21 – May 3)

> **Two parallel tracks.** Solo code track starts **now** (Apr 21) so teammate-independent infrastructure is ready before Phase 2. Team setup track runs Apr 27 – May 3 as originally planned.

### Track A — Solo code prep (Apr 21–29) — Louis

Teammate-independent work that can happen before Phase 2 starts:

- ✅ Implement `scripts/validate_run.py` — full impl against `telemetry/SCHEMA.md` v0.2 (2026-04-20)
- ✅ Unit tests for `validate_run.py` using synthetic fixture runs — `tests/test_validate_run.py` (20 tests, all passing)
- ✅ Corkscrew track-segment map draft — `telemetry/segments.txt` (18 IDs, Phase 3 will tune against track reference data)
- ❌ ~~Skeleton `scripts/run_race.py`~~ — **dropped 2026-04-22**, two-PowerShell manual launch is faster than orchestration for a solo 1-lap regime
- ❌ ~~Skeleton `scripts/label_segments.py`~~ — **superseded 2026-04-22** by `telemetry/segments.yaml` + `scripts/segment_tagger.py` (Run 001 derivation)
- ❌ ~~Skeleton `scripts/ab_run.py`~~ — **dropped 2026-04-22**, manual single-variable A/B against Run 008/Run 023 anchors works cleanly
- ⬜ Draft `docs/phase1-kickoff.md` — agenda for Apr 27 team sync (strategy walk-through + SCHEMA overview)

**Exit:** code scaffolding is waiting for teammates on Day 1 of Phase 2.

### Track B — Team environment setup (Apr 27 – May 3)

Zo-side (shared / reproducible):
- ✅ Install Ollama on Zo (for testing Granite without local sim) — v0.21.0, `ollama serve` running
- ✅ Pull Granite models: `granite4:tiny-h` (4.2 GB), `granite4:350m-h` (366 MB), `granite-embedding:30m` (62 MB)
- ✅ Validate Granite responds correctly — see `docs/granite-validation.md`

**Solo project** — Track B collapses to a single Windows desktop (registration confirmed 2026-04-21).

Local machine (Windows desktop, RTX 3050 6 GB):
- ✅ Install VSCode (2026-04-21)
- ✅ Install Ollama locally (0.21.0 pre-existing) + pull Granite models (all three verified)
- ✅ Install continue.dev VSCode extension (2026-04-21)
- ✅ Configure `%USERPROFILE%\.continue\config.yaml` — Granite responds through Continue chat
- ✅ Install TORCS (IBM Quick Start bundle extracted to `C:\torcs\`) (2026-04-21)
- ✅ Confirm TORCS launches and Corkscrew loads (2026-04-21)
- ✅ Clone repo locally to `%USERPROFILE%\ibmRacingLeague\` (2026-04-21 AM)
- ✅ Python 3.12.10 verified; `gym==0.26.2` + `cloudpickle` + `gym_notices` installed via pip (2026-04-21 AM)
- ✅ Confirmed `snakeoil3_gym.py` uses **only stdlib** (`socket`, `sys`, `getopt`, `os`, `time`) — Phase 2 Day 1 smoke test has zero runtime-deps risk (2026-04-21 AM)
- ✅ **Python → UDP → TORCS smoke test passed** (2026-04-21 AM) — snakeoil3 client connected to `scr_server`, car driven around Corkscrew end-to-end. See `docs/screenshots/2026-04-21_phase1-smoke-test-success.png`.
- ⬜ Read `docs/simulation-guide/` + `telemetry/SCHEMA.md` end-to-end before Phase 2

**Exit criteria:** working sim, Granite chats through VSCode, strategy + schema docs reviewed. **Fully closed as of 2026-04-21 AM** — only remaining item is reading the simulation-guide + SCHEMA end-to-end (self-study, no blocker).

### Architecture discovery (2026-04-21)

The IBM bundle uses the **Simulated Car Racing (SCR) architecture**: TORCS ships with a built-in `scr_server` robot that opens a UDP socket (port 3001) and waits for an external Python client. Our driver is therefore a **Python UDP client** (subclass of `snakeoil3_gym.py` in `C:\torcs\gym_torcs\`), not a C++ robot compiled into `drivers/`. This simplifies Phase 2 significantly — no C++ toolchain needed. Fully documented in `docs/simulation-guide/03-running-our-driver.md`.

## Phase 2 — Baseline AI driver (Apr 30 – May 14) — *pulled forward 4 days*

- ✅ **Day 1 smoke test:** ran `python snakeoil3_gym.py` against a live `scr_server` race on Corkscrew — full Python→UDP→TORCS loop verified end-to-end (2026-04-21 AM). Demo controller drives poorly but that's expected; screenshot archived in `docs/screenshots/`.
- ✅ Implement `src/driver_baseline.py` as a `snakeoil3` subclass — completes a clean Corkscrew lap (2026-04-21 PM). Finishing **P1** with lap time **`3:32.92`**, damages **0**, top speed 65 km/h. `trackPos` stayed in `[-0.66, +0.66]` (never left the track). Canonical SCR steering `(angle - trackPos*0.5) / STEER_LOCK` + off-track recovery mode. Commits: `d9aeb4f`, `7091c72`, `379c7bb`. Evidence: `docs/screenshots/2026-04-21_phase2-day1-p1-finish.png`. Full run data: `telemetry/baseline.md`.
- ✅ Extended telemetry logger (SCHEMA v0.2 fields) — `scripts/log_telemetry.py` rewritten as importable `TelemetryLogger` library. Writes `frames.ndjson` + `manifest.json` per run; driver integrates via `--no-log`/`--run-dir`/`--notes`. 8 unit tests in `tests/test_log_telemetry.py`, all passing. Commits: `2d116fe`, `df41e63`, `487c6de`. (2026-04-22)
- ❌ ~~Wire `scripts/run_race.py` full impl~~ — **dropped 2026-04-22**; two-PowerShell manual launch remains the canonical regime
- ❌ ~~Test harness: 5-lap average, same start conditions — `scripts/run_race.py --laps 5`~~ — **dropped 2026-04-22.** Competition judges a *single standing-start lap* (submission form field #6 verbatim: `"Standing start lap time - used to determine who qualifies"`). A 5-lap mean would tune the controller to rolling-start dynamics, not standing-start. 1-lap Quick Race stays the canonical regime. Cross-run determinism of 0.144 s (4 runs, Run 002 entry) means single-run A/B deltas are already trustworthy to ~0.1 s.
- ✅ **IBM F1 car confirmed** (2026-04-22) — brake-calibration telemetry measured 22 m/s² mean / 25 m/s² peak decel; these numbers match the F1 spec sheet from the IBM Box reference library, not the Quick Start trb1. `scr_server` selects IBM F1 by default on Corkscrew.
- ✅ Every run archive must pass `scripts/validate_run.py` before commit — enforced from Run 006 onward. Run 005 attempt caught a real schema violation (post-race frames logged after `curLapTime` reset), fixed in commit `487c6de`.
- ✅ Record baseline lap time in `telemetry/baseline.md` — Run 001 (scoreboard) + Run 002 (driver log, 2026-04-22 AM) archived. Cross-run determinism verified: 4 runs, 0.144 s spread (0.068%). Commit `9e1d1c3`.
- ✅ Fix `driver_baseline.py` race-end detection + per-lap logging — commits `7fcfab3`, `1d2b003`, `9e1d1c3`. Loop now exits at ~10,700 steps via stale-`curLapTime` detection (400 consecutive frozen ticks) instead of 99,999. Three-path lap capture: `lastLapTime` (primary) → `curLapTime` reset (fallback) → final-on-race-end (catches single-lap races where scr_server stops mid-lap). All three paths deduped against a 1-second tolerance.
- ✅ Daily commits to `main` — 20+ commits 2026-04-21 through 2026-04-23, all pushed

## Phase 3 — Performance tuning (May 15 – June 4) — *pulled forward; rubric gate cleared 2026-04-22*

See [`docs/phase3-experiments.md`](./phase3-experiments.md) for the full iteration log (Runs 006–025).

- ✅ **Rubric gate `≤3:00.98` cleared 2026-04-22** (Run 007 `170.566 s` dirty, then Run 008 `175.106 s` clean).
- ✅ **Canonical clean reference** — Run 008 `175.106 s`, damages 0, off-tracks 0 (commit `7690afc`).
- ✅ **Segment-based driver shipped** — `src/driver_baseline.py` consumes `telemetry/segments.yaml` for per-segment speed targets. 16 segments derived from Run 001 telemetry (`bin=5.0m`). Commits `447a5c3` through `52252ea`.
- ✅ **Lookahead brake controller** — `brake_dist = (v² − v_target²) / (2 · decel)` using measured decel ceiling. Replaces naive threshold braking.
- ✅ **Brake calibration sprint (2026-04-22)** — measured real decel: **22 m/s² mean / 25 m/s² peak** on IBM F1 (commit `b878a51`). Calibration mode + analyzer in `scripts/`. Previous guess of 14 m/s² was ~35% conservative.
- ✅ **Round 2 strategies shipped (2026-04-22, commits `52252ea`, `c4c3a0e`):**
  - r2a: 60 m buffer, 14 m/s² decel (conservative)
  - **r2a-v2: 60 m + `--full-pedal-brake`** — **Run 023 PB `160.666 s`, damages 0, off-tracks 0** ← current submission anchor
  - r2b: 45 m, 18 m/s² (mid)
  - r2c: 30 m, 21 m/s² (aggressive)
- 🔄 **Open investigation — s08 elevation hypothesis** — kink at ~1950 m causes off-tracks at 102 km/h despite mild geometry. `z` field added to telemetry schema; `scripts/elevation_profile.py` ships. One calibration lap distinguishes pure-traction-saturation vs weight-transfer-grip-loss. See `docs/phase3-experiments.md` §Open investigation and `docs/racing-methodology.md` §5.
- ❌ ~~PID steering~~ — **dropped 2026-04-22**. P-only steering held trackPos within bounds through Run 023; complexity not justified.
- ❌ ~~`scripts/label_segments.py` + `ab_run.py`~~ — superseded by `telemetry/segments.yaml` derivation + manual A/B against Run 008/Run 023 anchors.
- ❌ ~~`telemetry/leaderboard.md`~~ — merged into `telemetry/baseline.md` progression tables.
- ⬜ Granite-assisted code review (chat mode) — `docs/granite-suggestions.md`. Run 023 archive + `segments.yaml` are now concrete inputs.
- ⬜ **Stretch target: `≤2:30` with zero damages** — current PB `2:40.67` leaves ~10.7 s on the table. Next gains plausibly come from: (a) resolving s08 kink → unlock s06/s08 >100 km/h; (b) trail-braking replacement for `--full-pedal-brake`; (c) late-apex line for s09/s13. All three documented in `docs/racing-methodology.md` §5.

## Phase 4 — Polish & differentiate (June 5 – June 21) — *starts 3 days earlier, ends same date = +3-day buffer*

- ⬜ Record fastest-lap video (uni + team name overlay for full duration, **standing start, full-screen TORCS resolution** per form instruction)
- ⬜ Record team video (max 3 min, talk to team/course/uni/developer strategy/IBM Granite/SkillsBuild badges)
- ⬜ Blog draft in `blog/` (hits all 9 rubric points from mission brief)
- ⬜ Publish blog (Medium or WordPress)
- ⬜ Finalize top-level README with architecture diagram
- ⬜ **Create bespoke F1 car livery** — submission form field #12 requires a custom livery with university (MDC) logo + team identifier, linked from Google Drive. Not in original scope; surfaced 2026-04-22 during form walkthrough.
- ⬜ **SkillsBuild badges presentation slides** — submission form field #10 requires a slide deck (Google Slides preferred) showing images + links of completed IBM SkillsBuild badges. Track badge completion in `docs/skillsbuild-progress.md` and generate the deck near submission time.

## Phase 5 — Dry run & submit (June 22 – July 1)

- ⬜ Full submission dress rehearsal — **by June 25**
- ⬜ Fix anything broken
- ⬜ Submit: https://ibm.biz/TORCSForm — **by June 28** (3-day buffer)
- ⬜ Link check: videos playable, repo accessible, blog live

---

## Velocity buffer

Tracks how far ahead (+) or behind (−) the original plan we are. Update whenever a phase boundary shifts.

| Checkpoint | Days vs. original plan | Note |
|---|---|---|
| 2026-04-20 (Zo-side done) | **+6 days** | Ollama + Granite all validated ahead of Phase 1 start |
| 2026-04-21 (plan rev 2 adopted) | **+6 days → target +3** | Spending 3 days of lead on quality (validator, segment map, kickoff prep); banking 3 days into Phase 4 |
| 2026-04-21 (Track A complete) | **+6 days** | All 7 Track A items shipped in one session (validator + 20 tests, segment map, 3 skeletons, kickoff agenda); buffer fully preserved — ahead of target |
| 2026-04-21 (local env + TORCS up) | **+6 days** | Same day: Continue+Granite working on Windows; TORCS installed, Corkscrew loads. SCR/snakeoil3 architecture discovered → Phase 2 simpler than originally scoped (Python client, not C++ robot). |
| 2026-04-21 AM (Phase 1 Track B closed) | **+6 days** | 20-min morning session: repo cloned locally, Python 3.12.10 verified, `gym==0.26.2` installed. Discovered `snakeoil3_gym.py` is pure stdlib — tonight's smoke test has no prep. Only remaining Track B item is reading docs/schema end-to-end. |
| 2026-04-21 AM (Phase 2 Day 1 done early) | **+6 → +7 days** | Pre-work smoke test passed on first try: Python→UDP→TORCS round-trip verified, car driven around Corkscrew under snakeoil3 demo control. Phase 2 Day 1 goal achieved ~9 days ahead of original plan. Next: actually write `src/driver_baseline.py`. Evidence: `docs/screenshots/2026-04-21_phase1-smoke-test-success.png`. |
| 2026-04-21 PM (`driver_baseline.py` shipped) | **+7 → +9 days** | First real custom driver completes a clean Corkscrew lap and finishes in **1st place** with lap time **`3:32.92`**, damages **0**. 3 iterations tonight: scalar-vs-list action fix, then canonical SCR steering formula + 55 km/h target + off-track recovery. `trackPos` stayed on-track the full race. Phase 2's main deliverable reached — next session is telemetry logger + run archive wiring, not driver correctness. Phase 3's target is now concrete: ≤ `3:00.98` (-15% vs baseline). Evidence: `docs/screenshots/2026-04-21_phase2-day1-p1-finish.png`. |
| 2026-04-22 AM (Run 001 soft bugs closed) | **+9 days (held)** | Per-lap timing now captured from the driver log, not the scoreboard. Race-end detection keyed on stale `curLapTime` (not speed/lapTime zeros — scr_server sends the final frame frozen). Loop exits at ~10,700 steps, no more 99k ghost ticks. Run 002 clean: lap `3:32.81` from driver log matches scoreboard to 0.01 s. Cross-run determinism: 4 runs, 0.144 s spread — Phase 3 A/B comparisons can trust single-run deltas down to ~0.1 s. Commits: `7fcfab3`, `1d2b003`, `9e1d1c3`. Evidence: `docs/screenshots/2026-04-22_phase2-day1-run002-clean.png`. |
| 2026-04-22 AM (submission format resolved) | **+9 days (held, small debit)** | Walked the live submission form at `https://forms.office.com/r/gD0gMZaTwP`. Field #6 verbatim: `"Standing start lap time - used to determine who qualifies"` — confirms competition is a **single standing-start lap** on Corkscrew with the **IBM F1 car**. Dropped 5-lap harness item (would have tuned to rolling-start dynamics, wrong regime). Added 3 previously-unscoped deliverables: (a) IBM F1 car verification in TORCS, (b) bespoke livery with uni + team ID, (c) SkillsBuild badges presentation deck. Net: minor scope addition (~3–4h), no schedule impact since 1-lap setup is what we already built. |
| 2026-04-22 (SCHEMA v0.2 logger shipped) | **+9 → +12 days** | `TelemetryLogger` library + driver integration + 8 unit tests landed; Run 006 archive is the first canonical v0.2 reference (10,706 frames, validator PASS). Phase 2 main deliverable "extended telemetry logger" was originally sized for May 4–14; shipped on Apr 22, banking ~3 more days into Phase 4. Commits: `2d116fe`, `df41e63`, `487c6de`, `1fbac08`. |
| 2026-04-22 (Phase 3 rubric gate HIT) | **+12 → +26 days** | Run 007 (`--target-speed 80`, commit `0822c99`) lapped `2:50.57` vs `3:32.99` baseline (−19.9%). Phase 3's `≤3:00.98` gate was scheduled for May 15 – June 4; cleared it on Apr 22. That's ~2 weeks of Phase 3 banked up-front. Does *not* mean Phase 3 is done: 41 damages and a `trackPos=-3.77` spin say we're past the P-only steering's stability margin. Remaining Phase 3 work is now "push faster while cleaning up off-tracks," not "qualify." Evidence: `docs/screenshots/2026-04-22_phase3-day1-run007-target80-2-50-57.png`. |
| 2026-04-22 (Path A clean baseline shipped) | **+26 days (held)** | Run 008 (`--target-speed 80` + two slow zones, commit `447a5c3`) lapped `2:55.11` (`175.106 s`) with **damages 0 and off-tracks 0** — the first *legal, repeatable* sub-3:00 reference. Cost over Run 007's dirty fast lap: only +4.540 s. Rubric gate `≤180.98` now cleared cleanly (vs Run 007's dirty-but-faster proof-of-concept). Commit: `7690afc`. |
| 2026-04-22 PM (segment driver + brake calibration) | **+26 days (held)** | Runs 009–015 tightened zone padding and wired `telemetry/segments.yaml` into the driver. Runs 016–018 introduced the lookahead brake controller. Brake calibration sprint (commit `b878a51`) measured real decel: **22 m/s² mean, 25 m/s² peak** — prior 14 m/s² guess was ~35% conservative, unlocking aggressive Round 2. |
| 2026-04-22 PM (Round 2 + PB `2:40.67`) | **+26 → +30 days** | Round 2 lookahead strategies r2a/r2b/r2c shipped (commit `52252ea`); r2a-v2 with `--full-pedal-brake` (commit `c4c3a0e`) set PB **Run 023 `160.666 s` damages 0 off-tracks 0** — `−24.5%` vs baseline. Run 025 clocked `160.326 s` but with 1 off-track at s08 kink, so Run 023 is the safe submission anchor. |
| 2026-04-23 (elevation hypothesis + methodology docs) | **+30 days (held)** | Added `z` field to telemetry schema (commit `4649b71`) + `scripts/elevation_profile.py` analyzer to test whether s08 kink is a weight-transfer crest or pure traction-circle saturation. Shipped `docs/racing-methodology.md` (commit `5f1d2a6`) synthesizing GT2 physics + Ahura TORCS equations + TORCS-Keras RL insights as the reference framework for remaining tuning. |
| — | — | — |

**Escalation rule:** if buffer drops below **+0 days** (on-schedule or behind) at any phase boundary, pause and replan. Do not compress by cutting scope without team discussion.

---

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Late start (behind other teams) | Aggressive Phase 0, cross-training so no single-point-of-failure |
| Teammate drops out | Cross-training = anyone can cover anyone's work |
| Mac teammate can't run TORCS | Wine setup documented in `setup.md`; have Windows-machine backup |
| Video production eats too much time | Lock video scripts in Phase 3; record in one session in Phase 4 |
| Granite models too slow on laptop | Use Zo for heavy Granite calls; keep local models small (`tiny-h`, `350m`) |
| Telemetry logged inconsistently across teammates → dataset unusable | Lock `telemetry/SCHEMA.md` in Phase 1; enforce via `scripts/validate_run.py` in Phase 1 Track A |
| Solo code track outpaces team track → knowledge silo | Mandatory Apr 27 team kickoff walk-through of everything Louis built in Track A |
| Aggressive schedule forces teammates to cut corners on setup | Track A work is additive, not a substitute for teammate setup; exit criteria unchanged |

---

## Data advantage — our competitive strategy

> Inspiration: a short video on why ByteDance's AI tools are pulling ahead of US competitors — they own native, uncompressed video from Douyin plus engagement telemetry that no one else can reproduce. Saved in `Saved Links.md` (2026-04-20 18:50).

**The parallel to this competition:** every team gets the same TORCS sim, the same starter code, and the same Granite models. Public data is a level playing field. **Our moat is the richness and labeling of the telemetry we generate from our own laps.** That's our Douyin.

### What this means for how we work

1. **Telemetry is a first-class deliverable, not a debug log.** Phase 2's logger must emit the full signal set in `telemetry/SCHEMA.md` — tire slip, lateral g, controller decision metadata, segment IDs. Other teams will log lap time and speed. We log everything.
2. **Every run is archived and labeled.** `telemetry/runs/<timestamp>/` with `manifest.json`, `frames.ndjson`, and `segments.csv`. Never overwrite. This turns our run history into a dataset.
3. **Segment-level "engagement metrics."** `segments.csv` tags each segment traversal with delta-vs-baseline, smoothness score, crash flag, and whether a Granite suggestion influenced the run. That is our analog to TikTok watch-time + likes — the labeled signal that makes the dataset actually useful.
4. **A/B harness is the flywheel.** Phase 3's A/B script (`scripts/ab_run.py`) generates comparative labeled data on every tuning experiment. Compound effect: each test makes the next Granite code-review session smarter because we can paste in real history.
5. **The blog narrative writes itself.** Phase 4 blog framing: "we didn't have more compute or a better model — we won on data density by logging what no one else logged, then letting Granite read our own history."

### Action items this adds to each phase

| Phase | New item |
|---|---|
| Phase 1 Track A | Implement `validate_run.py`; draft segment map; stub remaining scripts; write kickoff agenda |
| Phase 1 Track B | Team kickoff Apr 27 walks through SCHEMA + "Data advantage" strategy |
| Phase 2 | Extended logger; wire `run_race.py` full impl; enforce validator on every run |
| Phase 3 | Wire `label_segments.py` + `ab_run.py`; maintain `telemetry/leaderboard.md`; log Granite suggestions |
| Phase 4 | Blog hits the "data advantage" angle explicitly; reference Granite code-review sessions that used our labeled dataset |
