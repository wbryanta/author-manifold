#!/usr/bin/env python3
"""P7 — Statistical treatment for the Tier 1 paper claims (issue #95).

Computes confidence intervals, exact tests, bootstrap CIs, permutation
framings, and a Holm-Bonferroni multiple-comparison registry for the headline
claims frozen in reports/validation/wave2/PRIMARY_ARTIFACT.md:

1. Enter-rate (style-prompted samples entering the target author's W-p90
   region): Clopper-Pearson bounds on k/n, exact one-sided binomial tests
   against meaningful alternatives, and a permutation/hypergeometric framing
   against the unprompted condition (documented as degenerate when the event
   count is zero everywhere).
2. Off-manifold (unprompted nearest-author W-percentile > 90 for all
   samples): Clopper-Pearson CI on k/n, the on-manifold rate the data can
   exclude, and an honest account of the W-percentile resolution limit (the
   percentile is an empirical mid-rank against the artifact's W LOO samples).
3. Model proximity medians: seeded bootstrap 95% CIs on each model's median
   unprompted nearest-author distance; pairwise exact Mann-Whitney U with
   Holm-Bonferroni across all model pairs.
4. Approach (style-prompted nearest-is-target): exact binomial against the
   1/n_authors design null and against an empirical null built from the
   unprompted nearest-author distribution.
5. Manuscript AI-closer chapters (optional trajectory input): binomial
   vs 50% plus CP CI, framed as
   DESCRIPTIVE (chapters share one author/manuscript; not independent).
6. Registry of all claims with Holm-Bonferroni-adjusted p-values.

The tool is re-runnable on the scaled corpus: all inputs are parametrized and
all n's are detected from the data files, never hard-coded.

Outputs <out-dir>/tier1_statistics.json + tier1_statistics.md.

Relates: issue #95 P7; docs/research/TIER1_PAPER_OUTLINE.md §10.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger("tier1_statistics")

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SEED = 20260609
DEFAULT_N_BOOT = 10_000
DEFAULT_N_PERM = 10_000

# The E4 gate: a sample is "inside" an author's region when its distance to
# that author sits at or below the within-author W-p90 (w_percentile <= 90).
W_REGION_PCT = 90.0


# ---------------------------------------------------------------------------
# Statistical helpers (unit-tested in tests/test_tier1_statistics.py)
# ---------------------------------------------------------------------------

def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """Exact two-sided (1 - alpha) Clopper-Pearson CI for a binomial proportion.

    Edge cases: k == 0 -> lower bound exactly 0.0; k == n -> upper bound
    exactly 1.0 (the beta quantile is undefined at those corners).
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if not 0 <= k <= n:
        raise ValueError(f"k must be in [0, n], got k={k}, n={n}")
    from scipy.stats import beta

    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2.0, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
    return lo, hi


def cp_upper(k: int, n: int, conf: float = 0.95) -> float:
    """One-sided exact upper confidence bound (level ``conf``) on a proportion.

    For k == 0 this equals 1 - (1 - conf)**(1/n): the largest rate p0 for
    which observing zero successes still has probability >= 1 - conf.
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if not 0 <= k <= n:
        raise ValueError(f"k must be in [0, n], got k={k}, n={n}")
    if k == n:
        return 1.0
    from scipy.stats import beta

    return float(beta.ppf(conf, k + 1, n - k))


def cp_lower(k: int, n: int, conf: float = 0.95) -> float:
    """One-sided exact lower confidence bound (level ``conf``) on a proportion."""
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if not 0 <= k <= n:
        raise ValueError(f"k must be in [0, n], got k={k}, n={n}")
    if k == 0:
        return 0.0
    from scipy.stats import beta

    return float(beta.ppf(1.0 - conf, k, n - k + 1))


def binom_p(k: int, n: int, p0: float, alternative: str = "two-sided") -> float:
    """Exact binomial test p-value (wraps scipy.stats.binomtest)."""
    from scipy.stats import binomtest

    return float(binomtest(k, n, p0, alternative=alternative).pvalue)


def max_rate_excluded_zero(n: int, conf: float = 0.95) -> float:
    """For 0/n successes: the smallest rate p0 rejectable one-sided at 1-conf.

    Any true rate >= this value would produce 0/n with probability < 1-conf,
    so the data exclude all rates at or above it. Identical to cp_upper(0, n).
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    return 1.0 - (1.0 - conf) ** (1.0 / n)


def holm_bonferroni(pvals: Sequence[float]) -> List[float]:
    """Holm-Bonferroni step-down adjusted p-values, in the input order.

    adj_(i) = max over j <= i of min(1, (m - j + 1) * p_(j)) with p sorted
    ascending; enforces monotonicity and caps at 1.
    """
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = min(1.0, (m - rank) * pvals[idx])
        running = max(running, val)
        adjusted[idx] = running
    return adjusted


