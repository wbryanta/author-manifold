# Hostile Statistical Review: `draft_v01.md` ("Approaching Without Entering")

**Reviewer stance**: adversarial by assignment. Every check below was re-computed from the
committed evidence JSONs in this worktree (`reports/validation/**`,
`data/artifacts/*.json`) or from `git log` on this worktree.
Commands were run with the project venv; numbers are reproducible from the cited files.

**Verdict in one line**: the paper's *approach* half survives review (weakened); the
*entry* half — the headline "0/318 never enters" — is, as currently framed, a
**length-calibration artifact**: by the paper's own E6 data, the target authors' own
prose cannot pass the entry criterion at the sample length used. Several secondary
claims (the 0.94% bound, the 89%-vs-52% human contrast, the translation bound, the
−1.8% chassis claim) do not survive honest treatment of clustering, cross-shelf
comparability, or vocabulary controls.

---

## F1. The entry criterion is unsatisfiable at sample length — by the authors themselves

**Severity: FATAL (to the "0/318 enter" framing as stated; repairable by reframing)**

The entry criterion is: target-author distance ≤ W-p90, where W is the **full-novel**
leave-one-out work→centroid distribution (n=78). From the frozen artifact
(`author_space_v1_wave2.json`): W-p90 = **0.800**, W median = 0.579.

The paper's own E6 (`reports/validation/e6_results.json`) measured what
happens when *the shelf authors' own novels* are cut into windows and placed against
their own author centroid:

| Text | distance to own/target author centroid |
|---|---|
| Author's own full novel (W LOO, n=78) | median 0.579, p90 **0.800** |
| **Author's own 3,000-word window** (n=295) | p25 **1.237**, median **1.341**, p75 1.458 |
| Styled AI sample (~3,500 words, n=318) | min 1.170, median 1.710 |

The 25th-percentile *human self-window* (1.237) is **55% above the entry threshold**
(0.800). At ~3,000–3,500 words, essentially **zero** windows of the target author's own
published prose would "enter the target author's within-author region" as the paper
defines it. The criterion the 318 AI samples failed is a criterion **Toni Morrison's own
chapters would fail**. Small-sample distance inflation under Delta (which the paper
itself invokes for PAN, §A, and for self-consistency ratios, §5.6) makes the W-p90
region geometrically unreachable for any window-scale text by anyone.

Direct consequences, all computed:

- "0/318 entered" carries no information about AI-vs-author at this length; the matched
  human "enter rate" is also ~0 (p25 of self-windows is 1.55× the threshold).
- The Brinton pastiche "0/37 entered" (§5.5) is the same artifact: her chunks are 3,000
  words. "Neither dedicated human imitators nor LLMs cross" — neither does Austen,
  chunked at 3,000 words. The Discussion's conjecture that "to enter it is nearly to
  *be* the author" is **directly falsified by E6**: being the author is not sufficient
  to enter at this length.
- The informative, honest comparison is the **distance gap at matched length**: styled
  AI median 1.710 vs human-self-window median 1.341 (and styled AI min 1.170 is *below*
  the human-self-window p25 of 1.237 — 4/318 styled samples are closer to their target
  than a quarter of the target authors' own windows are to themselves; 26/318 = 8.2%
  beat the human-self-window median). That is a real, defensible result — and it is a
  much smaller and two-sided one than "never enters."

**Neutralize**: recalibrate W at sample length (length-matched W distribution from
~3,500-word windows of shelf works — the data already exist in the E6 pipeline) and
restate entry against that. Under a length-matched W-p75 (1.458), entries are no longer
zero (47/318 styled samples sit below it). Alternatively, drop "enter" entirely and
report the matched-length distance gap with the human-self-window distribution as the
explicit yardstick. Anything else is indefensible under review.

---

## F2. "0.94% upper bound" ignores clustering; honest bound is 3–9%

**Severity: MAJOR**

The 318 styled samples are not 318 independent Bernoulli trials. They come from 64
(model × target × condition) cells of ~5 repeated calls each, sharing model, prompt,
scenario, and exemplars. Computed from `wave2/e4_results.json`:

- ICC of target-distance within cells: **0.467**; ICC of the binary nearest-is-target:
  **0.536**. Design effect ≈ **2.9–3.1** → effective n ≈ **102–111**, not 318.
