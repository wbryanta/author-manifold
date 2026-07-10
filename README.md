# author-manifold

**An author-relative measurement space for stylometric placement** — the
instrument, validation harness, corpora, and recorded results behind
**"The Width of a Voice: Placing Machine Imitation Inside Authors' Own
Variation"** (Will Bryant, preprint v0.5.4 — PDF at
[`docs/paper/`](docs/paper/), DOI: [10.5281/zenodo.21210011](https://doi.org/10.5281/zenodo.21210011); targeting
CHR 2027).

Instead of measuring "voice distance" from a single privileged origin, the
instrument calibrates on shelves of known authors measured **relative to
each other**, persists the empirical within-author (W) and between-author
(B) distance distributions, and reports every new placement as a percentile
of those distributions: *"distance to austen-jane is at p38 of
within-author variation"* is meaningful with no reference author at all.

## Headline findings (v0.4 — Results 2.0, length-matched envelopes)

All entry numbers are read against per-author **length-matched envelopes**
(LM-W: 3,000-MFW-token windows, work-level leave-one-out), under the
**function-words-only** vocabulary as primary — the full-vocabulary framing
is topic-porous and reported as secondary. The earlier full-novel W-p90
entry criterion (v2: "0/318 enter") was a length-calibration artifact
caught by adversarial review and is retired; see
`reports/validation/author_space/wave2/PRIMARY_ARTIFACT.md` (Number Freeze v3) and
`docs/PAPER_DRAFT.md` §4-5.

