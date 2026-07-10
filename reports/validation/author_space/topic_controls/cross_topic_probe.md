# Cross-Topic Robustness Probe (C1b, issue #95 P3)

- Generated: 2026-06-10T00:09:34.940637+00:00
- Artifact: data/artifacts/author_space_v1_wave2.json (variant mfw_delta)
- Authors with >= 4 works: 12 (69 held-out works)
- Content vocabulary: top 2000 shelf words minus function words = 1724 content words (276 function words removed); per-work tf normalized.

**Question:** does MFW-Delta LOO attribution degrade when a held-out work shares less subject matter (content-word profile) with its author's other works?

## Headline

- Top-1 accuracy: 97.1% (67/69; 2 errors)
- Within-author LOO topic similarity range: 0.540 - 0.951 (p50 0.854); between-author context p50 0.714
- Spearman(topic sim, attribution margin): rho = -0.373 (p = 0.002)
- Spearman(topic sim, distance to own LOO centroid): rho = -0.433 (p = 0.000)
- Point-biserial(error, topic sim): r = -0.459 (p = 0.000)

## Scatter summary (quartile bins of LOO topic similarity)

| Bin | Topic-sim range | n | Top-1 | Median margin | Median d_own |
|---|---|---|---|---|---|
| Q1 | 0.540 - 0.755 | 18 | 88.9% | -0.140 | 0.649 |
| Q2 | 0.755 - 0.854 | 17 | 100.0% | -0.170 | 0.655 |
| Q3 | 0.862 - 0.905 | 17 | 100.0% | -0.239 | 0.530 |
| Q4 | 0.907 - 0.951 | 17 | 100.0% | -0.260 | 0.507 |

## Attribution errors

- mccarthy-cormac / Stella Maris: own rank 14, margin +0.438, topic sim 0.541
- whitehead-colson / The Intuitionist: own rank 4, margin +0.030, topic sim 0.540

## Reading

Within-author content similarity spans 0.411 of cosine (works genuinely differ in subject matter), while LOO attribution stays at 97.1% overall and 88.9% in the LOWEST topic-similarity quartile (works most off-topic for their author). The topic-similarity vs attribution-margin correlation is rho = -0.373 (p = 0.002).

There is a graded coupling: works that are more topically typical of their author also sit closer in MFW Delta. This is expected even under purely stylistic attribution, because topic and style co-drift within a career (and atypical-topic works are often atypical-register works, e.g. a dialogue-only novel). The decisive observation is that attribution does NOT collapse at the off-topic end of the range: MFW identity degrades gracefully with topical atypicality but is not riding topic. Cross-check with the function-words-only probe (zero content words in the vocabulary) to close the loop.

---

# Addendum (manual): closing the loop

## Function-words-only cross-check (`fwonly_probe/cross_topic_probe.json`)

The same probe re-run against the fw-only artifact (vocabulary contains
ZERO content words, so topic cannot enter the distance mechanically):

- Top-1: 95.7% (66/69, 3 errors); Q1 (lowest topic-similarity quartile)
  top-1 = 88.9%, identical to the mixed-vocabulary space.
- rho(topic sim, margin) = -0.308 (p = 0.010) — the coupling persists at
  almost the same strength WITHOUT any content words in the vocabulary.

This is the decisive observation: since the fw-only Delta cannot see topic
words, the graded topic-margin coupling must come from co-drift (works that
are topically atypical for an author tend to also be register/period
atypical — e.g. *Stella Maris*, a dialogue-only novel, is both the most
off-topic and the most off-style McCarthy in both spaces). The coupling is
therefore not evidence that MFW identity rides topic.

## PAN14 benchmark sanity run (`pan_mfw_delta.json`)

The repo's PAN infrastructure (validation/pan, PAN14 authorship
verification) fits a small sanity run: Burrows Delta over top-300 MFW,
score = -Delta(unknown, mean of knowns), AUC over Y/N labels (balanced
sets; verification, NOT closed-set attribution — numbers are not comparable
to the E2 gates, and PAN14 texts are ~750-1500 words vs whole novels here).

| Subset | n | vocab none | fw-only |
|---|---|---|---|
| English essays (cross-topic by construction) | 200 | AUC 0.595 | AUC 0.633 |
| English novels (cross-genre) | 100 | AUC 0.840 | AUC 0.614 |

Readings: (a) on the explicitly cross-topic essays subset, removing content
words IMPROVES verification — content words are noise under topic shift,
consistent with the C1 motivation; (b) on the cross-genre novels subset
content words help, i.e. the unfiltered vocabulary does absorb
genre/content signal — which is exactly why the gold-shelf headline claims
were re-checked under fw-only (they hold; see `fwonly_comparison.md`);
(c) short-text verification AUCs are far below the whole-novel gold-shelf
regime, as expected from the E6 window-length findings. No deeper PAN
integration was attempted: the dataset is verification-shaped (Y/N pairs),
not closed-set attribution, so it cannot host the E2/E4 protocols directly.

## Overall cross-topic verdict

Within-shelf content similarity varies widely (cosine 0.54-0.95) while LOO
attribution stays at 97.1% (mixed vocab) / 95.7% (fw-only), and never drops
below 88.9% even in the most off-topic quartile. The residual
topic-attribution coupling survives content-word removal, identifying it as
career co-drift rather than topical leakage. MFW identity on this shelf is
not riding topic.
