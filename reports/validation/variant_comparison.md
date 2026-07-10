# Distance-Variant Comparison (E1 + E2, gold shelf)

- Generated: 2026-06-09T20:15:06.315729+00:00
- Baseline dir: data/baselines/author_space_build/work_baselines
- Manifest: data/baselines/author_space_build/control_shelf_manifest.yaml
- Authors: 11 calibrated (59 works); seed 20260609
- MFW block: top-300 shelf words, Burrows Delta (mean |z_i - z_j|); blend scale = median(pairwise d18) / median(pairwise Delta) = 5.375

Combined distance: `d = alpha * d_d18 + (1 - alpha) * scale * d_delta`.

| Variant | E1 AUC (>=0.90) | Silh.>0 frac (>=0.80) | E2 top-1 (>=0.70) | E2 top-3 (>=0.85) | Gates |
|---|---|---|---|---|---|
| d18 | 0.892 FAIL | 0.545 FAIL | 64.4% FAIL | 84.7% FAIL | FAIL |
| d18_weighted | 0.913 PASS | 0.636 FAIL | 74.6% PASS | 93.2% PASS | FAIL |
| mfw_delta | 0.924 PASS | 0.818 PASS | 94.9% PASS | 96.6% PASS | PASS |
| combined_alpha0.3 | 0.933 PASS | 0.909 PASS | 93.2% PASS | 94.9% PASS | PASS |
| combined_alpha0.5 | 0.930 PASS | 0.909 PASS | 88.1% PASS | 94.9% PASS | PASS |
| combined_alpha0.7 | 0.918 PASS | 0.909 PASS | 81.4% PASS | 93.2% PASS | PASS |

## Selection

- Selected variant: **mfw_delta**
- Rationale: mfw_delta is the simplest passing variant; combined does not clearly beat it, so the simpler model wins.

Selection rule: prefer the simplest variant passing all four gates (d18 < d18_weighted < mfw_delta < combined); combined is preferred over mfw_delta only when it clearly beats it (>= 3/4 gate metrics better-or-equal AND top-1 at least 2 points higher).
