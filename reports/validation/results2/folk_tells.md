# Folk "AI Tells" vs the Corpora — Document-Level Discrimination

- Generated: 2026-06-11T15:19:29.214228+00:00
- HUMAN: 390 windows of 3500 words (5 seeded non-overlapping windows/work) from the 78 wave-2 shelf works, 15 authors; body offsets per Control Shelf manifest
- AI: 400 unprompted ai-longform samples (8 models), truncated to 3500 words (length symmetry; rates are per 1,000 words)
- Seed 20260609; AUC = P(AI > human window), ties 0.5; CI = seeded author/model cluster bootstrap (2000 resamples)
- Direction: every tell is scored in the folk direction (AI-high). AUC < 0.5 means the tell runs HUMAN-high — flagging on it selects celebrated novelists over machines.

## Main table

| Tell | Human median (IQR) | AI median (IQR) | AUC [95% CI] | Sens @95% spec | Human flagged @50% AI | Most-flagged authors |
|---|---|---|---|---|---|---|
| em_dash | 1.71 (0.29–4.00) | 3.71 (1.83–6.29) | 0.680 [0.483, 0.849] | 20.8% | 28.7% | Pynchon 15/20, Whitehead 14/20, Morrison 29/45 |
| not_x_but_y | 0.00 (0.00–0.29) | 0.29 (0.00–0.57) | 0.621 [0.521, 0.733] | 23.0% | 42.8% | Proulx 13/20, Morrison 29/45, Pynchon 12/20 |
| tricolon | 0.43 (0.29–0.86) | 0.57 (0.29–1.11) | 0.542 [0.416, 0.664] | 5.5% | 50.0% | Sebald 13/15, Robinson 11/15, Murakami 25/35 |
| exclamation | 0.29 (0.00–0.86) | 0.00 (0.00–0.00) | 0.238 [0.160, 0.322] | 0.2% | degenerate† | — |
| lets_opener | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.446 [0.418, 0.472] | 1.8% | degenerate† | — |
| superlative | 0.86 (0.57–1.43) | 0.57 (0.29–0.86) | 0.305 [0.225, 0.386] | 0.5% | 80.0% | Delillo 29/30, Proulx 19/20, Saunders 19/20 |
| delve_leverage | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.496 [0.491, 0.501] | 0.2% | degenerate† | — |
| corporate_jargon | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.496 [0.478, 0.512] | 3.2% | degenerate† | — |
| hedges | 0.57 (0.00–1.14) | 0.29 (0.00–0.69) | 0.410 [0.297, 0.527] | 1.8% | 74.6% | Ishiguro 30/30, Sebald 15/15, Saunders 19/20 |
| staging_adverbs | 0.29 (0.00–0.29) | 0.29 (0.00–0.57) | 0.587 [0.523, 0.649] | 6.2% | 50.3% | Mccarthy 27/40, Foster Wallace 10/15, Morrison 30/45 |
| container_words | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.496 [0.481, 0.511] | 3.0% | degenerate† | — |
| unnamed_consensus | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.484 [0.454, 0.517] | 4.0% | degenerate† | — |
| **combined z-sum** | -0.50 (-2.94–2.37) | -0.52 (-2.41–1.78) | 0.506 [0.377, 0.623] | 5.0% | 50.8% | Ishiguro 24/30, Pynchon 16/20, Morrison 34/45 |

† degenerate: the tell is absent from at least half the AI samples (AI median 0), so the only threshold catching 50% of AI flags every document, human or machine. No witch-hunt number is quotable; the tell simply does not occur often enough in unprompted AI fiction to detect anything.

Tell glosses:

