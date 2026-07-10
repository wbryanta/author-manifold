# R3 — Where the Style-Prompting Gap Lives (Dimension-Level Movement)

- Generated: 2026-06-11T00:48:49.553696+00:00
- Space artifact: data/artifacts/author_space_v1_wave2.json (variant: mfw_delta, 15 authors)
- Styled samples analyzed: 318 (conditions: style_prompted, exemplar); matched unprompted cells: 80; skipped: missing_baseline=2, other_condition=192
- Movement units: pooled-shelf sigma per dimension (MFW row: Burrows Delta over the top-300 shelf vocabulary). Positive = the style-prompted sample sits closer to the target author than the same model's matched unprompted sample(s).

## Reading

Across 318 style-targeted samples, dimensions that survive Holm correction across all 19 tests (sign test, p<0.05): toward the target — repetition_ratio (deliberate word repetition); vocabulary_richness (vocabulary richness); ttr (type-token ratio); sentiment_score (overall sentiment (VADER)); present_ratio (present-tense share); past_ratio (past-tense share); away from it — certainty_index (certainty vs hedging); function_word_ratio_extended (function-word share (lexical chassis)); char_ngram_mean (character-trigram texture). Before correction (pilot-scale evidence, confirmatory run = scaled corpus): style prompting moves TOWARD the target on repetition_ratio (deliberate word repetition; +0.98 sigma, p=0.000); vocabulary_richness (vocabulary richness; +0.83 sigma, p=0.000); ttr (type-token ratio; +0.73 sigma, p=0.000); sentiment_score (overall sentiment (VADER); +0.32 sigma, p=0.000); present_ratio (present-tense share; +0.17 sigma, p=0.000); past_ratio (past-tense share; +0.13 sigma, p=0.001); complexity_score (syntactic complexity; +0.09 sigma, p=0.029). It tends to move AWAY on char_ngram_mean (character-trigram texture; -0.83 sigma, p=0.000); function_word_ratio_extended (function-word share (lexical chassis); -0.39 sigma, p=0.000); certainty_index (certainty vs hedging; -0.20 sigma, p=0.002); lexical_density (content-word density; -0.11 sigma, p=0.029). Note: repetition_ratio, vocabulary_richness, ttr, sentiment_score are length-sensitive dimensions — their movement is real (styled and unprompted samples are length-matched) but their large absolute gaps to novel-length shelf works are partly a length artifact, so closure percentages there understate the shift. The MFW chassis barely budges by contrast: median Delta movement -0.0300 (median gap closure -1.8% vs the unprompted Delta of 1.654). Caricature watch (>=25% of axis-eligible samples overshoot past the target, rel position > 1.25): self_focus_ratio (first-person focus).

## Ranked dimension movement (18 D18 dimensions + MFW chassis)

Bold = significant after Holm correction (sign test, two-sided, alpha=0.05). Overshoot = samples whose relative position along the unprompted->target axis exceeds 1.25 (axis gap >= 0.25 sigma required).

