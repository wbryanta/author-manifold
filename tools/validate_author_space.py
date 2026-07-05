#!/usr/bin/env python3
"""
Author-Relative Space Validation Harness (Phase 3: E1-E3)

Scientific go/no-go gate for the author-relative measurement space
(ADR-0041, forthcoming; issue #60). Before any placement of a new text is trusted,
these experiments must prove the D18++ dimensions and the pooled-normalized
space separate KNOWN authors on a calibration shelf.

Experiments:
    E1  Within- vs between-author separation. Leave-one-out work->own-centroid
        distances (within family) vs work->other-author-centroid distances
        (between family), pooled AUC + per-author silhouette coefficients.
        Gate: AUC >= 0.90 AND >= 80% of authors with silhouette > 0.
    E2  Leave-one-work-out attribution. Each work attributed by nearest
        centroid (own author's centroid rebuilt without the held-out work).
        Gate: top-1 accuracy >= 70% AND top-3 accuracy >= 85%.
        Also reports C_llr (descriptive) and a cosine-similarity-on-raw-
        vectors sanity check (NOT a gate).
    E3  Per-dimension discriminative validity at work level. One-way ANOVA
        F / eta-squared per dimension vs a seeded permutation null (1000
        label shuffles, per-dimension null p99), plus an ICC(1)-like ratio.
        Gate: >= 6 dimensions exceed their null p99. Emits
        "recommended_dimension_set_v2" for downstream use.
    E6  Window-length sensitivity (issue #60 criterion 3; documentation-only,
        NO gate; run explicitly via --experiments e6). Slices each work's
        body text into non-overlapping windows at {800, 1500, 3000} words,
        attributes each window by nearest author MFW centroid (LOO), and
        reports per-length top-1/top-3 accuracy plus the W/B distance
        distributions (medians + AUC). Needs body text (manifest offsets).

Outputs (under --output-dir):
    e1_results.json, e2_results.json, e3_results.json
        Machine-readable; each includes explicit "pass": true/false and
        "criteria" with thresholds + observed values.
    summary.md
        Combined PASS/FAIL gate table, per-author silhouettes, confusion
        matrix, ranked dimension table, plain-language interpretation.
    e6_results.json + e6_report.md
        Window-length sensitivity table + reading (only when e6 requested).

Exit codes: 0 = all selected gates pass; 3 = harness ran cleanly but at
least one gate failed (results still written); 2 = usage error (argparse);
1 = unexpected crash.

Usage:
    # Public-domain shelf (the run that ships with this release)
    python3 tools/validate_author_space.py \
        --baseline-dir data/pd_work_baselines \
        --manifest data/pd_manifest.yaml \
        --distance-variant mfw_delta \
        --output-dir reports/validation/pd_shelf_rerun

    # D18-only variant (no raw text needed)
    python3 tools/validate_author_space.py \
        --baseline-dir data/pd_work_baselines \
        --output-dir reports/validation/pd_shelf_d18

    # Distance-variant comparison (d18 / d18_weighted / mfw_delta / combined
    # with alpha sweep); writes variant_comparison.{md,json}
    python3 tools/validate_author_space.py \
        --manifest data/pd_manifest.yaml \
        --distance-variant all

Metric reuse: C_llr and ROC AUC come from
author_manifold.attribution_metrics.
"""

import sys
from pathlib import Path


def _ensure_repo_paths() -> Path:
    """Ensure the repo root and src/ are importable when run uninstalled."""
    repo_root = Path(__file__).resolve().parents[1]
    for path in (repo_root / "src", repo_root):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
    return repo_root


REPO_ROOT = _ensure_repo_paths()

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from author_manifold.attribution_metrics import compute_c_llr, compute_roc_auc
from author_manifold.author_space import (
    AuthorRelativeSpace,
    DIMENSION_SET_V1,
    MFW_DEFAULT_N,
    MFW_VOCAB_FILTERS,
    load_shelf,
    mfw_tokenize,
)

logger = logging.getLogger(__name__)

DEFAULT_BASELINE_DIR = "data/pd_work_baselines"
DEFAULT_OUTPUT_DIR = "reports/validation"
DEFAULT_SEED = 20260609
# Gated experiments (drive the exit code). E6 is documentation-only (issue
# #60 criterion 3): run only when explicitly requested via --experiments.
ALL_EXPERIMENTS = ("e1", "e2", "e3")
KNOWN_EXPERIMENTS = ALL_EXPERIMENTS + ("e6",)

# E6 window-length sensitivity defaults (issue #60 criterion 3).
E6_WINDOW_LENGTHS = (800, 1500, 3000)
E6_MAX_WINDOWS_PER_WORK = 5

# Distance variants compared by --distance-variant all (ADR-0041 amendment).
VARIANT_CHOICES = ("d18", "d18_weighted", "mfw_delta", "combined", "all")
COMBINED_ALPHAS = (0.3, 0.5, 0.7)
# Simplicity ranking for variant selection (lower = simpler / preferred when
# multiple variants pass the gates).
VARIANT_SIMPLICITY = {"d18": 0, "d18_weighted": 1, "mfw_delta": 2, "combined": 3}

# Gate thresholds (Phase 3 plan; ADR-0041 forthcoming).
E1_AUC_THRESHOLD = 0.90
E1_SILHOUETTE_FRACTION_THRESHOLD = 0.80
E2_TOP1_THRESHOLD = 0.70
E2_TOP3_THRESHOLD = 0.85
E3_MIN_SIGNIFICANT_DIMS = 6
E3_N_PERMUTATIONS = 1000


def _resolve(path_str: str) -> Path:
    """Resolve a path argument against cwd first, then repo root."""
    path = Path(path_str)
    if path.is_absolute() or path.exists():
        return path
    candidate = REPO_ROOT / path
    return candidate if candidate.exists() else path


def _criterion(threshold: float, observed: Optional[float], comparison: str = ">=") -> Dict[str, Any]:
    """One gate criterion: threshold, observed value, and its pass verdict."""
    if observed is None:
        ok = False
    elif comparison == ">=":
        ok = observed >= threshold
    elif comparison == "<=":
        ok = observed <= threshold
    else:
        raise ValueError(f"Unknown comparison: {comparison}")
    return {
        "threshold": threshold,
        "comparison": comparison,
        "observed": observed,
        "pass": ok,
    }


def _author_arrays(
    space: AuthorRelativeSpace,
) -> Tuple[List[str], Dict[str, np.ndarray]]:
    """Sorted calibrated author slugs and per-author normalized work matrices."""
    slugs = sorted(space.authors)
    vectors = {
        slug: np.vstack([w.vector for w in space.authors[slug].works]) for slug in slugs
    }
    return slugs, vectors


def _author_mfw_arrays(
    space: AuthorRelativeSpace, slugs: Sequence[str]
) -> Optional[Dict[str, np.ndarray]]:
    """Per-author MFW z-vector matrices, or None when the block is absent."""
    if space.mfw is None:
        return None
    out: Dict[str, np.ndarray] = {}
    for slug in slugs:
        works = space.authors[slug].works
        if any(w.mfw_z is None for w in works):
            return None
        out[slug] = np.vstack([w.mfw_z for w in works])
    return out


# =============================================================================
# Distance-variant specs (ADR-0041 amendment: MFW Burrows-Delta block)
# =============================================================================

@dataclass
class VariantSpec:
    """One distance variant to evaluate E1/E2 under.

    ``weights_sqrt`` is the per-dimension sqrt-weight vector for
    ``d18_weighted`` (weights normalized to mean 1 before sqrt, matching
    ``AuthorRelativeSpace``); ``scale`` is the d18/Delta blend scale for
    ``combined`` (``space.blend['scale']``).
    """

    label: str
    variant: str
    alpha: float = 0.5
    weights_sqrt: Optional[np.ndarray] = None
    scale: Optional[float] = None

    def distance(
        self,
        d18_a: np.ndarray,
        mfw_a: Optional[np.ndarray],
        d18_b: np.ndarray,
        mfw_b: Optional[np.ndarray],
    ) -> float:
        """Point distance under this variant (mirrors space.work_distance)."""
        if self.variant in ("d18", "d18_weighted"):
            delta = d18_a - d18_b
            if self.weights_sqrt is not None:
                delta = delta * self.weights_sqrt
            return float(np.linalg.norm(delta))
        if mfw_a is None or mfw_b is None:
            raise ValueError(f"Variant {self.variant!r} requires MFW z-vectors")
        delta_d = float(np.mean(np.abs(mfw_a - mfw_b)))
        if self.variant == "mfw_delta":
            return delta_d
        d18 = float(np.linalg.norm(d18_a - d18_b))
        return self.alpha * d18 + (1.0 - self.alpha) * float(self.scale) * delta_d


