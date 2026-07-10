#!/usr/bin/env python3
"""Results 2.0 — re-analysis of entry/approach against length-matched envelopes.

Red-team remediation run (docs/redteam/RED_TEAM_SYNTHESIS.md K1, K4,
K5, K6, K7, K9, K10; redteam_stats_attack.md F1/F2/F5/F7/F8/F9;
redteam_claims_attack.md §1/§3/§5/§6). Everything the paper previously
claimed against the full-novel W-p90 entry criterion is restated against the
per-author LENGTH-MATCHED envelopes (LM-W; built by validate_lm_envelopes.py
at 3,000 MFW tokens, work-level LOO):

a. ENTRY — every styled sample (style_prompted + exemplar) is truncated to
   the envelope window length and placed against the TARGET author's LM
   envelope at p90/p95/p99, with (i) exact Clopper-Pearson bounds,
   (ii) cluster-robust bounds via the design effect from the ANOVA ICC over
   (model x target x condition) cells, and (iii) bootstrap CIs on the LM
   thresholds themselves (entry-rate range across the threshold CI).
   Floor discipline (K5): samples below the practice floor are a separately
   reported stratum; samples below the hard floor are excluded from every
   claim. Floors are applied in MFW tokens — the unit the envelope windows
   are built in.

b. HUMAN BASELINES on the same footing — Brinton pastiche chunks vs
   Austen's LM envelope on the PD shelf, full-vocab AND fw-only (K7: the PD
   fw-only run had never been done; the artifact is built by
   build_author_space.py --mfw-vocab-filter function_words_only), plus the
   same-author positive-control row (E8 held-out rates) per shelf.

c. APPROACH, corrected (K6) — nearest-is-target vs the SCENARIO-MATCHED
   null (each target's bound scenario's unprompted nearest-author rate),
   per target / per model / pooled, with cell-level bootstrap CIs; plus the
   rank-vs-metric statement (median delta-to-target, styled minus matched
   unprompted) stated plainly.

d. TRANSLATION BOUND at matched length (K7/F8) — cross- vs same-translator
   Burrows Delta at the WINDOW level (3,000 tokens) within translated
   authors, with honest n (work pairs are the inferential unit) and an
   explicit recommendation, including 'cut from paper' when the design
   cannot support a magnitude claim. Public-release note: this subsection
   needs the contemporary novels' raw text at the artifact-recorded paths;
   without locally held copies it reports 'none usable' (every other
   section runs from data shipped in this repository).

e. CHASSIS restated (K10) — the R3 MFW movement re-read as immobility
   (CI, per-target signs) from the frozen r3_dimension_gap.json.

f. CONTROLS (v0.3 red-team formalization; redteam_stats_attack_v03.md
   G1/G2/G5/G7, redteam_claims_attack_v03.md findings 1/3/6) — the controls
   both v0.3 attackers computed by hand, now owned by the pipeline:

   - G1 unprompted-entry control: unprompted samples on the four BOUND
     scenarios, floor-compliant, truncated to the window, placed against
     the bound target's LM envelope @p90 (identical code path as styled).
     Styled-minus-unprompted increment with independent cluster-bootstrap
     CIs and per-model Fisher tests. This is the PRIMARY entry framing:
     styled entry is an increment over an envelope-porosity base rate.
   - G2 model-matched completion comparison: per-model completion-vs-styled
     entry over the matched pools only (models with at least one compliant
     completion AND at least one primary styled sample), exact sign test,
     pooled matched rates. Reads results2/completion_results.json.
   - G7 width de-circularized: (a) the full model x target entry table;
     (b) ALL shelf authors as pseudo-targets for the unprompted samples
     (every floor-compliant unprompted sample against every author's LM
     envelope) — per-author entry rate vs envelope p90 width, correlation
     with CI, n = all shelf authors, not 4; (c) a width-independent
     restatement: per-target styled median distance with the envelope
     width and the median's percentile within the target's own envelope.
   - E8 yardstick (G4, reporting only — NO gate changes): per-shelf
     observed self-entry rates with cluster-naive (window CP) AND
     work-level bootstrap CIs, plus the strict gate verdict as committed.

Outputs (under --output-dir, default
reports/validation/author_space/results2_rerun/): {entry_results.json,
entry_report.md,controls_results.json,controls_results.md,e8_yardstick.md}.
Every table carries its n, its clustering treatment, and
its threshold-CI sensitivity. Numbers + readings, no claim formatting.
The released evidence run of this tool is committed under
reports/validation/author_space/results2/ — a rerun reproduces its numbers
exactly (seeded) apart from the generation timestamp and the
private-text-only translation subsection (d above).

Usage:
    python3 tools/rerun_entry_analysis.py
"""

from __future__ import annotations

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
import itertools
import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from author_manifold.author_space import (
    AuthorRelativeSpace,
    LengthMatchedEnvelopes,
    MFWBlock,
    design_effect,
    mfw_tokenize,
    sha256_of_file,
)

logger = logging.getLogger("rerun_entry_analysis")

ARTIFACT_DIR = REPO_ROOT / "data/artifacts"
ENTRY_LEVELS = (90, 95, 99)
STYLED_CONDITIONS = ("style_prompted", "exemplar")

GUTENBERG_START = re.compile(
    r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)
