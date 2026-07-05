# Author-Relative Space Validation (E1-E3)

- Generated: 2026-06-10T00:05:27.617967+00:00
- Baseline dir: data/baselines/author_space_build/work_baselines
- Manifest: data/baselines/author_space_build/control_shelf_manifest.yaml
- Authors: 15 calibrated (78 works); seed 20260609
- Dimension set: v1 (18 dims)

## Gate table

| Experiment | Criterion | Threshold | Observed | Verdict |
|---|---|---|---|---|
| E1 Within vs between author separation | pooled_auc | >= 0.900 | 0.911 | PASS |
| E1 Within vs between author separation | silhouette_positive_fraction | >= 0.800 | 0.867 | PASS |
| E2 Leave-one-work-out attribution | top1_accuracy | >= 0.700 | 0.923 | PASS |
| E2 Leave-one-work-out attribution | top3_accuracy | >= 0.850 | 0.974 | PASS |

**Overall: PASS**

## E1 — Within vs between author separation

Pooled AUC: 0.911 (within n=78, median 0.543; between n=1092, median 0.870)

| Author | Works | Silhouette | Within median | Between median |
|---|---|---|---|---|
| delillo-don | 6 | 0.157 | 0.498 | 0.779 |
| didion-joan | 4 | 0.186 | 0.559 | 0.836 |
| foster_wallace-david | 3 | 0.064 | 0.682 | 0.857 |
| ishiguro-kazuo | 6 | 0.107 | 0.672 | 1.045 |
| mccarthy-cormac | 8 | -0.039 | 0.743 | 1.123 |
| morrison-toni | 9 | 0.248 | 0.446 | 0.819 |
| murakami-haruki | 7 | 0.103 | 0.610 | 0.819 |
| ondaatje-michael | 7 | 0.196 | 0.526 | 0.867 |
| proulx-annie | 4 | 0.210 | 0.419 | 0.758 |
| pynchon-thomas | 4 | 0.064 | 0.638 | 0.880 |
| robinson-marilynne | 3 | -0.023 | 0.825 | 0.901 |
| saunders-george | 4 | 0.200 | 0.564 | 0.843 |
| sebald-w_g | 3 | 0.384 | 0.512 | 1.068 |
| tokarczuk-olga | 6 | 0.199 | 0.489 | 0.808 |
| whitehead-colson | 4 | 0.128 | 0.448 | 0.795 |

**What this means:** A work by a known author sits closer to its own author's centroid than to other authors' centroids with discrimination AUC 0.911 (1.0 = perfect, 0.5 = chance). 13 of 15 authors form coherent clusters (silhouette > 0). Within-author variation is reliably smaller than between-author separation, so W/B percentile statements made in this space are meaningful.

## E2 — Leave-one-work-out attribution

Top-1: 92.3%, top-3: 97.4% over 78 held-out works, 15 candidate authors. C_llr 1.854 (min 0.751; descriptive only). Sanity check (cosine on raw vectors, not a gate): top-1 n/a.

Confusion matrix (rows = true author, columns = predicted, by index):

| # | Author | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | delillo-don | 6 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 | didion-joan |  | 4 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 3 | foster_wallace-david |  |  | 1 |  |  |  |  |  |  | 1 |  | 1 |  |  |  |
| 4 | ishiguro-kazuo |  |  |  | 6 |  |  |  |  |  |  |  |  |  |  |  |
| 5 | mccarthy-cormac |  |  |  |  | 6 |  |  |  | 1 |  | 1 |  |  |  |  |
| 6 | morrison-toni |  |  |  |  |  | 9 |  |  |  |  |  |  |  |  |  |
| 7 | murakami-haruki |  |  |  |  |  |  | 7 |  |  |  |  |  |  |  |  |
| 8 | ondaatje-michael |  |  |  |  |  |  |  | 7 |  |  |  |  |  |  |  |
| 9 | proulx-annie |  |  |  |  |  |  |  |  | 4 |  |  |  |  |  |  |
| 10 | pynchon-thomas |  |  | 1 |  |  |  |  |  |  | 3 |  |  |  |  |  |
| 11 | robinson-marilynne |  |  |  |  |  |  |  | 1 |  |  | 2 |  |  |  |  |
| 12 | saunders-george |  |  |  |  |  |  |  |  |  |  |  | 4 |  |  |  |
| 13 | sebald-w_g |  |  |  |  |  |  |  |  |  |  |  |  | 3 |  |  |
| 14 | tokarczuk-olga |  |  |  |  |  |  |  |  |  |  |  |  |  | 6 |  |
| 15 | whitehead-colson |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 4 |

**What this means:** When each work is held out and re-attributed by nearest author centroid, the true author is the single best match 92% of the time and among the top three 97% of the time. The space carries enough authorial signal for closed-set attribution among known authors, supporting its use as a measurement frame.
