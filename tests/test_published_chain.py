"""Value-pinning integration test for the paper's published §5.2 chain.

Everything else in this suite tests behaviour. This module tests *numbers*:
the selection chain the paper's headline entry rates depend on, asserted
against the published counts exactly.

WHAT THIS GUARDS
----------------

1. **The chain, recomputed.** `TestChainRecomputedFromTheCorpus` rebuilds
   1,072 -> 1,069 -> 318 -> 236 from the shipped manifest and the shipped
   sample files, through `rerun_entry_analysis.load_corpus` and
   `STYLED_CONDITIONS` — the same loader and the same stratification the
   published run used, imported rather than reimplemented, so a change to
   how samples are read, tokenized, dropped, or stratified moves these
   numbers and fails here. The floors are read from the published run's own
   meta rather than restated, so the recomputation uses the parameters the
   paper declares.

2. **The recorded artifacts.** The remaining classes assert that the
   committed evidence JSONs still carry those same counts and the published
   entry rates. That is a check on the artifacts, not on the code that
   produced them.

WHAT THIS DOES *NOT* GUARD
--------------------------

The placement math. Whether a sample lands inside a target's envelope is
computed from the author-space and envelope artifacts by
`rerun_entry_analysis.py` / `cross_target_entry_matrix.py`; the entry
counts here are read from those tools' recorded output, not recomputed.
The cross-target matrix is the check that re-derives placement and
hard-aborts on drift (README quickstart, step 4).

The chain, as published (paper §5.2, §4.3, §4.4; evidence in
reports/validation/author_space/results2/):

    1,072 manifest records
      -> 1,069 loadable (3 empty/unusable)
      ->   318 style-targeted samples
      ->   236 primary stratum (>= the 3,000 MFW-token practice floor)
           with 76 sub-floor and 6 hard-floor exclusions
      ->    72 of 236 entering the target's fw-only LM p90 envelope (30.5%)
      ->    13 of 121 bound-scenario unprompted samples entering (10.7%),
                the base rate the +19.8 pp increment is measured against

Added by the forensic code and data review of 2026-08-06 (finding A-12);
extended from artifact-reading to corpus recomputation after the
cross-family review of 2026-08-07 (finding F3).
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS2 = REPO_ROOT / "reports/validation/author_space/results2"
MANIFEST = REPO_ROOT / "data/ai-longform/manifest.jsonl"
CORPUS_DIR = REPO_ROOT / "data/ai-longform"

sys.path.insert(0, str(REPO_ROOT / "tools"))

# The shipped analysis code, imported so this test exercises it rather than
# a second implementation of it. A reimplementation here could agree with
# the published numbers while the tool had drifted away from them.
from rerun_entry_analysis import (  # noqa: E402
    STYLED_CONDITIONS as TOOL_STYLED_CONDITIONS,
    load_corpus,
)

# The published chain. Changing a number here is changing the paper.
N_MANIFEST_RECORDS = 1072
N_LOADABLE = 1069
N_STYLED_TOTAL = 318
N_STYLED_PRIMARY = 236
N_STYLED_SUBFLOOR = 76
N_STYLED_HARD_FLOOR_EXCLUDED = 6
N_FWONLY_ENTERED = 72
N_FULL_ENTERED = 48
N_UNPROMPTED_BOUND = 121
N_UNPROMPTED_ENTERED_FWONLY = 13
N_UNPROMPTED_ENTERED_FULL = 20
STYLED_CONDITIONS = ("style_prompted", "exemplar")


@pytest.fixture(scope="module")
def entry_results():
    return json.loads((RESULTS2 / "entry_results.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def controls_results():
    return json.loads(
        (RESULTS2 / "controls_results.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def loaded_corpus():
    """Every usable sample, through the tool's own loader (tokenizes 1,069
    files; the one slow fixture in the suite, shared across this module)."""
    return load_corpus(CORPUS_DIR)


@pytest.mark.integration
class TestChainRecomputedFromTheCorpus:
    """1,072 -> 1,069 -> 318 -> 236, recomputed from the shipped corpus.

    Not read from a result file: read from the manifest and the sample
    files, through the loader and the stratification the published run
    used. This is the class that fails when analysis code drifts.
    """

    def test_styled_conditions_come_from_the_tool(self):
        # If the tool's notion of "styled" changes, the paper's 318 changes
        # with it -- so the constant is imported, and pinned to its value.
        assert tuple(TOOL_STYLED_CONDITIONS) == STYLED_CONDITIONS

    def test_loader_drops_exactly_the_three_unusable_samples(
            self, loaded_corpus):
        manifest_rows = [
            json.loads(line) for line in
            MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        assert len(manifest_rows) == N_MANIFEST_RECORDS
        assert len(loaded_corpus) == N_LOADABLE
        # Keyed on file_path: sample_id is not unique across models.
        dropped = ({r["file_path"] for r in manifest_rows}
                   - {r["file_path"] for r in loaded_corpus})
        assert len(dropped) == N_MANIFEST_RECORDS - N_LOADABLE
        # Every drop must be an unusable sample, not a silently missing file.
        for file_path in dropped:
            path = CORPUS_DIR / file_path
            assert path.exists(), f"{file_path} is missing, not empty"

    def test_styled_stratification_recomputes_to_the_published_counts(
            self, loaded_corpus, entry_results):
        # Floors are the published run's declared parameters, not restated
        # here; test_floors_are_the_published_ones pins them to 1500/3000.
        meta = entry_results["meta"]
        hard_floor, practice_floor = meta["hard_floor"], meta["practice_floor"]
        assert meta["floor_unit"] == "mfw_tokens"

        styled = [r for r in loaded_corpus
                  if r["condition"] in TOOL_STYLED_CONDITIONS]
        hard_excluded = [r for r in styled if r["_n_tokens"] < hard_floor]
        subfloor = [r for r in styled
                    if hard_floor <= r["_n_tokens"] < practice_floor]
        primary = [r for r in styled if r["_n_tokens"] >= practice_floor]

        assert len(styled) == N_STYLED_TOTAL
        assert len(primary) == N_STYLED_PRIMARY
        assert len(subfloor) == N_STYLED_SUBFLOOR
        assert len(hard_excluded) == N_STYLED_HARD_FLOOR_EXCLUDED
        # The strata partition the styled samples.
        assert (len(primary) + len(subfloor)
                + len(hard_excluded)) == len(styled)

    def test_recomputed_strata_match_the_recorded_ones(
            self, loaded_corpus, entry_results):
        """Same files, not just the same counts."""
        meta = entry_results["meta"]
        styled = [r for r in loaded_corpus
                  if r["condition"] in TOOL_STYLED_CONDITIONS]
        recomputed_excluded = sorted(
            r["file_path"] for r in styled
            if r["_n_tokens"] < meta["hard_floor"])
        recomputed_subfloor = sorted(
            r["file_path"] for r in styled
            if meta["hard_floor"] <= r["_n_tokens"] < meta["practice_floor"])
        assert recomputed_excluded == meta["hard_floor_excluded_files"]
        assert recomputed_subfloor == meta["subfloor_files"]

    def test_unprompted_pool_is_the_published_size(self, loaded_corpus):
        """The G1 control's denominator, from the corpus rather than a JSON.

        The published 121 is the *bound-scenario* subset of the unprompted
        condition -- the scenarios that also occur styled -- so the corpus
        can only bound it from above; that bound is what is checked here.
        """
        unprompted = [r for r in loaded_corpus
                      if r["condition"] == "unprompted"]
        assert len(unprompted) >= N_UNPROMPTED_BOUND


@pytest.mark.integration
class TestPublishedSelectionChain:
    """1,072 -> 1,069 -> 318 -> 236, from the shipped manifest and evidence."""

    def test_manifest_holds_the_published_record_count(self):
        rows = [
            json.loads(line) for line in
            MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        assert len(rows) == N_MANIFEST_RECORDS
        # No duplicate file_path: the count is 1,072 distinct samples.
        assert len({r["file_path"] for r in rows}) == N_MANIFEST_RECORDS

    def test_styled_conditions_are_named_and_populated(self):
        rows = [
            json.loads(line) for line in
            MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        conditions = {r["condition"] for r in rows}
        # Guards the A-3 defect: a renamed/absent styled condition silently
        # halves the styled stratum.
        for condition in STYLED_CONDITIONS:
            assert condition in conditions, (
                f"styled condition {condition!r} missing from the manifest; "
                f"present: {sorted(conditions)}")
        styled = [r for r in rows if r["condition"] in STYLED_CONDITIONS]
        # Every styled record must name a target, or it cannot be placed.
        assert all(r.get("style_target") for r in styled)

    def test_recorded_stratification_matches_the_published_chain(
            self, entry_results):
        meta = entry_results["meta"]
        assert meta["n_corpus_samples"] == N_LOADABLE
        assert meta["n_styled_total"] == N_STYLED_TOTAL
        assert meta["n_styled_primary"] == N_STYLED_PRIMARY
        assert meta["n_styled_subfloor"] == N_STYLED_SUBFLOOR
        assert meta["n_styled_hard_floor_excluded"] == N_STYLED_HARD_FLOOR_EXCLUDED
        # The strata partition the styled samples: nothing is lost or counted
        # twice between 318 and 236.
        assert (meta["n_styled_primary"] + meta["n_styled_subfloor"]
                + meta["n_styled_hard_floor_excluded"]) == N_STYLED_TOTAL

    def test_floors_are_the_published_ones(self, entry_results):
        meta = entry_results["meta"]
        assert (meta["hard_floor"], meta["practice_floor"]) == (1500, 3000)
        assert meta["floor_unit"] == "mfw_tokens"
        assert meta["window_words"] == 3000


@pytest.mark.integration
class TestPublishedEntryRates:
    """The §5.2 headline rates, both vocabularies, on the primary stratum."""

    @pytest.mark.parametrize("vocab,entered", [
        ("fwonly", N_FWONLY_ENTERED),
        ("full", N_FULL_ENTERED),
    ])
    def test_primary_entry_at_p90(self, entry_results, vocab, entered):
        primary = entry_results["entry"][vocab]["primary"]
        assert primary["n"] == N_STYLED_PRIMARY
        p90 = primary["per_level"]["p90"]
        assert (p90["entered"], p90["n"]) == (entered, N_STYLED_PRIMARY)
        assert p90["rate"] == pytest.approx(entered / N_STYLED_PRIMARY)

    def test_fwonly_is_the_larger_rate(self, entry_results):
        """The paper's framing: the increment lives on function words."""
        fw = entry_results["entry"]["fwonly"]["primary"]["per_level"]["p90"]
        full = entry_results["entry"]["full"]["primary"]["per_level"]["p90"]
        assert fw["entered"] > full["entered"]


