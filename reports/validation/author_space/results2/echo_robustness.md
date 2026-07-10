# Echo-excluded robustness check (§8.14 evidence)

*2026-07-07 (verified 2026-07-10). Method: recompute the pooled §5.2/§5.4
rates from the frozen Results 2.0 per-sample placements with the four
echo-bearing samples removed, and compare each recomputed point estimate to
the published interval. Valid because the LM-envelope thresholds derive from
the human held-out windows, not the AI corpus — removing AI samples cannot
change any remaining sample's entry status; only pool composition changes.
Independently re-derived by an adversarial reviewer (own selection chain,
tokenizer-level spot checks, recomputed contrasts): no discrepancy.*

## The 4 echo-bearing samples (see `DATA_LICENSES` in the companion repository)

| # | file | condition | run length | analyses touched |
|---|---|---|---|---|
| 1 | `qwen3_6_35b/irrigation__exemplar_mccarthy-cormac__s2.txt` | exemplar (styled) | 24 words | §5.2 entry, §5.5 chassis, §5.6 approach (primary n=236) |
| 2 | `claude-fable-5/completion_ondaatje-michael__s4.txt` | completion | 30 words (a traditional song the source novel itself quotes as an epigraph) | §5.4 (matched pool) |
| 3 | `claude-opus-4-8/completion_didion-joan__s2.txt` | completion | 24 words | §5.4 (matched pool) |
| 4 | `claude-fable-5/completion_morrison-toni__s3.txt` | completion | 19 words | §5.4 (matched pool) |

Unaffected by construction (no echo sample is unprompted or paraphrase):
§5.2 unprompted base rates (13/121 fw, 20/121 full), §5.3 width correlation
(309 unprompted placements), §5.7 self-consistency (400 unprompted trials),
§5.8 folk tells (400 unprompted samples), the paraphrase battery (192).

## §5.2 / §5.5 / §5.6 — remove #1 (the only styled echo)

Sample #1 is a **full-vocabulary non-entry** by the frozen aggregate
(qwen3.6:35b full-vocab entered_p90 = 0/28 — every qwen styled sample is a
full non-entry). On the **primary function-word vocabulary it is one of
the 72 p90 entries** (per-sample verification in
`cross_target_matrix.json`), so the fw row below is resolved exactly, not
bounded: removing it gives 71/235.

| statistic | published | published CI | recomputed (−#1) | in CI? |
|---|---|---|---|---|
| styled full p90 | 48/236 = 20.34% | [15.4, 26.0]% | 48/235 = 20.43% | YES |
| styled fw p90 | 72/236 = 30.51% | [24.7, 36.8]% | 71/235 = 30.21% (exact; #1 is a fw entry) | YES |
| approach nearest-is-target | 122/236 = 51.7% | [41.3, 62.0]% (DEFF) | 121–122/235 = 51.5–51.9% | YES |
| §5.6 full distance median Δ | −0.0051 | brackets 0 | shifts <0.001 | YES |
| §5.5 chassis full MFW | −0.0070 | [−0.0233, +0.0197] | ≈−0.0048 | YES |

Removing one sample from n=236 moves any pooled rate by ≤~0.4 pp — below
the width of every published interval.

## §5.4 — remove #2, #3, #4 (completion echoes; fw-only p90)

Per-cell fw entries: fable/ondaatje 0/5, opus/didion 0/5, fable/morrison
2/5 → removals change per-model entries by at most 1, robust to which
physical sample in each cell is the echo.

| model | published completion fw | published styled fw | recomputed (−echoes) | completion > styled? |
|---|---|---|---|---|
| claude-fable-5 | 10/20 = 50.0% | 35.9% | 9–10/18 = 50.0–55.6% | YES |
| claude-opus-4-8 | 7/20 = 35.0% | 22.5% | 7/19 = 36.8% | YES |
| sonnet / gpt-5-mini / qwen | (no echoes) | — | unchanged | YES |
| haiku | 0/2 (tie) | 0% | unchanged | tie (excluded) |

Model-matched sign test unchanged: **5/5 completion-higher, exact one-sided
p = 0.031**. Pooled matched completion fw: published 27/86 = 31.4%
(CP [21.8, 42.3]); recomputed 26–27/83 = 31.3–32.5% — within CI.

## Verdict

Removing all four echo-bearing samples leaves every reported §5.2/§5.4/
§5.5/§5.6 rate within its published interval and the §5.4 sign test
unchanged; §5.3/§5.7/§5.8 and the unprompted bases are unaffected by
construction. Additional bound from the cross-target matrix re-analysis
(2026-07-10): the maximum single-sample leave-one-out shift of the paired
cross-target contrast D over all 236 styled samples is ≤ 0.36 pp —
immaterial to that verdict as well.