def bootstrap_median_ci(
    values: Sequence[float],
    n_boot: int = DEFAULT_N_BOOT,
    seed: int = DEFAULT_SEED,
    alpha: float = 0.05,
) -> Dict[str, float]:
    """Seeded percentile-bootstrap CI on the median. Deterministic for a seed."""
    arr = np.asarray(list(values), dtype=float)
    if arr.size == 0:
        raise ValueError("values must be non-empty")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, arr.size, size=(n_boot, arr.size))
    meds = np.median(arr[idx], axis=1)
    lo, hi = np.percentile(meds, [100.0 * alpha / 2.0, 100.0 * (1.0 - alpha / 2.0)])
    return {
        "median": float(np.median(arr)),
        "ci_lo": float(lo),
        "ci_hi": float(hi),
        "n": int(arr.size),
        "n_boot": int(n_boot),
        "seed": int(seed),
    }


def permutation_rate_test(
    group_a: Sequence[int],
    group_b: Sequence[int],
    n_perm: int = DEFAULT_N_PERM,
    seed: int = DEFAULT_SEED,
) -> Dict[str, Any]:
    """One-sided label-permutation test on binary outcomes.

    Null: outcomes are exchangeable across groups. Reports P(count_A <= observed)
    under random relabeling — exactly the hypergeometric CDF — plus a seeded
    Monte Carlo replicate (deterministic for a given seed) as a cross-check.
    When the pooled event count is zero the test is DEGENERATE (p = 1.0,
    zero power); callers must report that honestly rather than as evidence.
    """
    from scipy.stats import hypergeom

    a = np.asarray(list(group_a), dtype=int)
    b = np.asarray(list(group_b), dtype=int)
    pooled = np.concatenate([a, b])
    n_a, total = int(a.size), int(pooled.size)
    successes = int(pooled.sum())
    observed = int(a.sum())

    p_exact = float(hypergeom.cdf(observed, total, successes, n_a))

    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_perm):
        perm = rng.permutation(pooled)
        if int(perm[:n_a].sum()) <= observed:
            hits += 1
    p_mc = (hits + 1) / (n_perm + 1)

    return {
        "observed_count_a": observed,
        "n_a": n_a,
        "n_b": int(b.size),
        "pooled_successes": successes,
        "p_exact_hypergeometric": p_exact,
        "p_monte_carlo": float(p_mc),
        "n_perm": int(n_perm),
        "seed": int(seed),
        "degenerate": successes == 0,
    }


def empirical_match_null(
    target_counts: Dict[str, int],
    reference_nearest_counts: Dict[str, int],
) -> float:
    """Null P(nearest == target) when targets are fixed by design and the
    nearest author is drawn iid from a reference (unprompted) distribution.

    p0 = sum_t  (n_target_t / n_targets) * (n_reference_nearest_t / n_reference)
    """
    n_targets = sum(target_counts.values())
    n_ref = sum(reference_nearest_counts.values())
    if n_targets == 0 or n_ref == 0:
        raise ValueError("target_counts and reference_nearest_counts must be non-empty")
    return float(
        sum(
            (cnt / n_targets) * (reference_nearest_counts.get(t, 0) / n_ref)
            for t, cnt in target_counts.items()
        )
    )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _resolve(path_str: str, *roots: Path) -> Optional[Path]:
    p = Path(path_str)
    if p.is_absolute() and p.exists():
        return p
    for root in roots:
        cand = (root / p).resolve()
        if cand.exists():
            return cand
    return None


