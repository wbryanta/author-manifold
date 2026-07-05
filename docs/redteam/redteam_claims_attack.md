# Red-Team Claims Attack — draft_v01.md

**Reviewer posture:** hostile empiricist (falsifiable claims only, baselines or it didn't happen) crossed with a prose reviewer who deletes every sentence that survives only because it is vague.
**Scope:** `docs/research/paper/draft_v01.md` (v0.2), checked against `reports/validation/**` evidence JSONs, `wave2/PRIMARY_ARTIFACT.md`, `docs/research/tier1_related_work_reconciliation.md`, and the artifact JSONs under `data/artifacts/`. Every number below was recomputed read-only from the committed artifacts; reproduction snippets are in §10.
**Date:** 2026-06-10.

**Verdict: REJECT in current form.** The instrument, the gate discipline, the controls, and the statistics are genuinely good — better hygiene than most of the literature it cites. But the paper's central interpretive claims (R1 "off-manifold", R2 "never enters", R5 "two-sided identity boundary", and the Discussion's identity conjecture) rest on a length-unmatched calibration that makes the headline events **structurally impossible for any text of the tested length, including the target author's own prose**. I verified this directly: Jane Austen's own novels, chunked exactly like the pastiche, enter Austen's own W-p90 region **0/74** times. The 0/318 result is real arithmetic on a vacuous criterion. Under a length-matched criterion, the paper's human-pastiche contrast *inverts*: Brinton **enters** Austen's matched envelope 35/37 (94.6%) while styled LLMs reach only ~25%. That inverted result is a better paper than the one drafted. Details, severities, and fixes below.

---

## 1. FATAL — The entry criterion is unsatisfiable at sample length; "0/318 never enter" is a calibration artifact, not a finding about imitation

**The claim (Abstract):** "**0 of 318 attempts enter** the target's within-author region (one-sided 95% bound: 0.94%)." **(§5.2):** "0/318 styled samples entered the target author's within-author p90 region." **(§5.5):** the pastiche "likewise never enters."

**The mechanics:** "Entered" = target-author `w_percentile ≤ 90` (`run_e4_ai_placement.py:126-129`), where `w_percentile` is the mid-rank of the sample's Delta distance against the artifact's W LOO distribution — **78 full-novel-to-centroid distances**. The W-p90 entry bar is a distance of **0.7998** (wave-2 artifact) / **0.7790** (PD artifact). Burrows's Delta distances are strongly length-inflated for short texts, which the paper itself measures: E6 (`e6_results.json`) shows own-author **3,000-word windows** sit at median **1.341** from their own author's centroid (p25 = 1.237, p75 = 1.458). The entry bar of 0.80 is roughly 3.5 IQR-widths below the *median* of genuine same-author text at the tested length. No 3,000–3,500-word text by anyone clears it.

**Direct verification (the missing positive control, which I ran):** Austen's five novels, stripped and chunked at ~3,000 words by the *same code path* as the pastiche (`place_pastiche_baseline.py` protocol, PD artifact), every 3rd chunk (n=74), with the source novels **included** in her centroid — i.e., biased *toward* entry:

| Text | n chunks | Entered own/target W-p90 | Median distance to Austen | Median target W-pct |
|---|---|---|---|---|
| **Austen herself** (positive control, not in paper) | 74 | **0/74** | **1.504** | 100.0 |
| Brinton pastiche (paper §5.5) | 37 | 0/37 | 1.537 | 100.0 |
| Forster, chunked (cross-author) | 9 | — | 1.760 | — |
| Brontë, chunked (cross-author) | 10 | — | 1.838 | — |
| Dickens, chunked (cross-author) | 10 | — | 1.924 | — |

Jane Austen cannot enter Jane Austen's within-author region under this criterion. Therefore "0/318 LLM samples entered" and "0/37 pastiche chunks entered" carry **zero information about imitation**. The same defect voids the R1 headline sentence in its strong reading: every Austen self-chunk scores W-pct 100.0, so "no model … produced a single sample that a calibrated nearest-author placement would treat as plausibly that author's work" (§5.1) is a sentence that is also true of Austen writing Austen. The off-manifold gate, at sample length, is a length detector.

**The numbers the paper already contains and does not confront:** gpt-5's unprompted median nearest-author distance is **1.320** (§5.4). Genuine same-author 3,000-word windows sit at median **1.341** (§3.7, same table). The paper prints, two sections apart, that gpt-5's unprompted prose is *numerically closer to its nearest shelf author than shelf authors' own chunks are to themselves*, and never reconciles this with "off-manifold, every sample."

