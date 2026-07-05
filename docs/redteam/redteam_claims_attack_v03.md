# Red-Team Claims Attack v2 — draft_v01.md (v0.3, "The Width of a Voice")

**Reviewer posture:** same hostile empiricist who rejected v0.2. The authors claim full remediation per `RED_TEAM_SYNTHESIS.md`; this pass re-attacks every headline sentence against the Results 2.0 evidence (`reports/validation/results2/`, `wave2/e8_results.md`), the raw corpus on disk, and the git record. Every number below was re-checked read-only; reproduction snippets in §12. This run discharges the remediation plan's own step 5 ("re-run both red-team agents on v0.3").
**Date:** 2026-06-11.

**Verdict: MAJOR REVISION — the instrument now survives; several headline sentences do not.** The v0.2 FATALs are genuinely discharged: the length-matched envelopes and the E8 positive control are real fixes, the identity conjecture is gone, "pre-registered" is gone, the translation bound is cut, clustering and floors are primary, and the artifact confession is (mostly) honest. No vacuous criterion remains. But v0.3 commits **fresh inference errors of exactly the family that killed v0.2 — printing the numbers and then writing a different sentence**. The worst is new and inverted: the completion condition's "parity with named-style prompting" is a composition artifact; **model-matched, completion beats named-style prompting for every single model that complied** (pooled matched 31.0% vs 21.9%). The new headline concept (envelope width) is built on per-target marginals while the per-model marginal in the same tables is *larger*; the abstract's "statistically indistinguishable" parity with Brinton is an inference the paper's own evidence file forbids; and the E8 gate verdict committed to disk is **FAIL**, relabeled "PARTIAL" in the paper and "They do" in the abstract. All of this is fixable with wording plus one cheap re-analysis — none of it requires touching the instrument. Details below.

---

## 1. FATAL (headline-inverting) — "Completion enters at 31.0%, parity with named-style prompting" is a composition artifact; model-matched, completion *wins* for every compliant model

**The claims:** Abstract: "A completion condition (the model continues the author's own text) enters at 31.0%, parity with named-style prompting." §2.3: "it reaches parity with named-style prompting (31.0% vs 30.5%)." §5.4 heading: "voice-from-text reaches parity with named imitation." §5.4: "Inheriting the author's actual opening — topic, register, and local function-word stream — **buys no more entry than being told the author's name**." Discussion: "Completion conditioning — the literature's strongest mechanism — **adds nothing over the author's name** (31.0%)."

**The evidence the paper itself prints, never cross-tabulated.** Per-model fw-only p90 entry, styled (§5.2 table / `entry_report.md`) vs completion (`completion_results.md`, which the paper quotes only as "claude-fable-5 leads with 10/20"):

| Model | styled fw-only @p90 | completion fw-only @p90 | Δ (points) |
|---|---|---|---|
| claude-fable-5 | 14/39 (35.9%) | 10/20 (50.0%) | **+14.1** |
| claude-opus-4-8 | 9/40 (22.5%) | 7/20 (35.0%) | **+12.5** |
| claude-sonnet-4-6 | 3/32 (9.4%) | 3/20 (15.0%) | **+5.6** |
| gpt-5-mini | 14/40 (35.0%) | 5/8 (62.5%) | **+27.5** (target-skewed: 5 of 8 are McCarthy) |
| qwen3.6:35b | 3/28 (10.7%) | 2/16 (12.5%) | **+1.8** |
| claude-haiku-4-5 | 0/17 (0.0%) | 0/2 (0.0%) | tie (n=2) |
| gpt-5 | 29/40 (72.5%) | — (20/20 refused) | unmeasurable |

Every model measurable in both conditions enters **more** under completion (5/5 strictly positive; sign test p ≈ 0.03 even before clustering arguments, and three of the five — fable, opus, sonnet — are target-balanced 4×5 designs, so the sign pattern is not a target-mix artifact). Pooled over the *same* models, completion is 27/87 = 31.0% vs styled 43/196 = **21.9%** — roughly **+9 points**, not parity. The pooled "parity" (31.0 vs 30.5) exists only because the styled pool contains gpt-5 at 72.5% — and gpt-5 is precisely the model the completion condition lost to refusal. The paper even prints the caveat ("refusals skew the compliant set toward Claude models... not model-matched") and then states the parity headline in the abstract, §2.3, the §5.4 heading, and the Discussion anyway. Worse, the caveat's *direction* is misread: the skew toward Claude (weaker styled enterers) means composition is *suppressing* the completion rate relative to a matched comparison, so "adds nothing" is not merely unsupported — it is the wrong sign.

