# Controls — v0.3 Red-Team Formalization (G1/G2/G7 + claims 1/3)

- Generated: 2026-06-11T08:06:52.273417+00:00
- Window: 3000 MFW tokens; floors as in entry_report.md (same strata, same placement code path).
- Unprompted control pools: 121 floor-compliant unprompted samples on the four bound scenarios (G1); 309 floor-compliant unprompted samples on all scenarios (G7 pseudo-target analysis).
- Provenance: same artifacts as entry_results.json (see its meta).

## f1. Unprompted-entry control (G1) — the PRIMARY entry framing

Unprompted samples on the bound scenario, placed against the bound target's LM envelope @p90 — identical truncation, floor, and code path as styled entry. Styled entry is read as an INCREMENT over this base rate.

| Vocabulary | Unprompted @p90 | Styled @p90 | Increment (pp) | cluster-bootstrap 95% (pp) | excludes zero | Fisher p (naive) |
|---|---|---|---|---|---|---|
| full | 20/121 (16.5%) | 48/236 (20.3%) | +3.8 | [-12.6, +18.6] | no | 4.77e-01 |
| fwonly | 13/121 (10.7%) | 72/236 (30.5%) | +19.8 | [+4.3, +33.5] | YES | 2.17e-05 |

### Per model — full

| Model | Unprompted @p90 | Styled @p90 | Increment (pp) | Fisher two-sided p |
|---|---|---|---|---|
| claude-fable-5 | 5/20 (25.0%) | 11/39 (28.2%) | +3.2 | 1.000 |
| claude-haiku-4-5 | 0/9 (0.0%) | 1/17 (5.9%) | +5.9 | 1.000 |
| claude-opus-4-8 | 2/20 (10.0%) | 9/40 (22.5%) | +12.5 | 0.307 |
| claude-sonnet-4-6 | 3/20 (15.0%) | 6/32 (18.8%) | +3.8 | 1.000 |
| gemma4:26b | 0/1 (0.0%) | 0/0 (—) | — | — |
| gpt-5 | 6/20 (30.0%) | 16/40 (40.0%) | +10.0 | 0.573 |
| gpt-5-mini | 3/20 (15.0%) | 5/40 (12.5%) | -2.5 | 1.000 |
| qwen3.6:35b | 1/11 (9.1%) | 0/28 (0.0%) | -9.1 | 0.282 |

### Per target — full

| Target | LM p90 | Unprompted @p90 | Styled @p90 |
|---|---|---|---|
| didion-joan | 1.490 | 0/33 (0.0%) | 2/66 (3.0%) |
| mccarthy-cormac | 1.715 | 19/29 (65.5%) | 41/56 (73.2%) |
| morrison-toni | 1.510 | 1/29 (3.4%) | 3/58 (5.2%) |
| ondaatje-michael | 1.409 | 0/30 (0.0%) | 2/56 (3.6%) |

### Per model — fwonly

| Model | Unprompted @p90 | Styled @p90 | Increment (pp) | Fisher two-sided p |
|---|---|---|---|---|
| claude-fable-5 | 0/20 (0.0%) | 14/39 (35.9%) | +35.9 | 0.001 |
| claude-haiku-4-5 | 0/9 (0.0%) | 0/17 (0.0%) | +0.0 | 1.000 |
| claude-opus-4-8 | 0/20 (0.0%) | 9/40 (22.5%) | +22.5 | 0.023 |
| claude-sonnet-4-6 | 0/20 (0.0%) | 3/32 (9.4%) | +9.4 | 0.276 |
| gemma4:26b | 0/1 (0.0%) | 0/0 (—) | — | — |
| gpt-5 | 9/20 (45.0%) | 29/40 (72.5%) | +27.5 | 0.049 |
| gpt-5-mini | 2/20 (10.0%) | 14/40 (35.0%) | +25.0 | 0.062 |
| qwen3.6:35b | 2/11 (18.2%) | 3/28 (10.7%) | -7.5 | 0.609 |

### Per target — fwonly

| Target | LM p90 | Unprompted @p90 | Styled @p90 |
|---|---|---|---|
| didion-joan | 1.239 | 0/33 (0.0%) | 9/66 (13.6%) |
| mccarthy-cormac | 1.553 | 9/29 (31.0%) | 43/56 (76.8%) |
| morrison-toni | 1.336 | 3/29 (10.3%) | 14/58 (24.1%) |
| ondaatje-michael | 1.227 | 1/30 (3.3%) | 6/56 (10.7%) |

Reading: at full vocabulary the imitation increment is small and per-model nonsignificant — full-vocab 'entry' is mostly envelope porosity to AI house style on a deliberately adjacent scenario. The fw-only increment is large and significant; the fw-only framing is primary. Any styled rate should be quoted next to its model's unprompted base (e.g. the best styled model's base).

## f2. Model-matched completion vs styled entry (G2)

