# E8 — Length-Matched Envelopes (LM-W) + Same-Author Positive Control

- Generated: 2026-06-11T05:05:47.915860+00:00
- Window length: 3000 MFW tokens; seed 20260609; max windows/work: all
- Envelope: window -> own-author centroid Burrows Delta, leave-one-WORK-out (window's own work never in its centroid).
- Held-out test: each work's windows vs the p90 of the OTHER works' window distances (non-circular).
- Gate per author: binomial 95% CI contains 0.90 OR rate >= 0.80. The floor is the operative criterion because windows cluster within works (2-7 works/author), making the window-count binomial CI anti-conservative; a single off-style work should not fail an author whose envelope otherwise captures their length-matched variation, while rate < 0.80 genuinely would.

## Shelf `wave2` — **FAIL**

- Artifact: `data/artifacts/author_space_v1_wave2.json` (sha256 `e1907b2a287d…`); vocab_filter: none
- Envelope sidecar: `data/artifacts/lm_envelopes_wave2_3000w.json`
- Pooled held-out inside@p90: 2495/2842 = 0.878 (CP 95% [0.865, 0.890])

| Author | Works | Windows | LM p50 | LM p90 | LM p95 | LM p99 | Held-out inside@p90 | Rate | CP 95% CI | Cluster-adj CI (DEFF) | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| delillo-don | 6 | 223 | 1.313 | 1.458 | 1.533 | 1.652 | 201/223 | 0.901 | [0.854, 0.937] | [0.854, 0.937] (1.0) | PASS |
| didion-joan | 4 | 71 | 1.321 | 1.490 | 1.518 | 1.555 | 63/71 | 0.887 | [0.790, 0.950] | [0.790, 0.950] (1.0) | PASS |
| foster_wallace-david | 3 | 281 | 1.424 | 1.600 | 1.660 | 1.762 | 254/281 | 0.904 | [0.863, 0.936] | [0.808, 0.962] (4.1) | PASS |
| ishiguro-kazuo | 6 | 200 | 1.547 | 1.715 | 1.768 | 1.893 | 178/200 | 0.890 | [0.838, 0.930] | [0.759, 0.964] (4.5) | PASS |
| mccarthy-cormac | 8 | 251 | 1.458 | 1.715 | 1.913 | 2.083 | 227/251 | 0.904 | [0.861, 0.938] | [0.578, 0.997] (23.1) | PASS |
| morrison-toni | 9 | 203 | 1.345 | 1.510 | 1.559 | 2.027 | 180/203 | 0.887 | [0.835, 0.927] | [0.811, 0.940] (1.9) | PASS |
| murakami-haruki | 7 | 436 | 1.464 | 1.627 | 1.680 | 1.806 | 387/436 | 0.888 | [0.854, 0.916] | [0.817, 0.938] (3.7) | PASS |
| ondaatje-michael | 7 | 158 | 1.291 | 1.409 | 1.442 | 1.577 | 140/158 | 0.886 | [0.826, 0.931] | [0.765, 0.958] (3.1) | PASS |
| proulx-annie | 4 | 155 | 1.276 | 1.437 | 1.496 | 1.557 | 126/155 | 0.813 | [0.742, 0.871] | [0.594, 0.944] (6.9) | PASS |
| pynchon-thomas | 4 | 263 | 1.277 | 1.431 | 1.480 | 1.563 | 227/263 | 0.863 | [0.816, 0.902] | [0.419, 0.997] (38.8) | PASS |
| robinson-marilynne | 3 | 85 | 1.543 | 1.731 | 1.812 | 1.871 | 70/85 | 0.824 | [0.726, 0.898] | [0.270, 0.998] (19.3) | PASS |
| saunders-george | 4 | 79 | 1.401 | 1.535 | 1.563 | 1.712 | 70/79 | 0.886 | [0.795, 0.947] | [0.721, 0.971] (2.5) | PASS |
| sebald-w_g | 3 | 57 | 1.168 | 1.294 | 1.353 | 1.421 | 50/57 | 0.877 | [0.763, 0.949] | [0.687, 0.973] (2.2) | PASS |
| tokarczuk-olga | 6 | 269 | 1.311 | 1.452 | 1.512 | 1.573 | 236/269 | 0.877 | [0.832, 0.914] | [0.811, 0.927] (1.9) | PASS |
| whitehead-colson | 4 | 111 | 1.240 | 1.454 | 1.511 | 1.608 | 86/111 | 0.775 | [0.686, 0.849] | [0.237, 0.994] (24.8) | **FAIL** |

Gate-floor failures and their driver works (held-out inside per work):
- whitehead-colson: rate 0.775; The Intuitionist 3/28 (cluster-adjusted CI contains 0.90)

## Shelf `wave2_fwonly` — **FAIL**

- Artifact: `data/artifacts/author_space_v1_wave2_fwonly.json` (sha256 `fb401057db7a…`); vocab_filter: function_words_only
- Envelope sidecar: `data/artifacts/lm_envelopes_wave2_fwonly_3000w.json`
- Pooled held-out inside@p90: 2380/2842 = 0.837 (CP 95% [0.823, 0.851])

| Author | Works | Windows | LM p50 | LM p90 | LM p95 | LM p99 | Held-out inside@p90 | Rate | CP 95% CI | Cluster-adj CI (DEFF) | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| delillo-don | 6 | 223 | 1.117 | 1.287 | 1.319 | 1.361 | 196/223 | 0.879 | [0.829, 0.919] | [0.745, 0.958] (5.1) | PASS |
| didion-joan | 4 | 71 | 1.114 | 1.239 | 1.276 | 1.337 | 61/71 | 0.859 | [0.756, 0.930] | [0.725, 0.944] (1.5) | PASS |
| foster_wallace-david | 3 | 281 | 1.464 | 1.689 | 1.741 | 1.905 | 201/281 | 0.715 | [0.659, 0.767] | [0.366, 0.939] (27.5) | **FAIL** |
| ishiguro-kazuo | 6 | 200 | 1.382 | 1.575 | 1.653 | 1.770 | 174/200 | 0.870 | [0.815, 0.913] | [0.608, 0.983] (12.7) | PASS |
| mccarthy-cormac | 8 | 251 | 1.242 | 1.553 | 1.669 | 1.805 | 223/251 | 0.888 | [0.843, 0.925] | [0.560, 0.995] (23.0) | PASS |
| morrison-toni | 9 | 203 | 1.179 | 1.336 | 1.360 | 1.787 | 181/203 | 0.892 | [0.841, 0.931] | [0.801, 0.951] (2.6) | PASS |
| murakami-haruki | 7 | 436 | 1.380 | 1.738 | 1.856 | 2.033 | 375/436 | 0.860 | [0.824, 0.891] | [0.452, 0.995] (55.7) | PASS |
| ondaatje-michael | 7 | 158 | 1.104 | 1.227 | 1.241 | 1.297 | 141/158 | 0.892 | [0.833, 0.936] | [0.690, 0.982] (7.0) | PASS |
| proulx-annie | 4 | 155 | 1.009 | 1.197 | 1.232 | 1.287 | 115/155 | 0.742 | [0.666, 0.809] | [0.380, 0.954] (16.0) | **FAIL** |
| pynchon-thomas | 4 | 263 | 1.312 | 1.498 | 1.570 | 1.710 | 218/263 | 0.829 | [0.778, 0.872] | [0.334, 0.996] (47.6) | PASS |
| robinson-marilynne | 3 | 85 | 1.309 | 1.497 | 1.540 | 1.595 | 73/85 | 0.859 | [0.766, 0.925] | [0.420, 0.997] (12.3) | PASS |
| saunders-george | 4 | 79 | 1.257 | 1.373 | 1.486 | 1.637 | 70/79 | 0.886 | [0.795, 0.947] | [0.525, 0.996] (8.4) | PASS |
| sebald-w_g | 3 | 57 | 1.108 | 1.236 | 1.251 | 1.275 | 48/57 | 0.842 | [0.721, 0.925] | [0.709, 0.931] (1.2) | PASS |
| tokarczuk-olga | 6 | 269 | 1.249 | 1.391 | 1.444 | 1.546 | 217/269 | 0.807 | [0.754, 0.852] | [0.590, 0.940] (11.7) | PASS |
| whitehead-colson | 4 | 111 | 1.036 | 1.243 | 1.274 | 1.353 | 87/111 | 0.784 | [0.696, 0.856] | [0.299, 0.990] (19.8) | **FAIL** |

Gate-floor failures and their driver works (held-out inside per work):
- foster_wallace-david: rate 0.715; Girl With Curious Hair 41/42; Infinite jest 108/186; The Broom of the System 52/53 (cluster-adjusted CI contains 0.90)
- proulx-annie: rate 0.742; Barkskins 38/77; The Shipping News 36/37 (cluster-adjusted CI contains 0.90)
- whitehead-colson: rate 0.784; The Intuitionist 6/28; The Nickel Boys 18/19; The Underground Railroad 28/29 (cluster-adjusted CI contains 0.90)

## Shelf `pd` — **PASS**

- Artifact: `data/artifacts/author_space_pd_v1.json` (sha256 `9568b219ba7e…`); vocab_filter: none
- Envelope sidecar: `data/artifacts/lm_envelopes_pd_3000w.json`
- Pooled held-out inside@p90: 1375/1575 = 0.873 (CP 95% [0.856, 0.889])

| Author | Works | Windows | LM p50 | LM p90 | LM p95 | LM p99 | Held-out inside@p90 | Rate | CP 95% CI | Cluster-adj CI (DEFF) | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| austen-jane | 5 | 214 | 1.574 | 1.706 | 1.754 | 1.850 | 189/214 | 0.883 | [0.832, 0.923] | [0.763, 0.956] (4.1) | PASS |
| bronte-charlotte | 4 | 228 | 1.494 | 1.640 | 1.697 | 1.799 | 201/228 | 0.882 | [0.832, 0.920] | [0.766, 0.953] (4.1) | PASS |
| dickens-charles | 4 | 355 | 1.647 | 1.838 | 1.877 | 2.002 | 315/355 | 0.887 | [0.850, 0.918] | [0.767, 0.959] (7.0) | PASS |
| fitzgerald-f_scott | 3 | 85 | 1.557 | 1.723 | 1.761 | 1.840 | 77/85 | 0.906 | [0.823, 0.958] | [0.823, 0.958] (1.0) | PASS |
| forster-e_m | 5 | 141 | 1.485 | 1.578 | 1.613 | 1.699 | 128/141 | 0.908 | [0.847, 0.950] | [0.830, 0.958] (1.5) | PASS |
| hawthorne-nathaniel | 3 | 82 | 1.423 | 1.537 | 1.557 | 1.618 | 74/82 | 0.902 | [0.817, 0.957] | [0.788, 0.967] (1.6) | PASS |
| joyce-james | 3 | 140 | 1.735 | 2.044 | 2.143 | 2.242 | 114/140 | 0.814 | [0.740, 0.875] | [0.554, 0.958] (8.3) | PASS |
| melville-herman | 4 | 189 | 1.505 | 1.724 | 1.807 | 1.940 | 152/189 | 0.804 | [0.740, 0.858] | [0.493, 0.967] (15.0) | PASS |
| woolf-virginia | 4 | 141 | 1.579 | 1.744 | 1.776 | 1.821 | 125/141 | 0.887 | [0.822, 0.934] | [0.752, 0.963] (3.3) | PASS |

## Shelf `pd_fwonly` — **FAIL**

- Artifact: `data/artifacts/author_space_pd_v1_fwonly.json` (sha256 `e1ef12ad4265…`); vocab_filter: function_words_only
- Envelope sidecar: `data/artifacts/lm_envelopes_pd_fwonly_3000w.json`
- Pooled held-out inside@p90: 1378/1575 = 0.875 (CP 95% [0.858, 0.891])

| Author | Works | Windows | LM p50 | LM p90 | LM p95 | LM p99 | Held-out inside@p90 | Rate | CP 95% CI | Cluster-adj CI (DEFF) | Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| austen-jane | 5 | 214 | 1.314 | 1.453 | 1.498 | 1.564 | 193/214 | 0.902 | [0.854, 0.938] | [0.854, 0.938] (1.0) | PASS |
| bronte-charlotte | 4 | 228 | 1.363 | 1.550 | 1.609 | 1.752 | 198/228 | 0.868 | [0.818, 0.909] | [0.634, 0.978] (12.1) | PASS |
| dickens-charles | 4 | 355 | 1.445 | 1.612 | 1.660 | 1.742 | 318/355 | 0.896 | [0.859, 0.926] | [0.816, 0.949] (3.8) | PASS |
| fitzgerald-f_scott | 3 | 85 | 1.702 | 2.071 | 2.134 | 2.172 | 67/85 | 0.788 | [0.686, 0.869] | [0.374, 0.982] (11.1) | **FAIL** |
| forster-e_m | 5 | 141 | 1.392 | 1.569 | 1.584 | 1.657 | 124/141 | 0.879 | [0.814, 0.928] | [0.806, 0.932] (1.2) | PASS |
| hawthorne-nathaniel | 3 | 82 | 1.362 | 1.486 | 1.571 | 1.612 | 71/82 | 0.866 | [0.773, 0.931] | [0.601, 0.982] (5.2) | PASS |
| joyce-james | 3 | 140 | 1.448 | 1.785 | 2.085 | 2.668 | 114/140 | 0.814 | [0.740, 0.875] | [0.554, 0.958] (8.3) | PASS |
| melville-herman | 4 | 189 | 1.534 | 1.719 | 1.769 | 1.929 | 166/189 | 0.878 | [0.823, 0.921] | [0.755, 0.953] (3.8) | PASS |
| woolf-virginia | 4 | 141 | 1.449 | 1.627 | 1.691 | 1.745 | 127/141 | 0.901 | [0.839, 0.945] | [0.829, 0.949] (1.3) | PASS |

Gate-floor failures and their driver works (held-out inside per work):
- fitzgerald-f_scott: rate 0.788; The Beautiful and Damned 23/41 (cluster-adjusted CI contains 0.90)

**Overall E8: FAIL**
