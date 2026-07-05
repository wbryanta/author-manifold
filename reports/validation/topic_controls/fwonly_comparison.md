# Function-Words-Only Vocabulary Control (C1a, issue #95 P3)

Topic-confound control for the MFW-Delta findings: the wave-2 top-300 MFW
vocabulary is 46.7% open-class (see `vocab_inspection.md`). Here the
15-author space is rebuilt with `vocab_filter=function_words_only` — the
Burrows-Delta candidate vocabulary restricted to the 376-entry closed-class
`STYLOMETRIC_FUNCTION_WORDS` list BEFORE top-N selection, so the measurement
vocabulary carries zero lexical-content signal — and E1/E2/E4 are re-run.

- Control artifact: `data/artifacts/author_space_v1_wave2_fwonly.json`
  (same manifest, baselines, seed, min-works and calibrated 15-author/78-work
  set as wave-2; verified identical work lists. `mfw_n_effective` = 300 — the
  shelf has >= 300 distinct function words, so no vocabulary shrinkage.
  A `beatty-paul` work added to the manifest after the wave-2 freeze loads as
  reference-only and does not touch calibration.)
- 160/300 words are shared with the wave-2 vocabulary; the 140 content words
  are replaced by deeper-ranked function words.
- Machine-readable: `fwonly_e1e2/e{1,2}_results.json`, `e4_results.json`
  (full current corpus), `fwonly_e4_paired.json` (frozen wave-2 sample set).

## Gate table: wave-2 (mixed vocab) vs function-words-only

| Gate | Threshold | wave-2 | fw-only | Delta | Verdict (fw-only) |
|---|---|---|---|---|---|
| E1 pooled AUC | >= 0.90 | 0.941 | 0.911 | -0.030 | PASS |
| E1 silhouette > 0 | >= 80% of authors | 14/15 (0.933) | 13/15 (0.867) | -1 author | PASS |
| E2 LOO top-1 | >= 0.70 | 96.2% | 92.3% | -3.9 pts | PASS |
| E2 LOO top-3 | >= 0.85 | 96.2% | 97.4% | +1.2 pts | PASS |
| E4 unprompted off-manifold (paired 36) | 0 violations | 0/36 | 0/36 | none | PASS |
| E4 style-prompted nearest==target (paired 24) | reported, not gated | 9/24 | 7/24 | -2 | — |
| **E4 entered target W-p90 region (paired 24)** | reported, not gated | **0/24** | **0/24** | **none** | — |

W/B scale shifts modestly (W loo p50 0.579 -> 0.543; B pairs p50 0.956 ->
0.870): removing content words removes some between-author separation too,
as expected — content differences are real author differences on this shelf,
just not the ones we want to lean on.

### Per-author movement (E2 top-1, E1 silhouette)

Losses concentrate in three authors: foster_wallace-david (3 works,
top-1 1.00 -> 0.33), pynchon-thomas (1.00 -> 0.75), mccarthy-cormac
(0.875 -> 0.75; silhouette dips just below 0, the new second negative
author after robinson-marilynne). whitehead-colson improves (0.75 -> 1.00).
All other 11 authors are unchanged at 100% top-1.

## E4 deltas (paired on the frozen wave-2 60-sample set)

The AI corpus manifest has grown since the wave-2 freeze (replicate samples,
gpt-5); the paired comparison below is restricted to the exact 60 sample
files of the frozen wave-2 E4 run (`fwonly_e4_paired.json`). The fw-only run
over the full current corpus (70 samples, incl. gpt-5) also passes the gate:
46 unprompted, 0 violations; 24 styled, 7 nearest==target, 0 entered
(`e4_results.json` in this directory).

| Quantity | wave-2 | fw-only |
|---|---|---|
| Unprompted samples with nearest-author W-pct <= 90 | 0/36 | 0/36 |
| Min nearest-author W-percentile (unprompted) | 98.7 | 98.7 |
| Style-prompted nearest == target | 9/24 | 7/24 |
| **Style-prompted entered target W-p90 region** | **0/24** | **0/24** |
| Min target W-percentile (style-prompted) | 98.7 | 97.4 |

Both headline findings are vocabulary-robust:

1. **Off-manifold (E4 gate)** holds exactly: every unprompted AI sample stays
   beyond every author's within-author p90 even when the measurement
   vocabulary contains no content words.
2. **Never-enters (0/24)** holds exactly: style-prompted samples still never
   enter the target author's W-p90 region; the closest any sample gets to
   any target barely moves (min target W-pct 98.7 -> 97.4).

One secondary observation shifts: the per-model proximity ordering by median
unprompted nearest-distance reshuffles under fw-only (qwen3.6 1.825 -> 1.287
and gemma4 1.697 -> 1.311 move from farthest to nearest; haiku 1.635 ->
1.763 becomes farthest). A real fraction of the local models' wave-2
distance was carried by content-word divergence. This ordering was already
flagged as unresolved in the wave-2 freeze notes (n=6/model); the fw-only
result strengthens the case for treating intra-family ordering as
unsettled pending the P1 scale-up — and for reporting model orderings under
the fw-only vocabulary when they are reported at all.

## Verdict

The E1/E2 gates pass and both E4 headline findings reproduce exactly under a
vocabulary with zero content words. The off-manifold and never-enters
results are not topic artifacts of the mixed top-300 vocabulary. Costs of
the control: ~3-4 points of E2 top-1 (concentrated in the two smallest/most
idiosyncratic-vocabulary authors) and ~0.03 of E1 AUC — consistent with
content words carrying some genuine authorial signal, while the chassis of
the findings is function-word structure.
