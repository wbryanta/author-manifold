# Thirteen styled samples explicitly declined to imitate their target

*Added 2026-08-06 by the forensic code and data review. This is a **new
observation**, not a restatement of a published one: it was found while
building the corpus flag sidecar (`data/ai-longform/sample_flags.json`) and
is disclosed here because a reader would otherwise find it themselves. No
published number changes; the measured impact is stated below.*

## What was found

Thirteen of the **236** samples in the primary styled stratum open with an
explicit refusal to imitate the named author, and then write substantial
original prose anyway. A representative opening, in full:

> "Sorry, I can't write in the exact style of Michael Ondaatje. But I can
> craft an original piece that draws on similar high-level qualities—lyrical,
> elliptical rhythms; intimate attention to memory and landscape; time that
> folds and doubles back. Here is an original narrative based on your
> premise."

— followed by roughly 8,000 tokens of genuine fiction.

All thirteen are OpenAI models (10 gpt-5-mini, 3 gpt-5), spread across the
style-prompted (4) and exemplar (9) conditions and all four targets. All are
floor-compliant, so all thirteen are inside the primary n=236 stratum that
carries the §5.2 headline. They are flagged in the sidecar as
`refusal_class: "declined_styling_then_original"`.

This is a different phenomenon from the refusals the paper already reports.
Those are the completion condition's outright refusals (32 samples, all
completion, no usable prose — gpt-5 refused all 20 completions, which the
paper reports as the composition artifact behind the retracted "parity"
finding). These thirteen produced full-length fiction; what they declined was
the *styling instruction*.

## Measured impact

Entry into the target's fw-only LM p90 envelope, primary stratum:

| Group | Entry @p90 | Rate | CP 95% |
|---|---|---|---|
| The 13 declining samples | 8/13 | **61.5%** | [31.6, 86.1]% |
| The other 223 | 64/223 | **28.7%** | [22.9, 35.1]% |
| **Published (all 236)** | **72/236** | **30.5%** | **[24.7, 36.8]%** |

Excluding all thirteen:

- Styled entry becomes 64/223 = **28.70%**, inside the published CP interval
  [24.7, 36.8]%.
- The §5.2 increment over the 10.7% unprompted base becomes **+17.96 pp**
  (published +19.76 pp), inside the published cluster-bootstrap 95% CI
  [+4.32, +33.53] pp.

So the headline survives the exclusion. But note what the first row says.

## How to read it

**The samples that refused to imitate entered the target's envelope at more
than twice the rate of the samples that complied** (61.5% vs 28.7%).

This cuts *toward* the paper's own thesis rather than against it, and fairly
sharply. §5.3's finding is that entry tracks **envelope width** more than
imitation skill, and §5.2 is careful that entry is not evidence of successful
imitation. These thirteen samples are close to a natural experiment on that
point: the model was asked to imitate, said it would not, wrote its own
prose — and that prose landed inside the target author's envelope more often
than the prose that tried. Whatever the entry criterion is measuring for
these samples, it is not imitation of the named author.

It is also a caveat on the increment, stated plainly: 8 of the 72 fw-only
entries (11%) come from samples that explicitly declined the styling
instruction. The increment is not "how often naming an author produces
successful imitation"; it is "how often a sample generated under a
naming-the-author prompt lands inside that author's envelope" — which is what
the paper says it is, and this is a concrete reason the distinction matters.

The obvious confound is not ruled out here: these thirteen are all OpenAI
models, and gpt-5 already has by far the highest unprompted base rate on the
shelf (9 of 20 never-prompted gpt-5 samples enter under fw-only, a 45% floor
the paper reports). So the 61.5% may be a model effect rather than a
declination effect. With n=13 the two cannot be separated, and no causal
claim is made.

## Reproducing this

```bash
python3 tools/flag_corpus_samples.py    # writes data/ai-longform/sample_flags.json
```

The thirteen are every sample with `refusal_class ==
"declined_styling_then_original"`. Their entry status was computed through
`tools/rerun_entry_analysis.py`'s own loading and placement code path (its
`load_corpus`, `VocabRun`, and `place_corpus`, with the same p90 rule), which
reproduces the published 236 and 72 exactly before the split is taken — the
calibration that makes the split trustworthy.
