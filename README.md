# author-manifold

**An author-relative measurement space for stylometric placement** — the
instrument, validation harness, corpora, and recorded results behind
**"The Width of a Voice: Placing Machine Imitation Inside Authors' Own
Variation"** (Will Bryant, preprint v0.5.3 — PDF at
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
`reports/validation/wave2/PRIMARY_ARTIFACT.md` (Number Freeze v3) and
`docs/PAPER_DRAFT.md` §4-5.

| Finding | Number |
|---|---|
| Styled entry as a **controlled increment** over the unprompted base rate (fw-only, @p90): never-prompted AI on the same scenarios already enters 13/121 (10.7%); naming the author raises it to 72/236 (30.5%) | **+19.8 pp** [+4.3, +33.5] cluster-bootstrap 95%, excludes zero (full-vocabulary increment: +3.8 pp [−12.6, +18.6] — porosity, not imitation) |
| Model-matched **completion vs named-style** (fw-only, @p90): continuing the author's own text beats being told the author's name for every informative model | **5/5** completion-higher, exact one-sided p = 0.031; GPT-5 (the best styled model) refused all completions — the previously reported pooled "parity" was that composition artifact |
| **Envelope width predicts entry** (de-circularized: all 15 shelf authors as pseudo-targets for 309 unprompted samples) | Pearson **r = +0.844** [+0.59, +0.95] fw-only (full vocab +0.73); Ishiguro is the wide-but-distant outlier |
| **E8 positive control** (held-out windows inside own LM p90) | strict gate as committed: **FAIL** (3/4 shelves); the observed self-entry yardstick is reported instead — pooled 83.7–87.8% (`reports/validation/results2/e8_yardstick.md`) |
| Human pastiche (Brinton 1913 vs Austen's LM envelope) — **descriptive juxtaposition only** (chunks of one novel, not independent) | 27/36 (75%) fw-only chunks enter Austen's p90; 34/36 full-vocabulary |
| Public-domain shelf validation (9 authors / 35 novels, fully shipped) | E1 separation **AUC 0.999**, E2 leave-one-out attribution **100%** top-1 |
| Contemporary shelf validation (15 authors / 78 novels, artifacts shipped, texts not) | E1 AUC 0.941, E2 top-1 96.2% |

Exact statistical treatment (Clopper-Pearson + design-effect-adjusted +
cluster-bootstrap intervals on every pooled rate, threshold-quantile CI
sweeps, exact tests, Holm registry):
`reports/validation/results2/entry_report.md` and
`reports/validation/results2/controls_results.md`; instrument validation
remains locked to Number Freeze v2
(`reports/validation/wave2/tier1_statistics.md`).

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
(`reports/validation/results2/`), not hand-patched.

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

## Quickstart (~30 minutes, everything from shipped data)

```bash
git clone https://github.com/wbryanta/author-manifold.git
cd author-manifold
python3 -m venv venv && source venv/bin/activate
pip install -e .

# 1. E1-E3: validate the public-domain shelf (9 authors, 35 novels)
#    Gates: E1 AUC >= 0.90, E2 top-1 >= 70% / top-3 >= 85%, E3 >= 6 dims.
#    Expected: ALL PASS (AUC 0.999, 100%/100%, 15/18). ~2 min.
python3 tools/validate_author_space.py \
    --baseline-dir data/pd_work_baselines \
    --manifest data/pd_manifest.yaml \
    --distance-variant mfw_delta \
    --output-dir reports/validation/pd_shelf_rerun

# 2. E4: place the AI corpus into the PD space. Gate: every unprompted
#    sample off-manifold. Expected: PASS (400/400 unprompted off-manifold,
#    0/318 styled samples enter the FULL-NOVEL W-p90 — reproduced as the
#    recorded v2 instrument run; as a paper entry criterion it is retired
#    in favor of length-matched envelopes, see headline table). The
#    shipped corpus is the complete frozen design matrix: 912 v2
#    generations plus the 160-record completion condition (1,072 manifest
#    records). ~5 min.
python3 tools/run_e4_ai_placement.py \
    --artifact data/artifacts/author_space_pd_v1.json \
    --output-dir reports/validation/pd_shelf_rerun

# 3. P5: the human pastiche baseline (Brinton 1913 vs Austen). ~1 min.
python3 tools/place_pastiche_baseline.py \
    --output-dir reports/validation/pd_shelf_rerun

# 4. Test suite
pip install pytest && pytest
```

Everything above runs from this repository alone — the public-domain shelf
texts, per-work baselines, AI corpus, and space artifacts all ship. Results
land in `reports/validation/pd_shelf_rerun/` next to the recorded runs in
`reports/validation/pd_shelf/`.

To reproduce the wave-2 statistics from the shipped placement results:

```bash
python3 tools/tier1_statistics.py \
    --e4-results reports/validation/wave2/e4_results.json \
    --artifact data/artifacts/author_space_v1_wave2.json
```

## What's in the box

```
src/author_manifold/        The instrument: AuthorRelativeSpace (calibration,
                            MFW Burrows-Delta block, W/B distributions,
                            placement), attribution metrics (C_llr, ROC AUC)
tools/                      CLI: build/validate the space, E4 AI placement,
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
docs/paper/                 The preprint PDF (v0.5.3, CC BY 4.0)
docs/PAPER_DRAFT.md         The paper source (markdown, v0.5.3, figures
                            placed) + docs/references.bib
docs/figures/               Print figures F1-F7 (PDF + 600-dpi PNG) with
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
  note   = {Preprint v0.5.3; targeting CHR 2027},
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
