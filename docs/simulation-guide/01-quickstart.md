# 01 — Quickstart

**Goal:** prove the sim runs on your machine. No custom driver yet. No telemetry yet. Just: does TORCS launch, can it race a lap?

**Time:** ~10 minutes if setup is already done.

**Prerequisites:** finished everything in `../setup.md` through at least Step 6 (TORCS installed).

---

## Steps

1. **Launch TORCS**
   - Windows: run `wtorcs.exe` from the install directory
   - Mac (Wine): `wine wtorcs.exe`

2. **Configure a quick race**
   - Main menu → `Race` → `Quick Race` → `Configure Race`
   - Track: `road/corkscrew` (our target track)
   - Opponents: just pick any one built-in AI for now (e.g., `berniw`)
   - Accept → `New Race`

3. **Watch the race**
   - Let it run at least one full lap.
   - Note the lap time displayed in the HUD. This is your reference for how fast a built-in AI is on Corkscrew.

4. **Exit cleanly**
   - Press `ESC` → `Abort Race` → `Exit`
   - Confirm TORCS closes without errors.

---

## Exit criteria

- [ ] TORCS launched successfully
- [ ] Corkscrew track loaded without error
- [ ] A built-in AI completed at least one lap
- [ ] You noted the built-in AI's lap time (write it down — you'll compare against our driver later)

---

## What you just verified

- TORCS install is sane.
- The Corkscrew track is available (required for the competition).
- The rendering / physics pipeline works on your machine.

---

## Next

- Read `02-launching-torcs.md` to understand TORCS's config system more deeply.
- Then `03-running-our-driver.md` to load our custom controller instead of the built-ins.
