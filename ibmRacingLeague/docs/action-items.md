# Action Items Tracker

As of **2026-04-24 (end of late session)**. Submission anchor: **Run 031 — `156.586 s` (`2:36.59`), 0 damages, 1 transient boundary touch at s08 kink** (inside TORCS tolerance; lap counted). Cumulative **−9.040 s** since v3 Run 013. **Runs 032–035 (v8–v11) produced no new valid submission** — either DNF'd or scored 18 damages via an s09 hairpin cut. Submission is still Run 031.

For the full iteration log see [`docs/phase3-experiments.md`](./phase3-experiments.md) §Session 2026-04-24 (both parts); for theory see [`docs/racing-methodology.md`](./racing-methodology.md); for segment IDs see [`docs/track-map.md`](./track-map.md).

## Open

| # | Item | Owner | Priority | Notes |
|---|---|---|---|---|
| 1 | **v12 — surgical s09 + s08b fix** | Louis | High | v8–v11 iterations exposed two persistent failure modes. (a) `s09` hairpin: racing-line apex `+0.40` still lets the car cut the inside at 56 km/h (peak trackPos +2.21 in Run 035) → push `s09` to 50 km/h + apex `+0.25`. (b) `s08` kink: 6 consecutive runs show −1.2+ trackPos at 1940–1976 m no matter what is edited on `s08c` → the real problem zone is `s08b` (the kink itself). Try `s08b` apex_pos `+0.20` + `s08a` speed 98 → 92. Expected: damages=0 finish at 150–155 s. |
| 1b | **Run elevation-calibration lap → `scripts/elevation_profile.py` → confirm or reject s08 crest at ~1950 m** | Louis | **High (upgraded)** | 6 runs (030–035) all show `|trackPos| ≥ 1.0` at 1940–1976 m. Racing-line edits on `s08c` cannot fix it because the off-track is at the kink itself (`s08b`). Until we measure the elevation profile we are re-discovering the same failure every iteration. Do this BEFORE spending more runs on s08 tuning. |
| 1c | Capture full `find_offtracks` + segment_report into run-specific `post_lap.md` for every run | Louis | Medium | Tonight's Runs 032–035 log is reconstructed from console paste. Having a per-run markdown with timings, peak trackPos, and damage count makes session debriefs faster. Light scripts/PowerShell change; already have the analyzers. |
| 2 | Bespoke F1 car livery (submission form field #12) — university logo + team identifier, link from Google Drive | Louis | Medium | Not technical work; schedule ~2 h session. Required for valid submission. |
| 3 | SkillsBuild badges presentation slides (submission form field #10) — Google Slides with badge images + links | Louis | Medium | Track badge completion in `docs/skillsbuild-progress.md`; generate deck near submission time. |
| 4 | Submission form dress rehearsal — walk all 12 fields, upload draft artifacts, verify video length + livery link work | Louis | Medium | Schedule by **2026-06-25** per roadmap Phase 5. |
| 5 | Fastest-lap video recording (standing start, full-screen, university + team name overlay) | Louis | Medium | Phase 4 deliverable; record **Run 031 v7** as fallback now, re-record if v12+ delivers a cleaner faster lap. |
| 6 | Team video (max 3 min) covering team / course / uni / strategy / Granite / SkillsBuild | Louis | Low | Phase 4; script first, record in one session. |
| 7 | Blog post — hit all 9 rubric points, frame around the "data advantage" narrative | Louis | Low | Phase 4; roadmap §Data advantage has the outline. |
| 8 | Sync progression with mfundora007 — collect their best Corkscrew lap time on `torcs_jm_par.py` | Louis | Medium | Team repo has no documented teammate lap time (see `docs/competitive-intel.md`). Team submission needs the fastest team lap; we should compare Run 031 against theirs before the form dress rehearsal (#4). |

## Stretch (post-elevation-resolution)

| # | Item | Notes |
|---|---|---|
| S1 | Trail-braking replacement for `--full-pedal-brake` | GT2 + Ahura both describe progressive brake release coupled to steering. Current full-pedal leaves ~0.2–0.5 s per hairpin. See `docs/racing-methodology.md` §5. |
| S2 | Late-apex trajectory for s09 / s13 | Currently we control entry speed but not line. Bias trackPos outside before brake zone; measure s10/s14 full-throttle onset distance. |
| S3 | Granite-assisted code review session | Paste Run 023 archive + `segments.yaml` + `docs/racing-methodology.md` into Granite chat; capture suggestions in `docs/granite-suggestions.md`. |

## Closed (historical, latest first)

- ⚠️ **v11 s09 + s08c line pullback — NOT clean** (2026-04-24 late) — Run 035: 145.162 s clock time but s09 peak trackPos +2.21 (still cutting). Lesson: `s08c` edits don't fix kink-zone off-tracks; `s08b` is the real problem zone. Commit `efba15b`.
- ⚠️ **v10 hard s13 rollback — s13 clean but s09 cut exposed** (2026-04-24 late) — Run 034: 145.026 s clock, 18 damages. s13 apex pullback to −0.40 worked (peak 0.85). New failure mode: racing-line + 60 km/h at s09 produces a hairpin cut. Commit `969adee`.
- ❌ **v9 rollback of s07/s08a/s12/s13/s14 — DNF at s13** (2026-04-24 late) — Run 033. Rolled back the v8 failure zones but s13 apex at −0.55 still too aggressive at 60 km/h target → terminal off. Commit `b8398da`.
- ❌ **v8 aggressive (12 deltas off Run 031) — DNF** (2026-04-24 late) — Run 032. s07 87 + s08a 102 off at the kink; s12 95 + s13 62 off at the hairpin. Too many simultaneous deltas to isolate. Commit `ef4242b`.
- ✅ **v7 straight-cap push + small corner bumps → PB 156.586 s** (2026-04-24) — Run 031, cumulative −9.040 s from v3. Commit `5a25810`. **CURRENT SUBMISSION ANCHOR.**
- ✅ **v6 racing-line + corner-speed bumps → PB 160.606 s** (2026-04-24) — Run 030, −5.020 s in one step. Commit `67cb401`.
- ✅ **v5 racing-line interpolator shipped** (2026-04-24) — `entry_pos` / `apex_pos` / `exit_pos` per segment; steering pulls toward interpolated `trackPos` target. Commit `45f81ee`.
- ✅ **Track map reference** (2026-04-24) — `docs/track-map.md` + `docs/track-map.png` + `scripts/render_track_map.py` for per-segment lookup. Commit `a84dea3`.
- ✅ **Docs refresh** (2026-04-23) — `racing-methodology.md` added; `phase3-experiments.md` and `baseline.md` backfilled through Run 025.
- ✅ **Elevation instrumentation** (2026-04-23) — `z` field in frames schema; `scripts/elevation_profile.py` analyzer shipped.
- ✅ **Round 2 lookahead + PB** (2026-04-22) — r2a-v2 strategy set Run 023 `160.666 s`.
- ✅ **Brake calibration** (2026-04-22) — measured 22 m/s² mean / 25 m/s² peak.
- ✅ **Segment-based driver** (2026-04-22) — `segments.yaml` + per-segment speed targets.
- ✅ **IBM F1 car verified** (2026-04-22) — brake telemetry matches the spec sheet.
- ✅ **Team registration** (2026-04-21) — confirmation received. Team on `mdc-racing-league/AI-Driver` (Louis + mfundora007); `ibmRacingLeague` remains Louis's working repo.
- ✅ **TORCS + Python + Granite toolchain setup** (2026-04-21).
- ✅ **Submission criteria clarified** (2026-04-22) — single standing-start lap on Corkscrew with IBM F1 car; 12-field form walkthrough complete.
