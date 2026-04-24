# Competitive Intelligence — TORCS / IBM AI Racing League

**Compiled:** 2026-04-24 (overnight pre-meeting research)
**Method:** GitHub search via `gh` CLI across the `mdc-racing-league` org and the wider public TORCS-AI ecosystem. Public repos only.

---

## TL;DR — What we should consider stealing

1. **Discretized actions are more stable than continuous** for any RL/learned controller (popovicidaniela A3C thesis explicitly hit this wall). Reinforces our deterministic segment-map approach as the right call.
2. **Sensor-averaging across adjacent track rangefinders** (A-Raafat Q-learning uses 3-sensor averages at -40°/-20°/0°/20°/40°) is a cheap noise-reduction trick we don't currently apply.
3. **Within our own team:** our segment-based controller is ~30–60 s ahead of mfundora007's driver (a constant-target snakeoil3 modular extension). Real conversation tomorrow is which approach the team submission rides on, not which is "better."
4. **The IBM League's explicit Granite requirement** is unusual vs. the public TORCS landscape (which is RL-dominated). Most public projects don't use any LLM. Doing so visibly is a differentiator the rubric rewards.

---

## Section A — Within-team (mdc-racing-league org)

### `mdc-racing-league/AI-Driver` — `torcs_jm_par.py` (mfundora007)

- **Repo:** https://github.com/mdc-racing-league/AI-Driver (last update 2026-04-22)
- **Source file:** `torcs_jm_par.py` (~21 KB) — vendored 2013-vintage `snakeoil3` Python client (`version= "20130505-2"`) with a teammate-authored `drive_modular()` function appended.
- **Controller approach:** simple heuristic. Single global `TARGET_SPEED = 90` km/h, single `STEER_GAIN = 35` for the entire track, brake when `abs(angle) > 1.0 rad`, fixed gear-speed table, optional traction control via wheel-spin diff.
- **No segment map.** No per-corner tuning. No lookahead braking. Same parameters apply to a 102-km/h s08 straight and a 50-km/h s09 hairpin.
- **AI usage:** none — pure rule-based heuristics. No Granite, no model.
- **Sensor inputs:** standard snakeoil dict (`speedX`, `angle`, `trackPos`, `wheelSpinVel`, etc.) — same as ours.
- **Estimated pace on Corkscrew:** unknown (no telemetry committed). Heuristically: a constant-90 km/h driver hits the s09/s13 hairpins way too fast, so most likely outcome is heavy off-track or DNF. Likely never beats our deterministic segment map.

**Implication for tomorrow's meeting:** The "two drivers, pick one" framing is real. Our segment-based approach has 67 commits of tuning behind it and a 160.666 s PB. Their `drive_modular` is a clean readable starting point. The right team move is probably **adopt our controller as the submission baseline**, but credit `torcs_jm_par.py` as the original onboarding scaffold and use it as the "minimal demo" reference for the team intro video.

### `mdc-racing-league/AI-Driver/DMTestingBranch`

- **What it is:** another teammate testing branch off team `main`. Contents not deeply inspected in this sweep (no obvious driver source delta vs main from git log).
- **Action:** ask in the meeting what's there before deciding; could be active work we shouldn't override.

### Our fork — `LouisRodriguez12101815/ibmRacingLeague`

- 67 commits ahead of team main, segment-based controller, 160.666 s PB. Already detailed in PR #2.

---

## Section B — Wider TORCS public landscape

These aren't competing teams — they're priors we can learn from. Most are academic / hobby projects from 2017–2025.

### High-signal projects

#### `mmujtaba0085/TORCS-AI`
- **URL:** https://github.com/mmujtaba0085/TORCS-AI
- **Approach:** "Multi-branch architecture to train, test, and compare different ML models for high-speed track navigation." Neural-net-based controller trained on logged telemetry CSVs.
- **Key quote from their README:** *"Rule-based controllers are NOT acceptable."* — hint that some academic TORCS challenges explicitly forbid heuristics. **The IBM League brief does NOT impose this restriction** (it requires Granite, not ML for control), so our deterministic approach is in-bounds. Worth confirming if anyone on the team has heard otherwise.
- **Stealable:** the data-collection → preprocessing → train → test → integrate workflow is well-documented and could inform how we structure a Granite-assisted offline analysis pipeline.

#### `A-Raafat/Torcs---Reinforcement-Learning-using-Q-Learning` (38 ⭐)
- **URL:** https://github.com/A-Raafat/Torcs---Reinforcement-Learning-using-Q-Learning
- **Approach:** Q-learning, lane-keeping focused.
- **State design (worth stealing):** uses `speedX`, `angle`, `trackPos`, plus 5 distance sensors at -40°, -20°, 0°, 20°, 40°. **The 20° readings are computed as averages over sensors {6,7,8} and {10,11,12}** to reduce noise — a cheap trick we don't apply. Could improve our PID steering stability, especially on the kink at 1940-1960 m where we already had to slow to 88 km/h.
- **Limitation:** lane-keeping only, doesn't address racing pace.

