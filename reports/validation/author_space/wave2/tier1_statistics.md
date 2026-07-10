# Tier 1 statistical treatment (issue #95 P7)

- Generated: 2026-06-11T00:32:04.855686+00:00
- E4 results: `reports/validation/wave2/e4_results.json` (n placed = 910; 400 unprompted, 159 style-prompted, 159 exemplar, 8 models, 15 anchor authors)
- Artifact: `data/artifacts/author_space_v1_wave2.json`
- Manuscript trajectory: `not provided`
- Seed: 20260609; bootstrap resamples: 10000; permutations: 10000

All binomial intervals are exact Clopper-Pearson. All tests are exact (binomial / Mann-Whitney / hypergeometric); no normal approximations are used at these n's.

## 1. Enter-rate claim

**0/159 style-prompted samples entered the target author's W-p90 region.**

- Enter rate 0/159 = 0.000; CP 95% two-sided [0.0000, 0.0229]; one-sided 95% upper bound **0.0187**.
- The data exclude (one-sided alpha = 0.05) any true enter-rate >= **1.9%**.

| H0 (one-sided) | p-value | rejected at 0.05 |
|---|---|---|
| enter-rate >= 0.05 | 0.0003 | yes |
| enter-rate >= 0.1 | 5.30e-08 | yes |
| enter-rate >= 0.125 | 6.02e-10 | yes |
| enter-rate >= 0.2 | 3.90e-16 | yes |

- Permutation framing (prompted vs unprompted exchangeable w.r.t. W-p90 region membership): pooled event count = 0; exact hypergeometric p = 1.0000, Monte Carlo p = 1.0000 (10000 perms, seed 20260609).
- The permutation test is DEGENERATE when no sample in either condition lies inside any W-p90 region (pooled event count 0): p = 1.0 by construction and the test has zero power. The informative quantity is the exact Clopper-Pearson upper bound.

Assumptions: Samples treated as independent Bernoulli trials; the 159 samples come from 8 models x 4 targets, so model/target clustering is ignored — with k=0 the CP bound is unaffected by clustering direction but the effective n may be smaller than the nominal n. Permutation framing assumes exchangeability of prompted and unprompted samples w.r.t. region membership under the null.

## 2. Off-manifold claim

**400/400 unprompted samples off-manifold (nearest-author W-pct > 90).**

- CP 95% two-sided [0.9908, 1.0000]; one-sided 95% lower bound 0.9925.
- The data exclude any true ON-manifold rate >= **0.7%** (one-sided alpha = 0.05).
- Exact test of H0 'off-manifold rate <= 0.90': p = 4.98e-19.

### W-percentile resolution (honest limits)

- w_percentile is an empirical mid-rank percentile against the artifact's W LOO distribution (n=78); it is NOT a parametric tail probability.
- Granularity: 1.282 percentile points per rank; largest resolvable value below 100 is 99.36.
- min observed 97.4359 => the AI distance exceeds ~76.0 of 78 W LOO values; a value of 100.0 only certifies the distance exceeds all 78 reference values, i.e. an exceedance probability <= 1/79 (~1.27%) under exchangeability, not literally zero.

Assumptions: Samples treated as independent across models and prompts (n=400 unprompted samples; 8 models); per-model clustering would widen the effective CI. The W-percentile inherits sampling noise from the finite W LOO reference sample; ranks, not tail probabilities, are the claim.

## 3. Model proximity medians

Median unprompted nearest-author distance with seeded percentile-bootstrap 95% CIs (10000 resamples):

| model | n | median | bootstrap 95% CI |
|---|---|---|---|
| gpt-5 | 50 | 1.3197 | [1.2939, 1.3571] |
| gpt-5-mini | 50 | 1.5040 | [1.4726, 1.5364] |
| claude-fable-5 | 50 | 1.5502 | [1.5287, 1.5866] |
| claude-sonnet-4-6 | 50 | 1.6324 | [1.6063, 1.6673] |
| claude-opus-4-8 | 50 | 1.6360 | [1.6071, 1.6678] |
| claude-haiku-4-5 | 50 | 1.6369 | [1.6168, 1.7035] |
| qwen3.6:35b | 50 | 1.7286 | [1.7057, 1.7547] |
| gemma4:26b | 50 | 1.7706 | [1.7380, 1.7916] |

