# R3 — Where the Style-Prompting Gap Lives (Dimension-Level Movement)

- Generated: 2026-06-11T08:07:02.756694+00:00
- Space artifact: data/artifacts/author_space_v1_wave2.json (variant: mfw_delta, 15 authors)
- Styled samples analyzed: 236 (conditions: style_prompted, exemplar); matched unprompted cells: 80; skipped: missing_baseline=2, styled_below_min_tokens=82, other_condition=352
- Styled floor: >= 3000 MFW tokens (floor-compliant construction; sub-floor and hard-floor styled samples excluded per §3.7; unprompted matched baselines unfiltered)
- Movement units: pooled-shelf sigma per dimension (MFW row: Burrows Delta over the top-300 shelf vocabulary). Positive = the style-prompted sample sits closer to the target author than the same model's matched unprompted sample(s).

## Reading

Across 236 style-targeted samples, dimensions that survive Holm correction across all 19 tests (sign test, p<0.05): toward the target — repetition_ratio (deliberate word repetition); vocabulary_richness (vocabulary richness); ttr (type-token ratio); sentiment_score (overall sentiment (VADER)); present_ratio (present-tense share); past_ratio (past-tense share); away from it — sentence_cv (sentence-length variability (sentence rhythm)); lexical_density (content-word density); function_word_ratio_extended (function-word share (lexical chassis)); char_ngram_mean (character-trigram texture). Before correction (pilot-scale evidence, confirmatory run = scaled corpus): style prompting moves TOWARD the target on repetition_ratio (deliberate word repetition; +1.15 sigma, p=0.000); vocabulary_richness (vocabulary richness; +0.95 sigma, p=0.000); ttr (type-token ratio; +0.85 sigma, p=0.000); sentiment_score (overall sentiment (VADER); +0.37 sigma, p=0.000); present_ratio (present-tense share; +0.20 sigma, p=0.000); past_ratio (past-tense share; +0.16 sigma, p=0.000). It tends to move AWAY on char_ngram_mean (character-trigram texture; -0.90 sigma, p=0.000); function_word_ratio_extended (function-word share (lexical chassis); -0.38 sigma, p=0.000); lexical_density (content-word density; -0.31 sigma, p=0.000); certainty_index (certainty vs hedging; -0.26 sigma, p=0.011); sentence_cv (sentence-length variability (sentence rhythm); -0.14 sigma, p=0.002); abstract_ratio (abstract vs concrete vocabulary; -0.11 sigma, p=0.031). Note: repetition_ratio, vocabulary_richness, ttr, sentiment_score are length-sensitive dimensions — their movement is real (styled and unprompted samples are length-matched) but their large absolute gaps to novel-length shelf works are partly a length artifact, so closure percentages there understate the shift. The MFW chassis barely budges by contrast: median Delta movement -0.0070 (median gap closure -0.4% vs the unprompted Delta of 1.640). Caricature watch (>=25% of axis-eligible samples overshoot past the target, rel position > 1.25): self_focus_ratio (first-person focus).

## Ranked dimension movement (18 D18 dimensions + MFW chassis)

Bold = significant after Holm correction (sign test, two-sided, alpha=0.05). Overshoot = samples whose relative position along the unprompted->target axis exceeds 1.25 (axis gap >= 0.25 sigma required).