def _spec_from_space(space: AuthorRelativeSpace) -> VariantSpec:
    """VariantSpec matching the space's own active distance configuration."""
    weights_sqrt = None
    if space.distance_variant == "d18_weighted" and space.dimension_weights:
        w = np.array(
            [float(space.dimension_weights.get(d, 0.0)) for d in space.dimensions],
            dtype=float,
        )
        weights_sqrt = np.sqrt(w * (len(w) / w.sum()))
    return VariantSpec(
        label=space.distance_variant,
        variant=space.distance_variant,
        alpha=space.alpha,
        weights_sqrt=weights_sqrt,
        scale=(space.blend or {}).get("scale"),
    )


def _eta2_weights(
    space: AuthorRelativeSpace, e3_results_path: Optional[Path]
) -> Dict[str, float]:
    """Per-dimension eta-squared weights for d18_weighted.

    Loaded from a prior E3 run when available (the recorded gold-shelf
    numbers), otherwise recomputed via the same per-dimension ANOVA — the two
    are identical because eta^2 needs no permutation null.
    """
    if e3_results_path is not None and e3_results_path.is_file():
        payload = json.loads(e3_results_path.read_text(encoding="utf-8"))
        table = payload.get("dimension_table") or []
        weights = {
            row["dimension"]: float(row["eta_squared"])
            for row in table
            if row.get("dimension") in space.dimensions
        }
        if len(weights) == len(space.dimensions):
            logger.info("Loaded eta^2 weights from %s", e3_results_path)
            return weights
        logger.warning(
            "e3 results at %s cover %d/%d dims; recomputing eta^2",
            e3_results_path, len(weights), len(space.dimensions),
        )
    slugs, vec_by = _author_arrays(space)
    matrix = np.vstack([vec_by[s] for s in slugs])
    label_idx = np.concatenate(
        [np.full(vec_by[s].shape[0], i, dtype=int) for i, s in enumerate(slugs)]
    )
    _, eta_sq, _ = _anova_per_dimension(matrix, label_idx, len(slugs))
    return {dim: float(eta_sq[i]) for i, dim in enumerate(space.dimensions)}


# =============================================================================
# E1 — Within vs between author separation
# =============================================================================

def run_e1(
    space: AuthorRelativeSpace, spec: Optional[VariantSpec] = None
) -> Dict[str, Any]:
    """Within- vs between-author separation: pooled AUC + per-author silhouette.

    Within family: leave-one-out work -> own-author centroid (centroid of the
    author's OTHER works). Between family: work -> other-author full centroid.
    Both are work->centroid distances under the distance variant of ``spec``
    (default: the space's own active variant), mirroring the W "loo" /
    B "work_to_centroid" calibration families of the artifact.
    """
    from sklearn.metrics import silhouette_samples

    spec = spec or _spec_from_space(space)
    slugs, vec_by = _author_arrays(space)
    mfw_by = _author_mfw_arrays(space, slugs)
    if spec.variant in ("mfw_delta", "combined") and mfw_by is None:
        raise ValueError(
            f"Variant {spec.variant!r} needs the MFW block on the space "
            "(build with mfw_n=...)"
        )

    def _mfw(slug: str, i: Optional[int]) -> Optional[np.ndarray]:
        if mfw_by is None:
            return None
        return mfw_by[slug][i] if i is not None else mfw_by[slug].mean(axis=0)

    within: List[float] = []
    between: List[float] = []
    per_author: Dict[str, Dict[str, Any]] = {}
    within_by_author: Dict[str, List[float]] = {s: [] for s in slugs}
    between_by_author: Dict[str, List[float]] = {s: [] for s in slugs}

    for slug in slugs:
        vectors = vec_by[slug]
        n = vectors.shape[0]
        total = vectors.sum(axis=0)
        mfw_total = mfw_by[slug].sum(axis=0) if mfw_by is not None else None
        for i in range(n):
            if n >= 2:
                loo_centroid = (total - vectors[i]) / (n - 1)
                loo_mfw = (
                    (mfw_total - mfw_by[slug][i]) / (n - 1)
                    if mfw_by is not None else None
                )
                d = spec.distance(vectors[i], _mfw(slug, i), loo_centroid, loo_mfw)
                within.append(d)
                within_by_author[slug].append(d)
            for other in slugs:
                if other == slug:
                    continue
                d = spec.distance(
                    vectors[i], _mfw(slug, i),
                    space.authors[other].centroid, _mfw(other, None),
                )
                between.append(d)
                between_by_author[slug].append(d)

    # Pooled AUC: within distances should be SMALLER, so score = -distance
    # with within as the positive class.
    y_true = [1] * len(within) + [0] * len(between)
    y_scores = [-d for d in within] + [-d for d in between]
    auc = compute_roc_auc(y_true, y_scores)

    # Per-author silhouette over all works (author labels). The d18 variant
    # keeps the original euclidean-on-vectors path (exact reproduction of the
    # recorded baseline numbers); other variants use the precomputed pairwise
    # work-work distance matrix under the variant.
    matrix = np.vstack([vec_by[s] for s in slugs])
    labels = np.concatenate([np.full(vec_by[s].shape[0], i) for i, s in enumerate(slugs)])
    if spec.variant == "d18":
        sil = silhouette_samples(matrix, labels, metric="euclidean")
    else:
        flat: List[Tuple[str, int]] = [
            (s, i) for s in slugs for i in range(vec_by[s].shape[0])
        ]
        n_all = len(flat)
        pairwise = np.zeros((n_all, n_all))
        for a in range(n_all):
            slug_a, i_a = flat[a]
            for b in range(a + 1, n_all):
                slug_b, i_b = flat[b]
                d = spec.distance(
                    vec_by[slug_a][i_a], _mfw(slug_a, i_a),
                    vec_by[slug_b][i_b], _mfw(slug_b, i_b),
                )
                pairwise[a, b] = pairwise[b, a] = d
        sil = silhouette_samples(pairwise, labels, metric="precomputed")
    n_positive = 0
    for i, slug in enumerate(slugs):
        sil_mean = float(np.mean(sil[labels == i]))
        if sil_mean > 0:
            n_positive += 1
        per_author[slug] = {
            "n_works": int(vec_by[slug].shape[0]),
            "silhouette": sil_mean,
            "within_median": float(np.median(within_by_author[slug]))
            if within_by_author[slug] else None,
            "between_median": float(np.median(between_by_author[slug])),
        }
    silhouette_fraction = n_positive / len(slugs) if slugs else 0.0

    criteria = {
        "pooled_auc": _criterion(E1_AUC_THRESHOLD, float(auc) if auc is not None else None),
        "silhouette_positive_fraction": _criterion(
            E1_SILHOUETTE_FRACTION_THRESHOLD, silhouette_fraction
        ),
    }
    return {
        "experiment": "e1",
        "name": "Within vs between author separation",
        "distance_variant": spec.label,
        "pass": all(c["pass"] for c in criteria.values()),
        "criteria": criteria,
        "n_within": len(within),
        "n_between": len(between),
        "within_median": float(np.median(within)) if within else None,
        "between_median": float(np.median(between)) if between else None,
        "per_author": per_author,
        "n_authors_silhouette_positive": n_positive,
        "n_authors": len(slugs),
    }


# =============================================================================
# E2 — Leave-one-work-out attribution
# =============================================================================

def _softmin_posteriors(distances: Sequence[float]) -> np.ndarray:
    """Posterior-like scores from distances: softmax(-d) over candidates."""
    z = -np.asarray(distances, dtype=float)
    z -= z.max()
    exp = np.exp(z)
    return exp / exp.sum()


