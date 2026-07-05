# E8 Yardstick — Observed Self-Entry Comparators (G4, reporting only)

- Generated: 2026-06-11T08:06:52.273417+00:00; source: `reports/validation/wave2/e8_results.json`.
- REPORTING DATA ONLY — the strict gate verdict is quoted as committed (no re-adjudication). The envelopes are used with the OBSERVED self-entry rate as the comparator; the nominal-0.90 gate FAILS strictly (per-author floor, 3 of 4 shelves) and the pooled rates below are the honest yardstick the entry tables are read against.
- Overall strict gate as committed: **FAIL**.

| Shelf | Inside@p90 | Rate | window-naive CP 95% | work-level bootstrap 95% | n works | strict gate |
|---|---|---|---|---|---|---|
| wave2 | 2495/2842 | 87.8% | [86.5%, 89.0%] | [83.8%, 91.1%] | 78 | **FAIL** |
| wave2_fwonly | 2380/2842 | 83.7% | [82.3%, 85.1%] | [77.3%, 90.2%] | 78 | **FAIL** |
| pd | 1375/1575 | 87.3% | [85.6%, 88.9%] | [82.9%, 91.4%] | 35 | PASS |
| pd_fwonly | 1378/1575 | 87.5% | [85.8%, 89.1%] | [83.6%, 91.1%] | 35 | **FAIL** |

Usage: entry rates are compared against these OBSERVED self-entry rates (the empirical yardstick), not against the nominal 0.90. The work-level bootstrap CI is the honest interval (windows cluster within works); the window-naive CP interval is shown so the anti-conservatism is visible rather than hidden.