| Dimension | Gloss | Median movement [95% CI] | Frac toward | sign p | Holm p | Median gap closure | Overshoot | Median gap (unprompted -> styled) |
|---|---|---|---|---|---|---|---|---|
| **repetition_ratio** | deliberate word repetition † | +0.975 [+0.860, +1.124] | 0.79 | 0.0000 | 0.0000 | 18% | 1/318 | 5.764 -> 4.591 |
| **vocabulary_richness** | vocabulary richness † | +0.830 [+0.718, +0.909] | 0.78 | 0.0000 | 0.0000 | 15% | 1/318 | 5.575 -> 4.680 |
| **ttr** | type-token ratio † | +0.731 [+0.611, +0.821] | 0.77 | 0.0000 | 0.0000 | 14% | 0/318 | 5.445 -> 4.690 |
| **sentiment_score** | overall sentiment (VADER) † | +0.323 [+0.195, +0.482] | 0.63 | 0.0000 | 0.0001 | 21% | 40/288 | 1.573 -> 1.387 |
| **present_ratio** | present-tense share | +0.174 [+0.054, +0.225] | 0.61 | 0.0002 | 0.0021 | 19% | 46/298 | 1.096 -> 0.974 |
| **past_ratio** | past-tense share | +0.135 [+0.064, +0.200] | 0.59 | 0.0009 | 0.0109 | 14% | 50/298 | 1.232 -> 1.044 |
| paragraph_cv | paragraph-length variability (paragraph rhythm) | +0.115 [-0.016, +0.223] | 0.54 | 0.1299 | 0.7792 | 4% | 8/318 | 2.261 -> 2.230 |
| formality_index | formality (latinate register) | +0.090 [-0.045, +0.262] | 0.54 | 0.1971 | 0.9853 | 20% | 44/278 | 1.034 -> 1.028 |
| complexity_score | syntactic complexity | +0.087 [+0.030, +0.194] | 0.56 | 0.0286 | 0.2572 | 18% | 26/289 | 0.855 -> 0.850 |
| metaphor_per_100 | metaphor density | +0.056 [-0.083, +0.169] | 0.52 | 0.4661 | 1.0000 | 4% | 55/278 | 1.327 -> 1.357 |
| abstract_ratio | abstract vs concrete vocabulary | -0.012 [-0.096, +0.092] | 0.49 | 0.7792 | 1.0000 | 5% | 51/258 | 0.713 -> 0.786 |
| self_focus_ratio | first-person focus | -0.020 [-0.071, +0.043] | 0.48 | 0.5374 | 1.0000 | -5% | 81/268 | 1.202 -> 1.169 |
| future_ratio | future-tense share | -0.063 [-0.144, +0.119] | 0.48 | 0.4661 | 1.0000 | -1% | 43/278 | 1.445 -> 1.490 |
| sentence_cv | sentence-length variability (sentence rhythm) | -0.085 [-0.160, +0.016] | 0.45 | 0.1037 | 0.7262 | -6% | 46/298 | 1.101 -> 1.230 |
| lexical_density | content-word density | -0.113 [-0.215, -0.012] | 0.44 | 0.0286 | 0.2572 | -5% | 59/268 | 0.749 -> 0.895 |
| **certainty_index** | certainty vs hedging | -0.204 [-0.371, -0.104] | 0.41 | 0.0020 | 0.0219 | -7% | 45/288 | 1.699 -> 1.822 |
| **function_word_ratio_extended** | function-word share (lexical chassis) | -0.393 [-0.549, -0.257] | 0.35 | 0.0000 | 0.0000 | -24% | 7/278 | 1.940 -> 2.432 |
| **char_ngram_mean** | character-trigram texture | -0.832 [-0.943, -0.704] | 0.20 | 0.0000 | 0.0000 | -31% | 7/288 | 2.098 -> 2.963 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **mfw_delta** | top-300 MFW Burrows Delta (function-word chassis) | -0.030 [-0.048, -0.013] | 0.42 | 0.0042 | 0.0417 | -2% | n/a | 1.654 -> 1.710 |

## Per-target median movement (top 5 dimensions per target)

- **didion-joan** (n=80): sentiment_score +1.21, repetition_ratio +0.83, vocabulary_richness +0.62, ttr +0.47, present_ratio +0.38; MFW +0.0334
- **mccarthy-cormac** (n=79): repetition_ratio +0.99, ttr +0.99, vocabulary_richness +0.98, paragraph_cv +0.46, sentiment_score +0.22; MFW +0.0584
- **morrison-toni** (n=79): repetition_ratio +1.63, vocabulary_richness +1.30, ttr +1.10, formality_index +0.37, sentiment_score +0.25; MFW -0.0790
- **ondaatje-michael** (n=80): repetition_ratio +0.34, complexity_score +0.25, formality_index +0.24, metaphor_per_100 +0.22, vocabulary_richness +0.18; MFW -0.0673

## Method notes

- Same D18 feature pipeline as the gold shelf (parent-project `generate_baselines.py --tier better` run), normalized with the artifact's pooled shelf_norm; target position = the author's d18 centroid in the artifact.
- Matched baseline = mean per-dimension gap over the same (model, scenario) unprompted samples; with one unprompted sample per cell (pilot) this is the per-sample gap.
- The sign test asks only 'did it move toward the target?' per sample; the bootstrap CI (seeded, n=2000) quantifies how big the median move is.
- Overshoot (rel position > 1.25) flags caricature: the sample moved past the target along the unprompted->target axis (parody literature predicts exaggeration of marked features).
- † marks length-sensitive dimensions (ttr, vocabulary_richness, repetition_ratio, sentiment_score): styled-vs-unprompted movement is length-matched and therefore valid, but their absolute gaps to novel-length shelf works are length-inflated, so closure percentages understate the shift there.
- Caveats: pilot n is small per target; dimensions are not independent (no claim of orthogonality); MFW movement is in Delta units and only the unit-free gap-closure column is directly comparable with the sigma rows.