**Compounding detail:** the completion prompt did not name the author (commit c6b044c: "continue target author's opening, **no author named**"); §4.1 omits this. So the comparison is *name-only* vs *text-only*, and the honest model-matched sentence is: "the author's opening, without the name, buys more entry than the name for every model that will do it." That is a better finding than parity — it says the function-word stream is more inheritable from text than from a name, which fits the paper's own chassis mechanism — and the draft inverted it.

**Neutralization (mandatory):** (a) add the model-matched comparison (one table; all numbers already computed); (b) rewrite abstract/§2.3/§5.4/Discussion: "Among models that complied, completion entered more than named-style prompting (model-matched 31.0% vs 21.9%; positive for all five comparable models); whether it would beat the best styled model is unmeasurable — that model refused all 20 completions." (c) state the no-author-named design in §4.1. The "parity" sentence is not available in any section.

---

## 2. MAJOR — "Statistically indistinguishable from a praised novel-length human pastiche" is an inference the evidence file forbids, on a comparison the paper's own concept declares uninterpretable

**The claim (Abstract):** "the best model (gpt-5) enters at 72.5% under the function-word vocabulary — **statistically indistinguishable** from a praised novel-length human pastiche (75.0%)." Repeated as "comparable... on the same footing" (Contribution 2) and "the best of them is at human-pastiche parity on the identity vocabulary" (Discussion).

