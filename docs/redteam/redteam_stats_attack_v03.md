# Hostile Statistical Review v2: `draft_v01.md` v0.3 ("The Width of a Voice")

**Reviewer stance**: same hostile reviewer as `redteam_stats_attack.md` (the v0.2 attack).
Every check below was re-computed from the committed evidence files
(`reports/validation/results2/*`, `wave2/e8_results.md`, the LM envelope
sidecars, the AI corpus manifest + texts) or by re-running placement code from the
frozen artifacts with the project venv. Where I attack a missing analysis, I ran it
myself; the numbers are mine and reproducible (`mfw_tokenize` → truncate to 3,000
tokens → `MFWBlock.delta` vs `mfw_centroid` vs the sidecar quantiles — the exact
`rerun_entry_analysis.py` code path).

**Verdict in one line**: the remediation was largely real — the instrument, the LM
envelopes, the E8 idea, the cluster statistics, the floors, and the provenance language
are genuinely fixed — but v0.3 commits four new headline-level sins: the full-vocabulary
"entry" result has **no unprompted-entry control** and is ~80% base rate; the completion
"parity" claim is a **composition artifact that reverses under model matching** (their
own table shows completion > styled for every comparable model); "statistically
indistinguishable from a human pastiche" is an **unpowered non-test performed on an n
the paper's own evidence file declares non-inferential**; and the E8 gate is a
**post-hoc disjunction whose evidence file says FAIL where the paper says PARTIAL**.
Plus one flat factual error in the flagship section (§5.3 "McCarthy's envelope is the
widest on the shelf" — it is not, in either vocabulary, per the paper's own E8 table).

**Does v0.3 survive?** Not as written. But unlike v0.2, nothing here requires rebuilding
the instrument: every fix is "report the control you didn't run" (I ran two of them
below) or "stop saying the sentence your own table contradicts."

---

## Part I — New findings against v0.3

### G1. The missing control: unprompted samples already enter. Full-vocabulary "entry" is ~80% base rate

**Severity: FATAL to the full-vocabulary entry framing; MAJOR overall (fw-only survives)**

The paper reports styled entry (20.3% full / 30.5% fw-only @p90) against two
comparators: the same-author yardstick (84–88%) and the human pastiche. It never
reports the one comparator that isolates the *imitation* effect: **unprompted samples
on the same bound scenario, same truncation, same floor, against the same target
envelope**. I computed it (n=121 unprompted samples on the four bound scenarios with
≥3,000 MFW tokens, truncated to 3,000, vs the target's LM p90 — identical code path):

| Vocabulary | Unprompted entry @p90 | Styled entry @p90 (paper) | Imitation increment |
|---|---|---|---|
| full | **20/121 (16.5%)** | 48/236 (20.3%) | **+3.8 pp** |
| fw-only | 13/121 (10.7%) | 72/236 (30.5%) | +19.8 pp |

Per target, full vocabulary: McCarthy **19/29 (65.5%)** unprompted vs 73.2% styled;
Didion 0/33 vs 3.0%; Morrison 1/29 (3.4%) vs 5.2%; Ondaatje 0/30 vs 3.6%.
**McCarthy's envelope admits two-thirds of generic, never-prompted AI fiction on the
irrigation scenario.** Per model, full vocabulary, the styled-minus-unprompted increment
is within noise for *every* model (fable 28% vs 25%; gpt-5 40% vs 30%; opus 22% vs 10%;
sonnet 19% vs 15%; gpt-5-mini 12% vs **15%** — negative; qwen 0% vs 9% — negative).
This is exactly what the paper's own §5.6 predicts (full-vocab distance change −0.005,
CI brackets zero) and never connects to the entry tables.

Consequences:

- The abstract's "machine entry is real, graded, and structured: styled samples …
  enter at 20.3% (full vocabulary)" attributes to imitation what is mostly envelope
  porosity to AI house style on a deliberately adjacent scenario (§4.1's own design
  admission). At full vocabulary the *imitation* contribution to entry is ~4 points
  and per-model nonsignificant.
- The fw-only story survives and is genuinely strong: pooled 10.7%→30.5%; fable
  **0/20 → 36%**; gpt-5 45%→72.5%; gpt-5-mini 10%→35%. Note even here the paper's
  best number, gpt-5's 72.5%, sits on a **45% unprompted base** (9/20 of gpt-5's
  never-prompted samples already enter the target envelopes) — a fact that belongs in
  the same sentence as the 72.5%.
