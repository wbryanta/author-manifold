# Adversarial review record

This directory holds the adversarial reviews run against this research
program, published in full — including the ones that rejected the work.

**Read this first if you are skimming.** Three review cycles are recorded
here, and they do **not** all attack the same thing:

| Cycle | Date | What it attacked | Verdict | Disposition |
|---|---|---|---|---|
| 1 | 2026-06-10 | **This paper**, draft v0.2 ("Approaching Without Entering") | REJECT as framed | Fixed by re-analysis, not wording. The headline entry criterion was retired as a length-calibration artifact and replaced with length-matched envelopes. |
| 2 | 2026-06-11 | **This paper**, draft v0.3 ("The Width of a Voice") | MAJOR REVISION | All findings addressed in v0.4/v0.5.4. The completion "parity" claim was retracted and inverted; the E8 gate verdict is reported as the committed **FAIL** throughout. |
| 3 | 2026-07-02 | **A different, withdrawn study** — the June 2026 reasoning-effort dose-response experiment. **Not part of this paper.** | Not submittable as framed | Both headline claims retracted before any external reader saw them. The study was withdrawn; this paper never contained it. |

**The paper's own §9.2 refers to "both adversarial review reports."** That is
cycles 1 and 2 — the two that reviewed this paper. Cycle 3 is published here
as well because the retraction record is part of the work, but it reviewed a
different experiment. Quotations from cycle 3 (notably "Not submittable as
framed") are **about the withdrawn effort study, not about this paper.**

Every file in this directory carries a status header saying which draft it
attacked and what became of its findings.

## Files

- `redteam_stats_attack.md` — cycle 1, statistics lane, draft v0.2
- `redteam_claims_attack.md` — cycle 1, claims lane, draft v0.2
- `RED_TEAM_SYNTHESIS.md` — cycle 1 synthesis + remediation plan
- `redteam_stats_attack_v03.md` — cycle 2, statistics lane, draft v0.3
- `redteam_claims_attack_v03.md` — cycle 2, claims lane, draft v0.3
- `cycle3_2026-07/` — cycle 3, the **withdrawn** effort study (see its README)

## Review provenance — who these reviewers were

These are **self-commissioned** reviews, not journal peer review, and the
distinction matters, so it is stated plainly rather than left to inference.

- **Cycles 1 and 2** were run by adversarial reviewer agents given a hostile
  brief (falsifiable claims only; recompute every number from the committed
  evidence before attacking it). Both lanes did in fact recompute: in cycle 1
  every recomputed number matched, and the failures they found were all in
  the inference layer, not the arithmetic. Cycle 2's statistics lane ran the
  analyses the paper had *not* run, and its numbers are reproducible from the
  released artifacts.
- **Cycle 3** was a six-lane independent review plus a senior consolidation
  pass, run against the effort study's raw artifacts.
- **"SOL"**, which appears in commit `9aea08b` ("SOL re-audit patch"), refers
  to a **cross-family adversarial reviewer**: gpt-5.6-sol, an OpenAI-family
  model used as an outside gate on work produced with Anthropic-family
  models. It is used at plan-time and pre-merge gates throughout this
  project, and the 2026-08-06 forensic review was gated by it in two rounds
  plus an independent fresh-context bar-raiser pass.

Cross-family review is deliberate and is the answer to the obvious objection
that a project reviewing its own work with the same model family is grading
its own homework. Disclosing it helps rather than hurts: a reviewer from a
different lab's model family has no shared priors to protect, and in practice
it dissented — the 2026-08-06 round corrected a robustness footnote that
claimed pooled rates were unaffected when they in fact moved (they stayed
within interval, which is what is now stated).

None of this is a substitute for external peer review. It is a record of what
was tried to break the work before shipping it, and of what broke.

## What the reviews actually changed

Four headline claims were retracted and corrected across the three cycles:

1. **"0/318 styled samples ever enter"** (cycle 1) — a length-calibration
   artifact; the criterion could not be satisfied by the target authors' own
   prose. Retired and replaced with length-matched envelopes.
2. **"Completion reaches parity with named-style prompting"** (cycle 2) — a
   composition artifact created by GPT-5 refusing all completions.
   Model-matched, completion *beats* naming the author for every informative
   model.
3. **Two effort-study headlines** (cycle 3, p = 0.011 and p = 0.021) —
   construct-validity failures in both. Withdrawn.

The E8 positive control's strict verdict is **FAIL**, and it is reported as
FAIL — in the paper, in the README, and by the gate tooling, which exits
nonzero by design.

*This README added 2026-08-06 by the forensic code and data review
(findings E-3/E-4/E-5/E-6, C-6).*
