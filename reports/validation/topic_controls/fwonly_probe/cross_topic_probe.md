# Cross-Topic Robustness Probe (C1b, issue #95 P3)

- Generated: 2026-06-10T00:09:40.420340+00:00
- Artifact: data/artifacts/author_space_v1_wave2_fwonly.json (variant mfw_delta)
- Authors with >= 4 works: 12 (69 held-out works)
- Content vocabulary: top 2000 shelf words minus function words = 1724 content words (276 function words removed); per-work tf normalized.

**Question:** does MFW-Delta LOO attribution degrade when a held-out work shares less subject matter (content-word profile) with its author's other works?

## Headline

- Top-1 accuracy: 95.7% (66/69; 3 errors)
- Within-author LOO topic similarity range: 0.540 - 0.951 (p50 0.854); between-author context p50 0.714
- Spearman(topic sim, attribution margin): rho = -0.308 (p = 0.010)
- Spearman(topic sim, distance to own LOO centroid): rho = -0.300 (p = 0.012)
- Point-biserial(error, topic sim): r = -0.221 (p = 0.068)

## Scatter summary (quartile bins of LOO topic similarity)

| Bin | Topic-sim range | n | Top-1 | Median margin | Median d_own |
|---|---|---|---|---|---|
| Q1 | 0.540 - 0.755 | 18 | 88.9% | -0.105 | 0.559 |
| Q2 | 0.755 - 0.854 | 17 | 94.1% | -0.153 | 0.630 |
| Q3 | 0.862 - 0.905 | 17 | 100.0% | -0.192 | 0.519 |
| Q4 | 0.907 - 0.951 | 17 | 100.0% | -0.177 | 0.470 |

## Attribution errors

- mccarthy-cormac / Stella Maris: own rank 13, margin +0.272, topic sim 0.541
- mccarthy-cormac / The Orchard Keeper: own rank 2, margin +0.000, topic sim 0.837
- pynchon-thomas / V.: own rank 2, margin +0.067, topic sim 0.755

## Reading

Within-author content similarity spans 0.411 of cosine (works genuinely differ in subject matter), while LOO attribution stays at 95.7% overall and 88.9% in the LOWEST topic-similarity quartile (works most off-topic for their author). The topic-similarity vs attribution-margin correlation is rho = -0.308 (p = 0.010).

There is a graded coupling: works that are more topically typical of their author also sit closer in MFW Delta. This is expected even under purely stylistic attribution, because topic and style co-drift within a career (and atypical-topic works are often atypical-register works, e.g. a dialogue-only novel). The decisive observation is that attribution does NOT collapse at the off-topic end of the range: MFW identity degrades gracefully with topical atypicality but is not riding topic. Cross-check with the function-words-only probe (zero content words in the vocabulary) to close the loop.