Pairwise exact Mann-Whitney U, Holm-Bonferroni across 28 pairs:

| pair | medians | U | p raw | p Holm | sig (0.05) |
|---|---|---|---|---|---|
| gpt-5 vs gemma4:26b | 1.320 vs 1.771 | 0 | 1.98e-29 | 5.55e-28 | YES |
| gpt-5 vs claude-opus-4-8 | 1.320 vs 1.636 | 1 | 3.96e-29 | 1.07e-27 | YES |
| gpt-5 vs claude-haiku-4-5 | 1.320 vs 1.637 | 3 | 1.39e-28 | 3.61e-27 | YES |
| gpt-5 vs claude-sonnet-4-6 | 1.320 vs 1.632 | 4 | 2.38e-28 | 5.95e-27 | YES |
| gpt-5 vs claude-fable-5 | 1.320 vs 1.550 | 8 | 1.33e-27 | 3.19e-26 | YES |
| gpt-5 vs qwen3.6:35b | 1.320 vs 1.729 | 16 | 1.81e-26 | 4.17e-25 | YES |
| gpt-5-mini vs gemma4:26b | 1.504 vs 1.771 | 27 | 2.92e-25 | 6.43e-24 | YES |
| claude-fable-5 vs gemma4:26b | 1.550 vs 1.771 | 85 | 4.78e-21 | 1.00e-19 | YES |
| gpt-5 vs gpt-5-mini | 1.320 vs 1.504 | 91 | 1.05e-20 | 2.09e-19 | YES |
| gpt-5-mini vs qwen3.6:35b | 1.504 vs 1.729 | 233 | 1.15e-14 | 2.18e-13 | YES |
| gpt-5-mini vs claude-haiku-4-5 | 1.504 vs 1.637 | 315 | 3.72e-12 | 6.70e-11 | YES |
| gpt-5-mini vs claude-opus-4-8 | 1.504 vs 1.636 | 327 | 7.95e-12 | 1.35e-10 | YES |
| gpt-5-mini vs claude-sonnet-4-6 | 1.504 vs 1.632 | 342 | 2.00e-11 | 3.20e-10 | YES |
| claude-fable-5 vs qwen3.6:35b | 1.550 vs 1.729 | 372 | 1.16e-10 | 1.74e-09 | YES |
| claude-opus-4-8 vs gemma4:26b | 1.636 vs 1.771 | 425 | 2.02e-09 | 2.83e-08 | YES |
| claude-sonnet-4-6 vs gemma4:26b | 1.632 vs 1.771 | 433 | 3.03e-09 | 3.94e-08 | YES |
| claude-haiku-4-5 vs gemma4:26b | 1.637 vs 1.771 | 581 | 2.00e-06 | 2.40e-05 | YES |
| claude-fable-5 vs claude-haiku-4-5 | 1.550 vs 1.637 | 587 | 2.51e-06 | 2.76e-05 | YES |
| claude-fable-5 vs claude-opus-4-8 | 1.550 vs 1.636 | 607 | 5.25e-06 | 5.25e-05 | YES |
| claude-fable-5 vs claude-sonnet-4-6 | 1.550 vs 1.632 | 610 | 5.85e-06 | 5.26e-05 | YES |
| claude-sonnet-4-6 vs qwen3.6:35b | 1.632 vs 1.729 | 746 | 0.0004 | 0.0034 | YES |
| gpt-5-mini vs claude-fable-5 | 1.504 vs 1.550 | 751 | 0.0005 | 0.0034 | YES |
| claude-opus-4-8 vs qwen3.6:35b | 1.636 vs 1.729 | 765 | 0.0007 | 0.0043 | YES |
| claude-haiku-4-5 vs qwen3.6:35b | 1.637 vs 1.729 | 892 | 0.0133 | 0.0664 | no |
| qwen3.6:35b vs gemma4:26b | 1.729 vs 1.771 | 981 | 0.0640 | 0.2560 | no |
| claude-sonnet-4-6 vs claude-haiku-4-5 | 1.632 vs 1.637 | 1131 | 0.4156 | 1.0000 | no |
| claude-opus-4-8 vs claude-haiku-4-5 | 1.636 vs 1.637 | 1158 | 0.5298 | 1.0000 | no |
| claude-sonnet-4-6 vs claude-opus-4-8 | 1.632 vs 1.636 | 1226 | 0.8719 | 1.0000 | no |