- Source: `reports/validation/results2/completion_results.json` (completion run 2026-06-11T08:06:40.225669+00:00).
- Matched pools only: models with >= 1 compliant completion AND >= 1 primary styled sample. Pooled unmatched comparisons are composition artifacts (the best styled model refused all completions).

### Vocabulary: fwonly (PRIMARY)

| Model | Completion @p90 | Styled @p90 | Diff (pp) | Direction |
|---|---|---|---|---|
| claude-fable-5 | 10/20 (50.0%) | 14/39 (35.9%) | +14.1 | completion_higher |
| claude-haiku-4-5 | 0/2 (0.0%) | 0/17 (0.0%) | +0.0 | tie |
| claude-opus-4-8 | 7/20 (35.0%) | 9/40 (22.5%) | +12.5 | completion_higher |
| claude-sonnet-4-6 | 3/20 (15.0%) | 3/32 (9.4%) | +5.6 | completion_higher |
| gpt-5-mini | 5/8 (62.5%) | 14/40 (35.0%) | +27.5 | completion_higher |
| qwen3.6:35b | 2/16 (12.5%) | 3/28 (10.7%) | +1.8 | completion_higher |

Excluded from matching: gpt-5 (no compliant completion); gemma4:26b (no primary styled sample).
Sign test (informative models, ties dropped): 5/5 completion-higher; exact one-sided p = 0.0312 (two-sided 0.0625); 1 tie(s) uninformative.
Pooled matched: completion 27/86 (31.4%, CP [21.8%, 42.3%]) vs styled 43/196 (21.9%, CP [16.4%, 28.4%]); diff +9.5 pp.

### Vocabulary: full (content-confounded secondary)

| Model | Completion @p90 | Styled @p90 | Diff (pp) | Direction |
|---|---|---|---|---|
| claude-fable-5 | 10/20 (50.0%) | 11/39 (28.2%) | +21.8 | completion_higher |
| claude-haiku-4-5 | 0/2 (0.0%) | 1/17 (5.9%) | -5.9 | styled_higher |
| claude-opus-4-8 | 3/20 (15.0%) | 9/40 (22.5%) | -7.5 | styled_higher |
| claude-sonnet-4-6 | 5/20 (25.0%) | 6/32 (18.8%) | +6.2 | completion_higher |
| gpt-5-mini | 0/8 (0.0%) | 5/40 (12.5%) | -12.5 | styled_higher |
| qwen3.6:35b | 0/16 (0.0%) | 0/28 (0.0%) | +0.0 | tie |

Excluded from matching: gpt-5 (no compliant completion); gemma4:26b (no primary styled sample).
Sign test (informative models, ties dropped): 2/5 completion-higher; exact one-sided p = 0.8125 (two-sided 1.0000); 1 tie(s) uninformative.
Pooled matched: completion 18/86 (20.9%, CP [12.9%, 31.0%]) vs styled 32/196 (16.3%, CP [11.4%, 22.3%]); diff +4.6 pp.

Reading: model-matched, completion enters MORE than named-style prompting for every informative model under the primary vocabulary; the pooled 'parity' exists only because the model best at styled imitation refused the completion task. Clustered intervals for the completion pool itself are in completion_results.{json,md}.

## f3. Width vs enterability, de-circularized (G7)

### (a) Model x target entry @p90 — fwonly

| Model | didion-joan | mccarthy-cormac | morrison-toni | ondaatje-michael |
|---|---|---|---|---|
| claude-fable-5 | 3/9 | 10/10 | 1/10 | 0/10 |
| claude-haiku-4-5 | 0/8 | 0/3 | 0/1 | 0/5 |
| claude-opus-4-8 | 0/10 | 7/10 | 2/10 | 0/10 |
| claude-sonnet-4-6 | 0/10 | 3/6 | 0/10 | 0/6 |
| gpt-5 | 5/10 | 10/10 | 9/10 | 5/10 |
| gpt-5-mini | 1/10 | 10/10 | 2/10 | 1/10 |
| qwen3.6:35b | 0/9 | 3/7 | 0/7 | 0/5 |

### (a) Model x target entry @p90 — full

| Model | didion-joan | mccarthy-cormac | morrison-toni | ondaatje-michael |
|---|---|---|---|---|
| claude-fable-5 | 1/9 | 10/10 | 0/10 | 0/10 |
| claude-haiku-4-5 | 0/8 | 1/3 | 0/1 | 0/5 |
| claude-opus-4-8 | 0/10 | 9/10 | 0/10 | 0/10 |
| claude-sonnet-4-6 | 0/10 | 6/6 | 0/10 | 0/6 |
| gpt-5 | 1/10 | 10/10 | 3/10 | 2/10 |
| gpt-5-mini | 0/10 | 5/10 | 0/10 | 0/10 |
| qwen3.6:35b | 0/9 | 0/7 | 0/7 | 0/5 |

### (b) All shelf authors as pseudo-targets (unprompted porosity vs width) — fwonly

