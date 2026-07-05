# Adversarial cycle 3 (2026-07): the effort-study headlines, red-teamed and retracted

This directory documents the third self-commissioned adversarial review cycle of this
research program — the one that **overturned two significant-looking headline claims
before any external reader saw them**. It is published deliberately: the retraction
record is part of the work.

## What was claimed (June 2026 extension — never part of the paper)

A multi-vendor "reasoning-effort dose-response" experiment (gpt-5, Claude Opus 4.8,
Gemini 2.5, DeepSeek; 15 conditions, ~450 samples, 10 target authors) produced two
apparently strong results:

1. **"Test-time reasoning restores authorial voice in gpt-5"** — 9/10 authors moved
   closer to the target author's function-word centroid under high reasoning effort
   (sign p = 0.021; cross-model contrast p = 0.011).
2. **"Reasoning universally closes the function-word surprisal deficit"** — all four
   vendors' outputs moved toward the human fw-surprisal level with reasoning
   (necessary-but-not-sufficient framing).

These are exactly the kind of numbers that get rushed to a preprint.

## What the red team found

An independent 6-lane adversarial review (statistics, measurement validity, cross-lab
confounds, novelty, reproducibility, claims calibration — with a senior pass that
re-derived the worst findings from raw artifacts) is committed verbatim as
[`ADVERSARIAL_REVIEW_2026-07-02.md`](./ADVERSARIAL_REVIEW_2026-07-02.md). Its two fatal
findings, both subsequently **confirmed by targeted controls**:

- **The "identity restoration" is generic drift, not target-specific.** Decomposing
  each sample's movement against all 15 author centroids
  ([`control_target_specificity.json`](./control_target_specificity.json)): ~2/3 of
  gpt-5's movement is toward *all* authors; the target-specific residual is null
  (p = 0.34). No vendor shows target-specific movement. Also: no cross-vendor contrast
  had ever been computed, and none is significant when computed (the Gelman–Stern
  error); the gpt-5 effect does not survive Holm correction within its family.
- **The "entropy restoration" is a mean-level confound.** Per-sample fw-surprisal
  variance correlates r = 0.93 with the mean; under the scale-free CV² control
  ([`control_cv2.json`](./control_cv2.json)) **no vendor restores dispersion** and
  Gemini significantly reverses. The mean itself rises significantly in only 2 of 4
  vendors.

A follow-up detection dose-response (Fast-DetectGPT;
[`detection_dose_analysis.json`](./detection_dose_analysis.json)) showed reasoning
does move text toward the human detector band (Gemini/DeepSeek 9/10 authors,
p = 0.021) — but the detector statistic is 87% explained by the same fw-surprisal
mean shift (r = −0.93), i.e. the same effect re-expressed, not a new axis; and all
machine text remains trivially separable from the human band.

## Outcome

Both headline claims were **retracted**. What survives: a modest, honest fact —
vendor reasoning effort shifts the *location* of the function-word surprisal
distribution toward human levels in some vendors (significant in 2/4), without
restoring dispersion and without buying any author-specific movement — plus a
reusable pair of controls (target-vs-others decomposition; CV² mean-control) that any
future "X humanizes LLM writing" claim should have to pass.

The paper ("The Width of a Voice") never contained these claims; its findings stand
on the separately-frozen and separately-audited foundation results. The one thing the
cycle contributed to the paper is a discriminant-validity limitation, stated in its
Limitations section.

The raw experiment (generation scripts, corpus manifest, full result set) lives in the
private research repository; the adversarial review and the control/detection results
included in this directory are the complete published record of the cycle — every claim
above traces to a file here.

*Cycles 1–2 (earlier retractions and corrections on the foundation results) are
documented in the sibling `redteam_*.md` files in the parent directory.*
