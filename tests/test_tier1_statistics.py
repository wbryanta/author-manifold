"""Unit tests for the P7 statistical helpers
(tools/tier1_statistics.py; issue #95 P7).

Covers: Clopper-Pearson edge cases (0/n, n/n, invalid n), exact binomial
sanity values, Holm-Bonferroni ordering/monotonicity/capping, permutation
determinism under a fixed seed (including the degenerate all-zero case),
bootstrap determinism, and the empirical match-probability null.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add tools/ to path to import tier1_statistics.
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from tier1_statistics import (  # noqa: E402
    binom_p,
    bootstrap_median_ci,
    clopper_pearson,
    cp_lower,
    cp_upper,
    empirical_match_null,
    holm_bonferroni,
    max_rate_excluded_zero,
    permutation_rate_test,
)


# ---------------------------------------------------------------------------
# Clopper-Pearson edge cases
# ---------------------------------------------------------------------------

class TestClopperPearson:
    def test_zero_of_n_lower_is_exactly_zero(self):
        lo, hi = clopper_pearson(0, 24)
        assert lo == 0.0
        # Closed form for k=0, two-sided 95%: 1 - (alpha/2)**(1/n)
        assert hi == pytest.approx(1.0 - 0.025 ** (1.0 / 24.0), rel=1e-9)

    def test_n_of_n_upper_is_exactly_one(self):
        lo, hi = clopper_pearson(36, 36)
        assert hi == 1.0
        # Closed form for k=n: lower = (alpha/2)**(1/n)
        assert lo == pytest.approx(0.025 ** (1.0 / 36.0), rel=1e-9)

    def test_one_sided_upper_zero_of_n_closed_form(self):
        assert cp_upper(0, 24) == pytest.approx(1.0 - 0.05 ** (1.0 / 24.0), rel=1e-9)

    def test_one_sided_lower_n_of_n_closed_form(self):
        assert cp_lower(36, 36) == pytest.approx(0.05 ** (1.0 / 36.0), rel=1e-9)
        assert cp_upper(36, 36) == 1.0
        assert cp_lower(0, 24) == 0.0

    def test_interval_contains_point_estimate(self):
        lo, hi = clopper_pearson(9, 24)
        assert lo < 9 / 24 < hi

    def test_invalid_n_raises(self):
        with pytest.raises(ValueError):
            clopper_pearson(0, 0)
        with pytest.raises(ValueError):
            cp_upper(0, 0)
        with pytest.raises(ValueError):
            max_rate_excluded_zero(0)

    def test_invalid_k_raises(self):
        with pytest.raises(ValueError):
            clopper_pearson(25, 24)
        with pytest.raises(ValueError):
            clopper_pearson(-1, 24)

    def test_max_rate_excluded_matches_one_sided_upper(self):
        assert max_rate_excluded_zero(24) == pytest.approx(cp_upper(0, 24), rel=1e-9)


# ---------------------------------------------------------------------------
# Exact binomial sanity
# ---------------------------------------------------------------------------

class TestBinomP:
    def test_zero_of_n_vs_p0_one_sided_is_survival_closed_form(self):
        # P(X = 0 | n=24, p=0.10) = 0.9**24 under the 'less' alternative.
        assert binom_p(0, 24, 0.10, alternative="less") == pytest.approx(
            0.9 ** 24, rel=1e-12
        )

    def test_all_successes_vs_p0(self):
        # P(X = 36 | n=36, p=0.9) = 0.9**36 under the 'greater' alternative.
        assert binom_p(36, 36, 0.90, alternative="greater") == pytest.approx(
            0.9 ** 36, rel=1e-12
        )

    def test_two_sided_at_half_is_symmetric(self):
        assert binom_p(22, 33, 0.5) == pytest.approx(binom_p(11, 33, 0.5), rel=1e-9)


# ---------------------------------------------------------------------------
# Holm-Bonferroni
# ---------------------------------------------------------------------------

class TestHolm:
    def test_known_example_ordering(self):
        # sorted: .005 -> 4x, .01 -> 3x, .03 -> 2x, .04 -> 1x with monotone max
        pvals = [0.01, 0.04, 0.03, 0.005]
        adj = holm_bonferroni(pvals)
        assert adj == pytest.approx([0.03, 0.06, 0.06, 0.02])

    def test_results_in_input_order(self):
        pvals = [0.04, 0.005, 0.03, 0.01]
        adj = holm_bonferroni(pvals)
        # smallest raw p gets m * p regardless of position
        assert adj[1] == pytest.approx(0.02)
        assert adj[0] == pytest.approx(0.06)

    def test_monotone_nondecreasing_in_sorted_order(self):
        rng = np.random.default_rng(7)
        pvals = list(rng.uniform(0, 1, size=20))
        adj = holm_bonferroni(pvals)
        order = sorted(range(20), key=lambda i: pvals[i])
        sorted_adj = [adj[i] for i in order]
        assert all(a <= b + 1e-12 for a, b in zip(sorted_adj, sorted_adj[1:]))

    def test_caps_at_one(self):
        assert holm_bonferroni([0.9, 0.8]) == [1.0, 1.0]

    def test_single_p_unchanged(self):
        assert holm_bonferroni([0.037]) == [pytest.approx(0.037)]

    def test_empty(self):
        assert holm_bonferroni([]) == []


# ---------------------------------------------------------------------------
# Permutation test: determinism + degenerate case
# ---------------------------------------------------------------------------

class TestPermutation:
    def test_deterministic_with_seed(self):
        a = [1, 0, 0, 1, 0, 0, 0, 0]
        b = [1, 1, 0, 1, 1, 0, 1, 0]
        r1 = permutation_rate_test(a, b, n_perm=2000, seed=123)
        r2 = permutation_rate_test(a, b, n_perm=2000, seed=123)
        assert r1["p_monte_carlo"] == r2["p_monte_carlo"]
        assert r1["p_exact_hypergeometric"] == r2["p_exact_hypergeometric"]

    def test_seed_changes_mc_stream_not_exact(self):
        a = [1, 0, 0, 1, 0, 0, 0, 0]
        b = [1, 1, 0, 1, 1, 0, 1, 0]
        r1 = permutation_rate_test(a, b, n_perm=500, seed=1)
        r2 = permutation_rate_test(a, b, n_perm=500, seed=2)
        assert r1["p_exact_hypergeometric"] == r2["p_exact_hypergeometric"]

    def test_degenerate_all_zero_is_p_one_and_flagged(self):
        r = permutation_rate_test([0] * 24, [0] * 36, n_perm=200, seed=42)
        assert r["degenerate"] is True
        assert r["p_exact_hypergeometric"] == pytest.approx(1.0)
        assert r["p_monte_carlo"] == pytest.approx(1.0)

    def test_mc_close_to_exact(self):
        a = [0] * 10 + [1] * 2
        b = [1] * 8 + [0] * 4
        r = permutation_rate_test(a, b, n_perm=20000, seed=9)
        assert r["p_monte_carlo"] == pytest.approx(
            r["p_exact_hypergeometric"], abs=0.02
        )


# ---------------------------------------------------------------------------
# Bootstrap median CI
# ---------------------------------------------------------------------------

class TestBootstrap:
    def test_deterministic_with_seed(self):
        vals = [1.45, 1.51, 1.56, 1.57, 1.58, 1.64]
        r1 = bootstrap_median_ci(vals, n_boot=2000, seed=99)
        r2 = bootstrap_median_ci(vals, n_boot=2000, seed=99)
        assert (r1["ci_lo"], r1["ci_hi"]) == (r2["ci_lo"], r2["ci_hi"])

    def test_ci_contains_median_and_brackets(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        r = bootstrap_median_ci(vals, n_boot=2000, seed=3)
        assert r["ci_lo"] <= r["median"] <= r["ci_hi"]
        assert min(vals) <= r["ci_lo"] and r["ci_hi"] <= max(vals)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            bootstrap_median_ci([])


# ---------------------------------------------------------------------------
# Empirical match null
# ---------------------------------------------------------------------------

class TestEmpiricalNull:
    def test_uniform_reduces_to_design_null(self):
        targets = {"a": 6, "b": 6, "c": 6, "d": 6}
        ref = {x: 1 for x in "abcdefghijklmno"}  # 15 authors uniform
        assert empirical_match_null(targets, ref) == pytest.approx(1.0 / 15.0)

    def test_missing_target_contributes_zero(self):
        targets = {"a": 1, "z": 1}
        ref = {"a": 10}  # 'z' never nearest in reference
        assert empirical_match_null(targets, ref) == pytest.approx(0.5 * 1.0)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            empirical_match_null({}, {"a": 1})
        with pytest.raises(ValueError):
            empirical_match_null({"a": 1}, {})