- One-sided 95% CP upper bound for 0 events: n=318 → 0.94% (paper); n_eff=111 →
  **2.7%**; clusters-as-units n=64 → **4.6%**; n=32 → 8.9%.

The paper's §4.5 sentence — "with zero observed events the Clopper–Pearson bound is
unaffected by clustering direction" — is **false**. The point estimate (0) is unaffected;
the *bound* scales as ~3/n_eff and triples-to-quintuples under any honest design-effect
correction. Same for the off-manifold claim: the 99.25% one-sided lower bound becomes
96.3% at the 80 (model × scenario) cluster level (ICC of unprompted distance within
those cells = 0.402) and 68.8% at the model level (8 clusters, all 8 at 50/50).

**Neutralize**: report cluster-robust bounds (cells as units, or beta-binomial /
GEE with exchangeable correlation) alongside the naive CP. The abstract's "(one-sided
95% bound: 0.94%)" must change; "≤ ~5% under cell-level clustering" is what the data
support.

---

## F3. "Pre-registered" gates: same-session, same-actor, minutes-scale; instrument selected after gate failure

**Severity: MAJOR**

Git archaeology on this worktree (all 2026-06-09, CDT):

| Time | Commit | Event |
|---|---|---|
| 13:55 | `1ad20be` | E1–E3 validation harness |
| 14:01 | `188be7c` | **ADR-0041 draft** (gates incl. E4 W-p90) committed **in the same commit as the AI corpus generator** |
| 15:16 | `45c6004` | d18 **fails** all four gates → MFW Delta block added; `variant_comparison.md` generated 15:15, same minute |
| 15:17 | `5bea197` | **E4 runs** (one minute after the instrument changed) |
| 15:35 | `06b7a25` | ADR updated with E4/E6 findings |

Facts a reviewer will extract:

1. The interval between "gates fixed" and "AI text placed" is **76 minutes**, within a
   single working session, by the same human+model pair, with no external registration,
   no timestamped OSF/AsPredicted record. "Pre-registered" (§1, §3.1, Appendix B) is a
   strong word for same-afternoon git commits.
2. The original instrument (D18) **failed** the pre-stated gates. ADR-0041's own risk
   section calls this an "explicit stop rule." The project did not stop: it swapped in
   the MFW Delta block and re-passed within the hour. The §3.6 "pre-stated rule" for
   variant selection ("simplest passing variant wins…") has **no provenance prior to
   the variant results**: it first appears in `variant_comparison.md`, generated
   2026-06-09T20:15:06 UTC, the same minute as the comparison itself. There is no
   committed artifact stating the rule before the d18/mfw/blend numbers were seen.
   Three blend alphas (0.3/0.5/0.7) were also evaluated — a small garden of forking
   paths around the distance definition, none registered.
3. The Holm "confirmatory family" was **edited after results were known**: C1b/C1c
   (per-condition enter rates) were added at freeze-v2 prep (`930b292`, 2026-06-10
   15:14) — after the pilot 0/24 and the scaled 0/248 results (`c695c71`, 10:53) had
   been observed. With p-values at 1e-7..1e-15 this changes no verdicts, but the family
   is demonstrably not pre-registered, so it should not be described as "the full
   confirmatory family… fixed before."
4. Analyses run and *not* in the family: fw-only re-run (built 19:15 on 06-09, after
   the first E4 result at 15:17), truncation re-run, paraphrase battery, PD shelf,
   pastiche, model self-consistency (97.8% LOO), cross-topic Spearman tests, PAN, R3's
   separate 19-test family, plus the exemplar-vs-style contrast (see F6). Several are
   quoted with significance-flavored language in the paper.

**Neutralize**: replace "pre-registered" with "gates fixed in a same-day ADR prior to
E4 execution (76 min; no external registry)" — honest and still worth something. Add
the d18-failure → MFW-swap sequence to the main text (it is currently presented as
"motivated the final distance design rather than emerging from it", §3.6, which a
reviewer with `git log` will read as false: it emerged from gate failure on the data).
Declare the analyses outside the family explicitly as exploratory.

---

## F4. Threshold archaeology: robust at p90–p98 under the primary vocabulary, NOT under the paper's own robustness vocabulary

**Severity: MAJOR**

