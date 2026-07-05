# E5 — Translator Envelope / Wave-2 Stress Test

- Generated: 2026-06-09
- Wave-2 authors added to the gold shelf: tokarczuk-olga (6 works, 2
  translators), murakami-haruki (7, mixed/under-tagged translators),
  sebald-w_g (3, 2 translators), foster_wallace-david (3, fiction-only).
- Space: 15 calibrated authors, 78 works, distance_variant=mfw_delta.

## Gates with translated/mixed-form authors included: PASS (improved)

| Criterion | Gold shelf (11 authors) | +Wave 2 (15 authors) |
|---|---|---|
| E1 pooled AUC | 0.924 | **0.941** |
| E1 silhouette > 0 | 9/11 | **14/15** |
| E2 LOO top-1 | 94.9% | **96.2%** |
| E2 LOO top-3 | 96.6% | 96.2% |

Translation does not break MFW-Delta attribution. Authors observed through
translators still attribute to themselves; adding them sharpened the shelf.

## Translator substructure (within-author MFW Delta pairs, where tagged)

| Pair type | n | Median Delta |
|---|---|---|
| Same translator, same author | 5 | 0.569 |
| Cross-translator, same author | 8 | 0.750 |
| (Reference: shelf within-author pairs p50) | — | ≈ 0.70 |
| (Reference: shelf between-author pairs p50) | — | ≈ 0.958 |

The translator effect is real (+0.18 median Delta across translators) but
sits well inside the within-vs-between gap: a cross-translator Tokarczuk
pair is still much closer than any cross-author pair. Sebald is the clean
case: Bell-vs-Hulse pairs at 0.560–0.635, tighter than many same-author
same-language pairs on the shelf. (Murakami's translator tags are largely
missing in the manifest — substructure not assessable there; tagging gap
noted for the corpus manifest.)

## Verdict on ADR-0036 Amendment 2 §Q3 (stability-weighted distance)

**Not adopted for identity distance.** The gates pass — and improve — with
translated authors under plain MFW Delta; there is no deficit for stability
weighting to fix. The translator *envelope* (variance metadata, cockpit
display band, `translator-mixed` confidence caveat) is retained as
descriptive surface: the +0.18 cross-translator shift is genuine signal a
reader should see. The `use_stability_weighting` flag in
`influence_adjacency.py` stays default-False, applicable only to the D18
interpretive layer.
