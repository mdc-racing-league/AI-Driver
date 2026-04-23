# Segment report — 2026-04-22T20-20-32

Per-segment performance aggregates for lap 1 of this run, bucketed by `trackDistance` into the segments defined in `telemetry/segments.yaml`.

| # | id | kind | range (m) | target v (km/h) | t (s) | v min/avg/max | entry_kmh | exit_kmh | peak \|trackPos\| | peak \|steer\| | frames |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | s00_straight | straight | 0–405 | 80.0 | 20.32 | 26.0/72.0/81.0 | 26.0 | 81.0 | 0.189 | 0.13 | 961 |
| 1 | s01_turn_L_475m | corner | 405–545 | 75.0 | 6.974 | 74.9/75.3/81.0 | 81.0 | 75.0 | 0.42 | 0.325 | 318 |
| 2 | s02_straight | straight | 545–735 | 80.0 | 8.562 | 75.0/79.8/80.2 | 75.0 | 80.1 | 0.194 | 0.081 | 421 |
| 3 | s03_turn_R_775m | corner | 735–815 | 75.0 | 3.92 | 74.9/75.3/80.1 | 80.1 | 75.1 | 0.311 | 0.238 | 197 |
| 4 | s04_straight | straight | 815–1000 | 80.0 | 8.34 | 75.1/79.7/80.2 | 75.1 | 80.1 | 0.185 | 0.082 | 418 |
| 5 | s05_turn_R_1040m | corner | 1000–1080 | 78.0 | 3.72 | 78.0/78.2/80.1 | 80.1 | 78.1 | 0.245 | 0.183 | 187 |
| 6 | s06_straight | straight | 1080–1480 | 80.0 | 17.984 | 78.1/80.0/80.2 | 78.1 | 80.0 | 0.219 | 0.066 | 860 |
| 7 | s07_turn_L_1540m | corner | 1480–1600 | 78.0 | 5.61 | 77.9/78.1/80.0 | 80.0 | 78.1 | 0.261 | 0.183 | 256 |
| 8 | s08_straight | straight | 1600–2380 | 95.0 | 30.206 | 78.1/93.3/95.1 | 78.1 | 95.0 | 0.839 | 0.621 | 1374 |
| 9 | s09_turn_R_2605m | corner | 2380–2540 | 58.0 | 10.098 | 55.4/59.7/95.1 | 95.0 | 59.2 | 0.667 | 0.612 | 460 |
| 10 | s10_straight | straight | 2540–2945 | 80.0 | 18.494 | 59.2/79.2/81.1 | 59.2 | 81.0 | 0.193 | 0.171 | 884 |
| 11 | s11_turn_R_2985m | corner | 2945–3025 | 78.0 | 3.72 | 78.4/78.7/81.0 | 81.0 | 78.4 | 0.238 | 0.186 | 187 |
| 12 | s12_straight | straight | 3025–3245 | 80.0 | 9.88 | 78.4/80.0/80.1 | 78.4 | 80.1 | 0.206 | 0.051 | 495 |
| 13 | s13_turn_L_3272m | corner | 3245–3300 | 58.0 | 3.7 | 56.9/59.1/80.1 | 80.1 | 58.7 | 0.661 | 0.546 | 186 |
| 14 | s14_straight | straight | 3300–3605 | 80.0 | 14.34 | 58.7/76.5/80.1 | 58.7 | 80.1 | 0.236 | 0.096 | 718 |
| 15 | s15_turn_L_3607m | corner | 3605–3610 | 78.0 | 0.14 | 79.0/79.0/80.0 | 80.0 | 79.0 | 0.0 | 0.0 | 407 |

_Sum of per-segment elapsed time: **166.008 s** (≠ lap time — each segment's elapsed counts from first-frame-in to last-frame-in, so inter-segment gaps are not double-counted but the very last tick of each segment is dropped)._

## Corner Entry/Exit Analysis

```
Segment                  | Entry km/h | Target km/h | Exit km/h | Margin
--------------------------------------------------------------------------------
s01_turn_L_475m          |       81.0 |        75.0 |      75.0 | OK
s03_turn_R_775m          |       80.1 |        75.0 |      75.1 | OK
s05_turn_R_1040m         |       80.1 |        78.0 |      78.1 | OK
s07_turn_L_1540m         |       80.0 |        78.0 |      78.1 | OK
s09_turn_R_2605m         |       95.0 |        58.0 |      59.2 | ⚠️  HOT ENTRY
s11_turn_R_2985m         |       81.0 |        78.0 |      78.4 | OK
s13_turn_L_3272m         |       80.1 |        58.0 |      58.7 | ⚠️  HOT ENTRY
s15_turn_L_3607m         |       80.0 |        78.0 |      79.0 | OK
```
