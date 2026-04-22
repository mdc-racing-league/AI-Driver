# Phase 1 Kickoff — Team Sync Agenda

**When:** Monday, 2026-04-27 (first day of Phase 1)
**Duration:** 60 minutes
**Facilitator:** Louis
**Attendees:** Full team
**Format:** Video call + screen share (Discord)

---

## Why this meeting exists

Phase 1 is where all teammates stand up their local environments. But while Louis had the lead (Phase 1 Track A), several things changed that the team needs to see *before* writing any driver code:

1. The repo gained a documentation spine (`README.md`, `docs/simulation-guide/`).
2. We adopted a **"data advantage" strategy** that makes telemetry a first-class deliverable.
3. `telemetry/SCHEMA.md` locks the contract every teammate's logger must match.
4. `scripts/validate_run.py` is ready — every run archive must pass it.
5. The roadmap shifted to aggressive Plan Revision 2 (Phase 2 starts Apr 30, not May 4).

If teammates start Phase 1 without this context, they'll drift off-schema and we lose the compounding dataset advantage. **This meeting is the single most important knowledge-transfer moment of the project.**

---

## Pre-read (send 24 hours before)

Teammates are expected to have **skimmed** these before the meeting:

1. `docs/roadmap.md` — especially "Data advantage" section and the Plan Revision 2 note at top
2. `docs/simulation-guide/README.md` — the 7-file runbook map
3. `telemetry/SCHEMA.md` — at minimum the design principles + v0.2 field list
4. `docs/granite-validation.md` — model-selection rules

**Email template:**
> Subject: Phase 1 kickoff Monday — pre-read (20 min)
>
> Team — before Monday's 60-min kickoff please skim the 4 docs linked below. I'll walk through them live but the meeting works much better if you've seen them once.
>
> 1. roadmap.md (read top + "Data advantage" section)
> 2. docs/simulation-guide/README.md
> 3. telemetry/SCHEMA.md (principles + field list)
> 4. docs/granite-validation.md
>
> Total pre-read: ~20 minutes.

---

## Agenda

### 1. Context: where we are (5 min)

- Phase 0 status: registration complete, repo restructured, Zo-side environment live
- Velocity buffer: +6 days coming into Phase 1 → spent on Track A, targeting +3 going into Phase 2
- Plan Revision 2 summary: **Phase 2 starts Apr 30, not May 4**. Phase 4 gains 3 days of buffer for blog/video.

### 2. Strategy: the data advantage (10 min)

**Walk through `docs/roadmap.md` "Data advantage" section.**

Key points to emphasize:
- Every team has the same TORCS sim, same Granite models, same starter code.
- Our moat is **proprietary labeled telemetry**. ByteDance/Douyin parallel.
- This changes how we work: telemetry is a first-class deliverable, not a debug log.
- Every run is archived under `telemetry/runs/<timestamp>/` — never overwritten.
- Every run must pass `scripts/validate_run.py` before commit.

**Q&A: anyone disagrees with this framing? Better ideas? Now is the time.**

### 3. Repo tour (10 min)

Live screen-share walk of:

- `README.md` — start here
- `docs/setup.md` — one-time install steps for Phase 1
- `docs/simulation-guide/` — day-to-day runbook (once installed)
- `telemetry/SCHEMA.md` — the data contract
- `telemetry/segments.txt` — canonical segment IDs
- `scripts/validate_run.py` + `tests/test_validate_run.py` — what "locked schema" enforcement looks like

### 4. Your Phase 1 assignment (10 min)

Walk through `docs/setup.md` steps 1–9 in order. Point out:

- Windows vs. Mac differences
- Use `granite4:tiny-h` for chat, `granite4:350m-h` for autocomplete (never for domain facts — it hallucinates; see `granite-validation.md`)
- Exit criteria: each teammate lap the Corkscrew track with a built-in AI before Phase 2

**Explicit ask:** "Read `docs/simulation-guide/` + `telemetry/SCHEMA.md` end-to-end before writing any driver code."

### 5. Phase 2 preview (10 min)

What happens immediately after Phase 1 exit:

- **Phase 2 starts Apr 30** (not May 4 — pulled forward)
- First deliverable: `src/driver_baseline.py` that completes a clean Corkscrew lap
- Second deliverable: extended telemetry logger matching SCHEMA v0.2
- Third deliverable: `scripts/run_race.py` full implementation (skeleton already exists)

Who owns what: **decide in this meeting**. Suggestion — pair programming per deliverable, swap on each, so cross-training sticks.

### 6. Risks, questions, parking lot (10 min)

Known risks from `docs/roadmap.md`:
- Late start relative to other teams
- Teammate drops out → cross-training mitigates
- Mac + TORCS friction → Wine docs + Windows backup
- Solo-track knowledge silo → this meeting is the mitigation

Open Q&A. Capture anything that doesn't resolve in a "Parking Lot" section in Discord.

### 7. Concrete next steps (5 min)

Before end-of-meeting, everyone commits to:

- [ ] Block a ~4-hour window this week to complete `docs/setup.md` steps 1–9
- [ ] Post a "Phase 1 setup done" screenshot in Discord when finished
- [ ] Flag blockers within 24 hours (don't silently stall)
- [ ] By Apr 30 at the latest: complete a Corkscrew lap with a built-in AI

---

## Facilitator notes (for Louis)

**Tone:**
Aggressive plan, collaborative execution. The pull-forward adds buffer, not pressure — make that clear.

**If someone pushes back on the data-advantage strategy:**
Surface the cost. The strategy adds ~1 extra hour of telemetry plumbing in Phase 2 but compounds through Phases 3–4. Alternative (just log lap time) wins you Phase 2 time but loses Phase 3 by a lot. Decide as a team.

**If someone is running behind on SkillsBuild:**
Push to complete it during Phase 1 Week 1 at the latest. It gates Phase 2 contribution per the mission brief.

**If registration isn't done yet:**
That's a blocker — resolve live in this meeting before adjourning.

**Record the meeting** if teammates consent. Future self will thank you when recalling "who agreed to own the extended logger."

---

## Post-meeting outputs

- [ ] Discord post: "Phase 1 kickoff notes" (bullet summary + owner table)
- [ ] Update `docs/roadmap.md`: mark kickoff complete, add owner names to Phase 2 items
- [ ] Send pre-read email 24 hours before meeting
- [ ] Confirm all teammates have Discord access + repo clone permissions