GUTENBERG_END = re.compile(
    r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def clopper_pearson(x: float, n: float, alpha: float = 0.05) -> Tuple[float, float]:
    """Exact two-sided CP interval; accepts fractional effective counts."""
    from scipy.stats import beta

    if n <= 0:
        return (0.0, 1.0)
    lo = 0.0 if x <= 0 else float(beta.ppf(alpha / 2, x, n - x + 1))
    hi = 1.0 if x >= n else float(beta.ppf(1 - alpha / 2, x + 1, n - x))
    return (lo, hi)


def cp_one_sided_upper(x: float, n: float, alpha: float = 0.05) -> float:
    from scipy.stats import beta

    if n <= 0:
        return 1.0
    return 1.0 if x >= n else float(beta.ppf(1 - alpha, x + 1, n - x))


def cluster_bootstrap_ci(
    values: Sequence[float],
    clusters: Sequence[Any],
    n_bootstrap: int = 2000,
    seed: int = 20260609,
    alpha: float = 0.05,
) -> Tuple[float, float]:
    """Percentile bootstrap CI for a mean, resampling CLUSTERS with replacement."""
    by: Dict[Any, List[float]] = defaultdict(list)
    for value, label in zip(values, clusters):
        by[label].append(float(value))
    cluster_arrays = [np.asarray(v) for v in by.values()]
    k = len(cluster_arrays)
    if k < 2:
        m = float(np.mean(values)) if len(values) else float("nan")
        return (m, m)
    rng = np.random.default_rng(seed)
    means = np.empty(n_bootstrap)
    for b in range(n_bootstrap):
        idx = rng.integers(0, k, size=k)
        sample = np.concatenate([cluster_arrays[i] for i in idx])
        means[b] = sample.mean()
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return (float(lo), float(hi))


def binom_test_greater(k: int, n: int, p0: float) -> float:
    from scipy.stats import binomtest

    if n == 0:
        return float("nan")
    return float(binomtest(k, n, p0, alternative="greater").pvalue)


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------

class VocabRun:
    """One vocabulary's spaces + envelopes (contemporary shelf + PD shelf)."""

    def __init__(
        self,
        label: str,
        space_path: Path,
        envelope_path: Path,
        pd_space_path: Path,
        pd_envelope_path: Path,
    ):
        self.label = label
        self.space_path = space_path
        self.envelope_path = envelope_path
        self.pd_space_path = pd_space_path
        self.pd_envelope_path = pd_envelope_path
        self.space = AuthorRelativeSpace.from_artifact(space_path)
        self.envelopes = LengthMatchedEnvelopes.from_artifact(envelope_path)
        self.pd_space = AuthorRelativeSpace.from_artifact(pd_space_path)
        self.pd_envelopes = LengthMatchedEnvelopes.from_artifact(pd_envelope_path)
        for env, space, name in (
            (self.envelopes, self.space, label),
            (self.pd_envelopes, self.pd_space, f"{label}/pd"),
        ):
            if env.meta.get("vocab_filter") != space.mfw.vocab_filter:
                raise ValueError(f"Envelope/space vocab mismatch for {name}")

    def provenance(self) -> Dict[str, Any]:
        return {
            "space": str(self.space_path.relative_to(REPO_ROOT)),
            "space_sha256": sha256_of_file(self.space_path),
            "envelopes": str(self.envelope_path.relative_to(REPO_ROOT)),
            "envelopes_source_sha256": self.envelopes.meta.get(
                "source_artifact_sha256"),
            "pd_space": str(self.pd_space_path.relative_to(REPO_ROOT)),
            "pd_envelopes": str(self.pd_envelope_path.relative_to(REPO_ROOT)),
            "window_words": self.envelopes.window_words,
            "vocab_filter": self.space.mfw.vocab_filter,
        }


def author_distances(
    space: AuthorRelativeSpace, tokens: Sequence[str]
) -> Dict[str, float]:
    """Burrows-Delta distances from a token window to every calibrated centroid."""
    z = space.mfw.featurize_tokens(tokens)
    return {
        slug: MFWBlock.delta(z, entry.mfw_centroid)
        for slug, entry in space.authors.items()
    }


def load_corpus(corpus_dir: Path) -> List[Dict[str, Any]]:
    manifest_path = corpus_dir / "manifest.jsonl"
    records = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    out = []
    for rec in records:
        path = corpus_dir / rec["file_path"]
        if not path.exists():
            logger.warning("missing sample file: %s", path)
            continue
        tokens = mfw_tokenize(path.read_text(encoding="utf-8"))
        if not tokens:
            logger.warning("empty sample skipped: %s", rec["sample_id"])
            continue
        rec["_tokens"] = tokens
        rec["_n_tokens"] = len(tokens)
        out.append(rec)
    return out


def place_corpus(
    run: VocabRun, records: List[Dict[str, Any]], window_words: int
) -> List[Dict[str, Any]]:
    """Place each corpus sample (truncated to the envelope window length)."""
    placements = []
    for rec in records:
        tokens = rec["_tokens"][:window_words]
        dists = author_distances(run.space, tokens)
        nearest = min(dists, key=dists.get)
        placements.append({
            "sample_id": rec["sample_id"],
            "model": rec["model"],
            "condition": rec["condition"],
            "scenario_id": rec["scenario_id"],
            "style_target": rec.get("style_target"),
            "n_tokens": rec["_n_tokens"],
            "word_count": rec.get("word_count"),
            "nearest_author": nearest,
            "nearest_distance": dists[nearest],
            "target_distance": (
                dists.get(rec["style_target"]) if rec.get("style_target") else None
            ),
        })
    return placements


# ---------------------------------------------------------------------------
# a. Entry analysis
# ---------------------------------------------------------------------------

def entry_block(
    run: VocabRun,
    styled: List[Dict[str, Any]],
    stratum_label: str,
    seed: int,
    n_bootstrap: int,
) -> Dict[str, Any]:
    """Entry rates vs the target's LM envelope at p90/p95/p99 with all three
    uncertainty treatments (CP, design-effect, threshold bootstrap)."""
    n = len(styled)
    cells = [f"{p['model']}|{p['style_target']}|{p['condition']}" for p in styled]
    out: Dict[str, Any] = {
        "stratum": stratum_label,
        "n": n,
        "clustering": "(model x target x condition) cells",
        "n_cells": len(set(cells)),
    }
    if n == 0:
        return out

    distances = [p["target_distance"] for p in styled]
    de_dist = design_effect(distances, cells)
    out["icc_target_distance"] = de_dist["icc"]
    out["median_target_distance"] = float(np.median(distances))

    # Threshold bootstrap per target (computed once per level below).
    targets = sorted({p["style_target"] for p in styled})
    threshold_ci: Dict[str, Dict[int, Tuple[float, float]]] = {
        t: {
            level: run.envelopes.authors[t].bootstrap_quantile_ci(
                level, n_bootstrap=n_bootstrap, seed=seed)
            for level in ENTRY_LEVELS
        }
        for t in targets
    }

    per_level: Dict[str, Any] = {}
    for level in ENTRY_LEVELS:
        entered = [
            1 if p["target_distance"]
            <= run.envelopes.quantile(p["style_target"], level) else 0
            for p in styled
        ]
        x = int(sum(entered))
        de = design_effect(entered, cells)
        ci = clopper_pearson(x, n)
        ci_adj = clopper_pearson(
            x / de["design_effect"], n / de["design_effect"])
        boot_ci = cluster_bootstrap_ci(entered, cells, n_bootstrap, seed)
        # Entry-rate range over the threshold CI (resampled envelope windows).
        rate_lo = float(np.mean([
            1 if p["target_distance"] <= threshold_ci[p["style_target"]][level][0]
            else 0 for p in styled
        ]))
        rate_hi = float(np.mean([
            1 if p["target_distance"] <= threshold_ci[p["style_target"]][level][1]
            else 0 for p in styled
        ]))
        per_level[f"p{level}"] = {
            "entered": x,
            "n": n,
            "rate": x / n,
            "cp_ci95": list(ci),
            "cp_one_sided_upper95": cp_one_sided_upper(x, n),
            "icc_entered": de["icc"],
            "design_effect": de["design_effect"],
            "n_eff": de["n_eff"],
            "cp_ci95_design_effect_adjusted": list(ci_adj),
            "cell_bootstrap_ci95": list(boot_ci),
            "rate_range_over_threshold_ci95": [rate_lo, rate_hi],
            "thresholds": {
                t: {
                    "value": run.envelopes.quantile(t, level),
                    "ci95": list(threshold_ci[t][level]),
                } for t in targets
            },
        }
    out["per_level"] = per_level

    # Per-model table at p90 (K7: never average across models without bests).
    per_model = {}
    for model in sorted({p["model"] for p in styled}):
        rows = [p for p in styled if p["model"] == model]
        x90 = sum(
            1 for p in rows
            if p["target_distance"] <= run.envelopes.quantile(p["style_target"], 90)
        )
        per_model[model] = {
            "n": len(rows),
            "entered_p90": x90,
            "rate_p90": x90 / len(rows),
            "cp_ci95": list(clopper_pearson(x90, len(rows))),
            "median_target_distance": float(
                np.median([p["target_distance"] for p in rows])),
        }
    out["per_model"] = per_model
    best = max(per_model.items(), key=lambda kv: kv[1]["rate_p90"])
    out["best_model_p90"] = {"model": best[0], **best[1]}

    per_target = {}
    for t in targets:
        rows = [p for p in styled if p["style_target"] == t]
        x90 = sum(
            1 for p in rows
            if p["target_distance"] <= run.envelopes.quantile(t, 90))
        per_target[t] = {
            "n": len(rows),
            "entered_p90": x90,
            "rate_p90": x90 / len(rows),
            "lm_p90": run.envelopes.quantile(t, 90),
            "median_target_distance": float(
                np.median([p["target_distance"] for p in rows])),
        }
    out["per_target"] = per_target

    per_condition = {}
    for cond in STYLED_CONDITIONS:
        rows = [p for p in styled if p["condition"] == cond]
        if not rows:
            continue
        x90 = sum(
            1 for p in rows
            if p["target_distance"] <= run.envelopes.quantile(p["style_target"], 90))
        per_condition[cond] = {
            "n": len(rows), "entered_p90": x90, "rate_p90": x90 / len(rows),
        }
    out["per_condition"] = per_condition
    return out


# ---------------------------------------------------------------------------
# b. Human baselines (PD shelf) on the same footing
# ---------------------------------------------------------------------------

def pastiche_block(
    run: VocabRun,
    pastiche_path: Path,
    target: str,
    window_words: int,
    seed: int,
    n_bootstrap: int,
) -> Dict[str, Any]:
    raw = pastiche_path.read_text(encoding="utf-8")
    m = GUTENBERG_START.search(raw)
    if m:
        raw = raw[m.end():]
    m = GUTENBERG_END.search(raw)
    if m:
        raw = raw[: m.start()]
    tokens = mfw_tokenize(raw)
    n_chunks = len(tokens) // window_words
    env = run.pd_envelopes.authors[target]
    chunks = []
    for i in range(n_chunks):
        chunk = tokens[i * window_words:(i + 1) * window_words]
        dists = author_distances(run.pd_space, chunk)
        nearest = min(dists, key=dists.get)
        chunks.append({
            "chunk": i,
            "nearest_author": nearest,
            "target_distance": dists[target],
        })
    result: Dict[str, Any] = {
        "pastiche": str(pastiche_path.relative_to(REPO_ROOT)),
        "target": target,
        "n_chunks": n_chunks,
        "clustering": "single work — chunks are NOT independent "
                      "(one author, one novel, shared characters/world); "
                      "n is descriptive, not inferential",
        "nearest_is_target": sum(
            1 for c in chunks if c["nearest_author"] == target),
        "median_target_distance": float(
            np.median([c["target_distance"] for c in chunks])) if chunks else None,
        "lm_quantiles": env.quantiles,
    }
    for level in ENTRY_LEVELS:
        x = sum(
            1 for c in chunks if c["target_distance"] <= env.quantiles[f"p{level}"])
        t_lo, t_hi = env.bootstrap_quantile_ci(
            level, n_bootstrap=n_bootstrap, seed=seed)
        result[f"entered_p{level}"] = {
            "entered": x,
            "n": n_chunks,
            "rate": x / n_chunks if n_chunks else None,
            "cp_ci95": list(clopper_pearson(x, n_chunks)),
            "rate_range_over_threshold_ci95": [
                float(np.mean([c["target_distance"] <= t_lo for c in chunks])),
                float(np.mean([c["target_distance"] <= t_hi for c in chunks])),
            ] if chunks else None,
        }
    result["chunks"] = chunks
    return result


def positive_control_rows(e8_path: Path) -> Dict[str, Any]:
    """Same-author held-out rows (E8) so the entry table has its yardstick."""
    if not e8_path.is_file():
        return {"available": False, "e8_path": str(e8_path)}
    e8 = json.loads(e8_path.read_text(encoding="utf-8"))
    rows = {}
    for shelf in e8.get("shelves", []):
        rows[shelf["shelf"]] = {
            "pooled_inside_p90": shelf["pooled_held_out_inside_p90"],
            "pooled_n": shelf["pooled_held_out_n"],
            "pooled_rate": shelf["pooled_held_out_rate"],
            "pooled_rate_ci95": shelf["pooled_rate_ci95"],
            "construction": "leave-work-out held-out windows (E8)",
            "per_author": {
                a["author"]: {
                    "inside": a["held_out_inside_p90"],
                    "n": a["held_out_n"],
                    "rate": a["held_out_rate"],
                }
                for a in shelf["authors"]
            },
        }
    return {"available": True, "e8_path": str(e8_path.relative_to(REPO_ROOT)),
            "shelves": rows}


# ---------------------------------------------------------------------------
# c. Approach, corrected
# ---------------------------------------------------------------------------

def approach_block(
    placements: List[Dict[str, Any]],
    styled: List[Dict[str, Any]],
    seed: int,
    n_bootstrap: int,
) -> Dict[str, Any]:
    unprompted = [p for p in placements if p["condition"] == "unprompted"]

    # Target -> bound scenario(s) from the styled records themselves.
    target_scenarios: Dict[str, set] = defaultdict(set)
    for p in styled:
        target_scenarios[p["style_target"]].add(p["scenario_id"])
    binding = {t: sorted(s) for t, s in target_scenarios.items()}

    per_target = {}
    pooled_null_hits = 0
    pooled_null_n = 0
    for target, scenarios in sorted(binding.items()):
        rows = [p for p in styled if p["style_target"] == target]
        k = sum(1 for p in rows if p["nearest_author"] == target)
        null_rows = [p for p in unprompted if p["scenario_id"] in scenarios]
        null_k = sum(1 for p in null_rows if p["nearest_author"] == target)
        pooled_null_hits += null_k
        pooled_null_n += len(null_rows)
        p0 = null_k / len(null_rows) if null_rows else float("nan")
        cells = [f"{p['model']}|{p['condition']}" for p in rows]
        hits = [1 if p["nearest_author"] == target else 0 for p in rows]
        per_target[target] = {
            "scenarios": scenarios,
            "styled_nearest_is_target": k,
            "styled_n": len(rows),
            "styled_rate": k / len(rows) if rows else None,
            "scenario_matched_null_hits": null_k,
            "scenario_matched_null_n": len(null_rows),
            "scenario_matched_null_p0": p0,
            "binomial_p_greater_vs_matched_null": binom_test_greater(
                k, len(rows), p0) if null_rows else None,
            "cell_bootstrap_ci95": list(cluster_bootstrap_ci(
                hits, cells, n_bootstrap, seed)),
            "clustering": "(model x condition) cells within target",
        }

    pooled_k = sum(1 for p in styled if p["nearest_author"] == p["style_target"])
    pooled_n = len(styled)
    pooled_p0 = pooled_null_hits / pooled_null_n if pooled_null_n else float("nan")
    pooled_cells = [
        f"{p['model']}|{p['style_target']}|{p['condition']}" for p in styled]
    pooled_hits = [
        1 if p["nearest_author"] == p["style_target"] else 0 for p in styled]
    de = design_effect(pooled_hits, pooled_cells)

    per_model = {}
    for model in sorted({p["model"] for p in styled}):
        rows = [p for p in styled if p["model"] == model]
        k = sum(1 for p in rows if p["nearest_author"] == p["style_target"])
        per_model[model] = {
            "nearest_is_target": k,
            "n": len(rows),
            "rate": k / len(rows),
            "cp_ci95": list(clopper_pearson(k, len(rows))),
            "above_scenario_matched_null": (k / len(rows)) > pooled_p0,
        }
    best = max(per_model.items(), key=lambda kv: kv[1]["rate"])

    # Rank-vs-metric: styled target distance minus matched unprompted median
    # (same model, same scenario) target distance.
    unprompted_by_cell: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for p in unprompted:
        unprompted_by_cell[(p["model"], p["scenario_id"])].append(p)
    deltas = []
    delta_cells = []
    n_unmatched = 0
    for p in styled:
        matched = unprompted_by_cell.get((p["model"], p["scenario_id"]), [])
        if not matched:
            n_unmatched += 1
            continue
        target = p["style_target"]
        # Distance from each matched unprompted sample to the SAME target.
        matched_d = float(np.median([
            m["per_author_target_distance"][target] for m in matched
        ]))
        deltas.append(p["target_distance"] - matched_d)
        delta_cells.append(f"{p['model']}|{target}|{p['condition']}")
    rank_vs_metric = {
        "definition": "styled target distance minus median matched-unprompted "
                      "(same model, same scenario) distance to the same "
                      "target; positive = styled is FARTHER from the target",
        "n": len(deltas),
        "n_unmatched_skipped": n_unmatched,
        "median_delta": float(np.median(deltas)) if deltas else None,
        "fraction_closer_than_matched_unprompted": (
            float(np.mean([d < 0 for d in deltas])) if deltas else None),
        "cell_bootstrap_ci95_median": None,
        "clustering": "(model x target x condition) cells",
    }
    if deltas:
        # Bootstrap the median over cells.
        by: Dict[str, List[float]] = defaultdict(list)
        for d, c in zip(deltas, delta_cells):
            by[c].append(d)
        arrays = [np.asarray(v) for v in by.values()]
        rng = np.random.default_rng(seed)
        medians = np.empty(n_bootstrap)
        for b in range(n_bootstrap):
            idx = rng.integers(0, len(arrays), size=len(arrays))
            medians[b] = np.median(np.concatenate([arrays[i] for i in idx]))
        rank_vs_metric["cell_bootstrap_ci95_median"] = [
            float(np.percentile(medians, 2.5)),
            float(np.percentile(medians, 97.5)),
        ]

    return {
        "target_scenario_binding": binding,
        "per_target": per_target,
        "pooled": {
            "styled_nearest_is_target": pooled_k,
            "styled_n": pooled_n,
            "styled_rate": pooled_k / pooled_n if pooled_n else None,
            "scenario_matched_null_p0": pooled_p0,
            "scenario_matched_null_hits": pooled_null_hits,
            "scenario_matched_null_n": pooled_null_n,
            "binomial_p_greater_vs_matched_null": binom_test_greater(
                pooled_k, pooled_n, pooled_p0) if pooled_null_n else None,
            "icc": de["icc"],
            "design_effect": de["design_effect"],
            "n_eff": de["n_eff"],
            "cp_ci95_design_effect_adjusted": list(clopper_pearson(
                pooled_k / de["design_effect"], pooled_n / de["design_effect"])),
            "cell_bootstrap_ci95": list(cluster_bootstrap_ci(
                pooled_hits, pooled_cells, n_bootstrap, seed)),
            "clustering": "(model x target x condition) cells",
        },
        "per_model": per_model,
        "best_model": {"model": best[0], **best[1]},
        "rank_vs_metric": rank_vs_metric,
    }


def native_length_rank_vs_metric(
    run: VocabRun,
    primary_records: List[Dict[str, Any]],
    unprompted_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Continuity reference: the same rank-vs-metric delta at NATIVE sample
    lengths (the draft-v0.2 number, +0.03 full-vocab, was computed this way).
    Native lengths mix scales (gpt-5 over-writes 2.4x), so the matched-length
    figure is primary; this row exists so the change is traceable."""
    by_cell: Dict[Tuple[str, str], List[Dict[str, float]]] = defaultdict(list)
    for r in unprompted_records:
        by_cell[(r["model"], r["scenario_id"])].append(
            author_distances(run.space, r["_tokens"]))
    deltas = []
    for r in primary_records:
        cell = by_cell.get((r["model"], r["scenario_id"]))
        if not cell:
            continue
        target = r["style_target"]
        d = author_distances(run.space, r["_tokens"])[target]
        deltas.append(d - float(np.median([m[target] for m in cell])))
    return {
        "definition": "same delta as rank_vs_metric but at native sample "
                      "lengths (scale-mixed; reference only)",
        "n": len(deltas),
        "median_delta": float(np.median(deltas)) if deltas else None,
        "fraction_closer_than_matched_unprompted": (
            float(np.mean([d < 0 for d in deltas])) if deltas else None),
    }


# ---------------------------------------------------------------------------
# d. Translation bound at matched length
# ---------------------------------------------------------------------------

def translation_block(
    run: VocabRun,
    window_words: int,
    seed: int,
    max_windows_per_work: int = 30,
) -> Dict[str, Any]:
    from author_manifold.author_space import record_body_tokens

    rng = np.random.default_rng(seed)
    space = run.space

    def work_window_z(work) -> Optional[List[np.ndarray]]:
        tokens = record_body_tokens(work, text_root=REPO_ROOT)
        if not tokens:
            return None
        n_win = len(tokens) // window_words
        if n_win == 0:
            return None
        chosen = np.arange(n_win)
        if n_win > max_windows_per_work:
            chosen = np.sort(
                rng.choice(n_win, size=max_windows_per_work, replace=False))
        return [
            space.mfw.featurize_tokens(
                tokens[i * window_words:(i + 1) * window_words])
            for i in chosen
        ]

    def usable_translator(t: Optional[str]) -> Optional[str]:
        if not t or ";" in t:    # multi-translator works are not assignable
            return None
        return t

    pairs: List[Dict[str, Any]] = []
    z_cache: Dict[Tuple[str, int], Optional[List[np.ndarray]]] = {}
    for slug in sorted(space.authors):
        works = space.authors[slug].works
        tagged = [
            (i, w, usable_translator(w.translator))
            for i, w in enumerate(works)
        ]
        tagged = [(i, w, t) for i, w, t in tagged if t]
        if len(tagged) < 2:
            continue
        for (i_a, w_a, t_a), (i_b, w_b, t_b) in itertools.combinations(tagged, 2):
            for key, work in (((slug, i_a), w_a), ((slug, i_b), w_b)):
                if key not in z_cache:
                    z_cache[key] = work_window_z(work)
            za, zb = z_cache[(slug, i_a)], z_cache[(slug, i_b)]
            if not za or not zb:
                continue
            deltas = [
                MFWBlock.delta(a, b) for a in za for b in zb
            ]
            pairs.append({
                "author": slug,
                "work_a": w_a.title, "translator_a": t_a,
                "work_b": w_b.title, "translator_b": t_b,
                "pair_type": "same_translator" if t_a == t_b else "cross_translator",
                "n_window_pairs": len(deltas),
                "median_window_delta": float(np.median(deltas)),
            })

    same = [p["median_window_delta"] for p in pairs
            if p["pair_type"] == "same_translator"]
    cross = [p["median_window_delta"] for p in pairs
             if p["pair_type"] == "cross_translator"]

    # Exact permutation test on work-pair medians (the honest unit).
    perm_p = None
    observed = None
    if same and cross:
        observed = float(np.median(cross) - np.median(same))
        all_vals = same + cross
        n_same = len(same)
        count = total = 0
        for combo in itertools.combinations(range(len(all_vals)), n_same):
            s = [all_vals[i] for i in combo]
            c = [all_vals[i] for i in range(len(all_vals)) if i not in combo]
            stat = float(np.median(c) - np.median(s))
            total += 1
            if stat >= observed - 1e-12:
                count += 1
        perm_p = count / total

    # Same-geometry reference: same-author cross-work window pairs for the
    # NON-translated calibrated authors (translator = None throughout).
    ref_medians: List[float] = []
    for slug in sorted(space.authors):
        works = space.authors[slug].works
        if any(usable_translator(w.translator) for w in works):
            continue
        idx_pairs = list(itertools.combinations(range(len(works)), 2))
        if len(idx_pairs) > 4:
            sel = rng.choice(len(idx_pairs), size=4, replace=False)
            idx_pairs = [idx_pairs[i] for i in sel]
        for i_a, i_b in idx_pairs:
            for key, work in (((slug, i_a), works[i_a]), ((slug, i_b), works[i_b])):
                if key not in z_cache:
                    z_cache[key] = work_window_z(work)
            za, zb = z_cache[(slug, i_a)], z_cache[(slug, i_b)]
            if not za or not zb:
                continue
            za_s = za[:10]
            zb_s = zb[:10]
            ref_medians.append(float(np.median(
                [MFWBlock.delta(a, b) for a in za_s for b in zb_s])))

    # Validity verdict: 5-vs-8 work pairs cannot support a magnitude
    # comparison against styled-sample distances unless the contrast is both
    # large and significant at the work-pair level.
    valid = (
        perm_p is not None and perm_p < 0.05
        and len(same) >= 5 and len(cross) >= 5
    )
    recommendation = (
        "report as descriptive window-level contrast with work-pair n in the "
        "same sentence" if valid else "cut from paper"
    )
    return {
        "design": "within translated authors: all work pairs where both works "
                  "carry a single-translator tag; distance = window-level "
                  f"({window_words}-token) Burrows Delta, all cross-work "
                  "window pairs, summarized per WORK PAIR (the inferential "
                  "unit); window pairs within a work pair are not independent",
        "n_work_pairs_same_translator": len(same),
        "n_work_pairs_cross_translator": len(cross),
        "median_same_translator": float(np.median(same)) if same else None,
        "median_cross_translator": float(np.median(cross)) if cross else None,
        "cross_minus_same": observed,
        "exact_permutation_p_one_sided": perm_p,
        "reference_same_author_no_translator_median": (
            float(np.median(ref_medians)) if ref_medians else None),
        "reference_n_work_pairs": len(ref_medians),
        "pairs": pairs,
        "validity": {
            "scale_valid": True,
            "note": "window-level recomputation removes the F8 length "
                    "confound (novel-pair vs sample distances); what remains "
                    "is the tiny work-pair n",
            "supports_magnitude_claim_vs_prompting": bool(valid),
        },
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# e. Chassis restated (K10)
# ---------------------------------------------------------------------------

def chassis_block(r3_path: Path) -> Dict[str, Any]:
    if not r3_path.is_file():
        return {"available": False, "r3_path": str(r3_path)}
    r3 = json.loads(r3_path.read_text(encoding="utf-8"))
    mfw = r3["table"]["mfw_delta"]
    per_target = {
        t: d.get("mfw_median_movement") for t, d in r3["per_target"].items()
    }
    gap = mfw["median_gap_unprompted"]
    ci = mfw["median_movement_ci95"]
    signs = {t: ("toward" if v > 0 else "away") for t, v in per_target.items()}
    return {
        "available": True,
        "r3_path": str(r3_path.relative_to(REPO_ROOT)),
        "n": mfw["n"],
        "median_movement_delta": mfw["median_movement"],
        "median_movement_ci95": ci,
        "median_gap_unprompted": gap,
        "gap_closure_range_pct": [100 * ci[0] / gap, 100 * ci[1] / gap],
        "sign_test_p_holm": mfw.get("sign_test_p_holm"),
        "per_target_mfw_median_movement": per_target,
        "per_target_sign": signs,
        "reading": (
            "Immobility, not directed movement-away: aggregate MFW movement "
            f"median {mfw['median_movement']:+.3f} Delta "
            f"[{ci[0]:+.3f}, {ci[1]:+.3f}] on an unprompted gap of "
            f"{gap:.3f} (closure {100 * ci[0] / gap:+.1f}% to "
            f"{100 * ci[1] / gap:+.1f}%), with per-target signs split "
            f"{sum(1 for s in signs.values() if s == 'toward')}/"
            f"{len(signs)} toward. The CI brackets zero-to-slightly-negative "
            "and the sign flips across targets; the defensible claim is "
            "|closure| <= ~3% in either direction against 14-21% closure on "
            "texture dimensions (K10)."
        ),
    }


# ---------------------------------------------------------------------------
# f. Controls (v0.3 red-team G1/G2/G5/G7 + claims findings 1/3/6)
# ---------------------------------------------------------------------------

def fisher_two_sided_p(k1: int, n1: int, k0: int, n0: int) -> Optional[float]:
    from scipy.stats import fisher_exact

    if n1 == 0 or n0 == 0:
        return None
    return float(fisher_exact(
        [[k1, n1 - k1], [k0, n0 - k0]], alternative="two-sided")[1])


def diff_cluster_bootstrap_ci(
    v1: Sequence[float], c1: Sequence[Any],
    v0: Sequence[float], c0: Sequence[Any],
    n_bootstrap: int = 2000, seed: int = 20260609, alpha: float = 0.05,
) -> Tuple[float, float]:
    """Percentile bootstrap CI for mean(v1) - mean(v0), resampling each
    arm's CLUSTERS independently (the two arms share no clusters: styled
    cells are (model x target x condition), unprompted cells are
    (model x scenario))."""
    def groups(values: Sequence[float], clusters: Sequence[Any]) -> List[np.ndarray]:
        by: Dict[Any, List[float]] = defaultdict(list)
        for value, label in zip(values, clusters):
            by[label].append(float(value))
        return [np.asarray(g) for g in by.values()]

    g1, g0 = groups(v1, c1), groups(v0, c0)
    if len(g1) < 2 or len(g0) < 2:
        d = float(np.mean(v1) - np.mean(v0))
        return (d, d)
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_bootstrap)
    for b in range(n_bootstrap):
        s1 = np.concatenate([g1[i] for i in rng.integers(0, len(g1), size=len(g1))])
        s0 = np.concatenate([g0[i] for i in rng.integers(0, len(g0), size=len(g0))])
        diffs[b] = s1.mean() - s0.mean()
    return (float(np.percentile(diffs, 100 * alpha / 2)),
            float(np.percentile(diffs, 100 * (1 - alpha / 2))))


def unprompted_entry_control_block(
    run: VocabRun,
    styled: List[Dict[str, Any]],
    unp_bound: List[Dict[str, Any]],
    scen2target: Dict[str, str],
    seed: int,
    n_bootstrap: int,
    level: int = 90,
) -> Dict[str, Any]:
    """G1 — never-prompted samples on the bound scenarios, placed against
    the bound target's LM envelope: the base rate styled entry must beat.

    `unp_bound` rows are floor-compliant unprompted placements carrying
    `_all_author_distances` (window-truncated, same code path as styled)."""
    u_entered: List[int] = []
    u_cells: List[str] = []
    per_model_u: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    per_target_u: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for p in unp_bound:
        target = scen2target[p["scenario_id"]]
        d = p["_all_author_distances"][target]
        e = 1 if d <= run.envelopes.quantile(target, level) else 0
        u_entered.append(e)
        u_cells.append(f"{p['model']}|{p['scenario_id']}")
        per_model_u[p["model"]][0] += e
        per_model_u[p["model"]][1] += 1
        per_target_u[target][0] += e
        per_target_u[target][1] += 1

    s_entered = [
        1 if p["target_distance"] <= run.envelopes.quantile(p["style_target"], level)
        else 0 for p in styled
    ]
    s_cells = [f"{p['model']}|{p['style_target']}|{p['condition']}" for p in styled]
    per_model_s: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    per_target_s: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
    for p, e in zip(styled, s_entered):
        per_model_s[p["model"]][0] += e
        per_model_s[p["model"]][1] += 1
        per_target_s[p["style_target"]][0] += e
        per_target_s[p["style_target"]][1] += 1

    ku, nu = int(sum(u_entered)), len(u_entered)
    ks, ns = int(sum(s_entered)), len(s_entered)
    rate_u, rate_s = ku / nu if nu else None, ks / ns if ns else None
    inc_ci = diff_cluster_bootstrap_ci(
        s_entered, s_cells, u_entered, u_cells, n_bootstrap, seed)

    per_model = {}
    for model in sorted(set(per_model_u) | set(per_model_s)):
        ku_m, nu_m = per_model_u.get(model, [0, 0])
        ks_m, ns_m = per_model_s.get(model, [0, 0])
        per_model[model] = {
            "unprompted_entered": ku_m, "unprompted_n": nu_m,
            "unprompted_rate": ku_m / nu_m if nu_m else None,
            "styled_entered": ks_m, "styled_n": ns_m,
            "styled_rate": ks_m / ns_m if ns_m else None,
            "increment_pp": (
                100 * (ks_m / ns_m - ku_m / nu_m) if nu_m and ns_m else None),
            "fisher_two_sided_p": fisher_two_sided_p(ks_m, ns_m, ku_m, nu_m),
        }
    per_target = {}
    for target in sorted(set(per_target_u) | set(per_target_s)):
        ku_t, nu_t = per_target_u.get(target, [0, 0])
        ks_t, ns_t = per_target_s.get(target, [0, 0])
        per_target[target] = {
            "unprompted_entered": ku_t, "unprompted_n": nu_t,
            "unprompted_rate": ku_t / nu_t if nu_t else None,
            "styled_entered": ks_t, "styled_n": ns_t,
            "styled_rate": ks_t / ns_t if ns_t else None,
            "lm_p90": run.envelopes.quantile(target, level),
        }

    return {
        "level": f"p{level}",
        "design": "unprompted samples on the four BOUND scenarios, "
                  ">= practice floor, truncated to the envelope window, "
                  "placed against the BOUND target's LM envelope — the "
                  "identical code path as styled entry; isolates envelope "
                  "porosity to generic AI house style on an adjacent "
                  "scenario from the imitation effect",
        "unprompted": {
            "entered": ku, "n": nu, "rate": rate_u,
            "cp_ci95": list(clopper_pearson(ku, nu)),
            "clustering": "(model x scenario) cells",
            "n_cells": len(set(u_cells)),
        },
        "styled": {
            "entered": ks, "n": ns, "rate": rate_s,
            "cp_ci95": list(clopper_pearson(ks, ns)),
            "clustering": "(model x target x condition) cells",
            "n_cells": len(set(s_cells)),
        },
        "increment": {
            "styled_minus_unprompted_pp": (
                100 * (rate_s - rate_u)
                if rate_s is not None and rate_u is not None else None),
            "cluster_bootstrap_ci95_pp": [100 * inc_ci[0], 100 * inc_ci[1]],
            "excludes_zero": bool(inc_ci[0] > 0 or inc_ci[1] < 0),
            "fisher_two_sided_p_pooled_naive": fisher_two_sided_p(ks, ns, ku, nu),
        },
        "per_model": per_model,
        "per_target": per_target,
    }


def model_matched_completion_block(
    completion_path: Path,
    entry_results: Dict[str, Any],
) -> Dict[str, Any]:
    """G2 — completion vs styled entry over MATCHED model pools only.

    Pools exclude models with no compliant completion (gpt-5: 20/20
    refusals) and models with no primary styled sample (gemma4). Ties at
    equal rates are uninformative for the sign test."""
    if not completion_path.is_file():
        return {"available": False, "completion_path": str(completion_path)}
    comp = json.loads(completion_path.read_text(encoding="utf-8"))
    out: Dict[str, Any] = {
        "available": True,
        "completion_results": str(completion_path.relative_to(REPO_ROOT)),
        "completion_generated": comp["meta"].get("generated"),
        "vocab": {},
    }
    from scipy.stats import binomtest

    for vocab in ("fwonly", "full"):
        cpm = comp["entry"][vocab]["per_model"]
        spm = entry_results["entry"][vocab]["primary"]["per_model"]
        excluded = {
            m: "no compliant completion" for m in spm if cpm.get(m, {}).get("n", 0) == 0
        }
        excluded.update({
            m: "no primary styled sample" for m in cpm
            if m not in spm and cpm[m]["n"] > 0
        })
        matched = sorted(m for m in cpm if cpm[m]["n"] > 0 and m in spm)
        rows = {}
        n_pos = n_neg = n_tie = 0
        ck_tot = cn_tot = sk_tot = sn_tot = 0
        for m in matched:
            ck, cn = cpm[m]["p90"], cpm[m]["n"]
            sk, sn = spm[m]["entered_p90"], spm[m]["n"]
            c_rate, s_rate = ck / cn, sk / sn
            if c_rate > s_rate:
                direction = "completion_higher"; n_pos += 1
            elif c_rate < s_rate:
                direction = "styled_higher"; n_neg += 1
            else:
                direction = "tie"; n_tie += 1
            ck_tot += ck; cn_tot += cn; sk_tot += sk; sn_tot += sn
            rows[m] = {
                "completion_entered": ck, "completion_n": cn,
                "completion_rate": c_rate,
                "styled_entered": sk, "styled_n": sn, "styled_rate": s_rate,
                "diff_pp": 100 * (c_rate - s_rate),
                "direction": direction,
            }
        m_inf = n_pos + n_neg
        sign_one = (float(binomtest(n_pos, m_inf, 0.5, alternative="greater").pvalue)
                    if m_inf else None)
        sign_two = (float(binomtest(n_pos, m_inf, 0.5, alternative="two-sided").pvalue)
                    if m_inf else None)
        out["vocab"][vocab] = {
            "matched_models": matched,
            "excluded_models": excluded,
            "per_model": rows,
            "sign_test": {
                "completion_higher": n_pos, "styled_higher": n_neg,
                "ties_uninformative": n_tie, "n_informative": m_inf,
                "exact_p_one_sided_greater": sign_one,
                "exact_p_two_sided": sign_two,
            },
            "pooled_matched": {
                "completion": {
                    "entered": ck_tot, "n": cn_tot,
                    "rate": ck_tot / cn_tot if cn_tot else None,
                    "cp_ci95": list(clopper_pearson(ck_tot, cn_tot)),
                },
                "styled": {
                    "entered": sk_tot, "n": sn_tot,
                    "rate": sk_tot / sn_tot if sn_tot else None,
                    "cp_ci95": list(clopper_pearson(sk_tot, sn_tot)),
                },
                "diff_pp": (100 * (ck_tot / cn_tot - sk_tot / sn_tot)
                            if cn_tot and sn_tot else None),
            },
        }
    return out


def width_analysis_block(
    run: VocabRun,
    styled: List[Dict[str, Any]],
    unp_all: List[Dict[str, Any]],
    level: int = 90,
) -> Dict[str, Any]:
    """G7 — width-vs-enterability de-circularized.

    (a) full model x target entry table (the marginals' joint);
    (b) every floor-compliant unprompted sample against EVERY shelf
        author's LM envelope: per-author entry rate vs envelope p90 width,
        correlation over all shelf authors (n > 4, no imitation prompt in
        sight — pure porosity vs width);
    (c) width-independent restatement: per-target styled median distance,
        envelope width, and the median's percentile within the target's
        own envelope (entry = P(distance <= width-quantile) is mechanically
        increasing in width at fixed distance; (c) shows the distances)."""
    from scipy.stats import spearmanr

    # (a) model x target table.
    targets = sorted({p["style_target"] for p in styled})
    models = sorted({p["model"] for p in styled})
    cell_table: Dict[str, Dict[str, Any]] = {}
    for model in models:
        row = {}
        for t in targets:
            rows = [p for p in styled
                    if p["model"] == model and p["style_target"] == t]
            x = sum(1 for p in rows
                    if p["target_distance"] <= run.envelopes.quantile(t, level))
            row[t] = {"entered": x, "n": len(rows),
                      "rate": x / len(rows) if rows else None}
        cell_table[model] = row

    # (b) all shelf authors as pseudo-targets for the unprompted samples.
    authors = sorted(run.envelopes.authors)
    per_author = {}
    widths, rates = [], []
    for a in authors:
        q = run.envelopes.quantile(a, level)
        x = sum(1 for p in unp_all if p["_all_author_distances"][a] <= q)
        n = len(unp_all)
        per_author[a] = {
            "lm_p90": q, "entered": x, "n": n, "rate": x / n if n else None,
            "median_distance": float(np.median(
                [p["_all_author_distances"][a] for p in unp_all])) if n else None,
            "is_imitation_target": a in targets,
        }
        widths.append(q)
        rates.append(x / n if n else float("nan"))
    k = len(authors)
    r = float(np.corrcoef(widths, rates)[0, 1]) if k > 2 else None
    if r is not None and k > 3 and abs(r) < 1:
        z = np.arctanh(r)
        half = 1.96 / np.sqrt(k - 3)
        r_ci = [float(np.tanh(z - half)), float(np.tanh(z + half))]
    else:
        r_ci = None
    rho, rho_p = spearmanr(widths, rates) if k > 2 else (None, None)

    # (c) width-independent restatement for the four imitation targets.
    per_target = {}
    for t in targets:
        d = [p["target_distance"] for p in styled if p["style_target"] == t]
        med = float(np.median(d))
        per_target[t] = {
            "n_styled": len(d),
            "styled_median_distance": med,
            "lm_p90_width": run.envelopes.quantile(t, level),
            "median_percentile_in_target_envelope":
                run.envelopes.authors[t].percentile_of(med),
        }
    medians = [v["styled_median_distance"] for v in per_target.values()]
    target_widths = [v["lm_p90_width"] for v in per_target.values()]
    return {
        "level": f"p{level}",
        "model_target_table": {"targets": targets, "per_model": cell_table},
        "pseudo_target_all_authors": {
            "design": "every floor-compliant unprompted sample (all "
                      "scenarios, truncated to the window) placed against "
                      "every shelf author's LM envelope; entry rate per "
                      "author vs envelope p90 width — width-vs-porosity "
                      "with the imitation prompt removed and n_authors "
                      f"= {k}, not 4",
            "n_unprompted_samples": len(unp_all),
            "n_authors": k,
            "per_author": per_author,
            "pearson_r_width_vs_rate": r,
            "pearson_r_ci95_fisher_z": r_ci,
            "pearson_ci_note": "Fisher-z CI treats authors as independent "
                               "units; the same samples are scored against "
                               "every envelope, so author rates share "
                               "sampling noise (the width axis does not)",
            "spearman_rho": float(rho) if rho is not None else None,
            "spearman_p": float(rho_p) if rho_p is not None else None,
        },
        "per_target_distance_restatement": {
            "note": "entry = P(distance <= width-quantile) is mechanically "
                    "increasing in width at fixed distance; the non-circular "
                    "content is how flat the styled distance distributions "
                    "are across targets vs how much the widths vary",
            "per_target": per_target,
            "spread_of_styled_medians": float(max(medians) - min(medians)),
            "spread_of_widths": float(max(target_widths) - min(target_widths)),
        },
    }


def e8_yardstick_block(
    e8_path: Path, seed: int, n_bootstrap: int,
) -> Dict[str, Any]:
    """G4 (reporting only; NO gate changes) — per-shelf observed self-entry
    yardsticks with cluster-naive (window CP) and work-level bootstrap CIs,
    plus the strict gate verdict exactly as committed in e8_results.json."""
    if not e8_path.is_file():
        return {"available": False, "e8_path": str(e8_path)}
    e8 = json.loads(e8_path.read_text(encoding="utf-8"))
    rng = np.random.default_rng(seed)
    shelves = {}
    for shelf in e8.get("shelves", []):
        works = []  # (inside, n_windows) pooled across authors
        for a in shelf["authors"]:
            for wk in a.get("per_work", []):
                works.append((int(wk["inside"]), int(wk["n_windows"])))
        inside = shelf["pooled_held_out_inside_p90"]
        n = shelf["pooled_held_out_n"]
        boot_ci = None
        if len(works) >= 2:
            arr = np.asarray(works, dtype=float)
            rates = np.empty(n_bootstrap)
            for b in range(n_bootstrap):
                idx = rng.integers(0, len(works), size=len(works))
                sub = arr[idx]
                rates[b] = sub[:, 0].sum() / sub[:, 1].sum()
            boot_ci = [float(np.percentile(rates, 2.5)),
                       float(np.percentile(rates, 97.5))]
        shelves[shelf["shelf"]] = {
            "inside_p90": inside,
            "n_windows": n,
            "n_works": len(works),
            "rate": shelf["pooled_held_out_rate"],
            "cp_ci95_window_naive": shelf["pooled_rate_ci95"],
            "work_bootstrap_ci95": boot_ci,
            "strict_gate_pass_as_committed": shelf["pass"],
        }
    return {
        "available": True,
        "e8_path": str(e8_path.relative_to(REPO_ROOT)),
        "overall_strict_gate_pass_as_committed": e8.get("pass"),
        "note": "REPORTING DATA ONLY — the strict gate verdict is quoted "
                "as committed (no re-adjudication). The envelopes are used "
                "with the OBSERVED self-entry rate as the comparator; the "
                "nominal-0.90 gate FAILS strictly (per-author floor, 3 of "
                "4 shelves) and the pooled rates below are the honest "
                "yardstick the entry tables are read against.",
        "shelves": shelves,
    }


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

def fmt_pct(x: Optional[float]) -> str:
    return "—" if x is None else f"{100 * x:.1f}%"


def build_markdown(results: Dict[str, Any]) -> str:
    meta = results["meta"]
    lines = [
        "# Results 2.0 — Entry/Approach Re-analysis Against Length-Matched "
        "Envelopes (LM-W)",
        "",
        f"- Generated: {meta['generated']}",
        f"- Window length: {meta['window_words']} MFW tokens; samples "
        "truncated to the window length before placement (scale-valid vs "
        "the envelopes).",
        f"- Floors (applied in MFW tokens): hard {meta['hard_floor']} "
        f"(excluded from every claim), practice {meta['practice_floor']} "
        "(below = separately reported stratum).",
        f"- Styled samples: {meta['n_styled_total']} total -> "
        f"{meta['n_styled_primary']} primary (>= practice floor), "
        f"{meta['n_styled_subfloor']} sub-floor stratum, "
        f"{meta['n_styled_hard_floor_excluded']} hard-floor EXCLUDED: "
        f"{', '.join(meta['hard_floor_excluded_files']) or 'none'}",
        f"- Models with ZERO primary-stratum styled samples (all "
        "generations below the practice floor; they appear only in the "
        f"sub-floor stratum): "
        f"{', '.join(meta['models_with_zero_primary_styled']) or 'none'}",
        "- Clustering treatment: ICC (one-way ANOVA estimator) over "
        "(model x target x condition) cells; design effect "
        "DEFF = 1 + (m_bar - 1) * ICC; CP bounds also shown at "
        "DEFF-deflated counts; cell-level bootstrap CIs as the "
        "nonparametric complement.",
        "",
    ]

    # Headline reading (numbers + honest reading, no claim formatting).
    ef = results["entry"]["full"]["primary"]["per_level"]["p90"]
    efw = results["entry"]["fwonly"]["primary"]["per_level"]["p90"]
    bf = results["human_baselines"]["full"]["entered_p90"]
    bfw = results["human_baselines"]["fwonly"]["entered_p90"]
    best_f = results["entry"]["full"]["primary"]["best_model_p90"]
    best_fw = results["entry"]["fwonly"]["primary"]["best_model_p90"]
    pc = results["human_baselines"]["positive_controls"]
    pc_rows = pc.get("shelves", {}) if pc.get("available") else {}
    lines += [
        "## Reading (LM-W entry, both vocabularies)",
        "",
        f"- Full vocab @p90: styled models pooled "
        f"{ef['entered']}/{ef['n']} ({fmt_pct(ef['rate'])}); best model "
        f"{best_f['model']} {fmt_pct(best_f['rate_p90'])}; Brinton "
        f"{bf['entered']}/{bf['n']} ({fmt_pct(bf['rate'])}); same-author "
        f"held-out yardstick "
        f"{fmt_pct(pc_rows.get('wave2', {}).get('pooled_rate'))} (wave2) / "
        f"{fmt_pct(pc_rows.get('pd', {}).get('pooled_rate'))} (pd).",
        f"- Fw-only @p90: styled models pooled "
        f"{efw['entered']}/{efw['n']} ({fmt_pct(efw['rate'])}); best model "
        f"{best_fw['model']} {fmt_pct(best_fw['rate_p90'])}; Brinton "
        f"{bfw['entered']}/{bfw['n']} ({fmt_pct(bfw['rate'])}). Note the "
        "best model's fw-only entry rate is comparable to the human "
        "pastiche's — the human-vs-machine gap at p90 is carried by the "
        "model AVERAGE, not by the best model, and per-target rates are "
        "strongly heterogeneous (see per-target tables; McCarthy's wide "
        "envelope admits most attempts, Didion/Ondaatje admit few).",
        "- The two-sided result replaces the old vacuous criterion: the "
        "same-author positive control now sits near the nominal 0.90 "
        "where the full-novel criterion put it near 0.",
        "",
    ]

    # -- a. entry ------------------------------------------------------------
    lines += ["## a. Entry against LM-W envelopes", ""]
    for vocab in ("full", "fwonly"):
        blk = results["entry"][vocab]
        primary = blk["primary"]
        lines += [
            f"### Vocabulary: {vocab} "
            f"({'top-300 mixed' if vocab == 'full' else 'function-words-only'})",
            "",
            f"Primary stratum n = {primary['n']} "
            f"({primary['n_cells']} cells; ICC of target distance "
            f"{primary['icc_target_distance']:.3f}; median target distance "
            f"{primary['median_target_distance']:.3f}).",
            "",
            "| Level | Entered | Rate | CP 95% | one-sided upper | "
            "ICC(entered) | DEFF | n_eff | DEFF-adj CP 95% | "
            "cell-bootstrap 95% | rate range over threshold CI |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for level in ENTRY_LEVELS:
            row = primary["per_level"][f"p{level}"]
            rr = row["rate_range_over_threshold_ci95"]
            lines.append(
                f"| p{level} | {row['entered']}/{row['n']} "
                f"| {fmt_pct(row['rate'])} "
                f"| [{fmt_pct(row['cp_ci95'][0])}, {fmt_pct(row['cp_ci95'][1])}] "
                f"| {fmt_pct(row['cp_one_sided_upper95'])} "
                f"| {row['icc_entered']:.3f} | {row['design_effect']:.2f} "
                f"| {row['n_eff']:.0f} "
                f"| [{fmt_pct(row['cp_ci95_design_effect_adjusted'][0])}, "
                f"{fmt_pct(row['cp_ci95_design_effect_adjusted'][1])}] "
                f"| [{fmt_pct(row['cell_bootstrap_ci95'][0])}, "
                f"{fmt_pct(row['cell_bootstrap_ci95'][1])}] "
                f"| [{fmt_pct(rr[0])}, {fmt_pct(rr[1])}] |"
            )
        lines += [
            "",
            "Per model (p90; no cross-model averaging without the best "
            "model shown):",
            "",
            "| Model | Entered@p90 | Rate | CP 95% | median target dist |",
            "|---|---|---|---|---|",
        ]
        for model, row in primary["per_model"].items():
            lines.append(
                f"| {model} | {row['entered_p90']}/{row['n']} "
                f"| {fmt_pct(row['rate_p90'])} "
                f"| [{fmt_pct(row['cp_ci95'][0])}, {fmt_pct(row['cp_ci95'][1])}] "
                f"| {row['median_target_distance']:.3f} |"
            )
        best = primary["best_model_p90"]
        lines += [
            "",
            f"Best model @p90: **{best['model']}** "
            f"{best['entered_p90']}/{best['n']} ({fmt_pct(best['rate_p90'])}).",
            "",
            "| Target | LM p90 | Entered@p90 | Rate | median target dist |",
            "|---|---|---|---|---|",
        ]
        for t, row in primary["per_target"].items():
            lines.append(
                f"| {t} | {row['lm_p90']:.3f} | {row['entered_p90']}/{row['n']} "
                f"| {fmt_pct(row['rate_p90'])} "
                f"| {row['median_target_distance']:.3f} |"
            )
        sub = blk["subfloor"]
        lines += [
            "",
            f"Per condition @p90: " + "; ".join(
                f"{c}: {r['entered_p90']}/{r['n']} ({fmt_pct(r['rate_p90'])})"
                for c, r in primary["per_condition"].items()),
            "",
            f"Sub-floor stratum (>= {meta['hard_floor']}, "
            f"< {meta['practice_floor']} tokens; placed at native length — "
            f"scale-mismatched vs the {meta['window_words']}-token envelope, "
            "reported separately, licenses no headline claim): "
            + (
                f"n = {sub['n']}; entered@p90 "
                f"{sub['per_level']['p90']['entered']}/{sub['n']} "
                f"({fmt_pct(sub['per_level']['p90']['rate'])})"
                if sub.get("per_level") else f"n = {sub['n']}"
            ),
            "",
        ]

    # -- b. human baselines ----------------------------------------------
    lines += ["## b. Human baselines on the same footing (PD shelf)", ""]
    for vocab in ("full", "fwonly"):
        pb = results["human_baselines"][vocab]
        lines += [
            f"### Brinton pastiche vs Austen LM envelope — {vocab}",
            "",
            f"- n = {pb['n_chunks']} chunks ({pb['clustering']})",
            f"- Nearest-is-Austen: {pb['nearest_is_target']}/{pb['n_chunks']} "
            f"({fmt_pct(pb['nearest_is_target'] / pb['n_chunks'])})",
            f"- Median distance to Austen: {pb['median_target_distance']:.3f} "
            f"(Austen LM p50 {pb['lm_quantiles']['p50']:.3f}, "
            f"p90 {pb['lm_quantiles']['p90']:.3f})",
            "",
            "| Level | Entered | Rate | CP 95% | rate range over threshold CI |",
            "|---|---|---|---|---|",
        ]
        for level in ENTRY_LEVELS:
            row = pb[f"entered_p{level}"]
            rr = row["rate_range_over_threshold_ci95"]
            lines.append(
                f"| p{level} | {row['entered']}/{row['n']} "
                f"| {fmt_pct(row['rate'])} "
                f"| [{fmt_pct(row['cp_ci95'][0])}, {fmt_pct(row['cp_ci95'][1])}] "
                f"| [{fmt_pct(rr[0])}, {fmt_pct(rr[1])}] |"
            )
        lines.append("")
    pc = results["human_baselines"]["positive_controls"]
    if pc.get("available"):
        lines += [
            "### Same-author positive control (E8 held-out windows, "
            "leave-work-out)",
            "",
            "| Shelf | Inside@p90 | Rate | CP 95% |",
            "|---|---|---|---|",
        ]
        for shelf, row in pc["shelves"].items():
            lines.append(
                f"| {shelf} | {row['pooled_inside_p90']}/{row['pooled_n']} "
                f"| {fmt_pct(row['pooled_rate'])} "
                f"| [{fmt_pct(row['pooled_rate_ci95'][0])}, "
                f"{fmt_pct(row['pooled_rate_ci95'][1])}] |"
            )
        lines.append("")

    # -- c. approach -------------------------------------------------------
    lines += ["## c. Approach, corrected (scenario-matched null)", ""]
    for vocab in ("full", "fwonly"):
        ap = results["approach"][vocab]
        pooled = ap["pooled"]
        lines += [
            f"### Vocabulary: {vocab}",
            "",
            "| Target (scenario) | Styled nearest-is-target | "
            "Scenario-matched null | Binomial p (greater) | "
            "cell-bootstrap 95% |",
            "|---|---|---|---|---|",
        ]
        for t, row in ap["per_target"].items():
            lines.append(
                f"| {t} ({', '.join(row['scenarios'])}) "
                f"| {row['styled_nearest_is_target']}/{row['styled_n']} "
                f"({fmt_pct(row['styled_rate'])}) "
                f"| {row['scenario_matched_null_hits']}/"
                f"{row['scenario_matched_null_n']} "
                f"({fmt_pct(row['scenario_matched_null_p0'])}) "
                f"| {row['binomial_p_greater_vs_matched_null']:.2e} "
                f"| [{fmt_pct(row['cell_bootstrap_ci95'][0])}, "
                f"{fmt_pct(row['cell_bootstrap_ci95'][1])}] |"
            )
        lines += [
            "",
            f"Pooled: {pooled['styled_nearest_is_target']}/{pooled['styled_n']} "
            f"({fmt_pct(pooled['styled_rate'])}) vs scenario-matched null "
            f"p0 = {pooled['scenario_matched_null_hits']}/"
            f"{pooled['scenario_matched_null_n']} "
            f"({fmt_pct(pooled['scenario_matched_null_p0'])}); binomial "
            f"p = {pooled['binomial_p_greater_vs_matched_null']:.2e}; "
            f"ICC {pooled['icc']:.3f}, DEFF {pooled['design_effect']:.2f}, "
            f"n_eff {pooled['n_eff']:.0f}; DEFF-adj CP "
            f"[{fmt_pct(pooled['cp_ci95_design_effect_adjusted'][0])}, "
            f"{fmt_pct(pooled['cp_ci95_design_effect_adjusted'][1])}]; "
            f"cell-bootstrap [{fmt_pct(pooled['cell_bootstrap_ci95'][0])}, "
            f"{fmt_pct(pooled['cell_bootstrap_ci95'][1])}].",
            "",
            "| Model | Nearest-is-target | Rate | CP 95% | above matched null |",
            "|---|---|---|---|---|",
        ]
        for model, row in ap["per_model"].items():
            lines.append(
                f"| {model} | {row['nearest_is_target']}/{row['n']} "
                f"| {fmt_pct(row['rate'])} "
                f"| [{fmt_pct(row['cp_ci95'][0])}, {fmt_pct(row['cp_ci95'][1])}] "
                f"| {'yes' if row['above_scenario_matched_null'] else 'NO'} |"
            )
        rvm = ap["rank_vs_metric"]
        ci_med = rvm["cell_bootstrap_ci95_median"]
        if ci_med[1] < 0:
            distance_reading = (
                "the median distance change is small but its CI sits "
                "entirely below zero: under this vocabulary, prompting also "
                "modestly closes the distance at matched length.")
        elif ci_med[0] > 0:
            distance_reading = (
                "the CI sits entirely above zero: prompting moves samples "
                "slightly AWAY in distance while raising the target's rank.")
        else:
            distance_reading = (
                "the CI brackets zero: prompting raises the target's "
                "nearest-neighbor rank without closing the function-word "
                "distance (distance-flat).")
        native = ap.get("rank_vs_metric_native_length_reference") or {}
        lines += [
            "",
            f"Best model: **{ap['best_model']['model']}** "
            f"({fmt_pct(ap['best_model']['rate'])}).",
            "",
            f"Rank-vs-metric (stated plainly): median "
            f"styled-minus-matched-unprompted distance to target = "
            f"{rvm['median_delta']:+.4f} Delta (n = {rvm['n']}; cell-bootstrap "
            f"95% [{ci_med[0]:+.4f}, {ci_med[1]:+.4f}]; "
            f"{fmt_pct(rvm['fraction_closer_than_matched_unprompted'])} of "
            f"styled samples closer than matched unprompted) — "
            f"{distance_reading}"
            + (
                f" Native-length reference (the scale-mixed draft-v0.2 "
                f"construction): {native['median_delta']:+.4f} "
                f"(n = {native['n']})."
                if native.get("median_delta") is not None else ""
            ),
            "",
        ]

    # -- d. translation ------------------------------------------------------
    tr = results["translation"]
    lines += [
        "## d. Translation bound at matched length",
        "",
        f"- Design: {tr['design']}",
        f"- Same-translator work pairs: n = "
        f"{tr['n_work_pairs_same_translator']}, median window Delta "
        f"{tr['median_same_translator']:.3f}" if tr["median_same_translator"]
        else "- Same-translator work pairs: none usable",
        f"- Cross-translator work pairs: n = "
        f"{tr['n_work_pairs_cross_translator']}, median window Delta "
        f"{tr['median_cross_translator']:.3f}" if tr["median_cross_translator"]
        else "- Cross-translator work pairs: none usable",
        f"- Cross minus same: {tr['cross_minus_same']:+.3f}; exact "
        f"permutation p (one-sided) = {tr['exact_permutation_p_one_sided']:.3f}"
        if tr["cross_minus_same"] is not None else "- Contrast not computable",
        f"- Reference (same-author cross-work window pairs, non-translated "
        f"authors): median {tr['reference_same_author_no_translator_median']:.3f} "
        f"(n = {tr['reference_n_work_pairs']} work pairs)"
        if tr["reference_same_author_no_translator_median"] else "",
        f"- **Recommendation: {tr['recommendation']}** "
        f"(supports magnitude claim vs prompting: "
        f"{tr['validity']['supports_magnitude_claim_vs_prompting']})",
        "",
    ]

    # -- e. chassis ----------------------------------------------------------
    ch = results["chassis"]
    if ch.get("available"):
        signs = ", ".join(
            f"{t} {v:+.3f}" for t, v in
            ch["per_target_mfw_median_movement"].items())
        lines += [
            "## e. Chassis restated (K10 — immobility)",
            "",
            f"- Source: `{ch['r3_path']}` (n = {ch['n']})",
            f"- MFW median movement: {ch['median_movement_delta']:+.4f} Delta "
            f"[{ch['median_movement_ci95'][0]:+.4f}, "
            f"{ch['median_movement_ci95'][1]:+.4f}]; unprompted gap "
            f"{ch['median_gap_unprompted']:.3f}; closure "
            f"{ch['gap_closure_range_pct'][0]:+.1f}% to "
            f"{ch['gap_closure_range_pct'][1]:+.1f}%; sign-test Holm "
            f"p = {ch['sign_test_p_holm']:.3f}",
            f"- Per-target MFW movement: {signs}",
            f"- Reading: {ch['reading']}",
            "",
        ]
    return "\n".join(line for line in lines if line is not None)


def build_controls_markdown(controls: Dict[str, Any]) -> str:
    meta = controls["meta"]
    lines = [
        "# Controls — v0.3 Red-Team Formalization (G1/G2/G7 + claims 1/3)",
        "",
        f"- Generated: {meta['generated']}",
        f"- Window: {meta['window_words']} MFW tokens; floors as in "
        "entry_report.md (same strata, same placement code path).",
        f"- Unprompted control pools: {meta['n_unprompted_bound']} "
        "floor-compliant unprompted samples on the four bound scenarios "
        f"(G1); {meta['n_unprompted_all']} floor-compliant unprompted "
        "samples on all scenarios (G7 pseudo-target analysis).",
        "- Provenance: same artifacts as entry_results.json (see its meta).",
        "",
        "## f1. Unprompted-entry control (G1) — the PRIMARY entry framing",
        "",
        "Unprompted samples on the bound scenario, placed against the bound "
        "target's LM envelope @p90 — identical truncation, floor, and code "
        "path as styled entry. Styled entry is read as an INCREMENT over "
        "this base rate.",
        "",
        "| Vocabulary | Unprompted @p90 | Styled @p90 | Increment (pp) | "
        "cluster-bootstrap 95% (pp) | excludes zero | Fisher p (naive) |",
        "|---|---|---|---|---|---|---|",
    ]
    for vocab in ("full", "fwonly"):
        b = controls["unprompted_entry_control"][vocab]
        u, s, inc = b["unprompted"], b["styled"], b["increment"]
        ci = inc["cluster_bootstrap_ci95_pp"]
        lines.append(
            f"| {vocab} | {u['entered']}/{u['n']} ({fmt_pct(u['rate'])}) "
            f"| {s['entered']}/{s['n']} ({fmt_pct(s['rate'])}) "
            f"| {inc['styled_minus_unprompted_pp']:+.1f} "
            f"| [{ci[0]:+.1f}, {ci[1]:+.1f}] "
            f"| {'YES' if inc['excludes_zero'] else 'no'} "
            f"| {inc['fisher_two_sided_p_pooled_naive']:.2e} |"
        )
    for vocab in ("full", "fwonly"):
        b = controls["unprompted_entry_control"][vocab]
        lines += [
            "",
            f"### Per model — {vocab}",
            "",
            "| Model | Unprompted @p90 | Styled @p90 | Increment (pp) | "
            "Fisher two-sided p |",
            "|---|---|---|---|---|",
        ]
        for model, row in b["per_model"].items():
            inc = (f"{row['increment_pp']:+.1f}"
                   if row["increment_pp"] is not None else "—")
            p = (f"{row['fisher_two_sided_p']:.3f}"
                 if row["fisher_two_sided_p"] is not None else "—")
            lines.append(
                f"| {model} | {row['unprompted_entered']}/{row['unprompted_n']} "
                f"({fmt_pct(row['unprompted_rate'])}) "
                f"| {row['styled_entered']}/{row['styled_n']} "
                f"({fmt_pct(row['styled_rate'])}) | {inc} | {p} |"
            )
        lines += [
            "",
            f"### Per target — {vocab}",
            "",
            "| Target | LM p90 | Unprompted @p90 | Styled @p90 |",
            "|---|---|---|---|",
        ]
        for t, row in b["per_target"].items():
            lines.append(
                f"| {t} | {row['lm_p90']:.3f} "
                f"| {row['unprompted_entered']}/{row['unprompted_n']} "
                f"({fmt_pct(row['unprompted_rate'])}) "
                f"| {row['styled_entered']}/{row['styled_n']} "
                f"({fmt_pct(row['styled_rate'])}) |"
            )
    lines += [
        "",
        "Reading: at full vocabulary the imitation increment is small and "
        "per-model nonsignificant — full-vocab 'entry' is mostly envelope "
        "porosity to AI house style on a deliberately adjacent scenario. "
        "The fw-only increment is large and significant; the fw-only "
        "framing is primary. Any styled rate should be quoted next to its "
        "model's unprompted base (e.g. the best styled model's base).",
        "",
    ]

    # f2. Model-matched completion.
    mm = controls["model_matched_completion"]
    if mm.get("available"):
        lines += [
            "## f2. Model-matched completion vs styled entry (G2)",
            "",
            f"- Source: `{mm['completion_results']}` (completion run "
            f"{mm['completion_generated']}).",
            "- Matched pools only: models with >= 1 compliant completion "
            "AND >= 1 primary styled sample. Pooled unmatched comparisons "
            "are composition artifacts (the best styled model refused all "
            "completions).",
            "",
        ]
        for vocab in ("fwonly", "full"):
            v = mm["vocab"][vocab]
            st = v["sign_test"]
            pm = v["pooled_matched"]
            lines += [
                f"### Vocabulary: {vocab}"
                + (" (PRIMARY)" if vocab == "fwonly" else " (content-confounded secondary)"),
                "",
                "| Model | Completion @p90 | Styled @p90 | Diff (pp) | Direction |",
                "|---|---|---|---|---|",
            ]
            for model, row in v["per_model"].items():
                lines.append(
                    f"| {model} | {row['completion_entered']}/{row['completion_n']} "
                    f"({fmt_pct(row['completion_rate'])}) "
                    f"| {row['styled_entered']}/{row['styled_n']} "
                    f"({fmt_pct(row['styled_rate'])}) "
                    f"| {row['diff_pp']:+.1f} | {row['direction']} |"
                )
            excl = "; ".join(f"{m} ({why})" for m, why in v["excluded_models"].items())
            lines += [
                "",
                f"Excluded from matching: {excl or 'none'}.",
                f"Sign test (informative models, ties dropped): "
                f"{st['completion_higher']}/{st['n_informative']} "
                f"completion-higher; exact one-sided p = "
                f"{st['exact_p_one_sided_greater']:.4f} "
                f"(two-sided {st['exact_p_two_sided']:.4f}); "
                f"{st['ties_uninformative']} tie(s) uninformative.",
                f"Pooled matched: completion "
                f"{pm['completion']['entered']}/{pm['completion']['n']} "
                f"({fmt_pct(pm['completion']['rate'])}, CP "
                f"[{fmt_pct(pm['completion']['cp_ci95'][0])}, "
                f"{fmt_pct(pm['completion']['cp_ci95'][1])}]) vs styled "
                f"{pm['styled']['entered']}/{pm['styled']['n']} "
                f"({fmt_pct(pm['styled']['rate'])}, CP "
                f"[{fmt_pct(pm['styled']['cp_ci95'][0])}, "
                f"{fmt_pct(pm['styled']['cp_ci95'][1])}]); diff "
                f"{pm['diff_pp']:+.1f} pp.",
                "",
            ]
        lines += [
            "Reading: model-matched, completion enters MORE than named-style "
            "prompting for every informative model under the primary "
            "vocabulary; the pooled 'parity' exists only because the model "
            "best at styled imitation refused the completion task. "
            "Clustered intervals for the completion pool itself are in "
            "completion_results.{json,md}.",
            "",
        ]

    # f3. Width.
    lines += ["## f3. Width vs enterability, de-circularized (G7)", ""]
    for vocab in ("fwonly", "full"):
        w = controls["width"][vocab]
        mt = w["model_target_table"]
        lines += [
            f"### (a) Model x target entry @p90 — {vocab}",
            "",
            "| Model | " + " | ".join(mt["targets"]) + " |",
            "|---|" + "---|" * len(mt["targets"]),
        ]
        for model, row in mt["per_model"].items():
            cells = []
            for t in mt["targets"]:
                c = row[t]
                cells.append(f"{c['entered']}/{c['n']}" if c["n"] else "—")
            lines.append(f"| {model} | " + " | ".join(cells) + " |")
        lines.append("")
    for vocab in ("fwonly", "full"):
        ps = controls["width"][vocab]["pseudo_target_all_authors"]
        lines += [
            f"### (b) All shelf authors as pseudo-targets (unprompted "
            f"porosity vs width) — {vocab}",
            "",
            f"n = {ps['n_unprompted_samples']} unprompted samples x "
            f"{ps['n_authors']} authors. Pearson r(width, entry rate) = "
            f"{ps['pearson_r_width_vs_rate']:+.3f} "
            f"[{ps['pearson_r_ci95_fisher_z'][0]:+.3f}, "
            f"{ps['pearson_r_ci95_fisher_z'][1]:+.3f}] (Fisher z); "
            f"Spearman rho = {ps['spearman_rho']:+.3f} "
            f"(p = {ps['spearman_p']:.4f}).",
            "",
            "| Author | LM p90 | Unprompted entered@p90 | Rate | "
            "median distance | imitation target |",
            "|---|---|---|---|---|---|",
        ]
        for a, row in sorted(ps["per_author"].items(),
                             key=lambda kv: -kv[1]["lm_p90"]):
            lines.append(
                f"| {a} | {row['lm_p90']:.3f} | {row['entered']}/{row['n']} "
                f"| {fmt_pct(row['rate'])} | {row['median_distance']:.3f} "
                f"| {'YES' if row['is_imitation_target'] else ''} |"
            )
        lines.append("")
    for vocab in ("fwonly", "full"):
        pr = controls["width"][vocab]["per_target_distance_restatement"]
        lines += [
            f"### (c) Width-independent restatement — {vocab}",
            "",
            "| Target | styled median distance | LM p90 width | "
            "median's percentile in target envelope |",
            "|---|---|---|---|",
        ]
        for t, row in pr["per_target"].items():
            lines.append(
                f"| {t} | {row['styled_median_distance']:.3f} "
                f"| {row['lm_p90_width']:.3f} "
                f"| p{row['median_percentile_in_target_envelope']:.1f} |"
            )
        lines += [
            "",
            f"Spread of styled medians {pr['spread_of_styled_medians']:.3f} "
            f"vs spread of widths {pr['spread_of_widths']:.3f}. "
            f"({pr['note']})",
            "",
        ]
    lines += [
        "## f4. E8 yardstick",
        "",
        "See `e8_yardstick.md` (same data also under `e8_yardstick` in "
        "controls_results.json). No gate changes; reporting data only.",
        "",
    ]
    return "\n".join(lines)


def build_e8_yardstick_markdown(block: Dict[str, Any], generated: str) -> str:
    lines = [
        "# E8 Yardstick — Observed Self-Entry Comparators (G4, reporting only)",
        "",
        f"- Generated: {generated}; source: `{block['e8_path']}`.",
        f"- {block['note']}",
        f"- Overall strict gate as committed: "
        f"{'PASS' if block['overall_strict_gate_pass_as_committed'] else '**FAIL**'}.",
        "",
        "| Shelf | Inside@p90 | Rate | window-naive CP 95% | "
        "work-level bootstrap 95% | n works | strict gate |",
        "|---|---|---|---|---|---|---|",
    ]
    for shelf, row in block["shelves"].items():
        wb = row["work_bootstrap_ci95"]
        lines.append(
            f"| {shelf} | {row['inside_p90']}/{row['n_windows']} "
            f"| {fmt_pct(row['rate'])} "
            f"| [{fmt_pct(row['cp_ci95_window_naive'][0])}, "
            f"{fmt_pct(row['cp_ci95_window_naive'][1])}] "
            f"| [{fmt_pct(wb[0])}, {fmt_pct(wb[1])}] "
            f"| {row['n_works']} "
            f"| {'PASS' if row['strict_gate_pass_as_committed'] else '**FAIL**'} |"
        )
    lines += [
        "",
        "Usage: entry rates are compared against these OBSERVED self-entry "
        "rates (the empirical yardstick), not against the nominal 0.90. "
        "The work-level bootstrap CI is the honest interval (windows "
        "cluster within works); the window-naive CP interval is shown so "
        "the anti-conservatism is visible rather than hidden.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Results 2.0: entry/approach re-analysis against LM-W")
    parser.add_argument("--corpus-dir", type=Path,
                        default=REPO_ROOT / "data/ai-longform")
    parser.add_argument(
        "--pastiche", type=Path,
        default=REPO_ROOT / "data/pastiche/"
                            "brinton_old_friends_new_fancies_1913.txt")
    parser.add_argument("--pastiche-target", default="austen-jane")
    parser.add_argument(
        "--r3", type=Path,
        default=REPO_ROOT / "reports/validation/author_space/"
                            "r3_dimension_gap.json")
    parser.add_argument(
        "--e8", type=Path,
        default=REPO_ROOT / "reports/validation/author_space/wave2/"
                            "e8_results.json")
    parser.add_argument(
        "--completion-results", type=Path,
        default=REPO_ROOT / "reports/validation/author_space/results2/"
                            "completion_results.json",
        help="completion_results.json from analyze_completion_condition.py "
             "(G2 model-matched comparison reads it; run that tool first)")
    parser.add_argument("--window-words", type=int, default=3000)
    parser.add_argument("--hard-floor", type=int, default=1500)
    parser.add_argument("--practice-floor", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=20260609)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument(
        "--output-dir", type=Path,
        default=REPO_ROOT / "reports/validation/author_space/results2_rerun",
        help="where to write results (default: results2_rerun, so the "
             "released evidence under results2/ stays pristine for diffing)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    w = args.window_words
    runs = {
        "full": VocabRun(
            "full",
            ARTIFACT_DIR / "author_space_v1_wave2.json",
            ARTIFACT_DIR / f"lm_envelopes_wave2_{w}w.json",
            ARTIFACT_DIR / "author_space_pd_v1.json",
            ARTIFACT_DIR / f"lm_envelopes_pd_{w}w.json",
        ),
        "fwonly": VocabRun(
            "fwonly",
            ARTIFACT_DIR / "author_space_v1_wave2_fwonly.json",
            ARTIFACT_DIR / f"lm_envelopes_wave2_fwonly_{w}w.json",
            ARTIFACT_DIR / "author_space_pd_v1_fwonly.json",
            ARTIFACT_DIR / f"lm_envelopes_pd_fwonly_{w}w.json",
        ),
    }

    records = load_corpus(args.corpus_dir)
    logger.info("Loaded %d corpus samples", len(records))

    # Floor strata in MFW tokens (the envelope unit).
    styled_records = [r for r in records if r["condition"] in STYLED_CONDITIONS]
    hard_excluded = [r for r in styled_records if r["_n_tokens"] < args.hard_floor]
    subfloor = [
        r for r in styled_records
        if args.hard_floor <= r["_n_tokens"] < args.practice_floor
    ]
    primary = [r for r in styled_records if r["_n_tokens"] >= args.practice_floor]
    logger.info(
        "Styled strata: %d primary, %d sub-floor, %d hard-floor excluded",
        len(primary), len(subfloor), len(hard_excluded))

    results: Dict[str, Any] = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "tool": "rerun_entry_analysis.py",
            "window_words": w,
            "hard_floor": args.hard_floor,
            "practice_floor": args.practice_floor,
            "floor_unit": "mfw_tokens",
            "seed": args.seed,
            "n_bootstrap": args.n_bootstrap,
            "n_corpus_samples": len(records),
            "n_styled_total": len(styled_records),
            "n_styled_primary": len(primary),
            "n_styled_subfloor": len(subfloor),
            "n_styled_hard_floor_excluded": len(hard_excluded),
            "hard_floor_excluded_files": sorted(
                r["file_path"] for r in hard_excluded),
            "subfloor_files": sorted(r["file_path"] for r in subfloor),
            "condition_counts": {
                cond: sum(1 for r in records if r["condition"] == cond)
                for cond in sorted({r["condition"] for r in records})
            },
            "out_of_scope_conditions": [
                "paraphrase (robustness battery, not styled-to-target)",
                "completion (K8 — separate generation run, separate analysis)",
            ],
            "models_with_zero_primary_styled": sorted(
                {r["model"] for r in styled_records}
                - {r["model"] for r in primary}),
            "artifacts": {k: v.provenance() for k, v in runs.items()},
        },
        "entry": {},
        "human_baselines": {},
        "approach": {},
    }

    vocab_data: Dict[str, Dict[str, Any]] = {}
    for vocab, run in runs.items():
        # Place primary (truncated to window) and unprompted for approach;
        # the floor-eligible set for entry = primary; sub-floor placed at
        # native length, reported separately.
        eligible = [
            r for r in records
            if r["condition"] == "unprompted" or r in primary
        ]
        placements = place_corpus(run, eligible, w)
        # The rank-vs-metric needs each unprompted sample's distance to all
        # four targets, not just its nearest.
        target_set = sorted({p["style_target"] for p in placements
                             if p["style_target"]})
        for p, r in zip(placements, eligible):
            if p["condition"] == "unprompted":
                tokens = r["_tokens"][:w]
                dists = author_distances(run.space, tokens)
                p["per_author_target_distance"] = {
                    t: dists[t] for t in target_set}
                # Full per-author distances for the controls block (G1
                # unprompted-entry control + G7 pseudo-target analysis);
                # underscore key — never serialized.
                p["_all_author_distances"] = dists
        styled_placed = [p for p in placements
                         if p["condition"] in STYLED_CONDITIONS]
        subfloor_placed = place_corpus(run, subfloor, w)
        vocab_data[vocab] = {"run": run, "styled": styled_placed,
                             "placements": placements}

        results["entry"][vocab] = {
            "primary": entry_block(
                run, styled_placed, "primary (>= practice floor)",
                args.seed, args.n_bootstrap),
            "subfloor": entry_block(
                run, subfloor_placed,
                "sub-floor (hard floor <= n < practice floor; native length)",
                args.seed, args.n_bootstrap),
        }
        results["human_baselines"][vocab] = pastiche_block(
            run, args.pastiche, args.pastiche_target, w,
            args.seed, args.n_bootstrap)
        results["approach"][vocab] = approach_block(
            placements, styled_placed, args.seed, args.n_bootstrap)
        results["approach"][vocab]["rank_vs_metric_native_length_reference"] = (
            native_length_rank_vs_metric(
                run, primary,
                [r for r in records if r["condition"] == "unprompted"]))

    results["human_baselines"]["positive_controls"] = positive_control_rows(
        args.e8)
    results["translation"] = translation_block(
        runs["full"], w, args.seed)
    results["chassis"] = chassis_block(args.r3)

    # -- f. controls (G1/G2/G7 + E8 yardstick) ------------------------------
    # Bound scenario -> target mapping from the primary styled records.
    scen2target: Dict[str, str] = {}
    for r in primary:
        scen2target[r["scenario_id"]] = r["style_target"]
    controls: Dict[str, Any] = {
        "meta": {
            "generated": results["meta"]["generated"],
            "tool": "rerun_entry_analysis.py (controls block)",
            "window_words": w,
            "practice_floor": args.practice_floor,
            "seed": args.seed,
            "n_bootstrap": args.n_bootstrap,
            "scenario_target_binding": scen2target,
            "n_unprompted_bound": None,   # filled below
            "n_unprompted_all": None,
        },
        "unprompted_entry_control": {},
        "width": {},
    }
    for vocab, data in vocab_data.items():
        unp_floor = [
            p for p in data["placements"]
            if p["condition"] == "unprompted"
            and p["n_tokens"] >= args.practice_floor
        ]
        unp_bound = [p for p in unp_floor if p["scenario_id"] in scen2target]
        controls["meta"]["n_unprompted_bound"] = len(unp_bound)
        controls["meta"]["n_unprompted_all"] = len(unp_floor)
        controls["unprompted_entry_control"][vocab] = (
            unprompted_entry_control_block(
                data["run"], data["styled"], unp_bound, scen2target,
                args.seed, args.n_bootstrap))
        controls["width"][vocab] = width_analysis_block(
            data["run"], data["styled"], unp_floor)
    controls["model_matched_completion"] = model_matched_completion_block(
        args.completion_results, results)
    controls["e8_yardstick"] = e8_yardstick_block(
        args.e8, args.seed, args.n_bootstrap)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.output_dir / "entry_results.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    (args.output_dir / "entry_report.md").write_text(
        build_markdown(results), encoding="utf-8")
    (args.output_dir / "controls_results.json").write_text(
        json.dumps(controls, indent=2), encoding="utf-8")
    (args.output_dir / "controls_results.md").write_text(
        build_controls_markdown(controls), encoding="utf-8")
    if controls["e8_yardstick"].get("available"):
        (args.output_dir / "e8_yardstick.md").write_text(
            build_e8_yardstick_markdown(
                controls["e8_yardstick"], results["meta"]["generated"]),
            encoding="utf-8")

    print()
    for vocab in ("full", "fwonly"):
        e = results["entry"][vocab]["primary"]["per_level"]["p90"]
        b = results["human_baselines"][vocab]["entered_p90"]
        print(f"Entry@p90 ({vocab} vocab, primary): {e['entered']}/{e['n']} "
              f"({100 * e['rate']:.1f}%)")
        print(f"Brinton@p90 ({vocab} vocab): {b['entered']}/{b['n']} "
              f"({100 * b['rate']:.1f}%)")
    for vocab in ("full", "fwonly"):
        u = controls["unprompted_entry_control"][vocab]
        print(f"G1 control ({vocab}): unprompted "
              f"{u['unprompted']['entered']}/{u['unprompted']['n']} "
              f"({100 * u['unprompted']['rate']:.1f}%) vs styled "
              f"{u['styled']['entered']}/{u['styled']['n']} "
              f"({100 * u['styled']['rate']:.1f}%); increment "
              f"{u['increment']['styled_minus_unprompted_pp']:+.1f} pp")
    print(f"Results: {out_json}")
    print(f"Controls: {args.output_dir / 'controls_results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