def run_e2(
    space: AuthorRelativeSpace, spec: Optional[VariantSpec] = None
) -> Dict[str, Any]:
    """Leave-one-work-out nearest-centroid attribution.

    Primary method: nearest centroid under the distance variant of ``spec``
    (default: the space's own active variant; plain pooled euclidean for
    ``d18``). The held-out work's own author centroid is rebuilt without it;
    authors must keep >= 2 works in their LOO centroid (so only authors with
    >= 3 works contribute held-out trials, all authors remain candidates).

    Sanity check (NOT a gate; d18 variant only): cosine similarity on
    UNNORMALIZED raw vectors (shelf-mean-imputed) against the same LOO
    centroids. This is deliberately a different geometry; agreement indicates
    the primary result is not an artifact of the pooled normalization.

    C_llr is descriptive only: distances are converted to posterior-like
    scores via softmax(-d), target = true author's posterior per trial.
    """
    spec = spec or _spec_from_space(space)
    slugs, vec_by = _author_arrays(space)
    mfw_by = _author_mfw_arrays(space, slugs)
    if spec.variant in ("mfw_delta", "combined") and mfw_by is None:
        raise ValueError(
            f"Variant {spec.variant!r} needs the MFW block on the space "
            "(build with mfw_n=...)"
        )
    centroids = {slug: space.authors[slug].centroid for slug in slugs}
    mfw_centroids = (
        {slug: mfw_by[slug].mean(axis=0) for slug in slugs}
        if mfw_by is not None else {slug: None for slug in slugs}
    )
    run_sanity = spec.variant == "d18"
    # Raw-space (unnormalized, imputed) vectors and centroids for the sanity
    # method. Mean commutes with the affine de-normalization, so raw centroids
    # are exactly de-normalized normalized centroids.
    raw_by = {s: vec_by[s] * space.shelf_std + space.shelf_mean for s in slugs}
    raw_centroids = {s: centroids[s] * space.shelf_std + space.shelf_mean for s in slugs}

    confusion: Dict[str, Dict[str, int]] = {s: {} for s in slugs}
    per_author: Dict[str, Dict[str, Any]] = {}
    target_scores: List[float] = []
    non_target_scores: List[float] = []
    n_trials = n_top1 = n_top3 = n_sanity_top1 = 0
    skipped_authors: List[str] = []

    for slug in slugs:
        vectors = vec_by[slug]
        n = vectors.shape[0]
        if n < 3:
            skipped_authors.append(slug)
            logger.info("E2: skipping %s (only %d works; LOO centroid would drop below 2)", slug, n)
            continue
        total = vectors.sum(axis=0)
        mfw_total = mfw_by[slug].sum(axis=0) if mfw_by is not None else None
        raw_total = raw_by[slug].sum(axis=0)
        a_top1 = a_top3 = 0
        for i in range(n):
            held = vectors[i]
            held_mfw = mfw_by[slug][i] if mfw_by is not None else None
            distances = []
            for other in slugs:
                if other == slug:
                    centroid = (total - held) / (n - 1)
                    mfw_centroid = (
                        (mfw_total - held_mfw) / (n - 1)
                        if mfw_by is not None else None
                    )
                else:
                    centroid = centroids[other]
                    mfw_centroid = mfw_centroids[other]
                distances.append(spec.distance(held, held_mfw, centroid, mfw_centroid))
            order = np.argsort(distances)
            ranked = [slugs[j] for j in order]
            predicted = ranked[0]

            n_trials += 1
            if predicted == slug:
                n_top1 += 1
                a_top1 += 1
            if slug in ranked[:3]:
                n_top3 += 1
                a_top3 += 1
            confusion[slug][predicted] = confusion[slug].get(predicted, 0) + 1

            posteriors = _softmin_posteriors(distances)
            for j, other in enumerate(slugs):
                if other == slug:
                    target_scores.append(float(posteriors[j]))
                else:
                    non_target_scores.append(float(posteriors[j]))

            # Sanity method: cosine on raw vectors, same LOO protocol
            # (d18 variant only — it cross-checks the pooled normalization).
            if run_sanity:
                raw_held = raw_by[slug][i]
                sims = []
                for other in slugs:
                    raw_centroid = (
                        (raw_total - raw_held) / (n - 1) if other == slug
                        else raw_centroids[other]
                    )
                    denom = np.linalg.norm(raw_held) * np.linalg.norm(raw_centroid)
                    sims.append(float(raw_held @ raw_centroid / denom) if denom > 0 else 0.0)
                if slugs[int(np.argmax(sims))] == slug:
                    n_sanity_top1 += 1

        per_author[slug] = {
            "n_works": n,
            "top1_accuracy": a_top1 / n,
            "top3_accuracy": a_top3 / n,
        }

    top1 = n_top1 / n_trials if n_trials else 0.0
    top3 = n_top3 / n_trials if n_trials else 0.0
    c_llr, c_llr_min = compute_c_llr(target_scores, non_target_scores)

    if run_sanity:
        sanity_check: Dict[str, Any] = {
            "method": "cosine similarity on unnormalized raw vectors (LOO centroids)",
            "top1_accuracy": n_sanity_top1 / n_trials if n_trials else 0.0,
            "note": "Sanity cross-check only; NOT a gate.",
        }
    else:
        sanity_check = {
            "method": None,
            "top1_accuracy": None,
            "note": f"Sanity cross-check only run for the d18 variant; "
                    f"NOT a gate (variant: {spec.label}).",
        }

    criteria = {
        "top1_accuracy": _criterion(E2_TOP1_THRESHOLD, top1),
        "top3_accuracy": _criterion(E2_TOP3_THRESHOLD, top3),
    }
    return {
        "experiment": "e2",
        "name": "Leave-one-work-out attribution",
        "distance_variant": spec.label,
        "pass": all(c["pass"] for c in criteria.values()),
        "criteria": criteria,
        "n_trials": n_trials,
        "n_candidate_authors": len(slugs),
        "skipped_authors": skipped_authors,
        "per_author": per_author,
        "confusion_matrix": confusion,
        "c_llr": {
            "value": c_llr,
            "min": c_llr_min,
            "note": "Descriptive only (softmax(-distance) posteriors); not a gate.",
        },
        "sanity_check": sanity_check,
    }


# =============================================================================
# E3 — Per-dimension discriminative validity
# =============================================================================

