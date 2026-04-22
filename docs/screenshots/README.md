# Screenshots — Evidence & Milestones

Visual record of the key milestones and debugging moments in the IBM Racing League project.

## Naming convention

`YYYY-MM-DD_short-description.png`

Example: `2026-04-21_phase1-smoke-test-success.png`

---

## Index

| Date | File | What it shows | Milestone |
|---|---|---|---|
| 2026-04-21 | `2026-04-21_phase1-smoke-test-success.png` | TORCS running Corkscrew with `scr_server 1` as the active driver, controlled by our Python `snakeoil3_gym.py` client. Top Speed 224 km/h visible in HUD. Car is driving (poorly — snakeoil3's built-in demo controller). | **Phase 1 → Phase 2 handshake verified end-to-end.** First confirmed TORCS ↔ Python UDP round-trip on our stack. |

---

## Purpose

- **Submission evidence.** Proves milestones for the competition blog and final submission.
- **Debugging artifacts.** Failed states (crash screens, error dialogs) are valuable — keep them.
- **Blog post material.** Phase 4's blog will benefit from "here's what it looked like when X finally worked."

Keep both successes and failures. A screenshot of a broken run is as useful for the blog narrative as a screenshot of the win.
