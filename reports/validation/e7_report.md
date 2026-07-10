# E7 — Clustering Methodology Control (ADR-0035 Phase B, executed as ADR-0041 E7)

> *Release note: local path prefixes and personal-corpus identifiers were redacted from this frozen file for publication; all numeric content is unchanged.*

- Generated: 2026-06-09
- Control author: Don DeLillo — 6 fiction-eligible Control Shelf works,
  1971–2016, deliberately chosen for textbook stylistic discontinuity
  (early postmodern → late minimalist). Underworld excluded
  (`requires_manual_trim`).
- Protocol: 240 × 800-word windows (40/work, seed 42, body offsets from
  `control_shelf_manifest.yaml`, `window_text()` convention from
  `calibrate_register_targets.py`), per-window D18 baselines via
  `generate_baselines.py [personal-corpus reference redacted] --tier better` (2 shards), clustered
  with `cluster_voice_registers.py`'s exact algorithm: StandardScaler +
  KMeans(random_state=42, n_init=10), k auto-selected by max silhouette over
  2–8 — identical to how the internal reference baselines were built ([personal-corpus identifiers redacted]; the resulting numeric bar, silhouette 0.074, is stated in the paper's Appendix B).

## Verdict: **METHODOLOGY DOES NOT VALIDATE**

| Measure | Value | Reading |
|---|---|---|
| Best k (auto) | 2 | Numerically in the critic-predicted 2–4 range, but the split is not phases |
| Silhouette at k=2 | **0.142** | Beats the Bryant v3.0 bar (0.074); 2.6× the matched noise null (0.054) — real but *weak* structure |
| Noise nulls (10 reps) | Gaussian 0.054, column-permuted 0.054 | Bryant v3.0's 0.074 sits ≈ null; DeLillo clears it |
| Cluster vs work (ARI / NMI / purity) | 0.057 / 0.085 / 0.283 | Clusters do **not** track works |
| Cluster vs 2-period (early ≤1988 / late ≥2007) | ARI 0.023, purity 0.667 | ≈ chance (majority class = 0.667) |
| Cluster vs 3-phase | ARI 0.038, purity 0.438 | ≈ chance |
| True work-partition silhouette | 0.005 | Works are not compact clusters in this space at 800w |
| Nearest-work-centroid attribution | 62.9% (chance 16.7%) | Work signal exists in the *means*, swamped at window level |

The numeric half of the gate passes; the "critically coherent clusters"
half fails. On an author whose phase structure is visible to any critic, the
pipeline recovers no phase structure, and the structure it does recover is
substantially a feature-redundancy artifact (below).

### Contingency, k=2 (cluster × work)

| Cluster | americana 1971 | ratner's 1976 | white-noise 1985 | libra 1988 | falling-man 2007 | zero-k 2016 | n |
|---|---|---|---|---|---|---|---|
| 0 ("formal_direct") | 15 | 33 | 23 | 12 | 5 | 18 | 106 |
| 1 ("direct_dynamic") | 25 | 7 | 17 | 28 | 35 | 22 | 134 |

Both clusters mix all six works. Cluster × period: c0 = 83 early / 23 late,
c1 = 77 early / 57 late.

### What the k=2 split actually is

Top separating dimensions (scaled means c0 vs c1): vocabulary_richness
(+0.85/−0.67), ttr (+0.85/−0.67), repetition_ratio (−0.84/+0.66),
lexical_density (+0.70/−0.55), formality_index (+0.70/−0.55). I.e. **dense
discursive narration vs lexically sparse scene/dialogue prose**. Dialogue is
a significant but modest correlate (quote chars/100w: 4.56 vs 3.16,
point-biserial r = 0.203, p = 0.0016) — the driver is lexical richness, which
the feature set counts three times (see G2).

### Exemplar assessment (3 per cluster, scaled-space nearest-to-centroid; internal use)

**Cluster 0 — dense narration.** Exemplars span three novels and 36 years:
- `falling-man_w0065` (2007): "There was an element of pure ritual in his
  movements, something beyond the functional…"
- `ratner-s-star_w0098` (1976): "For an unreal moment he imagined that the
  man in the doorway was an extraterrestrial, here to confirm his arithmetic…"
- `americana_w0028` (1971): "…lost in the hollow of her breasts, swimming
  through fish-silver rooms, fathomless, deep in the shipwreck of sleep."

**Cluster 1 — dialogue-scene prose.** Also spans three novels:
- `falling-man_w0004` (2007): "'They were my things, not yours.' … 'This
  isn't the time.' 'You actually married the man.'"
- `ratner-s-star_w0095` (1976): "'I guess that's how you get a house with
  grounds.' … 'That fazes me. It really does.'"
- `white-noise_w0041` (1985): "'What kind of stuff?' 'I don't know but it's
  supposed to make the spill harmless…'"

Each triad shares a recognizable texture, so the axis is *articulable* — but
it is one thin axis (narration vs dialogue density), not a register
inventory, and it is invariant to DeLillo's 45-year stylistic arc.

### k-scan and the buried structure

Silhouette is monotonically decreasing: k=2 0.142, k=3 0.115, k=4 0.105,
k=5 0.100, k=6 0.098, k=7 0.090, k=8 0.084 — max-silhouette selection always
returns the smallest split offered. Forcing k=6 (not what the tool would
pick) reveals structure the selector throws away: **Falling Man dominates
cluster 1 (26/40) and Zero K dominates cluster 2 (26/40)** — the two
late-minimalist novels each claim a cluster (ARI vs work rises to 0.133) —
while cluster 4 degenerates to n=4, reproducing Bryant v2.0's micro-cluster
("YES", n=1) failure mode in miniature.

## Methodology gaps

1. **G1 — k-selection**: max-silhouette auto-k collapses to k=2 on
   overlapping elliptical data and discards real finer structure (the
   late-minimalist clusters at k=6). Fix: stability/consensus k (bootstrapped
   ARI), gap statistic, or GMM-BIC; silhouette as floor check only.
2. **G2 — feature redundancy / scaling**: `ttr`, `vocabulary_richness`,
   `repetition_ratio` are one signal counted three times (|r| ≥ 0.98;
   ttr~vocab r = +0.994, repetition~vocab r = −0.996); `past_ratio~present_ratio`
   r = −0.98. After per-feature standardization the lexical-richness axis is
   triple-weighted and dictates KMeans geometry — the discovered "registers"
   are substantially a double-counting artifact. Fix: decorrelate
   (PCA/whitening/Mahalanobis) or prune; or use E3's `dimension_set_v2`.
3. **G3 — no minimum-cluster-size guard**: nothing prevents degenerate
   micro-clusters (n=4 at k=6 here; n=1 in Bryant v2.0). Fix: min-size
   constraint with reassignment or HDBSCAN-style noise labeling.
4. **G4 — feature granularity at window scale**: D18 scalars at 800 words
   carry too little intra-author signal (true work-partition silhouette
   0.005; consistent with E6's finding that 800w windows only reach ~56%
   *between*-author attribution; intra-author phase differences are subtler).
   Fix candidates: chapter-scale aggregation, MFW-Delta features,
   permutation-null gates built into the tool.
5. **G5 — register naming**: `characterize_register()` thresholds are tuned
   to Bryant chat text (self_focus > 0.4, formality > 0.12); on literary
   prose they emit near-meaningless names ("formal_direct",
   "direct_dynamic"). Cosmetic, but symptomatic of Bryant-origin hardcoding.

## What did validate (scope-limited positives)

- The feature pipeline detects *some* real structure on a known author
  (2.6× noise null) — unlike Bryant v3.0, whose 0.074 sits at its null. The
  numeric bar is met.
- The single recovered axis (narration vs dialogue-scene) is articulable and
  exemplar-coherent — a genuine register-like contrast, however thin.
- Work-level authorial signal exists in the same 18 features at the mean
  level (62.9% nearest-work-centroid vs 16.7% chance), consistent with
  legacy E1–E3: features aren't worthless, the *unsupervised window-level
  clustering recipe* is the weak link.

## Consequence (binding for ADR-0041 Phase 5)

- **Do NOT re-cluster Bryant** (ADR-0035 Phase C) with this pipeline as-is.
  The clean_v2.1 corpus is ready, but the identical recipe on clean literary
  text still produces a trivial 2-way lexical split and, at higher k,
  micro-clusters — it would manufacture registers again.
- The supported Bryant decomposition remains **stratification by
  source/context** (gmail / documents / facebook / forum — see
  `bryant_strata_placement.md`): observed structure, not clustered structure.
- Per-register detector thresholds (ADR-0035 Phase C deliverable) remain
  deferred pending a methodology that passes this control with G1–G4
  addressed (candidates: decorrelated feature space + stability-selected k +
  min-size guard + permutation nulls; or MFW-Delta-space clustering at
  chapter scale). The DeLillo control is cheap to re-run: windows, baselines,
  and eval scripts are cached under `data/tmp/e7/`.

Raw numbers: `e7_results.json`. Full eval dump: `data/tmp/e7/e7_eval_out.json`.
Window inventory: `data/tmp/e7/window_index.json`. Register library artifact:
`data/tmp/e7/delillo_registers_e7.json`.
