"""
Tests for the author-relative measurement space (ADR-0041, forthcoming).

Unit tests run on synthetic baselines (4 authors x 5 works with controlled
separation); the integration test builds a real artifact from
data/pd_work_baselines (public-domain shelf) via the build tool.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pytest

from author_manifold.author_space import (
    AuthorRelativeSpace,
    DIMENSION_SET_V1,
    WorkRecord,
    extract_features,
    work_record_from_baseline,
)

SEED = 20260609


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
    works_per_author: int = 5,
    separation: float = 3.0,
    noise: float = 0.1,
    seed: int = SEED,
) -> List[WorkRecord]:
    """Synthetic shelf: well-separated author centers, small within noise."""
    rng = np.random.default_rng(seed)
    dims = DIMENSION_SET_V1
    records: List[WorkRecord] = []
    for a in range(n_authors):
        center = rng.normal(0.0, separation, size=len(dims))
        for w in range(works_per_author):
            values = center + rng.normal(0.0, noise, size=len(dims))
            baseline = make_baseline(dict(zip(dims, values)), f"author{a}-work{w}")
            records.append(
                work_record_from_baseline(
                    baseline,
                    author=f"author-{a}",
                    path=f"synthetic/author-{a}/work{w}_baseline.json",
                    dimensions=dims,
                )
            )
    return records


@pytest.fixture(scope="module")
def space() -> AuthorRelativeSpace:
    return AuthorRelativeSpace.build(
        synthetic_records(), min_works=3, seed=SEED, generated="2026-06-09T00:00:00Z"
    )


def test_extract_features_d18_and_style_fallback():
    baseline = make_baseline({"lexical_density": 0.5}, "t")
    baseline["style_features"] = {"ttr": 0.11}
    feats = extract_features(baseline, ["lexical_density", "ttr", "sentence_cv"])
    assert feats["lexical_density"] == 0.5
    assert feats["ttr"] == 0.11          # found via style_features fallback
    assert feats["sentence_cv"] is None  # missing -> None, imputed at build


def test_within_distances_below_between_on_separable_data(space):
    w_all = space.within["loo"].samples + space.within["pairs"].samples
    b_all = space.between["pairs"].samples + space.between["work_to_centroid"].samples
    assert w_all and b_all
    assert max(w_all) < min(b_all)


def test_quantiles_ordered_sensibly(space):
    for family in list(space.within.values()) + list(space.between.values()):
        q = family.quantiles
        ordered = [q[f"p{lvl}"] for lvl in (5, 10, 25, 50, 75, 90, 95)]
        assert ordered == sorted(ordered)
        for key, (lo, hi) in family.ci95.items():
            assert lo <= hi
    assert space.within["pooled"].quantiles["p50"] < space.between["pairs"].quantiles["p50"]


def test_calibration_sample_counts(space):
    # 4 authors x 5 works: loo = 20, within pairs = 4*C(5,2) = 40,
    # between pairs = C(20,2) - 40 = 150, work->other-centroid = 20*3 = 60.
    assert space.within["loo"].n == 20
    assert space.within["pairs"].n == 40
    assert space.within["pooled"].n == 60
    assert space.between["pairs"].n == 150
    assert space.between["work_to_centroid"].n == 60


def test_percentile_api_returns_p50_at_median_within_distance(space):
    rng = np.random.default_rng(SEED + 1)
    slug = sorted(space.authors)[0]
    entry = space.authors[slug]
    d50 = space.within["loo"].quantiles["p50"]
    direction = rng.normal(size=len(space.dimensions))
    direction /= np.linalg.norm(direction)
    target = entry.centroid + d50 * direction
    raw = dict(zip(space.dimensions, target * space.shelf_std + space.shelf_mean))

    result = space.place(raw)
    placement = next(p for p in result.placements if p.author == slug)
    assert placement.distance == pytest.approx(d50, rel=1e-6)
    assert 35.0 <= placement.w_percentile <= 65.0
    assert "within-author variation" in placement.statement


def test_placement_ranks_own_author_first(space):
    record = space.authors[sorted(space.authors)[2]].works[0]
    raw = {dim: record.raw[dim] for dim in space.dimensions}
    result = space.place(raw)
    assert result.nearest.author == record.author
    # Distances must be identical when given as an ordered raw vector.
    vec_result = space.place([raw[d] for d in space.dimensions])
    assert vec_result.distances() == pytest.approx(result.distances())


def test_artifact_round_trip_identical_placements(space, tmp_path):
    artifact_path = tmp_path / "author_space_v1.json"
    artifact = space.to_artifact(artifact_path)
    assert artifact_path.exists()
    assert set(artifact.keys()) == {
        "meta", "dimensions", "shelf_norm", "authors", "reference_authors",
        "distance_matrix", "within_author_dist", "between_author_dist",
        "feature_blocks", "distance_variant",
    }
    # D18-only space: no MFW block, no blend config.
    assert set(artifact["feature_blocks"]) == {"d18"}
    assert artifact["distance_variant"] == "d18"
    assert "blend" not in artifact

    reloaded = AuthorRelativeSpace.from_artifact(artifact_path)
    assert reloaded.dimensions == space.dimensions
    assert reloaded.meta["n_authors"] == space.meta["n_authors"]

    record = space.authors[sorted(space.authors)[1]].works[3]
    raw = {dim: record.raw[dim] for dim in space.dimensions}
    original = space.place(raw)
    restored = reloaded.place(raw)
    for orig, rest in zip(original.placements, restored.placements):
        assert orig.author == rest.author
        assert rest.distance == pytest.approx(orig.distance, rel=1e-12)
        assert rest.w_percentile == pytest.approx(orig.w_percentile, rel=1e-12)
        assert rest.b_percentile == pytest.approx(orig.b_percentile, rel=1e-12)


def test_min_works_exclusion_and_singleton_flag():
    records = synthetic_records()
    extra = synthetic_records(n_authors=2, works_per_author=2, seed=SEED + 7)
    # Rename: one author with 2 works, one singleton.
    for rec in extra:
        rec.author = {"author-0": "thin-author", "author-1": "lone-author"}[rec.author]
    records += [r for r in extra if r.author == "thin-author"]
    records += [r for r in extra if r.author == "lone-author"][:1]

    space = AuthorRelativeSpace.build(records, min_works=3, seed=SEED)
    assert set(space.authors) == {f"author-{i}" for i in range(4)}
    assert set(space.reference_authors) == {"thin-author", "lone-author"}
    assert space.reference_authors["lone-author"].singleton
    assert not space.reference_authors["thin-author"].singleton
    assert space.reference_authors["thin-author"].reference_only

    # Reference authors excluded from W/B calibration (counts unchanged).
    assert space.within["loo"].n == 20
    assert space.between["pairs"].n == 150

    # Excluded from default placement ranking; included on request with flag.
    raw = {d: r for d, r in zip(space.dimensions, space.shelf_mean)}
    default = space.place(raw)
    assert {p.author for p in default.placements} == set(space.authors)
    with_ref = space.place(raw, include_reference=True)
    ref_placements = [p for p in with_ref.placements if p.reference_only]
    assert {p.author for p in ref_placements} == {"thin-author", "lone-author"}
    assert any("reference-only" in p.statement for p in ref_placements)


def test_missing_dimension_imputation_and_coverage():
    records = synthetic_records()
    dropped = ["char_ngram_mean", "certainty_index"]
    # Remove two dims from a few works of author-0.
    for rec in records[:3]:
        for dim in dropped:
            rec.raw[dim] = None

    space = AuthorRelativeSpace.build(records, min_works=3, seed=SEED)
    touched = space.authors["author-0"].works[:3]
    for work in touched:
        assert work.imputed_dims == dropped
        assert work.coverage == pytest.approx(1.0 - len(dropped) / len(DIMENSION_SET_V1))
    coverage = space.meta["dimension_coverage"]
    assert coverage["char_ngram_mean"] == pytest.approx(17 / 20)
    assert coverage["lexical_density"] == 1.0

    # Placing a baseline missing dims must not crash and must record coverage.
    incomplete = make_baseline(
        {d: 0.0 for d in DIMENSION_SET_V1 if d not in dropped}, "incomplete"
    )
    result = space.place(incomplete)
    assert result.imputed_dims == dropped
    assert result.coverage < 1.0
    assert len(result.placements) == 4


def test_mahalanobis_secondary_method(space):
    record = space.authors[sorted(space.authors)[0]].works[0]
    raw = {dim: record.raw[dim] for dim in space.dimensions}
    result = space.place(raw, method="mahalanobis")
    assert result.method == "mahalanobis"
    assert all(p.distance >= 0.0 for p in result.placements)
    # Percentiles only calibrated for euclidean.
    assert all(p.w_percentile is None and p.b_percentile is None for p in result.placements)


def test_pairwise_author_matrix_symmetric(space):
    matrix = space.pairwise_author_matrix()
    slugs = sorted(space.authors)
    assert set(matrix) == set(slugs)
    for a in slugs:
        assert matrix[a][a] == 0.0
        for b in slugs:
            assert matrix[a][b] == pytest.approx(matrix[b][a])


@pytest.mark.integration
def test_build_tool_against_pd_shelf_baselines(tmp_path):
    repo_root = _repo_root()
    baseline_dir = repo_root / "data/pd_work_baselines"
    if not baseline_dir.is_dir():
        pytest.skip("pd_work_baselines not present")

    output = tmp_path / "author_space_v1.json"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    proc = subprocess.run(
        [
            sys.executable,
            str(repo_root / "tools/build_author_space.py"),
            "--baseline-dir", str(baseline_dir),
            "--min-works", "3",
            "--output", str(output),
        ],
        capture_output=True, text=True, env=env, timeout=300,
    )
    assert proc.returncode == 0, proc.stderr

    space = AuthorRelativeSpace.from_artifact(output)
    assert space.meta["n_authors"] >= 8
    assert space.meta["n_works"] >= space.meta["n_authors"] * 3
    assert len(space.dimensions) == len(DIMENSION_SET_V1)
    assert space.within["loo"].n > 0
    assert space.between["pairs"].n > 0
    assert space.within["pooled"].quantiles["p50"] < space.between["pairs"].quantiles["p50"]
    # NONFIC bucket must never enter the space (ADR-0036).
    assert "NONFIC_ON-WRITING" not in space.authors
    assert "NONFIC_ON-WRITING" not in space.reference_authors

    # A real work places its own author at a sane within percentile.
    with open(output, "r", encoding="utf-8") as handle:
        artifact = json.load(handle)
    slug = sorted(artifact["authors"])[0]
    work_path = artifact["authors"][slug]["works"][0]["path"]
    result = space.place(work_path)
    own = next(p for p in result.placements if p.author == slug)
    assert own.w_percentile is not None and 0.0 <= own.w_percentile <= 100.0


# =============================================================================
# MFW frequency block + distance variants (ADR-0041 amendment)
# =============================================================================

from author_manifold.author_space import (  # noqa: E402
    MFWBlock,
    MFW_DEFAULT_N,
    mfw_tokenize,
)


def _mfw_author_text(seed_words: List[str], rng: np.random.Generator, n: int = 600) -> str:
    """Synthetic text with an author-specific word distribution.

    Shared core vocabulary plus author-discriminating words, so MFW Delta
    separates the synthetic authors.
    """
    common = ["the", "and", "of", "a", "to", "in", "was", "it"]
    pool = common * 4 + seed_words * 6
    return " ".join(rng.choice(pool, size=n))


def synthetic_mfw_records(seed: int = SEED) -> List[WorkRecord]:
    """3 authors x 4 works with distinct d18 centers AND distinct vocabularies."""
    rng = np.random.default_rng(seed)
    seed_words = {
        0: ["river", "stone", "dusk", "horse"],
        1: ["ledger", "office", "memo", "contract"],
        2: ["orchid", "violin", "satin", "mirror"],
    }
    records: List[WorkRecord] = []
    for a in range(3):
        center = rng.normal(0.0, 3.0, size=len(DIMENSION_SET_V1))
        for w in range(4):
            values = center + rng.normal(0.0, 0.1, size=len(DIMENSION_SET_V1))
            baseline = make_baseline(dict(zip(DIMENSION_SET_V1, values)), f"a{a}-w{w}")
            record = work_record_from_baseline(
                baseline,
                author=f"author-{a}",
                path=f"synthetic/author-{a}/w{w}_baseline.json",
                dimensions=DIMENSION_SET_V1,
            )
            record.body_text = _mfw_author_text(seed_words[a], rng)
            records.append(record)
    return records


@pytest.fixture(scope="module")
def mfw_space() -> AuthorRelativeSpace:
    return AuthorRelativeSpace.build(
        synthetic_mfw_records(),
        min_works=3,
        seed=SEED,
        mfw_n=20,
        distance_variant="combined",
        alpha=0.5,
        generated="2026-06-09T00:00:00Z",
    )


def test_mfw_tokenize_matches_stylometry_regex_convention():
    assert mfw_tokenize("Don't STOP the beat-box, now!") == [
        "don't", "stop", "the", "beat", "box", "now"
    ]
    assert mfw_tokenize("Numbers 123 vanish") == ["numbers", "vanish"]


def test_mfw_featurization_on_synthetic_text():
    """Known counts -> exact relative frequencies and z-scores."""
    block = MFWBlock(
        vocabulary=["the", "river", "ledger"],
        mean=np.array([100.0, 10.0, 5.0]),
        std=np.array([20.0, 4.0, 2.0]),
    )
    # 10 tokens: 'the' x3, 'river' x1, 'ledger' x0, filler x6.
    text = "the the the river fish swim deep blue water cold"
    rel = block.relative_frequencies(mfw_tokenize(text))
    assert rel == pytest.approx([300.0, 100.0, 0.0])
    z = block.featurize_text(text)
    assert z == pytest.approx([(300 - 100) / 20, (100 - 10) / 4, (0 - 5) / 2])
    # Delta = mean |z_i - z_j|.
    other = np.zeros(3)
    assert MFWBlock.delta(z, other) == pytest.approx(np.mean(np.abs(z)))


def test_mfw_block_build_and_zscore_determinism(mfw_space):
    block = mfw_space.mfw
    assert block is not None
    assert block.n_mfw == 20
    # Vocabulary is shelf-frequency-ordered; common core words must be in it.
    assert "the" in block.vocabulary
    # Building twice from identical records gives identical block + z-vectors.
    again = AuthorRelativeSpace.build(
        synthetic_mfw_records(), min_works=3, seed=SEED,
        mfw_n=20, distance_variant="combined", alpha=0.5,
    )
    assert again.mfw.vocabulary == block.vocabulary
    assert np.array_equal(again.mfw.mean, block.mean)
    assert np.array_equal(again.mfw.std, block.std)
    for slug in mfw_space.authors:
        for w1, w2 in zip(mfw_space.authors[slug].works, again.authors[slug].works):
            assert np.array_equal(w1.mfw_z, w2.mfw_z)
    assert again.blend == mfw_space.blend
    # Featurizing the same text via the block is deterministic too.
    text = "the river the ledger orchid"
    assert np.array_equal(block.featurize_text(text), block.featurize_text(text))


def test_combined_distance_math(mfw_space):
    """combined = alpha * d18 + (1 - alpha) * scale * Delta, by hand."""
    a = mfw_space.authors["author-0"].works[0]
    b = mfw_space.authors["author-1"].works[1]
    d18 = float(np.linalg.norm(a.vector - b.vector))
    delta = float(np.mean(np.abs(a.mfw_z - b.mfw_z)))
    scale = mfw_space.blend["scale"]
    assert scale == pytest.approx(
        mfw_space.blend["d18_between_median"] / mfw_space.blend["delta_between_median"]
    )
    expected = 0.5 * d18 + 0.5 * scale * delta
    observed = mfw_space.work_distance(a.vector, a.mfw_z, b.vector, b.mfw_z)
    assert observed == pytest.approx(expected, rel=1e-12)
    # Components agree with the dedicated helpers.
    assert mfw_space.d18_component(a.vector, b.vector) == pytest.approx(d18)
    assert MFWBlock.delta(a.mfw_z, b.mfw_z) == pytest.approx(delta)


def test_mfw_calibration_under_combined_distance(mfw_space):
    """W/B distributions are recomputed under the active combined distance."""
    # Spot-check: the smallest within-pair sample equals the smallest
    # work-pair combined distance computed directly.
    pairs = []
    for entry in mfw_space.authors.values():
        works = entry.works
        for i in range(len(works)):
            for j in range(i + 1, len(works)):
                pairs.append(
                    mfw_space.work_distance(
                        works[i].vector, works[i].mfw_z,
                        works[j].vector, works[j].mfw_z,
                    )
                )
    assert sorted(pairs) == pytest.approx(mfw_space.within["pairs"].samples)


def test_place_with_raw_text_combined(mfw_space, tmp_path):
    record = mfw_space.authors["author-2"].works[0]
    baseline = make_baseline(
        {d: record.raw[d] for d in mfw_space.dimensions}, record.title
    )
    result = mfw_space.place(baseline, text=record.body_text)
    assert result.nearest.author == "author-2"
    own = next(p for p in result.placements if p.author == "author-2")
    assert own.w_percentile is not None

    # A .txt path is accepted in place of text=.
    txt = tmp_path / "sample.txt"
    txt.write_text(record.body_text, encoding="utf-8")
    result_path = mfw_space.place(baseline, text=txt.read_text(encoding="utf-8"))
    assert result_path.distances() == pytest.approx(result.distances())

    # Baseline-only input must raise a clear error when MFW is required.
    with pytest.raises(ValueError, match="requires raw text"):
        mfw_space.place(baseline)
    # Text-only input must raise for combined (needs d18 features too).
    with pytest.raises(ValueError, match="requires baseline features"):
        mfw_space.place(text=record.body_text)


def test_place_text_only_mfw_delta_variant():
    space = AuthorRelativeSpace.build(
        synthetic_mfw_records(), min_works=3, seed=SEED,
        mfw_n=20, distance_variant="mfw_delta",
    )
    record = space.authors["author-1"].works[2]
    result = space.place(text=record.body_text)
    assert result.nearest.author == "author-1"
    assert result.coverage == 1.0 and result.imputed_dims == []
    # .txt path as the positional argument works too.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "work.txt"
        path.write_text(record.body_text, encoding="utf-8")
        via_path = space.place(str(path))
        assert via_path.distances() == pytest.approx(result.distances())


def test_mfw_artifact_round_trip(mfw_space, tmp_path):
    artifact_path = tmp_path / "author_space_mfw.json"
    artifact = mfw_space.to_artifact(artifact_path)
    assert set(artifact["feature_blocks"]) == {"d18", "mfw_delta"}
    assert artifact["distance_variant"] == "combined"
    assert artifact["blend"]["alpha"] == 0.5
    assert artifact["meta"]["distance_variant"] == "combined"

    reloaded = AuthorRelativeSpace.from_artifact(artifact_path)
    assert reloaded.distance_variant == "combined"
    assert reloaded.alpha == 0.5
    assert reloaded.mfw.vocabulary == mfw_space.mfw.vocabulary
    assert reloaded.mfw.mean == pytest.approx(mfw_space.mfw.mean)
    assert reloaded.mfw.std == pytest.approx(mfw_space.mfw.std)
    assert reloaded.blend == pytest.approx(mfw_space.blend)
    for slug in mfw_space.authors:
        assert reloaded.authors[slug].mfw_centroid == pytest.approx(
            mfw_space.authors[slug].mfw_centroid
        )
        for w1, w2 in zip(mfw_space.authors[slug].works, reloaded.authors[slug].works):
            assert w2.mfw_z == pytest.approx(w1.mfw_z)

    record = mfw_space.authors["author-0"].works[3]
    baseline = make_baseline(
        {d: record.raw[d] for d in mfw_space.dimensions}, record.title
    )
    original = mfw_space.place(baseline, text=record.body_text)
    restored = reloaded.place(baseline, text=record.body_text)
    for orig, rest in zip(original.placements, restored.placements):
        assert orig.author == rest.author
        assert rest.distance == pytest.approx(orig.distance, rel=1e-12)
        assert rest.w_percentile == pytest.approx(orig.w_percentile, rel=1e-12)


def test_artifact_without_mfw_block_loads_as_d18(space, tmp_path):
    """Backward compat: pre-1.1.0 artifacts (no feature_blocks) load fine."""
    artifact = space.to_artifact()
    # Simulate a legacy artifact.
    artifact.pop("feature_blocks", None)
    artifact.pop("distance_variant", None)
    artifact["meta"] = {
        k: v for k, v in artifact["meta"].items()
        if k not in ("distance_variant", "alpha", "feature_blocks")
    }
    legacy_path = tmp_path / "legacy.json"
    legacy_path.write_text(json.dumps(artifact), encoding="utf-8")

    legacy = AuthorRelativeSpace.from_artifact(legacy_path)
    assert legacy.distance_variant == "d18"
    assert legacy.mfw is None
    record = space.authors[sorted(space.authors)[0]].works[0]
    raw = {dim: record.raw[dim] for dim in space.dimensions}
    assert legacy.place(raw).distances() == pytest.approx(space.place(raw).distances())


def test_mfw_build_requires_text():
    records = synthetic_records(n_authors=2, works_per_author=3)
    with pytest.raises(ValueError, match="needs raw text"):
        AuthorRelativeSpace.build(
            records, min_works=3, seed=SEED, mfw_n=10, distance_variant="mfw_delta"
        )


def test_d18_weighted_variant_distance():
    records = synthetic_records()
    weights = {d: float(i + 1) for i, d in enumerate(DIMENSION_SET_V1)}
    space = AuthorRelativeSpace.build(
        records, min_works=3, seed=SEED,
        distance_variant="d18_weighted", dimension_weights=weights,
    )
    a = space.authors["author-0"].works[0]
    b = space.authors["author-1"].works[0]
    w = np.array([weights[d] for d in space.dimensions])
    w = w * (len(w) / w.sum())   # normalized to mean 1
    expected = float(np.sqrt(np.sum(w * (a.vector - b.vector) ** 2)))
    assert space.work_distance(a.vector, None, b.vector, None) == pytest.approx(expected)
    # Weights must be persisted and round-trip.
    artifact = space.to_artifact()
    reloaded = AuthorRelativeSpace.from_artifact(artifact)
    assert reloaded.work_distance(a.vector, None, b.vector, None) == pytest.approx(expected)
