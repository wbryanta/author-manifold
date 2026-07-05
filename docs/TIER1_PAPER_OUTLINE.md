# Tier 1 Paper — Working Outline

**Working title:** Approaching Without Entering: Frontier-Model Long-Form
Fiction Measured Against Calibrated Within-Author Variation

**Alt titles:**
- Style Prompting Approaches but Never Enters: Placing LLM Fiction on the
  Author Manifold
- Within-Author Variation as the Yardstick: Long-Form LLM Fiction in an
  Author-Relative Measurement Space

**Status:** outline v0.3 (2026-06-10, scaled-corpus results in).

**Number Freeze v2 (2026-06-10):** the corpus-dependent numbers below are
superseded by `reports/validation/wave2/PRIMARY_ARTIFACT.md` (full 8-model
matrix, 910 placed): off-manifold **400/400**; enter rate **0/318**
(0/159 style + 0/159 exemplar); approach 63/159 style / 83/159 exemplar;
self-attribution 97.8%; R3 MFW closure −1.8%. The v0.3/v0.2 sections are
retained as status history.

**v0.3 scaled-corpus evidence (supersedes pilot numbers in §5 claims):**
- **Enter rate: 0/248** styled samples across 6 API models (Fable 5, Opus
  4.8, Sonnet 4.6, Haiku 4.5, gpt-5, gpt-5-mini) — **including 0/120 in the
  few-shot exemplar condition** (two ~600-word passages of the target author
  in context; the Jemama&Kumar-motivated blocking test). Exemplars improve
  targeting (60% nearest-is-target vs 46% style-only) but never entry.
  Robust: 0/248 under function-words-only vocabulary AND under 3,500-word
  truncation. CP one-sided 95% upper bound on true enter rate ≈ 1.2%
  (combined) / 2.3% (style-only); enter-rate ≥5% rejected (Holm p=1.8e-05).
- **Off-manifold: 333/333** unprompted samples (Holm p≈1.3e-14). Also
  **331/331 off the public-domain shelf** (9 classic authors, gates at AUC
  0.999/100% top-1) — generalizes across two centuries of prose.
- **The human baseline (P5/C2): the claim is now two-sided.** Brinton's
  novel-length 1913 Austen pastiche: 33/37 chunks nearest-is-target (humans
  approach far better than LLMs) yet **0/37 enter Austen's region** —
  matching the 1913 critics ("too fully Victorian to succeed"). Reframe §6
  C2 per the planned contingency: the within-author function-word region is
  a strong identity boundary that neither dedicated human imitators nor
  LLMs cross; what distinguishes humans is approach reliability, not entry.
- **P6 scaled:** model self-attribution 97.6% at n=50/model (chance 12.5%) —
  model lexical signatures are strong and stable at scale.

