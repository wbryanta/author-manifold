# Number Freeze v2 — wave-2 (15-author) artifact is PRIMARY

Frozen: **2026-06-10** (issue #95; supersedes the v1 pilot freeze of 2026-06-09).
The canonical measurement artifact for all Tier 1 paper claims is unchanged:

    data/artifacts/author_space_v1_wave2.json
    (15 authors, 78 works, distance_variant=mfw_delta, N=300)

What changed at v2 is the AI corpus: the full 8-model design matrix is
complete (912 samples generated, **910 placed** — two qwen3.6 generations
returned unusable output and were excluded). Per model: 50 unprompted
(10 scenarios × 5), 20 style_prompted and 20 exemplar (4 pairs × 5;
qwen3.6 19 each), 24 paraphrase (3 phrasings × 4 scenarios × 2).
All numbers below are recomputed on this corpus; never cite the v1 pilot
numbers for the corpus-dependent rows.

Evidence files (this directory unless noted):
`e4_results.json`, `tier1_statistics.{json,md}`, `e4_truncated/e4_results.json`,
`model_self_consistency.{json,md}`, `paraphrase_sensitivity.{json,md}`,
`../topic_controls/e4_scaled_fwonly/e4_results.json`, `../r3_dimension_gap.{json,md}`.

## Frozen headline numbers (Number Freeze v2)

| Claim | Value |
|---|---|
| Corpus | 8 models, 3 families; 912 generated / **910 placed** (400 unprompted, 159 style_prompted, 159 exemplar, 192 paraphrase) |
| E1 separation AUC / silhouette > 0 | 0.941 / 14/15 (unchanged from wave-2 build) |
| E2 LOO attribution top-1 / top-3 | 96.2% / 96.2% (unchanged from wave-2 build) |
| W pooled p50 / B pairs p50 | 0.687 / 1.076 (unchanged from wave-2 build) |
| E4 unprompted off-manifold | **400/400 PASS** (0 violations; min nearest W-pct 97.4; CP 95% [0.991, 1.000]; H0 "rate ≤ 0.90" p = 4.98e-19, Holm 1.14e-17) |
| E4 entered target W-p90 — style_prompted (C1) | **0/159** (CP [0.000, 0.023]; one-sided 95% upper 1.87%; H0 ≥ 0.10 Holm p = 7.42e-07; H0 ≥ 0.05 raw p = 2.87e-04) |
| E4 entered target W-p90 — exemplar (C1b) | **0/159** (same bounds/tests as C1) |
| E4 entered target W-p90 — combined styled (C1c) | **0/318** (CP [0.000, 0.012]; one-sided 95% upper 0.94%; H0 ≥ 0.10 raw p = 2.81e-15, Holm ≈ 6.19e-14; H0 ≥ 0.05 raw p = 8.24e-08) |
| E4 nearest == target (approach, C3) | style 63/159 (39.6%, CP [0.320, 0.477]); exemplar 83/159 (52.2%); combined 146/318 (45.9%); vs empirical null p0 = 0.1106: p = 1.35e-20 (Holm 3.25e-19) |
| Robustness — fw-only vocabulary (scaled re-run, same 910 samples) | 400/400 off-manifold (0 violations); **0/318 entered**; nearest==target 85/318 |
| Robustness — 3,500-word truncation (all 910 samples) | 400/400 off-manifold; **0/318 entered**; nearest==target 155/318 |
| Robustness — prompt paraphrase | off-manifold rate 1.000 under every phrasing; per-model max median spread 0.019 (gpt-5) – 0.106 (qwen3.6) Delta |
| R3 chassis (n=318, 8 models) | MFW Delta median movement −0.030 [−0.048, −0.013], gap closure **−1.8%** (chassis moves AWAY at scale; Holm p = 0.042) vs unprompted Delta gap 1.654 |
| R3 transferred (Holm-sig toward) | repetition_ratio, vocabulary_richness, ttr, sentiment_score, present_ratio, past_ratio |
| R3 moved-away (Holm-sig) | char_ngram_mean, function_word_ratio_extended, certainty_index |
| R3 overshoot (caricature, ≥25% of eligible) | self_focus_ratio (81/268) |
| Model self-consistency | LOO self-attribution **97.8%** (400 trials, 8 models, chance 12.5%); within-model Δ p50 1.373 (gpt-5) – 1.855 (haiku) = 1.86×–2.51× human within p50 (0.740); closest centroid pairs intra-family (fable\|opus 0.549, haiku\|sonnet 0.609, gpt-5\|gpt-5-mini 0.803); farthest gemma\|gpt-5 1.482 |

## Model proximity medians (unprompted nearest-author distance, n=50/model)

gpt-5 1.320 < gpt-5-mini 1.504 < fable 1.550 < sonnet 1.632 ≈ opus 1.636 ≈
haiku 1.637 < qwen3.6 1.729 ≈ gemma4 1.771.

- **Which orderings survive Holm** (23/28 pairs significant): everything
  except the sonnet/opus/haiku triangle (3 pairs), haiku|qwen3.6, and
  qwen3.6|gemma4 — those five orderings cannot be resolved from these data.
- **Vocabulary-sensitivity caveat:** under the fw-only vocabulary the local
  models reshuffle from farthest to among the nearest (qwen3.6 1.729 → 1.263,
  gemma4 1.771 → 1.330; haiku 1.637 → 1.727 becomes farthest). A real
  fraction of the locals' full-vocabulary distance is content-word
  divergence. Report model orderings under the fw-only vocabulary when they
  are reported at all; the headline findings are identical under both
  vocabularies.

## v1 (pilot) → v2 deltas

- E4 unprompted off-manifold: 36/36 → **400/400** (6 models → 8; full design).
- Entered target W-p90: 0/24 → **0/318** (0/159 style + 0/159 exemplar);
  CP one-sided upper tightens 11.7% → 0.94% (combined).
- Approach: 9/24 → 63/159 style (39.6%) / 83/159 exemplar (52.2%).
- R3 MFW gap closure changes sign: **+0.5% (pilot) → −1.8% (v2)** — at scale
  the function-word chassis moves slightly *away* from the target under style
  prompting; the larger n clarifies rather than contradicts the pilot's
  "chassis doesn't move" reading.
- Model ordering: pilot intra-Claude ordering (n=6/model) is superseded; at
  n=50/model all orderings resolve except the five pairs listed above.
- **Manuscript-trajectory rows recorded in the parent project** remain
  pinned to the v1-frozen artifact and were **not re-run at the v2 freeze**
  — personal data, out of paper scope; the paper excludes them from the
  confirmatory family.

---

# Number Freeze v3 — Results 2.0 (2026-06-11)

Supersedes v2 for all ENTRY, APPROACH, COMPLETION, and CHASSIS claims.
The v2 entry criterion (full-novel W-p90) was a length-calibration
artifact caught by adversarial review (RED_TEAM_SYNTHESIS.md K1);
canonical entry numbers now come from length-matched per-author
envelopes (LM-W, 3000w, leave-work-out) gated by the E8 positive
control. Canonical files: `results2/entry_report.md`,
`results2/entry_results.json`, `results2/completion_results.md`,
`e8_results.md`.

| Claim | v3 value |
|---|---|
| E8 positive control (held-out self-entry @p90) | 87.8% wave2 / 83.7% fwonly / 87.3% pd / 87.5% pd-fwonly; strict per-author gate PARTIAL (5/48 cells fail, all single-off-style-work, cluster-consistent with 0.90) |
| Styled entry @p90 (236 floor-compliant) | 20.3% full (DEFF-adj CI [11.7, 31.6]) / 30.5% fw-only ([20.9, 41.6]) |
| Best model vs human pastiche (fw-only @p90) | gpt-5 72.5% ~ Brinton 75.0% (parity); Brinton full-vocab 94.4% |
| Per-target enterability | mccarthy 73-77% / morrison 5-24% / didion 3-14% / ondaatje 4-11% — ordered by envelope width |
| Completion (87 compliant) | 31.0% fw-only @p90 (~ named-style parity); refusals: gpt-5 20/20, gpt-5-mini 12/20 target-selective, gemma4 5, Claude+qwen 0 |
| Chassis | immobile full-vocab (-0.030 [-0.048,-0.013], signs 2/4); fw-only closes ~6% |
| Approach | 51.7% vs scenario-matched null 21.2% (p=8.6e-25); ondaatje n.s.; distance flat full-vocab |
| Translation bound | CUT (n=13 matched-length, p=0.10) |
| v2 rows retained for | instrument validation (E1/E2/E3), self-attribution, paraphrase robustness, PAN appendix |
