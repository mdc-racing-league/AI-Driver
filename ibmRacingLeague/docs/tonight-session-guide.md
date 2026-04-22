# Tonight's Session Guide — Round 1 Experiment Suite

**Goal:** Run 6 strategies, collect telemetry, push results. I'll analyze and have Round 2 configs ready.

**Current best:** Run 013 — 165.666s (2:45.66), 0 damages

---

## Step 1 — Pull latest code (Window B)

```powershell
cd $env:USERPROFILE\ibmRacingLeague\ibmRacingLeague
git pull
```

---

## Step 2 — Launch TORCS (Window A)

```powershell
cd C:\torcs\torcs
.\wtorcs.exe
```

In the TORCS window:
**Race → Quick Race → Configure Race → Corkscrew → Accept → scr_server 1 only → Accept → New Race**

Window will say "Not Responding" — that is correct. Leave it.

---

## Step 3 — Run the suite (Window B)

```powershell
.\scripts\race_suite.ps1
```

The script handles everything. For each of the 6 strategies it will:
1. Print setup instructions
2. Wait for you to press **Enter**
3. Drive the lap automatically
4. Run validate + off-track scan + segment report
5. Print a 3-step checklist (screenshot → git push → restart TORCS)
6. Wait for Enter before the next strategy

To run just one strategy:
```powershell
.\scripts\race_suite.ps1 -Only flat-out
.\scripts\race_suite.ps1 -List    # see all IDs
```

After any manual run outside the suite:
```powershell
.\scripts\post_lap.ps1
```

---

## The 6 strategies

| ID | What it tests | Expected time |
|---|---|---|
| `run016` | Lookahead 200m / conservative braking | 155–162s |
| `run017` | Lookahead 150m / moderate braking | 150–158s |
| `run018` | Lookahead 120m / late braking | 145–155s |
| `flat-out` | Straights uncapped at 130 km/h, lookahead brakes for corners | unknown |
| `push-straights` | s08→110, s06/s10/s12→100 (track_index headroom) | ~158–163s |
| `regression` | Reproduce Run 013 exactly — confirm nothing drifted | ~165.7s |

---

## After each lap — 3 things

The script prints these automatically, but here they are:

1. **Screenshot** — take the TORCS Race Results screen, save to Downloads
2. **Git push** — exact commands printed by the script after every lap
3. **Restart TORCS** — kill + relaunch between every strategy

---

## After all runs — tell me "ready to analyze"

Once all runs are pushed, come back here and say **"ready to analyze"** (or just **"done"**).

I will:
- Read all new segment reports
- Cross-compare entry/exit speeds across all 6 strategies
- Identify the fastest clean lap and why
- Build Round 2 configs targeting the gaps

Round 2 will be a tighter set of 2–3 runs aimed at a specific time target.

---

## If TORCS freezes or crashes

```powershell
Get-Process wtorcs -ErrorAction SilentlyContinue | Stop-Process -Force
cd C:\torcs\torcs; .\wtorcs.exe
```
Then set up the race again from the menu.

## If the driver errors out

```powershell
git pull    # make sure you have latest code
python src\driver_baseline.py --help    # confirm flags are there
```

---

## Key files for reference

| File | What it is |
|---|---|
| `telemetry/baseline.md` | All runs 001–015 documented |
| `telemetry/track_index.md` | Cross-run speed stats per segment |
| `docs/phase3-experiments.md` | Run plans and results log |
| `telemetry/segments.yaml` | Current best segment config (Run 013) |
| `telemetry/segments_flat_out.yaml` | Straights at 130 km/h |
| `telemetry/segments_push.yaml` | Straights pushed to 100–110 km/h |