Sweep computed from the committed JSONs (target W-percentile per styled sample):

| Threshold | primary vocab | truncated | **fw-only** |
|---|---|---|---|
| W-p90 (criterion) | 0/318 | 0/318 | 0/318 |
| W-p95 | 0/318 | 0/318 | **1/318** |
| W-p98 | 0/318 | 0/318 | **37/318** |
| W-p99 | 101/318 | 81/318 | 122/318 |

- Under the **function-words-only vocabulary** — the paper's own topic-confound control,
  §6.1, which it advertises as reproducing the findings "exactly" — a gpt-5 exemplar
  sample (`estate_sale__exemplar_morrison-toni`) sits at target W-percentile **94.87**,
  i.e. **inside W-p95**. The fw-only minimum styled distance is 0.917 vs fw-only W-p90 =
  0.814: a **13% margin**, versus 46% under the full vocabulary (1.170 vs 0.800). The
  controlled vocabulary — the one the paper says carries the identity signal — brings
  the best imitations close to the boundary. "Unchanged under a function-words-only
  vocabulary" (abstract) is true only at exactly p90; at p95 it is false.
- The p99 jump (101/318 under the criterion vocabulary) is driven by a **single outlier**
  in the W LOO reference: max 1.601 vs second-max 1.145 (almost certainly *Stella
  Maris*, which §6.1b names as the most off-style work). 101 styled samples are closer
  to their target than the shelf's most atypical legitimate work is to its own author.
  The honest sentence is "every styled sample is farther than 77 of 78 within-author
  LOO distances" — the paper's resolution discussion (§3.4) gestures at this but never
  states that the styled percentile distribution takes exactly two values (98.72, 100.0).
- W-p90 itself was never registered with a rationale; ADR-0041 (14:01) states it without
  justification, 76 minutes before E4. Why 90 and not 95? At p95 the primary-vocab
  result still holds, so the paper would *strengthen* by reporting the sweep — its
  absence reads as threshold-protective.
- Bootstrap on the threshold (10,000 resamples of the n=78 W LOO): W-p90 95% CI
  [0.718, 0.943]; 0 entries under every resampled p90 (P(any enter)=0.000); at p95,
  P(any enter)=1.1%. The 0/318 is robust to threshold estimation error **under the
  primary vocabulary** — credit where due — but the fw-only fragility stands.
- The choice of W reference distribution is itself favorable: the artifact carries three
  (LOO p90=0.800, pooled p90=0.989, pairs p90=1.084) and the criterion uses the
  strictest. Defensible (sample→centroid matches LOO geometry) but never defended; under
  pairs-W-p95 (1.251), 8/318 styled samples enter.

**Neutralize**: publish the full sweep (p90/p95/p99 × three vocabularies × truncation)
as a table; flag the fw-only p95 near-entry and the single-outlier structure of the W
tail; defend W-LOO as the reference explicitly.

---

## F5. The approach claim's null ignores a designed target–scenario confound

**Severity: MAJOR**

