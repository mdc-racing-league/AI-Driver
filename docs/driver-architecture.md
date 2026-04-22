# Driver Architecture Draft

## Pipeline Overview
1. **Perception** – capture TORCS telemetry (speed, RPM, track position, opponent distance) and preprocess into structured features.
2. **Planning** – use heuristic rules or AI reasoning (via Ollama Granite models) to decide throttle, brake, and steering targets per frame.
3. **Control** – translate planned targets into TORCS controller wheel inputs using PID or other smoothing logic.

## Short-term Goals
- Prove out telemetry capture within TORCS environment.
- Build a simple heuristic controller as baseline.
- Experiment with Granite for strategic decisions on throttle/brake timing.

## Longer-term Ideas
- Integrate video/telemetry logging for training and analysis.
- Explore prompt engineering for Ollama to weigh track segments and adjust aggressiveness.

## Baseline Controller
- **Objective:** Drive a simple lap without AI assistance to verify TORCS control path.
- **Approach:** Use fixed throttle (80%), small steering bias to follow the track, gentle braking near turns, and log sensor readings each frame.
- **Inputs captured:** Speed, RPM, track position, distance to track edge, opponent proximity.
- **Next step:** Replace rule-based output with Granite-powered decision-making once sensor pipeline is stable.

## Reinforcement Learning Setup
- **Observation space:** `speed`, `rpm`, `trackPosition`, `trackDistance`, `opponentMinDistance`, `time`, `throttle`, `brake`, `steer` plus aggregate curvature (Karpathy-style features such as next-corner angle).
- **Action space:** Continuous `throttle`, `brake`, and `steer` outputs in [-1, 1] with safety clipping (avoid wheelspin or lockup).
- **Reward shaping:** +1 for every meter staying on track, +10 for nailing the corkscrew apex, penalty -5 when leaving track or hitting walls, small penalty for wheelspin (aggressive throttle). Encourage smooth throttle ramps for exit speed.
- **Warm start:** Use `baseline-commands.log` to seed the first policy rollouts; treat logged telemetry as expert demonstrations to pretrain or bootstrap a behavior cloning policy before switching to RL gradients.
- **Training loop idea:** TORCS acts as the environment; a Python supervisor script steps through episodes by 1) resetting the driver, 2) sampling actions from the policy, 3) sending them to TORCS (via UDP), 4) logging telemetry to `telemetry/raw.log`, 5) computing reward, 6) updating the policy using PPO/A3C with Mini-Batch.
- **Validation:** Record a lap video once per checkpoint and compare lap time/distance against the deterministic baseline to ensure progress.