- Contribution 2 ("Entry is real, graded, and two-sided") and §5.2 must be restated
  as increments over the unprompted base, or the full-vocab rate demoted to a
  base-rate row. The data needed are already placed by `rerun_entry_analysis.py`
  (it places all unprompted samples for the approach block); the control costs zero
  additional compute.

**Neutralize**: add an "unprompted (bound scenario) entry" row to every entry table;
lead with fw-only (the vocabulary where the effect exists); state gpt-5's unprompted
base next to its styled rate.

### G2. Completion "parity" is a composition artifact; model-matched, completion *beats* styled prompting in 5/5 informative models

**Severity: FATAL to the parity claim (abstract, §2.3, §5.4, Discussion)**

The paper's pooled comparison (31.0% completion vs 30.5% styled, fw-only @p90) pools a
completion set with **zero gpt-5** (20/20 refusals; gpt-5 is the best styled model at
72.5%) against a styled set where gpt-5 contributes 29 of 72 entries. The §5.4 caveat
("not model-matched") names the problem and then the abstract ("parity with named-style
prompting"), §2.3 ("it reaches parity… not the near-ceiling rates"), §5.4 ("buys no
more entry than being told the author's name"), and the Discussion ("adds nothing over
the author's name") all assert the conclusion the caveat forbids. Computed from the
paper's own two evidence tables (completion_results.md per-model entries vs
entry_report.md per-model styled entries, fw-only @p90):

| Model | Completion | Styled | Direction |
|---|---|---|---|
| claude-fable-5 | 10/20 (50%) | 14/39 (36%) | completion higher |
| claude-opus-4-8 | 7/20 (35%) | 9/40 (22%) | completion higher |
| claude-sonnet-4-6 | 3/20 (15%) | 3/32 (9%) | completion higher |
| gpt-5-mini | 5/8 (62%) | 14/40 (35%) | completion higher |
| qwen3.6:35b | 2/16 (12%) | 3/28 (11%) | completion higher |
| claude-haiku-4-5 | 0/2 | 0/17 | tie (uninformative) |

Completion is higher in **5 of 5** informative models (exact sign test p = 0.031);
pooled over the six shared models: completion 27/86 (31.4%) vs styled 43/196 (21.9%).
The defensible sentence is the *opposite* of the paper's: *for the models that comply,
inheriting the author's opening buys roughly 1.4× the entry rate of being told the
author's name; the pooled rates look equal only because the provider best at styled
imitation refused the completion task.* This was computable from the paper's own
printed tables by inspection.

Aggravating: the completion analysis has **no clustering treatment at all** (naive CP
only; 87 samples in ~(model×target) cells of ~5) — the K4 remediation was applied
everywhere except the one analysis added after it.

