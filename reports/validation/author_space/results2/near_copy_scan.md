# Near-verbatim (substitution-tolerant) leakage scan

*Added 2026-08-06 by the forensic code and data review, lane F. Every prior
leakage audit of this corpus matched **exact** word runs. Exact matching is
defeated by trivial paraphrase: change every eighth word and a copied passage
becomes invisible to it. This scan closes that gap, and finds nothing.*

## What was scanned

All **1,072** released `ai-longform` samples against all **141** in-copyright
novels held locally (the contemporary shelf and its neighbours — the same
text pool every previous audit used), plus a separate pass of every
completion and exemplar sample against **its own prompt slice**, which the
manifest records exactly (completion → the first *n* words of the source
body; exemplar → the recorded excerpt window).

## Method

Shingle-and-align, not exact match:

1. **Candidate generation.** Word-level shingles locate regions where a
   sample and a novel share enough material to be worth aligning, so the
   1,072 × 141 comparison is tractable.
2. **Alignment.** Each candidate region is aligned two ways — a diagonal
   scan and a `difflib` opcode alignment — and scored by **identity**: the
   fraction of aligned token positions that match. A passage with every
   eighth word substituted scores ~88% identity, and is caught; an exact-run
   scan sees only the 7-word fragments between substitutions.
3. **Report thresholds.** A finding is reported at either **≥40 aligned
   tokens at ≥80% identity** or **≥60 aligned tokens at ≥70% identity**.
   These are deliberately below any plausible "substantial passage" bar: a
   40-token span at 80% identity is roughly a long sentence with a word
   changed every five.

## Validation: the scan can actually catch what it claims to

A method that finds nothing is worthless without a positive control, so one
was planted. A 100-token passage was taken from a real novel
(Erdrich, *The Plague of Doves*, at word 40,000), degraded by substituting
every *k*-th token, and inserted into a real corpus sample. The scan was then
run blind against the full novel library.

| Substitution period | Substitutions | True identity | Caught? | Best span found |
|---|---|---|---|---|
| every 8th token | 12 | 88% | **yes** | 100 tokens @ 88% identity |
| every 6th token | 16 | 84% | **yes** | 100 tokens @ 84% |
| every 5th token | 20 | 80% | **yes** | 99 tokens @ 81% |
| every 4th token | 25 | 75% | **yes** | 99 tokens @ ≥70% |

In every configuration the scan recovered the passage **and identified the
correct source novel**. Critically, the prior exact-match scan's longest run
on these same planted passages was **0 words** — none would have been flagged
at the 12-word exact threshold. The gap was real, and this scan closes it.

## Result: clean

**Zero findings at either report threshold**, across all 1,072 samples ×
141 novels (95 s; 0 raw findings before deduplication) and across all 480
(sample, prompt-slice) pairs.

Best-span distribution on the ≥80%-identity track, over all 1,072 samples:

| Best aligned span | Samples |
|---|---|
| 0–19 tokens | 1,062 |
| 20–29 tokens | 9 |
| 30–39 tokens | 1 |
| 40–59 tokens | **0** |
| 60–99 tokens | **0** |
| 100+ tokens | **0** |

The distribution stops well short of the reporting threshold. The single
30–39 token span is the already-disclosed 30-word echo (a traditional song
the source novel itself quotes as an epigraph).

## The 13 known exact echoes are isolated fragments, not visible tips

The sharper question is whether the 13 known exact echoes are the visible
parts of longer near-copies — a 30-word exact run sitting inside a
150-word paraphrase would be a very different finding. It was tested
directly: each known echo was re-aligned against its source with the
substitution-tolerant matcher and allowed to extend in both directions.

**Maximum genuine extension: 7 additional matching words**, on one sample
(`claude-fable-5/completion_didion-joan__s3.txt`, a 13-word exact run). Most
extend by 0–3 matching words, and several by none at all. Where the alignment
column-span extends further (up to 11 columns at the 70% threshold), almost
none of those extra columns actually match — the 30-word Ondaatje echo, the
longest in the corpus, extends by 11 columns of which exactly **1** matches,
a 9% match rate, i.e. noise.

The echoes are isolated fragments. They do not sit inside longer copied
passages.

## Collection-level bound

Pooling **all 40 completion samples per target** and taking the union of
everything recovered, the total coverage of any single source novel is:

| Target novel | Union coverage of the whole novel | Coverage of the 600-word prompt opening | Longest contiguous stretch |
|---|---|---|---|
| McCarthy, *Outer Dark* | 492 / 59,282 = **0.83%** | 69/600 = 11.5% | 14 words |
| Didion, *Democracy* | 387 / 49,253 = **0.79%** | 95/617 = 15.4% | 24 words |
| Ondaatje, *Anil's Ghost* | 274 / 78,584 = **0.35%** | 108/607 = 17.8% | 30 words |
| Morrison, *A Mercy* | 120 / 44,021 = **0.27%** | 19/603 = 3.2% | 9 words |

Even with every sample for a target pooled, under 1% of any novel is
recoverable, in fragments. Reconstruction is not on the table.

Note what the middle column shows: the recovered material concentrates in the
**prompt opening** the models were given, not across the novel. That is the
expected signature of a model continuing from text in its context window,
not of memorization — and it is the basis for the corrected statement in
`DATA_LICENSES.md` (the earlier "no sample reproduces a source prompt"
sentence was wrong and has been removed).

---

## Provenance

Lane F of the forensic code and data review, 2026-08-06, added at the request
of a cross-family adversarial reviewer who observed that every prior audit
was exact-match only. Receipt scripts and raw outputs: the review's
`receipts/laneF/` (`nearlib.py`, `nearscan.py`, `prompt_nearscan.py`,
`control.py`, `known13_profile.py`, `build_index.py`, and their JSON
results). The scan runs against the 141 in-copyright novels, which do not
ship with this release, so it cannot be reproduced from this repository
alone; the method, thresholds, planted-positive validation, and full result
are recorded here so the claim is checkable in substance.