| Dimension | Gloss | Median movement [95% CI] | Frac toward | sign p | Holm p | Median gap closure | Overshoot | Median gap (unprompted -> styled) |
|---|---|---|---|---|---|---|---|---|
| **repetition_ratio** | deliberate word repetition † | +1.153 [+0.984, +1.397] | 0.86 | 0.0000 | 0.0000 | 24% | 1/236 | 5.277 -> 4.022 |
| **vocabulary_richness** | vocabulary richness † | +0.952 [+0.844, +1.128] | 0.86 | 0.0000 | 0.0000 | 20% | 1/236 | 5.189 -> 4.131 |
| **ttr** | type-token ratio † | +0.845 [+0.754, +1.000] | 0.85 | 0.0000 | 0.0000 | 18% | 0/236 | 5.093 -> 4.144 |
| **sentiment_score** | overall sentiment (VADER) † | +0.373 [+0.216, +0.523] | 0.64 | 0.0000 | 0.0003 | 24% | 24/210 | 1.573 -> 1.418 |
| **present_ratio** | present-tense share | +0.201 [+0.071, +0.253] | 0.63 | 0.0001 | 0.0014 | 20% | 39/226 | 1.073 -> 0.925 |
| **past_ratio** | past-tense share | +0.159 [+0.082, +0.243] | 0.62 | 0.0003 | 0.0036 | 15% | 42/226 | 1.116 -> 0.982 |
| paragraph_cv | paragraph-length variability (paragraph rhythm) | +0.138 [-0.028, +0.222] | 0.55 | 0.1715 | 1.0000 | 6% | 8/236 | 2.172 -> 2.016 |
| complexity_score | syntactic complexity | +0.090 [-0.015, +0.238] | 0.56 | 0.1035 | 0.7242 | 18% | 10/211 | 1.108 -> 0.980 |
| self_focus_ratio | first-person focus | +0.027 [-0.038, +0.070] | 0.52 | 0.5581 | 1.0000 | -3% | 61/200 | 1.202 -> 1.157 |
| metaphor_per_100 | metaphor density | +0.021 [-0.130, +0.163] | 0.50 | 0.9481 | 1.0000 | 0% | 37/233 | 1.613 -> 1.737 |
| future_ratio | future-tense share | -0.035 [-0.154, +0.127] | 0.48 | 0.6487 | 1.0000 | -0% | 33/207 | 1.377 -> 1.344 |
| formality_index | formality (latinate register) | -0.088 [-0.223, +0.090] | 0.47 | 0.4740 | 1.0000 | 11% | 35/197 | 0.909 -> 0.973 |
| abstract_ratio | abstract vs concrete vocabulary | -0.114 [-0.213, -0.029] | 0.43 | 0.0315 | 0.2519 | -9% | 34/188 | 0.672 -> 0.865 |
| **sentence_cv** | sentence-length variability (sentence rhythm) | -0.145 [-0.245, -0.084] | 0.40 | 0.0022 | 0.0215 | -13% | 36/226 | 1.101 -> 1.287 |
| certainty_index | certainty vs hedging | -0.259 [-0.407, -0.097] | 0.42 | 0.0110 | 0.0987 | -11% | 28/212 | 1.699 -> 1.803 |
| **lexical_density** | content-word density | -0.309 [-0.401, -0.206] | 0.33 | 0.0000 | 0.0000 | -30% | 39/193 | 0.738 -> 1.130 |
| **function_word_ratio_extended** | function-word share (lexical chassis) | -0.379 [-0.527, -0.227] | 0.36 | 0.0000 | 0.0005 | -25% | 7/212 | 1.812 -> 2.273 |
| **char_ngram_mean** | character-trigram texture | -0.902 [-1.100, -0.765] | 0.22 | 0.0000 | 0.0000 | -32% | 1/210 | 2.055 -> 2.915 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mfw_delta | top-300 MFW Burrows Delta (function-word chassis) | -0.007 [-0.023, +0.020] | 0.49 | 0.8452 | 1.0000 | -0% | n/a | 1.640 -> 1.650 |

## Per-target median movement (top 5 dimensions per target)

- **didion-joan** (n=66): sentiment_score +1.21, repetition_ratio +0.98, vocabulary_richness +0.82, ttr +0.70, present_ratio +0.41; MFW +0.0539
- **mccarthy-cormac** (n=56): repetition_ratio +1.33, vocabulary_richness +1.26, ttr +1.18, past_ratio +0.26, paragraph_cv +0.22; MFW +0.0679
- **morrison-toni** (n=58): repetition_ratio +1.94, vocabulary_richness +1.58, ttr +1.23, sentiment_score +0.49, complexity_score +0.26; MFW -0.0487
- **ondaatje-michael** (n=56): repetition_ratio +0.42, complexity_score +0.36, vocabulary_richness +0.29, ttr +0.20, formality_index +0.16; MFW -0.0345

## Method notes

- Same D18 feature pipeline as the gold shelf (parent-project `generate_baselines.py --tier better` run), normalized with the artifact's pooled shelf_norm; target position = the author's d18 centroid in the artifact.
- Matched baseline = mean per-dimension gap over the same (model, scenario) unprompted samples; with one unprompted sample per cell (pilot) this is the per-sample gap.
- The sign test asks only 'did it move toward the target?' per sample; the bootstrap CI (seeded, n=2000) quantifies how big the median move is.
- Overshoot (rel position > 1.25) flags caricature: the sample moved past the target along the unprompted->target axis (parody literature predicts exaggeration of marked features).
- † marks length-sensitive dimensions (ttr, vocabulary_richness, repetition_ratio, sentiment_score): styled-vs-unprompted movement is length-matched and therefore valid, but their absolute gaps to novel-length shelf works are length-inflated, so closure percentages understate the shift there.
- Caveats: pilot n is small per target; dimensions are not independent (no claim of orthogonality); MFW movement is in Delta units and only the unit-free gap-closure column is directly comparable with the sigma rows.
