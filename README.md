# author-manifold

**An author-relative measurement space for stylometric placement** — the
instrument, validation harness, corpora, and recorded results behind
**"The Width of a Voice: Placing Machine Imitation Inside Authors' Own
Variation"** (Will Bryant, preprint v0.5.5 — PDF at
[`docs/paper/`](docs/paper/), concept DOI:
[10.5281/zenodo.21210010](https://doi.org/10.5281/zenodo.21210010) —
resolves to the latest version; the v0.5.5 version DOI is
[10.5281/zenodo.21562806](https://doi.org/10.5281/zenodo.21562806);
targeting CHR 2027).

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
| **Envelope width predicts entry** (de-circularized: all 15 shelf authors as pseudo-targets for 309 unprompted samples) | Pearson **r = +0.844** [+0.59, +0.95] fw-only (full vocab +0.73); Ishiguro is the wide-but-distant outlier. The paper's own caveat travels with the number: the interval is Fisher-z, and the 15 per-author rates share the same 309 samples, so it treats correlated rows as independent and is **optimistic** (§5.6) |
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

## About this repository's history

Worth knowing before you read the commit log, because all three facts below
look odd out of context and each has a plain explanation.

**This is a curated public mirror, built fresh.** It is not the working
repository's history rewritten or truncated — it is a separate repository
created for the release. The working repository cannot be published: it holds
in-copyright novel corpora and a private personal corpus, neither of which is
distributable (see "What's NOT in the box"). So the release was assembled as
its own repository containing only what can ship. Nothing was removed from a
public history; there was no public history to remove from.

**The commit dates cluster tightly.** They reflect evidence-completeness
work against an already-frozen paper — shipping the artifacts the paper
cites, checking they reproduce, fixing what did not — rather than the pace at
which the research happened. The research spans 2026-06 to 2026-08; the
mirror's commits are the packaging of it.

**Commits carry `Co-Authored-By: Claude` trailers.** The paper discloses the
same thing more directly than the trailers do: this work was built in
sustained human–AI collaboration, and §8.11 says so explicitly, including
what the models did and what the sole author is answerable for. The trailers
are consistent with that disclosure, not a substitute for it — read §8.11.

**Adversarial review was run by AI reviewers, including a cross-family one.**
`docs/redteam/README.md` records who reviewed what, which draft each cycle
attacked, and what changed as a result — including that an OpenAI-family
model ("SOL") was used as an outside gate on work produced with
Anthropic-family models, specifically so the project is not grading its own
homework. Note that **cycle 3 reviewed a different, withdrawn study** and its
verdicts do not refer to this paper; every file in that directory now says so
at the top.

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
(`reports/validation/author_space/results2/`), not hand-patched. Cycle map,
dispositions, and reviewer provenance: `docs/redteam/README.md`.

**Evidence a skeptic would ask for, computed here first.** A forensic
code-and-data review (2026-08-06, seven independent reviewer lanes plus a
cross-family gate) ran the analyses an adversarial reader would run, and they
are published whichever way they fell:

| Question | File |
|---|---|
| Do the results hold if you remove *every* sample with a verbatim echo, not just the 4 above the disclosed threshold? | `results2/echo_robustness_13.md` — yes: every rate within its published interval, sign test unchanged |
| Is there *near*-verbatim leakage that exact matching would miss? | `results2/near_copy_scan.md` — no: zero spans at ≥40 tokens/80% identity, on a scan validated by a planted positive |
| Would a different subset of the folk tells beat the reported coin flip? | `results2/folk_tells_sensitivity.md` — yes, and the best a-priori subset (0.73) is now disclosed in the paper; the full-list result is the honest test of the folk claim |
| Do any styled samples refuse the styling instruction? | `results2/declined_styling_disclosure.md` — 13 of 236 do, and they enter at 61.5% vs 28.7%; no published number moves |
| Was anything published that turned out to be wrong? | `ERRATA.md` |

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

# ---- Test suite (~5 s). Expected: 128 passed. Includes
#      tests/test_published_chain.py, which pins the paper's §5.2
#      selection chain and headline rates to exact values from the
#      shipped artifacts, so numeric drift fails rather than passing
#      quietly.
pip install pytest && pytest
```

**Environment.** `pyproject.toml` carries deliberately loose floors
(Python ≥ 3.10, numpy ≥ 1.24, scipy ≥ 1.10, scikit-learn ≥ 1.3) and the
results do not depend on pinning: `constraints-verified.txt` records the
exact modern, unpinned stack (Python 3.14.6 / numpy 2.5.1 / scipy 1.18.0 /
scikit-learn 1.9.0) in which every number above was independently
reproduced digit-for-digit on 2026-08-06, from a fresh clone, by someone
other than the author. It also states the honest limitation: the original
runs behind the committed evidence predate version stamping and their exact
versions cannot be recovered. Runs from 2026-08-06 onward stamp interpreter
and library versions into their artifact `meta.versions` block.

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
#
# Precision note (forensic review 2026-08-06): because those two extra
# rows are in the recorded Holm family, the recorded registry corrects
# across 33 tests and this rerun across 31. All 31 shared registry rows
# reproduce their p_raw, estimate, CI, and significance verdict exactly;
# 19 of them differ in the p_holm column only, by the family-size factor.
# No significance verdict changes.
python3 tools/tier1_statistics.py \
    --e4-results reports/validation/author_space/wave2/e4_results.json \
    --artifact data/artifacts/author_space_v1_wave2.json \
    --n-boot 10000 --n-perm 10000 \
    --out-dir reports/validation/author_space/results2_rerun

# R3 dimension-level movement — the PRIMARY §5.5 artifact
# (results2/r3_floor_compliant.json, floor-compliant n=236). The floor is
# the paper's §3.7 MFW-token floor applied to the STYLE-TARGETED samples
# only; the matched unprompted baselines stay unfiltered so the movement
# contrast remains comparable. Expected (~2 s):
#   236 styled samples; skipped styled_below_min_tokens=82,
#   missing_baseline=2, other_condition=352
#   Transferred (Holm p<0.05, toward): repetition_ratio,
#   vocabulary_richness, ttr, sentiment_score, present_ratio, past_ratio
#   MFW chassis: median movement -0.0070 Delta (closure -0.4%)
python3 tools/analyze_style_transfer_dimensions.py \
    --min-tokens-styled-floor 3000 \
    --output-dir reports/validation/author_space/results2_rerun \
    --output-prefix r3_floor_compliant

# Without the flag the tool reproduces the SECONDARY native-length run
# (n=318) recorded in results2/entry_report.md section (e).
python3 tools/analyze_style_transfer_dimensions.py \
    --output-dir reports/validation/author_space/results2_rerun
```

**Provenance note on the R3 baselines (forensic review 2026-08-06).** The
recorded `results2/r3_floor_compliant.json` meta names
`data/tmp/r3_baselines` as its `baselines_dir` — that was the original
run's private working directory, not a shipped path. Re-running the
command above against the **shipped** `data/ai_baselines/` reproduces the
recorded artifact exactly: a full recursive JSON comparison at zero
tolerance found differences only in `meta.generated` and the three
`meta.*` path strings, with every numeric value identical (verified
2026-08-06). No unshipped input is required.

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
                            attribution metrics (ROC AUC)
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
docs/paper/                 The preprint PDFs (v0.5.5 current, v0.5.4 kept
                            for the record; CC BY 4.0)
docs/PAPER_DRAFT.md         The paper source (markdown, v0.5.4 edition kept
                            for diffability; the v0.5.5 PDF is current) +
                            docs/references.bib
docs/figures/               Print figures F1-F8 (PDF + 600-dpi PNG) with
                            generated captions
docs/redteam/               All three adversarial-review cycles + synthesis
                            (cycle3_2026-07/ includes the retraction record)
docs/METHODOLOGY.md         The measurement model and validation design
docs/adr/                   ADR-0041, the design of record (release summary
                            written from the paper's Methods §3)
ERRATA.md                   Corrections to previously published material
constraints-verified.txt    The environment in which reproduction was
                            independently verified (2026-08-06)
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
- AI corpus + derived baselines + reports + `data/pd_manifest.yaml`: CC0 1.0
- Documentation and figures (`docs/`, and the root-level `README.md`,
  `MODELS.md`, `ERRATA.md`, `DATA_LICENSES.md`): CC BY 4.0 — the same licence
  the preprint carries
- Public-domain shelf and pastiche text: public domain (US), Project
  Gutenberg provenance recorded per file; the Project Gutenberg license ships
  at `data/pd_shelf/GUTENBERG_LICENSE.txt`

See `DATA_LICENSES.md` for details, including the per-provider basis for the
CC0 dedication on model outputs, the corpus composition (refusals and
sub-floor outputs are flagged in `data/ai-longform/sample_flags.json`), and
the file-level exception ledger for the 13 samples carrying incidental
verbatim echoes of in-copyright text. `MODELS.md` records model pinning
status, including where it is weaker than it should be.

## Citation

```bibtex
@misc{bryant2026width,
  author = {Bryant, Will},
  title  = {The Width of a Voice: Placing Machine Imitation Inside
            Authors' Own Variation},
  year   = {2026},
  doi    = {10.5281/zenodo.21210010},
  note   = {Preprint v0.5.5; targeting CHR 2027. The DOI above is the
            Zenodo concept DOI and always resolves to the latest
            version; to pin v0.5.5 specifically, cite
            10.5281/zenodo.21562806},
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