**Robustness battery does not rescue it.** The truncation control (§5.7) truncates the *samples* to 3,500 words but never length-adjusts the *criterion*; truncation makes entry harder, so "unchanged under truncation" is the artifact reasserting itself. The fw-only re-run inherits the same unmatched calibration (fw-only W-p90 bar 0.8143). "Vocabulary-robust, length-robust, and wording-robust" (contribution 2) is robustness of an impossibility.

**What a corrected analysis shows (rough, reproducible):** with a *length-matched* envelope (Austen's own ~3,000-word chunk self-distances; p90 = **1.695**), Brinton's pastiche **enters 35/37 (94.6%)**. On the contemporary shelf, a crude matched threshold (~1.55 from E6 quartiles) admits ~**25%** of styled LLM samples (81/318 at ≤1.55; 63/318 at ≤1.50; 101/318 at ≤1.60). So the defensible recalibrated finding is approximately: *a competent human pastiche enters the length-matched within-author envelope nearly always; styled LLMs enter it roughly a quarter of the time.* Still a strong human–machine asymmetry — but the words "never," "boundary," and "identity" all die.

**Neutralization (fix, mandatory):**
1. Build per-author length-matched W distributions (the E6 windowing machinery already exists) at the sample lengths actually placed; re-state the entry criterion against those. Hold the source work out of the centroid (proper LOO; my Austen control is anti-conservative and still annihilates the current criterion).
2. Re-run E4/R2/R5 against the matched criterion and report whatever comes out, including the likely partial entry of styled samples and the near-total entry of the pastiche.
3. Add the same-author positive control to the protocol permanently: a criterion that the target author's own prose cannot satisfy is not a criterion.
4. Rewrite R1 as a length-matched comparison (unprompted samples vs same-length same-author windows vs same-length cross-author windows). The cross-author window median (1.535) vs styled-to-target median (1.710) is a real, non-vacuous gap — use it.

---

## 2. FATAL — The identity conjecture is contradicted by the paper's own calibration data, in both vocabularies

**The claim (§7):** "We conjecture the within-author function-word envelope is close to constitutive of authorial identity at this feature family — to enter it is nearly to *be* the author." **(Intro, contribution 4):** "The within-author function-word region appears to be an identity boundary that neither dedicated human imitators nor current models cross."

**The base-rate check the paper never ran:** how often does a *real novel by a different shelf author* sit inside an author's W-p90 region at full length (the only length at which the criterion is satisfiable at all)? From the frozen artifacts (`between_author_dist.work_to_centroid` vs the W LOO p90 bar, mid-rank semantics identical to E4's):

| Shelf / vocabulary | Cross-author work→centroid pairs inside W-p90 |
|---|---|
| Contemporary, primary (mixed top-300) | **160/1092 = 14.7%** |
| Contemporary, **fw-only** | **427/1092 = 39.1%** |
| Public-domain shelf | 0/280 = 0.0% |

At full length, one in seven cross-author placements on the primary shelf — and **two in five under the function-words-only vocabulary the paper holds up as the purified identity space** — are *inside* another author's within-author envelope. A DeLillo novel inside Didion's region is not "nearly Didion." E2's own confusion matrix (McCarthy→Murakami, Robinson→Tokarczuk, Whitehead→Pynchon) says the same thing. The region is a useful statistical envelope with a double-digit cross-author false-entry rate; it is not constitutive of anything. And note the direction of the vocabulary effect: stripping content words makes the region *less* identity-exclusive (14.7% → 39.1%), the opposite of what "the function-word envelope is close to constitutive of identity" predicts.

**What would falsify the conjecture, per its own wording?** Any non-target text entering the region. That observation already exists in the paper's own artifact 160 times. The only reason the *experimental* arms never produce it is §1: at sample length nothing can enter. The conjecture is unfalsifiable in the experiments (entry impossible) and falsified in the calibration (entry common). That is the worst possible configuration for a "conjecture."

**The mundane alternative the paper must rule out and doesn't:** "never enters" is fully explained by (a) length-inflated Delta at 3–3.5k words against a full-novel reference distribution, plus (b) nothing else. No identity metaphysics required.

