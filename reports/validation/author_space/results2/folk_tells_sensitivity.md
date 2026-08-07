# Folk "AI tells": subset and pooling sensitivity of the combined score

*Added 2026-08-06 by the forensic code and data review. The paper's §5.8
headline is that the 12-tell combined score separates AI from celebrated
human prose at **AUC 0.506 [0.377, 0.623]** — a coin flip. The obvious attack
is that a different subset or a different pooling rule would do better. It
would. This file computes those alternatives ourselves, in public, and says
which of them are legitimate tests of the folk claim and which are not.*

**Same configuration as the published result** (paper §5.8): human side =
390 windows of 3,500 words from the 78 contemporary shelf works, 15 authors;
AI side = the 400 unprompted `ai-longform` samples truncated to 3,500 words;
AUC = P(AI > human window), ties 0.5; seed 20260609. The published 12-tell
combined value **reproduces exactly (0.5058)**, which is what makes the rest
of the table comparable.

---

## The framing that decides how to read this table

The folk claim under test is not "some measurable feature separates AI from
human prose." It is the circulating one: **"these are the tells — all of
them indicate AI."** The honest test of that claim is the sum over the whole
circulating list, scored in the folk-claimed direction. That is the published
0.506.

Selecting the subset that scores best **after seeing the labels** tests a
different and much weaker claim: that *some* subset of the list separates.
It always will, and the AUC it reports is inflated by the selection. The
distinction matters here because four of the twelve tells run **backwards** —
celebrated novelists use them *more* than the models do — so dropping them is
a label-dependent move, not a neutral cleanup.

Two entries below are **not** label-dependent and therefore do carry weight:
the a-priori subsets, chosen before looking at any AUC because someone else
had already named them.

---

## Combined-score sensitivity

| Variant | AUC | Label-dependent? |
|---|---|---|
| **Published: z-sum, human-anchored, all 12 tells** | **0.5058** | no — the folk claim as stated |
| Pooled-anchored z-sum, all 12 | 0.4510 | no (pooling choice only) |
| Rank-sum pooling, all 12 | 0.4417 | no (pooling choice only) |
| log1p rates, z-sum, all 12 | 0.4572 | no (pooling choice only) |
| All 12 with a stricter `not_x_but_y` counter | 0.5116 | no |
| Drop the 4 backwards tells (8 forward tells) | 0.6657 | **yes** |
| 8 forward tells + strict `not_x_but_y` | 0.6707 | **yes** |
| Rank-sum pooling, 8 forward tells | 0.6811 | **yes** |
| log1p rates, z-sum, 8 forward tells | 0.6549 | **yes** |
| Only the 3 headline tells (em dash / not X but Y / tricolon) | 0.7056 | **yes** |
| **Only em dash + not X but Y (best pair)** | **0.7343** | **yes** |

Every alternative *pooling* rule applied to the full list lands at or below
the published value (0.44–0.51). The full list is a coin flip under any
pooling; the gains all come from choosing which tells to keep.

## A-priori subsets (chosen without reference to these AUCs)

| Subset | AUC |
|---|---|
| The triple named in this project's own public repository description (em dash / not X but Y / delve-leverage) | **0.7275** |
| Em dash alone | 0.6804 |

These are the load-bearing rows. A subset named in advance, by someone not
looking at the answer, reaches ~0.73 — so **the coin flip is a property of
the full circulating list, not of its best members.** The paper's v0.5.5 text
discloses this directly, and the abstract's "barely separate" should be read
as scoped to the whole list.

## Construct validity of the `not_x_but_y` counter

The counter is a regex, and regexes over-fire. Restricting it to genuine
"not X but Y" reframings — dropping matches whose *but*-clause is a finite
clause, i.e. ordinary negation followed by a new clause — barely moves the
per-tell AUC:

| `not_x_but_y` | AUC |
|---|---|
| As published | 0.6211 |
| Strict (reframing only) | 0.6182 |

**A known defect, documented rather than fixed:** the published counter
measurably overcounts plain negation, and it does so roughly twice as often
on the novelists as on the models — that is, *toward* this paper's own
conclusion that the tells do not single out AI. Because the difference is
0.003 AUC and correcting it would change a published number for no
interpretive gain, the counter is left exactly as it was and the bias is
recorded here. (The paper's v0.5.5 wording drops the word "conservative" for
this reason.)

## Superlative counter: `-est` blocklist gaps

The superlative heuristic blocks common `-est` words that are not
superlatives. Some are missed (`unrest`, `budapest`, `bucharest`,
`palimpsest`, `tempest`):

| Corpus | Unblocked false positives | Total superlative counts | Rate |
|---|---|---|---|
| Human (390 windows) | 8 | 1,506 | 0.53% |
| AI (400 samples) | 11 | 759 | 1.45% |

Under 1.5% either way, and again biased toward this paper's own conclusion
(a slightly inflated AI count would make the tells look *better*, not worse).
Documented, not silently patched.

## The number that matters to a person accused

The tell lists are used to accuse. So the operationally honest question is
not AUC but: **under a realistic accuser's rule — flag a document if *any*
tell exceeds the 95th percentile of celebrated human prose — how many
celebrated novelists get flagged?**

| Tell set | AI flagged | Celebrated human windows flagged |
|---|---|---|
| All 12 | 52.8% | **34.9%** |
| 8 forward tells | 51.7% | **23.8%** |
| 3 headline tells | 44.2% | **12.8%** |

Even the most favourable subset flags about one in eight windows of published
literary fiction while catching fewer than half the AI samples. The subset
choice that maximizes AUC also maximizes the false-accusation rate.

---

## Provenance

Computed 2026-08-06 by the forensic code and data review, re-run
independently for this file against the same corpora and seed as the
published §5.8 result. Because the human side is the rights-encumbered
contemporary shelf, this table cannot be regenerated from this repository
alone — `tools/analyze_folk_tells.py` defaults to the public-domain shelf and
prints a banner saying so. The published 12-tell value reproducing exactly
(0.5058) is the calibration that makes the other rows trustworthy.
