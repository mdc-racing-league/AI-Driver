# Track Index — Corkscrew Cross-Run Baseline

**Runs included (8):** Run 006, Run 007, Run 008 Path A, Run 009 Path A, Run 010 Path A, Run 011, Run 012, Run 013

## Per-segment baseline table

| Segment | Kind | Range | Target | Avg speed | Max speed | Best avg | Best run | Variance | Peak \|tPos\| | Time gap |
|---|---|---|---|---|---|---|---|---|---|---|
| s00_straight | straight | 0–405m | 80.0 | 70.2 | 81.6 | 72.0 | Run 007 | 12.6 | 0.189 | 4.27s |
| s01_turn_L_475m | corner | 405–545m | 75.0 | 76.6 | 81.6 | 80.3 | Run 009 Path A | 15.4 | 0.468 | 1.49s |
| s02_straight | straight | 545–735m | 80.0 | 77.6 | 80.2 | 80.1 | Run 009 Path A | 15.2 | 0.199 | 2.02s |
| s03_turn_R_775m | corner | 735–815m | 75.0 | 76.5 | 80.2 | 80.0 | Run 007 | 15.2 | 0.347 | 0.84s |
| s04_straight | straight | 815–1000m | 80.0 | 77.6 | 80.2 | 80.1 | Run 007 | 15.2 | 0.190 | 1.96s |
| s05_turn_R_1040m | corner | 1000–1080m | 78.0 | 77.1 | 80.2 | 80.0 | Run 007 | 15.2 | 0.249 | 0.85s |
| s06_straight | straight | 1080–1480m | 80.0 | 77.9 | 80.2 | 80.1 | Run 008 Path A | 15.3 | 0.221 | 4.23s |
| s07_turn_L_1540m | corner | 1480–1600m | 78.0 | 76.8 | 80.2 | 80.0 | Run 008 Path A | 15.8 | 0.265 | 1.34s |
| s08_straight | straight | 1600–2380m | 95.0 | 77.6 | 95.1 | 93.4 | Run 013 | 35.3 | 0.799 | 18.18s |
| s09_turn_R_2605m | corner | 2380–2540m | 58.0 | 59.3 | 94.9 | 71.9 | Run 007 | 35.9 | 3.522 | 9.24s |
| s10_straight | straight | 2540–2945m | 80.0 | 76.4 | 90.0 | 86.0 | Run 007 | 21.1 | 1.614 | 5.49s |
| s11_turn_R_2985m | corner | 2945–3025m | 78.0 | 83.5 | 90.0 | 88.3 | Run 008 Path A | 23.4 | 0.261 | 1.18s |
| s12_straight | straight | 3025–3245m | 80.0 | 80.0 | 86.9 | 84.6 | Run 009 Path A | 19.7 | 0.219 | 2.86s |
| s13_turn_L_3272m | corner | 3245–3300m | 58.0 | 64.0 | 83.0 | 74.7 | Run 007 | 16.3 | 3.827 | 0.28s |
| s14_straight | straight | 3300–3605m | 80.0 | 64.6 | 80.2 | 67.9 | Run 010 Path A | 9.6 | 3.873 | 2.70s |
| s15_turn_L_3607m | corner | 3605–3610m | 78.0 | 72.2 | 80.1 | 76.8 | Run 007 | 41.1 | 0.249 | 0.06s |

## Optimization opportunities

Segments ranked by **speed variance** (= gap between best and worst run through that section).
High variance = we've explored different speeds here and know there's room to push.

| Rank | Segment | Variance (km/h) | Best avg | Target | Headroom vs target |
|---|---|---|---|---|---|
| 1 | s15_turn_L_3607m | 41.1 | 76.8 | 78.0 | -1.2 |
| 2 | s09_turn_R_2605m | 35.9 | 71.9 | 58.0 | +13.9 |
| 3 | s08_straight | 35.3 | 93.4 | 95.0 | -1.6 |
| 4 | s11_turn_R_2985m | 23.4 | 88.3 | 78.0 | +10.3 |
| 5 | s10_straight | 21.1 | 86.0 | 80.0 | +6.0 |
| 6 | s12_straight | 19.7 | 84.6 | 80.0 | +4.6 |
| 7 | s13_turn_L_3272m | 16.3 | 74.7 | 58.0 | +16.7 |
| 8 | s07_turn_L_1540m | 15.8 | 80.0 | 78.0 | +2.0 |

## Corner stress index

Segments with highest peak `|trackPosition|` across all runs — corners where the car came closest to the edge.
Values > 0.7 are high-risk; > 1.0 = off-track.

| Segment | Kind | Peak \|tPos\| | Target (km/h) | Best avg speed |
|---|---|---|---|---|
| s14_straight | straight | 3.873 ⚠️ | 80.0 | 67.9 |
| s13_turn_L_3272m | corner | 3.827 ⚠️ | 58.0 | 74.7 |
| s09_turn_R_2605m | corner | 3.522 ⚠️ | 58.0 | 71.9 |
| s10_straight | straight | 1.614 ⚠️ | 80.0 | 86.0 |
| s08_straight | straight | 0.799 ⚠️ | 95.0 | 93.4 |
| s01_turn_L_475m | corner | 0.468 | 75.0 | 80.3 |
