# Action Items Tracker

As of **2026-04-23**. Submission anchor: Run 023 `160.666 s` (`2:40.67`), damages 0, off-tracks 0.

For the full iteration log see [`docs/phase3-experiments.md`](./phase3-experiments.md); for theory see [`docs/racing-methodology.md`](./racing-methodology.md).

## Open

| # | Item | Owner | Priority | Notes |
|---|---|---|---|---|
| 1 | Run elevation-calibration lap → `scripts/elevation_profile.py` → confirm or reject s08 crest at ~1950 m | Louis | High | Deterministic next step. If confirmed → carve out 1900:2000 micro-zone at ~92 km/h. If rejected → cap s08 target at ~95 km/h. Either resolves the only remaining off-track mode. |
| 2 | Bespoke F1 car livery (submission form field #12) — university logo + team identifier, link from Google Drive | Louis | Medium | Not technical work; schedule ~2 h session. Required for valid submission. |
| 3 | SkillsBuild badges presentation slides (submission form field #10) — Google Slides with badge images + links | Louis | Medium | Track badge completion in `docs/skillsbuild-progress.md`; generate deck near submission time. |
| 4 | Submission form dress rehearsal — walk all 12 fields, upload draft artifacts, verify video length + livery link work | Louis | Medium | Schedule by **2026-06-25** per roadmap Phase 5. |
| 5 | Fastest-lap video recording (standing start, full-screen, university + team name overlay) | Louis | Medium | Phase 4 deliverable; do not cut before elevation hypothesis resolved to avoid re-recording. |
| 6 | Team video (max 3 min) covering team / course / uni / strategy / Granite / SkillsBuild | Louis | Low | Phase 4; script first, record in one session. |
| 7 | Blog post — hit all 9 rubric points, frame around the "data advantage" narrative | Louis | Low | Phase 4; roadmap §Data advantage has the outline. |

## Stretch (post-elevation-resolution)

| # | Item | Notes |
|---|---|---|
| S1 | Trail-braking replacement for `--full-pedal-brake` | GT2 + Ahura both describe progressive brake release coupled to steering. Current full-pedal leaves ~0.2–0.5 s per hairpin. See `docs/racing-methodology.md` §5. |
| S2 | Late-apex trajectory for s09 / s13 | Currently we control entry speed but not line. Bias trackPos outside before brake zone; measure s10/s14 full-throttle onset distance. |
| S3 | Granite-assisted code review session | Paste Run 023 archive + `segments.yaml` + `docs/racing-methodology.md` into Granite chat; capture suggestions in `docs/granite-suggestions.md`. |

## Closed (historical, latest first)

- ✅ **Docs refresh** (2026-04-23) — `racing-methodology.md` added; `phase3-experiments.md` and `baseline.md` backfilled through Run 025.
- ✅ **Elevation instrumentation** (2026-04-23) — `z` field in frames schema; `scripts/elevation_profile.py` analyzer shipped.
- ✅ **Round 2 lookahead + PB** (2026-04-22) — r2a-v2 strategy set Run 023 `160.666 s`.
- ✅ **Brake calibration** (2026-04-22) — measured 22 m/s² mean / 25 m/s² peak.
- ✅ **Segment-based driver** (2026-04-22) — `segments.yaml` + per-segment speed targets.
- ✅ **IBM F1 car verified** (2026-04-22) — brake telemetry matches the spec sheet.
- ✅ **Team registration** (2026-04-21) — confirmation received. Team on `mdc-racing-league/AI-Driver` (Louis + mfundora007); `ibmRacingLeague` remains Louis's working repo.
- ✅ **TORCS + Python + Granite toolchain setup** (2026-04-21).
- ✅ **Submission criteria clarified** (2026-04-22) — single standing-start lap on Corkscrew with IBM F1 car; 12-field form walkthrough complete.
