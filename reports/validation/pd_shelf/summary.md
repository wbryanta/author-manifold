# Author-Relative Space Validation (E1-E3)

- Generated: 2026-06-10T15:49:36.718302+00:00
- Baseline dir: data/pd_work_baselines
- Manifest: data/pd_manifest.yaml
- Authors: 9 calibrated (35 works); seed 20260609
- Dimension set: v1 (18 dims)

## Gate table

| Experiment | Criterion | Threshold | Observed | Verdict |
|---|---|---|---|---|
| E1 Within vs between author separation | pooled_auc | >= 0.900 | 0.999 | PASS |
| E1 Within vs between author separation | silhouette_positive_fraction | >= 0.800 | 1.000 | PASS |
| E2 Leave-one-work-out attribution | top1_accuracy | >= 0.700 | 1.000 | PASS |
| E2 Leave-one-work-out attribution | top3_accuracy | >= 0.850 | 1.000 | PASS |
| E3 Per-dimension discriminative validity | n_dimensions_exceeding_null_p99 | >= 6.000 | 15.000 | PASS |

**Overall: PASS**

## E1 — Within vs between author separation

Pooled AUC: 0.999 (within n=35, median 0.571; between n=280, median 1.048)

| Author | Works | Silhouette | Within median | Between median |
|---|---|---|---|---|
| austen-jane | 5 | 0.419 | 0.507 | 1.185 |
| bronte-charlotte | 4 | 0.389 | 0.451 | 0.930 |
| dickens-charles | 4 | 0.254 | 0.536 | 0.977 |
| fitzgerald-f_scott | 3 | 0.218 | 0.646 | 1.004 |
| forster-e_m | 5 | 0.365 | 0.488 | 0.993 |
| hawthorne-nathaniel | 3 | 0.342 | 0.576 | 1.098 |
| joyce-james | 3 | 0.106 | 0.785 | 1.063 |
| melville-herman | 4 | 0.224 | 0.707 | 1.168 |
| woolf-virginia | 4 | 0.112 | 0.757 | 1.025 |

**What this means:** A work by a known author sits closer to its own author's centroid than to other authors' centroids with discrimination AUC 0.999 (1.0 = perfect, 0.5 = chance). 9 of 9 authors form coherent clusters (silhouette > 0). Within-author variation is reliably smaller than between-author separation, so W/B percentile statements made in this space are meaningful.

## E2 — Leave-one-work-out attribution

Top-1: 100.0%, top-3: 100.0% over 35 held-out works, 9 candidate authors. C_llr 1.482 (min 0.542; descriptive only). Sanity check (cosine on raw vectors, not a gate): top-1 n/a.

Confusion matrix (rows = true author, columns = predicted, by index):

| # | Author | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | austen-jane | 5 |  |  |  |  |  |  |  |  |
| 2 | bronte-charlotte |  | 4 |  |  |  |  |  |  |  |
| 3 | dickens-charles |  |  | 4 |  |  |  |  |  |  |
| 4 | fitzgerald-f_scott |  |  |  | 3 |  |  |  |  |  |
| 5 | forster-e_m |  |  |  |  | 5 |  |  |  |  |
| 6 | hawthorne-nathaniel |  |  |  |  |  | 3 |  |  |  |
| 7 | joyce-james |  |  |  |  |  |  | 3 |  |  |
| 8 | melville-herman |  |  |  |  |  |  |  | 4 |  |
| 9 | woolf-virginia |  |  |  |  |  |  |  |  | 4 |

**What this means:** When each work is held out and re-attributed by nearest author centroid, the true author is the single best match 100% of the time and among the top three 100% of the time. The space carries enough authorial signal for closed-set attribution among known authors, supporting its use as a measurement frame.

## E3 — Per-dimension discriminative validity

15 of 18 dimensions exceed their permutation-null p99 (1000 shuffles, seed 20260609).

| Rank | Dimension | F | eta^2 | null p99 | perm p | ICC-like | > null p99 |
|---|---|---|---|---|---|---|---|
| 1 | abstract_ratio | 19.4 | 0.857 | 0.493 | 0.0010 | 0.826 | yes |
| 2 | metaphor_per_100 | 15.4 | 0.825 | 0.492 | 0.0010 | 0.788 | yes |
| 3 | future_ratio | 14.4 | 0.816 | 0.492 | 0.0010 | 0.776 | yes |
| 4 | complexity_score | 13.9 | 0.811 | 0.488 | 0.0010 | 0.770 | yes |
| 5 | sentiment_score | 11.2 | 0.774 | 0.523 | 0.0010 | 0.724 | yes |
| 6 | function_word_ratio_extended | 10.6 | 0.765 | 0.524 | 0.0010 | 0.712 | yes |
| 7 | ttr | 7.3 | 0.692 | 0.485 | 0.0010 | 0.619 | yes |
| 8 | vocabulary_richness | 7.3 | 0.691 | 0.482 | 0.0010 | 0.618 | yes |
| 9 | repetition_ratio | 7.2 | 0.690 | 0.480 | 0.0010 | 0.616 | yes |
| 10 | certainty_index | 7.0 | 0.684 | 0.522 | 0.0020 | 0.609 | yes |
| 11 | lexical_density | 6.4 | 0.662 | 0.505 | 0.0010 | 0.581 | yes |
| 12 | formality_index | 5.6 | 0.633 | 0.547 | 0.0010 | 0.543 | yes |
| 13 | char_ngram_mean | 5.4 | 0.624 | 0.500 | 0.0010 | 0.532 | yes |
| 14 | self_focus_ratio | 5.3 | 0.619 | 0.519 | 0.0020 | 0.525 | yes |
| 15 | paragraph_cv | 3.1 | 0.489 | 0.423 | 0.0020 | 0.353 | yes |
| 16 | sentence_cv | 1.8 | 0.356 | 0.486 | 0.0869 | 0.171 | no |
| 17 | past_ratio | 1.4 | 0.308 | 0.492 | 0.2158 | 0.104 | no |
| 18 | present_ratio | 1.0 | 0.233 | 0.508 | 0.4446 | 0.000 | no |

Recommended dimension set v2 (exceeds null p99, ranked by eta^2): abstract_ratio, metaphor_per_100, future_ratio, complexity_score, sentiment_score, function_word_ratio_extended, ttr, vocabulary_richness, repetition_ratio, certainty_index, lexical_density, formality_index, char_ngram_mean, self_focus_ratio, paragraph_cv

**What this means:** For each dimension we ask whether authors differ more than random label shuffling would produce. 15 dimensions carry real author-discriminative signal at work level; the rest are indistinguishable from noise on this shelf. Enough dimensions are individually valid to support the 18-dim space; recommended_dimension_set_v2 lists the validated subset for downstream weighting.
