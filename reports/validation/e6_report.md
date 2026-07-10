# E6 — Window-Length Sensitivity (issue #60 criterion 3)

- Generated: 2026-06-09T20:31:25.514318+00:00
- Baseline dir: data/baselines/author_space_build/work_baselines
- Manifest: data/baselines/author_space_build/control_shelf_manifest.yaml
- Authors: 11 calibrated; 59 works with body text; seed 20260609
- MFW block: top-300 shelf words, Burrows Delta; up to 5 non-overlapping windows sampled per work; attribution = nearest author MFW centroid (leave-one-out: own work excluded from own-author centroid).

**No pass/fail gate** — this experiment documents how within/between separation degrades as the measured text gets shorter, and at what length attribution becomes unreliable.

| Window (words) | Windows | Top-1 | Top-3 | W median | B median | B/W ratio | AUC |
|---|---|---|---|---|---|---|---|
| 800 | 295 | 56.3% | 78.0% | 2.217 | 2.347 | 1.06 | 0.686 |
| 1500 | 295 | 74.2% | 87.8% | 1.752 | 1.911 | 1.09 | 0.748 |
| 3000 | 295 | 85.4% | 94.2% | 1.341 | 1.535 | 1.14 | 0.802 |
| full | 59 | 94.9% | 96.6% | 0.596 | 0.958 | 1.61 | 0.924 |

## Reading

As windows shrink from full works to 800 words, top-1 attribution moves from 94.9% (full) to 85.4% at 3000w and 56.3% at 800w; W-vs-B AUC moves from 0.924 to 0.686. The within-author median rises as windows shorten (small-sample noise inflates every distance) while the between-author median rises more slowly, compressing the B/W separation ratio.
Attribution falls below the E2 top-1 gate level (70%) at: 800w. W/B percentile statements at these window lengths should carry an explicit short-text caveat.
