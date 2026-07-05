# Methodology: The Author-Relative Measurement Space

*Adapted for this research release from ADR-0041 of the parent project
("Author-Relative Measurement Space", 2026-06-09). The parent project's
private corpora and case-study placements are not part of this release;
this document keeps the measurement model, the validation design, and the
recorded results that ship in `reports/`.*

---

## Context

Stylometric "voice distance" systems often measure distance **from a single
privileged origin** — one author's centroid, one register library. Two
failure modes motivated this design:

1. **Origin contamination.** A reference corpus built from heterogeneous
   sources (chat, email, forum text) describes *platform text shapes*, not
   literary voice; clustering silhouettes were statistically
   indistinguishable from noise.
2. **Unanchored σ.** A raw σ-from-origin has no empirical meaning: there is
   no answer to "how far do real authors drift from themselves?" baked into
   the number.

The structural fix: stop measuring from any one origin. Calibrate the
measurement space on **known authors measured relative to each other**,
validate that the features behave correctly on that known material, and
only then place new texts *into* the validated space as observations with
honest confidence bounds.

## The space (`src/author_manifold/author_space.py`)

`AuthorRelativeSpace` calibrates on a **shelf** of known authors:

- **Contemporary gold shelf, wave 1 (11 authors, untranslated, multi-work,
  fiction-only):** DeLillo, McCarthy, Morrison, Whitehead, Saunders,
  Proulx, Didion (fiction), Ishiguro, Ondaatje, Robinson, Pynchon — 59
  fiction-eligible works after body-trim QC and manifest filtering.
- **Wave 2 (translator/mixed-form stress test, 15 authors / 78 works):**
  adds Tokarczuk, Murakami, Sebald, Foster Wallace.
- **Public-domain replication shelf (9 authors / 35 works, shipped in
  full):** Austen, C. Brontë, Dickens, Fitzgerald, Forster, Hawthorne,
  Joyce, Melville, Woolf — every text first published before 1930 and
  redistributable; see `data/pd_shelf/README.md`.

The contemporary raw texts are rights-encumbered and are **not** included
in this release; their derived measurement artifacts (aggregate per-work
feature vectors) are — see `DATA_LICENSES.md`.

Key measurement properties:

- **Pooled normalization.** Dimensions are standardized by shelf-wide
  dispersion, not each author's own small-sample std. Distances are
  symmetric.
- **Calibration distributions.** `W` = within-author distances
  (leave-one-out work→centroid + within-author work pairs, pooled across
  the shelf); `B` = between-author distances. Both persisted with quantiles
  and bootstrap CIs in the artifact JSON.
- **Percentile-calibrated reporting.** A distance is reported as a
  percentile of W and of B ("at p38 of within-author variation") —
  replacing unanchored σ. The number now *means* something: how far this
  text sits relative to how much real authors vary internally versus from
  each other.

## Feature blocks and distance variants

**The D18-only finding (recorded, load-bearing for the research
narrative):** on the clean contemporary shelf, 18 interpretable scalar
stylometric dimensions alone FAIL the validation gates — E1 AUC 0.892
(gate 0.90), silhouette > 0 for only 6/11 authors, E2 LOO top-1 64.4%
(gate 70%) — even though E3 shows all 18 dimensions individually beat the
permutation null (η² 0.45–0.75). Errors concentrate in neighbor pairs
(Proulx↔Whitehead, Morrison→Robinson, McCarthy→Ondaatje). This is a
measured **feature-capacity ceiling**: coarse interpretable scalars
under-determine authorship at work scale.

**The fix:** a Burrows-Delta most-frequent-word block (top-300 shelf MFW,
per-word shelf z-scores, Delta = mean |Δz|), persisted in artifact v1.1.0.
Variant comparison (wave-1 shelf):

| Variant | E1 AUC | Silh.>0 | E2 top-1 | E2 top-3 | Gates |
|---|---|---|---|---|---|
| d18 (18 interpretable dims) | 0.892 | 6/11 | 64.4% | 84.7% | FAIL |
| d18 weighted by E3 η² | 0.913 | 7/11 | 74.6% | 93.2% | FAIL |
| **mfw_delta (selected)** | **0.924** | **9/11** | **94.9%** | **96.6%** | **PASS** |
| combined α=0.3 | 0.933 | 10/11 | 93.2% | 94.9% | PASS |

`mfw_delta` selected as the simplest passing variant. Division of labor:
**MFW Delta carries identity** (who wrote this); **the D18 dimensions carry
interpretation** (how the prose behaves). A function-words-only vocabulary
variant (`--vocab-filter function_words_only`) controls the topic confound;
headline results are robust under it (see
`reports/validation/topic_controls/`).

