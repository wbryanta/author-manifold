# Author-Relative Space Validation (E1-E3)

> *Release note: local path prefixes and personal-corpus identifiers were redacted from this frozen file for publication; all numeric content is unchanged.*

- Generated: 2026-06-09T19:51:03.508284+00:00
- Baseline dir: data/baselines/author_space_build/work_baselines
- Manifest: data/baselines/author_space_build/control_shelf_manifest.yaml
- Authors: 11 calibrated (59 works); seed 20260609
- Dimension set: v1 (18 dims)

## Gate table

| Experiment | Criterion | Threshold | Observed | Verdict |
|---|---|---|---|---|
| E1 Within vs between author separation | pooled_auc | >= 0.900 | 0.892 | FAIL |
| E1 Within vs between author separation | silhouette_positive_fraction | >= 0.800 | 0.545 | FAIL |
| E2 Leave-one-work-out attribution | top1_accuracy | >= 0.700 | 0.644 | FAIL |
| E2 Leave-one-work-out attribution | top3_accuracy | >= 0.850 | 0.847 | FAIL |
| E3 Per-dimension discriminative validity | n_dimensions_exceeding_null_p99 | >= 6.000 | 18.000 | PASS |

**Overall: FAIL**

## E1 — Within vs between author separation

Pooled AUC: 0.892 (within n=59, median 3.050; between n=590, median 5.269)

| Author | Works | Silhouette | Within median | Between median |
|---|---|---|---|---|
| delillo-don | 6 | 0.075 | 3.046 | 4.828 |
| didion-joan | 4 | 0.168 | 2.848 | 4.590 |
| ishiguro-kazuo | 6 | 0.277 | 3.145 | 6.525 |
| mccarthy-cormac | 8 | 0.085 | 3.131 | 6.102 |
| morrison-toni | 9 | -0.060 | 3.679 | 4.628 |
| ondaatje-michael | 7 | 0.187 | 2.757 | 4.569 |
| proulx-annie | 4 | -0.031 | 3.266 | 4.768 |
| pynchon-thomas | 4 | -0.006 | 3.972 | 5.807 |
| robinson-marilynne | 3 | -0.085 | 4.485 | 5.608 |
| saunders-george | 4 | 0.310 | 2.841 | 5.970 |
| whitehead-colson | 4 | -0.064 | 2.910 | 5.180 |

**What this means:** A work by a known author sits closer to its own author's centroid than to other authors' centroids with discrimination AUC 0.892 (1.0 = perfect, 0.5 = chance). 6 of 11 authors form coherent clusters (silhouette > 0). Separation is too weak: W/B percentile statements in this space would not be trustworthy. Do not proceed to author placement on these dimensions.

## E2 — Leave-one-work-out attribution

Top-1: 64.4%, top-3: 84.7% over 59 held-out works, 11 candidate authors. C_llr 1.160 (min 0.606; descriptive only). Sanity check (cosine on raw vectors, not a gate): top-1 55.9%.

Confusion matrix (rows = true author, columns = predicted, by index):

| # | Author | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | delillo-don | 5 | 1 |  |  |  |  |  |  |  |  |  |
| 2 | didion-joan |  | 3 |  |  | 1 |  |  |  |  |  |  |
| 3 | ishiguro-kazuo |  |  | 5 |  |  |  |  |  | 1 |  |  |
| 4 | mccarthy-cormac | 1 |  |  | 5 |  | 2 |  |  |  |  |  |
| 5 | morrison-toni |  | 1 |  |  | 5 |  |  |  | 3 |  |  |
| 6 | ondaatje-michael |  |  |  |  | 1 | 6 |  |  |  |  |  |
| 7 | proulx-annie |  |  |  |  |  |  | 1 |  |  |  | 3 |
| 8 | pynchon-thomas |  |  |  |  | 1 |  |  | 2 |  |  | 1 |
| 9 | robinson-marilynne |  |  | 1 |  |  | 1 |  |  | 1 |  |  |
| 10 | saunders-george |  |  |  |  |  |  |  |  |  | 4 |  |
| 11 | whitehead-colson |  |  |  |  |  |  | 2 | 1 |  |  | 1 |

**What this means:** When each work is held out and re-attributed by nearest author centroid, the true author is the single best match 64% of the time and among the top three 85% of the time. Attribution accuracy is below the gate: the space does not yet carry enough authorial signal to trust placements.

## E3 — Per-dimension discriminative validity

18 of 18 dimensions exceed their permutation-null p99 (1000 shuffles, seed 20260609).

| Rank | Dimension | F | eta^2 | null p99 | perm p | ICC-like | > null p99 |
|---|---|---|---|---|---|---|---|
| 1 | sentence_cv | 14.7 | 0.754 | 0.346 | 0.0010 | 0.721 | yes |
| 2 | sentiment_score | 14.3 | 0.749 | 0.374 | 0.0010 | 0.715 | yes |
| 3 | char_ngram_mean | 13.8 | 0.742 | 0.385 | 0.0010 | 0.707 | yes |
| 4 | certainty_index | 10.9 | 0.694 | 0.340 | 0.0010 | 0.651 | yes |
| 5 | lexical_density | 10.7 | 0.690 | 0.332 | 0.0010 | 0.647 | yes |
| 6 | metaphor_per_100 | 10.6 | 0.688 | 0.356 | 0.0010 | 0.644 | yes |
| 7 | function_word_ratio_extended | 8.6 | 0.643 | 0.346 | 0.0010 | 0.591 | yes |
| 8 | formality_index | 7.0 | 0.595 | 0.346 | 0.0010 | 0.533 | yes |
| 9 | self_focus_ratio | 6.9 | 0.591 | 0.377 | 0.0010 | 0.528 | yes |
| 10 | future_ratio | 5.9 | 0.552 | 0.375 | 0.0010 | 0.481 | yes |
| 11 | paragraph_cv | 4.5 | 0.485 | 0.342 | 0.0010 | 0.399 | yes |
| 12 | ttr | 4.0 | 0.455 | 0.375 | 0.0010 | 0.362 | yes |
| 13 | vocabulary_richness | 3.9 | 0.451 | 0.367 | 0.0010 | 0.357 | yes |
| 14 | abstract_ratio | 3.9 | 0.449 | 0.352 | 0.0020 | 0.354 | yes |
| 15 | repetition_ratio | 3.8 | 0.445 | 0.359 | 0.0020 | 0.349 | yes |
| 16 | past_ratio | 3.1 | 0.393 | 0.362 | 0.0060 | 0.284 | yes |
| 17 | present_ratio | 3.0 | 0.388 | 0.361 | 0.0060 | 0.279 | yes |
| 18 | complexity_score | 2.7 | 0.357 | 0.328 | 0.0060 | 0.239 | yes |

Recommended dimension set v2 (exceeds null p99, ranked by eta^2): sentence_cv, sentiment_score, char_ngram_mean, certainty_index, lexical_density, metaphor_per_100, function_word_ratio_extended, formality_index, self_focus_ratio, future_ratio, paragraph_cv, ttr, vocabulary_richness, abstract_ratio, repetition_ratio, past_ratio, present_ratio, complexity_score

**What this means:** For each dimension we ask whether authors differ more than random label shuffling would produce. 18 dimensions carry real author-discriminative signal at work level; the rest are indistinguishable from noise on this shelf. Enough dimensions are individually valid to support the 18-dim space; recommended_dimension_set_v2 lists the validated subset for downstream weighting.