- Smallest achievable exact two-sided p at these group sizes: 1.98e-29.
- Pairs NOT significant after Holm cannot be ordered from these data; PRIMARY_ARTIFACT.md's 'intra-family order unresolved' note is the supported reading.

Assumptions: Exact Mann-Whitney U assumes independent samples within and between groups (prompts are shared across models, which induces positive correlation across groups; the test ignores this). At n per group = [50], the smallest achievable two-sided exact p is 0.00000. Bootstrap median CIs at n=6 are coarse (only 462 distinct resamples exist); treat them as descriptive ranges.

## 4. Approach claim (nearest-is-target)

**63/159 style-prompted samples have nearest_author == style_target.**

- Rate 63/159 = 0.396; CP 95% [0.3196, 0.4767].
- Design null (uniform over anchors): p0 = 0.0667, one-sided p = 1.80e-32.
- Empirical null (unprompted nearest-author distribution x design target multiset): p0 = 0.1106, one-sided p = 1.35e-20.

Assumptions: Binomial tests treat the 159 samples as independent; they share models and prompts (clustering ignored). The empirical null is the stronger (more conservative) one: it credits the prompted condition only for matches beyond what the models' baseline nearest-author preferences already produce. Targets that never appear as unprompted nearest authors (e.g. mccarthy-cormac) contribute 0 to the empirical p0, so prompted matches on those targets are pure signal under this null.

## 5. Manuscript AI-closer chapters

Manuscript trajectory not provided; section skipped.

## 6. Claim registry with Holm-Bonferroni adjustment

Holm-Bonferroni applied across the full confirmatory family (33 tests: 3 headline claims + 28 model pairs). The manuscript row is descriptive (non-independent chapters) and is excluded from the family; its raw p-value is shown for context only.

