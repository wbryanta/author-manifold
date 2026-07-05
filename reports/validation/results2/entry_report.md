# Results 2.0 — Entry/Approach Re-analysis Against Length-Matched Envelopes (LM-W)

- Generated: 2026-06-11T08:06:52.273417+00:00
- Window length: 3000 MFW tokens; samples truncated to the window length before placement (scale-valid vs the envelopes).
- Floors (applied in MFW tokens): hard 1500 (excluded from every claim), practice 3000 (below = separately reported stratum).
- Styled samples: 318 total -> 236 primary (>= practice floor), 76 sub-floor stratum, 6 hard-floor EXCLUDED: gemma4_26b/estate_sale__exemplar_morrison-toni__s2.txt, gemma4_26b/irrigation__exemplar_mccarthy-cormac__s1.txt, gemma4_26b/irrigation__exemplar_mccarthy-cormac__s3.txt, gemma4_26b/irrigation__exemplar_mccarthy-cormac__s4.txt, gemma4_26b/irrigation__exemplar_mccarthy-cormac__s5.txt, gemma4_26b/night_ferry__exemplar_ondaatje-michael__s3.txt
- Models with ZERO primary-stratum styled samples (all generations below the practice floor; they appear only in the sub-floor stratum): gemma4:26b
- Clustering treatment: ICC (one-way ANOVA estimator) over (model x target x condition) cells; design effect DEFF = 1 + (m_bar - 1) * ICC; CP bounds also shown at DEFF-deflated counts; cell-level bootstrap CIs as the nonparametric complement.

## Reading (LM-W entry, both vocabularies)

