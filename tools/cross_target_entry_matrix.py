#!/usr/bin/env python3
"""Cross-target entry matrix — the Sec. 8.12 target-specificity control, at the
ENTRY level, on the frozen styled corpus (the level where the Sec. 5.2 headline
lives).

Question. Sec. 5.2 reports fw-only styled entry 72/236 (30.5%) at p90 against an
unprompted base of 13/121 (10.7%). Sec. 8.12 concedes the increment cannot, as
instrumented, distinguish movement toward the NAMED target from generic drift
toward published-fiction register. This analysis asks the entry-level version
directly: does a sample styled FOR author X enter X's envelope more often than
samples styled for OTHER authors enter X's envelope?

    matched     P(enter X's LM envelope @p90 | styled for X)
    mismatched  P(enter X's LM envelope @p90 | styled for Y != X)

fw-only is primary (the closed-class vocabulary blocks cross-target content
leakage by construction); full-vocabulary and p95/p99 are secondary replicas.

Positive-control gate (HARD ABORT). Before any mismatched number is computed,
the script re-places the frozen corpus and asserts INTEGER equality of matched
entry with the published Results 2.0 numbers (pooled + per model, both vocabs),
threshold equality with entry_results.json, the exact selection chain
(1,072 -> 1,069 -> 318 -> 6 hard-floor -> 76 subfloor -> 236 primary), and the
G1 unprompted control (13/121 fw / 20/121 full). Any mismatch: discrepancy
table, NO outputs, exit 1. The mismatched analysis must never run on an
unfaithful harness.

Pre-specified decision rule (fixed before this script first ran; fwonly @p90
only; margin DELTA_MARGIN = 0.099 = half the +19.8 pp headline increment):
  NON_SPECIFIC    if D_hi < DELTA_MARGIN  (a >=9.9 pp matched advantage is
                  excluded, regardless of row-sign consistency -- the
                  "regardless" clause gives this predicate precedence)
  TARGET_SPECIFIC elif D_lo > 0 AND all four per-envelope row deltas > 0
  MIDDLE_ZONE     otherwise
where d_i = entered_i(own target) - mean(entered_i(other 3 targets)),
D = mean(d_i), [D_lo, D_hi] = 95% cluster bootstrap over the
(model|styled_for|condition) generation cells (pairing respected: resampling a
cell carries both arms of every sample in it). Precedence NON_SPECIFIC >
TARGET_SPECIFIC > MIDDLE_ZONE. The verdict is computed mechanically from these
predicates and never prose-adjudicated.

Scenario caveat, carried in the output: targets are design-bound to scenarios
(irrigation->mccarthy, hotel_fire->didion, estate_sale->morrison,
night_ferry->ondaatje), so mismatched styled samples necessarily come from a
different scenario than X's bound one. The unprompted cross-matrix (unprompted
samples on OTHER scenarios placed against X) is reported per row as the
register-only comparator for that confound.

Outputs (under --output-dir, default
reports/validation/author_space/results2_rerun/; the frozen results2 files
are read as references and never opened for writing):
  cross_target_matrix.json
  cross_target_matrix.md
The released evidence run is committed under results2/.

Usage (everything it reads — the 1,072-record corpus, both vocabularies'
space artifacts and envelope sidecars, and the frozen results2 references —
ships in this repository):

    python3 tools/cross_target_entry_matrix.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

# Importing the harness also bootstraps src/ onto sys.path and resolves
# REPO_ROOT to this checkout's root (rerun_entry_analysis._ensure_repo_paths).
from rerun_entry_analysis import (  # noqa: E402
    ARTIFACT_DIR,
    REPO_ROOT,
    STYLED_CONDITIONS,
    VocabRun,
    author_distances,
    clopper_pearson,
    cluster_bootstrap_ci,
    diff_cluster_bootstrap_ci,
    fisher_two_sided_p,
    load_corpus,
)

import argparse  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
from collections import Counter, defaultdict  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from typing import Any, Dict, List, Optional, Sequence, Tuple  # noqa: E402

import numpy as np  # noqa: E402

from author_manifold.author_space import design_effect, sha256_of_file  # noqa: E402

logger = logging.getLogger("cross_target_entry_matrix")

TARGETS = ("didion-joan", "mccarthy-cormac", "morrison-toni", "ondaatje-michael")
LEVELS = (90, 95, 99)
VOCABS = ("fwonly", "full")
PRIMARY_VOCAB = "fwonly"
PRIMARY_LEVEL = 90
DELTA_MARGIN = 0.099  # pre-registered: half the +19.8 pp Sec. 5.2 increment

EXPECTED_BINDING = {
    "irrigation": "mccarthy-cormac",
    "hotel_fire": "didion-joan",
    "estate_sale": "morrison-toni",
    "night_ferry": "ondaatje-michael",
}

# Frozen Results 2.0 literals (belt-and-suspenders alongside the runtime JSON):
FROZEN = {
    "selection": {
        "manifest_records": 1072,
        "loaded_records": 1069,   # load_corpus drops zero-token files
        "styled_total": 318,
        "hard_floor_excluded": 6,
        "subfloor": 76,
        "primary": 236,
        "unprompted_bound": 121,
    },
    "fwonly": {
        "pooled_p90": (72, 236),
        "per_model_p90": {
            "gpt-5": (29, 40),
            "claude-fable-5": (14, 39),
            "gpt-5-mini": (14, 40),
            "claude-opus-4-8": (9, 40),
            "claude-sonnet-4-6": (3, 32),
            "qwen3.6:35b": (3, 28),
            "claude-haiku-4-5": (0, 17),
        },
        "unprompted_p90": (13, 121),
        "unprompted_per_target_p90": {
            "didion-joan": (0, 33),
            "mccarthy-cormac": (9, 29),
            "morrison-toni": (3, 29),
            "ondaatje-michael": (1, 30),
        },
    },
    "full": {
        "pooled_p90": (48, 236),
        "per_model_p90": {
            "gpt-5": (16, 40),
            "claude-fable-5": (11, 39),
            "gpt-5-mini": (5, 40),
            "claude-opus-4-8": (9, 40),
            "claude-sonnet-4-6": (6, 32),
            "qwen3.6:35b": (0, 28),
            "claude-haiku-4-5": (1, 17),
        },
        "unprompted_p90": (20, 121),
    },
}


# ---------------------------------------------------------------------------
# Selection (must reproduce the frozen 236 exactly)
# ---------------------------------------------------------------------------

def select_strata(
    corpus_dir: Path, hard_floor: int, practice_floor: int,
) -> Tuple[List[Dict], List[Dict], Dict[str, str], List[str]]:
    """Returns (primary_styled, unprompted_bound, scenario_binding, failures)."""
    failures: List[str] = []

    raw_lines = [
        line for line in
        (corpus_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(raw_lines) != FROZEN["selection"]["manifest_records"]:
        failures.append(
            f"manifest records: mine {len(raw_lines)} != frozen "
            f"{FROZEN['selection']['manifest_records']} (stale or partial "
            f"corpus checkout?)")

    records = load_corpus(corpus_dir)
    if len(records) != FROZEN["selection"]["loaded_records"]:
        failures.append(
            f"loaded records: mine {len(records)} != frozen "
            f"{FROZEN['selection']['loaded_records']}")

    styled = [r for r in records if r["condition"] in STYLED_CONDITIONS]
    if len(styled) != FROZEN["selection"]["styled_total"]:
        failures.append(
            f"styled total: mine {len(styled)} != frozen "
            f"{FROZEN['selection']['styled_total']}")

    hard = sorted(r["file_path"] for r in styled if r["_n_tokens"] < hard_floor)
    subfloor = [r for r in styled
                if hard_floor <= r["_n_tokens"] < practice_floor]
    primary = [r for r in styled if r["_n_tokens"] >= practice_floor]

    if len(hard) != FROZEN["selection"]["hard_floor_excluded"]:
        failures.append(f"hard-floor count: mine {len(hard)} != frozen 6")
    if len(subfloor) != FROZEN["selection"]["subfloor"]:
        failures.append(f"subfloor count: mine {len(subfloor)} != frozen 76")
    if len(primary) != FROZEN["selection"]["primary"]:
        failures.append(f"primary count: mine {len(primary)} != frozen 236")

    fps = [r["file_path"] for r in primary]
    if len(set(fps)) != len(fps):
        failures.append("primary file_paths are not unique")

    binding: Dict[str, str] = {}
    for r in primary:
        prev = binding.setdefault(r["scenario_id"], r["style_target"])
        if prev != r["style_target"]:
            failures.append(
                f"scenario {r['scenario_id']} bound to both {prev} and "
                f"{r['style_target']}")
    if binding != EXPECTED_BINDING:
        failures.append(f"scenario binding: mine {binding} != {EXPECTED_BINDING}")

    unp_bound = [
        r for r in records
        if r["condition"] == "unprompted"
        and r["scenario_id"] in EXPECTED_BINDING
        and r["_n_tokens"] >= practice_floor
    ]
    if len(unp_bound) != FROZEN["selection"]["unprompted_bound"]:
        failures.append(
            f"unprompted bound pool: mine {len(unp_bound)} != frozen 121")

    return primary, unp_bound, binding, failures


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------

def place_all(
    run: VocabRun, records: Sequence[Dict], window: int,
) -> List[Dict[str, Any]]:
    """Distances to all 15 centroids + entry flags vs all 4 target envelopes."""
    thresholds = {
        t: {lvl: run.envelopes.quantile(t, lvl) for lvl in LEVELS}
        for t in TARGETS
    }
    rows = []
    for r in records:
        dists = author_distances(run.space, r["_tokens"][:window])
        nearest = min(dists, key=dists.get)
        entered = {
            t: {f"p{lvl}": bool(dists[t] <= thresholds[t][lvl])
                for lvl in LEVELS}
            for t in TARGETS
        }
        row: Dict[str, Any] = {
            "file_path": r["file_path"],
            "sample_id": r["sample_id"],
            "model": r["model"],
            "scenario_id": r["scenario_id"],
            "condition": r["condition"],
            "styled_for": r.get("style_target"),
            "n_tokens": r["_n_tokens"],
            "distances": {k: float(v) for k, v in sorted(dists.items())},
            "nearest_author": nearest,
            "entered": entered,
        }
        own = r.get("style_target")
        if own:
            others = [dists[a] for a in dists if a != own]
            row["d_target_minus_mean_others"] = float(
                dists[own] - float(np.mean(others)))
            row["d_target_minus_min_others"] = float(
                dists[own] - float(np.min(others)))
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Positive-control gate
# ---------------------------------------------------------------------------

def gate_check(
    vocab: str,
    run: VocabRun,
    styled_rows: List[Dict],
    unp_rows: List[Dict],
    entry_ref: Dict,
    controls_ref: Dict,
) -> Tuple[Dict[str, Any], List[str]]:
    failures: List[str] = []
    report: Dict[str, Any] = {"vocab": vocab}

    # Matched entry, pooled + per model, @p90 (integer equality).
    pooled_k = sum(r["entered"][r["styled_for"]]["p90"] for r in styled_rows)
    pooled = (pooled_k, len(styled_rows))
    per_model: Dict[str, Tuple[int, int]] = {}
    for m in sorted({r["model"] for r in styled_rows}):
        ms = [r for r in styled_rows if r["model"] == m]
        per_model[m] = (
            sum(r["entered"][r["styled_for"]]["p90"] for r in ms), len(ms))

    frozen_pooled = FROZEN[vocab]["pooled_p90"]
    if pooled != frozen_pooled:
        failures.append(
            f"[{vocab}] pooled matched p90: mine {pooled} != frozen(inline) "
            f"{frozen_pooled}")
    if per_model != {k: tuple(v) for k, v in FROZEN[vocab]["per_model_p90"].items()}:
        failures.append(
            f"[{vocab}] per-model matched p90: mine {per_model} != frozen(inline) "
            f"{FROZEN[vocab]['per_model_p90']}")

    ref_primary = entry_ref["entry"][vocab]["primary"]
    ref_p90 = ref_primary["per_level"]["p90"]
    if (pooled_k, len(styled_rows)) != (ref_p90["entered"], ref_p90["n"]):
        failures.append(
            f"[{vocab}] pooled matched p90: mine {pooled} != entry_results.json "
            f"({ref_p90['entered']}, {ref_p90['n']})")
    for m, (k, n) in per_model.items():
        ref_m = ref_primary["per_model"].get(m)
        if ref_m is None or (k, n) != (ref_m["entered_p90"], ref_m["n"]):
            failures.append(
                f"[{vocab}] per-model {m}: mine ({k},{n}) != entry_results.json "
                f"({ref_m and (ref_m['entered_p90'], ref_m['n'])})")

    # Threshold provenance (exact float equality: same artifact, same code path).
    thr_report = {}
    for t in TARGETS:
        mine = run.envelopes.quantile(t, 90)
        ref = ref_p90["thresholds"][t]["value"]
        thr_report[t] = {"mine": mine, "ref": ref}
        if mine != ref:
            failures.append(
                f"[{vocab}] threshold {t}: mine {mine!r} != ref {ref!r}")

    # Artifact provenance vs entry_results meta.
    ref_art = entry_ref["meta"]["artifacts"][vocab]
    prov = run.provenance()
    if sha256_of_file(run.space_path) != ref_art["space_sha256"]:
        failures.append(f"[{vocab}] space sha256 drifted from entry_results meta")
    if prov.get("envelopes_source_sha256") != ref_art["envelopes_source_sha256"]:
        failures.append(f"[{vocab}] envelope source sha256 drifted")

    # G1 unprompted control @p90 (pooled + per target).
    unp_k = 0
    unp_per_target: Dict[str, Tuple[int, int]] = {}
    for t in TARGETS:
        scen = {s for s, tt in EXPECTED_BINDING.items() if tt == t}
        pool = [r for r in unp_rows if r["scenario_id"] in scen]
        k = sum(r["entered"][t]["p90"] for r in pool)
        unp_per_target[t] = (k, len(pool))
        unp_k += k
    unp = (unp_k, len(unp_rows))
    if unp != FROZEN[vocab]["unprompted_p90"]:
        failures.append(
            f"[{vocab}] unprompted G1 p90: mine {unp} != frozen "
            f"{FROZEN[vocab]['unprompted_p90']}")
    if vocab == "fwonly":
        frozen_ut = {k: tuple(v)
                     for k, v in FROZEN["fwonly"]["unprompted_per_target_p90"].items()}
        if unp_per_target != frozen_ut:
            failures.append(
                f"[fwonly] unprompted per-target: mine {unp_per_target} != "
                f"frozen {frozen_ut}")
    ref_unp = controls_ref["unprompted_entry_control"][vocab]["unprompted"]
    ref_unp_pair = (ref_unp["entered"], ref_unp["n"])
    if unp != ref_unp_pair:
        failures.append(
            f"[{vocab}] unprompted G1: mine {unp} != controls_results.json "
            f"{ref_unp_pair}")

    report.update({
        "pooled_matched_p90": {"mine": list(pooled), "frozen": list(frozen_pooled),
                               "match": pooled == frozen_pooled},
        "per_model_matched_p90": {
            m: {"mine": list(v),
                "frozen": list(FROZEN[vocab]["per_model_p90"].get(m, (None, None))),
                "match": v == tuple(FROZEN[vocab]["per_model_p90"].get(m, ()))}
            for m, v in per_model.items()},
        "thresholds_p90": thr_report,
        "unprompted_g1_p90": {"mine": list(unp),
                              "frozen": list(FROZEN[vocab]["unprompted_p90"]),
                              "match": unp == FROZEN[vocab]["unprompted_p90"]},
        "unprompted_per_target_p90": {k: list(v) for k, v in unp_per_target.items()},
    })
    return report, failures


# ---------------------------------------------------------------------------
# Matrix + contrasts
# ---------------------------------------------------------------------------

def styled_cluster(r: Dict) -> str:
    return f"{r['model']}|{r['styled_for']}|{r['condition']}"


def row_contrasts(
    styled_rows: List[Dict], level: int, n_bootstrap: int, seed: int,
) -> Dict[str, Any]:
    lv = f"p{level}"
    out: Dict[str, Any] = {}
    for t in TARGETS:
        matched = [r for r in styled_rows if r["styled_for"] == t]
        mismatched = [r for r in styled_rows if r["styled_for"] != t]
        v1 = [1.0 if r["entered"][t][lv] else 0.0 for r in matched]
        c1 = [f"{r['model']}|{r['condition']}" for r in matched]
        v0 = [1.0 if r["entered"][t][lv] else 0.0 for r in mismatched]
        c0 = [styled_cluster(r) for r in mismatched]
        k1, n1 = int(sum(v1)), len(v1)
        k0, n0 = int(sum(v0)), len(v0)
        ci = diff_cluster_bootstrap_ci(v1, c1, v0, c0, n_bootstrap, seed)
        out[t] = {
            "matched": {"entered": k1, "n": n1,
                        "rate": k1 / n1 if n1 else None,
                        "cp95": list(clopper_pearson(k1, n1))},
            "mismatched": {"entered": k0, "n": n0,
                           "rate": k0 / n0 if n0 else None,
                           "cp95": list(clopper_pearson(k0, n0))},
            "delta": (k1 / n1 - k0 / n0) if n1 and n0 else None,
            "delta_cluster_ci95": list(ci),
            "fisher_p_naive": fisher_two_sided_p(k1, n1, k0, n0),
            "design_effect_matched": design_effect(v1, c1),
            "design_effect_mismatched": design_effect(v0, c0),
        }
    return out


def paired_pooled(
    styled_rows: List[Dict], level: int, n_bootstrap: int, seed: int,
    targets: Sequence[str] = TARGETS,
) -> Dict[str, Any]:
    """D = mean over samples of [entered(own) - mean(entered(other targets))].

    Restricted to samples whose own target is in `targets`; 'others' are the
    remaining envelopes within `targets` (used by the exclude-McCarthy
    sensitivity)."""
    lv = f"p{level}"
    rows = [r for r in styled_rows if r["styled_for"] in targets]
    d_vals, clusters = [], []
    mm_events, mm_hits = 0, 0
    for r in rows:
        own = 1.0 if r["entered"][r["styled_for"]][lv] else 0.0
        others = [1.0 if r["entered"][t][lv] else 0.0
                  for t in targets if t != r["styled_for"]]
        d_vals.append(own - float(np.mean(others)))
        clusters.append(styled_cluster(r))
        mm_events += len(others)
        mm_hits += int(sum(others))
    D = float(np.mean(d_vals))
    lo, hi = cluster_bootstrap_ci(d_vals, clusters, n_bootstrap, seed)
    k_m = int(sum(1.0 if r["entered"][r["styled_for"]][lv] else 0.0 for r in rows))
    return {
        "targets": list(targets),
        "n_samples": len(rows),
        "n_cells": len(set(clusters)),
        "matched_pooled": {"entered": k_m, "n": len(rows),
                           "rate": k_m / len(rows) if rows else None,
                           "cp95": list(clopper_pearson(k_m, len(rows)))},
        "mismatched_pooled_naive": {
            "entered": mm_hits, "pair_events": mm_events,
            "rate": mm_hits / mm_events if mm_events else None,
            "note": ("pair-events multiple-count samples; CP interval "
                     "deliberately not given at pooled level -- the paired D "
                     "below is the inferential object"),
        },
        "D": D,
        "D_cluster_ci95": [lo, hi],
    }


def unprompted_cross(
    styled_rows: List[Dict], unp_rows: List[Dict], level: int,
    n_bootstrap: int, seed: int,
) -> Dict[str, Any]:
    """Per envelope X: unprompted-on-other-scenarios entry into X (register
    comparator) vs styled-mismatched entry into X."""
    lv = f"p{level}"
    out: Dict[str, Any] = {}
    for t in TARGETS:
        own_scen = {s for s, tt in EXPECTED_BINDING.items() if tt == t}
        cross_pool = [r for r in unp_rows if r["scenario_id"] not in own_scen]
        matched_pool = [r for r in unp_rows if r["scenario_id"] in own_scen]
        vk = [1.0 if r["entered"][t][lv] else 0.0 for r in cross_pool]
        ck = [f"{r['model']}|{r['scenario_id']}" for r in cross_pool]
        k_cross, n_cross = int(sum(vk)), len(vk)
        k_match = int(sum(1 for r in matched_pool if r["entered"][t][lv]))
        sm = [r for r in styled_rows if r["styled_for"] != t]
        v_sm = [1.0 if r["entered"][t][lv] else 0.0 for r in sm]
        c_sm = [styled_cluster(r) for r in sm]
        k_sm, n_sm = int(sum(v_sm)), len(v_sm)
        ci = diff_cluster_bootstrap_ci(v_sm, c_sm, vk, ck, n_bootstrap, seed)
        out[t] = {
            "unprompted_matched_scenario": {"entered": k_match,
                                            "n": len(matched_pool)},
            "unprompted_cross_scenario": {"entered": k_cross, "n": n_cross,
                                          "rate": k_cross / n_cross if n_cross else None,
                                          "cp95": list(clopper_pearson(k_cross, n_cross))},
            "styled_mismatched": {"entered": k_sm, "n": n_sm,
                                  "rate": k_sm / n_sm if n_sm else None},
            "styled_mismatched_minus_unprompted_cross": (
                (k_sm / n_sm - k_cross / n_cross) if n_sm and n_cross else None),
            "diff_cluster_ci95": list(ci),
            "fisher_p_naive": fisher_two_sided_p(k_sm, n_sm, k_cross, n_cross),
        }
    return out


def per_model_matrix(styled_rows: List[Dict], level: int) -> Dict[str, Any]:
    lv = f"p{level}"
    out: Dict[str, Any] = {}
    for m in sorted({r["model"] for r in styled_rows}):
        out[m] = {}
        for sf in TARGETS:
            pool = [r for r in styled_rows
                    if r["model"] == m and r["styled_for"] == sf]
            if not pool:
                continue
            out[m][sf] = {
                env: {"entered": int(sum(1 for r in pool if r["entered"][env][lv])),
                      "n": len(pool)}
                for env in TARGETS
            }
    return out


def threshold_sweep(
    styled_rows: List[Dict], entry_ref: Dict, vocab: str,
) -> Dict[str, Any]:
    """Recompute matched/mismatched pooled rates + D at the lo/hi ends of the
    frozen p90 threshold CIs (distances are persisted, so this is re-thresholding
    only)."""
    thr_ci = {
        t: entry_ref["entry"][vocab]["primary"]["per_level"]["p90"]
        ["thresholds"][t]["ci95"]
        for t in TARGETS
    }
    out = {}
    for end, idx in (("lo", 0), ("hi", 1)):
        k_m = n_m = 0
        d_vals = []
        mm_hits = mm_events = 0
        for r in styled_rows:
            entered = {t: r["distances"][t] <= thr_ci[t][idx] for t in TARGETS}
            own = r["styled_for"]
            k_m += int(entered[own]); n_m += 1
            others = [1.0 if entered[t] else 0.0 for t in TARGETS if t != own]
            d_vals.append((1.0 if entered[own] else 0.0) - float(np.mean(others)))
            mm_hits += int(sum(others)); mm_events += len(others)
        out[end] = {
            "matched_rate": k_m / n_m,
            "mismatched_rate_naive": mm_hits / mm_events,
            "D": float(np.mean(d_vals)),
            "thresholds": {t: thr_ci[t][idx] for t in TARGETS},
        }
    return out


def did_block(
    styled_rows: List[Dict], unp_rows: List[Dict], level: int,
    n_bootstrap: int, seed: int,
) -> Dict[str, Any]:
    """Difference-in-differences: (styled own-minus-other) minus (unprompted
    own-scenario-minus-other-scenario), pooled at the given level. This is the
    contrast that tests target-specificity of the styled-minus-unprompted
    INCREMENT (not merely of the styled rate). Styled cells and unprompted
    cells are resampled independently (they share no samples)."""
    lv = f"p{level}"

    def styled_stats(rows):
        m_k = m_n = mm_k = mm_n = 0
        for r in rows:
            own = r["styled_for"]
            m_k += int(r["entered"][own][lv]); m_n += 1
            for t in TARGETS:
                if t != own:
                    mm_k += int(r["entered"][t][lv]); mm_n += 1
        return m_k / m_n - mm_k / mm_n if m_n and mm_n else float("nan")

    def unp_stats(rows):
        own_k = own_n = cr_k = cr_n = 0
        for r in rows:
            bound = EXPECTED_BINDING[r["scenario_id"]]
            for t in TARGETS:
                hit = int(r["entered"][t][lv])
                if t == bound:
                    own_k += hit; own_n += 1
                else:
                    cr_k += hit; cr_n += 1
        return own_k / own_n - cr_k / cr_n if own_n and cr_n else float("nan")

    point_s = styled_stats(styled_rows)
    point_u = unp_stats(unp_rows)
    point = point_s - point_u

    by_s: Dict[str, List[Dict]] = defaultdict(list)
    for r in styled_rows:
        by_s[styled_cluster(r)].append(r)
    by_u: Dict[str, List[Dict]] = defaultdict(list)
    for r in unp_rows:
        by_u[f"{r['model']}|{r['scenario_id']}"].append(r)
    cs, cu = list(by_s.values()), list(by_u.values())
    rng = np.random.default_rng(seed)
    draws = np.empty(n_bootstrap)
    for b in range(n_bootstrap):
        rs = [row for i in rng.integers(0, len(cs), len(cs)) for row in cs[i]]
        ru = [row for i in rng.integers(0, len(cu), len(cu)) for row in cu[i]]
        draws[b] = styled_stats(rs) - unp_stats(ru)
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {
        "styled_own_minus_other": point_s,
        "unprompted_own_minus_other": point_u,
        "interaction": point,
        "interaction_cluster_ci95": [float(lo), float(hi)],
        "n_styled_cells": len(cs),
        "n_unprompted_cells": len(cu),
        "note": ("interaction = (styled matched - styled mismatched) - "
                 "(unprompted bound-scenario - unprompted cross-scenario); "
                 "arms resampled independently at cell level"),
    }


# ---------------------------------------------------------------------------
# Verdict (pre-registered; mechanical)
# ---------------------------------------------------------------------------

def verdict_block(pooled: Dict, rows: Dict) -> Dict[str, Any]:
    D = pooled["D"]
    d_lo, d_hi = pooled["D_cluster_ci95"]
    deltas = {t: rows[t]["delta"] for t in TARGETS}
    pred_non_specific = bool(d_hi < DELTA_MARGIN)
    pred_target_specific = bool(d_lo > 0 and all(v > 0 for v in deltas.values()))
    if pred_non_specific:
        branch = "NON_SPECIFIC"
    elif pred_target_specific:
        branch = "TARGET_SPECIFIC"
    else:
        branch = "MIDDLE_ZONE"
    return {
        "rule": (
            "fwonly@p90 only; DELTA_MARGIN=0.099 (=half the +19.8pp headline "
            "increment). NON_SPECIFIC if D_hi<margin (precedence, per the "
            "'regardless of sign consistency' clause); else TARGET_SPECIFIC if "
            "D_lo>0 AND all four row deltas>0; else MIDDLE_ZONE."),
        "delta_margin": DELTA_MARGIN,
        "D": D,
        "D_ci95": [d_lo, d_hi],
        "row_deltas": deltas,
        "predicates": {
            "non_specific__D_hi_below_margin": pred_non_specific,
            "target_specific__D_lo_pos_and_all_rows_pos": pred_target_specific,
        },
        "branch": branch,
        "wording_consequence": {
            "TARGET_SPECIFIC": (
                "named-target framing stands; Sec. 8.12 gains a resolution "
                "sentence citing this matrix"),
            "NON_SPECIFIC": (
                "rename the Sec. 5.2 noun (entry into the published-fiction "
                "register as instrumented by the target envelopes); abstract "
                "downgraded; Sec. 8.12 promoted to a finding"),
            "MIDDLE_ZONE": (
                "frozen numbers stand; noun renamed to the explicit upper "
                "bound ('fw-only envelope entry, an upper bound on "
                "target-specific imitation'); matrix rows quoted without a "
                "specificity verdict"),
        }[branch],
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_md(res: Dict[str, Any]) -> str:
    fw = res["matrix"]["fwonly"]["p90"]
    v = res["verdict"]
    lines = [
        "# Cross-target entry matrix (Sec. 8.12 specificity control at the entry level)",
        "",
        f"*Generated {res['meta']['generated']} by cross_target_entry_matrix.py; "
        f"seed {res['meta']['seed']}, {res['meta']['n_bootstrap']} bootstrap "
        "resamples; frozen corpus and envelopes (provenance in the JSON meta). "
        "Positive-control gate: PASS (matched entry reproduces Results 2.0 "
        "exactly, pooled + per model, both vocabularies).*",
        "",
        "## fwonly @p90 (primary)",
        "",
        "| Envelope X | matched k/n (rate) | mismatched k/n (rate) | delta (pp) "
        "| delta cluster CI95 (pp) | Fisher p (naive) |",
        "|---|---|---|---|---|---|",
    ]
    for t in TARGETS:
        r = fw["rows"][t]
        m, mm = r["matched"], r["mismatched"]
        lines.append(
            f"| {t} | {m['entered']}/{m['n']} ({100*m['rate']:.1f}%) "
            f"| {mm['entered']}/{mm['n']} ({100*mm['rate']:.1f}%) "
            f"| {100*r['delta']:+.1f} "
            f"| [{100*r['delta_cluster_ci95'][0]:+.1f}, "
            f"{100*r['delta_cluster_ci95'][1]:+.1f}] "
            f"| {r['fisher_p_naive']:.2e} |")
    p = fw["pooled_paired"]
    lines += [
        "",
        f"**Paired pooled D = {100*p['D']:+.2f} pp**, cluster CI95 "
        f"[{100*p['D_cluster_ci95'][0]:+.2f}, {100*p['D_cluster_ci95'][1]:+.2f}] pp "
        f"({p['n_samples']} samples, {p['n_cells']} cells). Matched pooled "
        f"{p['matched_pooled']['entered']}/{p['matched_pooled']['n']}; "
        f"mismatched naive "
        f"{p['mismatched_pooled_naive']['entered']}/"
        f"{p['mismatched_pooled_naive']['pair_events']} pair-events.",
        "",
        "## Unprompted cross-scenario comparator (fwonly @p90)",
        "",
        "| Envelope X | unprompted matched-scenario | unprompted cross-scenario "
        "| styled mismatched | styled-mm minus unp-cross (pp) | diff CI95 (pp) |",
        "|---|---|---|---|---|---|",
    ]
    for t in TARGETS:
        u = fw["unprompted_cross"][t]
        um, uc, sm = (u["unprompted_matched_scenario"],
                      u["unprompted_cross_scenario"], u["styled_mismatched"])
        lines.append(
            f"| {t} | {um['entered']}/{um['n']} | {uc['entered']}/{uc['n']} "
            f"({100*uc['rate']:.1f}%) | {sm['entered']}/{sm['n']} "
            f"({100*sm['rate']:.1f}%) "
            f"| {100*u['styled_mismatched_minus_unprompted_cross']:+.1f} "
            f"| [{100*u['diff_cluster_ci95'][0]:+.1f}, "
            f"{100*u['diff_cluster_ci95'][1]:+.1f}] |")
    xmc = fw["sensitivities"]["exclude_mccarthy"]
    sweep = fw["sensitivities"]["threshold_sweep"]
    cond = fw["sensitivities"]["per_condition"]
    lines += [
        "",
        "## Sensitivities (fwonly @p90, non-gating)",
        "",
        f"- Exclude-McCarthy paired D: {100*xmc['D']:+.2f} pp, CI95 "
        f"[{100*xmc['D_cluster_ci95'][0]:+.2f}, {100*xmc['D_cluster_ci95'][1]:+.2f}] "
        f"(3 envelopes, {xmc['n_samples']} samples).",
        f"- Threshold-CI sweep: D = {100*sweep['lo']['D']:+.2f} pp (all-lo) to "
        f"{100*sweep['hi']['D']:+.2f} pp (all-hi); matched rate "
        f"{100*sweep['lo']['matched_rate']:.1f}%-{100*sweep['hi']['matched_rate']:.1f}%.",
    ]
    for c, blk in sorted(cond.items()):
        lines.append(
            f"- {c}: matched {blk['matched_pooled']['entered']}/"
            f"{blk['matched_pooled']['n']} "
            f"({100*blk['matched_pooled']['rate']:.1f}%), D = {100*blk['D']:+.2f} pp "
            f"CI95 [{100*blk['D_cluster_ci95'][0]:+.2f}, "
            f"{100*blk['D_cluster_ci95'][1]:+.2f}].")
    lomo = fw["sensitivities"]["leave_one_model_out"]
    lines.append("- Leave-one-model-out paired D (drop the named model):")
    for m, blk in sorted(lomo.items()):
        lines.append(
            f"    - drop {m}: D = {100*blk['D']:+.2f} pp, CI95 "
            f"[{100*blk['D_cluster_ci95'][0]:+.2f}, "
            f"{100*blk['D_cluster_ci95'][1]:+.2f}] (n={blk['n_samples']}).")
    pmp = fw["sensitivities"]["per_model_paired"]
    did = fw["sensitivities"]["difference_in_differences"]
    lines.append(
        f"- Difference-in-differences (increment-level specificity): "
        f"styled own-minus-other {100*did['styled_own_minus_other']:+.2f} pp; "
        f"unprompted own-minus-other {100*did['unprompted_own_minus_other']:+.2f} pp; "
        f"interaction {100*did['interaction']:+.2f} pp, cluster CI95 "
        f"[{100*did['interaction_cluster_ci95'][0]:+.2f}, "
        f"{100*did['interaction_cluster_ci95'][1]:+.2f}].")
    lines.append("- Per-model paired D (that model's samples only):")
    for m, blk in sorted(pmp.items()):
        lines.append(
            f"    - {m}: D = {100*blk['D']:+.2f} pp, CI95 "
            f"[{100*blk['D_cluster_ci95'][0]:+.2f}, "
            f"{100*blk['D_cluster_ci95'][1]:+.2f}] (n={blk['n_samples']}).")
    full_p = res["matrix"]["full"]["p90"]["pooled_paired"]
    lines += [
        "",
        "## Secondary replicas",
        "",
        f"- full-vocab @p90: D = {100*full_p['D']:+.2f} pp, CI95 "
        f"[{100*full_p['D_cluster_ci95'][0]:+.2f}, "
        f"{100*full_p['D_cluster_ci95'][1]:+.2f}].",
    ]
    for lvl in (95, 99):
        pp_ = res["matrix"]["fwonly"][f"p{lvl}"]["pooled_paired"]
        lines.append(
            f"- fwonly @p{lvl}: D = {100*pp_['D']:+.2f} pp, CI95 "
            f"[{100*pp_['D_cluster_ci95'][0]:+.2f}, "
            f"{100*pp_['D_cluster_ci95'][1]:+.2f}].")
    lines += [
        "",
        "## Verdict (mechanical, pre-specified)",
        "",
        f"- Rule: {v['rule']}",
        f"- D = {100*v['D']:+.2f} pp, CI95 [{100*v['D_ci95'][0]:+.2f}, "
        f"{100*v['D_ci95'][1]:+.2f}]; margin {100*v['delta_margin']:.1f} pp.",
        f"- Row deltas (pp): " + ", ".join(
            f"{t} {100*v['row_deltas'][t]:+.1f}" for t in TARGETS),
        f"- Predicates: non_specific={v['predicates']['non_specific__D_hi_below_margin']}, "
        f"target_specific={v['predicates']['target_specific__D_lo_pos_and_all_rows_pos']}",
        f"- **Branch: {v['branch']}**",
        f"- Wording consequence: {v['wording_consequence']}",
        "",
        "*Scenario caveat: targets are design-bound to scenarios, so mismatched "
        "styled samples come from other scenarios by construction; the "
        "unprompted cross-scenario column above is the register-only comparator "
        "for that confound. fw-only is primary because the closed-class "
        "vocabulary blocks cross-target content leakage by design.*",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", type=Path,
                        default=REPO_ROOT / "data/ai-longform")
    parser.add_argument("--results-dir", type=Path,
                        default=REPO_ROOT /
                        "reports/validation/author_space/results2",
                        help="frozen Results 2.0 reference files (read-only)")
    parser.add_argument("--output-dir", type=Path,
                        default=REPO_ROOT /
                        "reports/validation/author_space/results2_rerun",
                        help="where to write the matrix (default: "
                             "results2_rerun, so the released evidence under "
                             "results2/ stays pristine for diffing)")
    parser.add_argument("--window-words", type=int, default=3000)
    parser.add_argument("--hard-floor", type=int, default=1500)
    parser.add_argument("--practice-floor", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=20260609)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # Incomplete-checkout guard.
    fwonly_env = ARTIFACT_DIR / "lm_envelopes_wave2_fwonly_3000w.json"
    if not fwonly_env.exists():
        logger.error(
            "fwonly envelope artifact missing at %s -- this released "
            "sidecar ships under data/artifacts/; is the checkout complete?",
            fwonly_env)
        return 1

    entry_ref = json.loads(
        (args.results_dir / "entry_results.json").read_text(encoding="utf-8"))
    controls_ref = json.loads(
        (args.results_dir / "controls_results.json").read_text(encoding="utf-8"))

    primary, unp_bound, binding, sel_failures = select_strata(
        args.corpus_dir, args.hard_floor, args.practice_floor)

    # Frozen hard-floor file list equality.
    records_all = None  # selection already validated counts; check file list:
    hard_ref = sorted(entry_ref["meta"]["hard_floor_excluded_files"])
    # Recompute hard list from a fresh pass over the manifest-backed styled set:
    # (select_strata validated counts; we re-derive the list for the equality check)
    # -- we reuse load_corpus once more would double tokenization cost; instead
    # derive from primary+subfloor complement is impossible, so select_strata
    # returns counts only; do the list check here cheaply via manifest n_tokens?
    # No: floors are in MFW tokens. Accept the cost: one extra load is ~15s.
    records_all = load_corpus(args.corpus_dir)
    styled_all = [r for r in records_all if r["condition"] in STYLED_CONDITIONS]
    hard_mine = sorted(r["file_path"] for r in styled_all
                       if r["_n_tokens"] < args.hard_floor)
    if hard_mine != hard_ref:
        sel_failures.append(
            f"hard-floor file list mismatch: mine {hard_mine} != frozen {hard_ref}")

    runs = {
        "full": VocabRun(
            "full",
            ARTIFACT_DIR / "author_space_v1_wave2.json",
            ARTIFACT_DIR / f"lm_envelopes_wave2_{args.window_words}w.json",
            ARTIFACT_DIR / "author_space_pd_v1.json",
            ARTIFACT_DIR / f"lm_envelopes_pd_{args.window_words}w.json",
        ),
        "fwonly": VocabRun(
            "fwonly",
            ARTIFACT_DIR / "author_space_v1_wave2_fwonly.json",
            ARTIFACT_DIR / f"lm_envelopes_wave2_fwonly_{args.window_words}w.json",
            ARTIFACT_DIR / "author_space_pd_v1_fwonly.json",
            ARTIFACT_DIR / f"lm_envelopes_pd_fwonly_{args.window_words}w.json",
        ),
    }

    placements: Dict[str, Dict[str, List[Dict]]] = {}
    gate_reports: Dict[str, Any] = {}
    gate_failures: List[str] = list(sel_failures)
    for vocab in VOCABS:
        styled_rows = place_all(runs[vocab], primary, args.window_words)
        unp_rows = place_all(runs[vocab], unp_bound, args.window_words)
        placements[vocab] = {"styled": styled_rows, "unprompted": unp_rows}
        rep, fails = gate_check(
            vocab, runs[vocab], styled_rows, unp_rows, entry_ref, controls_ref)
        gate_reports[vocab] = rep
        gate_failures.extend(fails)

    if gate_failures:
        logger.error("POSITIVE-CONTROL GATE FAILED (%d failures):",
                     len(gate_failures))
        for f in gate_failures:
            logger.error("  - %s", f)
        logger.error("No outputs written.")
        return 1
    logger.info("Positive-control gate: PASS (both vocabularies)")

    matrix: Dict[str, Any] = {}
    for vocab in VOCABS:
        styled_rows = placements[vocab]["styled"]
        unp_rows = placements[vocab]["unprompted"]
        matrix[vocab] = {}
        for lvl in LEVELS:
            blk = {
                "rows": row_contrasts(styled_rows, lvl,
                                      args.n_bootstrap, args.seed),
                "pooled_paired": paired_pooled(styled_rows, lvl,
                                               args.n_bootstrap, args.seed),
                "per_model_matrix": per_model_matrix(styled_rows, lvl),
                "unprompted_cross": unprompted_cross(
                    styled_rows, unp_rows, lvl, args.n_bootstrap, args.seed),
            }
            if lvl == PRIMARY_LEVEL:
                non_mc = tuple(t for t in TARGETS if t != "mccarthy-cormac")
                models = sorted({r["model"] for r in styled_rows})
                blk["sensitivities"] = {
                    "exclude_mccarthy": paired_pooled(
                        styled_rows, lvl, args.n_bootstrap, args.seed,
                        targets=non_mc),
                    "threshold_sweep": threshold_sweep(
                        styled_rows, entry_ref, vocab),
                    "per_condition": {
                        c: paired_pooled(
                            [r for r in styled_rows if r["condition"] == c],
                            lvl, args.n_bootstrap, args.seed)
                        for c in STYLED_CONDITIONS
                    },
                    "leave_one_model_out": {
                        m: paired_pooled(
                            [r for r in styled_rows if r["model"] != m],
                            lvl, args.n_bootstrap, args.seed)
                        for m in models
                    },
                    "per_model_paired": {
                        m: paired_pooled(
                            [r for r in styled_rows if r["model"] == m],
                            lvl, args.n_bootstrap, args.seed)
                        for m in models
                    },
                    "difference_in_differences": did_block(
                        styled_rows, unp_rows, lvl,
                        args.n_bootstrap, args.seed),
                }
            matrix[vocab][f"p{lvl}"] = blk

    verdict = verdict_block(
        matrix[PRIMARY_VOCAB][f"p{PRIMARY_LEVEL}"]["pooled_paired"],
        matrix[PRIMARY_VOCAB][f"p{PRIMARY_LEVEL}"]["rows"])

    result = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "tool": "cross_target_entry_matrix.py",
            "question": ("Sec. 8.12 target-specificity at the entry level: "
                         "matched vs mismatched envelope entry on the frozen "
                         "styled primary stratum"),
            "seed": args.seed,
            "n_bootstrap": args.n_bootstrap,
            "window_words": args.window_words,
            "hard_floor": args.hard_floor,
            "practice_floor": args.practice_floor,
            "floor_unit": "mfw_tokens",
            "selection_chain": FROZEN["selection"],
            "scenario_binding": EXPECTED_BINDING,
            "positive_control": gate_reports,
            "artifacts": {v: runs[v].provenance() for v in VOCABS},
            "reference_files": {
                "entry_results.json": sha256_of_file(
                    args.results_dir / "entry_results.json"),
                "controls_results.json": sha256_of_file(
                    args.results_dir / "controls_results.json"),
                "manifest.jsonl": sha256_of_file(
                    args.corpus_dir / "manifest.jsonl"),
            },
        },
        "matrix": matrix,
        "verdict": verdict,
        "per_sample": placements["fwonly"]["styled"],
        "per_sample_full": placements["full"]["styled"],
        "per_sample_unprompted_bound": placements["fwonly"]["unprompted"],
        "per_sample_unprompted_bound_full": placements["full"]["unprompted"],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.output_dir / "cross_target_matrix.json"
    out_md = args.output_dir / "cross_target_matrix.md"
    out_json.write_text(
        json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_md(result), encoding="utf-8")
    logger.info("Wrote %s and %s", out_json, out_md)
    logger.info("VERDICT: %s (D=%+.2f pp, CI [%+.2f, %+.2f])",
                verdict["branch"], 100 * verdict["D"],
                100 * verdict["D_ci95"][0], 100 * verdict["D_ci95"][1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