**Status history:** v0.2 (2026-06-09, post issue-#95 first execution wave).
Evidence base: ADR-0041 + `reports/validation/author_space/` (wave-2 dir is
primary per PRIMARY_ARTIFACT.md). Pre-submission experiments in §10 are
REQUIRED before any claim in §5 is published.

**v0.2 evidence updates (supersede v0.1 guesses where they conflict):**
- **R3 executed (pilot):** style prompting transfers *lexical-diversity
  texture* (repetition_ratio +1.08σ, vocabulary_richness +0.91σ, ttr +0.80σ
  toward target; ~11–17% gap closure) and **caricatures marked features**
  (metaphor, self-focus, certainty, sentiment overshoot >1.25× past target
  in 28–40% of eligible samples — the parody-literature prediction). The
  v0.1 guess that sentence rhythm transfers was WRONG: sentence_cv and
  formality drift away or past (McCarthy target +0.50σ; Fable unprompted
  +2.16σ; style-prompted +3.78σ). MFW chassis: −2.1% closure, coin-flip.
  (`r3_dimension_gap.md`)
- **C1 executed:** both headline findings hold EXACTLY under a 376-word
  closed-class function-words-only vocabulary (0/24 entered; 36/36
  off-manifold; all gates pass). 46.7% of the default top-300 vocabulary is
  content-bearing (incl. character-name leakage) — fw-only becomes the
  primary reported configuration, full-vocab as sensitivity. **The
  cross-family model-proximity ordering is NOT vocabulary-robust** (locals
  reshuffle to nearest under fw-only) — §5 R4 demoted to a caveated
  observation. (`topic_controls/`)
- **C5 executed:** models are NOT narrow-variance authors — within-model
  spread is 1.2–1.5× length-matched human within-author spread; yet LOO
  model self-attribution is 73.7% (chance 16.7%) and family structure is
  visible (Fable↔Opus 0.815, the closest pair). Reframe §6 C5 accordingly.
- **P7 executed:** 0/24 excludes enter-rate ≥11.7% (one-sided 95% CP);
  approach claim Holm-significant (p=0.020); only fable-vs-local ordering
  pairs survive correction. All §5 claims now carry CIs.
- **P9 executed:** novelty narrowed — qualitative "LLMs can't replicate
  style" is published (2025-26); what survives: within-author-percentile
  placement, approach-without-entering shape, ≥3k-word long form, R3
  decomposition, translation bound. MUST cite Mikros 2025 (DSH), Sawant
  2026 (near-scoop of calibrated-baseline framing — narrow our framing
  claim), Jemama & Kumar 2025 (makes the exemplar condition blocking).
  (`tier1_related_work_reconciliation.md`)
- **Generation comparability note:** gpt-5 ignores the ~3,500-word target
  (writes 7.7–9k words). Analysis of cross-model comparisons must
  length-truncate post hoc (longer samples bias closer under Delta).

**Format target:** 8-page conference paper + appendix.
**Venue candidates (ranked):** see §11.

---

## Abstract (sketch, ~180 words)

Whether large language models can write *as* a specific author is usually
tested as a classification problem against detectors. We instead ask the
question the way stylometry asks it of humans: how far is a text from an
author, measured in units of that author's own variation? We build an
author-relative measurement space from N novelists / M novels (v0: 15/78),
calibrated by within-author (W) and between-author (B) distance
distributions under Burrows's Delta over most-frequent words, validated by
leave-one-out attribution (96.2% top-1) and known-author separation gates.
Placing matched ~3,500-word fiction samples from four frontier models
(unprompted and style-prompted "in the manner of" four target authors), we
find: (1) every unprompted sample sits beyond the 98th percentile of
within-author variation — far off the human manifold; (2) style prompting
reliably moves samples *toward* the target author (9/16 nearest-neighbor
hits) but **never into** the target's within-author region (0/16); (3) the
gap is largest at the function-word level, suggesting current models adopt
an author's surface texture while retaining a model-typical lexical
chassis. We release the measurement harness and a public-domain replication
shelf.

---

## 1. Introduction

- The question reframed: not "can a detector tell?" but "where does AI
  long-form fiction *sit* relative to how much real authors vary
  internally?" Percentile-of-within-author-variation as the unit of claim.
- Why long form matters: most LLM-stylometry work operates on short texts;
  craft questions (voice sustained over chapters) live at 3K+ words.
  (Cite repo catalog: nocha / bookworm long-context literary papers.)
- Contributions:
  1. The author-relative measurement space + validation-gate protocol
     (machine-readable pass/fail; negative results retained).
  2. The approach-without-entering finding for style-prompted frontier
     models.
  3. The interpretable-feature capacity ceiling (replication of Delta's
     dominance, reframed as a division of labor: identity vs
     interpretation).
  4. Open harness + public-domain replication shelf + fully-owned AI
     corpus.
- Explicit non-goal framing: this is not an AI detector and makes no
  text-level provenance claims (single-sample, short-length placements
  carry stated unreliability).

## 2. Related work (anchor against `docs/research/papers/` catalog + new sweep)

- Classical attribution: Burrows's Delta lineage; function words as
  identity carriers; cross-topic robustness literature (PAN).
- LLM stylometry / AI-text detection: distinguishability of LLM prose;
  detector arms race; why we sidestep the detector framing.
- LLM author-imitation studies — the contrast class. Some report
  successful imitation that fools attributors (typically short texts /
  classifier framing). Our W/B-calibrated long-form result differs; engage
  directly, explain reconciliations (length, feature family, calibration).
- Human pastiche & parody scholarship (for the §6 human-imitation
  baseline).
- TODO: fresh literature sweep 2025-2026 (LLM style imitation, persona
  prompting, watermark-free attribution) before claiming novelty edges.

## 3. The author-relative measurement space (Methods I)

- Gold shelf construction: manifest-driven corpus discipline (form tags,
  body-trim fidelity, fiction-only centroids); 11 untranslated authors +
  4 translated/mixed-form (wave 2). Rights: novels analyzed as aggregates
  only; nothing redistributed.
- Features: (a) 18 interpretable stylometric dimensions; (b) top-300 MFW
  rel. frequencies, shelf z-scored; distance = mean |Δz| (Delta).
- Calibration: pooled normalization; W (LOO work→centroid + within pairs)
  and B (between-author) distributions with bootstrap CIs; placement
  reported as W/B percentiles.
- Validation gates (the protocol contribution):
  - E1 separation AUC ≥ 0.90 (got 0.924 / 0.941 with wave 2)
  - E2 LOO attribution ≥ 70% top-1 (got 94.9% / 96.2%)
  - E3 per-dimension permutation nulls (18/18)
  - E6 length sensitivity (94.9% → 56.3% from full work to 800w; B/W
    1.61 → 1.06) → the published claim floor: ≥3,000-word placements only.
- **The capacity-ceiling sidebar:** interpretable dimensions all
  individually significant yet collectively fail identity gates (AUC
  0.892, 64.4%); Delta closes it. Framed as replication-with-payoff:
  identity rides on function words; interpretation rides on dimensions.
  (One figure: variant comparison table.)
- E7 negative control (DeLillo register clustering) in one paragraph +
  appendix pointer — establishes the project's control discipline.

## 4. The AI corpus (Methods II)

- Generation protocol: 6 shared scenarios × unprompted + 4 style-prompted
  targets (McCarthy, Didion, Ondaatje, Morrison); ~3,500 words; uniform
  config (no sampling params, no thinking); models: Claude Fable 5, Opus
  4.8, Sonnet 4.6, Haiku 4.5 (+ local Gemma/Qwen; + GPT/Gemini per §10).
- Fully owned corpus → released verbatim.
- Honest scoping: single-prompt design, one generation per cell at v0
  (§10 scales this).

## 5. Results

- **R1 — Unprompted placement:** 24/24 samples beyond W-p98.3 for every
  author; per-model medians (Fable 5 1.525 < Sonnet 1.605 < Haiku 1.632 <
  Opus 1.640). Manifold figure (UMAP, illustrative-only caveat).
- **R2 — Approach without entering:** 9/16 nearest==target (direction
  works: style prompting is doing *something* real) vs 0/16 inside target
  W-p90 (it never completes). Per-target breakdown; distance-ladder
  figure (W median → W p90 → B median → AI medians).
- **R3 — Where the gap lives:** function-word (Delta) gap vs interpretable
  dimension profile of style-prompted samples — which dimensions DO move
  toward the target (surface texture: sentence rhythm, em-dash, metaphor
  density?) vs the MFW chassis that doesn't. (NEW ANALYSIS — cheap, data
  in hand; this is the mechanistic heart of the paper.)