- `em_dash` — em dashes (— plus standalone --)
- `not_x_but_y` — contrastive reframing: 'not X, but Y' / 'not X — it's Y'
- `tricolon` — serial triad 'X, Y, and Z' (1-2 word items; rule-of-three proxy)
- `exclamation` — exclamation marks
- `lets_opener` — sentence-initial 'Let's' / 'Let us'
- `superlative` — superlatives (-est blocklist-filtered; best/worst; most/least+adj)
- `delve_leverage` — 'delve'/'leverage' lemmas
- `corporate_jargon` — fixed corporate-jargon lexicon (synergy, stakeholder, ...)
- `hedges` — fixed hedge lexicon (perhaps, arguably, seemingly, ...)
- `staging_adverbs` — staging adverbs (quietly, softly, gently, profoundly, ...)
- `container_words` — abstract 'space'/'opportunity' frames
- `unnamed_consensus` — unnamed-consensus appeals ('most people', 'studies show', ...)
- `combined z-sum` — sum over all 12 tells of (rate − human window mean) / human window sd

## Per-model median rates (per 1,000 words)

| Tell | human windows | claude-fable-5 | claude-haiku-4-5 | claude-opus-4-8 | claude-sonnet-4-6 | gemma4_26b | gpt-5 | gpt-5-mini | qwen3_6_35b |
|---|---|---|---|---|---|---|---|---|---|
| em_dash | 1.71 | 5.43 | 7.01 | 2.57 | 5.73 | 3.31 | 2.86 | 6.29 | 0.00 |
| not_x_but_y | 0.00 | 0.00 | 0.32 | 0.14 | 0.14 | 0.75 | 0.00 | 0.29 | 0.87 |
| tricolon | 0.43 | 1.14 | 0.30 | 0.86 | 0.57 | 0.95 | 0.29 | 0.29 | 0.61 |
| exclamation | 0.29 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lets_opener | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| superlative | 0.86 | 0.57 | 0.57 | 0.86 | 0.59 | 0.41 | 0.29 | 0.29 | 0.00 |
| delve_leverage | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| corporate_jargon | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| hedges | 0.57 | 0.14 | 0.67 | 0.29 | 0.58 | 0.47 | 0.00 | 0.29 | 0.00 |
| staging_adverbs | 0.29 | 0.29 | 0.34 | 0.29 | 0.29 | 0.00 | 0.29 | 0.29 | 0.33 |
| container_words | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| unnamed_consensus | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## Per-author whole-work medians (per 1,000 words, descriptive)

| Author | works | em_dash | not_x_but_y | tricolon | exclamation | lets_opener | superlative | delve_leverage | corporate_jargon | hedges | staging_adverbs | container_words | unnamed_consensus |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Delillo | 6 | 0.77 | 0.03 | 0.42 | 0.07 | 0.07 | 1.01 | 0.01 | 0.04 | 0.44 | 0.27 | 0.01 | 0.04 |
| Didion | 4 | 1.27 | 0.19 | 0.41 | 0.02 | 0.00 | 0.78 | 0.00 | 0.01 | 0.63 | 0.10 | 0.02 | 0.10 |
| Foster Wallace | 3 | 3.27 | 0.12 | 0.96 | 0.83 | 0.03 | 1.00 | 0.00 | 0.07 | 0.73 | 0.27 | 0.02 | 0.02 |
| Ishiguro | 6 | 0.07 | 0.23 | 0.18 | 0.84 | 0.06 | 1.31 | 0.00 | 0.00 | 1.99 | 0.47 | 0.06 | 0.08 |
| Mccarthy | 8 | 0.38 | 0.02 | 0.08 | 0.03 | 0.13 | 0.66 | 0.00 | 0.00 | 0.43 | 0.27 | 0.00 | 0.03 |
| Morrison | 9 | 4.00 | 0.32 | 0.70 | 0.94 | 0.03 | 0.97 | 0.00 | 0.00 | 0.32 | 0.23 | 0.01 | 0.02 |
| Murakami | 7 | 3.19 | 0.27 | 0.71 | 0.59 | 0.06 | 1.08 | 0.00 | 0.01 | 0.57 | 0.23 | 0.02 | 0.10 |
| Ondaatje | 7 | 2.86 | 0.11 | 0.51 | 0.56 | 0.03 | 0.85 | 0.00 | 0.00 | 0.74 | 0.21 | 0.00 | 0.03 |
| Proulx | 4 | 2.65 | 0.15 | 0.27 | 1.55 | 0.08 | 1.09 | 0.00 | 0.00 | 0.24 | 0.06 | 0.00 | 0.05 |
| Pynchon | 4 | 5.27 | 0.19 | 0.78 | 1.97 | 0.02 | 0.98 | 0.01 | 0.03 | 0.65 | 0.22 | 0.00 | 0.04 |
| Robinson | 3 | 1.71 | 0.16 | 0.67 | 1.30 | 0.06 | 1.40 | 0.02 | 0.00 | 0.40 | 0.18 | 0.00 | 0.05 |
| Saunders | 4 | 1.55 | 0.18 | 0.49 | 3.16 | 0.06 | 1.25 | 0.00 | 0.04 | 0.96 | 0.16 | 0.00 | 0.07 |
| Sebald | 3 | 1.28 | 0.13 | 1.01 | 0.24 | 0.00 | 1.78 | 0.00 | 0.01 | 1.11 | 0.18 | 0.01 | 0.03 |
| Tokarczuk | 6 | 5.21 | 0.24 | 0.97 | 0.53 | 0.04 | 1.37 | 0.00 | 0.00 | 0.89 | 0.28 | 0.04 | 0.07 |
| Whitehead | 4 | 4.52 | 0.19 | 0.93 | 0.56 | 0.01 | 1.03 | 0.01 | 0.00 | 0.34 | 0.07 | 0.03 | 0.05 |