- Full vocab @p90: styled models pooled 48/236 (20.3%); best model gpt-5 40.0%; Brinton 34/36 (94.4%); same-author held-out yardstick 87.8% (wave2) / 87.3% (pd).
- Fw-only @p90: styled models pooled 72/236 (30.5%); best model gpt-5 72.5%; Brinton 27/36 (75.0%). Note the best model's fw-only entry rate is comparable to the human pastiche's — the human-vs-machine gap at p90 is carried by the model AVERAGE, not by the best model, and per-target rates are strongly heterogeneous (see per-target tables; McCarthy's wide envelope admits most attempts, Didion/Ondaatje admit few).
- The two-sided result replaces the old vacuous criterion: the same-author positive control now sits near the nominal 0.90 where the full-novel criterion put it near 0.

## a. Entry against LM-W envelopes

### Vocabulary: full (top-300 mixed)

Primary stratum n = 236 (54 cells; ICC of target distance 0.698; median target distance 1.708).

| Level | Entered | Rate | CP 95% | one-sided upper | ICC(entered) | DEFF | n_eff | DEFF-adj CP 95% | cell-bootstrap 95% | rate range over threshold CI |
|---|---|---|---|---|---|---|---|---|---|---|
| p90 | 48/236 | 20.3% | [15.4%, 26.0%] | 25.1% | 0.697 | 3.35 | 70 | [11.7%, 31.6%] | [10.6%, 30.6%] | [15.3%, 26.3%] |
| p95 | 65/236 | 27.5% | [21.9%, 33.7%] | 32.7% | 0.785 | 3.64 | 65 | [17.2%, 40.1%] | [16.5%, 39.1%] | [22.5%, 33.1%] |
| p99 | 128/236 | 54.2% | [47.7%, 60.7%] | 59.7% | 0.818 | 3.76 | 63 | [41.2%, 66.9%] | [40.9%, 66.7%] | [29.7%, 58.9%] |

Per model (p90; no cross-model averaging without the best model shown):

| Model | Entered@p90 | Rate | CP 95% | median target dist |
|---|---|---|---|---|
| claude-fable-5 | 11/39 | 28.2% | [15.0%, 44.9%] | 1.576 |
| claude-haiku-4-5 | 1/17 | 5.9% | [0.1%, 28.7%] | 1.781 |
| claude-opus-4-8 | 9/40 | 22.5% | [10.8%, 38.5%] | 1.797 |
| claude-sonnet-4-6 | 6/32 | 18.8% | [7.2%, 36.4%] | 1.732 |
| gpt-5 | 16/40 | 40.0% | [24.9%, 56.7%] | 1.524 |
| gpt-5-mini | 5/40 | 12.5% | [4.2%, 26.8%] | 1.721 |
| qwen3.6:35b | 0/28 | 0.0% | [0.0%, 12.3%] | 2.049 |

Best model @p90: **gpt-5** 16/40 (40.0%).

| Target | LM p90 | Entered@p90 | Rate | median target dist |
|---|---|---|---|---|
| didion-joan | 1.490 | 2/66 | 3.0% | 1.732 |
| mccarthy-cormac | 1.715 | 41/56 | 73.2% | 1.591 |
| morrison-toni | 1.510 | 3/58 | 5.2% | 1.788 |
| ondaatje-michael | 1.409 | 2/56 | 3.6% | 1.668 |

Per condition @p90: style_prompted: 25/124 (20.2%); exemplar: 23/112 (20.5%)

Sub-floor stratum (>= 1500, < 3000 tokens; placed at native length — scale-mismatched vs the 3000-token envelope, reported separately, licenses no headline claim): n = 76; entered@p90 6/76 (7.9%)

### Vocabulary: fwonly (function-words-only)

Primary stratum n = 236 (54 cells; ICC of target distance 0.547; median target distance 1.418).

| Level | Entered | Rate | CP 95% | one-sided upper | ICC(entered) | DEFF | n_eff | DEFF-adj CP 95% | cell-bootstrap 95% | rate range over threshold CI |
|---|---|---|---|---|---|---|---|---|---|---|
| p90 | 72/236 | 30.5% | [24.7%, 36.8%] | 35.8% | 0.545 | 2.84 | 83 | [20.9%, 41.6%] | [20.1%, 40.9%] | [23.3%, 33.5%] |
| p95 | 82/236 | 34.7% | [28.7%, 41.2%] | 40.2% | 0.614 | 3.07 | 77 | [24.2%, 46.5%] | [23.6%, 45.8%] | [31.4%, 42.8%] |
| p99 | 145/236 | 61.4% | [54.9%, 67.7%] | 66.7% | 0.697 | 3.35 | 70 | [49.1%, 72.8%] | [49.6%, 72.4%] | [37.3%, 70.3%] |

Per model (p90; no cross-model averaging without the best model shown):

| Model | Entered@p90 | Rate | CP 95% | median target dist |
|---|---|---|---|---|
| claude-fable-5 | 14/39 | 35.9% | [21.2%, 52.8%] | 1.360 |
| claude-haiku-4-5 | 0/17 | 0.0% | [0.0%, 19.5%] | 1.514 |
| claude-opus-4-8 | 9/40 | 22.5% | [10.8%, 38.5%] | 1.471 |
| claude-sonnet-4-6 | 3/32 | 9.4% | [2.0%, 25.0%] | 1.557 |
| gpt-5 | 29/40 | 72.5% | [56.1%, 85.4%] | 1.251 |
| gpt-5-mini | 14/40 | 35.0% | [20.6%, 51.7%] | 1.360 |
| qwen3.6:35b | 3/28 | 10.7% | [2.3%, 28.2%] | 1.539 |

Best model @p90: **gpt-5** 29/40 (72.5%).

| Target | LM p90 | Entered@p90 | Rate | median target dist |
|---|---|---|---|---|
| didion-joan | 1.239 | 9/66 | 13.6% | 1.419 |
| mccarthy-cormac | 1.553 | 43/56 | 76.8% | 1.422 |
| morrison-toni | 1.336 | 14/58 | 24.1% | 1.477 |
| ondaatje-michael | 1.227 | 6/56 | 10.7% | 1.377 |

Per condition @p90: style_prompted: 36/124 (29.0%); exemplar: 36/112 (32.1%)

Sub-floor stratum (>= 1500, < 3000 tokens; placed at native length — scale-mismatched vs the 3000-token envelope, reported separately, licenses no headline claim): n = 76; entered@p90 9/76 (11.8%)

## b. Human baselines on the same footing (PD shelf)

### Brinton pastiche vs Austen LM envelope — full

- n = 36 chunks (single work — chunks are NOT independent (one author, one novel, shared characters/world); n is descriptive, not inferential)
- Nearest-is-Austen: 31/36 (86.1%)
- Median distance to Austen: 1.549 (Austen LM p50 1.574, p90 1.706)

| Level | Entered | Rate | CP 95% | rate range over threshold CI |
|---|---|---|---|---|
| p90 | 34/36 | 94.4% | [81.3%, 99.3%] | [94.4%, 100.0%] |
| p95 | 36/36 | 100.0% | [90.3%, 100.0%] | [94.4%, 100.0%] |
| p99 | 36/36 | 100.0% | [90.3%, 100.0%] | [100.0%, 100.0%] |

### Brinton pastiche vs Austen LM envelope — fwonly

- n = 36 chunks (single work — chunks are NOT independent (one author, one novel, shared characters/world); n is descriptive, not inferential)
- Nearest-is-Austen: 36/36 (100.0%)
- Median distance to Austen: 1.411 (Austen LM p50 1.314, p90 1.453)

| Level | Entered | Rate | CP 95% | rate range over threshold CI |
|---|---|---|---|---|
| p90 | 27/36 | 75.0% | [57.8%, 87.9%] | [61.1%, 80.6%] |
| p95 | 31/36 | 86.1% | [70.5%, 95.3%] | [75.0%, 97.2%] |
| p99 | 35/36 | 97.2% | [85.5%, 99.9%] | [97.2%, 100.0%] |

### Same-author positive control (E8 held-out windows, leave-work-out)

| Shelf | Inside@p90 | Rate | CP 95% |
|---|---|---|---|
| wave2 | 2495/2842 | 87.8% | [86.5%, 89.0%] |
| wave2_fwonly | 2380/2842 | 83.7% | [82.3%, 85.1%] |
| pd | 1375/1575 | 87.3% | [85.6%, 88.9%] |
| pd_fwonly | 1378/1575 | 87.5% | [85.8%, 89.1%] |

## c. Approach, corrected (scenario-matched null)

### Vocabulary: full

| Target (scenario) | Styled nearest-is-target | Scenario-matched null | Binomial p (greater) | cell-bootstrap 95% |
|---|---|---|---|---|
| didion-joan (hotel_fire) | 27/66 (40.9%) | 4/40 (10.0%) | 4.75e-11 | [24.6%, 57.6%] |
| mccarthy-cormac (irrigation) | 39/56 (69.6%) | 4/40 (10.0%) | 1.71e-26 | [45.6%, 90.3%] |
| morrison-toni (estate_sale) | 14/58 (24.1%) | 0/40 (0.0%) | 0.00e+00 | [8.5%, 41.4%] |
| ondaatje-michael (night_ferry) | 42/56 (75.0%) | 26/40 (65.0%) | 7.39e-02 | [65.6%, 83.3%] |

Pooled: 122/236 (51.7%) vs scenario-matched null p0 = 34/160 (21.2%); binomial p = 8.59e-25; ICC 0.429, DEFF 2.44, n_eff 97; DEFF-adj CP [41.3%, 62.0%]; cell-bootstrap [41.5%, 62.0%].

| Model | Nearest-is-target | Rate | CP 95% | above matched null |
|---|---|---|---|---|
| claude-fable-5 | 26/39 | 66.7% | [49.8%, 80.9%] | yes |
| claude-haiku-4-5 | 13/17 | 76.5% | [50.1%, 93.2%] | yes |
| claude-opus-4-8 | 27/40 | 67.5% | [50.9%, 81.4%] | yes |
| claude-sonnet-4-6 | 14/32 | 43.8% | [26.4%, 62.3%] | yes |
| gpt-5 | 27/40 | 67.5% | [50.9%, 81.4%] | yes |
| gpt-5-mini | 8/40 | 20.0% | [9.1%, 35.6%] | NO |
| qwen3.6:35b | 7/28 | 25.0% | [10.7%, 44.9%] | yes |

Best model: **claude-haiku-4-5** (76.5%).

Rank-vs-metric (stated plainly): median styled-minus-matched-unprompted distance to target = -0.0051 Delta (n = 236; cell-bootstrap 95% [-0.0423, +0.0399]; 51.3% of styled samples closer than matched unprompted) — the CI brackets zero: prompting raises the target's nearest-neighbor rank without closing the function-word distance (distance-flat). Native-length reference (the scale-mixed draft-v0.2 construction): +0.0027 (n = 236).

### Vocabulary: fwonly

| Target (scenario) | Styled nearest-is-target | Scenario-matched null | Binomial p (greater) | cell-bootstrap 95% |
|---|---|---|---|---|
| didion-joan (hotel_fire) | 34/66 (51.5%) | 2/40 (5.0%) | 8.30e-27 | [35.5%, 68.2%] |
| mccarthy-cormac (irrigation) | 31/56 (55.4%) | 1/40 (2.5%) | 6.55e-35 | [29.4%, 80.0%] |
| morrison-toni (estate_sale) | 0/58 (0.0%) | 0/40 (0.0%) | 1.00e+00 | [0.0%, 0.0%] |
| ondaatje-michael (night_ferry) | 4/56 (7.1%) | 2/40 (5.0%) | 3.07e-01 | [0.0%, 15.7%] |

Pooled: 69/236 (29.2%) vs scenario-matched null p0 = 5/160 (3.1%); binomial p = 3.68e-46; ICC 0.619, DEFF 3.08, n_eff 77; DEFF-adj CP [19.4%, 40.7%]; cell-bootstrap [18.6%, 39.6%].

| Model | Nearest-is-target | Rate | CP 95% | above matched null |
|---|---|---|---|---|
| claude-fable-5 | 16/39 | 41.0% | [25.6%, 57.9%] | yes |
| claude-haiku-4-5 | 9/17 | 52.9% | [27.8%, 77.0%] | yes |
| claude-opus-4-8 | 16/40 | 40.0% | [24.9%, 56.7%] | yes |
| claude-sonnet-4-6 | 14/32 | 43.8% | [26.4%, 62.3%] | yes |
| gpt-5 | 11/40 | 27.5% | [14.6%, 43.9%] | yes |
| gpt-5-mini | 2/40 | 5.0% | [0.6%, 16.9%] | yes |
| qwen3.6:35b | 1/28 | 3.6% | [0.1%, 18.3%] | yes |

Best model: **claude-haiku-4-5** (52.9%).

Rank-vs-metric (stated plainly): median styled-minus-matched-unprompted distance to target = -0.0868 Delta (n = 236; cell-bootstrap 95% [-0.1215, -0.0546]; 71.6% of styled samples closer than matched unprompted) — the median distance change is small but its CI sits entirely below zero: under this vocabulary, prompting also modestly closes the distance at matched length. Native-length reference (the scale-mixed draft-v0.2 construction): -0.0576 (n = 236).

## d. Translation bound at matched length

- Design: within translated authors: all work pairs where both works carry a single-translator tag; distance = window-level (3000-token) Burrows Delta, all cross-work window pairs, summarized per WORK PAIR (the inferential unit); window pairs within a work pair are not independent
- Same-translator work pairs: n = 5, median window Delta 1.731
- Cross-translator work pairs: n = 8, median window Delta 1.789
- Cross minus same: +0.059; exact permutation p (one-sided) = 0.100
- Reference (same-author cross-work window pairs, non-translated authors): median 1.803 (n = 50 work pairs)
- **Recommendation: cut from paper** (supports magnitude claim vs prompting: False)

## e. Chassis restated (K10 — immobility)

- Source: `reports/validation/r3_dimension_gap.json` (n = 318)
- MFW median movement: -0.0300 Delta [-0.0475, -0.0131]; unprompted gap 1.654; closure -2.9% to -0.8%; sign-test Holm p = 0.042
- Per-target MFW movement: didion-joan +0.033, mccarthy-cormac +0.058, morrison-toni -0.079, ondaatje-michael -0.067
- Reading: Immobility, not directed movement-away: aggregate MFW movement median -0.030 Delta [-0.048, -0.013] on an unprompted gap of 1.654 (closure -2.9% to -0.8%), with per-target signs split 2/4 toward. The CI brackets zero-to-slightly-negative and the sign flips across targets; the defensible claim is |closure| <= ~3% in either direction against 14-21% closure on texture dimensions (K10).
