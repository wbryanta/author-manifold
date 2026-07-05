"""
Tests for the author-relative space validation harness E1-E3
(tools/validate_author_space.py; ADR-0041 forthcoming,
issue #60).

Unit tests run on synthetic shelves (4 authors x 6 works with controlled
separation; for E3, a planted split of discriminative vs pure-noise
dimensions). The integration test runs the full harness CLI against the
public-domain data/pd_work_baselines shelf and asserts STRUCTURAL
validity of the harness output (gate verdicts asserted structurally).
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pytest

# Add tools/ to path to import validate_author_space.
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from validate_author_space import (  # noqa: E402
    run_e1,
    run_e2,
    run_e3,
    run_experiments,
    build_summary_markdown,
)
from author_manifold.author_space import (  # noqa: E402
    AuthorRelativeSpace,
    DIMENSION_SET_V1,
    WorkRecord,
    work_record_from_baseline,
)

SEED = 20260609

# Planted E3 structure: these dims get author-specific means; the rest are
# pure noise drawn from the same distribution for every author.
DISCRIMINATIVE_DIMS = DIMENSION_SET_V1[:8]
NOISE_DIMS = DIMENSION_SET_V1[8:]


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
    return current.parents[1]


def make_baseline(values: Dict[str, float], title: str, word_count: int = 50000) -> Dict:
    """Synthetic per-work baseline JSON shaped like the real pipeline output."""
    return {
        "document": {"word_count": word_count, "metadata": {"title": title}},
        "pipeline": {"version": "synthetic"},
        "d18_profile": dict(values),
        "style_features": {},
    }


def synthetic_records(
    n_authors: int = 4,
    works_per_author: int = 6,
    separation: float = 2.0,
    within_noise: float = 0.15,
    seed: int = SEED,
) -> List[WorkRecord]:
    """Synthetic shelf with controlled separation and planted E3 structure.

    DISCRIMINATIVE_DIMS get well-separated author-specific centers with small
    within-author noise; NOISE_DIMS are i.i.d. standard normal for every
    work regardless of author (zero authorial signal).
    """
    rng = np.random.default_rng(seed)
    records: List[WorkRecord] = []
    for a in range(n_authors):
        center = rng.normal(0.0, separation, size=len(DISCRIMINATIVE_DIMS))
        for w in range(works_per_author):
            values = dict(
                zip(
                    DISCRIMINATIVE_DIMS,
                    center + rng.normal(0.0, within_noise, size=len(DISCRIMINATIVE_DIMS)),
                )
            )
            values.update(zip(NOISE_DIMS, rng.normal(0.0, 1.0, size=len(NOISE_DIMS))))
            baseline = make_baseline(values, f"author{a}-work{w}")
            records.append(
                work_record_from_baseline(
                    baseline,
                    author=f"author-{a}",
                    path=f"synthetic/author-{a}/work{w}_baseline.json",
                    dimensions=DIMENSION_SET_V1,
                )
            )
    return records


@pytest.fixture(scope="module")
def space() -> AuthorRelativeSpace:
    return AuthorRelativeSpace.build(
        synthetic_records(), min_works=3, seed=SEED, generated="2026-06-09T00:00:00Z"
    )


# =============================================================================
# E1
# =============================================================================

def test_e1_passes_on_separated_authors(space):
    result = run_e1(space)
    assert result["pass"] is True
    assert result["criteria"]["pooled_auc"]["observed"] >= 0.95
    assert result["criteria"]["silhouette_positive_fraction"]["observed"] == 1.0
    # 4 authors x 6 works: within loo = 24, between = 24 works x 3 others = 72.
    assert result["n_within"] == 24
    assert result["n_between"] == 72
    for slug, row in result["per_author"].items():
        assert row["silhouette"] > 0, slug
        assert row["within_median"] < row["between_median"], slug


def test_e1_fails_on_unseparated_authors():
    # No authorial signal anywhere: every dim is noise for every author.
    weak = AuthorRelativeSpace.build(
        synthetic_records(separation=0.0, within_noise=1.0, seed=SEED + 1),
        min_works=3,
        seed=SEED,
    )
    result = run_e1(weak)
    assert result["pass"] is False
    assert result["criteria"]["pooled_auc"]["observed"] < 0.90


# =============================================================================
# E2
# =============================================================================

def test_e2_top1_high_on_separated_authors(space):
    result = run_e2(space)
    assert result["pass"] is True
    assert result["criteria"]["top1_accuracy"]["observed"] >= 0.9
    assert result["criteria"]["top3_accuracy"]["observed"] >= 0.95
    assert result["n_trials"] == 24
    assert result["skipped_authors"] == []
    # Confusion diagonal dominates.
    for slug, row in result["confusion_matrix"].items():
        assert row.get(slug, 0) >= 5, (slug, row)
    # C_llr is reported and better than a random system (= 1.0).
    assert 0.0 <= result["c_llr"]["value"] < 1.0
    # Sanity method reported and clearly labeled as not a gate.
    assert "NOT a gate" in result["sanity_check"]["note"]
    assert 0.0 <= result["sanity_check"]["top1_accuracy"] <= 1.0


def test_e2_skips_authors_below_three_works(space):
    records = synthetic_records()
    extra = synthetic_records(n_authors=1, works_per_author=2, seed=SEED + 5)
    for rec in extra:
        rec.author = "thin-author"
    thin_space = AuthorRelativeSpace.build(records + extra, min_works=2, seed=SEED)
    result = run_e2(thin_space)
    assert result["skipped_authors"] == ["thin-author"]
    # thin-author still a candidate but contributes no held-out trials.
    assert result["n_candidate_authors"] == 5
    assert result["n_trials"] == 24


# =============================================================================
# E3
# =============================================================================

def test_e3_finds_planted_dims_and_rejects_noise(space):
    result = run_e3(space, seed=SEED, n_permutations=1000)
    assert result["pass"] is True
    recommended = set(result["recommended_dimension_set_v2"])
    # Every planted discriminative dim must be found...
    assert set(DISCRIMINATIVE_DIMS) <= recommended
    # ...and pure-noise dims must (essentially all) be rejected. p99 null
    # admits ~1% false positives per dim; allow at most one.
    assert len(recommended & set(NOISE_DIMS)) <= 1
    by_dim = {row["dimension"]: row for row in result["dimension_table"]}
    for dim in DISCRIMINATIVE_DIMS:
        assert by_dim[dim]["eta_squared"] > by_dim[dim]["null_p99_eta_squared"]
        assert by_dim[dim]["permutation_p"] <= 0.01
        assert by_dim[dim]["icc_like"] > 0.5
    # Ranked table: eta^2 non-increasing, planted dims rank above noise dims.
    etas = [row["eta_squared"] for row in result["dimension_table"]]
    assert etas == sorted(etas, reverse=True)
    ranks = {row["dimension"]: row["rank"] for row in result["dimension_table"]}
    assert max(ranks[d] for d in DISCRIMINATIVE_DIMS) < min(ranks[d] for d in NOISE_DIMS)


def test_e3_seeded_permutation_null_is_deterministic(space):
    a = run_e3(space, seed=SEED, n_permutations=200)
    b = run_e3(space, seed=SEED, n_permutations=200)
    assert a["dimension_table"] == b["dimension_table"]


# =============================================================================
# Harness end-to-end (synthetic, via CLI main)
# =============================================================================

def _write_synthetic_shelf(root: Path, records: List[WorkRecord]) -> None:
    for rec in records:
        author_dir = root / rec.author
        author_dir.mkdir(parents=True, exist_ok=True)
        baseline = make_baseline(
            {dim: val for dim, val in rec.raw.items() if val is not None}, rec.title
        )
        path = author_dir / f"{rec.title}_baseline.json"
        path.write_text(json.dumps(baseline), encoding="utf-8")


def test_main_writes_results_and_summary(tmp_path):
    import validate_author_space as vas

    shelf_dir = tmp_path / "shelf"
    _write_synthetic_shelf(shelf_dir, synthetic_records())
    out_dir = tmp_path / "out"

    rc = vas.main(
        [
            "--baseline-dir", str(shelf_dir),
            "--output-dir", str(out_dir),
            "--seed", str(SEED),
        ]
    )
    assert rc == 0  # separated synthetic shelf passes all gates

    for exp in ("e1", "e2", "e3"):
        payload = json.loads((out_dir / f"{exp}_results.json").read_text())
        assert payload["experiment"] == exp
        assert payload["pass"] is True
        assert payload["criteria"]
        for criterion in payload["criteria"].values():
            assert set(criterion) == {"threshold", "comparison", "observed", "pass"}
        assert payload["meta"]["seed"] == SEED
    assert json.loads((out_dir / "e3_results.json").read_text())[
        "recommended_dimension_set_v2"
    ]

    summary = (out_dir / "summary.md").read_text()
    assert "## Gate table" in summary
    assert "**Overall: PASS**" in summary
    assert "What this means" in summary


def test_summary_markdown_reports_failures():
    weak = AuthorRelativeSpace.build(
        synthetic_records(separation=0.0, within_noise=1.0, seed=SEED + 2),
        min_works=3,
        seed=SEED,
    )
    results = run_experiments(weak, ["e1", "e2", "e3"], seed=SEED)
    assert not all(r["pass"] for r in results.values())
    summary = build_summary_markdown(results, {"generated": "t", "seed": SEED})
    assert "**Overall: FAIL**" in summary
    assert "| FAIL |" in summary


# =============================================================================
# Integration: full harness against the public-domain shelf
# =============================================================================

@pytest.mark.integration
def test_full_harness_against_pd_shelf(tmp_path):
    """Structural validity of the harness output on the public-domain
    shelf (d18 variant, no manifest). The console gate table is printed
    for visibility (run pytest with -s to see it)."""
    repo_root = _repo_root()
    baseline_dir = repo_root / "data/pd_work_baselines"
    if not baseline_dir.is_dir():
        pytest.skip("pd_work_baselines not present")

    out_dir = tmp_path / "author_space_validation"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    proc = subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/validate_author_space.py"),
            "--baseline-dir", str(baseline_dir),
            "--min-works", "3",
            "--output-dir", str(out_dir),
        ],
        capture_output=True, text=True, env=env, timeout=600,
    )
    # 0 = all gates pass, 3 = gates failed but harness ran cleanly.
    assert proc.returncode in (0, 3), proc.stderr

    # Print the gate table for visibility.
    table_at = proc.stdout.find("AUTHOR-RELATIVE SPACE VALIDATION")
    assert table_at >= 0, "gate table missing from harness stdout"
    print()
    print(proc.stdout[max(0, table_at - 80):])

    for exp in ("e1", "e2", "e3"):
        result_path = out_dir / f"{exp}_results.json"
        assert result_path.exists(), f"missing {exp}_results.json"
        payload = json.loads(result_path.read_text())
        assert payload["experiment"] == exp
        assert isinstance(payload["pass"], bool)
        assert payload["criteria"]
        for criterion in payload["criteria"].values():
            assert "threshold" in criterion and "observed" in criterion

    e2 = json.loads((out_dir / "e2_results.json").read_text())
    assert e2["n_trials"] > 0
    assert e2["confusion_matrix"]
    e3 = json.loads((out_dir / "e3_results.json").read_text())
    assert len(e3["dimension_table"]) == len(DIMENSION_SET_V1)
    assert isinstance(e3["recommended_dimension_set_v2"], list)

    summary = (out_dir / "summary.md").read_text()
    assert "## Gate table" in summary
    for heading in ("## E1", "## E2", "## E3"):
        assert heading in summary


# =============================================================================
# Distance-variant comparison (ADR-0041 amendment: MFW Burrows-Delta block)
# =============================================================================

from validate_author_space import (  # noqa: E402
    VariantSpec,
    _eta2_weights,
    build_variant_comparison_markdown,
    run_variant_comparison,
)


def _variant_text(words: List[str], rng: np.random.Generator, n: int = 500) -> str:
    common = ["the", "and", "of", "a", "to", "in"]
    return " ".join(rng.choice(common * 3 + words * 5, size=n))


@pytest.fixture(scope="module")
def mfw_space() -> AuthorRelativeSpace:
    """Synthetic shelf with BOTH d18 separation and vocabulary separation."""
    rng = np.random.default_rng(SEED + 11)
    seed_words = {
        0: ["river", "stone", "dusk"],
        1: ["ledger", "office", "memo"],
        2: ["orchid", "violin", "satin"],
        3: ["engine", "circuit", "static"],
    }
    records = synthetic_records(seed=SEED + 11)
    for rec in records:
        author_idx = int(rec.author.split("-")[1])
        rec.body_text = _variant_text(seed_words[author_idx], rng)
    return AuthorRelativeSpace.build(
        records, min_works=3, seed=SEED, mfw_n=15
    )


def test_run_e1_e2_with_mfw_delta_spec(mfw_space):
    spec = VariantSpec("mfw_delta", "mfw_delta")
    e1 = run_e1(mfw_space, spec)
    e2 = run_e2(mfw_space, spec)
    assert e1["distance_variant"] == "mfw_delta"
    assert e2["distance_variant"] == "mfw_delta"
    # Planted vocabulary separation: Delta attribution must be strong.
    assert e1["criteria"]["pooled_auc"]["observed"] >= 0.9
    assert e2["criteria"]["top1_accuracy"]["observed"] >= 0.9
    # Sanity check only runs for d18.
    assert e2["sanity_check"]["top1_accuracy"] is None
    assert "NOT a gate" in e2["sanity_check"]["note"]


def test_combined_spec_matches_blend_formula(mfw_space):
    scale = mfw_space.blend["scale"]
    spec = VariantSpec("combined_alpha0.5", "combined", alpha=0.5, scale=scale)
    works_a = mfw_space.authors["author-0"].works[0]
    works_b = mfw_space.authors["author-1"].works[0]
    expected = 0.5 * float(np.linalg.norm(works_a.vector - works_b.vector)) + \
        0.5 * scale * float(np.mean(np.abs(works_a.mfw_z - works_b.mfw_z)))
    assert spec.distance(
        works_a.vector, works_a.mfw_z, works_b.vector, works_b.mfw_z
    ) == pytest.approx(expected, rel=1e-12)


def test_run_variant_comparison_structure_and_selection(mfw_space):
    eta2 = _eta2_weights(mfw_space, None)
    assert set(eta2) == set(mfw_space.dimensions)
    comparison = run_variant_comparison(mfw_space, eta2)
    labels = [row["label"] for row in comparison["rows"]]
    assert labels == [
        "d18", "d18_weighted", "mfw_delta",
        "combined_alpha0.3", "combined_alpha0.5", "combined_alpha0.7",
    ]
    for row in comparison["rows"]:
        for key in ("e1_auc", "silhouette_fraction", "top1", "top3", "all_pass"):
            assert key in row
    # Fully separated synthetic shelf: everything passes, simplest (d18) wins.
    assert all(row["all_pass"] for row in comparison["rows"])
    assert comparison["selection"]["selected"] == "d18"

    md = build_variant_comparison_markdown(
        comparison, {"generated": "t", "seed": SEED}
    )
    assert "| d18 " in md and "mfw_delta" in md
    assert "## Selection" in md


def test_variant_spec_requires_mfw_block(space):
    with pytest.raises(ValueError, match="MFW"):
        run_e1(space, VariantSpec("mfw_delta", "mfw_delta"))
    with pytest.raises(ValueError, match="MFW"):
        run_e2(space, VariantSpec("combined", "combined", alpha=0.5, scale=1.0))


# =============================================================================
# E6 — window-length sensitivity (issue #60 criterion 3; documentation-only)
# =============================================================================

from validate_author_space import (  # noqa: E402
    build_e6_markdown,
    run_e6,
)


def test_e6_structure_and_determinism(mfw_space):
    """E6 on the synthetic mfw shelf: structure, no gate, seeded determinism."""
    result = run_e6(
        mfw_space, seed=SEED, window_lengths=(40, 100), max_windows_per_work=3
    )
    assert result["experiment"] == "e6"
    assert result["gate"] is None
    assert result["pass"] is True          # documentation-only, never gates
    assert result["criteria"] == {}
    assert result["window_lengths"] == [40, 100]
    assert [row["window_words"] for row in result["per_length"]] == [40, 100]
    assert result["full_work_reference"]["window_words"] == "full"
    assert result["skipped_works"] == []

    for row in result["per_length"] + [result["full_work_reference"]]:
        assert row["n_windows"] > 0
        assert 0.0 <= row["top1_accuracy"] <= 1.0
        assert row["top1_accuracy"] <= row["top3_accuracy"] <= 1.0
        assert row["within"]["n"] > 0 and row["between"]["n"] > 0
        # Between distances pool (n_authors - 1) per trial.
        assert row["between"]["n"] == row["within"]["n"] * (result["n_authors"] - 1)
        assert row["within"]["median"] is not None
        assert row["between"]["median"] is not None
        assert 0.0 <= row["auc"] <= 1.0

    # Window cap honored: 4 authors x 6 works x <= 3 windows.
    assert all(row["n_windows"] <= 24 * 3 for row in result["per_length"])

    again = run_e6(
        mfw_space, seed=SEED, window_lengths=(40, 100), max_windows_per_work=3
    )
    assert again == result


def test_e6_separates_planted_vocabulary(mfw_space):
    """Planted per-author vocabulary: windows attribute well above chance and
    W medians sit below B medians at every tested length."""
    result = run_e6(
        mfw_space, seed=SEED, window_lengths=(60, 120), max_windows_per_work=4
    )
    for row in result["per_length"] + [result["full_work_reference"]]:
        assert row["top1_accuracy"] >= 0.5      # chance = 0.25 (4 authors)
        assert row["within"]["median"] < row["between"]["median"]
        assert row["auc"] >= 0.7
    # Full works carry at least as much signal as the shortest windows.
    shortest = result["per_length"][0]
    assert result["full_work_reference"]["auc"] >= shortest["auc"] - 1e-9


def test_e6_requires_mfw_block(space):
    with pytest.raises(ValueError, match="MFW block"):
        run_e6(space, seed=SEED)


def test_e6_skips_works_without_text(mfw_space):
    """Window lengths longer than every text -> zero windows everywhere."""
    result = run_e6(mfw_space, seed=SEED, window_lengths=(10_000,))
    row = result["per_length"][0]
    assert row["n_windows"] == 0
    assert row["top1_accuracy"] is None
    assert row["auc"] is None
    # Full-work reference is unaffected (uses persisted z-vectors).
    assert result["full_work_reference"]["n_windows"] > 0


def test_e6_markdown_report(mfw_space):
    result = run_e6(
        mfw_space, seed=SEED, window_lengths=(40, 100), max_windows_per_work=3
    )
    md = build_e6_markdown(result, {"generated": "t", "baseline_dir": "x"})
    assert "# E6 — Window-Length Sensitivity" in md
    assert "No pass/fail gate" in md
    assert "| 40 |" in md and "| 100 |" in md and "| full |" in md
    assert "## Reading" in md


def test_main_does_not_emit_e6_outputs_unless_requested(tmp_path):
    """E6 is opt-in: a default/gated CLI run must not write e6 artifacts.
    (The CLI e6 path needs on-disk body text via a manifest, so the full
    CLI e6 round-trip is exercised by the gold-shelf run, not unit tests;
    run_e6 itself is covered above through the in-memory space.)"""
    import validate_author_space as vas

    shelf_dir = tmp_path / "shelf"
    _write_synthetic_shelf(shelf_dir, synthetic_records())
    out_dir = tmp_path / "out"
    rc = vas.main(
        [
            "--baseline-dir", str(shelf_dir),
            "--output-dir", str(out_dir),
            "--seed", str(SEED),
            "--experiments", "e1",
        ]
    )
    assert rc == 0
    assert not (out_dir / "e6_results.json").exists()
    assert not (out_dir / "e6_report.md").exists()


def test_run_experiments_includes_e6(mfw_space):
    results = run_experiments(
        mfw_space, ["e1", "e6"], seed=SEED,
        e6_window_lengths=(50,), e6_max_windows=2,
    )
    assert set(results) == {"e1", "e6"}
    assert results["e6"]["window_lengths"] == [50]
    assert results["e6"]["max_windows_per_work"] == 2