**Neutralization:** delete the conjecture, or restate it as the measured, falsifiable claim the data support after the §1 recalibration — e.g., "under a length-matched criterion, styled LLM text enters the within-author envelope at X%, against a cross-author human base rate of Y% and a dedicated-pastiche rate of Z%." If X < Y (LLM imitations enter *less often than random other authors* do), that is a publishable, startling sentence — and it is checkable from data already on disk.

---

## 3. MAJOR — "Approach" is a rank phenomenon; in the paper's own identity metric, styled samples move *away* from the target

**The claim (Abstract):** "imitation prompting moves samples *toward* the target author — most strongly with in-context exemplars." **(Contribution 2):** "imitation prompting reliably moves samples toward their target (nearest-author hit rates 40–52% …)."

**The evidence:** nearest-is-target rates rise (63/159, 83/159 — verified). But the paper's identity distance does not fall. Recomputed from `e4_results.json`: styled-sample Delta distance to target minus matched-unprompted (same model, same scenario) distance to the same target = median **+0.0295**; only **42%** of styled samples get closer. The paper's own R3 says the same: MFW gap closure **−1.8%**, Holm p = 0.042, *away*. So in the only metric the paper credits with carrying identity, "imitation prompting moves samples toward the target" is **false**; what rises is the *rank* of the target, because prompting pushes samples off their default anchors (Ondaatje 133/400, Proulx 107/400 unprompted) faster than it pushes them anywhere near the target. Repulsion from the model's house voice is being narrated as attraction to the target.

The paper contains both numbers and never reconciles them; the abstract keeps the flattering one. "Most strongly with in-context exemplars" compounds it: exemplars improve the hit *rate* (52% vs 40%) while the median target distance barely moves (1.696 vs 1.715) and the away-drift persists (exemplar median +0.0251).

**Neutralization (fix):** everywhere "moves toward," substitute the supported claim: "raises the target's nearest-neighbor rank (40–52% vs 11% empirical null) without reducing — and at scale slightly increasing — Delta distance to the target." Drop "reliably" (a 40–52% hit rate is not reliability; it is better-than-null). The mechanism section becomes *stronger* under this wording: rank-up + distance-flat is exactly the texture-vs-chassis story.

---

## 4. MAJOR — "The strongest condition the literature implies should succeed" was not tested; completion prompting is missing

**The claim (Contribution 2):** "including all 159 with in-context exemplars, the strongest prompting condition the contrast literature implies should succeed." **(§4.1):** "This is the strongest imitation condition … since text-conditioned imitation is where the literature reports its largest successes [@jemama2025]."

**The evidence file truth:** the reconciliation doc (§1.2) is explicit that Jemama & Kumar's 99.9% figure is for **text completion** — "the model continues the author's own text, inheriting topic, register, and lexical context. This is the easiest possible conditioning and *closest to* our few-shot exemplar condition" — and that the exemplar condition is the *nearest tested proxy*, not the thing itself. Completion conditions the chassis directly (the model's continuation locally inherits the author's function-word stream); few-shot exemplars condition it indirectly. The first reviewer pass will say: the one condition the contrast paper actually used — and the one with a mechanistic reason to move function words — is the one you didn't run. "Strongest … the literature implies should succeed" is therefore an overreach; the literature implies *completion* should succeed, and completion is untested. Jones 2022's generator was likewise completion/fine-tune-shaped, not instruction-prompted (reconciliation §1.1).

