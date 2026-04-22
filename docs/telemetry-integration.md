# Telemetry Integration Guide

## Goal
Wire TORCS → telemetry log → baseline controller/logging so the RL supervisor sees a continuous stream of track data and actions. This keeps the car off the walls, aligns with the Corkscrew line guidance, and records everything needed for training.

## Steps
1. **Launch TORCS headless**
   - `xvfb-run -a /usr/games/torcs -s`
   - In Settings > Gameplay > Logging, set the telemetry file to `/home/workspace/ibmRacingLeague/telemetry/raw.log` (JSON format). If logging is not available via the UI, use a TORCS plugin or script the UDP telemetry stream and redirect it to the same path.
2. **Run the baseline controller**
   - Start the controller in one terminal. It tails `/home/workspace/ibmRacingLeague/telemetry/raw.log` and appends commands to `/home/workspace/ibmRacingLeague/telemetry/baseline-commands.log`.
3. **Run the telemetry logger**
   - In another terminal, run `python /home/workspace/ibmRacingLeague/scripts/log_telemetry.py --source /home/workspace/ibmRacingLeague/telemetry/raw.log --output /home/workspace/ibmRacingLeague/telemetry/frames.csv`. This normalizes the observations for the RL agent.
4. **Monitor safety metrics**
   - While TORCS is running, tail `telemetry/frames.csv` or use `tail -f` on `raw.log` to watch `trackPosition`/`trackDistance`. Keep records of the braking/steering actions to ensure you’re not hugging walls.
5. **Record the run**
   - Capture a video (OBS or simulated video export) of your lap to submit with the quality check. Store it under `ibmRacingLeague/videos/<timestamp>-baseline.mp4` and reference it in the mission brief.

## Notes
- These scripts can all run concurrently; once the log file grows, the baseline controller and logger stream updates automatically.
- When you switch to RL inference, the same telemetry paths feed the agent. Just point your supervisor to `frames.csv` for observations and to `baseline-commands.log` for the safe expert policy.
- Add any TORCS errors (audio warnings, driver crashes) to `docs/action-items.md` so future teammates know the workarounds.