| id | claim | estimate | 95% CI | test | p raw | p Holm | sig |
|---|---|---|---|---|---|---|---|
| C1_enter_rate | 0/159 style-prompted samples entered the target author's W-p90 region | 0/159 | [0.000, 0.023] | exact binomial, H0: enter-rate >= 0.10 (one-sided) | 5.30e-08 | 7.42e-07 | YES |
| C1b_enter_rate_exemplar | 0/159 exemplar (few-shot) samples entered the target author's W-p90 region | 0/159 | [0.000, 0.023] | exact binomial, H0: enter-rate >= 0.10 (one-sided) | 5.30e-08 | 7.42e-07 | YES |
| C1c_enter_rate_combined | 0/318 styled (style-prompted + exemplar) samples entered the target author's W-p90 region | 0/318 | [0.000, 0.012] | exact binomial, H0: enter-rate >= 0.10 (one-sided) | 2.81e-15 | 6.19e-14 | YES |
| C2_off_manifold | 400/400 unprompted samples off-manifold (nearest-author W-pct > 90) | 400/400 | [0.991, 1.000] | exact binomial, H0: off-manifold rate <= 0.90 (one-sided) | 4.98e-19 | 1.14e-17 | YES |
| C3_approach | 63/159 style-prompted samples have nearest_author == style_target | 63/159 | [0.320, 0.477] | exact binomial vs empirical null p0=0.1106 (one-sided greater) | 1.35e-20 | 3.25e-19 | YES |
| C4_order_gpt-5__vs__gpt-5-mini | median ordering: gpt-5 vs gpt-5-mini | 1.320 vs 1.504 | — | exact Mann-Whitney U (two-sided) | 1.05e-20 | 2.61e-19 | YES |
| C4_order_gpt-5__vs__claude-fable-5 | median ordering: gpt-5 vs claude-fable-5 | 1.320 vs 1.550 | — | exact Mann-Whitney U (two-sided) | 1.33e-27 | 3.85e-26 | YES |
| C4_order_gpt-5__vs__claude-sonnet-4-6 | median ordering: gpt-5 vs claude-sonnet-4-6 | 1.320 vs 1.632 | — | exact Mann-Whitney U (two-sided) | 2.38e-28 | 7.14e-27 | YES |
| C4_order_gpt-5__vs__claude-opus-4-8 | median ordering: gpt-5 vs claude-opus-4-8 | 1.320 vs 1.636 | — | exact Mann-Whitney U (two-sided) | 3.96e-29 | 1.27e-27 | YES |
| C4_order_gpt-5__vs__claude-haiku-4-5 | median ordering: gpt-5 vs claude-haiku-4-5 | 1.320 vs 1.637 | — | exact Mann-Whitney U (two-sided) | 1.39e-28 | 4.30e-27 | YES |
| C4_order_gpt-5__vs__qwen3.6:35b | median ordering: gpt-5 vs qwen3.6:35b | 1.320 vs 1.729 | — | exact Mann-Whitney U (two-sided) | 1.81e-26 | 5.08e-25 | YES |
| C4_order_gpt-5__vs__gemma4:26b | median ordering: gpt-5 vs gemma4:26b | 1.320 vs 1.771 | — | exact Mann-Whitney U (two-sided) | 1.98e-29 | 6.54e-28 | YES |
| C4_order_gpt-5-mini__vs__claude-fable-5 | median ordering: gpt-5-mini vs claude-fable-5 | 1.504 vs 1.550 | — | exact Mann-Whitney U (two-sided) | 0.0005 | 0.0034 | YES |
| C4_order_gpt-5-mini__vs__claude-sonnet-4-6 | median ordering: gpt-5-mini vs claude-sonnet-4-6 | 1.504 vs 1.632 | — | exact Mann-Whitney U (two-sided) | 2.00e-11 | 3.60e-10 | YES |
| C4_order_gpt-5-mini__vs__claude-opus-4-8 | median ordering: gpt-5-mini vs claude-opus-4-8 | 1.504 vs 1.636 | — | exact Mann-Whitney U (two-sided) | 7.95e-12 | 1.51e-10 | YES |
| C4_order_gpt-5-mini__vs__claude-haiku-4-5 | median ordering: gpt-5-mini vs claude-haiku-4-5 | 1.504 vs 1.637 | — | exact Mann-Whitney U (two-sided) | 3.72e-12 | 7.44e-11 | YES |
| C4_order_gpt-5-mini__vs__qwen3.6:35b | median ordering: gpt-5-mini vs qwen3.6:35b | 1.504 vs 1.729 | — | exact Mann-Whitney U (two-sided) | 1.15e-14 | 2.41e-13 | YES |
| C4_order_gpt-5-mini__vs__gemma4:26b | median ordering: gpt-5-mini vs gemma4:26b | 1.504 vs 1.771 | — | exact Mann-Whitney U (two-sided) | 2.92e-25 | 7.89e-24 | YES |
| C4_order_claude-fable-5__vs__claude-sonnet-4-6 | median ordering: claude-fable-5 vs claude-sonnet-4-6 | 1.550 vs 1.632 | — | exact Mann-Whitney U (two-sided) | 5.85e-06 | 5.26e-05 | YES |
| C4_order_claude-fable-5__vs__claude-opus-4-8 | median ordering: claude-fable-5 vs claude-opus-4-8 | 1.550 vs 1.636 | — | exact Mann-Whitney U (two-sided) | 5.25e-06 | 5.25e-05 | YES |
| C4_order_claude-fable-5__vs__claude-haiku-4-5 | median ordering: claude-fable-5 vs claude-haiku-4-5 | 1.550 vs 1.637 | — | exact Mann-Whitney U (two-sided) | 2.51e-06 | 2.76e-05 | YES |
| C4_order_claude-fable-5__vs__qwen3.6:35b | median ordering: claude-fable-5 vs qwen3.6:35b | 1.550 vs 1.729 | — | exact Mann-Whitney U (two-sided) | 1.16e-10 | 1.97e-09 | YES |
| C4_order_claude-fable-5__vs__gemma4:26b | median ordering: claude-fable-5 vs gemma4:26b | 1.550 vs 1.771 | — | exact Mann-Whitney U (two-sided) | 4.78e-21 | 1.24e-19 | YES |
| C4_order_claude-sonnet-4-6__vs__claude-opus-4-8 | median ordering: claude-sonnet-4-6 vs claude-opus-4-8 | 1.632 vs 1.636 | — | exact Mann-Whitney U (two-sided) | 0.8719 | 1.0000 | no |
| C4_order_claude-sonnet-4-6__vs__claude-haiku-4-5 | median ordering: claude-sonnet-4-6 vs claude-haiku-4-5 | 1.632 vs 1.637 | — | exact Mann-Whitney U (two-sided) | 0.4156 | 1.0000 | no |
| C4_order_claude-sonnet-4-6__vs__qwen3.6:35b | median ordering: claude-sonnet-4-6 vs qwen3.6:35b | 1.632 vs 1.729 | — | exact Mann-Whitney U (two-sided) | 0.0004 | 0.0034 | YES |
| C4_order_claude-sonnet-4-6__vs__gemma4:26b | median ordering: claude-sonnet-4-6 vs gemma4:26b | 1.632 vs 1.771 | — | exact Mann-Whitney U (two-sided) | 3.03e-09 | 4.55e-08 | YES |
| C4_order_claude-opus-4-8__vs__claude-haiku-4-5 | median ordering: claude-opus-4-8 vs claude-haiku-4-5 | 1.636 vs 1.637 | — | exact Mann-Whitney U (two-sided) | 0.5298 | 1.0000 | no |
| C4_order_claude-opus-4-8__vs__qwen3.6:35b | median ordering: claude-opus-4-8 vs qwen3.6:35b | 1.636 vs 1.729 | — | exact Mann-Whitney U (two-sided) | 0.0007 | 0.0043 | YES |
| C4_order_claude-opus-4-8__vs__gemma4:26b | median ordering: claude-opus-4-8 vs gemma4:26b | 1.636 vs 1.771 | — | exact Mann-Whitney U (two-sided) | 2.02e-09 | 3.23e-08 | YES |
| C4_order_claude-haiku-4-5__vs__qwen3.6:35b | median ordering: claude-haiku-4-5 vs qwen3.6:35b | 1.637 vs 1.729 | — | exact Mann-Whitney U (two-sided) | 0.0133 | 0.0664 | no |
| C4_order_claude-haiku-4-5__vs__gemma4:26b | median ordering: claude-haiku-4-5 vs gemma4:26b | 1.637 vs 1.771 | — | exact Mann-Whitney U (two-sided) | 2.00e-06 | 2.40e-05 | YES |
| C4_order_qwen3.6:35b__vs__gemma4:26b | median ordering: qwen3.6:35b vs gemma4:26b | 1.729 vs 1.771 | — | exact Mann-Whitney U (two-sided) | 0.0640 | 0.2560 | no |

---
Generated by tools/tier1_statistics.py — re-runnable on the scaled corpus via --e4-results / --trajectory / --artifact; all n's are auto-detected from the inputs.