def load_artifact_w_info(artifact_path: Path) -> Dict[str, Any]:
    """Pull the W distribution sizes that set the percentile resolution."""
    art = json.loads(artifact_path.read_text(encoding="utf-8"))
    within = art.get("within_author_dist", {})
    n_loo = int((within.get("loo") or {}).get("n", 0))
    n_pooled = int((within.get("pooled") or {}).get("n", 0))
    meta = art.get("meta", {})
    return {
        "artifact": str(artifact_path),
        "n_authors": int(meta.get("n_authors", 0)),
        "n_works": int(meta.get("n_works", 0)),
        # AuthorRelativeSpace.place() computes w_percentile against W *loo*
        # (see src/author_manifold/author_space.py: w_dist = self.within.get("loo")).
        "n_w_loo": n_loo,
        "n_w_pooled": n_pooled,
    }


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def section_enter_rate(sp: List[dict], up: List[dict], seed: int, n_perm: int) -> Dict[str, Any]:
    """Claim 1 — style-prompted samples entering the target W-p90 region."""
    n = len(sp)
    enters = [
        1 if (p.get("per_author", {}).get(p.get("style_target"), {})
              .get("w_percentile", 101.0) <= W_REGION_PCT) else 0
        for p in sp
    ]
    k = int(sum(enters))

    ci_lo, ci_hi = clopper_pearson(k, n)
    upper_1s = cp_upper(k, n)

    # Exact one-sided tests against meaningful alternatives H0: rate >= p0.
    alternatives = {}
    for p0 in (0.05, 0.10, 0.125, 0.20):
        alternatives[f"p0_{p0:g}"] = {
            "null": f"enter-rate >= {p0:g}",
            "p_value": binom_p(k, n, p0, alternative="less"),
            "rejected_at_0.05": binom_p(k, n, p0, alternative="less") < 0.05,
        }
    max_excluded = max_rate_excluded_zero(n) if k == 0 else upper_1s

    # Permutation framing vs unprompted. An unprompted sample has no style
    # target; the exchangeability-respecting outcome is "inside the W-p90
    # region of ANY gold-shelf author" (a superset of the target event, so
    # the comparison is conservative in favor of finding prompted entries).
    up_any = [
        1 if any(v.get("w_percentile", 101.0) <= W_REGION_PCT
                 for v in p.get("per_author", {}).values()) else 0
        for p in up
    ]
    sp_any = [
        1 if any(v.get("w_percentile", 101.0) <= W_REGION_PCT
                 for v in p.get("per_author", {}).values()) else 0
        for p in sp
    ]
    perm = permutation_rate_test(enters, up_any, n_perm=n_perm, seed=seed)
    perm_any = permutation_rate_test(sp_any, up_any, n_perm=n_perm, seed=seed + 1)

    return {
        "claim": f"{k}/{n} style-prompted samples entered the target author's W-p90 region",
        "k": k,
        "n": n,
        "rate": k / n,
        "clopper_pearson_95_two_sided": [ci_lo, ci_hi],
        "clopper_pearson_95_one_sided_upper": upper_1s,
        "max_enter_rate_excluded_one_sided_95": max_excluded,
        "exact_tests_vs_alternatives": alternatives,
        "permutation_vs_unprompted_target_region": perm,
        "permutation_vs_unprompted_any_region": perm_any,
        "assumptions": [
            "Samples treated as independent Bernoulli trials; the 24 samples "
            "come from 6 models x 4 targets, so model/target clustering is "
            "ignored — with k=0 the CP bound is unaffected by clustering "
            "direction but the effective n may be smaller than the nominal n.",
            "Permutation framing assumes exchangeability of prompted and "
            "unprompted samples w.r.t. region membership under the null.",
        ],
        "notes": (
            "The permutation test is DEGENERATE when no sample in either "
            "condition lies inside any W-p90 region (pooled event count 0): "
            "p = 1.0 by construction and the test has zero power. The "
            "informative quantity is the exact Clopper-Pearson upper bound."
            if perm["degenerate"] else
            "Permutation test is informative (non-zero pooled event count)."
        ),
    }


