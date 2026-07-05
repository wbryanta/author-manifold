#!/usr/bin/env python3
"""R3 — dimension-level gap analysis for style-prompted AI fiction.

E4 established the headline placement result (wave-2: 9/24 style-prompted
samples have the target as nearest author, 0/24 enter the target's
within-author p90 region under MFW Delta). This tool answers the mechanistic
follow-up at the heart of the Tier 1 paper (outline §5 R3, issue #95 P2):
under style prompting, WHICH of the 18 interpretable D18 dimensions actually
move toward the target author, and which do not — versus the MFW
(most-frequent-word / Burrows Delta) chassis that never moves.

Method
------
1. Inputs: the AI long-form corpus manifest (manifest.jsonl) + per-sample D18
   baselines produced by the D18 baseline pipeline (not part of this release; ``--tier
   better --input-dir data/ai-longform --output-dir
   data/ai_baselines`` (the same feature pipeline as the gold shelf), and
   the wave-2 author-space artifact (15 authors; d18 shelf_norm + per-author
   d18 centroids + MFW block + MFW centroids).
2. Every sample is normalized into pooled-shelf sigma units per dimension:
   ``z(d) = (raw(d) - shelf_mean(d)) / shelf_std(d)`` via
   ``AuthorRelativeSpace.normalize_raw``. Target positions are the author
   centroids stored in the artifact (already in the same units).
3. For each style-conditioned sample s with target t, the matched baseline is
   the set of *unprompted* samples from the same (model, scenario). Per
   dimension d:

   - ``gap_styled(d)   = |z_s(d) - z_t(d)|``
   - ``gap_unprompted(d) = mean_i |z_{u,i}(d) - z_t(d)|`` over matched
     unprompted samples i (pilot corpus: exactly one)
   - ``movement(d) = gap_unprompted(d) - gap_styled(d)``  (positive = the
     styled sample sits closer to the target than the model's unprompted
     voice does, in pooled-shelf sigma units)
   - relative position along the unprompted->target axis (for overshoot):
     ``rel(d) = (z_s(d) - mean_z_u(d)) / (z_t(d) - mean_z_u(d))``, computed
     only when the unprompted->target gap is at least ``--min-axis-gap``
     sigma (tiny denominators are meaningless). rel > 1 means the sample
     moved PAST the target; rel > --overshoot-threshold is flagged as
     overshoot (caricature, as the parody literature predicts).

4. Aggregation per dimension across styled samples: median movement with a
   seeded bootstrap 95% CI, fraction-moved-toward, two-sided sign test
   (binomial, zero movements excluded) with Holm correction across the 18
   dimensions + MFW row, median per-sample gap closure
   ``(gap_u - gap_s)/gap_u`` (guarded by --min-axis-gap), and overshoot rate.
5. The MFW chassis gets the same treatment as a 19th row: per-sample Burrows
   Delta to the target's MFW centroid under style prompting vs the matched
   unprompted Delta (movement in Delta units; closure is unit-free and
   comparable across rows). Overshoot is undefined for a scalar distance —
   reported as n/a.

Re-runnability on the scaled corpus: the tool reads whatever rows are in the
manifest at run time, filters by condition, and skips (with counts) rows
whose baseline JSON does not exist yet — re-run generate_baselines.py with
--skip-existing first, then this tool. Style conditions default to
``style_prompted`` and ``exemplar_targeted`` (the latter for the planned C3
few-shot condition); any row whose condition is in --style-conditions and
which has a style_target that exists in the space is analyzed.

Outputs ``r3_dimension_gap.json`` + ``r3_dimension_gap.md`` under
--output-dir.

Relates: ADR-0041; TIER1_PAPER_OUTLINE.md §5 R3; issue #95 item P2.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("analyze_style_transfer_dimensions")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "backend/core") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend/core"))

# Plain-language glosses for the report (paper figure F4 axis labels).
DIMENSION_GLOSS: Dict[str, str] = {
    "lexical_density": "content-word density",
    "abstract_ratio": "abstract vs concrete vocabulary",
    "formality_index": "formality (latinate register)",
    "complexity_score": "syntactic complexity",
    "paragraph_cv": "paragraph-length variability (paragraph rhythm)",
    "sentiment_score": "overall sentiment (VADER)",
    "repetition_ratio": "deliberate word repetition",
    "metaphor_per_100": "metaphor density",
    "past_ratio": "past-tense share",
    "present_ratio": "present-tense share",
    "future_ratio": "future-tense share",
    "char_ngram_mean": "character-trigram texture",
    "function_word_ratio_extended": "function-word share (lexical chassis)",
    "self_focus_ratio": "first-person focus",
    "sentence_cv": "sentence-length variability (sentence rhythm)",
    "certainty_index": "certainty vs hedging",
    "ttr": "type-token ratio",
    "vocabulary_richness": "vocabulary richness",
    "mfw_delta": "top-300 MFW Burrows Delta (function-word chassis)",
}

MFW_ROW = "mfw_delta"

# Dimensions whose raw values depend on document length (see the
# DIMENSION_SET_V1 note in author_space.py). The matched styled-vs-unprompted
# design controls length WITHIN each comparison (both samples ~target_words),
# so movement is meaningful — but their absolute gaps to novel-length shelf
# works are length-inflated, deflating the gap-closure percentages.
LENGTH_SENSITIVE_DIMS = frozenset({
    "ttr", "vocabulary_richness", "repetition_ratio", "sentiment_score",
})


def strip_comment_lines(raw: str) -> str:
    """Body text exactly as generate_baselines.load_document derives it in
    legacy (non-manifest) mode: drop all '#'-prefixed lines, then strip.
    Keeps the MFW featurization consistent with the D18 baselines (the AI
    samples carry at most a markdown title line)."""
    return "".join(
        ln for ln in raw.splitlines(keepends=True) if not ln.startswith("#")
    ).strip()


def baseline_path_for(baselines_dir: Path, file_path: str) -> Path:
    rel = Path(file_path)
    return baselines_dir / rel.parent / f"{rel.stem}_baseline.json"


def sign_test_p(movements: np.ndarray) -> Optional[float]:
    """Two-sided sign test (exact binomial), zeros excluded."""
    from scipy.stats import binomtest

    nonzero = movements[movements != 0.0]
    if len(nonzero) == 0:
        return None
    k = int(np.sum(nonzero > 0))
    return float(binomtest(k, len(nonzero), 0.5, alternative="two-sided").pvalue)


def holm_adjust(pvals: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """Holm step-down adjustment over the non-None p-values."""
    items = [(k, v) for k, v in pvals.items() if v is not None]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    adjusted: Dict[str, Optional[float]] = {k: None for k in pvals}
    running_max = 0.0
    for rank, (key, p) in enumerate(items):
        adj = min(1.0, (m - rank) * p)
        running_max = max(running_max, adj)  # enforce monotonicity
        adjusted[key] = running_max
    return adjusted


def bootstrap_median_ci(
    values: np.ndarray, rng: np.random.Generator, n_boot: int
) -> tuple[float, float]:
    medians = np.median(
        rng.choice(values, size=(n_boot, len(values)), replace=True), axis=1
    )
    return float(np.percentile(medians, 2.5)), float(np.percentile(medians, 97.5))


def fmt(x: Optional[float], spec: str = "+.3f") -> str:
    return format(x, spec) if x is not None else "—"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R3: which D18 dimensions move toward the target under style prompting"
    )
    parser.add_argument(
        "--artifact", type=Path,
        default=REPO_ROOT / "data/artifacts/author_space_v1_wave2.json",
    )
    parser.add_argument(
        "--corpus-dir", type=Path, default=REPO_ROOT / "data/ai-longform",
    )
    parser.add_argument(
        "--manifest", type=Path, default=None,
        help="Manifest JSONL (default: <corpus-dir>/manifest.jsonl)",
    )
    parser.add_argument(
        "--baselines-dir", type=Path, default=REPO_ROOT / "data/ai_baselines",
        help="Per-sample D18 baseline JSONs mirroring the corpus layout "
             "(precomputed; D18 pipeline not part of this release)",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=REPO_ROOT / "reports/validation",
    )
    parser.add_argument("--output-prefix", default="r3_dimension_gap")
    parser.add_argument(
        "--style-conditions", nargs="+",
        default=["style_prompted", "exemplar_targeted"],
        help="Manifest conditions treated as style-targeted",
    )
    parser.add_argument(
        "--baseline-condition", default="unprompted",
        help="Manifest condition providing the matched no-style baseline",
    )
    parser.add_argument("--models", nargs="+", default=None,
                        help="Optional restriction to these model slugs")
    parser.add_argument("--min-words", type=int, default=800,
                        help="Skip samples shorter than this (matches E4)")
    parser.add_argument(
        "--min-axis-gap", type=float, default=0.25,
        help="Minimum |z_target - z_unprompted| (sigma) for the relative-"
             "position / gap-closure ratios to be computed for a sample",
    )
    parser.add_argument(
        "--overshoot-threshold", type=float, default=1.25,
        help="Relative position beyond which a sample counts as overshooting "
             "the target (1.0 = exactly at the target)",
    )
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260609)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from author_manifold.author_space import AuthorRelativeSpace, extract_features

    space = AuthorRelativeSpace.from_artifact(args.artifact)
    dims = list(space.dimensions)
    if space.mfw is None:
        logger.warning("Artifact has no MFW block — the %s contrast row will be skipped", MFW_ROW)
    manifest_path = args.manifest or (args.corpus_dir / "manifest.jsonl")
    rows = [json.loads(line) for line in open(manifest_path, encoding="utf-8")
            if line.strip()]
    # Dedup by file_path (keep last — re-generated samples supersede).
    rows = list({r["file_path"]: r for r in rows}.values())
    rng = np.random.default_rng(args.seed)

    # ------------------------------------------------------------------
    # Load + featurize every eligible manifest row.
    # ------------------------------------------------------------------
    skipped = {"missing_baseline": 0, "missing_text": 0, "short": 0,
               "model_filtered": 0, "other_condition": 0,
               "unknown_target": 0, "no_matched_unprompted": 0}
    samples: List[Dict[str, Any]] = []
    for row in rows:
        condition = row.get("condition")
        is_style = condition in args.style_conditions and row.get("style_target")
        is_base = condition == args.baseline_condition
        if not (is_style or is_base):
            skipped["other_condition"] += 1
            continue
        if args.models and row.get("model_slug") not in args.models:
            skipped["model_filtered"] += 1
            continue
        if is_style and row["style_target"] not in space.authors:
            logger.warning("style_target %r not in space; skipping %s",
                           row["style_target"], row["sample_id"])
            skipped["unknown_target"] += 1
            continue
        text_path = args.corpus_dir / row["file_path"]
        bpath = baseline_path_for(args.baselines_dir, row["file_path"])
        if not bpath.exists():
            skipped["missing_baseline"] += 1
            logger.warning("no baseline yet for %s (re-run generate_baselines.py "
                           "--skip-existing); skipping", row["file_path"])
            continue
        if not text_path.exists():
            skipped["missing_text"] += 1
            continue
        baseline = json.loads(bpath.read_text(encoding="utf-8"))
        body = strip_comment_lines(text_path.read_text(encoding="utf-8"))
        if len(body.split()) < args.min_words:
            skipped["short"] += 1
            continue
        z, coverage, imputed = space.normalize_raw(extract_features(baseline, dims))
        if imputed:
            logger.warning("%s: imputed dims %s (coverage %.2f)",
                           row["file_path"], imputed, coverage)
        samples.append({
            "row": row,
            "z": z,
            "mfw_z": space.mfw.featurize_text(body) if space.mfw else None,
        })

    styled = [s for s in samples if s["row"]["condition"] in args.style_conditions]
    unprompted_by_cell: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for s in samples:
        if s["row"]["condition"] == args.baseline_condition:
            unprompted_by_cell[(s["row"]["model_slug"], s["row"]["scenario_id"])].append(s)

    logger.info("Featurized %d samples (%d style-targeted, %d unprompted cells); skipped: %s",
                len(samples), len(styled), len(unprompted_by_cell), dict(skipped))

    # ------------------------------------------------------------------
    # Per-sample, per-dimension movement toward the target.
    # ------------------------------------------------------------------
    n_dims = len(dims)
    per_sample: List[Dict[str, Any]] = []
    for s in styled:
        row = s["row"]
        cell = (row["model_slug"], row["scenario_id"])
        matched = unprompted_by_cell.get(cell)
        if not matched:
            skipped["no_matched_unprompted"] += 1
            logger.warning("no unprompted baseline for cell %s; skipping %s",
                           cell, row["sample_id"])
            continue
        target = space.authors[row["style_target"]]
        z_t = np.asarray(target.centroid, dtype=float)
        z_s = s["z"]
        z_u_stack = np.stack([m["z"] for m in matched])           # (k, 18)
        z_u_mean = z_u_stack.mean(axis=0)
        gap_s = np.abs(z_s - z_t)
        gap_u = np.abs(z_u_stack - z_t).mean(axis=0)              # mean of gaps
        movement = gap_u - gap_s
        axis = z_t - z_u_mean
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = (z_s - z_u_mean) / axis
        rel = np.where(np.abs(axis) >= args.min_axis_gap, rel, np.nan)
        closure = np.where(np.abs(axis) >= args.min_axis_gap,
                           movement / np.where(gap_u == 0, np.nan, gap_u), np.nan)

        rec: Dict[str, Any] = {
            "model": row["model_slug"],
            "scenario_id": row["scenario_id"],
            "condition": row["condition"],
            "sample_id": row["sample_id"],
            "sample_index": row.get("sample_index"),
            "style_target": row["style_target"],
            "n_matched_unprompted": len(matched),
            "dims": {
                dims[i]: {
                    "z_styled": float(z_s[i]),
                    "z_unprompted": float(z_u_mean[i]),
                    "z_target": float(z_t[i]),
                    "gap_styled": float(gap_s[i]),
                    "gap_unprompted": float(gap_u[i]),
                    "movement": float(movement[i]),
                    "rel_position": None if np.isnan(rel[i]) else float(rel[i]),
                    "gap_closure": None if np.isnan(closure[i]) else float(closure[i]),
                }
                for i in range(n_dims)
            },
        }
        # MFW chassis row: Burrows Delta to the target's MFW centroid.
        if space.mfw is not None and target.mfw_centroid is not None:
            from author_manifold.author_space import MFWBlock

            delta_s = MFWBlock.delta(s["mfw_z"], target.mfw_centroid)
            delta_u = float(np.mean(
                [MFWBlock.delta(m["mfw_z"], target.mfw_centroid) for m in matched]
            ))
            rec["mfw"] = {
                "delta_styled": float(delta_s),
                "delta_unprompted": delta_u,
                "movement": float(delta_u - delta_s),
                "gap_closure": float((delta_u - delta_s) / delta_u) if delta_u else None,
            }
        per_sample.append(rec)

    if not per_sample:
        logger.error("No style-targeted samples with matched unprompted baselines; "
                     "nothing to analyze. Skipped: %s", dict(skipped))
        return 2

    # ------------------------------------------------------------------
    # Aggregate per dimension.
    # ------------------------------------------------------------------
    def aggregate(values_by_key: Dict[str, np.ndarray],
                  extra: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for key, movements in values_by_key.items():
            lo, hi = bootstrap_median_ci(movements, rng, args.n_bootstrap)
            nonzero = movements[movements != 0.0]
            out[key] = {
                "gloss": DIMENSION_GLOSS.get(key, key),
                "n": int(len(movements)),
                "median_movement": float(np.median(movements)),
                "median_movement_ci95": [lo, hi],
                "mean_movement": float(np.mean(movements)),
                "fraction_moved_toward": (
                    float(np.sum(nonzero > 0) / len(nonzero)) if len(nonzero) else None
                ),
                "sign_test_p": sign_test_p(movements),
                **extra.get(key, {}),
            }
        return out

    movement_by_dim = {
        d: np.array([ps["dims"][d]["movement"] for ps in per_sample]) for d in dims
    }
    extra_by_dim: Dict[str, Dict[str, Any]] = {}
    for d in dims:
        gaps_u = np.array([ps["dims"][d]["gap_unprompted"] for ps in per_sample])
        gaps_s = np.array([ps["dims"][d]["gap_styled"] for ps in per_sample])
        rels = np.array([
            ps["dims"][d]["rel_position"] for ps in per_sample
            if ps["dims"][d]["rel_position"] is not None
        ])
        closures = np.array([
            ps["dims"][d]["gap_closure"] for ps in per_sample
            if ps["dims"][d]["gap_closure"] is not None
        ])
        n_over = int(np.sum(rels > args.overshoot_threshold)) if len(rels) else 0
        extra_by_dim[d] = {
            "median_gap_unprompted": float(np.median(gaps_u)),
            "median_gap_styled": float(np.median(gaps_s)),
            "median_gap_closure": float(np.median(closures)) if len(closures) else None,
            "n_axis_eligible": int(len(rels)),
            "median_rel_position": float(np.median(rels)) if len(rels) else None,
            "n_overshoot": n_over,
            "overshoot_rate": float(n_over / len(rels)) if len(rels) else None,
            "units": "pooled-shelf sigma",
        }

    has_mfw = all("mfw" in ps for ps in per_sample) and bool(per_sample)
    if has_mfw:
        movement_by_dim[MFW_ROW] = np.array(
            [ps["mfw"]["movement"] for ps in per_sample]
        )
        mfw_closures = np.array([
            ps["mfw"]["gap_closure"] for ps in per_sample
            if ps["mfw"]["gap_closure"] is not None
        ])
        extra_by_dim[MFW_ROW] = {
            "median_gap_unprompted": float(np.median(
                [ps["mfw"]["delta_unprompted"] for ps in per_sample])),
            "median_gap_styled": float(np.median(
                [ps["mfw"]["delta_styled"] for ps in per_sample])),
            "median_gap_closure": (
                float(np.median(mfw_closures)) if len(mfw_closures) else None
            ),
            "n_axis_eligible": None,
            "median_rel_position": None,
            "n_overshoot": None,
            "overshoot_rate": None,   # undefined for a scalar distance
            "units": "burrows delta (300 MFW)",
        }

    table = aggregate(movement_by_dim, extra_by_dim)
    holm = holm_adjust({k: v["sign_test_p"] for k, v in table.items()})
    for k, v in table.items():
        v["sign_test_p_holm"] = holm[k]
        v["significant_holm_05"] = (holm[k] is not None and holm[k] < 0.05)

    ranked = sorted(
        (k for k in table if k != MFW_ROW),
        key=lambda k: table[k]["median_movement"], reverse=True,
    )

    # Per-target medians (secondary breakdown).
    per_target: Dict[str, Dict[str, Any]] = {}
    for tgt in sorted({ps["style_target"] for ps in per_sample}):
        sub = [ps for ps in per_sample if ps["style_target"] == tgt]
        per_target[tgt] = {
            "n": len(sub),
            "median_movement_by_dim": {
                d: float(np.median([ps["dims"][d]["movement"] for ps in sub]))
                for d in dims
            },
        }
        if has_mfw:
            per_target[tgt]["mfw_median_movement"] = float(
                np.median([ps["mfw"]["movement"] for ps in sub])
            )

    # ------------------------------------------------------------------
    # Plain-language reading.
    # ------------------------------------------------------------------
    transferred = [d for d in ranked
                   if table[d]["significant_holm_05"] and table[d]["median_movement"] > 0]
    moved_away = [d for d in ranked
                  if table[d]["significant_holm_05"] and table[d]["median_movement"] < 0]
    unmoved = [d for d in ranked if not table[d]["significant_holm_05"]]
    caricature = [d for d in dims
                  if (table[d]["overshoot_rate"] or 0) >= 0.25
                  and table[d]["n_axis_eligible"] and table[d]["n_axis_eligible"] >= 5]

    def gloss_list(keys: List[str]) -> str:
        return "; ".join(f"{k} ({DIMENSION_GLOSS.get(k, k)})" for k in keys) or "none"

    # Strongest movers before correction (the pilot is underpowered for
    # Holm across 19 tests; the scaled corpus is the confirmatory run).
    raw_toward = [
        d for d in ranked
        if table[d]["median_movement"] > 0
        and (table[d]["sign_test_p"] or 1.0) < 0.05
    ]
    raw_away = [
        d for d in reversed(ranked)
        if table[d]["median_movement"] < 0
        and (table[d]["sign_test_p"] or 1.0) < 0.10
    ]

    def mover_phrase(keys: List[str]) -> str:
        return "; ".join(
            f"{k} ({DIMENSION_GLOSS.get(k, k)}; {table[k]['median_movement']:+.2f} "
            f"sigma, p={table[k]['sign_test_p']:.3f})"
            for k in keys
        ) or "none"

    mfw_summary = ""
    if has_mfw:
        m = table[MFW_ROW]
        mfw_summary = (
            f"The MFW chassis barely budges by contrast: median Delta movement "
            f"{m['median_movement']:+.4f} (median gap closure "
            f"{100 * (m['median_gap_closure'] or 0):.1f}% vs the unprompted Delta of "
            f"{m['median_gap_unprompted']:.3f})."
        )
    length_note = (
        " Note: " + ", ".join(d for d in raw_toward if d in LENGTH_SENSITIVE_DIMS)
        + " are length-sensitive dimensions — their movement is real (styled and "
        "unprompted samples are length-matched) but their large absolute gaps to "
        "novel-length shelf works are partly a length artifact, so closure "
        "percentages there understate the shift."
        if any(d in LENGTH_SENSITIVE_DIMS for d in raw_toward) else ""
    )
    reading = (
        f"Across {len(per_sample)} style-targeted samples, dimensions that survive "
        f"Holm correction across all 19 tests (sign test, p<0.05): toward the target "
        f"— {gloss_list(transferred)}; away from it — {gloss_list(moved_away)}. "
        f"Before correction (pilot-scale evidence, confirmatory run = scaled corpus): "
        f"style prompting moves TOWARD the target on {mover_phrase(raw_toward)}. "
        f"It tends to move AWAY on {mover_phrase(raw_away)}.{length_note} "
        f"{mfw_summary} "
        f"Caricature watch (>=25% of axis-eligible samples overshoot past the target, "
        f"rel position > {args.overshoot_threshold}): {gloss_list(caricature)}."
    )

    results: Dict[str, Any] = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "tool": "analyze_style_transfer_dimensions.py",
            "artifact": str(args.artifact),
            "distance_variant": space.distance_variant,
            "manifest": str(manifest_path),
            "baselines_dir": str(args.baselines_dir),
            "style_conditions": args.style_conditions,
            "baseline_condition": args.baseline_condition,
            "models": args.models,
            "min_words": args.min_words,
            "min_axis_gap_sigma": args.min_axis_gap,
            "overshoot_threshold": args.overshoot_threshold,
            "n_bootstrap": args.n_bootstrap,
            "seed": args.seed,
            "n_styled_analyzed": len(per_sample),
            "n_unprompted_cells": len(unprompted_by_cell),
            "skipped": skipped,
            "movement_definition": (
                "movement(d) = mean_i|z_unprompted_i(d) - z_target(d)| - "
                "|z_styled(d) - z_target(d)|, pooled-shelf sigma units; "
                "positive = styled sample closer to target than matched "
                "unprompted; MFW row uses Burrows Delta to the target MFW "
                "centroid instead of |z| gaps"
            ),
        },
        "experiment": "r3",
        "name": "Dimension-level gap analysis under style prompting",
        "reading": reading,
        "dimensions_ranked_by_median_movement": ranked,
        "transferred_dimensions": transferred,
        "moved_away_dimensions": moved_away,
        "unmoved_dimensions": unmoved,
        "raw_toward_dimensions_uncorrected_p05": raw_toward,
        "raw_away_dimensions_uncorrected_p10": raw_away,
        "length_sensitive_dimensions": sorted(LENGTH_SENSITIVE_DIMS),
        "caricature_dimensions": caricature,
        "table": table,
        "per_target": per_target,
        "per_sample": per_sample,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.output_dir / f"{args.output_prefix}.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Markdown report.
    # ------------------------------------------------------------------
    def row_md(key: str) -> str:
        t = table[key]
        ci = t["median_movement_ci95"]
        sig = "**" if t["significant_holm_05"] else ""
        over = (
            f"{t['n_overshoot']}/{t['n_axis_eligible']}"
            if t.get("n_overshoot") is not None else "n/a"
        )
        closure = (
            f"{100 * t['median_gap_closure']:.0f}%"
            if t.get("median_gap_closure") is not None else "—"
        )
        gloss = t["gloss"] + (" †" if key in LENGTH_SENSITIVE_DIMS else "")
        return (
            f"| {sig}{key}{sig} | {gloss} | {t['median_movement']:+.3f} "
            f"[{ci[0]:+.3f}, {ci[1]:+.3f}] | {fmt(t['fraction_moved_toward'], '.2f')} | "
            f"{fmt(t['sign_test_p'], '.4f')} | {fmt(t['sign_test_p_holm'], '.4f')} | "
            f"{closure} | {over} | {t['median_gap_unprompted']:.3f} -> "
            f"{t['median_gap_styled']:.3f} |"
        )

    lines = [
        "# R3 — Where the Style-Prompting Gap Lives (Dimension-Level Movement)",
        "",
        f"- Generated: {results['meta']['generated']}",
        f"- Space artifact: {args.artifact} (variant: {space.distance_variant}, "
        f"{len(space.authors)} authors)",
        f"- Styled samples analyzed: {len(per_sample)} "
        f"(conditions: {', '.join(args.style_conditions)}); matched unprompted "
        f"cells: {len(unprompted_by_cell)}; skipped: "
        + ", ".join(f"{k}={v}" for k, v in skipped.items() if v) + "",
        f"- Movement units: pooled-shelf sigma per dimension (MFW row: Burrows "
        f"Delta over the top-300 shelf vocabulary). Positive = the "
        f"style-prompted sample sits closer to the target author than the same "
        f"model's matched unprompted sample(s).",
        "",
        "## Reading",
        "",
        reading,
        "",
        "## Ranked dimension movement (18 D18 dimensions + MFW chassis)",
        "",
        "Bold = significant after Holm correction (sign test, two-sided, "
        "alpha=0.05). Overshoot = samples whose relative position along the "
        f"unprompted->target axis exceeds {args.overshoot_threshold} (axis gap "
        f">= {args.min_axis_gap} sigma required).",
        "",
        "| Dimension | Gloss | Median movement [95% CI] | Frac toward | sign p | "
        "Holm p | Median gap closure | Overshoot | Median gap (unprompted -> styled) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    lines += [row_md(k) for k in ranked]
    if has_mfw:
        lines += ["| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                  row_md(MFW_ROW)]
    lines += [
        "",
        "## Per-target median movement (top 5 dimensions per target)",
        "",
    ]
    for tgt, data in per_target.items():
        top = sorted(data["median_movement_by_dim"].items(),
                     key=lambda kv: kv[1], reverse=True)[:5]
        tops = ", ".join(f"{d} {v:+.2f}" for d, v in top)
        mfw_part = (
            f"; MFW {data['mfw_median_movement']:+.4f}"
            if "mfw_median_movement" in data else ""
        )
        lines.append(f"- **{tgt}** (n={data['n']}): {tops}{mfw_part}")
    lines += [
        "",
        "## Method notes",
        "",
        "- Same D18 feature pipeline as the gold shelf "
        "(precomputed by the D18 baseline pipeline), normalized "
        "with the artifact's pooled shelf_norm; target position = the author's "
        "d18 centroid in the artifact.",
        "- Matched baseline = mean per-dimension gap over the same "
        "(model, scenario) unprompted samples; with one unprompted sample per "
        "cell (pilot) this is the per-sample gap.",
        "- The sign test asks only 'did it move toward the target?' per sample; "
        "the bootstrap CI (seeded, n="
        f"{args.n_bootstrap}) quantifies how big the median move is.",
        "- Overshoot (rel position > "
        f"{args.overshoot_threshold}) flags caricature: the sample moved past "
        "the target along the unprompted->target axis (parody literature "
        "predicts exaggeration of marked features).",
        "- † marks length-sensitive dimensions (ttr, vocabulary_richness, "
        "repetition_ratio, sentiment_score): styled-vs-unprompted movement is "
        "length-matched and therefore valid, but their absolute gaps to "
        "novel-length shelf works are length-inflated, so closure percentages "
        "understate the shift there.",
        "- Caveats: pilot n is small per target; dimensions are not "
        "independent (no claim of orthogonality); MFW movement is in Delta "
        "units and only the unit-free gap-closure column is directly "
        "comparable with the sigma rows.",
        "",
    ]
    out_md = args.output_dir / f"{args.output_prefix}.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nR3 dimension gap analysis: {len(per_sample)} styled samples")
    print(f"Transferred (Holm p<0.05, toward): {transferred}")
    print(f"Moved away: {moved_away}")
    if has_mfw:
        print(f"MFW chassis: median movement {table[MFW_ROW]['median_movement']:+.4f} "
              f"Delta (closure {100 * (table[MFW_ROW]['median_gap_closure'] or 0):.1f}%)")
    print(f"Results: {out_json}\n         {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
