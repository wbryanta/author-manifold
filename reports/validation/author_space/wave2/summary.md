# Author-Relative Space Validation (E1-E3)

- Generated: 2026-06-09T20:55:08.507681+00:00
- Baseline dir: data/baselines/author_space_build/work_baselines
- Manifest: data/baselines/author_space_build/control_shelf_manifest.yaml
- Authors: 15 calibrated (78 works); seed 20260609
- Dimension set: v1 (18 dims)

## Gate table

| Experiment | Criterion | Threshold | Observed | Verdict |
|---|---|---|---|---|
| E1 Within vs between author separation | pooled_auc | >= 0.900 | 0.941 | PASS |
| E1 Within vs between author separation | silhouette_positive_fraction | >= 0.800 | 0.933 | PASS |
| E2 Leave-one-work-out attribution | top1_accuracy | >= 0.700 | 0.962 | PASS |
| E2 Leave-one-work-out attribution | top3_accuracy | >= 0.850 | 0.962 | PASS |

**Overall: PASS**

## E1 — Within vs between author separation

Pooled AUC: 0.941 (within n=78, median 0.579; between n=1092, median 0.956)

| Author | Works | Silhouette | Within median | Between median |
|---|---|---|---|---|
| delillo-don | 6 | 0.165 | 0.559 | 0.900 |
| didion-joan | 4 | 0.215 | 0.649 | 0.974 |
| foster_wallace-david | 3 | 0.170 | 0.613 | 0.899 |
| ishiguro-kazuo | 6 | 0.069 | 0.799 | 1.161 |
| mccarthy-cormac | 8 | 0.008 | 0.758 | 1.220 |
| morrison-toni | 9 | 0.239 | 0.499 | 0.877 |
| murakami-haruki | 7 | 0.212 | 0.549 | 0.900 |
| ondaatje-michael | 7 | 0.179 | 0.608 | 0.949 |
| proulx-annie | 4 | 0.241 | 0.510 | 0.846 |
| pynchon-thomas | 4 | 0.138 | 0.584 | 0.889 |
| robinson-marilynne | 3 | -0.074 | 0.956 | 1.060 |
| saunders-george | 4 | 0.176 | 0.571 | 0.926 |
| sebald-w_g | 3 | 0.432 | 0.533 | 1.113 |
| tokarczuk-olga | 6 | 0.174 | 0.524 | 0.887 |
| whitehead-colson | 4 | 0.131 | 0.553 | 0.931 |

**What this means:** A work by a known author sits closer to its own author's centroid than to other authors' centroids with discrimination AUC 0.941 (1.0 = perfect, 0.5 = chance). 14 of 15 authors form coherent clusters (silhouette > 0). Within-author variation is reliably smaller than between-author separation, so W/B percentile statements made in this space are meaningful.

## E2 — Leave-one-work-out attribution

Top-1: 96.2%, top-3: 96.2% over 78 held-out works, 15 candidate authors. C_llr 1.826 (min 0.732; descriptive only). Sanity check (cosine on raw vectors, not a gate): top-1 n/a.

Confusion matrix (rows = true author, columns = predicted, by index):

| # | Author | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | delillo-don | 6 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 | didion-joan |  | 4 |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 3 | foster_wallace-david |  |  | 3 |  |  |  |  |  |  |  |  |  |  |  |  |
| 4 | ishiguro-kazuo |  |  |  | 6 |  |  |  |  |  |  |  |  |  |  |  |
| 5 | mccarthy-cormac |  |  |  |  | 7 |  | 1 |  |  |  |  |  |  |  |  |
| 6 | morrison-toni |  |  |  |  |  | 9 |  |  |  |  |  |  |  |  |  |
| 7 | murakami-haruki |  |  |  |  |  |  | 7 |  |  |  |  |  |  |  |  |
| 8 | ondaatje-michael |  |  |  |  |  |  |  | 7 |  |  |  |  |  |  |  |
| 9 | proulx-annie |  |  |  |  |  |  |  |  | 4 |  |  |  |  |  |  |
| 10 | pynchon-thomas |  |  |  |  |  |  |  |  |  | 4 |  |  |  |  |  |
| 11 | robinson-marilynne |  |  |  |  |  |  |  |  |  |  | 2 |  |  | 1 |  |
| 12 | saunders-george |  |  |  |  |  |  |  |  |  |  |  | 4 |  |  |  |
| 13 | sebald-w_g |  |  |  |  |  |  |  |  |  |  |  |  | 3 |  |  |
| 14 | tokarczuk-olga |  |  |  |  |  |  |  |  |  |  |  |  |  | 6 |  |
| 15 | whitehead-colson |  |  |  |  |  |  |  |  |  | 1 |  |  |  |  | 3 |

**What this means:** When each work is held out and re-attributed by nearest author centroid, the true author is the single best match 96% of the time and among the top three 96% of the time. The space carries enough authorial signal for closed-set attribution among known authors, supporting its use as a measurement frame.