| Finding | Number |
|---|---|
| Styled entry as a **controlled increment** over the unprompted base rate (fw-only, @p90): never-prompted AI on the same scenarios already enters 13/121 (10.7%); naming the author raises it to 72/236 (30.5%) | **+19.8 pp** [+4.3, +33.5] cluster-bootstrap 95%, excludes zero (full-vocabulary increment: +3.8 pp [−12.6, +18.6] — porosity, not imitation) |
| Model-matched **completion vs named-style** (fw-only, @p90): continuing the author's own text beats being told the author's name for every informative model | **5/5** completion-higher, exact one-sided p = 0.031; GPT-5 (the best styled model) refused all completions — the previously reported pooled "parity" was that composition artifact |
| **Envelope width predicts entry** (de-circularized: all 15 shelf authors as pseudo-targets for 309 unprompted samples) | Pearson **r = +0.844** [+0.59, +0.95] fw-only (full vocab +0.73); Ishiguro is the wide-but-distant outlier |
| **E8 positive control** (held-out windows inside own LM p90) | strict gate as committed: **FAIL** (3/4 shelves); the observed self-entry yardstick is reported instead — pooled 83.7–87.8% (`reports/validation/author_space/results2/e8_yardstick.md`) |
| Human pastiche (Brinton 1913 vs Austen's LM envelope) — **descriptive juxtaposition only** (chunks of one novel, not independent) | 27/36 (75%) fw-only chunks enter Austen's p90; 34/36 full-vocabulary |
| Public-domain shelf validation (9 authors / 35 novels, fully shipped) | E1 separation **AUC 0.999**, E2 leave-one-out attribution **100%** top-1 |
| Contemporary shelf validation (15 authors / 78 novels, artifacts shipped, texts not) | E1 AUC 0.941, E2 top-1 96.2% |

Exact statistical treatment (Clopper-Pearson + design-effect-adjusted +
cluster-bootstrap intervals on every pooled rate, threshold-quantile CI
sweeps, exact tests, Holm registry):
`reports/validation/author_space/results2/entry_report.md` and
`reports/validation/author_space/results2/controls_results.md`; instrument validation
remains locked to Number Freeze v2
(`reports/validation/author_space/wave2/tier1_statistics.md`).

**Method note — adversarial review is part of the pipeline.** The results
above survived three full red-team cycles run against the project's own
claims and statistics (v0.2: `docs/redteam/redteam_stats_attack.md`,
`docs/redteam/redteam_claims_attack.md`, synthesized in
`docs/redteam/RED_TEAM_SYNTHESIS.md`; v0.3: the `*_v03.md` attacks;
cycle 3: `docs/redteam/cycle3_2026-07/`). The first cycle retired the
full-novel entry criterion and forced the length-matched re-analysis; the
second formalized the unprompted-entry control, the model-matched
completion comparison, the de-circularized width test, and the honest E8
FAIL. The third is published in full deliberately: a follow-on experiment
produced two significant-looking headline results (p = 0.011 / p = 0.021)
— an independent six-lane review plus targeted controls found two
construct-validity failures, and **both claims were retracted before any
external reader saw them**. Four headline claims retracted and corrected
across three cycles; each cycle's findings are owned by the pipeline
(`reports/validation/author_space/results2/`), not hand-patched.

## This is NOT an AI detector

The instrument answers a calibrated **authorship** question — "does this
text sit inside a specific author's measured manifold?" — not "was this
written by AI?". AI text landing in or out of an envelope is a measured
placement; human text by any uncalibrated author also lands wherever it
lands. The interesting results are comparative: calibrated authors
re-enter their own envelopes at 83.7–87.8% (observed E8 yardstick) while
styled AI reaches 30.5% fw-only against a 10.7% unprompted base; entry
rates track envelope *width* (r = +0.844) as much as imitation skill; and
a model continuing an author's own text enters more than a model told the
author's name (5/5 informative models).

## Quickstart — the paper's §9.2 replication claims (~5 minutes + tests)

The paper (§9.2) promises that from this repository alone a reader can
**(1)** rebuild the PD shelf space and its LM envelopes, **(2)** verify the
E8 positive control at the §3.9 values, **(3)** reproduce the Brinton
pastiche entry rates under both vocabularies, and **(4)** place the
released AI corpus against the released envelope sidecars. The steps below
deliver those four claims in order, with the exact expected numbers.

```bash
git clone https://github.com/wbryanta/author-manifold.git
cd author-manifold
python3 -m venv venv && source venv/bin/activate
pip install -e .

# ---- (1a) Rebuild + gate the PD shelf space (9 authors, 35 novels).
#      E1-E3 from shipped per-work baselines + manifest + texts.
#      Gates: E1 AUC >= 0.90, E2 top-1 >= 70% / top-3 >= 85%, E3 >= 6 dims.
#      Expected: "OVERALL: PASS" (E1 AUC 0.999, E2 100%/100%, E3 15/18).
#      ~20 s.
python3 tools/validate_author_space.py \
    --baseline-dir data/pd_work_baselines \
    --manifest data/pd_manifest.yaml \
    --distance-variant mfw_delta \
    --output-dir reports/validation/author_space/pd_shelf_rerun

# ---- (1b) Rebuild the PD LM envelopes from the shipped novel texts, and
#      (2) run E8, the same-author positive control, at the paper's values.
#      Expected output (~5 s; both rebuilt sidecars verified content-equal
#      to the released ones in data/artifacts/):
#        E8 [pd]:        PASS (pooled 1375/1575 inside@p90 = 87.3%; released sidecar MATCH)
#        E8 [pd_fwonly]: FAIL (pooled 1378/1575 inside@p90 = 87.5%; released sidecar MATCH)
#      Those are the §3.9/§9.1 values: 87.3% full / 87.5% fw-only. The
#      pd_fwonly FAIL is the Fitzgerald fw-only gate failure the paper
#      itself reports (§3.9 — "the strict gate verdict is FAIL"), so this
#      command exits with code 3 BY DESIGN; a reproduction that passed
#      would be wrong.
python3 tools/validate_lm_envelopes.py \
    --output-dir reports/validation/author_space/pd_shelf_rerun

# ---- (3) + (4) Results 2.0: place the released AI corpus (1,072 manifest
#      records -> 1,069 loadable -> 236 primary styled) and the Brinton
#      pastiche against the RELEASED envelope sidecars, both vocabularies.
#      Expected output (~5 s):
#        Entry@p90 (full vocab, primary): 48/236 (20.3%)
#        Brinton@p90 (full vocab): 34/36 (94.4%)
#        Entry@p90 (fwonly vocab, primary): 72/236 (30.5%)
#        Brinton@p90 (fwonly vocab): 27/36 (75.0%)
#        G1 control (full): unprompted 20/121 (16.5%) vs styled 48/236 (20.3%); increment +3.8 pp
#        G1 control (fwonly): unprompted 13/121 (10.7%) vs styled 72/236 (30.5%); increment +19.8 pp
#      That is promise (3) — Brinton 34/36 and 27/36 at p90 — and promise
#      (4): the §5.2 headline entry rates, exactly the committed evidence in
#      reports/validation/author_space/results2/ (the rerun lands in
#      results2_rerun/ and is numerically identical to the committed run;
#      only generation timestamps and the translation subsection differ —
#      the latter needs rights-encumbered novel texts, see the tool
#      docstring).
python3 tools/rerun_entry_analysis.py

# ---- (4, continued) The completion condition (K8) and the strongest
#      single check in the release: the cross-target matrix re-places the
#      frozen corpus and HARD-ABORTS unless the clone reproduces every
#      frozen 5.2 number exactly (pooled + per model, both vocabularies,
#      thresholds, the 1,072->236 selection chain, the G1 control) before
#      computing anything new. Expected (~5 s each):
#        K8 completion: fw-only entry 27/87 = 31.0% @p90; refused 37, sub-floor 35
#        Positive-control gate: PASS (both vocabularies)
#        VERDICT: TARGET_SPECIFIC (D=+16.10 pp, CI [+5.05, +27.09])
python3 tools/analyze_completion_condition.py
python3 tools/cross_target_entry_matrix.py

# ---- Test suite (~30 s). Expected: 116 passed.
pip install pytest && pytest
```

Everything above runs from this repository alone — the public-domain shelf
texts, per-work baselines, AI corpus, space artifacts, and LM envelope
sidecars all ship. Reruns land in `reports/validation/author_space/
pd_shelf_rerun/` and `.../results2_rerun/` (both gitignored) next to the
recorded evidence in `.../pd_shelf/` and `.../results2/`, so `git status`
stays clean and any drift is a diff away.

### The retired v0.2 criterion (kept for the retraction's reproducibility)

The first release's E4 entry criterion — "0/318 styled samples enter the
full-novel W-p90" — was a length-calibration artifact caught by adversarial
review and **retracted** (§4.5/§5.1 of the paper); the length-matched
envelopes above replace it. The instrument run is kept reproducible so the
retraction itself can be audited:

```bash
# Reproduces the RECORDED v2 instrument run — a superseded criterion,
# not a finding. Expected (~5 s):
#   E4 gate: PASS (400 unprompted, 0 violations; 318 style-prompted,
#   0 nearest-is-target)
python3 tools/run_e4_ai_placement.py \
    --artifact data/artifacts/author_space_pd_v1.json \
    --output-dir reports/validation/author_space/pd_shelf_rerun
```

### Other recorded analyses

```bash
# P5 human-pastiche baseline (full-novel W percentiles, the recorded
# pre-LM analysis; the paper's 34/36 & 27/36 LM numbers come from
# rerun_entry_analysis.py above). Expected (~1 s):
#   P5: 33/37 nearest-is-target, 0/37 entered W-p90; median target
#   W-pct 100.0
python3 tools/place_pastiche_baseline.py \
    --output-dir reports/validation/author_space/pd_shelf_rerun

# Wave-2 tier-1 statistics from the shipped placement results (the
# recorded run used 10,000 bootstrap/permutation draws). Every numeric
# value in the shared sections reproduces the recorded
# wave2/tier1_statistics.json exactly; the recorded file additionally
# carries the C1b/C1c enter-rate family rows, part of the RETIRED v0.2
# Holm family (paper §4.5) and produced by the parent project's run.
python3 tools/tier1_statistics.py \
    --e4-results reports/validation/author_space/wave2/e4_results.json \
    --artifact data/artifacts/author_space_v1_wave2.json \
    --n-boot 10000 --n-perm 10000 \
    --out-dir reports/validation/author_space/results2_rerun
```

### Regenerating the paper figures (F1-F8)

```bash
pip install matplotlib umap-learn   # umap-learn: released F1 projection;
                                    # PCA fallback (labeled) without it
python3 tools/build_paper_figures.py    # -> docs/figures_rerun/, ~15 s
```

All eight figures regenerate from the committed evidence JSONs and shipped
corpus/artifacts; F2 verifies its recomputed distributions against the
frozen results2 counts before rendering and aborts on any mismatch.

## What's in the box

```
src/author_manifold/        The instrument: AuthorRelativeSpace (calibration,
                            MFW Burrows-Delta block, W/B distributions,
                            placement), length-matched envelopes
                            (LengthMatchedEnvelopes / AuthorLMEnvelope,
                            work-level LOO + E8 held-out entry), cluster-
                            robust inference (ICC / design effect),
                            attribution metrics (C_llr, ROC AUC)
tools/                      CLI: build/validate the space, LM envelope
                            construction + E8 (validate_lm_envelopes),
                            the Results 2.0 re-analysis
                            (rerun_entry_analysis), completion-condition
                            placement (analyze_completion_condition),
                            cross-target specificity matrix with its
                            positive-control gate
                            (cross_target_entry_matrix), paper figures
                            (build_paper_figures), E4 AI placement,
                            tier-1 statistics, robustness probes (paraphrase,
                            self-consistency, cross-topic, style-transfer
                            dimensions), pastiche baseline, PD shelf builder,
                            AI corpus generator
tests/                      Unit + integration tests (run on shipped PD data)
data/pd_shelf/              35 public-domain novels, 9 authors, cleaned
                            body-only text with Gutenberg provenance
data/pd_work_baselines/     Precomputed per-work D18 feature baselines
data/pd_manifest.yaml       Build manifest (body offsets, fidelity verdicts)
data/artifacts/             Author-space artifacts: PD shelf (full + fw-only),
                            contemporary wave-2 (full + fw-only), and the
                            length-matched envelope sidecars
                            (lm_envelopes_*_3000w.json)
data/ai-longform/           ~1,060 AI-generated fiction samples, 8 models,
                            5 conditions (unprompted / style-prompted /
                            exemplar / paraphrase / completion), full
                            generation manifest (CC0)
data/ai_baselines/          Per-sample D18 baselines for the AI corpus
                            (v2 conditions; completion samples are
                            MFW-only, no D18 baselines)
data/pastiche/              Brinton 1913 (Gutenberg #43741, public domain)
reports/                    Recorded validation results (aggregates) +
                            interactive HTML report; reports/validation/
                            results2/ is the Results 2.0 (v0.4) evidence
                            set behind every headline number
docs/paper/                 The preprint PDF (v0.5.4, CC BY 4.0)
docs/PAPER_DRAFT.md         The paper source (markdown, v0.5.4, figures
                            placed) + docs/references.bib
docs/figures/               Print figures F1-F8 (PDF + 600-dpi PNG) with
                            generated captions
docs/redteam/               All three adversarial-review cycles + synthesis
                            (cycle3_2026-07/ includes the retraction record)
docs/METHODOLOGY.md         The measurement model and validation design
docs/TIER1_PAPER_OUTLINE.md Paper skeleton and claim framing
docs/tier1_related_work_reconciliation.md  Related-work reconciliation
```

## What's NOT in the box (and why)

- **Contemporary novel texts** (15 wave-2 authors): rights-encumbered. Only
  derived aggregate statistics ship (per-work z-scored frequency vectors of
  the 300 most frequent words + 18 scalar dimensions) — see
  `DATA_LICENSES.md`. Rebuilding those artifacts requires your own copies.
  Consequently the wave-2 LM envelopes cannot be *rebuilt* here (their
  released sidecars in `data/artifacts/` carry the recorded envelopes and
  are what every placement tool reads), and the translation-bound
  subsection of `rerun_entry_analysis.py` reports "none usable" without
  locally held novels — the paper's §9.2 wording: contemporary-shelf
  numbers verify against released aggregate artifacts; regeneration from
  raw texts requires local copies.
- **The D18 baseline-generation pipeline**: depends on a heavy stack
  (spaCy/transformers); per-work baselines ship precomputed. The MFW-Delta
  identity layer — which carries all headline claims — is computed from raw
  text by this package alone (numpy/scipy/scikit-learn/pyyaml only).
- **Private corpora and manuscript case-study placements** from the parent
  project: personal data, recorded separately, not part of the research
  release.
- **The exemplar condition's in-context excerpts**: drawn from contemporary
  novels; the *generated samples* ship, the excerpts do not.

## Licensing

- Code: Apache-2.0 (`LICENSE`)
- AI corpus + derived baselines + reports: CC0 1.0
- Public-domain shelf and pastiche text: public domain (US), Project
  Gutenberg provenance recorded per file

See `DATA_LICENSES.md` for details.

## Citation

```bibtex
@misc{bryant2026width,
  author = {Bryant, Will},
  title  = {The Width of a Voice: Placing Machine Imitation Inside
            Authors' Own Variation},
  year   = {2026},
  doi    = {10.5281/zenodo.21210011},
  note   = {Preprint v0.5.4; targeting CHR 2027},
  url    = {https://github.com/wbryanta/author-manifold}
}
```

For the instrument/software itself:

```bibtex
@misc{bryant2026authormanifold,
  author = {Bryant, Will},
  title  = {author-manifold: An Author-Relative Measurement Space for
            Stylometric Placement},
  year   = {2026},
  url    = {https://github.com/wbryanta/author-manifold}
}
```