Each imitation target is bound to exactly one scenario *chosen to be adjacent to
gold-shelf territory* (§4.1: "deliberately adjacent… so that placement against the
author manifold is interpretable"). The empirical null (p0=0.1106) crosses the
unprompted nearest-author distribution over **all** scenarios — it never asks what the
unprompted samples on the *same scenario* already do. Computed:

| Target (scenario) | styled nearest-is-target | unprompted nearest-is-target, **same scenario** |
|---|---|---|
| McCarthy (irrigation) | 49/79 = 62.0% | 4/40 = 10.0% |
| Didion (hotel_fire) | 25/80 = 31.2% | 3/40 = 7.5% |
| **Ondaatje (night_ferry)** | 53/80 = 66.2% | **23/40 = 57.5%** |
| Morrison (estate_sale) | 19/79 = 24.1% | 0/40 = 0.0% |

For a quarter of the styled set, the scenario alone already lands nearest-Ondaatje 57.5%
of the time with **no style prompt at all**; the prompting increment is +8.7pp (exact
binomial 53/80 vs p0=0.575: p = **0.070**, not significant). The pooled
scenario-matched null is p0 = 30/160 = **0.1875**, not 0.1106; 146/318 vs 0.1875 still
rejects (p ≈ 2.5e-28 unclustered), so the approach claim survives — but the reported
null is the wrong null, the Ondaatje row is mostly scenario, and the
`tier1_statistics.md` §4 assumption note ("targets that never appear as unprompted
nearest authors (e.g. mccarthy-cormac)") is stale/wrong (McCarthy appears 7/400 times).

Aggravating factors:

- **Per-model heterogeneity is extreme and hidden**: approach rates run gpt-5 75%,
  fable-5 72.5%, opus 65%, sonnet/haiku 50%, qwen 29%, gemma 15%, **gpt-5-mini 10% —
  below the paper's own empirical null of 11%**. "Imitation prompting reliably moves
  samples toward the target" (§5.2) is false for at least one of eight models; the
  abstract's "40–52%" is an average over models that differ by 7.5×.
- Cluster-robust CI on 146/318: cells-bootstrap [36.2%, 55.8%]; model-level bootstrap
  [29.1%, 61.9%]. Significant against any null on offer, but far looser than the CP
  [32.0%, 47.7%] printed.
- The 10 premises were authored within the Claude collaboration (committed in the same
  repo/commit stream by the human+Claude pair; §4.1). Scenario house-style is therefore
  a Claude-family artifact shared by all models' prompts. The observed proximity
  ordering (gpt-5 nearest, Claudes mid) argues against gross pro-Claude leakage on
  distance, but the approach analysis (where fable-5 is 72.5% vs gpt-5-mini 10%) has no
  control for premise–family affinity. Disclose; ideally add premises authored by a
  non-Claude source as a robustness cell.

**Neutralize**: re-state the approach claim against the scenario-matched null per
target; demote Ondaatje; report per-model rates in the main text; disclose premise
authorship.

---

## F6. Exemplar-beats-style is asserted but not supported once clustering is honest

**Severity: MAJOR (it is in the abstract)**

Abstract: "moves samples toward the target — **most strongly with in-context
exemplars**." The supporting contrast is 83/159 vs 63/159. Fisher exact two-sided
p = **0.032** treating samples as independent — and this test is (a) nowhere in the
Holm family, (b) computed on data with within-cell ICC ≈ 0.5. Deflating by the design
effect (≈3) pushes the contrast to p ≈ 0.2. There is no statistically defensible basis
for the abstract's "most strongly" ranking. The 52%-vs-40% difference is also entirely
compatible with two models' behavior (the cluster bootstrap CIs overlap heavily).

**Neutralize**: either run the contrast as a registered, cluster-aware test (GEE or
cell-level permutation) or soften to "directionally higher under exemplars (n.s. under
cluster-robust testing)."

---

## F7. The 89%-vs-52% human-pastiche headline is a three-way unfair comparison

**Severity: MAJOR**

The abstract's "approaching far more reliably (89% vs 52%)" compares:

1. **Different candidate sets**: Brinton 33/37 against **9** PD authors (chance 11.1%)
   vs models against **15** contemporary authors (chance 6.7%).
2. **Different aggregation**: 89% is one (excellent) human imitator; "52%" is the
   exemplar-condition average over eight models. The best models are gpt-5 75% and
   fable-5 72.5% (styled). Chance-adjusted: Brinton 87.8% vs gpt-5 73.2%. The honest
   gap between "a praised human pastiche" and "the best current model" is ~15 points,
   not 89-vs-52.
3. **Uncontrolled vocabulary on the human side only.** The PD top-300 vocabulary is
   137/300 open-class and includes `mr, mrs, miss, sir, lady, dear` — high-frequency
   Austen-register honorifics that saturate a Pride-and-Prejudice continuation (Darcy,
   Lady Catherine, Miss Bennet…). On the contemporary shelf the same concern (46.7%
   open-class, `tengo`) forced a fw-only control under which model approach **drops
   146→85/318 (45.9%→26.7%)**. **No fw-only pastiche run exists**
   (`pd_shelf/` contains no fwonly artifact). The one number that would make the
   comparison fair — Brinton under fw-only — was not computed, while the corresponding
   deflation was computed (and reported) for the models.
4. Different eras/registers: a 1913 Austen-world continuation against an
   1810s-1920s shelf where E1 AUC is 0.999 and E2 is 100% — see F10.

**Neutralize**: run Brinton under a PD fw-only vocabulary (cheap; the artifact builder
exists), report chance-adjusted per-model bests, and confine the human-vs-model contrast
to a like-for-like row. Until then the abstract's "(89% vs 52%)" should not survive.

---

## F8. The translation bound (§5.5, §7) mixes incommensurable length scales

**Severity: MAJOR**

"+0.18 Delta across translators… a fraction of the styled-LLM distances (≥1.3)" compares
**full-novel↔full-novel within-author pair Deltas** (cross-translator median 0.750,
same-translator 0.569; n≈80k-word texts) with **3,500-word-sample→centroid distances**.
E6 shows the author's *own* 3,000-word windows sit at 1.341 from their own centroid —
i.e., the styled-LLM number (median 1.710) is inflated relative to the translation
number by the same length mechanics the paper documents elsewhere. At matched length the
translator-vs-prompting comparison has never been computed; the Discussion's "a
translator preserves more of an author than style prompting achieves" is unsupported as
quantified. (It may well be true; the cited numbers cannot show it.)

**Neutralize**: window the translated works to 3,500 words and recompute the
cross-translator distance distribution at sample scale, or delete the magnitude
comparison and keep the qualitative observation.

---

## F9. The paper violates its own length floor inside the headline n

**Severity: MAJOR**

§3.7: "placements in this paper are made on texts of ≥3,000 words." §7: "below ~1,500
words they license no claims at all." Computed from `e4_results.json` word counts:

- **83/318 styled samples (26%) are below the 3,000-word practice floor.**
- **6/318 styled samples are below the 1,500-word hard floor** — inside the headline
  0/318 — including gemma4 styled samples at median 1,748 words.
- 95/400 unprompted samples are below 3,000 (none below 1,500).

Every sub-floor sample contributes a guaranteed zero to the enter count (shorter ⇒
larger distance ⇒ farther from the region), so the floor violations are all in the
direction that *helps* the headline. The §3.7 parenthetical only concedes gemma4's
"median 1,938" for v2-unprompted; the styled gemma median is 1,748 and the 6 hard-floor
violations are nowhere disclosed. A claim of "no claims below 1,500 words" with 6
sub-1,500 samples in the flagship numerator is a direct internal contradiction.

**Neutralize**: report 0/312 (or 0/229 at the practice floor) as the primary row, with
the full set as sensitivity. The result is unchanged; the hygiene matters.

---

## F10. PD shelf "replication" (AUC 0.999, 100% LOO) shows task triviality, not transfer

**Severity: MINOR (as evidence), MAJOR (as rhetoric)**

A 9-author shelf spanning Austen→Joyce→Fitzgerald separates at AUC 0.999 with 100%
attribution because era, register, and orthographic convention do the work; per-author
silhouettes (0.106–0.419) are modest, meaning even here the clusters are not tight —
the AUC is carried by between-era distances. "331/331 off-manifold" on this shelf is
near-vacuous: contemporary AI fiction is two centuries of register away from Hawthorne.
"0/248 styled entered any author's region" is doubly vacuous since (a) the imitation
targets are not on the shelf and (b) F1's length artifact applies. As a *pipeline*
replication (code runs end-to-end on free data) it is fine; as *evidential* replication
of the headline it is close to content-free, and §9.1's "reproduces the headline result"
overstates.

**Neutralize**: re-describe as an executable-pipeline release plus the pastiche host;
drop "reproduces the headline result across two centuries of prose."

---

## F11. The −1.8% chassis claim is fragile and sign-heterogeneous across targets

**Severity: MINOR-to-MAJOR (it is contribution #3 and in the abstract)**

From `r3_dimension_gap.md`: MFW median movement −0.030 [−0.048, −0.013], sign-test
Holm p = **0.0417** — the last test to survive a 19-test Holm family, with a CI whose
upper end is −0.013 Delta on an unprompted gap of 1.654 (−0.8% to −2.9% closure). And:
**per-target MFW movement is positive for two of four targets** (Didion +0.033,
McCarthy +0.058; §5.3's own text gives the range −0.079..+0.058). "The function-word
chassis moves slightly *away* under imitation pressure" (abstract, §5.3, §7) is an
aggregate-sign claim that flips for half the targets. The pilot measured +0.5%; the
draft calls the sign flip "clarifies rather than contradicts" — that is two looks at
the data narrated as one. The defensible claim is the null-ish one the pilot made:
the chassis is **immobile** (|closure| ≤ ~3% in either direction, against 14–21%
closure for texture dimensions). That contrast is the real finding and is rock-solid;
the directional "moves away" garnish is the weakest link in the paper's mechanism story
and should be cut or demoted to "consistent with zero or slightly negative."

Also note the R3 family (19 tests) is separate from the 33-test confirmatory family;
the abstract presents R3 conclusions at the same epistemic rank as C1–C3.

---

## F12. PAN appendix: the inversion is under-explained and the recovery curve over-read

**Severity: MINOR**

- The "monotonic recovery" rests on a top bin of n=35 (8 AI): AUC 0.856, Hanley-McNeil
  95% CI **[0.68, 1.00]**. Fine as a boundary sketch; not "demonstrated externally"
  (§1, §3.7) — that phrasing claims more than 8 positives can carry.
- fw-only PAN overall AUC = 0.512 (chance). The paper reads this as vindication
  (inversion was content-words). The hostile reading it never engages: if the fw-only
  signal is ~chance below 1,500 words and the full-vocab signal is genre-correlated,
  then the *long-form* signal could likewise be register/genre placement rather than
  authorship. The within-design rebuttal exists (E2 fw-only 92.3% on cross-author,
  same-register material; cross-topic probe §6.1b), so this attack is answerable —
  but the paper should answer it where it raises the PAN inversion, not leave the
  juxtaposition (fw-only ≈ chance on PAN; fw-only carries the headline) unaddressed.
- AUC 0.402 < 0.5 below 800 words means the pre-declared direction is *wrong* there;
  "degrades predictably" (§1) should read "inverts," which §7 does say — keep the
  language consistent.

---

## F13. Generation-protocol confounds (bundle)

**Severity: MINOR each, disclose-and-move-on**

- **qwen exclusions**: the two excluded generations have `word_count: 0` in
  `data/ai-longform/manifest.jsonl` (`irrigation__style_mccarthy-cormac` s4,
  `estate_sale__exemplar_morrison-toni` s5). Genuinely empty output; benign, but the
  criterion ("unusable") was not pre-stated — say "zero-length output" in §4.3 and the
  worry evaporates.
- **"Uniform configuration"** (§4.2) is not uniform: gpt-5-family reasons by default
  (acknowledged), produces 2.4× target length (median 8,246 words), and the Claude
  models had temperature/top_p *removed* while others use provider defaults — three
  decoding regimes described as one. The truncation control handles length for the
  headline; it does not make the configs "uniform." Reword.
- **Truncation artifacts**: cutting an 8k-word piece at 3,500 words mid-arc is a mild
  perturbation for MFW features (function-word rates are approximately stationary), so
  this attack is weak — but say so explicitly rather than leaving it to the reviewer.
- **gemma4 below floor**: see F9.

---

## F14. Version/metadata hygiene

**Severity: NITPICK (but reviewers grep)**

- `e6_results.json` `meta.distance_variant` says **"d18"** while its numbers (top-1
  94.9% full-work) are unmistakably mfw_delta — stale metadata in a load-bearing
  evidence file (predates the `f705de9` routing fix).
- The §3.5 gate table mixes shelves: E3 "18/18" is the 11-author gold shelf, E6 is
  wave-1, E1/E2/E4/E5 are wave-2 — flagged in-cell for E3 only. E3 and E6 were never
  re-run on the frozen 15-author primary artifact.
- `tier1_statistics.md` §4 assumption note about McCarthy never appearing as unprompted
  nearest is factually wrong on the v2 corpus (7/400).
- Four artifacts coexist (`author_space_v1.json`, `_wave2`, `_wave2_fwonly`, `_pd_v1`);
  the manuscript-trajectory rows (parent project) in `PRIMARY_ARTIFACT.md` are pinned to the superseded v1 and
  declared not re-run — acceptable since out-of-family, but the freeze doc should say
  "v1-frozen, do not cite against v2" more loudly than a bullet.
- `tier1_statistics.md` was regenerated 2026-06-11T00:32Z, *after* draft v0.1
  (2026-06-10 20:00Z) — the evidence file postdates the draft that cites it. The
  numbers match; the ordering invites a question that a freeze manifest with hashes
  would close.

---

## F15. Smaller items

- **Percentile granularity honesty (good, but incomplete)**: §3.4 discloses the 1/79
  resolution; it does not disclose that the styled percentile distribution is
  two-valued (98.72/100.0), i.e. the W reference effectively functions as a two-bin
  instrument at these distances. One sentence fixes it.
- **UMAP figure**: declared illustrative in the stub and Limitations — acceptable as
  long as the caption survives editing.
- **Mann–Whitney model pairs**: shared scenarios induce cross-group correlation
  (disclosed in the stats file's assumptions, not in the paper §5.4). Given the
  vocabulary demotion of the whole ordering, consider deleting C4 from the family
  entirely — 28 of the 33 "confirmatory" tests defend a table the paper itself demotes
  to "caveated observation," which makes the family look like Holm-padding.
- **Off-manifold rhetoric**: "no model… produced a single sample that a calibrated
  nearest-author placement would treat as plausibly that author's work" (§5.1) — under
  F1, no *human* sample at this length would be treated as plausibly the author's work
  either. The sentence must be length-qualified.

---

## What survives

To be explicit about what this review does **not** kill:

1. **Off-manifold separation at matched length is real**: styled AI median 1.710 vs
   human self-window median 1.341 — a genuine, large gap a length-matched recalibration
   will preserve (in weakened, honest form: overlap exists; 8.2% of styled samples beat
   the human-self median).
2. **Approach is real** for 3 of 4 targets and 6 of 8 models against the
   scenario-matched null.
3. **The texture-vs-chassis asymmetry** (large closure on lexical-diversity dimensions,
   ~zero on MFW) is the paper's most defensible mechanistic finding — if the "moves
   away" directional claim is dropped.
4. The fw-only and truncation controls were the right controls to run; they merely
   need their own adverse results (p95 near-entry; approach 46%→27%) surfaced rather
   than summarized as "identical."

## Triage table

| # | Finding | Severity | Minimum fix |
|---|---|---|---|
| F1 | Entry criterion unsatisfiable by the author's own prose at sample length | FATAL (reframe) | Length-matched W calibration or drop "enter" |
| F2 | 0.94% bound ignores ICC≈0.5; honest 3–9% | MAJOR | Cluster-robust bounds everywhere |
| F3 | "Pre-registered" = 76-minute same-session git ordering; instrument swapped after gate failure; Holm family edited post hoc | MAJOR | Rewrite provenance claims; disclose d18 failure sequence |
| F4 | fw-only sample inside W-p95; two-valued percentile; outlier-driven p99 | MAJOR | Publish threshold×vocabulary sweep |
| F5 | Approach null ignores designed target–scenario confound (Ondaatje +8.7pp, p=0.07) | MAJOR | Scenario-matched null; per-model rates |
| F6 | "Most strongly with exemplars" unsupported under clustering | MAJOR | Test it properly or soften |
| F7 | 89%-vs-52%: cross-shelf, aggregate-vs-individual, no fw-only pastiche control | MAJOR | Run Brinton fw-only; compare bests |
| F8 | Translation bound mixes novel-scale and sample-scale distances | MAJOR | Recompute at matched window length |
| F9 | 6 styled samples below the paper's own hard floor inside 0/318 | MAJOR | Floor-filtered primary row |
| F10 | PD shelf 0.999/100% = era separation; "replication" rhetoric | MINOR/MAJOR | Reframe as pipeline release |
| F11 | −1.8% chassis: Holm p=0.0417, sign flips across targets and from pilot | MAJOR (abstract) | Claim immobility, not direction |
| F12 | PAN top bin n_AI=8, CI [0.68,1.00]; fw-only≈chance tension unaddressed | MINOR | CIs + genre-attack paragraph |
| F13 | qwen=empty-output (benign), non-uniform "uniform config" | MINOR | Disclose |
| F14 | Stale `d18` metadata; mixed-shelf gate table; post-draft stats regeneration | NITPICK | Freeze manifest with hashes; re-run E3/E6 on wave-2 |
| F15 | Two-valued percentiles; C4 Holm-padding; length-unqualified rhetoric | MINOR | Wording |

*Generated by hostile statistical review, 2026-06-10. All computations reproducible
via PYTHONPATH=backend/core venv python against the committed JSONs; git evidence from
`git log` on this worktree.*