@pytest.mark.integration
class TestPublishedUnpromptedBaseRate:
    """The G1 control: 13/121 fw-only, the base the increment is read against."""

    def test_bound_unprompted_pool_size(self, controls_results):
        assert controls_results["meta"]["n_unprompted_bound"] == N_UNPROMPTED_BOUND

    @pytest.mark.parametrize("vocab,entered", [
        ("fwonly", N_UNPROMPTED_ENTERED_FWONLY),
        ("full", N_UNPROMPTED_ENTERED_FULL),
    ])
    def test_unprompted_entry_and_increment(
            self, controls_results, entry_results, vocab, entered):
        control = controls_results["unprompted_entry_control"][vocab]
        unprompted = control["unprompted"]
        assert (unprompted["entered"], unprompted["n"]) == (
            entered, N_UNPROMPTED_BOUND)

        styled = control["styled"]
        assert styled["n"] == N_STYLED_PRIMARY
        # The control's styled arm must be the same number the entry block
        # reports -- if these two ever disagree, the increment is meaningless.
        assert styled["entered"] == (
            entry_results["entry"][vocab]["primary"]["per_level"]["p90"]["entered"])

        increment_pp = 100.0 * (styled["rate"] - unprompted["rate"])
        expected_pp = 100.0 * (
            styled["entered"] / N_STYLED_PRIMARY - entered / N_UNPROMPTED_BOUND)
        assert increment_pp == pytest.approx(expected_pp)

    def test_fwonly_increment_is_the_published_plus_19_8_pp(
            self, controls_results):
        control = controls_results["unprompted_entry_control"]["fwonly"]
        increment_pp = 100.0 * (
            control["styled"]["rate"] - control["unprompted"]["rate"])
        assert increment_pp == pytest.approx(19.8, abs=0.05)

    def test_full_vocab_increment_is_the_published_plus_3_8_pp(
            self, controls_results):
        control = controls_results["unprompted_entry_control"]["full"]
        increment_pp = 100.0 * (
            control["styled"]["rate"] - control["unprompted"]["rate"])
        assert increment_pp == pytest.approx(3.8, abs=0.05)
