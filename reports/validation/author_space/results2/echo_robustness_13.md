# Echo-excluded robustness, extended to all 13 echo-bearing samples

*Added 2026-08-06 by the forensic code and data review. This extends
`echo_robustness.md`, which removed the **4** samples above the audit's
≥19-word run threshold, to the **13** samples that carry any verbatim run of
≥12 words — the count a skeptic recomputes at the lower threshold. It is the
stronger version of the same check, and it holds.*

**Why the count depends on a threshold.** "4" and "13" are the same audit at
two run lengths: 4 samples carry a run of ≥19 words, 13 carry a run of ≥12
words, and the longest run anywhere in the corpus is 30 words. Neither number
is more correct; the disclosure is that the count is threshold-dependent, so
this file removes at the more demanding threshold. Full inventory of the 13,
with run lengths and file paths, is in `DATA_LICENSES.md` (file-level
exception ledger).

**Method.** Recompute the pooled §5.2 / §5.4 / §5.5 / §5.6 rates from the
frozen Results 2.0 placements with the echo-bearing samples removed, and
compare each recomputed point estimate against its published interval. This
is valid because the LM-envelope thresholds derive from the **human** held-out
windows, not from the AI corpus: removing AI samples cannot change any
remaining sample's entry status. Only pool composition changes.

**Calibration first.** Before any exclusion, the unmodified corpus was re-run
through the same code path and checked against the frozen published values —
**10 of 10 checks matched exactly** (styled n and entries under both
vocabularies, completion k/n pooled and model-matched, and both sign tests).
A robustness result computed by a pipeline that cannot first reproduce the
baseline is worthless; this one can.

**Where the 13 sit.** 12 of 13 are completion samples and 1 is styled
(exemplar), so the styled-side results are almost entirely untouched. 9 of
the 13 sit in a primary (floor-compliant) analysis pool; the other 4 were
already excluded by the published floor discipline before any of this.

---

## Headline

**Every published rate stays within its published interval, and the sign test
is unchanged (5/5, exact one-sided p = 0.031).** The largest movement anywhere
is the pooled fw-only completion rate, 31.40% → 29.49%, against a published
CP interval of [21.8, 42.3]%.

| Analysis | Published | Minus 4 | Minus 13 | Published interval | Within? |
|---|---|---|---|---|---|
| §5.2 styled entry, fw-only | 72/236 = 30.51% | 71/235 = 30.21% | 71/235 = 30.21% | CP [24.7, 36.8]% | yes |
| §5.2 styled entry, full | 48/236 = 20.34% | 48/235 = 20.43% | 48/235 = 20.43% | CP [15.4, 26.0]% | yes |
| §5.2 increment, fw-only | +19.76 pp | +19.47 pp | +19.47 pp | cluster-boot [+4.32, +33.53] pp | yes |
| §5.2 increment, full | +3.81 pp | +3.90 pp | +3.90 pp | cluster-boot [−12.57, +18.63] pp | yes |
| §5.4 pooled completion, fw-only | 27/86 = 31.40% | 26/83 = 31.33% | 23/78 = **29.49%** | CP [21.8, 42.3]% | yes |
| §5.4 pooled completion, full | 18/86 = 20.93% | 17/83 = 20.48% | 14/78 = 17.95% | CP [12.9, 31.0]% | yes |
| §5.4 sign test, fw-only | 5/5, p = 0.031 | 5/5, p = 0.031 | **5/5, p = 0.031** | — | unchanged |
| §5.4 sign test, full | 2/5, p = 0.813 | 2/5, p = 0.813 | 2/5, p = 0.813 | — | unchanged |
| §5.6 approach, fw-only | 69/236 = 29.24% | 69/235 = 29.36% | 69/235 = 29.36% | DEFF-adj CP [19.4, 40.7]% | yes |
| §5.6 approach, full | 122/236 = 51.69% | 121/235 = 51.49% | 121/235 = 51.49% | DEFF-adj CP [41.3, 62.0]% | yes |
| §5.5 chassis MFW movement | −0.029977 | −0.029977 | **−0.029977** | CI [−0.04755, −0.01314] | identical |

