# PAN'25 Generative AI Detection — W/B Placement Benchmark Appendix

> *Release note: local path prefixes and personal-corpus identifiers were redacted from this frozen file for publication; all numeric content is unchanged.*

- Generated: 2026-06-10T19:48:10.313778+00:00
- Tool: `backend/pipeline/tools/pan_benchmark_placement.py` (seed 20260610)
- Artifact: `data/baselines/voice/author_space/author_space_v1_wave2.json` (15 calibrated authors, Burrows Delta over 300 MFW, `mfw_delta` variant)
- Robustness artifact: `data/baselines/voice/author_space/author_space_v1_wave2_fwonly.json` (function-words-only MFW vocabulary)
- Data: `validation/datasets/pan25_task1/processed/val.jsonl [local path prefix redacted]` — PAN'25 Task 1 (Voight-Kampff Generative AI Detection), Zenodo 14962653; local processed copy verified as the same source package

## Honesty header (read first)

1. **Domain mismatch, by design.** The author space is calibrated on long-form literary fiction (15 authors, 78 works). PAN task 1 mixes fiction (1837), news (1087), and essays (665) at an average of 608 words per text. Nothing was tuned on PAN data.
2. **The benchmark sits below our design regime.** 89% of texts are <800 words and 99% are <1500 words — below the measured length floor where E6 showed attribution becomes unreliable (top-1 56.3%, W-vs-B AUC 0.686 at 800-word windows). The per-bin degradation pattern below is therefore the expected behaviour of the method, demonstrated on PAN's benchmark: a boundary characterization, not a competitive entry.
3. **Our method is not a binary detector.** It reports calibrated placement (W/B percentiles) in an author space. For this appendix it is adapted transparently: score = nearest-author distance; pre-declared direction (from E4): AI sits farther off the human manifold, so higher = AI. The pre-registered operating point is the E4 off-manifold gate (nearest-author W-percentile > 90), fixed before any PAN text was scored. The "@opt" columns are the in-sample-optimal F1 threshold — an upper bound for context, not a claim.

## Dataset

- Split: `val.jsonl` of the PAN'25 task 1 train package (the official test set is withheld by the organizers)
- n = 3589 (1277 human / 2312 AI from 22 generator models)
- Words/text: mean 608, median 616, max 2892
- Length bins: <800: 3195, 800-1500: 359, 1500-3000: 35, >3000: 0

## Results — primary artifact (wave-2, top-300 MFW)

**Overall ROC AUC = 0.439** (n=3589; AUC 0.5 = chance; direction fixed a priori).

| Length bin | n | n human | n AI | ROC AUC | Acc @W-p90 | F1 @W-p90 | Acc @opt | F1 @opt |
|---|---|---|---|---|---|---|---|---|
| overall | 3589 | 1277 | 2312 | 0.439 | 0.644 | 0.784 | 0.653 | 0.788 |
| <800 | 3195 | 1094 | 2101 | 0.402 | 0.658 | 0.793 | 0.657 | 0.793 |
| 800-1500 | 359 | 156 | 203 | 0.570 | 0.565 | 0.722 | 0.604 | 0.738 |
| 1500-3000 | 35 | 27 | 8 | 0.856 | 0.229 | 0.372 | 0.800 | 0.696 |
| >3000 | 0 | 0 | 0 | — | — | — | — | — |

Median nearest-author distance (human vs AI) per bin — the raw separation behind the AUC:

| Length bin | median dist (human) | median dist (AI) |
|---|---|---|
| <800 | 2.390 | 2.319 |
| 800-1500 | 2.140 | 2.183 |
| 1500-3000 | 1.690 | 2.044 |
| >3000 | — | — |

### Secondary stratification: genre (domain-mismatch lens)

| Genre | n | n human | n AI | ROC AUC | Acc @W-p90 | F1 @W-p90 | Acc @opt | F1 @opt |
|---|---|---|---|---|---|---|---|---|
| essays | 665 | 132 | 533 | 0.239 | 0.802 | 0.890 | 0.800 | 0.889 |
| fiction | 1837 | 928 | 909 | 0.403 | 0.495 | 0.662 | 0.495 | 0.662 |
| news | 1087 | 217 | 870 | 0.576 | 0.800 | 0.889 | 0.831 | 0.904 |

### Reading