**Neutralize**: replace the parity claim with the model-matched contrast; add
DEFF/cell-bootstrap intervals to completion_results; keep the refusal table (which is
good — I verified gpt-5's 20 outputs are genuine refusals: "Sorry, I can't continue
that novel…", word counts 30–73 with two partial summaries at 251/677 words).

### G3. "Statistically indistinguishable from a praised human pastiche" is an unpowered non-test on an n the paper's own evidence file forbids

**Severity: MAJOR (it is in the abstract)**

gpt-5 29/40 (72.5%) vs Brinton 27/36 (75.0%): Fisher two-sided p = 1.0 — and the
95% Newcombe CI on the difference is **[−21.5 pp, +17.2 pp]** before any clustering
correction. With clustering, worse: gpt-5's 40 samples sit in 8 (target×condition)
cells (computed ICC of the entry indicator 0.158, DEFF 1.63, n_eff ≈ 24.5), and
Brinton's 36 chunks are one novel by one author — the entry_report itself prints:
"chunks are NOT independent … **n is descriptive, not inferential**." The abstract
performs the exact inference the evidence file disclaims. A test that cannot
distinguish a 20-point difference does not establish indistinguishability; no
equivalence test (TOST) is run, and none could pass at these n's for any margin a
reader would accept. Additional unfairness in both directions, undisclosed at the
point of claim:

- **Selection**: gpt-5 is the post-hoc best of 7 models; Brinton is the only human
  measured. Best-of-7 vs n-of-1 needs a multiplicity caveat.
- **Base rates**: gpt-5's unprompted fw-only entry base is 45% (G1); Brinton has no
  measurable base, and her per-cell breakdown (gpt-5: McCarthy 10/10, Morrison 9/10,
  Didion 5/10, Ondaatje 5/10 — computed) pools targets of violently different widths
  while Brinton faces one target. The paper's own §5.3 corollary — "any claimed
  imitation success rate that does not state the target's envelope width is
  uninterpretable" — applies verbatim to its own abstract sentence, which compares a
  width-pooled rate to a single-width rate across two different shelves whose Delta
  scales are not commensurable.

**Neutralize**: "numerically comparable (72.5% vs 75.0%); the comparison is unpowered
(diff CI ±20 pp) and crosses shelves and targets" — or drop it from the abstract and
keep the per-target rows.

### G4. E8: evidence file says FAIL, paper says PARTIAL; the gate disjunction is post-hoc and internally incoherent

**Severity: MAJOR**

- `wave2/e8_results.md` final line: "**Overall E8: FAIL**" (3 of 4 shelves FAIL).
  The paper's §3.5 gate table prints "**PARTIAL** — pooled near-nominal" — a verdict
  category that exists nowhere in the gate tooling. The paper invented a softer verdict
  for its own table while (credit) §3.9 does name all five failing cells.
- **The gate is a three-way instrument where only one part can ever bite, and that part
  was placed under the data.** The disjunction is: naive binomial CI contains 0.90 OR
  rate ≥ 0.80. Computed from the E8 tables: under the naive-CI criterion alone,
  **13/48** cells fail (and the *pooled* CI excludes 0.90 on **all four** shelves —
  fw-only pooled is 83.7% [82.3, 85.1], a 6-point shortfall from nominal that the
  abstract rounds to "near the nominal rate. They do: 84–88%"). Under the
  cluster-adjusted CI the gate is vacuous — DEFFs run to 23, 38, 47, **55.7**, so the
  adjusted CI contains 0.90 for *every* cell including all five named failures (the
  paper itself uses this argument to exculpate the failures — a criterion that passes
  Foster Wallace at 71.5% can never fail anything). The only operative criterion is
  the 0.80 floor, and the observed marginal cells sit at 0.804, 0.807, 0.813, 0.814,
  0.824, 0.829 — the floor rescues **8** cells that fail the CI criterion; at a floor
  of 0.85 roughly 12 cells fail. The pass/fail count is an artifact of where the floor
  sits, and the floor sits just below the data.
- **Provenance**: the gate spec was committed in the *same commit* as the E8 results
  (`02cf9ee`, 2026-06-11 00:18 — code, gate, and results together), and the tool's
  docstring justifies the floor by naming a specific failing work ("a single off-style
  work (e.g. Stella Maris)") — the rationale was written with the failures in view.
  `RED_TEAM_SYNTHESIS.md` (committed before) specified only "~the nominal rate."
  This is the same same-session gate-fitting pattern the paper itself confesses for
  d18→MFW in §3.6 and promises it has outgrown.
- **Would a pre-stated gate have failed the instrument?** Yes — any natural one
  ("per-author CI contains 0.90", "pooled CI contains 0.90", or "rate ≥ 0.85") fails
  somewhere on every shelf or in double-digit cells. The honest reading: held-out
  same-author windows under-enter their envelopes by 2–6 points systematically (work
  heterogeneity), the envelopes are mildly miscalibrated in the *strict* sense, and
  the right response is exactly what the analysis actually does — use the measured
  84–88% as the empirical yardstick rather than nominal 90% — while the gate verdict
  theater (PARTIAL) adds nothing and will be found out by anyone who opens the
  evidence file.

**Neutralize**: print FAIL in the gate table with the same sentence §3.9 already has;
drop the cluster-CI exculpation (or apply it consistently and admit the gate can't
fail); state the floor as a post-hoc operating choice, dated, like §3.6 does for the
variant rule. The science (pooled yardstick + named failures) is fine; the labeling
is not.

### G5. Chassis numbers: two constructions 6× apart, the headline one violates the paper's own hard floor

**Severity: MAJOR**

- Contribution 4 and §5.5 quote MFW movement **−0.030 Delta [−0.048, −0.013], Holm
  p = 0.042** from `r3_dimension_gap.json` — computed at **native length on n = 318**,
  which includes the 76 sub-floor samples *and the 6 hard-floor samples the paper says
  are "excluded from every claim"* (§3.7). §5.6 quotes the corrected matched-length
  construction on the floor-compliant n = 236: **−0.005 [−0.042, +0.040]** — brackets
  zero, not significant. These are the same physical quantity, 6× apart, and the paper
  presents both without reconciling them. The CI that "excludes zero" and the Holm
  p = 0.042 belong to the construction v0.3 itself superseded.
- The entire texture table (repetition +0.975, ttr +0.731, closures 14–21%) — the
  mechanism centerpiece — is from the same uncorrected n=318 native-length run, never
  re-executed under the floors and truncation that v0.3 made its standard everywhere
  else. Mitigation I checked: within-model styled/unprompted median lengths are close
  (ratios 0.91–1.16) for all API models, so the length-sensitive dimensions (ttr,
  vocabulary richness, repetition) are probably not badly contaminated — except gemma4
  (ratio 0.76, all sub-floor), which is in the n=318. "Probably survives" is the
  paper's job to demonstrate, not the reviewer's to concede.
- "Closes only ~6% of the gap under the function-word vocabulary": the arithmetic is
  −0.0868/1.418 = 6.1%, where 1.418 is the **median styled target distance**, not a
  gap. The parallel to the full-vocab "closure of −2.9% to −0.8%" (denominator:
  unprompted gap 1.654) uses a different denominator class. Using the matched
  unprompted distance (≈1.505) gives 5.8% — the conclusion stands, but the two
  "closure" percentages in one abstract sentence are not computed the same way, and
  the fw-only closure carries no test, no Holm family, and no per-target sign
  breakdown (the full-vocab claim has all three).

**Neutralize**: re-run R3 on the primary stratum at matched length (one flag in the
existing tool); quote one full-vocab movement number; compute both closures over the
same denominator; give the fw-only −0.087 its per-target signs.

### G6. §5.3 factual error: McCarthy's envelope is *not* "the widest on the shelf in both vocabularies"

**Severity: MAJOR (flat factual claim, contradicted by the paper's own E8 table)**

From `e8_results.md` LM p90 columns: full vocabulary — **Robinson 1.731 > McCarthy
1.715** (Ishiguro ties at 1.715). Function words only — McCarthy (1.553) is **fourth**,
behind **Murakami 1.738, Foster Wallace 1.689, Ishiguro 1.575**. McCarthy is the widest
*of the four imitation targets*, which is what §5.3 needs and should say. The error
also wastes the shelf's best free test of the width thesis: Murakami, Robinson, FW,
and Ishiguro have wider-or-comparable envelopes than McCarthy — if width explains
enterability, generic styled samples should enter *those* envelopes at high rates too.
That analysis costs nothing (all placements exist) and is not run.

### G7. "Enterability = envelope width" is half tautology, half true — and the true half is fw-only

**Severity: MAJOR as framed (contribution 3); MINOR if restated)**

Entry rate is P(distance ≤ width-quantile): at any fixed distance distribution it is
*mechanically* increasing in width. The non-circular content is the empirical claim
that the distance distributions are flat across targets ("differ far less," §5.3).
Checked: **fw-only, yes** — per-target styled medians 1.377–1.477 (spread 0.100)
against width spread 0.326; width does the work. **Full vocabulary, no** — medians
1.591–1.788 (spread 0.197) against width spread 0.306; the models are also genuinely
*closer* to McCarthy in absolute Delta, so width and proximity are comparably sized
contributors. The width-independent restatement the section needs is one line per
target (the styled median's percentile within the target's own envelope): styled
median sits ≈ p75 of McCarthy's envelope vs **above p99** of Didion's. Also: the
ordering claim has n=4 targets (P(perfect ordering by chance) = 1/24 per vocabulary,
and the two vocabularies are not independent), and "LM p90 in Delta units" is
shelf-normalized — not the portable cross-study scalar contribution 3 sells (Delta is
z-scored per shelf; Austen's 1.453 and Didion's 1.239 are not on one scale).

**Neutralize**: state the mechanical direction openly ("wider envelopes admit more at
fixed distance by construction; the finding is that fw-only distances are flat, so
width is the binding constraint"); add the percentile-of-median row; confine the
"width is the denominator" proposal to within-shelf use; run the G6 wide-non-target
check.

### G8. §5.8 recycles the criterion the paper spent §3.9 burying

**Severity: MINOR**

"Surviving v0.2 controls: prompt-paraphrase sensitivity (**off-manifold-rate 1.000**
under every phrasing at full-novel scale)" — off-manifold-vs-full-novel-W is precisely
the measure §3.9 demonstrates is vacuous for window-scale text (the rate is 1.000 for
*Austen* too). The per-phrasing distance medians (1.591–1.625, spreads 0.019–0.106 —
verified against `paraphrase_sensitivity.md`) are fine and sufficient; the resurrected
off-manifold rate should go. The paraphrase battery has not been re-run against LM
envelopes — one sentence should say so.

### G9. "Two independent adversarial reviews": independent of each other, not of the project

**Severity: MINOR (disclosure), MAJOR if a venue reads "independent" as "external"**

The two reviews (`redteam_stats_attack.md`, `redteam_claims_attack.md`) were
commissioned by the author, executed by Claude-family agents inside the same
human–Claude collaboration that wrote the paper, and committed together in one commit
(`7be8bf6`, 2026-06-10) against a never-circulated internal draft. The accounts in
§1/§3.9/§5.1 match the git history (the self-caught-artifact narrative is *not*
sanitized on the facts — dates, sequence, and the E6 contradiction are reported
accurately, and the remediation plan was committed before the re-analysis ran, as
claimed). But "independent" will be read as "external," and §8.11's otherwise thorough
disclosure discloses collaborative *writing*, not collaborative *reviewing*. The
Discussion also credits the measurement frame ("fails loudly … caught its own
headline") for what was actually commissioned-review labor — v0.1 and v0.2 printed the
E6 contradiction (1.341 vs 0.800) unreconciled and the frame did not catch it; the
agents did, after drafting.

**Neutralize**: "two adversarial reviews, run independently of each other by AI agents
within the same collaboration (disclosed in §8.11), both recomputing from frozen
artifacts" — still a good story; now also a true one in the reading a stranger gives it.

### G10. Construction checks that PASSED (reported for fairness)

**Severity: none — attacks attempted and neutralized by the code**

1. **Leave-work-out is correct.** `LengthMatchedEnvelopes.build_from_space` excludes
   the window's own work from its centroid; `held_out_entry` re-derives thresholds
   from other works only (genuinely non-circular); windows are non-overlapping with
   trailing partials dropped.
2. **The centroid-estimator mismatch is immaterial.** Samples are scored against the
   full k-work centroid while envelope windows face (k−1)-work LOO centroids — a real
   asymmetry that I quantified by re-scoring all 236 primary styled samples against
   every LOO centroid: median inflation +0.001 to +0.006 Delta per target (k = 4–9),
   entry counts change by ≤1 sample in 8 target×vocabulary cells. Dead end; the
   construction survives.
3. **Units are consistent.** Envelope windows, sample truncation, and both floors are
   all in MFW tokens (`\b[a-z']+\b` over lowercased text); the 3,000-token window
   matches the E6 3,000-word framing closely enough that nothing turns on it; the 236/76/6
   strata recompute exactly.
4. **gpt-5 refusals are real.** I read the outputs: 20/20 begin "Sorry, I can't
   continue that novel…" (two append plot summaries, 251/677 words). The
   classification is token-count-based in the tool, but the abstract's "refused
   20/20" is substantively accurate.
5. **Numbers trace.** Spot-checked >30 values across entry_report (all six entry-table
   rows, all per-model/per-target/per-condition rows, ICC/DEFF columns), e8_results
   (pooled rows, per-author quantiles, all five failures and driver works), Brinton
   blocks, approach tables incl. Ondaatje p=0.074 and Morrison fw 0/58, rank-vs-metric
   medians and CIs, translation block (5/8 pairs, +0.059, p=0.100), chassis per-target
   signs, completion compliance/entry tables, fwonly_comparison (0.941→0.911,
   96.2→92.3, 97.4), paraphrase medians, summary.md (AUC 0.941, 14/15, 96.2/96.2).
   All match the draft except the items in G11.

### G11. Number drift and hygiene

**Severity: NITPICK (each), but they are the kind reviewers collect**

- **Appendix B says "4/48 author×vocab cells fail"; §3.5 and §3.9 say five.** Five is
  correct (Whitehead ×2, Foster Wallace, Proulx, Fitzgerald) — Appendix B conflates
  distinct authors (4) with cells (5).
- §4.1/§4.3 say "159 generations recorded" for completion; the manifest holds **160**
  completion records, one of which (qwen3.6) is zero-length and silently dropped at
  load. Say "160 recorded, 1 zero-length excluded" — the styled condition already
  gets exactly this treatment in §4.3.
- §5.7 cites `redteam_claims_attack.md §7` as the evidence source for the "≈0.8–1.1×"
  matched-length self-consistency ratio — a paper number whose only provenance is the
  red team's recomputation. Promote the computation into an owned evidence file.
- `completion_results.md` prints raw CP tuples ("CP (0.215…, 0.418…)") — unfinished
  formatting in a cited evidence file.
- F1's stub caption still carries the retired criterion (flagged in-stub as must-fix;
  hold it to that).

---

## Part II — Remediation audit of my v0.2 findings (F1–F15)

| v0.2 finding | Status in v0.3 | Notes |
|---|---|---|
| F1 entry criterion unsatisfiable | **FIXED** | LM envelopes + E8; the artifact is reported as a result (§3.9/§5.1), not buried |
| F2 clustering ignored | **FIXED** for entry/approach (3 intervals everywhere); **NOT applied** to the new completion analysis (G2) |
| F3 "pre-registered" | **FIXED** — §3.1/§3.6/App B provenance language is now exemplary; but the E8 gate repeats the same-commit gate-fitting pattern (G4) |
| F4 threshold fragility | **FIXED** — p90/p95/p99 sweeps with threshold-quantile bootstrap CIs in every table |
| F5 scenario confound | **FIXED** — scenario-matched null, Ondaatje conceded n.s., per-model rates in main text, premise authorship disclosed |
| F6 exemplar claim | **FIXED** — dropped; per-condition rows show 20.2 vs 20.5 |
| F7 89-vs-52 pastiche | **PARTIALLY** — fw-only pastiche run, per-model bests, in-world caveat all present; replaced by the new parity overreach (G3) |
| F8 translation bound | **FIXED** — recomputed at matched length, found underpowered, cut, documented (§8.2) |
| F9 floor violations | **FIXED** for entry (strata enforced, 6 exclusions named); **NOT** for §5.5 chassis/texture, still n=318 incl. hard-floor samples (G5) |
| F10 PD "replication" | **FIXED** — §9.1 reframed as executable-pipeline release |
| F11 chassis direction | **MOSTLY FIXED** — immobility adopted, signs split disclosed; stale −0.030/Holm-0.042 still quoted as headline support (G5) |
| F12 PAN | **FIXED** — hostile genre reading answered in App A; "inverts" language consistent |
| F13 generation confounds | **FIXED** — zero-length disclosure, three decoding regimes named |
| F14 metadata hygiene | **MOSTLY** — E3 inheritance flagged in-table; artifact SHAs in App B |
| F15 wording items | **FIXED** — two-valued percentiles disclosed, C4 family retired, §5.1 length-qualified |

That is 11 clean fixes of 15, honestly executed. The synthesis plan was followed.

---

## Triage table (v0.3)

| # | Finding | Severity | Minimum fix |
|---|---|---|---|
| G1 | No unprompted-entry control; full-vocab entry ≈ 80% base rate (16.5% vs 20.3%); McCarthy admits 65.5% of unprompted samples | **FATAL** (full-vocab entry framing) | Add unprompted-entry rows; restate entry as increment; lead with fw-only |
| G2 | Completion "parity" reverses under model matching (5/5 models completion > styled, sign p=.031; matched pools 31.4% vs 21.9%) | **FATAL** (parity claim) | Replace parity sentence in abstract/§2.3/§5.4/Discussion; add clustering to completion stats |
| G3 | "Statistically indistinguishable" from Brinton: diff CI ±20 pp; Brinton n declared non-inferential by own evidence file; best-of-7 selection; cross-shelf | **MAJOR** | "Numerically comparable; comparison unpowered"; or cut from abstract |
| G4 | E8: evidence says FAIL, paper says PARTIAL; gate disjunction post-hoc (same-commit), floor placed under the data, cluster-CI disjunct vacuous (DEFF ≤ 55.7) | **MAJOR** | Print FAIL; date the floor as post-hoc; drop the vacuous exculpation |
| G5 | Chassis −0.030 (native, n=318, floor-violating, Holm .042) vs −0.005 (matched, n=236, n.s.) both quoted, unreconciled; texture table never re-run under floors; ~6% denominator mismatch | **MAJOR** | Re-run R3 on primary stratum; one number; same denominators |
| G6 | "McCarthy widest on the shelf in both vocabularies" — false (Robinson full; Murakami/FW/Ishiguro fw-only) | **MAJOR** | "Widest of the four targets"; run wide-non-target entry check |
| G7 | Width-enterability: mechanical at fixed distance; distance flat only fw-only; n=4 ordering; Delta width not cross-shelf portable | **MAJOR** (as contribution 3) | State the construction; percentile-of-median row; scope the scalar |
| G8 | §5.8 resurrects "off-manifold-rate 1.000" (the vacuous criterion) as a robustness control | MINOR | Quote distance medians only; note paraphrase not re-run vs LM-W |
| G9 | "Independent adversarial reviews" = same-collaboration Claude agents, one commit; review provenance undisclosed | MINOR/MAJOR | One clause in §1 + §8.11 |
| G10 | Construction checks passed (LOO correct; centroid mismatch ≤0.006 Delta, ≤1 entry; units consistent; refusals verified) | — | Keep; cite if challenged |
| G11 | 4/48-vs-5/48; 159-vs-160; red-team file as evidence source; raw CP tuples; F1 caption | NITPICK | Sweep |

## What survives

1. **The instrument and the E8 *idea*** — a same-author positive control at matched
   length is the right permanent fix, and the envelope construction itself is clean
   (G10). The gate *verdict labeling* is the problem, not the machinery.
2. **The fw-only entry result, restated as an increment**: 10.7% unprompted → 30.5%
   styled → (model-matched) ~1.4× more under completion; fable 0/20 → 36%; gpt-5
   45% → 72.5%. That is a real, large, controlled imitation effect — the paper's
   strongest result, currently buried under the confounded full-vocab number.
3. **The two-sided human baseline** (Brinton 94.4% full / 75.0% fw-only with the
   content-reuse interpretation) — as description, not as an equivalence test.
4. **Approach vs the scenario-matched null** (Ondaatje conceded), the rank-vs-metric
   decomposition, the floors, the threshold sweeps, the cluster intervals, the
   refusal data, and the provenance honesty of §3.1/§3.6/Appendix B.
5. **Width as the binding constraint under the function-word vocabulary** — with the
   tautological component stated, this is still a useful reframe.

*Generated by hostile statistical review, 2026-06-11. All recomputations from the
frozen artifacts and corpus in this worktree; placement code path identical to
`rerun_entry_analysis.py`; git evidence from `git log`/`git show` on this worktree.*
