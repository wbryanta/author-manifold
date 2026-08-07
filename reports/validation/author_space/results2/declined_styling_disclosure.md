# Twenty-one styled samples explicitly declined to imitate their target

*Added 2026-08-06 by the forensic code and data review; **corrected the same
day** after independent verification (see "Correction record" at the end).
This is a **new observation**, not a restatement of a published one: it was
found while building the corpus flag sidecar
(`data/ai-longform/sample_flags.json`) and is disclosed here because a reader
would otherwise find it themselves. No published number changes; the measured
impact is stated below.*

## What was found

Twenty-one of the **236** samples in the primary styled stratum open with an
explicit refusal to imitate the named author, and then write substantial
original prose anyway. A representative opening, in full:

> "Sorry, I can't write in the exact style of Michael Ondaatje. But I can
> craft an original piece that draws on similar high-level qualities—lyrical,
> elliptical rhythms; intimate attention to memory and landscape; time that
> folds and doubles back. Here is an original narrative based on your
> premise."

— followed by roughly 8,000 **words** of genuine fiction.

All twenty-one are OpenAI models (12 gpt-5-mini, 9 gpt-5) — no
Anthropic-family or local model produced one. They span both styled
conditions (14 exemplar, 7 style-prompted) and all four targets, though very
unevenly: Ondaatje 7, McCarthy 6, Morrison 6, Didion 2. All are
floor-compliant, so all twenty-one sit inside the primary n=236 stratum that
carries the §5.2 headline. They are flagged
`refusal_class: "declined_styling_then_original"` in the sidecar.

This is a different phenomenon from the refusals the paper already reports.
Those are the completion condition's outright refusals (32 samples, all
completion, no usable prose — gpt-5 refused all 20 completions, which the
paper reports as the composition artifact behind the retracted "parity"
finding). These twenty-one produced full-length fiction; what they declined
was the *styling instruction*.

## Measured impact

Entry into the target's fw-only LM p90 envelope, primary stratum:

| Group | Entry @p90 | Rate | CP 95% |
|---|---|---|---|
| The 21 declining samples | 13/21 | 61.9% | [38.4, 81.9]% |
| The other 215 | 59/215 | 27.4% | [21.6, 33.9]% |
| **Published (all 236)** | **72/236** | **30.5%** | **[24.7, 36.8]%** |

Excluding all twenty-one:

- Styled entry becomes 59/215 = **27.44%**, inside the published CP interval
  [24.7, 36.8]%.
- The §5.2 increment over the 10.7% unprompted base becomes **+16.70 pp**
  (published +19.76 pp), inside the published cluster-bootstrap 95% CI
  [+4.32, +33.53] pp.

**The headline rate and the increment both survive the exclusion.** That is
the load-bearing result here.

## How to read it — and how not to

The raw contrast (61.9% vs 27.4%) is **not** interpretable as an effect of
declining, because the decliners are not a random subset of the 236. Two
confounds are severe, and both are variables the paper's own §5.2/§5.3
identify as the dominant drivers of entry:

**1. Model family.** Every decliner is an OpenAI model, and OpenAI models
have by far the highest entry rates in the stratum (gpt-5 72.5%, gpt-5-mini
35.0%, against 0–35.9% for the rest). Comparing decliners to the full
non-decliner pool is therefore mostly comparing OpenAI to everyone else.
**Within OpenAI — the only family that produced decliners — the contrast
shrinks to 61.9% (13/21) versus 50.8% (30/59).**

**2. Target envelope width.** Entry rates differ enormously by target
(McCarthy 76.8%, Morrison 24.1%, Didion 13.6%, Ondaatje 10.7%), and McCarthy
is the widest of the four target envelopes (fw-only LM p90 = 1.553). Six of
the twenty-one decliners target McCarthy — over-represented relative to a
pool where McCarthy is 56 of 236.

**Under matching on both, the gap is not distinguishable from composition.**
A stratified permutation test that shuffles the decliner label *within each
(model × target) cell* — so model and target composition are held fixed —
gives a one-sided **p = 0.32** (20,000 draws, seed 20260609) against an
observed +34.5 pp raw difference. There is no evidence here that declining
the styling instruction is associated with higher entry once you account for
which model produced the sample and which author it was aimed at.

**What does survive as a legitimate reading.** These samples are prose that
entered a target author's envelope *without any attempt to imitate that
author* — the model said so in its first sentence. That is a clean
illustration of the paper's own point that **entry is not evidence of
imitation**: the entry criterion is a measurement of where a text sits, and
texts can sit inside an author's envelope for reasons that have nothing to do
with imitating them. It is consistent with §5.3's finding that entry tracks
envelope width, and it is a concrete reason the §5.2 increment must be read
as "how often a sample generated under an author-naming prompt lands inside
that author's envelope" — which is what the paper says — rather than as an
imitation success rate.

No causal claim is made in either direction.

## Reproducing this

```bash
python3 tools/flag_corpus_samples.py    # writes data/ai-longform/sample_flags.json
```

The twenty-one are every sample with `refusal_class ==
"declined_styling_then_original"`. Their entry status was computed through
`tools/rerun_entry_analysis.py`'s own loading and placement code path (its
`load_corpus`, `VocabRun`, and `place_corpus`, with the same p90 rule), which
reproduces the published 236 and 72 exactly before the split is taken — the
calibration that makes the split trustworthy.

*Maintainer note on tokenization:* `flag_corpus_samples.py` strips leading
`#` lines before tokenizing (matching the featurization path);
`rerun_entry_analysis.py`'s `load_corpus` tokenizes the raw file. The
difference is at most 5 tokens (a markdown title line), and **zero** samples
fall on different sides of the 0 / 1,500 / 3,000-token boundaries under the
two conventions, so the stratum is identical either way. Noted so a future
maintainer does not have to rediscover it.

## Correction record

The first version of this file, published earlier on 2026-08-06, reported
**13** samples rather than 21, and framed the raw contrast as "more than
twice the rate" and as "close to a natural experiment" on whether entry
requires imitation.

Both were wrong, and were caught by independent adversarial verification:

- **The count.** The refusal regex required either the word "Sorry" or a
  specific verb object, so it missed eight declinations of the form "I can't
  write in X's exact voice, but here's an original piece…". The pattern
  `i can(?:'|’)?t\s+write\s+in\b` was added and the sidecar regenerated; it
  reclassified exactly those eight samples and nothing else. The earlier
  count also made the claim "all four targets" false (the 13 included no
  Didion sample); at 21 it is true, and the real spread is now given.
- **The framing.** The "natural experiment" reading did not survive matching:
  the decliners are entirely OpenAI and disproportionately McCarthy-targeted,
  and the stratified test above returns p = 0.32. That reading is withdrawn
  and replaced with the confound analysis.

The measured impact on published numbers was unaffected in direction by the
correction — the exclusion rate moved from 28.70% (at 13) to 27.44% (at 21),
both inside the published interval, and the increment from +17.96 pp to
+16.70 pp, both inside the published CI.