1. **AUC recovers monotonically with length** (0.402 → 0.570 → 0.856 across the populated bins), tracking the E6 length-floor curve. In the only bin at/above the floor (1500-3000 words, n=35 — small), the pre-declared direction holds: median nearest-author distance 1.690 (human) vs 2.044 (AI).
2. **Below the floor the direction inverts** (AUC < 0.5 in the <800 bin): short human texts land *farther* from the literary manifold than short AI texts. This is consistent with E6's mechanism (small-sample noise inflates every distance, hitting heterogeneous human texts hardest) plus genre: the inversion is strongest for essays (AUC 0.239) where LLM outputs' smoothed function-word profiles sit closer to the literary-fiction shelf than the human essays do.
3. **The pre-registered W-p90 gate saturates on this benchmark**: recall 1.000 at precision 0.644 — i.e. virtually every PAN text, human or machine, is off-manifold relative to the 15 calibrated authors. The gate is answering the question it was built for ("is this one of these authors?" — correctly: none of them are) and is therefore uninformative as a binary AI detector here. Its accuracy equals the AI base rate.

## Robustness row — fw-only artifact

Function-words-only MFW vocabulary (same 15 authors). Overall AUC = 0.512 (delta vs primary: 0.073).

| Length bin | n | n human | n AI | ROC AUC | Acc @W-p90 | F1 @W-p90 | Acc @opt | F1 @opt |
|---|---|---|---|---|---|---|---|---|
| overall | 3589 | 1277 | 2312 | 0.512 | 0.644 | 0.784 | 0.654 | 0.788 |
| <800 | 3195 | 1094 | 2101 | 0.491 | 0.658 | 0.793 | 0.660 | 0.794 |
| 800-1500 | 359 | 156 | 203 | 0.566 | 0.565 | 0.722 | 0.627 | 0.744 |
| 1500-3000 | 35 | 27 | 8 | 0.815 | 0.229 | 0.372 | 0.771 | 0.636 |
| >3000 | 0 | 0 | 0 | — | — | — | — | — |

## External baselines

Skipped. External detector envs were availability-checked but not run: each predict_score call subprocess-loads Falcon-7B (30-60s cold start on MPS), putting any meaningful subset far over the 30-minute compute budget, and a background Ollama generation job held the GPU during this run. Re-run with --run-baselines on idle hardware to fill this row.

Availability at run time: Binoculars: ready, Fast-DetectGPT: ready

For published context, PAN'25 task-1 organizer baselines (Binoculars et al.) report ROC AUC ≈ 0.9+ on this data; supervised task submissions exceed that. Our placement method does not compete in this regime and this appendix does not claim otherwise.

## Appendix paragraph (draft, appendix-ready)

To situate the placement method against the dominant short-text benchmark, we evaluated it as a binary scorer on the PAN'25 Voight-Kampff Generative AI Detection task (Zenodo 14962653; validation split, n=3589: 1277 human, 2312 machine texts from 22 generators across essays, news, and fiction; median 616 words). Each text was scored by its nearest-author distance in the 15-author literary-fiction space, with the direction (machine text sits farther off the human manifold) and the operating threshold (within-author p90) fixed a priori; nothing was tuned on PAN data. Overall ROC AUC was 0.439 (function-words-only vocabulary: 0.512). Stratified by length, AUC recovered monotonically: 0.402 (n=3195) below 800 words, 0.570 (n=359) at 800–1,500 words, and 0.856 (n=35) at 1,500–3,000 words. The benchmark contains no texts above 3,000 words, and 89% of it sits below 800 words — under the length floor at which our own calibration experiments (E6) already show attribution becoming unreliable. Below that floor the pre-declared direction in fact inverts (AUC < 0.5): short human texts, especially essays, land farther from the literary manifold than short machine texts, consistent with small-sample distance inflation hitting heterogeneous human prose hardest. The pre-registered off-manifold gate saturates — nearly every PAN text, human or machine, is correctly off-manifold relative to the 15 calibrated authors — so it carries no detection signal in this regime. We report these numbers as a boundary characterization rather than a competitive entry: the method is designed for long-form, fiction-register authorship placement, and its degradation (and inversion) on short, mixed-genre texts is the measured edge of that design regime, demonstrated on the field's own benchmark. Purpose-built short-text detectors (e.g., the PAN organizers' Binoculars baseline, AUC ≈ 0.9+ here) remain the right tool in that regime.
