# 02 — Launching TORCS

How TORCS is organized, how to configure races reproducibly, and how to automate launches.

**Prerequisites:** finished quickstart (`01-quickstart.md`).

---

## TORCS directory layout (relevant parts)

| Path | Purpose |
|---|---|
| `wtorcs.exe` (or `torcs` on Linux) | Main binary |
| `config/raceman/quickrace.xml` | Config for Quick Race mode — this is what we edit for reproducible runs |
| `drivers/` | Where custom AI drivers live (our controller goes here) |
| `tracks/road/corkscrew/` | Our target track |
| `runtime/results/` | Per-race result XML files |

Exact paths vary slightly by platform — the IBM Wtorcs bundle may nest these differently. Check `docs/Wtorcs-ollama-instructions.pdf` for the specific layout of the distributed bundle.

---

## Configuring a reproducible race

Racing "manually" from the GUI is fine for smoke tests, but for comparing runs you need **identical conditions every time**. Edit `config/raceman/quickrace.xml`:

- Fix the track: `<attstr name="name" val="corkscrew"/>`
- Fix the weather/time-of-day (TORCS has some stochasticity otherwise)
- Set a deterministic number of laps (we use 1 for timed laps; 5 for stability tests)
- Lock the driver list (only our driver, or our driver + a specific opponent set)

> **Why this matters:** our A/B harness (Phase 3) compares our driver's lap time across code variants. If weather or opponent roster changes between runs, you can't tell if a speed change came from your code or from the sim.

---

## Headless / automated launch

For CI and for the A/B harness, you'll want to launch TORCS without the GUI:

```
wtorcs.exe -nofuel -nodamage -nolaptime -T
```

(Flags vary by TORCS build; `-T` is the common "text mode" flag. Confirm against `wtorcs.exe --help` on your install.)

**Note:** even in text mode TORCS produces per-tick telemetry if our driver is emitting it — see `04-capturing-telemetry.md`.

---

## Verifying track and car availability

Before starting Phase 2 work, confirm:

- Track `corkscrew` appears in the track list
- A baseline car (e.g. `car1-trb1`) appears in the car list
- You can successfully launch a 1-lap quick race with those selections

Both are referenced in the mission brief (`docs/TORCSRegtoSubmission0901-Mission Brief-Detailed (1).pdf`).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `data/fonts/*.glf: No such file or directory` at launch | Launched with wrong working directory | `cd C:\torcs\torcs\` first, then `.\wtorcs.exe`. Or use a shortcut with "Start in" set to the install folder. |
| Window title shows `(Not Responding)` on loading screen | Race configured with `scr_server` driver, no Python client connected | **Expected** — `scr_server` blocks waiting for a UDP client on port 3001. See `03-running-our-driver.md`. Start the Python client in a second terminal, or swap `scr_server` for a built-in AI in Configure Race. |
| "Track not found" | Install missed the road pack | Reinstall TORCS; verify `tracks/road/corkscrew/` exists |
| Black screen on launch | Graphics driver / OpenGL | Update graphics drivers; try windowed mode |
| Wine crash on Mac | Missing dependency | See `../setup.md` Mac section and the MacOS extras bundle |

Runtime issues after race start are in `06-troubleshooting.md`.

---

## Next

- `03-running-our-driver.md` — load our controller instead of the built-ins
