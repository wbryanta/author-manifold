# Red Team Synthesis — draft v0.2 verdict and remediation plan

Date: 2026-06-10. Inputs: `redteam_stats_attack.md`, `redteam_claims_attack.md`
(independent adversarial reviews; both recomputed claims from frozen evidence —
every recomputed number matched, the failures are all in the inference layer).

## Verdict: REJECT v0.2 as framed. The data contains a stronger honest paper.

## Kill list (deduplicated, ranked)

### FATAL — must be fixed by re-analysis, not wording

**K1. The entry criterion is unsatisfiable at sample length (both attackers,
independently).** W-p90 (Delta 0.800) is calibrated on full-novel LOO
distances; Delta inflates at sample length. Authors' OWN 3,000-word windows
sit at median 1.341 from their own centroid (E6) — Austen's own novels,
chunked like the test samples, enter Austen's region **0/74**. Therefore
0/318 (and Brinton's 0/37) is a length-calibration artifact carrying no
information about imitation. gpt-5 unprompted (1.320) is *closer* than
authors' own windows (1.341) — both numbers were printed in v0.2,
unreconciled.
**Fix:** length-matched per-author W envelopes (LM-W) built from same-length
windows of each author's works (E6 machinery exists); a **permanent
same-author positive control** (author's own held-out windows must enter
their own LM envelope at ~the nominal rate) as a new validation gate (E8);
all entry claims restated against LM-W.
**The honest result already in the data:** under length-matched envelopes,
Brinton enters Austen's ~95% (35/37); styled models ~25%; styled-AI median
1.710 vs human-self 1.341; 4/318 styled samples beat the human-self p25.
Two-sided, mechanistic, stronger than the artifact it replaces.

**K2. The identity conjecture is falsified by our own artifact.** Cross-author
full-novel placements enter other authors' regions 14.7% (39.1% fw-only —
opposite of the conjecture's prediction). "To enter it is nearly to be the
author" is removed, not softened.

**K3. "Pre-registered" is indefensible.** Git archaeology: ADR drafted 14:01,
d18 fails gates, MFW swapped in 15:16 (against the ADR's own stop-rule
wording), E4 at 15:17; the variant-selection rule first appears in the same
minute as the results; the Holm family was expanded after results were known.
**Fix:** replace all "pre-registered/pre-stated" language with the truth:
"gates and thresholds were specified before AI placement, within the same
development session; we claim engineering discipline and full public
reproducibility, not formal preregistration." The d18→MFW pivot is reported
as an explicit, dated methodology change (it already is in ADR-0041 — the
PAPER must say it too). Holm family membership documented with dates.

### MAJOR — must be fixed (analysis or scope)

**K4. Clustering.** ICC 0.47–0.54 within (model×target×condition) cells;
design effect ≈3; honest one-sided bound on the (re-defined) enter rate is
~2.7–4.6%, not 0.94%. Report cluster-aware bounds as primary; the §4.5
"unaffected by clustering" sentence is deleted.

**K5. Floor violations inside the headline.** 83/318 styled samples below the
3,000-word practice floor; **6 below the 1,500 hard floor** while the paper
says such texts "license no claims at all." Re-analysis excludes sub-floor
samples (or reports them separately); gemma4's regeneration at proper length
or exclusion decided by result-stability.

**K6. Approach claim confounds.** Target↔scenario design binding (unprompted
night_ferry already lands nearest-Ondaatje 57.5%); corrected scenario-matched
null is 0.1875; per-model approach spans 10%–75% ("reliably" is false for
gpt-5-mini); "approach" is RANK movement while metric distance is flat/+0.03
away — restate as "rank-up, distance-flat" (which is also the cleanest
mechanistic result, consistent with R3). "Most strongly with exemplars" not
robust to clustering — demote or test properly.

**K7. Human comparisons not design-supported.** 89%-vs-52% mixes shelves,
candidate counts, one-human-vs-model-average (best model 75%), and a PD
vocabulary containing mr/mrs/miss/sir/lady with no fw-only pastiche run.
**Fix:** fw-only pastiche run; per-model (not averaged) comparison; explicit
cross-shelf caveats; or move to a length-matched same-shelf design.
Translation bound (full-novel pairs vs sample distances; n=13) is scale-mixed
— recompute at matched length or cut.

**K8. Untested stronger condition.** Completion prompting (the contrast
literature's actual mechanism) was never run. Add a completion condition to
the corpus (model continues the author's own opening passage) before any
"strongest condition" claim; otherwise the claim is deleted and the
limitation stated.

**K9. Threshold fragility.** Under fw-only one sample sits inside W-p95;
37/318 inside p98; styled percentiles take only two values (resolution).
Entry claims must be reported across thresholds (p90/p95/p99) with the W
quantile-estimation uncertainty (bootstrap) attached — under LM-W envelopes.

**K10. Chassis direction.** −1.8% is Holm p=0.0417 with positive sign for 2/4
targets: claim **immobility** (CI brackets zero-to-slightly-negative), not
directed movement-away. Abstract metaphor-caricature mention fails our own
≥25% bar (19.8%) — self_focus only, or restate bar.

**K11. Disclosure gaps.** Add: scenario/prompt authorship (Claude), target
selection rationale, Claude = 4/8 models, decoding asymmetry
(Claude-no-thinking vs GPT-5 default reasoning). The PAN "degrades
predictably" wording becomes "degrades and below the floor inverts."

### What survives (the rebuilt paper's spine)

- The percentile measurement frame and gate discipline (honestly labeled),
  E7 negative control, public replication shelf.
- Matched-length off-manifold separation: styled AI 1.710 vs human-self
  1.341 — real, with honest overlap reported (4/318 below human-self p25).
- The two-sided length-matched entry result (Brinton ~95% vs models ~25%).
- Texture-moves / chassis-immobile decomposition (restated per K10).
- Model self-attribution 97.8% (variance ratios restated at matched length).
- Approach-as-rank for 3/4 targets, 6/8 models, against the corrected null.
- The PAN boundary characterization (with inversion stated plainly).

## Remediation plan (Results 2.0)

1. **E8 positive control + LM-W envelopes** (new gate; E6 machinery): build
   per-author length-matched envelopes at 3,000w; verify authors' held-out
   windows enter their own envelope at ~nominal rate. ~1 day.
2. **Re-run all entry/approach analyses** against LM-W with cluster-robust
   bounds, multi-threshold reporting, floor-compliant sample set, corrected
   approach null, fw-only pastiche run, length-matched translation bound.
   ~1 day.
3. **Completion condition**: generate (8 models × 4 targets × 5; opening
   ~600 words of a target novel, model continues ~3,500 words; rights: same
   in-context-only handling as exemplar) + place. ~1 day incl. generation.
4. **Rewrite**: abstract/intro/results/discussion to the new headline;
   conjecture out; pre-registration language out; disclosure expanded;
   Holm registry rebuilt with dated family. ~1 day.
5. Re-freeze (v3), update mirror, re-run both red-team agents on v0.3.

**Candidate honest headline:** *Length-matched, a dedicated human pastiche
enters its target author's envelope almost always; frontier models prompted
the same way enter a quarter of the time, raise the target's rank without
closing the function-word distance, and no condition tested — including
in-context exemplars — moves the chassis.*
