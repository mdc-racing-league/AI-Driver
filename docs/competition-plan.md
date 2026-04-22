# IBM AI Racing League Competition Plan

## Phase 1: Launch Pad (Tonight)
1. **Register the team** – complete the official league registration and record the confirmation/ID (scheduled for Friday).
2. **Define acceptance criteria** – document what constitutes an official lap, along with video capture requirements and scoring expectations.
3. **Set up repo structure** – ensure the repo houses directories for `src/`, `models/`, `data/`, `docs/`, `videos/`, and automation scripts, keeping the IBM project isolated and tracked.
4. **Establish the dev environment** – confirm TORCS, Python (3.12+), and Ollama/Granite dependencies are installed and note any blockers.
5. **Sketch the driver pipeline** – outline perception → planning → control stages in `docs/driver-architecture.md` for future reference.

## Phase 2: Build & Iterate
- Implement baseline controller that can complete a lap in TORCS using scripted actions or simple heuristics.
- Integrate Ollama-powered AI reasoning for decision-making, tuning prompts and inputs with telemetry.
- Start gathering telemetry/log data for analysis to iterate on speed, stability, and cornering.
- Capture video evidence matching submission rules and store drafts in `videos/`.

## Phase 3: Polish & Submit
- Refine AI logic, add redundancy for fault tolerance, and instrument logging for validation.
- Produce required videos and optional blog content summarizing learnings.
- Perform final test runs, collect metrics, and submit to IBM AI Racing League before the deadline.
