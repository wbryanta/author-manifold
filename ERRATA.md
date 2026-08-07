# Errata

Corrections to material previously published in this repository. Entries are
additive: nothing is silently rewritten, and each entry states what was wrong,
what changed, and whether any paper result depends on it.

---

## E-1 (2026-08-06) — the `C_llr` metric was not C_llr; removed

**What was published.** `src/author_manifold/attribution_metrics.py` exported
`compute_c_llr()`, and `tools/validate_author_space.py` reported its output
in the E2 (leave-one-work-out attribution) block of every validation summary,
labelled "descriptive only; not a gate". Published values included:

| Shelf | Reported "C_llr" | Reported "min" |
|---|---|---|
| PD shelf (9 authors / 35 works) | 1.482 | 0.542 |
| Wave-2 contemporary (15 authors / 78 works) | 1.826 | 0.732 |
| Wave-2 fw-only | 1.854 | 0.751 |
| Earlier hybrid-model harness (`reports/validation/summary.md`) | 1.160 | 0.606 |

**What is wrong.** The implementation is not a log-likelihood-ratio cost. A
valid C_llr (Brümmer & du Preez 2006) is 0 for a perfect system and exactly 1
for a non-informative one, and is computed over likelihood ratios. This
implementation fed posterior-like scores in [0, 1] into the target term as if
they were likelihood ratios, while treating the same scores as posteriors in
the non-target term — two different units in one average. Measured behaviour
of the shipped function:

| System | Valid C_llr | This implementation |
|---|---|---|
| Perfect (targets 1.0, non-targets 0.0) | 0.000 | **0.500** |
| Non-informative (all scores 0.5) | 1.000 | **1.292** |

Both anchors of the scale are wrong, so the published numbers are not
interpretable on the C_llr scale and are not comparable to C_llr values
reported anywhere else in the forensic-attribution literature. In particular,
a reader comparing the published 1.482 / 1.826 / 1.854 against the standard
"1.0 = useless system" anchor would conclude the attribution system is worse
than chance. That conclusion would be an artifact of the broken scale: the
same runs report E2 leave-one-work-out top-1 accuracy of 100% (PD) and 96.2%
(wave-2), which is the result that was actually gated and actually reported in
the paper.

The defect also contradicted the repository's own test, which asserted
`0.0 <= c_llr < 1.0` on the grounds that the system beats a random one. That
bound held only on the well-separated synthetic fixture; every published shelf
value violated it.

**What changed (2026-08-06).** `compute_c_llr()` is removed rather than
reimplemented. It was descriptive only — no gate, no paper claim, and no
figure depended on it — so a correct PAV/isotonic reimplementation would add a
number the paper does not use. Removed with it: the call site in
`tools/validate_author_space.py`, the `c_llr` block in newly generated E2
results, the C_llr line in the shipped validation summaries (each replaced
with a pointer to this file), and the test asserting the bogus bound.

**Scope — what does NOT change.** No paper number, no gate, and no figure.
E1 (AUC 0.999 PD), E2 (top-1 100% PD / 96.2% wave-2), E3, and E8 are computed
independently of this function and are unaffected; all repository gates
reproduce their published values after the removal.

**Historical evidence files.** Result JSONs recorded before this date
(`reports/validation/**/e2_results.json`, `variant_comparison.json`) still
contain a `c_llr` block. Those files are the record of what those runs
computed and are deliberately left intact; the values in them should be
disregarded for the reasons above.

*Found by the forensic code and data review of 2026-08-06 (finding A-6).*