**Four defects, in order:**
1. **No test exists, and none is licensed.** No statistical comparison of 29/40 vs 27/36 appears in any evidence file. The evidence file itself (`entry_report.md` §b, twice; §5.2 of the draft, in parentheses) declares Brinton's n "**descriptive, not inferential**" — 36 non-independent chunks of one novel. "Statistically indistinguishable" performs the exact inference the paper's own caveat prohibits. (gpt-5's side is clustered too: ICC 0.55, 8 cells.)
2. **Best-of-seven selection.** gpt-5 is the maximum of seven per-model rates (0%–72.5%) compared against a single human. A selected maximum vs an n=1 baseline with no selection correction is a forking-paths comparison; the same logic applied to the *worst* model yields "humans dominate machines 75% to 0%."
3. **Cross-shelf, width-unadjusted — indicted by the paper's own corollary.** §5.3 closes: "any claimed imitation success rate that does not state the target's envelope width is uninterpretable." The abstract's parity comparison states no widths. They matter: Austen's fw-only LM p90 is **1.453, the second-narrowest on the PD shelf** (only Hawthorne 1.486 — actually Austen 1.453 is the narrowest; Hawthorne is 1.486), while gpt-5's 72.5% pools one wide target (McCarthy 1.553) with three narrow ones. Brinton hit 75% against a narrow envelope; gpt-5's rate is partly McCarthy-subsidized. Width-adjusting this comparison is the paper's own invention; it must either apply it here or stop comparing.
4. **"Praised" is uncited.** §2.6's pastiche-reception citation is still `[cite]`. A "first" or "praised" claim with a placeholder citation is an invitation.

**Neutralization:** "the best model (gpt-5) enters at 72.5% fw-only — in the same range as the human pastiche's 75.0%, though the two rates are against different shelves and targets of different envelope widths and neither supports a formal comparison (Brinton's chunks are non-independent; gpt-5 is the best of seven models)." If that sentence is too long for the abstract, the comparison does not belong in the abstract.

---

## 3. MAJOR — The width concept: real structure, oversold as "a property of the target"; the per-model marginal in the same tables is larger, and two supporting sentences are factually false

The new headline ("The Width of a Voice"; Contribution 3; §5.3; abstract: "Enterability is substantially a property of the *target*... how imitable an author is, on this instrument, is in large part how wide their envelope is"; Discussion: "which author is being imitated predicts entry far better than which model is imitating").

**3a. The model marginal is as large as the target marginal — and the paper never decomposes them.** fw-only @p90: per-target spread 10.7%→76.8% (66.1 points); per-model spread 0.0%→72.5% (**72.5 points** — larger). The claim "predicts entry far better" was never tested (no two-way decomposition, no model×target table — 28 cells the data fully support), and a hard bound from the printed numbers refutes the strong reading: gpt-5 has exactly 10 styled samples per target and entered 29/40, so even if all 10 McCarthy samples entered, **gpt-5 entered the three *narrow* envelopes at ≥19/30 (≥63%)** — while all other models combined entered them at ≤10/150 (**≤6.7%**). For the best model, the "narrow" targets are not narrow; Didion's envelope "admits 3–14%" only when you average gpt-5 with five models that barely enter anything. "Enterability is substantially a property of the target" is true of the model-average and false of the best model — which is the model the abstract's previous sentence celebrates. The defensible sentence: "averaged over models, per-target entry tracks envelope width; the best model largely escapes the width constraint."

**3b. "The entry-rate ordering is the envelope-width ordering" (§5.3) is false in the co-primary vocabulary printed directly above it.** Full vocab: Didion (width 1.490) enters 2/66 = 3.0%; Ondaatje (width 1.409) enters 2/56 = 3.6% — wider envelope, lower entry. Noise at 2-vs-2 counts, certainly — which is the point: with n=4 targets you cannot assert an ordering identity; you can report a monotone trend (fw-only is monotone 4/4) with its fragility stated.

**3c. "McCarthy — ... whose LM p90 is the widest on the shelf in both vocabularies" (§5.3) is false in both vocabularies.** Full vocab: Robinson 1.731 > McCarthy 1.715 (Ishiguro ties at 1.715). fw-only: Murakami 1.738 and Foster Wallace 1.689 > McCarthy 1.553 (McCarthy is third). McCarthy is the widest *of the four targets*. The error matters beyond accuracy: it conceals a free validation set (see 3e).

**3d. Near-circularity, unacknowledged.** Entry is *defined* as distance ≤ the width quantile, so width→entry is partially mechanical; the substantive empirical content is that styled-imitation distances are roughly target-invariant (medians 1.59–1.79 full, 1.377–1.477 fw). The paper gestures at this ("what varies is how much of that distance each author's own variation forgives") but never tests distance-distribution constancy across targets, which is the actual load-bearing claim.

**3e. What a hostile reviewer demands — and the data already on disk can supply.** (i) Width-vs-entry as a *correlation with n>4*: the 400 unprompted and 318 styled samples have computable distances to **all 15** shelf authors, and the LM sidecars hold all 15 widths; entry-into-each-author's-envelope vs width over 15 authors (×2 vocabularies) is one script. If Robinson and Murakami (wider than McCarthy) also admit more samples, the concept is earned; if not, width is a 4-point anecdote with a McCarthy/not-McCarthy dichotomy doing all the work. (ii) The model×target 28-cell table in §5.3 or an appendix. (iii) A logistic decomposition (entry ~ model + target) with cluster-robust uncertainty. (iv) One sentence acknowledging the definitional coupling. As drafted, "width" is a genuinely promising concept supported at the strength of a 2×2 anecdote — exactly the thing the title bets the paper on.

**Severity:** MAJOR, not FATAL — the per-target structure is real, E8's per-work failures genuinely echo it, and the weakened claim survives. But the title-level concept currently rests on 4 targets, one false superlative, one false ordering sentence, and an untested "far better."

---

## 4. MAJOR — E8's committed verdict is FAIL; the paper says "PARTIAL," and the abstract says "They do"

**The record:** `e8_results.md` (committed 2026-06-11 00:18) ends "**Overall E8: FAIL**" — three of four shelf/vocabulary combinations fail the per-author floor somewhere. The paper's gate table (§3.5) renders this "PARTIAL — pooled near-nominal; per-author failures reported in §3.9." The abstract renders it "the authors' own held-out windows must re-enter at near the nominal rate. **They do**: 84–88%."

**Three layers:**
1. **Post-hoc gate adjudication, the confessed v0.2 sin repeated unconfessed.** The remediation plan (`RED_TEAM_SYNTHESIS.md`, committed 22:39 the night before) specified E8 as "held-out windows must enter their own LM envelope at ~the nominal rate." The operative gate as run — "binomial CI contains 0.90 **OR rate ≥ 0.80**" — and the further adjudication "treat the pooled rate as the operative yardstick" first appear in the same commit as the results (00:18; the e8 report and entry report were generated at 00:05/00:14). §3.6 confesses exactly this pattern for the v0.2 variant-selection rule ("the rule's first committed appearance is contemporaneous with the comparison results"); §3.9 does not confess it for E8. Given that the paper invites git archaeology by citing its own remediation plan, a reviewer will find this in five minutes.
2. **"Near the nominal rate" is strained for fw-only.** Pooled wave2 fw-only is 83.7%, CP [82.3%, 85.1%] — the interval excludes 0.90 decisively. 87.8/87.3/87.5 are defensibly "near nominal"; 83.7 is "modestly below nominal," and the abstract's "84–88%" rounds the one problematic number up and into a range that reads as a pass.
3. **Credit where due:** §3.9 does state "we report the strict gate verdict as it fell — three of four shelves fail the per-author floor somewhere," names every failing cell and driver work, and the per-author failures genuinely are single-work effects with cluster-adjusted CIs containing 0.90. The *reporting* is honest; the *labels* ("PARTIAL," "They do") and the unstated timing of the OR-floor are not.

**Neutralization:** gate table verdict: "strict per-author gate: FAIL (5/48 cells; §3.9); pooled control: 83.7–87.8% vs nominal 90%." Abstract: "they re-enter at 84–88% (strict per-author gate fails for 4 of 24 authors, each driven by one off-style work)." Appendix B provenance note: add that the OR-floor and pooled-yardstick adjudication were specified contemporaneously with the E8 results, matching the §3.6 disclosure standard.

---

## 5. MAJOR — The adversarial-review provenance is the one reflexivity still undisclosed

The abstract leans on "adversarial review caught the artifact"; §1 and §7 say "two **independent** adversarial reviews." The reviews are `redteam_stats_attack.md` and `redteam_claims_attack.md` — **self-commissioned AI red-team passes, run inside the same human–Claude collaboration that wrote the paper**, committed to the same repo, one of them cited as an evidence source in §5.7. "Independent" is true in the narrow sense (two separate agent runs that recomputed from frozen artifacts without sharing state) and misleading in the reading every reviewer will default to (external referees). For a paper whose §8.11 discloses that Claude drafted the stimuli, the prompts, and "this sentence," omitting that Claude also performed the adversarial review that the abstract showcases — on a paper studying Claude-family models — is the single most conspicuous remaining gap. It also bears on the abstract's rhetorical question (#3 in my brief): the self-caught-artifact narrative is an honest feature *only if* the catching mechanism is disclosed; undisclosed, a reviewer may read it as "this team ships artifacts and grades its own retraction."

**Other K11 residuals:** (a) **Target selection vs the width headline.** §4.1/§8.4 disclose the four targets were "fixed... without a documented selection procedure." That was adequate when targets were incidental; now that the headline concept is *per-target* envelope width, the undocumented choice of one wide + three narrow targets is load-bearing and deserves its own sentence in Limitation 4 (were widths known or knowable when targets were picked? The LM envelopes postdate target selection by two days — say so; it's exculpatory). (b) **The qwen ghost sample:** 160 completion files exist on disk; `completion_mccarthy-cormac__s3.txt` (qwen) is zero-length and silently absent from the 159 records; the compliance table shows qwen "refused/partial 0." Count it (as it was for the two v0.2 qwen styled samples). (c) `n` accounting: §4.1 "159 generations recorded" vs §4.3 "20 per model requested" (=160) — explain the delta in-text.

**What is now adequately disclosed (verified):** scenario/prompt authorship ✓; Claude = 4/8 ✓; decoding asymmetry, with §5.7 correctly demoting the cross-model ordering for it ✓; same-session gates ✓; sole-author responsibility ✓.

---

## 6. MAJOR — §5.5 (R3) violates the paper's own hard floor: "excluded from every claim" except the mechanism claim

§3.7: "a **hard floor of 1,500 MFW tokens**, below which a sample is excluded from **every claim**." §5.5: "n=318 styled samples" — all of them, including the 6 hard-floor gemma4 samples and the 76 sub-floor samples, at native length. The R3 texture/chassis analysis was not re-run on the floor-compliant stratum; the v0.2 numbers were imported with a justification ("internally length-matched" because styled-vs-matched-unprompted) that addresses *bias* but not the floor rule the paper states as absolute, and not the noise explosion below 1,500 tokens that the paper's own E6 documents. The fix is one re-run on n=236 (the machinery exists; the matched-unprompted construction is unchanged) or an explicit carve-out sentence in §3.7 — but "every claim" cannot stand over a Results subsection that ignores it. The chassis immobility result will almost certainly survive; run it and say so.

Related (MINOR): §5.7's matched-length variance ratio ("≈0.8–1.1×") cites *the red-team report's own back-of-envelope* (`redteam_claims_attack.md §7` — flagged "rough" in the source) as its evidence. An adversary's sanity check is not an artifact. Compute the same-author 3,000-word window-pair distribution from the E8 sidecar data and cite that.

---

## 7. Refusal reporting (instructed attack surface #4): substantively neutral — verified — with two nits

I pulled the raw gpt-5 completion outputs: all 20 are genuine refusals (45–73 words each; "Sorry, I can't continue that copyrighted text…", offering summaries or "an original 3,500-word passage in a similar voice"). So "gpt-5 refused that task 20/20 times" is accurate, and the refusals are **continuation/copyright-shaped, not imitation-shaped** — gpt-5 explicitly *offers* style imitation. The paper should say this; it sharpens the "policy posture toward that request" reading and pre-empts the misreading that gpt-5 refuses imitation per se. Treating refusal as right-censoring for inference (§8.6) while reporting it as a compliance finding (§5.4) is consistent and fine. Nits: the paragraph header "Refusal asymmetry, reported neutrally" protests too much — delete the label and let the table be neutral; "claude-fable-5 leads with 10/20" is leading by *count* — by rate gpt-5-mini leads (5/8, 62.5%); the qwen zero-length output belongs in the refused/partial column (§5).

---

## 8. The abstract (instructed surface #6): 381 words; what earns its place

Counted: **381 words** — roughly 130–180 over typical venue limits. Sentence triage:

| Sentence | Verdict |
|---|---|
| "Whether language models can write *as* a specific author…" | Keep — the frame in 15 words. |
| "We pose it the way stylometry poses it…at the same text length." | Keep — the unit; this is the paper. |
| 56-word construction sentence (gates + E8 + "They do: 84–88%") | Compress to ~30 words; fix "They do" per §4. |
| "We report this control because our first criterion failed it." + 42-word artifact-history sentence | **Compress both to one clause** ("…a control added after adversarial review (self-run, disclosed §8.11) showed our first, full-novel-calibrated criterion was unsatisfiable at sample length"). The full confession is §1/§3.9/§7 material; two abstract sentences of process narrative is where "this team ships artifacts" gets formed. |
| 77-word "Against the corrected envelopes…" monster (rates + gpt-5 parity + Brinton + content reuse) | Split; delete "statistically indistinguishable" and "praised" (§2). The 20.3%/30.5%/72.5%/75.0%/94.4% pileup is five numbers where three carry it. |
| "Enterability is substantially a property of the *target*…" | Keep, qualified "averaged over models" (§3); note Morrison's 24.1% breaks the quoted "3–14%" — say "3–24%" or name all three narrow targets. |
| Completion sentence | Rewrite per §1 — the corrected version is *more* interesting. |
| "Mechanistically, lexical-diversity texture transfers…" | Keep — best sentence in the abstract. |
| "Imitation prompting raises the target's nearest-neighbor rank…" | Merge into the mechanism sentence. |
| "We release…" | Keep. |

Also: "styled samples from **seven** frontier and local models" vs §1's "**eight** models across three families" — the gemma4 exclusion is real but unexplained at abstract altitude; one parenthesis ("(one of eight produced no floor-compliant samples)") or say eight and footnote.

---

## 9. Internal consistency sweep (instructed surface #8): every number that appears twice

| Number | Locations | Verdict |
|---|---|---|
| E8 failing cells | §3.5 "5 of 48"; §3.9 "Five of 48"; Lim. 7 "5 of 48" | **Appendix B says "4/48" — wrong** (wave2: Whitehead; wave2_fw: FW, Proulx, Whitehead; pd_fw: Fitzgerald = 5). Fix App B. |
| E8 pooled rates | abstract "84–88%"; §3.9/§5.1 "83.7–87.8" | 83.7→"84" rounds a sub-nominal CI out of sight (§4). |
| 20.3/30.5; per-level tables | abstract, §1, §5.2, T2 | ✓ match `entry_results.json` exactly (incl. all three CI constructions, threshold-CI ranges). |
| gpt-5 72.5 [56.1, 85.4]; per-model table | §5.2 | ✓. |
| Brinton 34/36, 27/36, 1.549/1.574, 1.411/1.314, 31/36, 36/36 | §5.2, §9.1 | ✓; v0.2's "37 chunks" → 36 explained by token-windowing — fine. |
| Per-target widths/entries | §5.3 table | ✓ vs `e8_results.md` and JSON. |
| "widest on the shelf in both vocabularies" | §5.3 | **✗ false both ways** (Robinson 1.731 full; Murakami 1.738 fw). |
| Completion 31.0/20.7; strata 87/35/37; per-target 19/4/3/1 | §4.3, §5.4 | ✓ vs JSON (sums verified). 159 vs 160-files: see §5b. |
| Approach 51.7 vs 21.2; 8.6e-25; DEFF CP [41.3, 62.0]; per-target rows; Ondaatje p=0.074; fw 29.2 vs 3.1 | §5.6 | ✓ all match. |
| Chassis −0.030 on 1.654; signs 2/4; −0.087 [−0.122, −0.055]; 71.6%; ~6% of 1.418 | abstract, §5.5, §5.6, F4 stub | ✓ (−0.087/1.418 = 6.1%). |
| ICC 0.55–0.70; DEFF ≈2.8–3.8; n_eff 63–83 | §4.5, Lim. 9 | ✓ (0.547–0.698; 2.84–3.76; 65–83). |
| Self-consistency 97.8%/400; pairs 1.373–1.855; centroid Deltas | §5.7 | ✓ vs `model_self_consistency.md`. |
| Paraphrase medians 1.591–1.619 vs 1.625; spreads 0.019–0.106 | §6.2 | ✓. **But §5.8 also quotes "off-manifold-rate 1.000 under every phrasing at full-novel scale" — a zombie of the retired criterion** (it is the unsatisfiable full-novel W-p90 applied to window-scale samples, mislabeled "full-novel scale"), in direct violation of §3.4's "never against the table above." Quote the spread numbers only. |
| fw-only gates 0.911/92.3/97.4 | §6.1a | ✓ vs `fwonly_comparison.md`. |
| E6 table; PAN table; 0.439/0.512/0.402/0.239/0.856 | §3.7, App A | ✓ (unchanged from v0.2; previously verified). |
| "factor of twenty in admission rate" (Discussion) | — | full-vocab 20–24×, fw-only 5.6–7.2×. Say "up to a factor of twenty (full vocabulary)" or give both. |

---

## 10. Are the v0.2 findings actually fixed? (K1–K11 + my original §§1–9)

| Item | Status |
|---|---|
| K1 entry criterion / positive control | **Fixed** (LM-W + E8; §5.1 reports the artifact as a result) — modulo the §4 adjudication issue. |
| K2 identity conjecture | **Fixed** — removed, not softened; no "constitutive"/"identity boundary" text survives. |
| K3 "pre-registered" | **Fixed** — §3.1/§3.6/App B state the d18→MFW pivot, the same-session provenance, the Holm-family history, with dates. Exemplary. |
| K4 clustering | **Fixed** — DEFF + cell-bootstrap primary everywhere; v0.2 "unaffected" claim explicitly retracted. |
| K5 floors | **Mostly fixed** — enforced in entry/approach; **violated in §5.5/R3 (n=318)** — see §6. |
| K6 approach null/confounds | **Fixed** — scenario-matched null, Ondaatje conceded in-table, rank-vs-metric stated plainly, exemplar demoted (though "does not separate under cluster-honest comparison" cites a test no evidence file contains — show it or say "rates 29.0% vs 32.1%, not distinguished at these n's"). |
| K7 human comparison | **Half-fixed** — fw-only pastiche run, in-sentence caveats, n=1 limitation ✓; but the new parity framing imports new defects (§2). |
| K8 completion | **Run** ✓ — and then misread (§1). |
| K9 thresholds | **Fixed** — p90/p95/p99 sweeps with threshold-quantile CIs throughout. |
| K10 chassis direction | **Fixed** — immobility with signs split; metaphor-caricature out of the abstract; self_focus-only kept with its bar. |
| K11 disclosure | **Mostly fixed**; remaining: review provenance, E8-rule timing, target-choice-vs-width sentence (§5). |
| My §9.1 (durable/predictably) | **Fixed** — "auditable, re-runnable, falsifiable"; inversion reported in §1, App A, Discussion. |
| My §9.3 E3 inherited | **Disclosed** ("PASS (inherited)", App B) — the cheap re-run on wave-2 was skipped; acceptable, but a one-hour run would delete the asterisk. |
| Translation bound | **Cut** ✓ (§8.2, with the underpowered recomputation reported). |
| "first published" / "four hundred words" / "more often than not" / "terminally" | All gone ✓. |

---

## 11. Brandwine pass — the ten worst sentences in v0.3, with rewrites

1. **"the best model (gpt-5) enters at 72.5% under the function-word vocabulary — statistically indistinguishable from a praised novel-length human pastiche (75.0%)"** (Abstract). Untested inference on a baseline the evidence file marks non-inferential; best-of-7 vs n=1; width-unadjusted cross-shelf; "praised" uncited.
   → "the best model (gpt-5) enters at 72.5% — in the range of a novel-length human pastiche's 75.0%, though on a different shelf and target, and neither rate supports a formal comparison."

2. **"A completion condition (the model continues the author's own text) enters at 31.0%, parity with named-style prompting; gpt-5 refused that task 20/20 times."** (Abstract). Composition artifact; model-matched it is +9 points and positive for all five comparable models.
   → "Given the author's opening instead of the name, every model that complied entered *more* (model-matched 31.0% vs 21.9%); the best styled model refused all 20 completion requests."

3. **"Inheriting the author's actual opening — topic, register, and local function-word stream — buys no more entry than being told the author's name."** (§5.4). False for every model measured in both conditions.
   → "Model-matched, inheriting the author's opening bought 2–28 points more entry than the name alone; the pooled parity (31.0% vs 30.5%) is an artifact of the best styled model's absence from the compliant set."

4. **"Completion conditioning — the literature's strongest mechanism — adds nothing over the author's name (31.0%)."** (Discussion). Same inversion, restated as mechanism.
   → "Completion conditioning outperformed the name for every compliant model, but modestly — nowhere near the short-length near-ceiling rates — and the strongest styled model would not perform it."

5. **"The entry-rate ordering is the envelope-width ordering."** (§5.3). False at full vocabulary (Didion 3.0% < Ondaatje 3.6% with the wider envelope), printed one table up.
   → "fw-only entry is monotone in envelope width across all four targets; full-vocabulary entry is monotone except one adjacent swap at 2-vs-2 counts."

6. **"McCarthy — whose catalog spans *Blood Meridian* to the dialogue-only *Stella Maris*, and whose LM p90 is the widest on the shelf in both vocabularies"** (§5.3). Robinson (1.731) is wider at full vocabulary; Murakami (1.738) and Foster Wallace (1.689) at fw-only.
   → "…whose LM p90 is the widest of the four targets (and third-widest on the shelf under the function-word vocabulary)."

7. **"Enterability is substantially a property of the *target*"** (Abstract) / **"a reusable, measurable property… not of the imitating system"** (Contribution 3). The per-model spread (0–72.5%) exceeds the per-target spread (10.7–76.8%); gpt-5 enters the narrow envelopes ≥63% while the rest manage ≤7%.
   → "Averaged over models, enterability tracks the target: McCarthy's wide envelope admits 73–77% of attempts, the three narrow envelopes 3–24%. The best model is the exception — it enters the narrow envelopes at a rate no other model approaches."

8. **"which author is being imitated predicts entry far better than which model is imitating"** (Discussion). Untested; the printed marginals say the opposite ordering of effect sizes is at least as defensible.
   → "target and model are jointly strong predictors of entry — target width orders the model-average, while the best model breaks the width constraint; a two-factor decomposition is given in §X." (Then run it.)

9. **"any claimed imitation success rate that does not state the target's envelope width is uninterpretable"** (§5.3). Self-indicting (the abstract's parity comparison states no widths) and overclaimed ("uninterpretable").
   → "an imitation success rate is hard to interpret without the target's envelope width as denominator — a number our own cross-shelf comparison in §5.2 also owes (Austen fw-only p90: 1.453; the four contemporary targets: 1.227–1.553)."

10. **"an author who contains multitudes (McCarthy) is 'easy' to imitate in exactly the sense that his own books barely resemble each other"** (§5.3). E2 attributes McCarthy's held-out works 7/8 top-1; his books resemble each other enough to be near-perfectly attributable. The width is intra-author *spread*, not loss of identity.
    → "…is 'easy' to enter in exactly the sense that his own books are unusually far from one another — while remaining attributable to him (7/8 leave-one-out)."

(Honorable mention, would be #11: §5.8's "off-manifold-rate 1.000 under every phrasing at full-novel scale" — delete the clause; it re-quotes the criterion the whole paper exists to retract, as evidence of robustness.)

---

## 12. Reproduction of every number introduced in this review

All read-only from repo root.

1. **Completion vs styled per model** — `results2/completion_results.json` `entry.fwonly.per_model` (fable 10/20, opus 7/20, sonnet 3/20, mini 5/8, qwen 2/16, haiku 0/2) vs `results2/entry_report.md` §a fw-only per-model (14/39, 9/40, 3/32, 14/40, 3/28, 0/17). Matched pools: 27/87 = 31.0% vs (14+9+3+14+3+0)/(39+40+32+40+28+17) = 43/196 = 21.9%. mini target mix from `completion_results.md` (Didion 3, McCarthy 5).
2. **gpt-5 narrow-envelope bound** — §4.3: styled = 4 pairs × 5 × 2 conditions = 10/target; gpt-5 n=40 (no exclusions), entered 29 (fw-only). McCarthy ≤ 10 ⇒ narrow-3 ≥ 19/30. Pooled narrow-3 entries 9+14+6 = 29 (per-target JSON) ⇒ other models ≤ 10/150.
3. **Width superlatives** — `wave2/e8_results.md`: full LM p90 Robinson 1.731, Ishiguro 1.715, McCarthy 1.715; fw-only Murakami 1.738, FW 1.689, McCarthy 1.553. PD fw-only: Austen 1.453 (minimum), Hawthorne 1.486.
4. **Full-vocab ordering inversion** — `entry_results.json` entry.full.primary.per_target: didion (2, 66), ondaatje (2, 56); widths 1.490 vs 1.409.
5. **E8 strict verdict** — `e8_results.md` final line "**Overall E8: FAIL**"; failing cells: wave2 Whitehead; wave2_fwonly FW/Proulx/Whitehead; pd_fwonly Fitzgerald = **5** cells (draft App B line 687 says "4/48"). fw-only pooled 2380/2842 = 83.7%, CP [0.823, 0.851].
6. **Gate timing** — `git log`: RED_TEAM_SYNTHESIS 7be8bf6 (06-10 22:39); Results 2.0 + E8 02cf9ee (06-11 00:18; e8 report generated 00:05 local); the OR-≥0.80 floor and "pooled operative" wording first appear in that commit; the synthesis (committed earlier) specifies only "~the nominal rate."
7. **gpt-5 refusals** — `data/ai-longform/gpt-5/completion_*.txt`: 20 files, 45–73 words each (total 1,741), all beginning "Sorry, I can't…" with offers of summary or "an original 3,500-word passage in a similar voice."
8. **The 160th completion** — 20 completion files per model dir (8 × 20 = 160); `qwen3_6_35b/completion_mccarthy-cormac__s3.txt` = 0 words; `completion_results.json` meta n_records = 159; compliance table qwen = 16+3+0 = 19.
9. **Abstract** — 381 words (split on whitespace between "## Abstract" and "## 1.").
10. **Marginal spreads (fw-only @p90)** — per-model 0.0–72.5 (range 72.5 pts), per-target 10.7–76.8 (range 66.1 pts); "factor of twenty": 73.2/3.0 = 24.4 and 73.2/3.6 = 20.3 (full); 76.8/13.6 = 5.6 and 76.8/10.7 = 7.2 (fw-only).
11. **Cross-checked verbatim** (all match): §5.2 entry tables incl. every CI; §5.6 approach tables incl. p-values; §5.5 R3 tables vs `r3_dimension_gap.md`; Brinton block vs `entry_report.md` §b; §5.7 vs `model_self_consistency.md`; §6.2 vs `paraphrase_sensitivity.md`; §6.1a vs `fwonly_comparison.md`; chassis vs `entry_report.md` §e (−0.0051 [−0.042, +0.040]; −0.0868 [−0.122, −0.055], 71.6%).

---

## 13. Severity roll-up and verdict

| # | Finding | Severity | Neutralization |
|---|---|---|---|
| 1 | Completion "parity"/"adds nothing": composition artifact; model-matched completion wins for all 5 comparable models (+9 pts pooled) | **FATAL** (headline sentence inverted by the paper's own tables) | Model-matched table + rewrite abstract/§2.3/§5.4/§7; disclose no-author-named design |
| 2 | "Statistically indistinguishable" gpt-5~Brinton: no test, evidence file forbids inference, best-of-7, width-unadjusted cross-shelf, "praised" uncited | MAJOR | "In the same range," with shelf/width/selection caveats; cite or cut "praised" |
| 3 | Width oversold as target-property: model marginal larger; gpt-5 enters narrow envelopes ≥63% vs ≤7% others; ordering sentence false at full vocab; "widest on the shelf" false both vocabs; circularity unacknowledged; n=4 | MAJOR | Model×target table; 15-author width-entry correlation (data on disk); qualify "averaged over models"; fix two false sentences |
| 4 | E8 committed verdict FAIL → "PARTIAL"/"They do"; OR-floor + pooled-yardstick adjudication contemporaneous with results, undisclosed; fw-only 83.7% CI excludes 0.90 | MAJOR | Honest labels; App B timing disclosure to §3.6 standard |
| 5 | "Independent adversarial reviews" provenance (self-run Claude red-team agents) absent from §8.11 | MAJOR | One disclosure sentence; qualify "independent" |
| 6 | §5.5/R3 includes hard-floor and sub-floor samples against §3.7's "excluded from every claim" | MAJOR | Re-run R3 on n=236 (or carve out explicitly) |
| 7 | §5.7 ratio sourced to the attacker's back-of-envelope; exemplar "cluster-honest comparison" cites no test; zombie "off-manifold 1.000" in §5.8; Morrison omitted from abstract's "3–14%"; "factor of twenty" vocab-selective; fable "leads" by count not rate | MINOR (each) | Compute/cite/delete/qualify |
| 8 | App B "4/48" vs "5 of 48"; abstract seven-vs-eight models; 159-vs-160 completion accounting + qwen ghost sample; "praised" placeholder cite; §2 still a skeleton (stance fidelity uncheckable) | NITPICK | Wording/bookkeeping; §2 must be written before any submission verdict means anything |

**Does v0.3 survive?** **Yes, as a major revision — and only just.** What was rotten in v0.2 is genuinely fixed: the criterion is now satisfiable by the people it measures, the confessions are dated and checkable, the statistics are cluster-honest, and the two-sided graded-entry result with the E8 control is a real contribution that I could not break — every pooled number, interval, and threshold sweep I recomputed matched. But v0.3 re-commits v0.2's signature failure mode at the new headlines: the completion parity claim is inverted by a cross-tabulation of two tables the paper itself prints; the width concept is narrated past its n=4, model-marginal-blind evidence; and the abstract performs an inference its own evidence file prohibits. The fixes are days, not weeks: one model-matched table, one 15-author width-entry correlation, one R3 re-run on the primary stratum, honest E8 labels, one disclosure sentence about who the adversarial reviewers were, and roughly ten sentences rewritten as listed. Do those, and the paper stops being a target. Ship the current sentences, and reviewer 2 finds the completion inversion in an afternoon — it is sitting in plain sight between §5.2's per-model table and §5.4's compliance table, exactly where the 1.320-vs-1.341 contradiction sat in v0.2.

---
*Report generated read-only; the only file written is this one. All computations re-derivable via §12.*