**Neutralization:** (a) Run a completion condition (seed each generation with ~500–1,000 words of the target's actual text, score only the continuation) — the generation harness already handles excerpt transmission for exemplars, so this is cheap; or (b) disclose: "the completion condition of [@jemama2025], which conditions the function-word stream directly, is untested here; exemplar prompting is the strongest *instruction-style* condition we test." Pick one; the current sentence is not available.

---

## 5. MAJOR — The 89%-vs-40–52% "approach reliability" comparison is not design-supported

**The claim (Abstract):** "approaching far more reliably (89% vs 52%)." **(§5.5):** "what distinguishes the human imitator is **approach reliability**: 89% nearest-is-target sustained across an entire novel, versus 40–52% for the best-conditioned LLMs."

**The defects, in order of lethality:**
1. **Different shelves, different chance levels.** Brinton's 33/37 is against the 9-author PD shelf (chance ≈ 11.1%, and the genre/period competition for "sounds most like Austen" is thin — Forster is the only other comedy-of-manners-adjacent author). The LLM 40–52% is against the 15-author contemporary shelf (chance ≈ 6.7%) with several stylistically adjacent authors. The rates are not on a common scale; no null-adjusted comparison is offered.
2. **n=1 imitator, one work, non-independent units.** 37 chunks of a single novel by a single author share topic, characters (Austen's own!), period, and register. Reusing Austen's characters and settings drags content-coupled MFW mass toward Austen mechanically — the paper's own §3.3 concedes 46.7% of the primary vocabulary is open-class. The LLM samples are 318 independent generations over 4 targets and 10 scenarios *not* set in the targets' worlds. Sustained-single-work vs independent-samples is a category mismatch dressed as a ratio.
3. **"Far more reliably" generalizes from one pastiche to "human imitators."** §7 then upgrades it to "what distinguishes the human imitator is reliability of approach" — a population claim from n=1.
4. **And per §1, the actually striking Brinton fact is suppressed by the broken criterion:** her median distance to Austen (1.537) is within 2.2% of Austen's own chunk-level self-distance (1.504), and under a matched envelope she *enters* 94.6% of the time. The paper had a human imitator who, on its own instrument, nearly *is* Austen at the chunk level, and reported her as "entering never."

**Neutralization:** report Brinton with null-adjusted rates (vs the PD shelf's empirical unprompted anchor distribution, the same construction as the LLM empirical null), state n=1/single-work/in-world-content caveats in the same sentence as the 89%, and after the §1 recalibration, report her matched-envelope entry rate. Abstract "(89% vs 52%)" must carry the different-shelf caveat or go.

---

## 6. MAJOR — The translation bound is an invalid comparison (and rests on 13 pairs)

**The claim (§5.5):** "Even passage through a translator preserves more of an author's measurable signal than style prompting achieves." **(§7):** "+0.18 Delta across translators, against styled-model gaps an order larger."

**The evidence file truth (`e5_report.md`):** the translator effect is computed from **5** same-translator pairs vs **8** cross-translator pairs — thirteen pairs total, no CI, two authors' translators effectively driving it. The paper cites "+0.18" three times without ever printing n=5/n=8.

**The comparison is also cross-kind and length-confounded:** cross-translator pairs are *full-novel-to-full-novel* Delta (0.750); styled-model "gaps" are *3.5k-word-sample-to-centroid* Delta (~1.7), which §1 shows is dominated by length inflation (genuine same-author text at that length sits at 1.341–1.504). Apples (novel pairs) to length-inflated oranges (short samples). The honest length-matched contrast would be styled samples (1.710) vs same-length same-author windows (1.341) — a gap of ~0.37, not "an order larger" than 0.18.

**Neutralization:** print the pair counts; either drop the translation-vs-prompting sentence or restate it length-matched. The reconciliation doc calls this "an unclaimed one-liner" — it is unclaimed because as currently computed it is unclaimable.

---

## 7. MAJOR — §5.6's "models are wide-variance" ratio collapses at matched length, and the matched data are in the paper

**The claim (§5.6):** within-model spread "1.86×–2.51× the human within-author pair median (0.740)," caveated as partly length inflation; Limitation 10 calls the figures "length-inflated upper bounds."

**The check:** the human reference at *matched* length exists in E6: own-author 3,000-word windows at median 1.341 from centroid (pair-distances run ~1.25–1.3× centroid distances on this shelf, so same-author *pairs* at sample length sit roughly 1.7). Models' within-model pair p50: 1.373–1.855. The matched-length ratio is therefore roughly **0.8×–1.1×** — i.e., the entire 1.86–2.51× headline is plausibly length artifact, not "part of that ratio." Publishing a number you can de-confound with a table you already printed, and choosing the confounded version with a caveat, is the pattern this paper repeats (cf. §1, §6).

**Neutralization:** compute the within-model spread against same-length human window pairs and report that ratio; keep the (true, interesting) 97.8% self-attribution result, which does not depend on the confound.

---

## 8. MAJOR — Disclosure does not neutralize the reflexivity it names

**The claim (Limitation 11):** reflexivity "handled structurally: all gates and thresholds were fixed (ADR-0041) before any AI sample was placed, models from two other families were added, and the full pipeline is reproducible."

**What that covers:** threshold-gaming and family-exclusivity. **What it does not cover:**
1. **Design authorship.** The 10 scenarios, the base instruction, the four "in the manner of X" prompts, the three paraphrases, and the exemplar-selection scheme were written in collaboration with Claude — the family constituting 4 of 8 studied models. Prompt and scenario authorship can shift *all models'* measured placements (scenarios were chosen "deliberately adjacent to gold-shelf territory," §4.1 — chosen by whom, against what alternatives?), and can plausibly differ in efficacy across families (a Claude-drafted instruction may sit closer to Anthropic instruction-tuning distributions). None of this is gate-protected: gates constrain the *criterion*, not the *stimuli*.
2. **Target selection.** Why McCarthy/Didion/Ondaatje/Morrison? Undisclosed. Ondaatje is also the corpus's dominant unprompted anchor (133/400) — the empirical null absorbs this for C3, but the *choice* process is still unstated, and a hostile reader will ask whether targets were picked after seeing pilot anchor distributions.
3. **Cross-model fairness of conditions.** "No extended thinking on Claude" while "gpt-5-family models reason by default; the default is left in place" (§4.2) is a defensible choice, but it is a *disclosed asymmetry*, not uniformity — and §5.4 then reports a cross-model ordering in which the reasoning-enabled family wins. The paper demotes the ordering for vocabulary reasons; it should demote it for configuration asymmetry too.
4. **Who is "we."** Sole human author; the Disclosure should state plainly which artifacts (prompts, scenarios, code, drafts of this paper) the collaborating model produced, since the paper's subject is precisely that model family's stylistic fingerprints.

**Neutralization (disclose):** one paragraph: scenario/prompt provenance, target-selection procedure and timing relative to pilot data, the reasoning-configuration asymmetry as a §5.4 caveat, and an explicit statement that stimuli (unlike thresholds) were not fixed independently of the collaborating model.

---

## 9. The remaining attack surfaces

### 9.1 Detector-frame consistency (MAJOR for one sentence, otherwise defensible)
The non-goal paragraph (§1) and Appendix A's "boundary characterization" framing are internally consistent and unusually honest (reporting AUC 0.439, below chance, on the field's benchmark). Two sentences are not:
- "Its claims are positions in a validated space — **which is precisely what makes them durable where detector scores are not**" (§1). Unsupported prophecy. No evidence in the repo addresses temporal durability of these placements across model generations; the one durability-adjacent fact (pilot→v2 sign flip on R3 gap closure, +0.5%→−1.8%) cuts the other way. Cut, or downgrade to "auditable where detector scores are not."
- "degrades **predictably** below ~1,500 words (we measure exactly how…)" (§1). Appendix A shows the direction *inverts* (AUC 0.402 overall short-bin; essays 0.239). E6 predicted decay toward chance, not inversion; the inversion was discovered post hoc. "Degrades measurably, and below ~800 words inverts" is the true sentence — §7 gets this right ("including below chance, which we report"); §1 does not.
- NITPICK: Appendix A's "Acc @opt / F1 @opt" columns are post-hoc optimal-threshold numbers inside a paragraph claiming "nothing was tuned on PAN data." Label them explicitly as post-hoc references.

### 9.2 Novelty vs the reconciliation doc (MINOR)
"To our knowledge no prior work places long-form machine text against calibrated within-author variation of named authors" survives the catalog: Sawant 2026 calibrates verifier scores (ceiling/floor), not distance percentiles, on anonymous everyday authors; Mikros 2025 is named-author literary imitation but classifier-verdict at 1.4–2k words; Zeng & Nini is forensic LR verification. The hedge is tight. Two obligations from the reconciliation are not yet discharged in the draft: §2.4 must cite Sawant *by name in the contribution paragraph's vicinity* (the doc: "This is the paper a reviewer will wave at us; pre-empt by name" — currently Sawant appears only in skeleton §2.4), and §2 is still a skeleton — a reviewer cannot check stance fidelity against a placeholder. Also note the reconciliation's own command — "do not claim … 'LLMs cannot fully replicate a named author's style' — the qualitative finding is established" — sits uneasily with an abstract whose emotional payload is exactly that qualitative finding; the abstract should foreground the *unit* (percentile-of-W) harder than the *verdict* (never enters), which after §1's recalibration it will have to anyway.

### 9.3 Sentence-level audit — additional overreaches not covered above
| Sentence (location) | Defect | Severity |
|---|---|---|
| "910 **matched** long-form fiction samples (~3,500 words…)" (Abstract, §1) | gpt-5 median 8,246 words, gemma4 1,938 (§4.4). They are matched in *prompt*, not in the property the parenthesis asserts. Say "matched-prompt (~3,500-word target; two models materially non-compliant, §4.4)". | MINOR (abstract-level) |
| "marked features (self-focus, **metaphor**) overshoot into caricature" (Contribution 3; Abstract "marked features overshoot into caricature") | `r3_dimension_gap.md`: only self_focus_ratio crosses the pre-set ≥25% overshoot bar (81/268 = 30.2%); metaphor is 55/278 = 19.8%, below it, and metaphor's overall movement is n.s. (Holm p = 1.0). Also self_focus_ratio's overall median movement is −0.020, n.s. — "overshoot" is a subgroup tail, narrated as a mechanism. §5.3 body is accurate; abstract and contribution 3 are not. | MAJOR (claims its own threshold says no) |
| "with in-context exemplars it finds the right author **more often than not**" (§7) | 52.2% on exemplar only; combined styled 45.9% — less often than not. Quotable smuggle. | MINOR |
| "Style prompting works directionally and **fails terminally**" (§5.2) | "Terminally" asserts permanence; the failure is structural to an unsatisfiable criterion (§1). After recalibration this adverb is indefensible; even before, it is rhetoric. | MINOR |
| "E3 … 18/18 **(gold-shelf run, 11 authors)** … PASS" (§3.5) | The frozen 15-author primary artifact never passed (or ran) its own E3; the gate row imports a pass from a different shelf. §3.5's preamble — "the space is not used … until pre-registered gates pass **on the shelf**" — is therefore not literally true of E3. Re-run E3 on wave-2 (cheap) or flag the row as inherited. | MAJOR (protocol-integrity claim) |
| "the first published Austen imitation (1913)" (Contribution 4) vs "the earliest known Austen continuation" (§5.5) | Two different claims (imitation vs continuation/sequel); the evidence file says "first published Austen pastiche." Pick one term and verify it; "first" claims attract counterexamples. | NITPICK |
| "(one McCarthy→Murakami…)" E2 errors (§3.5) | Verified consistent with confusion matrix; fine. | — |
| "minimum observed 97.4; modal values 98.7 and 100.0" (§5.1) | Verified: min 97.4359; modes 100.0 (215), 98.7 (184). Accurate. | — |
| "empirical null … p0 = 0.1106" (§5.2) | Reconstructed independently from e4_results.json: 0.1106. Accurate, and genuinely conservative. | — |
| Holm family "33 tests: 5 claim rows … plus 28 model-pair orderings" (§4.5) | Paper is right; the *evidence file's own header* (`tier1_statistics.md` §6) says "3 headline claims + 28 model pairs" = 31 ≠ its own 33 rows. Fix the generator's header string. | NITPICK (evidence file) |
| "no prior work…" / CP bounds / 0.94% / ≤1/79 resolution / E6 table / §5.4 medians+CIs / fw-only deltas / paraphrase spreads | All recomputed or checked against JSONs/markdowns; all accurate as numbers. The paper's arithmetic hygiene is excellent. The disease is inference, not computation. | — |

### 9.4 Scenario-topic coupling residual (MINOR)
§6.1's controls are good, but the *approach* metric retains a content path the controls don't close: nearest-is-target under the mixed vocabulary embeds scenario–author topical affinity (irrigation→McCarthy is a designed pairing — "deliberately adjacent to gold-shelf territory"). The fw-only approach rate drops from 146/318 to **85/318** (§5.7) — i.e., **42% of the approach signal is content-word-borne**. The paper reports this number but never says the sentence; §5.2's headline approach claims are all mixed-vocabulary. State plainly: approach under the identity-grade (fw-only) vocabulary is 26.7%, not 45.9%, against the (recomputed-under-fw-only) empirical null.

---

## 10. Reproduction of every number introduced in this review

All from repo root, read-only; venv for the two placement runs.

1. **Cross-author full-work entry base rates** (artifacts: `data/artifacts/author_space_v1_wave2{,_fwonly}.json`, `author_space_pd_v1.json`): mid-rank percentile of each `between_author_dist.work_to_centroid` sample against `within_author_dist.loo` samples; count ≤ 90. → 160/1092 (14.65%), 427/1092 (39.10%), 0/280. W-p90 bars: 0.7998 / 0.8143 / 0.7790.
2. **Austen self-control**: `AuthorRelativeSpace.from_artifact(author_space_pd_v1.json)`; Gutenberg-strip + 3,000-word chunking exactly as `place_pastiche_baseline.py`; every 3rd chunk of all 5 novels (n=74). → 0/74 entered, 74/74 nearest=Austen, median distance 1.504, all W-pct 100.0. Matched p90 of self-distances = 1.695 → Brinton 35/37 ≤ 1.695.
3. **Cross-author chunks→Austen**: same pipeline on *Jane Eyre* (1.838), *A Passage to India* (1.760), *Bleak House* (1.924) medians.
4. **Styled distance-to-target vs matched unprompted** (`wave2/e4_results.json`): per styled sample, target distance minus median matched (model, scenario) unprompted distance to same target → median +0.0295, 42% closer; per condition +0.0310/+0.0251. Styled target-distance median 1.710 (style 1.715 / exemplar 1.696), min 1.170; ≤1.50: 63/318, ≤1.55: 81/318, ≤1.60: 101/318.
5. **E6 window distributions** (`e6_results.json`): 3,000w within median 1.341 (p25 1.237, p75 1.458), between median 1.535; full-work within 0.596.
6. **§5.1/§5.2 verifications** (`wave2/e4_results.json`): 400 unprompted, min nearest W-pct 97.4359, modes 100.0×215 / 98.7×184; anchors Ondaatje 133, Proulx 107, Sebald 38, DeLillo 34; 63/159, 83/159, 146/318; empirical null p0 = 0.1106.
7. **Translator pair counts** (`wave2/e5_report.md`): same-translator n=5 (0.569), cross-translator n=8 (0.750).
8. **Overshoot** (`r3_dimension_gap.md`): self_focus 81/268 (30.2%, over bar), metaphor 55/278 (19.8%, under bar); metaphor Holm p = 1.0; self_focus overall movement −0.020, n.s.

---

## 11. Severity roll-up and the path that survives

| # | Finding | Severity | Neutralization |
|---|---|---|---|
| 1 | Entry criterion unsatisfiable at sample length; Austen 0/74 vs herself; R1+R2 headline inferences vacuous as framed | **FATAL** | Fix: length-matched W envelopes; add same-author positive control; re-run E4/R5; rewrite R1/R2 |
| 2 | Identity conjecture contradicted by 14.7%/39.1% cross-author entry at full length; unfalsifiable in-experiment | **FATAL** | Fix: delete or restate as measured matched-envelope rates vs cross-author base rate |
| 3 | "Moves toward the target" false in the identity metric (+0.03 away, 42% closer); approach is rank, not distance | MAJOR | Fix wording everywhere; the mechanism story improves |
| 4 | "Strongest condition" claim; completion prompting untested | MAJOR | Run completion or disclose the gap; current sentence unavailable |
| 5 | 89% vs 40–52% comparison: different shelves/nulls, n=1, non-independent in-world chunks | MAJOR | Null-adjust, caveat in-sentence, report matched-envelope entry |
| 6 | Translation bound: 13 pairs, cross-kind length-confounded comparison | MAJOR | Print ns; drop or length-match |
| 7 | §5.6 variance ratio ≈1× at matched length | MAJOR | Recompute matched; keep self-attribution result |
| 8 | Reflexivity disclosure omits stimulus/target authorship and config asymmetry | MAJOR | Disclose |
| 9 | "Durable where detector scores are not"; "degrades predictably" vs discovered inversion; E3 gate inherited from wrong shelf; metaphor-caricature in abstract; fw-only approach rate unstated as headline | MAJOR (each locally) | Cut/restate; re-run E3 on wave-2; fix abstract |
| 10 | "Matched … ~3,500 words"; "more often than not"; "reliably"; "fails terminally"; "first published"; tier1 header 3-vs-5; @opt labeling | MINOR/NITPICK | Wording |

**What genuinely survives, and is worth saying loudly in v0.3:** the calibrated-percentile frame; the gate discipline including the published E7 failure; the exact-statistics hygiene (every recomputed number matched); the fw-only and paraphrase controls; the E6 length curve and PAN boundary honesty; model self-attribution 97.8%; the texture-vs-chassis decomposition (R3), which under finding #3's corrected wording becomes the paper's cleanest result; and — after recalibration — a defensible and more interesting headline: *length-matched, a dedicated human pastiche enters the target's within-author envelope almost always; styled frontier models enter it a quarter of the time and their function-word distance to the target does not shrink at all.* That is a falsifiable, two-sided, non-mystical claim, and the data to make it are already on disk.

---

## 12. Brandwine prose pass — the ten worst sentences, with rewrites

1. **"A novel-length human pastiche shows the same shape — approaching far more reliably (89% vs 52%), entering never — recasting the boundary as a property of authorial identity rather than a deficiency of machines."** (Abstract)
 Defect: "the same shape" is the artifact's shape (Austen herself shows it); the rates are cross-shelf incomparables; "recasting … identity" is the falsified conjecture compressed into a participle.
 Rewrite: "A novel-length human pastiche lands nearest its target in 33/37 chunks (9-author shelf) and, like every text we place at this length, never enters the full-novel-calibrated region — exposing the entry criterion's length dependence, which we correct in §5.5."

2. **"We conjecture the within-author function-word envelope is close to constitutive of authorial identity at this feature family — to enter it is nearly to *be* the author."** (§7)
 Defect: contradicted at base rate 14.7% (mixed) and 39.1% (fw-only) by the paper's own calibration pairs.
 Rewrite: "On this shelf, the within-author envelope is entered by other authors' full novels at 14.7% (39.1% function-words-only); it is a statistical envelope with a measured cross-author false-entry rate, not an identity criterion."

3. **"imitation prompting reliably moves samples toward their target (nearest-author hit rates 40–52% against an 11% empirical null) yet 0 of 318 attempts … enter."** (Contribution 2)
 Defect: "reliably" (≤52% is not reliability); "toward" (median Delta to target moves +0.03 *away*); "0 of 318" (vacuous criterion).
 Rewrite: "Imitation prompting raises the target's nearest-neighbor rank well above the 11% empirical null (40–52%) without reducing Delta distance to the target, which at scale increases slightly (+0.03 median)."

4. **"including all 159 with in-context exemplars, the strongest prompting condition the contrast literature implies should succeed."** (Contribution 2)
 Defect: the literature's success condition is completion, untested here.
 Rewrite: "including all 159 with in-context exemplars — the strongest instruction-style condition we test; the completion conditioning of Jemama & Kumar, which feeds the target's own function-word stream to the model, remains untested."

5. **"Its claims are positions in a validated space — which is precisely what makes them durable where detector scores are not."** (§1)
 Defect: prophecy, unowned, no durability evidence; "precisely" is confidence cosplay.
 Rewrite: "Its claims are positions in a validated space: auditable, re-runnable, and falsifiable against named distributions — properties detector scores lack."

6. **"No model in any family, at provider-default configuration, produced a single sample that a calibrated nearest-author placement would treat as plausibly that author's work."** (§5.1)
 Defect: by the same criterion, no *author* produced a 3,000-word passage the placement would treat as plausibly their own work (Austen: 0/74).
 Rewrite: "No unprompted sample fell inside the full-novel W-p90 of any author; note this criterion is not satisfiable by same-length excerpts of the authors themselves (§X), so we additionally report length-matched comparisons."

7. **"Even passage through a translator preserves more of an author's measurable signal than style prompting achieves."** (§5.5)
 Defect: 13 pairs, full-novel Delta compared against length-inflated 3.5k-sample Delta; cross-kind ratio.
 Rewrite: "Cross-translator within-author novel pairs (n=8) sit +0.18 Delta above same-translator pairs (n=5) — well inside the within/between gap; a length-matched comparison to styled samples is given in §X."

8. **"Style prompting works directionally and fails terminally, and both halves are significant."** (§5.2)
 Defect: "terminally" asserts an endpoint the design can't see (prompting-only, criterion unsatisfiable); "both halves are significant" launders a degenerate permutation test (p=1.0, zero power) by leaning on the CP bound.
 Rewrite: "Style prompting changes which author a sample is nearest to; it does not close the function-word distance, and no styled sample met the entry criterion (exact CP one-sided upper bound 0.94%)."

9. **"what it exaggerates past the target is the marked features (self-focus, metaphor), the signature of parody."** (Contribution 3)
 Defect: metaphor is below the paper's own ≥25% overshoot bar (19.8%); self-focus overall movement is n.s.; "signature of parody" is connotation doing evidence's job.
 Rewrite: "and one marked feature — self-focus — overshoots the target in 30% of eligible samples, the exaggeration pattern parody scholarship predicts; metaphor shows the same tendency below our pre-set threshold (20%)."

10. **"But the four hundred most ordinary words — the determiners, prepositions, auxiliaries, and pronouns that carry attribution — do not follow."** (§7)
 Defect: "four hundred" is wrong in both directions (the list is 376 entries; the measured block is top-300); elegance bought with a fabricated number.
 Rewrite: "But the closed-class vocabulary that carries attribution — the 300 most frequent words of the shelf, under either vocabulary — does not follow."

---
*Report generated read-only; the only file written is this one. All computations re-derivable via §10.*