def _anova_per_dimension(
    matrix: np.ndarray, label_idx: np.ndarray, n_groups: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-column one-way ANOVA. Returns (F, eta_squared, ss_within)."""
    n, _ = matrix.shape
    grand = matrix.mean(axis=0)
    ss_total = ((matrix - grand) ** 2).sum(axis=0)
    ss_between = np.zeros_like(grand)
    for g in range(n_groups):
        group = matrix[label_idx == g]
        ss_between += group.shape[0] * (group.mean(axis=0) - grand) ** 2
    ss_within = ss_total - ss_between
    df_between = n_groups - 1
    df_within = n - n_groups
    with np.errstate(divide="ignore", invalid="ignore"):
        f_stat = (ss_between / df_between) / np.where(
            ss_within > 0, ss_within / df_within, np.nan
        )
        eta_sq = np.where(ss_total > 0, ss_between / ss_total, 0.0)
    return f_stat, eta_sq, ss_within


def run_e3(
    space: AuthorRelativeSpace,
    seed: int = DEFAULT_SEED,
    n_permutations: int = E3_N_PERMUTATIONS,
) -> Dict[str, Any]:
    """Per-dimension discriminative validity at WORK level.

    For each dimension: one-way ANOVA F and eta-squared across authors, a
    seeded permutation null (label shuffles preserve cross-dimension
    correlation) giving each dimension's null p99 of eta-squared, and an
    ICC(1)-like ratio (between-author variance component / total, with the
    unbalanced-design k0 correction). Dimensions whose observed eta-squared
    exceeds their own null p99 are flagged and emitted as
    recommended_dimension_set_v2.

    Eta-squared is invariant to per-dimension affine transforms, so running
    on pooled-normalized vectors equals running on raw values (with
    shelf-mean imputation for missing entries — conservative, biases toward
    the null).
    """
    slugs, vec_by = _author_arrays(space)
    matrix = np.vstack([vec_by[s] for s in slugs])
    label_idx = np.concatenate(
        [np.full(vec_by[s].shape[0], i, dtype=int) for i, s in enumerate(slugs)]
    )
    n, n_dims = matrix.shape
    k = len(slugs)
    dims = list(space.dimensions)

    f_obs, eta_obs, ss_within = _anova_per_dimension(matrix, label_idx, k)

    # ICC(1)-like: between-author variance component over total.
    counts = np.array([vec_by[s].shape[0] for s in slugs], dtype=float)
    k0 = (n - (counts ** 2).sum() / n) / (k - 1)
    ms_within = ss_within / (n - k)
    grand = matrix.mean(axis=0)
    ss_total = ((matrix - grand) ** 2).sum(axis=0)
    ms_between = (ss_total - ss_within) / (k - 1)
    sigma_between = np.maximum((ms_between - ms_within) / k0, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        icc = np.where(
            sigma_between + ms_within > 0,
            sigma_between / (sigma_between + ms_within),
            0.0,
        )

    # Permutation null: shuffle author labels, recompute eta-squared.
    rng = np.random.default_rng(seed)
    null_eta = np.empty((n_permutations, n_dims), dtype=float)
    for p in range(n_permutations):
        permuted = rng.permutation(label_idx)
        _, null_eta[p], _ = _anova_per_dimension(matrix, permuted, k)
    null_p99 = np.percentile(null_eta, 99, axis=0)
    perm_p = (1 + (null_eta >= eta_obs).sum(axis=0)) / (1 + n_permutations)
    exceeds = eta_obs > null_p99

    order = np.argsort(-eta_obs)
    dimension_table = [
        {
            "dimension": dims[i],
            "rank": rank + 1,
            "f_statistic": float(f_obs[i]) if np.isfinite(f_obs[i]) else None,
            "eta_squared": float(eta_obs[i]),
            "null_p99_eta_squared": float(null_p99[i]),
            "permutation_p": float(perm_p[i]),
            "icc_like": float(icc[i]),
            "exceeds_null_p99": bool(exceeds[i]),
        }
        for rank, i in enumerate(order)
    ]
    recommended = [dims[i] for i in order if exceeds[i]]
    n_significant = int(exceeds.sum())

    criteria = {
        "n_dimensions_exceeding_null_p99": _criterion(
            E3_MIN_SIGNIFICANT_DIMS, n_significant
        ),
    }
    return {
        "experiment": "e3",
        "name": "Per-dimension discriminative validity",
        "pass": all(c["pass"] for c in criteria.values()),
        "criteria": criteria,
        "n_works": int(n),
        "n_authors": k,
        "n_dimensions": n_dims,
        "n_permutations": n_permutations,
        "seed": seed,
        "dimension_table": dimension_table,
        "recommended_dimension_set_v2": recommended,
    }


# =============================================================================
# E6 — Window-length sensitivity (issue #60 criterion 3; documentation-only)
# =============================================================================

def _resolve_text_file(path_str: str) -> Optional[Path]:
    """Resolve a work's text_path: absolute, cwd-relative, or repo-root-relative."""
    path = Path(path_str)
    if path.is_file():
        return path
    candidate = REPO_ROOT / path
    return candidate if candidate.is_file() else None


def _work_body_tokens(work) -> Optional[List[str]]:
    """MFW tokens of a work's body text (body_text override or manifest slice)."""
    if work.body_text is not None:
        return mfw_tokenize(work.body_text)
    if not work.text_path:
        return None
    path = _resolve_text_file(work.text_path)
    if path is None:
        return None
    text = path.read_text(encoding="utf-8")
    start = work.body_start or 0
    end = work.body_end if work.body_end is not None else len(text)
    return mfw_tokenize(text[start:end])


def _dist_block(samples: Sequence[float]) -> Dict[str, Any]:
    arr = np.asarray(samples, dtype=float)
    return {
        "n": int(arr.size),
        "median": float(np.median(arr)) if arr.size else None,
        "p25": float(np.percentile(arr, 25)) if arr.size else None,
        "p75": float(np.percentile(arr, 75)) if arr.size else None,
    }


def run_e6(
    space: AuthorRelativeSpace,
    seed: int = DEFAULT_SEED,
    window_lengths: Sequence[int] = E6_WINDOW_LENGTHS,
    max_windows_per_work: int = E6_MAX_WINDOWS_PER_WORK,
) -> Dict[str, Any]:
    """Window-length sensitivity of the W/B separations (MFW block).

    For each window length L, each calibrated work's body text is sliced into
    non-overlapping L-word windows (MFW tokenizer convention; trailing
    partial window dropped), up to ``max_windows_per_work`` windows sampled
    per work (seeded, without replacement). Each window is featurized against
    the space's MFW vocabulary norm and attributed by nearest author MFW
    centroid under Burrows Delta, leave-one-out: the window's own work is
    excluded from its author's centroid (other authors use their full
    centroids).

    Per length: top-1 / top-3 attribution accuracy, the within distribution
    (window -> own-author LOO centroid), the between distribution (window ->
    other-author centroids), their medians, and the pooled W-vs-B AUC. A
    ``full`` reference row repeats the protocol on whole-work z-vectors.

    NO pass/fail gate (issue #60 criterion 3 asks for documentation): the
    question is how W/B separation degrades with window length and at what
    length attribution becomes unreliable. ``pass`` is always True so this
    experiment never trips the harness exit code.
    """
    if space.mfw is None:
        raise ValueError("E6 requires the MFW block (build the space with mfw_n=...)")
    slugs = sorted(space.authors)
    rng = np.random.default_rng(seed)

    mfw_by: Dict[str, np.ndarray] = {}
    for slug in slugs:
        works = space.authors[slug].works
        if any(w.mfw_z is None for w in works):
            raise ValueError(f"E6: author {slug} has works without MFW z-vectors")
        mfw_by[slug] = np.vstack([w.mfw_z for w in works])
    centroids = {slug: mfw_by[slug].mean(axis=0) for slug in slugs}

    # Body tokens per (slug, work index); works without resolvable text are
    # recorded and skipped.
    tokens_by: Dict[Tuple[str, int], List[str]] = {}
    skipped_works: List[str] = []
    for slug in slugs:
        for idx, work in enumerate(space.authors[slug].works):
            tokens = _work_body_tokens(work)
            if not tokens:
                skipped_works.append(f"{slug}/{work.title}")
                continue
            tokens_by[(slug, idx)] = tokens

    def attribute(z: np.ndarray, slug: str, loo_centroid: np.ndarray) -> Tuple[List[str], List[float]]:
        """Ranked authors + per-author Delta distances for one observation."""
        dists = [
            float(np.mean(np.abs(z - (loo_centroid if other == slug else centroids[other]))))
            for other in slugs
        ]
        order = np.argsort(dists)
        return [slugs[j] for j in order], dists

    def summarize(
        label: Any, within: List[float], between: List[float],
        top1: int, top3: int, trials: int, n_works: int,
    ) -> Dict[str, Any]:
        auc = None
        if within and between:
            auc = compute_roc_auc(
                [1] * len(within) + [0] * len(between),
                [-d for d in within] + [-d for d in between],
            )
        w_med = float(np.median(within)) if within else None
        b_med = float(np.median(between)) if between else None
        return {
            "window_words": label,
            "n_works": n_works,
            "n_windows": trials,
            "top1_accuracy": top1 / trials if trials else None,
            "top3_accuracy": top3 / trials if trials else None,
            "within": _dist_block(within),
            "between": _dist_block(between),
            "wb_median_ratio": (b_med / w_med) if (w_med and b_med) else None,
            "auc": float(auc) if auc is not None else None,
        }

    per_length: List[Dict[str, Any]] = []
    for length in window_lengths:
        within: List[float] = []
        between: List[float] = []
        top1 = top3 = trials = 0
        n_works_used = 0
        for (slug, idx) in sorted(tokens_by):
            tokens = tokens_by[(slug, idx)]
            author_matrix = mfw_by[slug]
            n_works = author_matrix.shape[0]
            if n_works < 2:
                continue  # no LOO centroid possible
            n_windows = len(tokens) // length
            if n_windows == 0:
                continue
            chosen = np.arange(n_windows)
            if n_windows > max_windows_per_work:
                chosen = np.sort(
                    rng.choice(n_windows, size=max_windows_per_work, replace=False)
                )
            n_works_used += 1
            loo_centroid = (
                author_matrix.sum(axis=0) - author_matrix[idx]
            ) / (n_works - 1)
            for w_i in chosen:
                chunk = tokens[w_i * length:(w_i + 1) * length]
                z = space.mfw.featurize_tokens(chunk)
                ranked, dists = attribute(z, slug, loo_centroid)
                trials += 1
                if ranked[0] == slug:
                    top1 += 1
                if slug in ranked[:3]:
                    top3 += 1
                own = dists[slugs.index(slug)]
                within.append(own)
                between.extend(
                    d for j, d in enumerate(dists) if slugs[j] != slug
                )
        per_length.append(
            summarize(int(length), within, between, top1, top3, trials, n_works_used)
        )

    # Full-work reference row (same LOO protocol on whole-work z-vectors).
    within_f: List[float] = []
    between_f: List[float] = []
    top1_f = top3_f = trials_f = 0
    n_works_f = 0
    for slug in slugs:
        author_matrix = mfw_by[slug]
        n_works = author_matrix.shape[0]
        if n_works < 2:
            continue
        total = author_matrix.sum(axis=0)
        for idx in range(n_works):
            loo_centroid = (total - author_matrix[idx]) / (n_works - 1)
            ranked, dists = attribute(author_matrix[idx], slug, loo_centroid)
            trials_f += 1
            n_works_f += 1
            if ranked[0] == slug:
                top1_f += 1
            if slug in ranked[:3]:
                top3_f += 1
            within_f.append(dists[slugs.index(slug)])
            between_f.extend(d for j, d in enumerate(dists) if slugs[j] != slug)
    full_row = summarize(
        "full", within_f, between_f, top1_f, top3_f, trials_f, n_works_f
    )

    return {
        "experiment": "e6",
        "name": "Window-length sensitivity of W/B separations (MFW block)",
        "gate": None,
        "pass": True,   # documentation-only: never trips the harness exit code
        "criteria": {},
        "seed": seed,
        "max_windows_per_work": max_windows_per_work,
        "window_lengths": [int(v) for v in window_lengths],
        "n_authors": len(slugs),
        "n_works_with_text": len(tokens_by),
        "skipped_works": skipped_works,
        "mfw_n": space.mfw.n_mfw,
        "per_length": per_length,
        "full_work_reference": full_row,
    }


def build_e6_markdown(result: Dict[str, Any], meta: Dict[str, Any]) -> str:
    """E6 report: per-length table + plain-language degradation reading."""
    rows = list(result["per_length"]) + [result["full_work_reference"]]
    lines = [
        "# E6 — Window-Length Sensitivity (issue #60 criterion 3)",
        "",
        f"- Generated: {meta.get('generated')}",
        f"- Baseline dir: {meta.get('baseline_dir')}",
        f"- Manifest: {meta.get('manifest') or 'none'}",
        f"- Authors: {result['n_authors']} calibrated; "
        f"{result['n_works_with_text']} works with body text; seed {result['seed']}",
        f"- MFW block: top-{result['mfw_n']} shelf words, Burrows Delta; "
        f"up to {result['max_windows_per_work']} non-overlapping windows "
        "sampled per work; attribution = nearest author MFW centroid "
        "(leave-one-out: own work excluded from own-author centroid).",
        "",
        "**No pass/fail gate** — this experiment documents how within/between "
        "separation degrades as the measured text gets shorter, and at what "
        "length attribution becomes unreliable.",
        "",
        "| Window (words) | Windows | Top-1 | Top-3 | W median | B median "
        "| B/W ratio | AUC |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['window_words']} | {row['n_windows']} "
            f"| {_fmt(row['top1_accuracy'], '.1%')} "
            f"| {_fmt(row['top3_accuracy'], '.1%')} "
            f"| {_fmt(row['within']['median'])} "
            f"| {_fmt(row['between']['median'])} "
            f"| {_fmt(row['wb_median_ratio'], '.2f')} "
            f"| {_fmt(row['auc'])} |"
        )
    if result["skipped_works"]:
        lines += [
            "",
            f"Skipped (no resolvable body text): "
            f"{', '.join(result['skipped_works'])}",
        ]
    # Plain-language reading: where does top-1 drop below the E2 gate level?
    unreliable = [
        row for row in result["per_length"]
        if row["top1_accuracy"] is not None and row["top1_accuracy"] < E2_TOP1_THRESHOLD
    ]
    sorted_lengths = sorted(
        (row for row in result["per_length"] if row["top1_accuracy"] is not None),
        key=lambda r: r["window_words"],
    )
    lines += ["", "## Reading", ""]
    if sorted_lengths:
        shortest, longest = sorted_lengths[0], sorted_lengths[-1]
        lines.append(
            f"As windows shrink from full works to {shortest['window_words']} "
            f"words, top-1 attribution moves from "
            f"{_fmt(result['full_work_reference']['top1_accuracy'], '.1%')} (full) "
            f"to {_fmt(longest['top1_accuracy'], '.1%')} at "
            f"{longest['window_words']}w and "
            f"{_fmt(shortest['top1_accuracy'], '.1%')} at "
            f"{shortest['window_words']}w; W-vs-B AUC moves from "
            f"{_fmt(result['full_work_reference']['auc'])} to "
            f"{_fmt(shortest['auc'])}. The within-author median rises as "
            "windows shorten (small-sample noise inflates every distance) "
            "while the between-author median rises more slowly, compressing "
            "the B/W separation ratio."
        )
        if unreliable:
            bad = ", ".join(f"{row['window_words']}w" for row in unreliable)
            lines.append(
                f"Attribution falls below the E2 top-1 gate level "
                f"({E2_TOP1_THRESHOLD:.0%}) at: {bad}. W/B percentile "
                "statements at these window lengths should carry an explicit "
                "short-text caveat."
            )
        else:
            lines.append(
                f"Top-1 stays at or above the E2 gate level "
                f"({E2_TOP1_THRESHOLD:.0%}) at every tested window length; "
                "within the tested range, length mainly costs separation "
                "margin (B/W ratio), not attribution reliability."
            )
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# Variant comparison (--distance-variant all)
# =============================================================================

def build_variant_specs(
    space: AuthorRelativeSpace,
    eta2: Dict[str, float],
    alphas: Sequence[float] = COMBINED_ALPHAS,
) -> List[VariantSpec]:
    """The comparison roster: d18, d18_weighted, mfw_delta, combined@alphas."""
    w = np.array([float(eta2.get(d, 0.0)) for d in space.dimensions], dtype=float)
    weights_sqrt = np.sqrt(w * (len(w) / w.sum()))
    scale = (space.blend or {}).get("scale")
    specs = [
        VariantSpec("d18", "d18"),
        VariantSpec("d18_weighted", "d18_weighted", weights_sqrt=weights_sqrt),
    ]
    if space.mfw is not None and scale is not None:
        specs.append(VariantSpec("mfw_delta", "mfw_delta"))
        specs += [
            VariantSpec(f"combined_alpha{a:g}", "combined", alpha=a, scale=scale)
            for a in alphas
        ]
    else:
        logger.warning("MFW block absent: comparing d18 variants only")
    return specs


def _select_variant(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Pick the winning variant from comparison rows.

    Rule (documented in the report): prefer the SIMPLEST variant that passes
    all four E1/E2 gates (simplicity order d18 < d18_weighted < mfw_delta <
    combined; among passing combined alphas, best top-1 then AUC). When both
    mfw_delta and a combined alpha pass, combined is chosen only if it
    clearly beats mfw_delta: better-or-equal on at least 3 of the 4 gate
    metrics AND top-1 at least 2 points higher. If nothing passes, report the
    best by (top-1, AUC) with selected=None.
    """
    def metrics(row: Dict[str, Any]) -> Tuple[float, float, float, float]:
        return (row["e1_auc"], row["silhouette_fraction"], row["top1"], row["top3"])

    passing = [r for r in rows if r["all_pass"]]
    best_overall = max(rows, key=lambda r: (r["top1"], r["e1_auc"]))
    if not passing:
        return {
            "selected": None,
            "best_failing": best_overall["label"],
            "reason": "No variant passes all gates; best by top-1/AUC reported.",
        }

    # Collapse combined alphas to the best passing one.
    combined_pass = [r for r in passing if r["variant"] == "combined"]
    best_combined = (
        max(combined_pass, key=lambda r: (r["top1"], r["e1_auc"]))
        if combined_pass else None
    )
    candidates = [r for r in passing if r["variant"] != "combined"]
    if best_combined is not None:
        candidates.append(best_combined)
    candidates.sort(key=lambda r: VARIANT_SIMPLICITY[r["variant"]])
    selected = candidates[0]
    reason = f"Simplest variant passing all gates: {selected['label']}."

    mfw_row = next((r for r in candidates if r["variant"] == "mfw_delta"), None)
    if (
        selected["variant"] == "mfw_delta"
        and best_combined is not None
        and mfw_row is not None
    ):
        wins = sum(
            c >= m for c, m in zip(metrics(best_combined), metrics(mfw_row))
        )
        if wins >= 3 and best_combined["top1"] >= mfw_row["top1"] + 0.02:
            selected = best_combined
            reason = (
                f"mfw_delta passes, but {best_combined['label']} clearly beats "
                f"it ({wins}/4 gate metrics better-or-equal, top-1 "
                f"+{best_combined['top1'] - mfw_row['top1']:.1%}); preferring "
                "combined for robustness."
            )
        elif selected["variant"] == "mfw_delta":
            reason = (
                "mfw_delta is the simplest passing variant; combined does not "
                "clearly beat it, so the simpler model wins."
            )
    return {"selected": selected["label"], "reason": reason}


def run_variant_comparison(
    space: AuthorRelativeSpace,
    eta2: Dict[str, float],
    alphas: Sequence[float] = COMBINED_ALPHAS,
) -> Dict[str, Any]:
    """E1+E2 under every distance variant; gate verdicts + selection."""
    specs = build_variant_specs(space, eta2, alphas)
    rows: List[Dict[str, Any]] = []
    full: Dict[str, Dict[str, Any]] = {}
    for spec in specs:
        logger.info("Variant %s: running E1+E2 ...", spec.label)
        e1 = run_e1(space, spec)
        e2 = run_e2(space, spec)
        full[spec.label] = {"e1": e1, "e2": e2}
        c1, c2 = e1["criteria"], e2["criteria"]
        row = {
            "label": spec.label,
            "variant": spec.variant,
            "alpha": spec.alpha if spec.variant == "combined" else None,
            "e1_auc": c1["pooled_auc"]["observed"],
            "silhouette_fraction": c1["silhouette_positive_fraction"]["observed"],
            "top1": c2["top1_accuracy"]["observed"],
            "top3": c2["top3_accuracy"]["observed"],
            "e1_auc_pass": c1["pooled_auc"]["pass"],
            "silhouette_pass": c1["silhouette_positive_fraction"]["pass"],
            "top1_pass": c2["top1_accuracy"]["pass"],
            "top3_pass": c2["top3_accuracy"]["pass"],
        }
        row["all_pass"] = all(
            row[k] for k in ("e1_auc_pass", "silhouette_pass", "top1_pass", "top3_pass")
        )
        rows.append(row)
        logger.info(
            "Variant %s: AUC %.3f sil-frac %.3f top1 %.1f%% top3 %.1f%% -> %s",
            spec.label, row["e1_auc"], row["silhouette_fraction"],
            row["top1"] * 100, row["top3"] * 100,
            "PASS" if row["all_pass"] else "FAIL",
        )
    selection = _select_variant(rows)
    return {"rows": rows, "selection": selection, "full_results": full}


def build_variant_comparison_markdown(
    comparison: Dict[str, Any], meta: Dict[str, Any]
) -> str:
    """Markdown comparison table + selection rationale."""
    lines = [
        "# Distance-Variant Comparison (E1 + E2, gold shelf)",
        "",
        f"- Generated: {meta.get('generated')}",
        f"- Baseline dir: {meta.get('baseline_dir')}",
        f"- Manifest: {meta.get('manifest') or 'none'}",
        f"- Authors: {meta.get('n_authors')} calibrated "
        f"({meta.get('n_works')} works); seed {meta.get('seed')}",
        f"- MFW block: top-{meta.get('mfw_n')} shelf words, Burrows Delta "
        f"(mean |z_i - z_j|); blend scale = median(pairwise d18) / "
        f"median(pairwise Delta) = {_fmt(meta.get('blend_scale'))}",
        "",
        "Combined distance: `d = alpha * d_d18 + (1 - alpha) * scale * d_delta`.",
        "",
        "| Variant | E1 AUC (>=0.90) | Silh.>0 frac (>=0.80) | E2 top-1 (>=0.70) "
        "| E2 top-3 (>=0.85) | Gates |",
        "|---|---|---|---|---|---|",
    ]

    def mark(value: str, ok: bool) -> str:
        return f"{value} {'PASS' if ok else 'FAIL'}"

    for row in comparison["rows"]:
        lines.append(
            f"| {row['label']} "
            f"| {mark(format(row['e1_auc'], '.3f'), row['e1_auc_pass'])} "
            f"| {mark(format(row['silhouette_fraction'], '.3f'), row['silhouette_pass'])} "
            f"| {mark(format(row['top1'], '.1%'), row['top1_pass'])} "
            f"| {mark(format(row['top3'], '.1%'), row['top3_pass'])} "
            f"| {'PASS' if row['all_pass'] else 'FAIL'} |"
        )
    selection = comparison["selection"]
    lines += [
        "",
        "## Selection",
        "",
        f"- Selected variant: **{selection.get('selected') or 'NONE (no variant passes)'}**",
        f"- Rationale: {selection['reason']}",
        "",
        "Selection rule: prefer the simplest variant passing all four gates "
        "(d18 < d18_weighted < mfw_delta < combined); combined is preferred "
        "over mfw_delta only when it clearly beats it (>= 3/4 gate metrics "
        "better-or-equal AND top-1 at least 2 points higher).",
        "",
    ]
    return "\n".join(lines)


# =============================================================================
# Reporting
# =============================================================================

def _fmt(value: Optional[float], spec: str = ".3f") -> str:
    return "n/a" if value is None else format(value, spec)


def build_summary_markdown(
    results: Dict[str, Dict[str, Any]], meta: Dict[str, Any]
) -> str:
    """Combined markdown report: gate table + per-experiment detail."""
    lines: List[str] = [
        "# Author-Relative Space Validation (E1-E3)",
        "",
        f"- Generated: {meta.get('generated')}",
        f"- Baseline dir: {meta.get('baseline_dir')}",
        f"- Manifest: {meta.get('manifest') or 'none'}",
        f"- Authors: {meta.get('n_authors')} calibrated "
        f"({meta.get('n_works')} works); seed {meta.get('seed')}",
        f"- Dimension set: {meta.get('dimension_set_version')} "
        f"({meta.get('n_dimensions')} dims)",
        "",
        "## Gate table",
        "",
        "| Experiment | Criterion | Threshold | Observed | Verdict |",
        "|---|---|---|---|---|",
    ]
    for exp in ALL_EXPERIMENTS:
        result = results.get(exp)
        if result is None:
            continue
        for name, criterion in result["criteria"].items():
            verdict = "PASS" if criterion["pass"] else "FAIL"
            lines.append(
                f"| {exp.upper()} {result['name']} | {name} "
                f"| {criterion['comparison']} {_fmt(criterion['threshold'])} "
                f"| {_fmt(criterion['observed'])} | {verdict} |"
            )
    overall = all(r["pass"] for r in results.values()) if results else False
    lines += ["", f"**Overall: {'PASS' if overall else 'FAIL'}**", ""]

    e1 = results.get("e1")
    if e1:
        lines += [
            "## E1 — Within vs between author separation",
            "",
            f"Pooled AUC: {_fmt(e1['criteria']['pooled_auc']['observed'])} "
            f"(within n={e1['n_within']}, median {_fmt(e1['within_median'])}; "
            f"between n={e1['n_between']}, median {_fmt(e1['between_median'])})",
            "",
            "| Author | Works | Silhouette | Within median | Between median |",
            "|---|---|---|---|---|",
        ]
        for slug in sorted(e1["per_author"]):
            row = e1["per_author"][slug]
            lines.append(
                f"| {slug} | {row['n_works']} | {row['silhouette']:.3f} "
                f"| {_fmt(row['within_median'])} | {_fmt(row['between_median'])} |"
            )
        auc = e1["criteria"]["pooled_auc"]["observed"]
        lines += [
            "",
            "**What this means:** "
            f"A work by a known author sits closer to its own author's centroid "
            f"than to other authors' centroids with discrimination AUC "
            f"{_fmt(auc)} (1.0 = perfect, 0.5 = chance). "
            f"{e1['n_authors_silhouette_positive']} of {e1['n_authors']} authors "
            "form coherent clusters (silhouette > 0). "
            + (
                "Within-author variation is reliably smaller than between-author "
                "separation, so W/B percentile statements made in this space are "
                "meaningful."
                if e1["pass"]
                else "Separation is too weak: W/B percentile statements in this "
                "space would not be trustworthy. Do not proceed to new-text "
                "placement on these dimensions."
            ),
            "",
        ]

    e2 = results.get("e2")
    if e2:
        lines += [
            "## E2 — Leave-one-work-out attribution",
            "",
            f"Top-1: {_fmt(e2['criteria']['top1_accuracy']['observed'], '.1%')}, "
            f"top-3: {_fmt(e2['criteria']['top3_accuracy']['observed'], '.1%')} "
            f"over {e2['n_trials']} held-out works, "
            f"{e2['n_candidate_authors']} candidate authors. "
            f"C_llr {_fmt(e2['c_llr']['value'])} "
            f"(min {_fmt(e2['c_llr']['min'])}; descriptive only). "
            f"Sanity check (cosine on raw vectors, not a gate): top-1 "
            f"{_fmt(e2['sanity_check']['top1_accuracy'], '.1%')}.",
            "",
        ]
        if e2["skipped_authors"]:
            lines += [
                f"Skipped as held-out source (< 3 works): "
                f"{', '.join(e2['skipped_authors'])}",
                "",
            ]
        slugs = sorted(e2["confusion_matrix"])
        header = " | ".join(str(i + 1) for i in range(len(slugs)))
        lines += [
            "Confusion matrix (rows = true author, columns = predicted, by index):",
            "",
            f"| # | Author | {header} |",
            "|---|---|" + "---|" * len(slugs),
        ]
        for i, true_slug in enumerate(slugs):
            row = e2["confusion_matrix"][true_slug]
            cells = " | ".join(str(row.get(pred, 0) or "") for pred in slugs)
            lines.append(f"| {i + 1} | {true_slug} | {cells} |")
        lines += [
            "",
            "**What this means:** When each work is held out and re-attributed "
            "by nearest author centroid, the true author is the single best "
            f"match {_fmt(e2['criteria']['top1_accuracy']['observed'], '.0%')} "
            "of the time and among the top three "
            f"{_fmt(e2['criteria']['top3_accuracy']['observed'], '.0%')} of the "
            "time. "
            + (
                "The space carries enough authorial signal for closed-set "
                "attribution among known authors, supporting its use as a "
                "measurement frame."
                if e2["pass"]
                else "Attribution accuracy is below the gate: the space does "
                "not yet carry enough authorial signal to trust placements."
            ),
            "",
        ]

    e3 = results.get("e3")
    if e3:
        n_sig = e3["criteria"]["n_dimensions_exceeding_null_p99"]["observed"]
        lines += [
            "## E3 — Per-dimension discriminative validity",
            "",
            f"{int(n_sig)} of {e3['n_dimensions']} dimensions exceed their "
            f"permutation-null p99 ({e3['n_permutations']} shuffles, "
            f"seed {e3['seed']}).",
            "",
            "| Rank | Dimension | F | eta^2 | null p99 | perm p | ICC-like | > null p99 |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for row in e3["dimension_table"]:
            lines.append(
                f"| {row['rank']} | {row['dimension']} "
                f"| {_fmt(row['f_statistic'], '.1f')} "
                f"| {row['eta_squared']:.3f} | {row['null_p99_eta_squared']:.3f} "
                f"| {row['permutation_p']:.4f} | {row['icc_like']:.3f} "
                f"| {'yes' if row['exceeds_null_p99'] else 'no'} |"
            )
        lines += [
            "",
            "Recommended dimension set v2 (exceeds null p99, ranked by eta^2): "
            + (", ".join(e3["recommended_dimension_set_v2"]) or "(none)"),
            "",
            "**What this means:** For each dimension we ask whether authors "
            "differ more than random label shuffling would produce. "
            f"{int(n_sig)} dimensions carry real author-discriminative signal "
            "at work level; the rest are indistinguishable from noise on this "
            "shelf. "
            + (
                "Enough dimensions are individually valid to support the "
                "18-dim space; recommended_dimension_set_v2 lists the validated "
                "subset for downstream weighting."
                if e3["pass"]
                else "Too few dimensions survive the permutation null: the "
                "dimension set needs rework before the space can be trusted."
            ),
            "",
        ]
    return "\n".join(lines)


def print_gate_table(results: Dict[str, Dict[str, Any]]) -> None:
    """Console PASS/FAIL gate table."""
    print()
    print("=" * 72)
    print("AUTHOR-RELATIVE SPACE VALIDATION — GATE TABLE")
    print("=" * 72)
    for exp in ALL_EXPERIMENTS:
        result = results.get(exp)
        if result is None:
            continue
        verdict = "PASS" if result["pass"] else "FAIL"
        print(f"  {exp.upper()}  {result['name']:<42s} {verdict}")
        for name, criterion in result["criteria"].items():
            print(
                f"        {name}: {_fmt(criterion['observed'])} "
                f"(gate {criterion['comparison']} {_fmt(criterion['threshold'])})"
                f" -> {'pass' if criterion['pass'] else 'FAIL'}"
            )
    overall = all(r["pass"] for r in results.values()) if results else False
    print("-" * 72)
    print(f"  OVERALL: {'PASS' if overall else 'FAIL'}")
    print("=" * 72)
    print()


# =============================================================================
# Main CLI
# =============================================================================

def run_experiments(
    space: AuthorRelativeSpace,
    experiments: Sequence[str],
    seed: int = DEFAULT_SEED,
    spec: Optional[VariantSpec] = None,
    e6_window_lengths: Sequence[int] = E6_WINDOW_LENGTHS,
    e6_max_windows: int = E6_MAX_WINDOWS_PER_WORK,
) -> Dict[str, Dict[str, Any]]:
    """Run the selected experiments against a built space."""
    results: Dict[str, Dict[str, Any]] = {}
    for exp in experiments:
        if exp == "e1":
            results["e1"] = run_e1(space, spec)
        elif exp == "e2":
            results["e2"] = run_e2(space, spec)
        elif exp == "e3":
            results["e3"] = run_e3(space, seed=seed)
        elif exp == "e6":
            results["e6"] = run_e6(
                space, seed=seed,
                window_lengths=e6_window_lengths,
                max_windows_per_work=e6_max_windows,
            )
        else:
            raise ValueError(f"Unknown experiment: {exp}")
        logger.info(
            "%s: %s", exp.upper(),
            "documented (no gate)" if results[exp].get("gate", exp) is None
            else ("PASS" if results[exp]["pass"] else "FAIL"),
        )
    return results


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validation experiments E1-E3 for the author-relative "
                    "measurement space (ADR-0041, forthcoming; issue #60)"
    )
    parser.add_argument(
        "--baseline-dir", default=DEFAULT_BASELINE_DIR,
        help=f"Directory of <author>/<work>_baseline.json (default: {DEFAULT_BASELINE_DIR})",
    )
    parser.add_argument(
        "--manifest", default=None,
        help="Optional Control Shelf manifest YAML (filters to centroid-"
             "eligible fiction, fidelity clean/edge_cleaned)",
    )
    parser.add_argument(
        "--authors", default=None,
        help="Comma-separated author slugs to restrict to (e.g. the gold shelf)",
    )
    parser.add_argument(
        "--min-works", type=int, default=3,
        help="Authors below this become reference-only and are excluded from "
             "all experiments (default: 3)",
    )
    parser.add_argument(
        "--experiments", default=",".join(ALL_EXPERIMENTS),
        help="Comma list of experiments to run (default: e1,e2,e3; e6 — "
             "window-length sensitivity, documentation-only, needs body "
             "text via the manifest — must be requested explicitly)",
    )
    parser.add_argument(
        "--e6-window-lengths", default=",".join(str(v) for v in E6_WINDOW_LENGTHS),
        help="Comma list of E6 window lengths in words "
             f"(default: {','.join(str(v) for v in E6_WINDOW_LENGTHS)})",
    )
    parser.add_argument(
        "--e6-max-windows", type=int, default=E6_MAX_WINDOWS_PER_WORK,
        help=f"Max windows sampled per work for E6 (default: {E6_MAX_WINDOWS_PER_WORK})",
    )
    parser.add_argument(
        "--distance-variant", default="d18", choices=VARIANT_CHOICES,
        help="Distance variant for E1/E2: d18 (recorded baseline), "
             "d18_weighted (E3 eta^2 weights), mfw_delta (Burrows Delta on "
             "the MFW block), combined (alpha blend), or 'all' to run the "
             "full variant comparison and write variant_comparison.{md,json} "
             "(default: d18)",
    )
    parser.add_argument(
        "--alpha", type=float, default=0.5,
        help="Blend weight for the combined variant (default: 0.5; "
             "'all' additionally sweeps %s)" % (COMBINED_ALPHAS,),
    )
    parser.add_argument(
        "--mfw-n", type=int, default=MFW_DEFAULT_N,
        help=f"MFW vocabulary size for the Burrows-Delta block "
             f"(default: {MFW_DEFAULT_N}; only used by mfw_delta/combined/all)",
    )
    parser.add_argument(
        "--vocab-filter", default="none", choices=MFW_VOCAB_FILTERS,
        help="MFW vocabulary filter: 'function_words_only' restricts the "
             "candidate vocabulary to the closed-class stylometric function-"
             "word list BEFORE top-N selection (topic-confound control, "
             "issue #95 P3; default: none)",
    )
    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR,
        help=f"Results directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help=f"RNG seed for permutation null / bootstrap (default: {DEFAULT_SEED})",
    )
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    baseline_dir = _resolve(args.baseline_dir)
    if not baseline_dir.is_dir():
        parser.error(f"Baseline directory not found: {baseline_dir}")
    manifest_path = _resolve(args.manifest) if args.manifest else None
    if manifest_path is not None and not manifest_path.is_file():
        parser.error(f"Manifest not found: {manifest_path}")
    authors = (
        [a.strip() for a in args.authors.split(",") if a.strip()]
        if args.authors else None
    )
    experiments = [e.strip().lower() for e in args.experiments.split(",") if e.strip()]
    unknown = [e for e in experiments if e not in KNOWN_EXPERIMENTS]
    if unknown:
        parser.error(f"Unknown experiments: {', '.join(unknown)}")
    try:
        e6_window_lengths = [
            int(v) for v in args.e6_window_lengths.split(",") if v.strip()
        ]
    except ValueError:
        parser.error(f"Invalid --e6-window-lengths: {args.e6_window_lengths!r}")
    if "e6" in experiments and any(v <= 0 for v in e6_window_lengths):
        parser.error("--e6-window-lengths must be positive integers")

    records = load_shelf(
        baseline_dir,
        dimensions=DIMENSION_SET_V1,
        manifest_path=manifest_path,
        authors=authors,
    )
    if not records:
        parser.error(f"No work baselines loaded from {baseline_dir}")
    logger.info("Loaded %d work records from %s", len(records), baseline_dir)

    variant = args.distance_variant
    # E6 featurizes text windows via the MFW block, so it forces the block on.
    need_mfw = variant in ("mfw_delta", "combined", "all") or "e6" in experiments
    # The space is always BUILT as d18 here (feature vectors are identical
    # across variants); E1/E2 apply the variant via VariantSpec, so a single
    # build (and a single tokenization pass over the shelf) serves all.
    space = AuthorRelativeSpace.build(
        records,
        dimensions=DIMENSION_SET_V1,
        min_works=args.min_works,
        seed=args.seed,
        generated=datetime.now(timezone.utc).isoformat(),
        manifest_path=str(manifest_path) if manifest_path else None,
        mfw_n=args.mfw_n if need_mfw else None,
        mfw_vocab_filter=args.vocab_filter if need_mfw else "none",
    )
    logger.info(
        "Built space: %d calibrated authors, %d works%s",
        space.meta["n_authors"], space.meta["n_works"],
        f", MFW top-{args.mfw_n} (vocab_filter={args.vocab_filter})"
        if need_mfw else "",
    )

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "baseline_dir": str(baseline_dir),
        "manifest": str(manifest_path) if manifest_path else None,
        "authors_filter": authors,
        "min_works": args.min_works,
        "seed": args.seed,
        "n_authors": space.meta["n_authors"],
        "n_works": space.meta["n_works"],
        "n_dimensions": len(space.dimensions),
        "dimension_set_version": space.meta["dimension_set_version"],
        "distance_variant": variant,
    }
    if need_mfw:
        meta["mfw_n"] = args.mfw_n
        meta["mfw_n_effective"] = space.mfw.n_mfw if space.mfw else None
        meta["mfw_vocab_filter"] = args.vocab_filter
        meta["blend_scale"] = (space.blend or {}).get("scale")

    if variant == "all":
        # Full variant comparison: E1+E2 per variant + alpha sweep. The
        # recorded d18 e*_results.json / summary.md are NOT overwritten.
        eta2 = _eta2_weights(space, output_dir / "e3_results.json")
        comparison = run_variant_comparison(space, eta2)
        json_path = output_dir / "variant_comparison.json"
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump({"meta": meta, **comparison}, handle, indent=1)
        logger.info("Wrote %s", json_path)
        md_path = output_dir / "variant_comparison.md"
        md_path.write_text(
            build_variant_comparison_markdown(comparison, meta), encoding="utf-8"
        )
        logger.info("Wrote %s", md_path)
        selection = comparison["selection"]
        print()
        print("=" * 72)
        print("DISTANCE-VARIANT COMPARISON")
        print("=" * 72)
        for row in comparison["rows"]:
            print(
                f"  {row['label']:<18s} AUC {row['e1_auc']:.3f}  "
                f"sil {row['silhouette_fraction']:.3f}  "
                f"top1 {row['top1']:.1%}  top3 {row['top3']:.1%}  "
                f"{'PASS' if row['all_pass'] else 'FAIL'}"
            )
        print("-" * 72)
        print(f"  SELECTED: {selection.get('selected') or 'NONE'}")
        print(f"  {selection['reason']}")
        print("=" * 72)
        return 0 if selection.get("selected") else 3

    # Single-variant run.
    spec: Optional[VariantSpec] = None
    if variant == "d18_weighted":
        eta2 = _eta2_weights(space, output_dir / "e3_results.json")
        w = np.array([eta2.get(d, 0.0) for d in space.dimensions], dtype=float)
        spec = VariantSpec(
            "d18_weighted", "d18_weighted",
            weights_sqrt=np.sqrt(w * (len(w) / w.sum())),
        )
    elif variant == "mfw_delta":
        spec = VariantSpec("mfw_delta", "mfw_delta")
    elif variant == "combined":
        spec = VariantSpec(
            f"combined_alpha{args.alpha:g}", "combined",
            alpha=args.alpha, scale=(space.blend or {}).get("scale"),
        )
        meta["alpha"] = args.alpha

    results = run_experiments(
        space, experiments, seed=args.seed, spec=spec,
        e6_window_lengths=e6_window_lengths,
        e6_max_windows=args.e6_max_windows,
    )

    for exp, result in results.items():
        result_path = output_dir / f"{exp}_results.json"
        with open(result_path, "w", encoding="utf-8") as handle:
            json.dump({"meta": meta, **result}, handle, indent=1)
        logger.info("Wrote %s", result_path)

    # E6 is documentation-only: it gets its own report file and is excluded
    # from the gated summary.md (which records the E1-E3 go/no-go evidence).
    gated_results = {k: v for k, v in results.items() if k in ALL_EXPERIMENTS}
    if "e6" in results:
        e6_md_path = output_dir / "e6_report.md"
        e6_md_path.write_text(
            build_e6_markdown(results["e6"], meta), encoding="utf-8"
        )
        logger.info("Wrote %s", e6_md_path)
        row = results["e6"]["full_work_reference"]
        print()
        print("E6 — window-length sensitivity (documentation-only, no gate):")
        for entry in results["e6"]["per_length"] + [row]:
            label = (
                f"{entry['window_words']}w"
                if isinstance(entry["window_words"], int) else "full"
            )
            print(
                f"  {label:>6s}  "
                f"top1 {_fmt(entry['top1_accuracy'], '.1%'):>6s}  "
                f"top3 {_fmt(entry['top3_accuracy'], '.1%'):>6s}  "
                f"W med {_fmt(entry['within']['median'])}  "
                f"B med {_fmt(entry['between']['median'])}  "
                f"AUC {_fmt(entry['auc'])}"
            )
    if gated_results:
        summary_path = output_dir / "summary.md"
        summary_path.write_text(
            build_summary_markdown(gated_results, meta), encoding="utf-8"
        )
        logger.info("Wrote %s", summary_path)
        print_gate_table(gated_results)
    return 0 if all(r["pass"] for r in gated_results.values()) else 3


if __name__ == "__main__":
    sys.exit(main())
