# Cross-target entry matrix (Sec. 8.12 specificity control at the entry level)

*Generated 2026-07-10T16:20:53.953361+00:00 by cross_target_entry_matrix.py; seed 20260609, 2000 bootstrap resamples; frozen corpus and envelopes (provenance in the JSON meta). Positive-control gate: PASS (matched entry reproduces Results 2.0 exactly, pooled + per model, both vocabularies).*

## fwonly @p90 (primary)

| Envelope X | matched k/n (rate) | mismatched k/n (rate) | delta (pp) | delta cluster CI95 (pp) | Fisher p (naive) |
|---|---|---|---|---|---|
| didion-joan | 9/66 (13.6%) | 3/170 (1.8%) | +11.9 | [+1.8, +22.9] | 7.04e-04 |
| mccarthy-cormac | 43/56 (76.8%) | 92/180 (51.1%) | +25.7 | [+3.6, +44.3] | 6.55e-04 |
| morrison-toni | 14/58 (24.1%) | 7/178 (3.9%) | +20.2 | [+4.0, +39.0] | 2.16e-05 |
| ondaatje-michael | 6/56 (10.7%) | 0/180 (0.0%) | +10.7 | [+0.0, +23.3] | 1.44e-04 |

**Paired pooled D = +16.10 pp**, cluster CI95 [+5.05, +27.09] pp (236 samples, 54 cells). Matched pooled 72/236; mismatched naive 102/708 pair-events.

## Unprompted cross-scenario comparator (fwonly @p90)

| Envelope X | unprompted matched-scenario | unprompted cross-scenario | styled mismatched | styled-mm minus unp-cross (pp) | diff CI95 (pp) |
|---|---|---|---|---|---|
| didion-joan | 0/33 | 2/88 (2.3%) | 3/170 (1.8%) | -0.5 | [-4.3, +3.0] |
| mccarthy-cormac | 9/29 | 42/92 (45.7%) | 92/180 (51.1%) | +5.5 | [-13.3, +26.3] |
| morrison-toni | 3/29 | 5/92 (5.4%) | 7/178 (3.9%) | -1.5 | [-7.6, +4.6] |
| ondaatje-michael | 1/30 | 2/91 (2.2%) | 0/180 (0.0%) | -2.2 | [-5.4, +0.0] |

## Sensitivities (fwonly @p90, non-gating)

- Exclude-McCarthy paired D: +13.33 pp, CI95 [+6.80, +21.08] (3 envelopes, 180 samples).
- Threshold-CI sweep: D = +14.12 pp (all-lo) to +11.86 pp (all-hi); matched rate 23.3%-33.5%.
- exemplar: matched 36/112 (32.1%), D = +17.56 pp CI95 [+2.70, +34.29].
- style_prompted: matched 36/124 (29.0%), D = +14.78 pp CI95 [-0.25, +30.77].
- Leave-one-model-out paired D (drop the named model):
    - drop claude-fable-5: D = +16.07 pp, CI95 [+4.30, +28.08] (n=197).
    - drop claude-haiku-4-5: D = +17.35 pp, CI95 [+5.04, +29.71] (n=219).
    - drop claude-opus-4-8: D = +17.18 pp, CI95 [+4.92, +30.64] (n=196).
    - drop claude-sonnet-4-6: D = +17.48 pp, CI95 [+5.08, +30.82] (n=204).
    - drop gpt-5: D = +10.54 pp, CI95 [-1.07, +22.79] (n=196).
    - drop gpt-5-mini: D = +15.82 pp, CI95 [+4.22, +28.28] (n=196).
    - drop qwen3.6:35b: D = +17.95 pp, CI95 [+6.06, +31.31] (n=208).
- Per-model paired D (that model's samples only):
    - claude-fable-5: D = +16.24 pp, CI95 [-17.09, +52.15] (n=39).
    - claude-haiku-4-5: D = +0.00 pp, CI95 [+0.00, +0.00] (n=17).
    - claude-opus-4-8: D = +10.83 pp, CI95 [-10.83, +36.67] (n=40).
    - claude-sonnet-4-6: D = +7.29 pp, CI95 [-4.63, +27.09] (n=32).
    - gpt-5: D = +43.33 pp, CI95 [+17.50, +71.67] (n=40).
    - gpt-5-mini: D = +17.50 pp, CI95 [-11.67, +55.85] (n=40).
    - qwen3.6:35b: D = +2.38 pp, CI95 [-14.94, +23.33] (n=28).

## Secondary replicas

- full-vocab @p90: D = +15.11 pp, CI95 [+4.60, +26.40].
- fwonly @p95: D = +11.58 pp, CI95 [-1.53, +25.15].
- fwonly @p99: D = +11.02 pp, CI95 [-3.94, +26.00].

## Verdict (mechanical, pre-specified)

- Rule: fwonly@p90 only; DELTA_MARGIN=0.099 (=half the +19.8pp headline increment). NON_SPECIFIC if D_hi<margin (precedence, per the 'regardless of sign consistency' clause); else TARGET_SPECIFIC if D_lo>0 AND all four row deltas>0; else MIDDLE_ZONE.
- D = +16.10 pp, CI95 [+5.05, +27.09]; margin 9.9 pp.
- Row deltas (pp): didion-joan +11.9, mccarthy-cormac +25.7, morrison-toni +20.2, ondaatje-michael +10.7
- Predicates: non_specific=False, target_specific=True
- **Branch: TARGET_SPECIFIC**
- Wording consequence: named-target framing stands; Sec. 8.12 gains a resolution sentence citing this matrix

*Scenario caveat: targets are design-bound to scenarios, so mismatched styled samples come from other scenarios by construction; the unprompted cross-scenario column above is the register-only comparator for that confound. fw-only is primary because the closed-class vocabulary blocks cross-target content leakage by design.*