n = 309 unprompted samples x 15 authors. Pearson r(width, entry rate) = +0.844 [+0.585, +0.947] (Fisher z); Spearman rho = +0.685 (p = 0.0049).

| Author | LM p90 | Unprompted entered@p90 | Rate | median distance | imitation target |
|---|---|---|---|---|---|
| murakami-haruki | 1.738 | 244/309 | 79.0% | 1.619 |  |
| foster_wallace-david | 1.689 | 235/309 | 76.1% | 1.583 |  |
| ishiguro-kazuo | 1.575 | 22/309 | 7.1% | 1.802 |  |
| mccarthy-cormac | 1.553 | 151/309 | 48.9% | 1.560 | YES |
| pynchon-thomas | 1.498 | 57/309 | 18.4% | 1.619 |  |
| robinson-marilynne | 1.497 | 76/309 | 24.6% | 1.593 |  |
| tokarczuk-olga | 1.391 | 59/309 | 19.1% | 1.532 |  |
| saunders-george | 1.373 | 22/309 | 7.1% | 1.615 |  |
| morrison-toni | 1.336 | 27/309 | 8.7% | 1.518 | YES |
| delillo-don | 1.287 | 24/309 | 7.8% | 1.496 |  |
| whitehead-colson | 1.243 | 30/309 | 9.7% | 1.441 |  |
| didion-joan | 1.239 | 5/309 | 1.6% | 1.462 | YES |
| sebald-w_g | 1.236 | 0/309 | 0.0% | 1.573 |  |
| ondaatje-michael | 1.227 | 9/309 | 2.9% | 1.470 | YES |
| proulx-annie | 1.197 | 31/309 | 10.0% | 1.398 |  |

### (b) All shelf authors as pseudo-targets (unprompted porosity vs width) — full

n = 309 unprompted samples x 15 authors. Pearson r(width, entry rate) = +0.729 [+0.345, +0.904] (Fisher z); Spearman rho = +0.749 (p = 0.0013).

| Author | LM p90 | Unprompted entered@p90 | Rate | median distance | imitation target |
|---|---|---|---|---|---|
| robinson-marilynne | 1.731 | 74/309 | 23.9% | 1.810 |  |
| mccarthy-cormac | 1.715 | 91/309 | 29.4% | 1.767 | YES |
| ishiguro-kazuo | 1.715 | 2/309 | 0.6% | 1.963 |  |
| murakami-haruki | 1.627 | 36/309 | 11.7% | 1.778 |  |
| foster_wallace-david | 1.600 | 26/309 | 8.4% | 1.768 |  |
| saunders-george | 1.535 | 3/309 | 1.0% | 1.848 |  |
| morrison-toni | 1.510 | 7/309 | 2.3% | 1.726 | YES |
| didion-joan | 1.490 | 1/309 | 0.3% | 1.738 | YES |
| delillo-don | 1.458 | 3/309 | 1.0% | 1.713 |  |
| whitehead-colson | 1.454 | 2/309 | 0.6% | 1.713 |  |
| tokarczuk-olga | 1.452 | 3/309 | 1.0% | 1.685 |  |
| proulx-annie | 1.437 | 6/309 | 1.9% | 1.653 |  |
| pynchon-thomas | 1.431 | 0/309 | 0.0% | 1.774 |  |
| ondaatje-michael | 1.409 | 1/309 | 0.3% | 1.661 | YES |
| sebald-w_g | 1.294 | 0/309 | 0.0% | 1.753 |  |

### (c) Width-independent restatement — fwonly

| Target | styled median distance | LM p90 width | median's percentile in target envelope |
|---|---|---|---|
| didion-joan | 1.419 | 1.239 | p100.0 |
| mccarthy-cormac | 1.422 | 1.553 | p82.5 |
| morrison-toni | 1.477 | 1.336 | p98.5 |
| ondaatje-michael | 1.377 | 1.227 | p100.0 |

Spread of styled medians 0.101 vs spread of widths 0.326. (entry = P(distance <= width-quantile) is mechanically increasing in width at fixed distance; the non-circular content is how flat the styled distance distributions are across targets vs how much the widths vary)

### (c) Width-independent restatement — full

| Target | styled median distance | LM p90 width | median's percentile in target envelope |
|---|---|---|---|
| didion-joan | 1.732 | 1.490 | p100.0 |
| mccarthy-cormac | 1.591 | 1.715 | p76.9 |
| morrison-toni | 1.788 | 1.510 | p98.0 |
| ondaatje-michael | 1.668 | 1.409 | p100.0 |

Spread of styled medians 0.196 vs spread of widths 0.307. (entry = P(distance <= width-quantile) is mechanically increasing in width at fixed distance; the non-circular content is how flat the styled distance distributions are across targets vs how much the widths vary)

## f4. E8 yardstick

See `e8_yardstick.md` (same data also under `e8_yardstick` in controls_results.json). No gate changes; reporting data only.
