# ADR-0041 — Author-Relative Measurement Space (release summary)

**Status:** Implemented; the design of record for everything in this
repository.
**Date of the original decision:** 2026-06-09.
**This document:** a release summary written 2026-08-06, faithful to the
paper's Methods (§3) and its gate/threshold/seed registry (Appendix B).

> **Why this file exists, and what it is not.** The paper cites
> `docs/adr/ADR-0041-author-relative-measurement-space.md` for the full
> design, and code in `src/` and `tools/` refers to "ADR-0041" for the
> measurement model and to "ADR-0036" for centroid hygiene. Those documents
> are internal records of the parent project: they are written in terms of a
> private personal corpus and a private manuscript, neither of which is part
> of this research release (see README, "What's NOT in the box"). Rather than
> ship those documents or leave the citations dangling, this file states the
> decisions they record, in the terms the paper uses. **The paper is
> authoritative**; where this summary is thinner, read paper §3 and
> Appendix B. Nothing here is a new claim, and no number originates here.

---

## Context and decision

Voice distance had been measured from a single privileged origin centroid.
An origin-relative distance answers "how far from this one reference?", which
cannot say whether the distance is large *for this author* — the comparator
is missing.

**The decision: measure author-relatively.** Calibrate the space on a shelf
of known authors measured relative to *each other*, persist the empirical
within-author (W) and between-author (B) distance distributions, and report
every placement as a percentile of those distributions. "Distance to
`austen-jane` is at p38 of within-author variation" is then meaningful with
no reference author at all.

## 1. Shelf construction (paper §3.2)

The space is calibrated on a manifest-driven shelf of published novelists.
Every work carries form tags, body-trim fidelity status, and fiction-centroid
membership; works flagged `requires_manual_trim` are excluded, and only
fiction enters author centroids. These are the centroid-hygiene rules the
code attributes to ADR-0036 — in this release they are visible as
`FICTION_FORMS`, `ACCEPTED_FIDELITY`, and `EXCLUDED_SLUGS` in
`src/author_manifold/author_space.py`, and as the fidelity verdicts and body
offsets in `data/pd_manifest.yaml`.

Two shelves ship here:

- **Contemporary (wave 2):** 15 novelists, 78 in-copyright works — the
  paper's frozen primary. Wave 2 deliberately added four stress-test authors
  (two translated, one mixed-translator, one mixed-form) under a
  non-degrading adoption rule (E5). Derived artifacts ship; the texts do not.
- **Public domain:** 9 authors, 35 pre-1930 novels — the fully redistributable
  replication shelf, texts and all (`data/pd_shelf/`).

Translator substructure is retained as descriptive metadata only; the
translator-effect analysis was attempted and found underpowered, so no
translator claim is made.

## 2. Features and distance (paper §3.3, §3.6)

Two feature families per work:

1. **D18** — 18 interpretable scalar stylometric dimensions
   (`DIMENSION_SET_V1`). Length-dependent dimensions (TTR, vocabulary
   richness, repetition ratio, sentiment) are *retained* here rather than
   dropped: pooled-shelf normalization plus W/B calibration measures them
   against how much they vary within versus between authors, instead of
   against a foreign centroid.
2. **MFW block** — relative frequencies of the top-300 most frequent shelf
   words, z-scored against shelf-wide dispersion; distance is Burrows's Delta
   (mean |Δz|). See `MFWBlock` for the exact construction.

A **function-words-only variant** restricts the candidate vocabulary to a
closed-class list *before* top-N selection, so the measurement vocabulary
carries no lexical-content signal. It exists because 140 of the unfiltered
top-300 words are open-class, which makes the topic-confound worry legitimate
on its face. Both vocabularies are reported side by side for every entry and
approach claim, with **function-words-only as primary**.

**The capacity ceiling, and the honest history of the instrument change.**
D18 was this ADR's original instrument. All 18 dimensions are individually
valid (each exceeds its permutation-null p99), yet collectively they failed
all four E1/E2 identity gates. The MFW Delta block was added and evaluated
the same session, and `mfw_delta` was selected under a stated rule (simplest
variant passing all four gates wins unless a blend clearly beats it). This
was **a dated methodology change after a gate failure, not a pre-specified
design**, and the variant-selection rule's first committed appearance is
contemporaneous with the variant results — a selection heuristic, not a
pre-commitment. The resulting division of labor is load-bearing downstream:
**MFW Delta carries identity; the interpretable dimensions carry
interpretation.**

Distance variants in the code: `d18`, `d18_weighted`, `mfw_delta` (selected),
and `combined` (α-blended, with a median-ratio scale factor so both
components contribute on the D18 scale before weighting).

## 3. Normalization, calibration, percentile semantics (paper §3.4)

