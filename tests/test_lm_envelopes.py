"""Length-matched envelopes (LM-W) + cluster-robust inference helpers.

Unit tests for the pure statistics (AuthorLMEnvelope, anova_icc,
design_effect) plus integration tests against the shipped artifacts: the
released PD envelope sidecars must load, agree with the recorded E8
numbers (paper §3.9/§9.1: PD pooled held-out inside@p90 1375/1575 full,
1378/1575 fw-only), and rebuild deterministically from the shipped shelf
texts.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from author_manifold.author_space import (
    AuthorLMEnvelope,
    AuthorRelativeSpace,
    LengthMatchedEnvelopes,
    LM_DEFAULT_WINDOW_WORDS,
    LM_QUANTILE_LEVELS,
    anova_icc,
    design_effect,
    sha256_of_file,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO_ROOT / "data/artifacts"


def _synthetic_envelope() -> AuthorLMEnvelope:
    """Three works, ten windows each, distances 0.1 .. 3.0."""
    windows = []
    d = 0.0
    for work_index, work in enumerate(("alpha", "beta", "gamma")):
        for w in range(10):
            d += 0.1
            windows.append({
                "work_index": work_index, "work": work,
                "window": w, "distance": round(d, 10),
            })
    dists = np.asarray([w["distance"] for w in windows])
    return AuthorLMEnvelope(
        author="synthetic",
        n_works=3,
        works_used=["alpha", "beta", "gamma"],
        windows=windows,
        quantiles={f"p{q}": float(np.percentile(dists, q))
                   for q in LM_QUANTILE_LEVELS},
    )


class TestAuthorLMEnvelope:
    def test_percentile_of_is_midrank(self):
        env = _synthetic_envelope()
        assert env.percentile_of(0.0) == 0.0
        assert env.percentile_of(999.0) == 100.0
        # 1.55 sits between the 15th and 16th of 30 sorted distances.
        assert env.percentile_of(1.55) == pytest.approx(50.0)
        # An exact hit gets the mid-rank of its ties.
        assert env.percentile_of(env.windows[0]["distance"]) == pytest.approx(
            100.0 * 0.5 / 30)

    def test_entered_uses_quantile_levels(self):
        env = _synthetic_envelope()
        p90 = env.quantiles["p90"]
        assert env.entered(p90 - 1e-9)
        assert env.entered(p90)          # boundary is inside (<=)
        assert not env.entered(p90 + 1e-9)
        assert env.entered(p90 + 1e-9, level=99)

    def test_held_out_entry_is_leave_work_out(self):
        env = _synthetic_envelope()
        ho = env.held_out_entry(level=90)
        assert ho["n"] == 30
        assert len(ho["per_work"]) == 3
        # gamma's windows (2.1..3.0) sit above the other works' p90
        # (alpha+beta distances are 0.1..2.0, p90 = 1.81): none inside.
        gamma = next(w for w in ho["per_work"] if w["work"] == "gamma")
        assert gamma["inside"] == 0
        # alpha's windows (0.1..1.0) sit inside beta+gamma's p90: all inside.
        alpha = next(w for w in ho["per_work"] if w["work"] == "alpha")
        assert alpha["inside"] == alpha["n_windows"]
        assert ho["inside"] == sum(w["inside"] for w in ho["per_work"])

    def test_bootstrap_quantile_ci_is_seeded_and_ordered(self):
        env = _synthetic_envelope()
        lo1, hi1 = env.bootstrap_quantile_ci(90, n_bootstrap=200, seed=7)
        lo2, hi2 = env.bootstrap_quantile_ci(90, n_bootstrap=200, seed=7)
        assert (lo1, hi1) == (lo2, hi2)
        assert lo1 <= env.quantiles["p90"] <= hi1

    def test_roundtrip_to_from_dict(self):
        env = _synthetic_envelope()
        clone = AuthorLMEnvelope.from_dict(env.author, env.to_dict())
        assert clone.quantiles == env.quantiles
        assert clone.n_works == env.n_works
        assert [w["distance"] for w in clone.windows] == [
            w["distance"] for w in env.windows]


class TestClusterInference:
    def test_icc_zero_when_clusters_identical(self):
        values = [0, 1, 0, 1, 0, 1]
        clusters = ["a", "a", "b", "b", "c", "c"]
        assert anova_icc(values, clusters) == pytest.approx(0.0, abs=0.35)

    def test_icc_one_when_clusters_are_constant_and_distinct(self):
        values = [0, 0, 0, 1, 1, 1]
        clusters = ["a", "a", "a", "b", "b", "b"]
        assert anova_icc(values, clusters) == pytest.approx(1.0)

    def test_icc_degenerate_inputs_return_zero(self):
        assert anova_icc([1.0, 2.0], ["a", "a"]) == 0.0          # 1 cluster
        assert anova_icc([1.0, 2.0], ["a", "b"]) == 0.0          # singletons
        assert anova_icc([], []) == 0.0

    def test_icc_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            anova_icc([1.0], ["a", "b"])

    def test_design_effect_accounting(self):
        values = [0, 0, 0, 1, 1, 1]
        clusters = ["a", "a", "a", "b", "b", "b"]
        de = design_effect(values, clusters)
        assert de["n"] == 6
        assert de["n_clusters"] == 2
        assert de["mean_cluster_size"] == 3.0
        # Perfect clustering: DEFF = 1 + (3-1)*1 = 3, n_eff = 2.
        assert de["design_effect"] == pytest.approx(3.0)
        assert de["n_eff"] == pytest.approx(2.0)

    def test_design_effect_floor_at_one(self):
        de = design_effect([0, 1, 0, 1], ["a", "a", "b", "b"])
        assert de["design_effect"] >= 1.0
        assert de["n_eff"] <= de["n"]


class TestShaOfFile:
    def test_sha256_of_file(self, tmp_path):
        p = tmp_path / "x.bin"
        p.write_bytes(b"author-manifold")
        import hashlib
        assert sha256_of_file(p) == hashlib.sha256(b"author-manifold").hexdigest()


@pytest.mark.integration
class TestReleasedSidecars:
    """The released envelope sidecars are self-consistent and match the
    recorded E8 numbers (the §9.2 promise-4 substrate)."""

    @pytest.mark.parametrize("name,pooled_inside", [
        ("lm_envelopes_pd_3000w.json", 1375),
        ("lm_envelopes_pd_fwonly_3000w.json", 1378),
    ])
    def test_pd_sidecars_reproduce_recorded_e8_pooled_rates(
            self, name, pooled_inside):
        envs = LengthMatchedEnvelopes.from_artifact(ARTIFACTS / name)
        assert len(envs.authors) == 9
        assert envs.window_words == LM_DEFAULT_WINDOW_WORDS
        held = envs.held_out_entry_rates(level=90)
        n = sum(h["n"] for h in held.values())
        inside = sum(h["inside"] for h in held.values())
        assert (inside, n) == (pooled_inside, 1575)

    def test_wave2_sidecars_load_with_15_authors(self):
        for name in ("lm_envelopes_wave2_3000w.json",
                     "lm_envelopes_wave2_fwonly_3000w.json"):
            envs = LengthMatchedEnvelopes.from_artifact(ARTIFACTS / name)
            assert len(envs.authors) == 15
            for env in envs.authors.values():
                assert env.n_windows > 0
                assert env.quantiles["p50"] < env.quantiles["p90"]

    def test_wave2_sidecar_pins_shipped_space_artifact(self):
        envs = LengthMatchedEnvelopes.from_artifact(
            ARTIFACTS / "lm_envelopes_wave2_3000w.json")
        assert envs.meta["source_artifact_sha256"] == sha256_of_file(
            ARTIFACTS / "author_space_v1_wave2.json")


@pytest.mark.integration
class TestBuildFromSpace:
    def test_pd_rebuild_subset_matches_released_sidecar(self):
        """Rebuild Austen's envelope from the shipped shelf texts and check
        the window distances agree exactly with the released sidecar."""
        space = AuthorRelativeSpace.from_artifact(
            ARTIFACTS / "author_space_pd_v1.json")
        # Restrict to one author to keep the test fast.
        space.authors = {"austen-jane": space.authors["austen-jane"]}
        envs = LengthMatchedEnvelopes.build_from_space(
            space, text_root=REPO_ROOT,
            source_artifact=ARTIFACTS / "author_space_pd_v1.json")
        released = json.loads(
            (ARTIFACTS / "lm_envelopes_pd_3000w.json").read_text())
        mine = envs.authors["austen-jane"]
        ref = released["authors"]["austen-jane"]
        assert mine.n_windows == ref["n_windows"]
        assert mine.quantiles == pytest.approx(ref["quantiles"])
        ref_d = [w["distance"] for w in ref["windows"]]
        my_d = [w["distance"] for w in mine.windows]
        assert my_d == pytest.approx(ref_d)

    def test_requires_mfw_delta_variant(self):
        space = AuthorRelativeSpace.from_artifact(
            ARTIFACTS / "author_space_pd_v1.json")
        space.distance_variant = "d18"
        with pytest.raises(ValueError, match="mfw_delta"):
            LengthMatchedEnvelopes.build_from_space(space, text_root=REPO_ROOT)
