# Roadmap & Phase Tracker

> Target: **2026-07-01** submission deadline. Today: 2026-04-21. Budget: ~10 weeks.
>
> **Plan revision 2 (2026-04-20): "Aggressive pull-forward."** Zo-side Phase 1 finished 6 days early. We're spending the lead on a parallel solo-code track that starts now, pulling Phase 2 forward by 4 days and accruing ~3 days of buffer into Phase 4. See "Velocity buffer" below.

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
- ⬜ Skeleton `scripts/run_race.py` with `--help` and TODO blocks
- ⬜ Skeleton `scripts/label_segments.py` with `--help` and TODO blocks
- ⬜ Skeleton `scripts/ab_run.py` with `--help` and TODO blocks
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
- ⬜ Implement `src/driver_baseline.py` as a `snakeoil3` subclass — completes a clean Corkscrew lap (no crashes)
- ⬜ Extended telemetry logger (SCHEMA v0.2 fields) — reads from `snakeoil3.state` dict per tick; replaces v0.1 in `scripts/log_telemetry.py`
- ⬜ Wire `scripts/run_race.py` full impl — orchestrates both `wtorcs.exe` + Python client, handles the two-process startup
- ⬜ Test harness: 5-lap average, same start conditions — `scripts/run_race.py --laps 5`
- ⬜ Every run archive must pass `scripts/validate_run.py` before commit
- ⬜ Record baseline lap time in `telemetry/baseline.md`
- ⬜ Daily commits to `main`

## Phase 3 — Performance tuning (May 15 – June 4) — *pulled forward 3 days*

- ⬜ Segment-by-segment Corkscrew map — finalize from Phase 1 Track A draft
- ⬜ PID or lookup-table controller tuned per segment
- ⬜ Wire `scripts/label_segments.py` and `scripts/ab_run.py` full impls
- ⬜ Granite-assisted code review (chat mode) — capture suggestions in `docs/granite-suggestions.md`
- ⬜ A/B test every change against baseline; only keep improvements; maintain `telemetry/leaderboard.md`
- ⬜ **Target: lap time -15% vs baseline, zero crashes over 10 consecutive runs**

## Phase 4 — Polish & differentiate (June 5 – June 21) — *starts 3 days earlier, ends same date = +3-day buffer*

- ⬜ Record fastest-lap video (uni + team name overlay for full duration)
- ⬜ Record team video (intros, approach, IBM Granite + SkillsBuild usage)
- ⬜ Blog draft in `blog/` (hits all 9 rubric points from mission brief)
- ⬜ Publish blog (Medium or WordPress)
- ⬜ Finalize top-level README with architecture diagram

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