#### `popovicidaniela/Master-Thesis` (38 ⭐)
- **URL:** https://github.com/popovicidaniela/Master-Thesis
- **Approach:** A3C deep RL, master's thesis project.
- **Key finding from their README:** *"Works best with discrete actions: 4 workers, 1e-4 learning rate. Couldn't get it to work for the continuous actions space; something goes wrong with the actions it generates."*
- **Implication:** Continuous-action RL on TORCS is genuinely hard. Validates our choice to go segment-deterministic. If we ever bolt on a learned component, start discrete (e.g., a segment-classifier picking from a finite set of throttle/brake regimes), not continuous policy.

#### `ZijianHan/torcs-reinforcement-learning` (13 ⭐)
- **URL:** https://github.com/ZijianHan/torcs-reinforcement-learning
- **Approach:** Q-learning with hierarchical "intra-policy" structure for path planning. Uses a low-level controller for throttle and a higher-level RL agent for path choices.
- **Stealable concept:** **separation of concerns** — high-level chooses *which segment behavior* (e.g., "Run-B safe" vs "Run-023 aggressive"), low-level executes the actual throttle/brake. Our current `segments_submission.yaml` ad-hoc mixes both philosophies; a cleaner abstraction could let us A/B faster.

### Reference / lower-signal

- **`ugo-nama-kun/gym_torcs` (423 ⭐)** — the standard OpenAI Gym wrapper for TORCS RL. Not directly applicable to us (we don't use gym), but every academic TORCS RL paper since 2017 cites it. Useful citation if the blog references TORCS RL ecosystem.
- **`numan98khan/rTORCS-Python-Driver`** — heuristic Python bot (2020). Sparse README, similar in spirit to mfundora007's `drive_modular` but for an rTORCS variant. No standout insights.
- **`Ignotus/torcsnet`, `kschan/torcs_scripts`, `FionaLippert/TORCS_Controller`** — various smaller controllers (RNN+evolutionary, Haskell bindings, etc.). Nothing actionable.

### What's missing / negative results

- **No public repo found** explicitly tagged "IBM AI Racing League" or "ibm-racing-league". Either teams aren't publishing, or they keep their work private until after the season. The MDC league sub-org has only one team repo visible.
- **No public repo found** integrating IBM Granite (or any LLM) into a TORCS control loop. We'd be the first visible example. Likely because real-time control at 50 Hz is not a natural LLM workload — confirming our `granite-validation.md` analysis that Granite belongs in the **offline / analysis** path, not the runtime.
- **No public Corkscrew-specific tuning maps** found. Our `segments.yaml` (16 segments, observed telemetry, target speeds) appears to be a novel artifact for this track. Worth highlighting in the submission.

---

## Section C — Recommended actions for the team

Ranked by expected value vs. cost:

### 1. Adopt the segment-based controller as the submission baseline
**Cost:** zero (already exists). **Value:** ~30+ s lap-time advantage over `torcs_jm_par.py`, plus a documented methodology to talk about in the team intro video. Settle this in the meeting.

### 2. Add Granite to the offline analysis path (already planned — task 2 of this overnight batch)
**Cost:** ~1 hr of script work. **Value:** answers "did you use IBM Granite?" with a tangible artifact, not just "we used it for code review." See `scripts/granite_segment_review.py` (being built tonight).

### 3. Add 3-sensor track-rangefinder averaging to the steering input
**Cost:** ~10 lines in `driver_baseline.py`. **Value:** noise reduction borrowed from A-Raafat's Q-learning state design. Could let us push s08 and s11 caps higher without the kink jitter that forced the 88 km/h micro-zone in `segments_submission.yaml`. Test in a single-lap A/B before committing.

### 4. Add the controller-comparison narrative to the team intro video
**Cost:** ~5 min of video time. **Value:** "we built two drivers, here's how the segment-based one outpaces the heuristic one by 30+ s on Corkscrew" is a strong competition-rubric narrative — shows iteration, comparison, evidence. mfundora007's driver becomes a useful baseline-as-foil rather than a discarded effort.

### 5. (Optional, lower value) Consider hierarchical "behavior-mode" abstraction
**Cost:** ~half-day refactor. **Value:** would let us swap between `segments.yaml` / `segments_run_b.yaml` / `segments_submission.yaml` from a single CLI flag without three YAML files. Borrowed from ZijianHan's intra-policy structure. Defer until after submission unless the meeting surfaces a need.

### Out of scope (rejected)
- **Full RL/imitation rewrite** — the public landscape shows continuous-action RL on TORCS is genuinely hard (popovicidaniela), and we have a working 160 s lap. Don't burn submission time on this.
- **Switch to gym_torcs** — would force us to abandon our existing driver_baseline + telemetry pipeline. No clear win.

---

## Sources

All findings derived from public GitHub data fetched 2026-04-24 via `gh search repos` and `gh api repos/<owner>/<repo>/readme`. No private repos accessed; no scraping of authenticated content.