## Validation experiments (`tools/validate_author_space.py` and companions)

The space is not trusted until these gates pass on the calibration shelf:

| Exp | Question | Gate |
|---|---|---|
| E1 | Do works cluster within-author vs between-author? | pooled AUC ≥ 0.90; silhouette > 0 for ≥ 80% of authors |
| E2 | Does leave-one-work-out attribution recover the author? | top-1 ≥ 70%, top-3 ≥ 85% |
| E3 | Which dimensions actually discriminate authors? | ≥ 6 dims above permutation-null p99 |
| E4 | Where does AI long-form fiction land? | unprompted AI above within-author p90 for every author |
| E5 | Does a translator envelope help? | adopt only if E2-on-wave-2 improves or neutral |
| E6 | Are W/B distributions window-length sensitive? | documented, no gate |
| E7 | Does register clustering methodology validate on a known author? | negative control |

## Recorded results (shipped under `reports/`)

**Wave 2 (contemporary shelf, `reports/validation/wave2/`):** E1 AUC 0.941,
silhouette 14/15; E2 top-1 96.2%. Translator substructure is real
(cross-translator within-author pairs median 0.750 vs same-translator
0.569) but sits well inside the within-vs-between gap — authors survive
translation; stability-weighted distance NOT adopted.

**Public-domain shelf (`reports/validation/pd_shelf/`):** E1 AUC 0.999,
silhouette 9/9; E2 top-1 and top-3 100%; E3 15/18 dimensions above null.
Fully replicable from this repository alone.

**E4 — AI long-form placement: PASS.** 400/400 unprompted samples from 8
models (Claude Fable 5 / Opus 4.8 / Sonnet 4.6 / Haiku 4.5, GPT-5,
GPT-5-mini, Gemma 4 26B, Qwen 3.6 35B) sit off-manifold: nearest-author
W-percentile > 90 for every sample, zero confident misattributions —
although the space was never trained on AI text. Styled samples
(style-prompted + few-shot exemplar): 146/318 land *nearest* their target
(style prompting moves text in the right direction) but **0/318 enter the
target's within-author p90 region**. Statistical treatment (exact
Clopper-Pearson bounds, permutation framings, Holm-Bonferroni registry) in
`reports/validation/wave2/tier1_statistics.md`.

**P5 — human pastiche baseline (`reports/validation/pd_shelf/`):** Brinton's
*Old Friends and New Fancies* (1913), the first published Austen pastiche:
33/37 chunks land nearest Austen, **0/37 enter her within-author p90
region** — a dedicated human imitator shows the same
approach-without-entering signature as the LLMs, and the instrument's
reading matches the critical consensus on the work.

**E6 — length sensitivity.** MFW attribution: 94.9% top-1 at full-work
scale → 85.4% @3,000w → 74.2% @1,500w → 56.3% @800w. **Constraint: W/B
percentile claims below ~1,500 words carry an explicit unreliability
caveat; short texts are placed on ≥3,000-word concatenated chunks.**

**E7 — clustering methodology control: DOES NOT VALIDATE** (the negative
result this control existed to catch). A D18-feature KMeans register
pipeline run on DeLillo — an author with textbook-visible stylistic
phases — finds none of them (silhouette 0.142, cluster-vs-period ARI ≈
chance). Binding consequence in the parent project: register re-clustering
stays blocked pending a methodology that passes this control.

## What this is NOT

This instrument is **not an AI detector**. It answers "does this text sit
inside a specific author's measured manifold?" — a calibrated authorship
question. AI text landing off-manifold is a *measured placement*, not a
detection verdict; human text by an uncalibrated author also lands
off-manifold. See `docs/TIER1_PAPER_OUTLINE.md` for the claim framing.

## AI long-form corpus (E4 substrate)

`tools/generate_ai_longform_corpus.py` generates matched ~3,500-word
literary fiction excerpts under shared scenarios and four conditions
(unprompted, style-prompted, paraphrase, few-shot exemplar) across Claude,
OpenAI, and local Ollama models. Uniform generation config (no sampling
params, no thinking). Output: `data/ai-longform/` + `manifest.jsonl` —
fully owned content, released CC0 (see `DATA_LICENSES.md`). Note: the
exemplar condition's in-context excerpts come from rights-encumbered
contemporary novels; regenerating that condition requires your own copies
of the works (the *generated samples* ship; the excerpts do not).