Dimensions are standardized by **shelf-wide (pooled) dispersion**, not by
each author's own small-sample standard deviation. Distances are symmetric.
The artifact persists two full-novel calibration distributions with quantiles
and seeded bootstrap CIs: **W** (within-author, leave-one-out work→centroid
and within-author work pairs) and **B** (between-author).

**Scope condition:** these distributions are valid comparators *only for
novel-scale texts*. Delta distances inflate strongly at window scale, so
every window-scale entry claim is made against the length-matched envelopes
of §5 below, never against the full-novel W table.

## 4. Validation gates E1–E8 (paper §3.5)

No placement claim is trusted until every gate is run on the shelf, its
result recorded, and every failure explicitly adjudicated.

| Exp | Question | Gate |
|---|---|---|
| E1 | Within- vs between-author separation | pooled AUC ≥ 0.90; silhouette > 0 for ≥ 80% of authors |
| E2 | Leave-one-work-out attribution | top-1 ≥ 70%; top-3 ≥ 85% |
| E3 | Per-dimension discriminative validity | ≥ 6 dimensions above permutation-null p99 |
| E4 | AI long-form placement | placement protocol gates |
| E5 | Translator / mixed-form stress test | adopt wave 2 only if gates non-degrading |
| E6 | Window-length sensitivity | documented; no pass/fail |
| E7 | Clustering-methodology negative control | beat noise-level silhouette *with* coherent clusters |
| E8 | **Same-author positive control** | per-author binomial 95% CI contains 0.90 **OR** rate ≥ 0.80 |

Negative results are retained rather than patched. **E7 does not validate**
(the silhouette bar is met but the recovered split is a
narration-versus-dialogue axis uncorrelated with the author's 45-year arc);
its binding consequence — no register clustering downstream — was adopted.
**E8's strict verdict is FAIL** on 3 of 4 shelf/vocabulary combinations, and
is reported as FAIL.

Run them with `tools/validate_author_space.py` (E1–E3) and
`tools/validate_lm_envelopes.py` (E8).

## 5. Length-matched envelopes and E8 (paper §3.7, §3.9)

The paper's first entry criterion was calibrated at full-novel scale and
applied at window scale, where Delta inflation made it unsatisfiable even by
the target authors' own prose. That criterion is **retracted**; the fix is
the methodological core of the paper.

**The envelope.** Each work is cut into 3,000-MFW-token windows; each
window's Delta distance to its own author's centroid is computed
**leave-one-WORK-out** (a window's own work never contributes to the centroid
it is measured against — otherwise the comparison is circular); the envelope
is the distribution of those distances, with p50/p90/p95/p99 persisted per
author. **Entry at level p** = sample distance to the target ≤ the target's
LM p-quantile, with samples truncated to the window length first so the
comparison is scale-valid.

**Two length floors** are enforced in every analysis: a **hard floor of 1,500
MFW tokens** (below it, a sample is excluded from every claim) and a
**practice floor of 3,000 MFW tokens** (defining the primary stratum).
Samples between the floors are reported separately and license no headline
claim.

**E8 as a permanent positive control.** A criterion the true author cannot
satisfy is not a criterion. Each work's held-out windows are tested against
the p90 envelope of the *other* works' windows. The 0.80-OR floor is a
post-hoc operating choice specified contemporaneously with the results, so it
is **not allowed to adjudicate**: the gate verdict is reported strictly, and
it is FAIL. Because held-out same-author windows systematically under-enter
their own envelopes by 2–6 points, the **observed self-entry rate (84–88%),
not the nominal 90th percentile, is the yardstick** every entry rate in the
paper is read against.

## 6. What this design does not claim

- **Not preregistration.** Engineering discipline and full public
  reproducibility are claimed; formal preregistration is not, and there is no
  external registry record. Two rules — the distance-variant selection rule
  and E8's 0.80-OR floor — were specified contemporaneously with the results
  they apply to, and the retired v0.2 Holm family was expanded after results
  were known. Appendix B of the paper is the authoritative provenance record.
- **Not an AI detector.** The instrument answers a calibrated authorship
  question ("does this text sit inside this author's measured manifold?"),
  not "was this written by AI?".

## Where this lives in the code

| Concept | Implementation |
|---|---|
| The space, W/B calibration, placement | `AuthorRelativeSpace` (`src/author_manifold/author_space.py`) |
| MFW Delta block, fw-only filter | `MFWBlock`, `STYLOMETRIC_FUNCTION_WORDS` |
| Length-matched envelopes, E8 | `LengthMatchedEnvelopes`, `AuthorLMEnvelope` |
| Cluster-robust inference | `anova_icc`, `design_effect` |
| Gates E1–E3 / E8 | `tools/validate_author_space.py` / `tools/validate_lm_envelopes.py` |
| Recorded gate evidence | `reports/validation/author_space/` |