The unprompted base rates (13/121 fw-only, 20/121 full) are untouched by
construction: no echo-bearing sample is unprompted.

§5.5 is **byte-identical** across all three conditions because the chassis
analysis runs on the styled stratum, and 12 of the 13 echoes are completions,
which that analysis never included.

---

## §5.4 per-model detail, fw-only (the primary vocabulary)

The sign test asks, per model, whether completion entry exceeds styled entry.
Its verdict is a count of models, so it is robust to the pool shrinking as
long as no model flips direction. None does.

| Model | Baseline | Minus 4 | Minus 13 | Direction |
|---|---|---|---|---|
| claude-fable-5 | 10/20 = 50.0% (+14.1) | 9/18 = 50.0% (+14.1) | 6/14 = 42.9% (+7.0) | completion higher, all three |
| claude-haiku-4-5 | 0/2 = 0.0% (+0.0) | 0/2 (+0.0) | 0/2 (+0.0) | tie, all three |
| claude-opus-4-8 | 7/20 = 35.0% (+12.5) | 7/19 = 36.8% (+14.3) | 7/19 = 36.8% (+14.3) | completion higher, all three |
| claude-sonnet-4-6 | 3/20 = 15.0% (+5.6) | 3/20 (+5.6) | 3/20 (+5.6) | completion higher, all three |
| gpt-5-mini | 5/8 = 62.5% (+27.5) | 5/8 (+27.5) | 5/8 (+27.5) | completion higher, all three |
| qwen3.6:35b | 2/16 = 12.5% (+1.8) | 2/16 (+5.1) | 2/15 = 13.3% (+5.9) | completion higher, all three |
| **Sign test** | **5 higher, 0 lower, 1 tie; p = 0.031** | **5/0/1; p = 0.031** | **5/0/1; p = 0.031** | **unchanged** |

(gpt-5 is absent because it refused all completions — the composition
artifact the paper reports.)

---

## The one place the exclusion bites: the Didion completion cell

This is the boundary observation worth stating plainly rather than leaving
for someone else to find.

**Five of the 13 echoes are Didion completion samples** (runs of 13, 13, 14,
17, and 24 words — four from claude-fable-5, one from claude-opus-4-8), and
they include **every fw-only envelope entry in that cell**. Excluding them
empties it:

| Didion completion cell | Baseline | Minus 13 |
|---|---|---|
| fw-only entry @p90 | 3/24 = 12.5% | **0/19 = 0.0%** |
| full-vocabulary entry @p90 | 4/24 = 16.7% | 1/19 = 5.3% |

Read honestly: for this one target, the samples that entered the envelope
were also the samples carrying short verbatim echoes of the source novel's
opening. That is a real confound at the per-target level, and it is why the
per-target completion cells should not be read as independent evidence of
imitation skill.

It does not propagate to the pooled claim. The pooled fw-only completion rate
moves 31.40% → 29.49%, well inside its published CP interval, and the sign
test — the actual §5.4 claim — is unchanged at 5/5, p = 0.031, because the
model-level directions do not flip.

---

## Provenance

Re-run by lane G of the forensic code and data review, 2026-08-06, using the
frozen Results 2.0 placements and the same code path as the published run.
Receipt scripts and raw outputs: the review's `receipts/laneG/`
(`build_filtered_corpus.py`, `compare.py`, `comparison.txt`,
`sec54_fwonly.txt`, `echo_pool_status.txt`). The Didion cell was verified
independently against the per-target completion results under both
conditions. Cross-checked by a cross-family adversarial reviewer, which
corrected an earlier draft that claimed the pooled rates were unaffected:
they do move, they stay within interval, and that is what is stated here.