## Out-of-register chat tells (noted, not scored)

Chat-register phrases ('Great question', 'I hope this helps', 'As an AI', ...) cannot occur inside fiction and are noted rather than scored: 0 occurrences in 390 human windows; 0 in 400 AI samples.

## Reading

Of the 12 folk tells, 2 reach AUC >= 0.60 at document level, 6 sit near chance (0.45-0.60), and 4 run materially in the WRONG direction — celebrated human prose is higher on the tell than machine prose (`exclamation` 0.238, `superlative` 0.305, `hedges` 0.410, `lets_opener` 0.446). 6 of the 12 are absent from at least half the unprompted AI samples — too rare in machine fiction to flag anything. The best single tell is `em_dash` (AUC 0.680, catching 21% of AI at 95% specificity); the worst is `exclamation` (AUC 0.238). The combined z-sum over all 12 reaches AUC 0.506 [0.377, 0.623], catching 5% of AI at 95% specificity. The converse is the witch-hunt number: a combined-tell threshold tuned to catch half the machine samples flags 50.8% of 3,500-word windows by celebrated novelists — most often Ishiguro (24/30 windows), Pynchon (16/20 windows), Morrison (34/45 windows).

The em dash, the most-litigated tell, runs human median 1.71/1,000 words vs AI median 3.71 (AUC 0.680; cluster-bootstrap CI [0.483, 0.849] — crosses 0.5 once model/author clustering is respected). Claude-family median 5.58 vs 3.08 for the other models (per-model medians in the table above). An em-dash threshold catching half the AI flags 28.7% of human windows — led by Pynchon (15/20), Whitehead (14/20), Morrison (29/45).

## Method notes

- Conservative operationalizations (documented in `analyze_folk_tells.py`): bounded-span regexes for 'not X, but Y'; 1-2-word-item serial triads only; -est blocklist for superlatives; bare modals excluded from the hedge lexicon; literal 'space'/'opportunity' uses excluded by requiring the framing construction.
- Human windows cluster within author (15 clusters) and AI samples within model (8 clusters); the AUC CI resamples at cluster level.
- Length difference handled by windowing: human works are sampled as 3,500-word windows matched to the AI samples' ~3,500-word target; AI samples are truncated to 3,500 words. Whole-work per-author medians are reported descriptively only.
- 'Sens @95% spec' = share of AI samples above the human-window 95th percentile. 'Human flagged @50% AI' = share of human windows at or above the AI median (the threshold a tell-based detector needs to catch half the machine text).