def section_off_manifold(up: List[dict], w_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Claim 2 — unprompted samples off-manifold (nearest W-pct > 90)."""
    n = len(up)
    k = int(sum(1 for p in up if p.get("nearest_w_percentile", 0.0) > W_REGION_PCT))
    obs_min = min(p.get("nearest_w_percentile", 0.0) for p in up) if up else None

    ci_lo, ci_hi = clopper_pearson(k, n)
    lower_1s = cp_lower(k, n)
    on_manifold_excluded = (
        max_rate_excluded_zero(n) if k == n else 1.0 - lower_1s
    )

    resolution: Dict[str, Any] = {"available": w_info is not None}
    if w_info is not None and w_info.get("n_w_loo"):
        n_loo = w_info["n_w_loo"]
        step = 100.0 / n_loo
        resolution.update(
            {
                "n_w_loo_samples": n_loo,
                "n_w_pooled_samples": w_info.get("n_w_pooled"),
                "percentile_basis": (
                    "w_percentile is an empirical mid-rank percentile against "
                    f"the artifact's W LOO distribution (n={n_loo}); it is NOT "
                    "a parametric tail probability."
                ),
                "granularity_pct_points": step,
                "max_resolvable_percentile_below_100": 100.0 * (n_loo - 0.5) / n_loo,
                "observed_min_nearest_w_percentile": obs_min,
                "observed_min_rank_interpretation": (
                    None if obs_min is None else
                    f"min observed {obs_min:.4f} => the AI distance exceeds "
                    f"~{obs_min * n_loo / 100.0:.1f} of {n_loo} W LOO values; "
                    "a value of 100.0 only certifies the distance exceeds all "
                    f"{n_loo} reference values, i.e. an exceedance probability "
                    f"<= 1/{n_loo + 1} (~{100.0 / (n_loo + 1):.2f}%) under "
                    "exchangeability, not literally zero."
                ),
            }
        )

    return {
        "claim": f"{k}/{n} unprompted samples off-manifold (nearest-author W-pct > {W_REGION_PCT:g})",
        "k": k,
        "n": n,
        "rate": k / n if n else None,
        "observed_min_nearest_w_percentile": obs_min,
        "clopper_pearson_95_two_sided": [ci_lo, ci_hi],
        "clopper_pearson_95_one_sided_lower": lower_1s,
        "max_on_manifold_rate_excluded_one_sided_95": on_manifold_excluded,
        "exact_test_vs_off_manifold_rate_le_90pct": {
            "null": "off-manifold rate <= 0.90",
            "p_value": binom_p(k, n, 0.90, alternative="greater"),
        },
        "w_percentile_resolution": resolution,
        "assumptions": [
            "Samples treated as independent across models and prompts "
            "(6 models x 6 prompts in the pilot); per-model clustering would "
            "widen the effective CI.",
            "The W-percentile inherits sampling noise from the finite W LOO "
            "reference sample; ranks, not tail probabilities, are the claim.",
        ],
    }


def section_model_medians(
    up: List[dict], seed: int, n_boot: int
) -> Dict[str, Any]:
    """Claim 3 — model proximity ordering on unprompted nearest distances."""
    from scipy.stats import mannwhitneyu

    by_model: Dict[str, List[float]] = {}
    for p in up:
        by_model.setdefault(p["model"], []).append(float(p["nearest_distance"]))

    models = sorted(by_model, key=lambda m: float(np.median(by_model[m])))
    medians = {}
    for i, m in enumerate(models):
        medians[m] = bootstrap_median_ci(
            by_model[m], n_boot=n_boot, seed=seed + i
        )

    pairs = []
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            a, b = models[i], models[j]
            res = mannwhitneyu(
                by_model[a], by_model[b], alternative="two-sided", method="exact"
            )
            pairs.append(
                {
                    "pair": f"{a} vs {b}",
                    "n_a": len(by_model[a]),
                    "n_b": len(by_model[b]),
                    "median_a": float(np.median(by_model[a])),
                    "median_b": float(np.median(by_model[b])),
                    "U": float(res.statistic),
                    "p_raw": float(res.pvalue),
                }
            )
    adj = holm_bonferroni([p["p_raw"] for p in pairs])
    for rec, a_p in zip(pairs, adj):
        rec["p_holm"] = a_p
        rec["significant_at_0.05_holm"] = a_p < 0.05

    import math

    n_per = sorted({len(v) for v in by_model.values()})
    min_possible_p = (
        2.0 / float(math.comb(n_per[0] * 2, n_per[0])) if n_per else None
    )

    return {
        "claim": "model proximity ordering (median unprompted nearest-author distance)",
        "order_by_median": models,
        "medians_bootstrap": medians,
        "pairwise_mann_whitney_holm": pairs,
        "n_pairs": len(pairs),
        "min_possible_exact_p_two_sided": min_possible_p,
        "assumptions": [
            "Exact Mann-Whitney U assumes independent samples within and "
            "between groups (prompts are shared across models, which induces "
            "positive correlation across groups; the test ignores this).",
            f"At n per group = {n_per}, the smallest achievable two-sided "
            f"exact p is {min_possible_p:.5f}" + (
                " — only complete separations can survive Holm across "
                "all pairs." if min_possible_p and min_possible_p * len(pairs) > 0.01 else "."
            ),
            "Bootstrap median CIs at n=6 are coarse (only 462 distinct "
            "resamples exist); treat them as descriptive ranges.",
        ],
        "interpretation": (
            "Pairs NOT significant after Holm cannot be ordered from these "
            "data; PRIMARY_ARTIFACT.md's 'intra-family order unresolved' "
            "note is the supported reading."
        ),
    }


def section_approach(sp: List[dict], up: List[dict], n_authors: int) -> Dict[str, Any]:
    """Claim 4 — style-prompted nearest-is-target above chance."""
    n = len(sp)
    k = int(sum(1 for p in sp if p.get("nearest_author") == p.get("style_target")))

    target_counts = Counter(p["style_target"] for p in sp)
    up_nearest_counts = Counter(p["nearest_author"] for p in up)

    p_design = 1.0 / n_authors
    p_empirical = empirical_match_null(dict(target_counts), dict(up_nearest_counts))

    ci_lo, ci_hi = clopper_pearson(k, n)

    return {
        "claim": f"{k}/{n} style-prompted samples have nearest_author == style_target",
        "k": k,
        "n": n,
        "rate": k / n,
        "clopper_pearson_95_two_sided": [ci_lo, ci_hi],
        "design_null": {
            "null": f"uniform random target among {n_authors} anchors (p0 = 1/{n_authors})",
            "p0": p_design,
            "p_value_one_sided_greater": binom_p(k, n, p_design, alternative="greater"),
        },
        "empirical_null": {
            "null": (
                "nearest author distributed as in the unprompted condition, "
                "targets fixed at the design multiset "
                f"({dict(sorted(target_counts.items()))}); "
                f"unprompted nearest counts {dict(sorted(up_nearest_counts.items()))}"
            ),
            "p0": p_empirical,
            "p_value_one_sided_greater": binom_p(k, n, p_empirical, alternative="greater"),
        },
        "assumptions": [
            "Binomial tests treat the 24 samples as independent; they share "
            "models and prompts (clustering ignored).",
            "The empirical null is the stronger (more conservative) one: it "
            "credits the prompted condition only for matches beyond what the "
            "models' baseline nearest-author preferences already produce.",
            "Targets that never appear as unprompted nearest authors (e.g. "
            "mccarthy-cormac) contribute 0 to the empirical p0, so prompted "
            "matches on those targets are pure signal under this null.",
        ],
    }


def section_manuscript(trajectory: Optional[dict]) -> Optional[Dict[str, Any]]:
    """Claim 5 — manuscript chapters closer to AI centroid than to nearest human."""
    if trajectory is None:
        return None
    summary = trajectory.get("summary", {})
    n = int(summary.get("n_chapters", 0))
    k = int(summary.get("n_closer_to_ai", 0))
    if n == 0:
        return None
    ci_lo, ci_hi = clopper_pearson(k, n)
    return {
        "claim": f"{k}/{n} manuscript chapters closer to the AI side than the human manifold",
        "k": k,
        "n": n,
        "rate": k / n,
        "median_ai_ratio": summary.get("median_ai_ratio"),
        "clopper_pearson_95_two_sided": [ci_lo, ci_hi],
        "binomial_vs_50pct": {
            "null": "P(chapter AI-closer) = 0.5 (knife-edge null)",
            "p_value_two_sided": binom_p(k, n, 0.5, alternative="two-sided"),
            "p_value_one_sided_greater": binom_p(k, n, 0.5, alternative="greater"),
        },
        "framing": "DESCRIPTIVE",
        "assumptions": [
            "Chapters are NOT independent draws: one author, one manuscript, "
            "one revision state. The binomial p-value is reported only as a "
            "calibration of the knife-edge null WITHIN this manuscript; it "
            "supports no inference across manuscripts or authors.",
            "Report the CP interval as the honest summary; do not enter this "
            "claim into the confirmatory family.",
        ],
    }


def build_registry(sections: Dict[str, Any]) -> Dict[str, Any]:
    """Claim 6 — one table of every tested claim with Holm-adjusted p-values."""
    rows: List[Dict[str, Any]] = []

    s1 = sections["enter_rate"]
    rows.append(
        {
            "id": "C1_enter_rate",
            "claim": s1["claim"],
            "estimate": f"{s1['k']}/{s1['n']}",
            "ci95": s1["clopper_pearson_95_two_sided"],
            "test": "exact binomial, H0: enter-rate >= 0.10 (one-sided)",
            "p_raw": s1["exact_tests_vs_alternatives"]["p0_0.1"]["p_value"],
            "family": "confirmatory",
            "in_holm": True,
        }
    )

    s2 = sections["off_manifold"]
    rows.append(
        {
            "id": "C2_off_manifold",
            "claim": s2["claim"],
            "estimate": f"{s2['k']}/{s2['n']}",
            "ci95": s2["clopper_pearson_95_two_sided"],
            "test": "exact binomial, H0: off-manifold rate <= 0.90 (one-sided)",
            "p_raw": s2["exact_test_vs_off_manifold_rate_le_90pct"]["p_value"],
            "family": "confirmatory",
            "in_holm": True,
        }
    )

    s4 = sections["approach"]
    rows.append(
        {
            "id": "C3_approach",
            "claim": s4["claim"],
            "estimate": f"{s4['k']}/{s4['n']}",
            "ci95": s4["clopper_pearson_95_two_sided"],
            "test": (
                "exact binomial vs empirical null p0="
                f"{s4['empirical_null']['p0']:.4f} (one-sided greater)"
            ),
            "p_raw": s4["empirical_null"]["p_value_one_sided_greater"],
            "family": "confirmatory",
            "in_holm": True,
            "sensitivity": {
                "design_null_p0": s4["design_null"]["p0"],
                "design_null_p": s4["design_null"]["p_value_one_sided_greater"],
            },
        }
    )

    s3 = sections["model_medians"]
    for pair in s3["pairwise_mann_whitney_holm"]:
        rows.append(
            {
                "id": f"C4_order_{pair['pair'].replace(' vs ', '__vs__')}",
                "claim": f"median ordering: {pair['pair']}",
                "estimate": f"{pair['median_a']:.3f} vs {pair['median_b']:.3f}",
                "ci95": None,
                "test": "exact Mann-Whitney U (two-sided)",
                "p_raw": pair["p_raw"],
                "family": "confirmatory",
                "in_holm": True,
            }
        )

    s5 = sections.get("manuscript")
    if s5 is not None:
        rows.append(
            {
                "id": "C5_manuscript_ai_closer",
                "claim": s5["claim"],
                "estimate": f"{s5['k']}/{s5['n']}",
                "ci95": s5["clopper_pearson_95_two_sided"],
                "test": "exact binomial vs 0.5 (two-sided) — DESCRIPTIVE only",
                "p_raw": s5["binomial_vs_50pct"]["p_value_two_sided"],
                "family": "descriptive",
                "in_holm": False,
            }
        )

    holm_idx = [i for i, r in enumerate(rows) if r["in_holm"]]
    adj = holm_bonferroni([rows[i]["p_raw"] for i in holm_idx])
    for i, a in zip(holm_idx, adj):
        rows[i]["p_holm"] = a
        rows[i]["significant_at_0.05_holm"] = a < 0.05
    for r in rows:
        if not r["in_holm"]:
            r["p_holm"] = None
            r["significant_at_0.05_holm"] = None

    return {
        "n_tests_in_holm_family": len(holm_idx),
        "note": (
            "Holm-Bonferroni applied across the full confirmatory family "
            f"({len(holm_idx)} tests: 3 headline claims + "
            f"{len(s3['pairwise_mann_whitney_holm'])} model pairs). The manuscript "
            "row is descriptive (non-independent chapters) and is excluded "
            "from the family; its raw p-value is shown for context only."
        ),
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def _fmt_p(p: Optional[float]) -> str:
    if p is None:
        return "—"
    if p < 1e-4:
        return f"{p:.2e}"
    return f"{p:.4f}"


def render_markdown(out: Dict[str, Any]) -> str:
    meta = out["meta"]
    s1, s2 = out["enter_rate"], out["off_manifold"]
    s3, s4 = out["model_medians"], out["approach"]
    s5, reg = out.get("manuscript"), out["registry"]

    lines = [
        "# Tier 1 statistical treatment (issue #95 P7)",
        "",
        f"- Generated: {meta['generated']}",
        f"- E4 results: `{meta['e4_results']}` (n placed = {meta['n_placed']}; "
        f"{meta['n_unprompted']} unprompted, {meta['n_style_prompted']} style-prompted, "
        f"{meta['n_models']} models, {meta['n_authors']} anchor authors)",
        f"- Artifact: `{meta['artifact'] or 'unresolved'}`",
        f"- Manuscript trajectory: `{meta['trajectory_results'] or 'not provided'}`",
        f"- Seed: {meta['seed']}; bootstrap resamples: {meta['n_boot']}; "
        f"permutations: {meta['n_perm']}",
        "",
        "All binomial intervals are exact Clopper-Pearson. All tests are exact "
        "(binomial / Mann-Whitney / hypergeometric); no normal approximations "
        "are used at these n's.",
        "",
        "## 1. Enter-rate claim",
        "",
        f"**{s1['claim']}.**",
        "",
        f"- Enter rate {s1['k']}/{s1['n']} = {s1['rate']:.3f}; CP 95% two-sided "
        f"[{s1['clopper_pearson_95_two_sided'][0]:.4f}, "
        f"{s1['clopper_pearson_95_two_sided'][1]:.4f}]; one-sided 95% upper "
        f"bound **{s1['clopper_pearson_95_one_sided_upper']:.4f}**.",
        f"- The data exclude (one-sided alpha = 0.05) any true enter-rate >= "
        f"**{s1['max_enter_rate_excluded_one_sided_95'] * 100:.1f}%**.",
        "",
        "| H0 (one-sided) | p-value | rejected at 0.05 |",
        "|---|---|---|",
    ]
    for key, alt in s1["exact_tests_vs_alternatives"].items():
        lines.append(
            f"| {alt['null']} | {_fmt_p(alt['p_value'])} | "
            f"{'yes' if alt['rejected_at_0.05'] else 'no'} |"
        )
    perm = s1["permutation_vs_unprompted_target_region"]
    lines += [
        "",
        f"- Permutation framing (prompted vs unprompted exchangeable w.r.t. "
        f"W-p90 region membership): pooled event count = "
        f"{perm['pooled_successes']}; exact hypergeometric p = "
        f"{_fmt_p(perm['p_exact_hypergeometric'])}, Monte Carlo p = "
        f"{_fmt_p(perm['p_monte_carlo'])} ({perm['n_perm']} perms, seed "
        f"{perm['seed']}).",
        f"- {s1['notes']}",
        "",
        "Assumptions: " + " ".join(s1["assumptions"]),
        "",
        "## 2. Off-manifold claim",
        "",
        f"**{s2['claim']}.**",
        "",
        f"- CP 95% two-sided [{s2['clopper_pearson_95_two_sided'][0]:.4f}, "
        f"{s2['clopper_pearson_95_two_sided'][1]:.4f}]; one-sided 95% lower "
        f"bound {s2['clopper_pearson_95_one_sided_lower']:.4f}.",
        f"- The data exclude any true ON-manifold rate >= "
        f"**{s2['max_on_manifold_rate_excluded_one_sided_95'] * 100:.1f}%** "
        "(one-sided alpha = 0.05).",
        f"- Exact test of H0 'off-manifold rate <= 0.90': p = "
        f"{_fmt_p(s2['exact_test_vs_off_manifold_rate_le_90pct']['p_value'])}.",
        "",
        "### W-percentile resolution (honest limits)",
        "",
    ]
    res = s2["w_percentile_resolution"]
    if res.get("available") and res.get("n_w_loo_samples"):
        lines += [
            f"- {res['percentile_basis']}",
            f"- Granularity: {res['granularity_pct_points']:.3f} percentile "
            f"points per rank; largest resolvable value below 100 is "
            f"{res['max_resolvable_percentile_below_100']:.2f}.",
            f"- {res['observed_min_rank_interpretation']}",
        ]
    else:
        lines.append("- Artifact not resolved; resolution limits not computed.")
    lines += [
        "",
        "Assumptions: " + " ".join(s2["assumptions"]),
        "",
        "## 3. Model proximity medians",
        "",
        "Median unprompted nearest-author distance with seeded percentile-"
        f"bootstrap 95% CIs ({meta['n_boot']} resamples):",
        "",
        "| model | n | median | bootstrap 95% CI |",
        "|---|---|---|---|",
    ]
    for m in s3["order_by_median"]:
        b = s3["medians_bootstrap"][m]
        lines.append(
            f"| {m} | {b['n']} | {b['median']:.4f} | "
            f"[{b['ci_lo']:.4f}, {b['ci_hi']:.4f}] |"
        )
    lines += [
        "",
        "Pairwise exact Mann-Whitney U, Holm-Bonferroni across "
        f"{s3['n_pairs']} pairs:",
        "",
        "| pair | medians | U | p raw | p Holm | sig (0.05) |",
        "|---|---|---|---|---|---|",
    ]
    for pair in sorted(s3["pairwise_mann_whitney_holm"], key=lambda r: r["p_raw"]):
        lines.append(
            f"| {pair['pair']} | {pair['median_a']:.3f} vs "
            f"{pair['median_b']:.3f} | {pair['U']:.0f} | "
            f"{_fmt_p(pair['p_raw'])} | {_fmt_p(pair['p_holm'])} | "
            f"{'YES' if pair['significant_at_0.05_holm'] else 'no'} |"
        )
    lines += [
        "",
        f"- Smallest achievable exact two-sided p at these group sizes: "
        f"{_fmt_p(s3['min_possible_exact_p_two_sided'])}.",
        f"- {s3['interpretation']}",
        "",
        "Assumptions: " + " ".join(s3["assumptions"]),
        "",
        "## 4. Approach claim (nearest-is-target)",
        "",
        f"**{s4['claim']}.**",
        "",
        f"- Rate {s4['k']}/{s4['n']} = {s4['rate']:.3f}; CP 95% "
        f"[{s4['clopper_pearson_95_two_sided'][0]:.4f}, "
        f"{s4['clopper_pearson_95_two_sided'][1]:.4f}].",
        f"- Design null (uniform over anchors): p0 = {s4['design_null']['p0']:.4f}, "
        f"one-sided p = {_fmt_p(s4['design_null']['p_value_one_sided_greater'])}.",
        f"- Empirical null (unprompted nearest-author distribution x design "
        f"target multiset): p0 = {s4['empirical_null']['p0']:.4f}, one-sided "
        f"p = {_fmt_p(s4['empirical_null']['p_value_one_sided_greater'])}.",
        "",
        "Assumptions: " + " ".join(s4["assumptions"]),
        "",
        "## 5. Manuscript AI-closer chapters",
        "",
    ]
    if s5 is not None:
        lines += [
            f"**{s5['claim']}** (median AI/human ratio "
            f"{s5['median_ai_ratio']}). FRAMING: {s5['framing']}.",
            "",
            f"- Rate {s5['k']}/{s5['n']} = {s5['rate']:.3f}; CP 95% "
            f"[{s5['clopper_pearson_95_two_sided'][0]:.4f}, "
            f"{s5['clopper_pearson_95_two_sided'][1]:.4f}].",
            f"- Binomial vs 0.5: two-sided p = "
            f"{_fmt_p(s5['binomial_vs_50pct']['p_value_two_sided'])}, "
            f"one-sided p = "
            f"{_fmt_p(s5['binomial_vs_50pct']['p_value_one_sided_greater'])}.",
            "",
            "Assumptions: " + " ".join(s5["assumptions"]),
        ]
    else:
        lines.append("Manuscript trajectory not provided; section skipped.")
    lines += [
        "",
        "## 6. Claim registry with Holm-Bonferroni adjustment",
        "",
        reg["note"],
        "",
        "| id | claim | estimate | 95% CI | test | p raw | p Holm | sig |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in reg["rows"]:
        ci = (
            f"[{r['ci95'][0]:.3f}, {r['ci95'][1]:.3f}]" if r["ci95"] else "—"
        )
        sig = (
            "YES" if r["significant_at_0.05_holm"]
            else ("no" if r["significant_at_0.05_holm"] is not None else "n/a")
        )
        lines.append(
            f"| {r['id']} | {r['claim']} | {r['estimate']} | {ci} | "
            f"{r['test']} | {_fmt_p(r['p_raw'])} | {_fmt_p(r.get('p_holm'))} | {sig} |"
        )
    lines += [
        "",
        "---",
        "Generated by tools/tier1_statistics.py — re-runnable "
        "on the scaled corpus via --e4-results / --trajectory / --artifact; all n's "
        "are auto-detected from the inputs.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(
    e4_path: Path,
    trajectory_path: Optional[Path],
    artifact_path: Optional[Path],
    out_dir: Path,
    seed: int,
    n_boot: int,
    n_perm: int,
) -> Dict[str, Any]:
    e4 = json.loads(e4_path.read_text(encoding="utf-8"))
    placements = e4.get("placements", [])
    up = [p for p in placements if p.get("condition") == "unprompted"]
    sp = [p for p in placements if p.get("condition") == "style_prompted"]
    if not up:
        raise ValueError(f"no unprompted placements found in {e4_path}")

    n_authors = len(up[0].get("per_author", {})) if up else 0

    if artifact_path is None:
        meta_art = (e4.get("meta") or {}).get("artifact")
        if meta_art:
            artifact_path = _resolve(meta_art, REPO_ROOT, e4_path.parent)
    w_info = None
    if artifact_path is not None and Path(artifact_path).exists():
        w_info = load_artifact_w_info(Path(artifact_path))
        if w_info["n_authors"] and n_authors and w_info["n_authors"] != n_authors:
            logger.warning(
                "artifact n_authors=%d != per_author entries=%d",
                w_info["n_authors"], n_authors,
            )
    else:
        logger.warning("artifact not resolved; W-percentile resolution limited")

    trajectory = None
    if trajectory_path is not None and trajectory_path.exists():
        trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
    elif trajectory_path is not None:
        logger.warning("Trajectory results not found at %s; skipping section 5",
                       trajectory_path)

    sections: Dict[str, Any] = {
        "enter_rate": section_enter_rate(sp, up, seed=seed, n_perm=n_perm),
        "off_manifold": section_off_manifold(up, w_info),
        "model_medians": section_model_medians(up, seed=seed, n_boot=n_boot),
        "approach": section_approach(sp, up, n_authors=n_authors),
        "manuscript": section_manuscript(trajectory),
    }
    registry = build_registry(sections)

    out: Dict[str, Any] = {
        "tool": "tier1_statistics",
        "relates": "issue #95 P7; TIER1_PAPER_OUTLINE.md §10",
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "e4_results": str(e4_path),
            "trajectory_results": str(trajectory_path) if trajectory is not None else None,
            "artifact": str(artifact_path) if w_info else None,
            "n_placed": len(placements),
            "n_unprompted": len(up),
            "n_style_prompted": len(sp),
            "n_models": len({p["model"] for p in placements}),
            "n_authors": n_authors,
            "w_info": w_info,
            "seed": seed,
            "n_boot": n_boot,
            "n_perm": n_perm,
        },
        **sections,
        "registry": registry,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "tier1_statistics.json"
    md_path = out_dir / "tier1_statistics.md"
    json_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(out), encoding="utf-8")
    logger.info("wrote %s and %s", json_path, md_path)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="P7: statistical treatment for Tier 1 paper claims"
    )
    parser.add_argument(
        "--e4-results", type=Path,
        default=REPO_ROOT / "reports/validation/wave2/e4_results.json",
        help="E4 placement results JSON (pilot or scaled corpus)",
    )
    parser.add_argument(
        "--trajectory", type=Path, default=None,
        help="Manuscript trajectory JSON (optional, not part of this "
             "release; section 5 skipped when not provided)",
    )
    parser.add_argument(
        "--artifact", type=Path, default=None,
        help="Author-space artifact (default: resolved from e4 meta.artifact)",
    )
    parser.add_argument(
        "--out-dir", type=Path, default=None,
        help="Output directory (default: directory of --e4-results)",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--n-boot", type=int, default=DEFAULT_N_BOOT)
    parser.add_argument("--n-perm", type=int, default=DEFAULT_N_PERM)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    out_dir = args.out_dir or args.e4_results.parent
    run(
        e4_path=args.e4_results,
        trajectory_path=args.trajectory,
        artifact_path=args.artifact,
        out_dir=out_dir,
        seed=args.seed,
        n_boot=args.n_boot,
        n_perm=args.n_perm,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