- **R4 — Cross-model:** generational/model ordering with CIs (gated on
  §10 scale-up; v0 n=6/model is reported as pilot only).
- **R5 — Translation bound (secondary):** cross-translator within-author
  pairs (+0.18 Delta) as a human "voice transfer" reference point — even
  *translation* preserves more authorial signal than style prompting
  achieves. (Potentially the paper's best one-liner; verify framing.)

## 6. Controls and robustness (REQUIRED, see §10)

- **C1 Topic confound:** scenarios ≠ authors' actual subject matter; MFW
  top-300 is mostly-but-not-purely function words. Controls: (a) re-run
  with function-words-only vocabulary (strip content words); (b)
  PAN-style cross-topic check using repo infrastructure; (c)
  scenario-matched human texts if obtainable.
- **C2 Human-imitation baseline:** can humans enter another author's
  region? Published pastiche/parody + (stretch) commissioned MFA
  imitations. If humans sometimes enter and models never do, the claim
  sharpens; if humans also never enter, reframe as "imitation is hard,
  period" (still publishable, weaker).
- **C3 Prompt sensitivity:** k prompt paraphrases per cell; exemplar-laden
  prompts (few-shot passages of the target author in-context) as the
  strongest imitation condition — if in-context exemplars still don't
  enter, the finding is much stronger.
- **C4 Length sensitivity of the finding** (not just of attribution):
  does the style-prompted gap shrink at 10K+ words? (Cheap with current
  harness.)
- **C5 Self-consistency:** within-model "author" coherence — do a model's
  own samples cluster like an author (its own W distribution)? (Likely
  yes and tight — "LLMs are authors with narrow variance" is a quotable
  secondary result.)

## 7. Discussion

- Function-word inertia: style prompting transfers texture, not chassis;
  implications for "engineering weaknesses out into craft" (revision
  loops vs prompting; connect to the manuscript case study in one paragraph,
  pointer to companion essay).
- What percentile-calibrated claims buy over detector scores
  (interpretability, falsifiability, no arms race).
- What this does NOT show: not a detector; not "AI can never imitate"
  (statement is model+condition+length-bound); not robust to deliberate
  MFW-targeted adversarial mimicry (future work).

## 8. Limitations

15-author shelf; Anglophone literary fiction only; translation conflates
translator+author (quantified, §5 R5); single-prompt family at v0; no
human-imitation baseline at v0 (→ §10); UMAP figures illustrative;
generation configs uniform but vendor-default-dependent.

## 9. Reproducibility & release

- Public-domain replication shelf (8-10 classic authors) so reviewers can
  run E1-E4 end-to-end without rights-encumbered texts.
- Release: harness code, AI corpus (fully owned), artifact JSONs
  (aggregates only for contemporary authors), manifold report HTML.
- Disclosure note: system and study built in human-AI collaboration
  (Claude); models under study include the collaborating model family —
  state plainly, discuss conflict-of-interest handling (fixed gates
  pre-registered in ADR-0041 before E4 ran; multi-vendor models added).

## 10. Pre-submission experiment checklist (blocking — tracked in issue #95)

| # | Item | Status | Est. effort |
|---|---|---|---|
| P1 | Scale AI corpus: ≥10 scenarios × ≥5 samples/cell × 6-8 models (incl. GPT, Gemini) | pilot done (Claude×40, local in flight) | 2-3 days + API spend |
| P2 | R3 dimension-level gap analysis (which dimensions move, which don't) | not started (data in hand) | 1 day |
| P3 | C1 topic controls (function-word-only vocab + cross-topic) | infra exists | 1-2 days |
| P4 | C3 prompt sensitivity incl. few-shot exemplar condition | not started | 1-2 days |
| P5 | C2 human pastiche baseline (corpus acquisition!) | not started | open-ended; minimum viable: published parody anthologies |
| P6 | C5 model self-consistency W distributions | not started | 0.5 day |
| P7 | Statistical treatment: permutation tests for enter-rate, CIs on model medians, multiple-comparison handling | not started | 1 day |
| P8 | Public-domain replication shelf build + E1-E4 rerun on it | not started | 2-3 days |
| P9 | Fresh related-work sweep (2025-26 imitation literature) + reconcile contrast claims | not started | 1-2 days |
| P10 | Wave-2 artifact as primary (15-author) + freeze all numbers against it | artifact built | 0.5 day |

## 11. Venues

1. **CHR (Computational Humanities Research)** — best fit: methods +
   literary substance + negative-control culture; full paper.
2. **NLP4DH / LaTeCH-CLfL** (ACL workshops) — strong fit, faster cycle.
3. **PAN @ CLEF** — if reframed toward attribution robustness.
4. **ACL/EMNLP main or Findings** — possible with P1-P7 complete and the
   C2/C3 conditions strengthening generality; higher bar, broader reach.
5. arXiv preprint immediately after P1-P3 + P7 regardless of venue.

Companion artifacts: manuscript case-study essay (separate, non-archival);
manifold report HTML linked as demo.

## Figure plan

F1 manifold (UMAP, works + AI overlay) · F2 distance ladder (W/B
quantiles vs AI per condition) · F3 variant table (capacity ceiling) ·
F4 dimension-level movement under style prompting (R3) · F5 length
sensitivity · T1 gates · T2 per-model placement stats · T3 enter-rate
with CIs.
