"""Value-pinning integration test for the paper's published §5.2 chain.

Everything else in this suite tests behaviour. This module tests *numbers*:
it walks the selection chain the paper's headline entry rates depend on,
reading only shipped artifacts, and asserts each published count exactly.

The point is drift detection. A refactor that quietly changes how samples
are counted, filtered, or stratified would still pass a behavioural suite
while silently invalidating the paper; here it fails CI with the number
that moved.

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

Added by the forensic code and data review of 2026-08-06 (finding A-12).
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS2 = REPO_ROOT / "reports/validation/author_space/results2"
MANIFEST = REPO_ROOT / "data/ai-longform/manifest.jsonl"

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
