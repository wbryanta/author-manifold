#!/usr/bin/env python3
"""E8 — Length-matched envelopes (LM-W) + the permanent same-author positive control.

Red-team K1 remediation (docs/redteam/RED_TEAM_SYNTHESIS.md): the
full-novel W LOO distribution is unsatisfiable at sample length (Austen's
own 3,000-word chunks enter Austen's W-p90 region 0/74), so all entry
claims must be restated against per-author LENGTH-MATCHED envelopes. This
tool:

1. Builds per-author LM envelopes at a fixed window length (default 3,000
   MFW tokens) for each requested shelf artifact: every calibrated work's
   body text is sliced into non-overlapping windows, featurized against the
   artifact's MFW block, and the envelope is the distribution of
   window -> author-centroid Burrows-Delta distances with the window's own
   work EXCLUDED from its centroid (work-level LOO — no self-inflation).
   Persisted as sidecar artifacts (``lm_envelopes_<shelf>_<L>w.json``),
   including the fw-only shelves (red-team K7: the PD fw-only run had never
   been done). When a released sidecar with the same name exists under
   data/artifacts/, the rebuilt envelope is verified against it (quantiles,
   window counts, window distances) and the result is reported.

2. Runs the E8 gate — the permanent positive control: each author's own
   held-out windows must fall inside their own LM p90 at a rate consistent
   with the nominal 0.90. Held-out means leave-WORK-out: a work's windows
   are tested against the p90 of the OTHER works' window distances
   (comparing windows against a quantile of a distribution that includes
   them would be ~0.90 by construction, i.e. circular).

   Gate per author: exact binomial (Clopper-Pearson) 95% CI on the
   held-out inside@p90 rate contains 0.90, OR rate >= 0.80 (gate floor).
   Rationale for the floor: windows cluster within works and authors have
   only 2-7 works, so the window-count binomial CI is anti-conservative
   (true CI is wider under the work-level design effect); demanding strict
   binomial consistency with 0.90 would produce false failures driven by a
   single off-style work (e.g. Stella Maris), while a rate below 0.80
   genuinely indicates the envelope is not capturing the author's own
   length-matched variation. Both readings are reported per author.

Public-release scope: only the public-domain shelves (``pd``,
``pd_fwonly``) rebuild from data shipped in this repository (the 35
PD novels under data/pd_shelf/). The contemporary shelves (``wave2``,
``wave2_fwonly``) can be requested via --shelves but require locally held
copies of the novels at the artifact-recorded text paths; their released
envelope SIDECARS ship under data/artifacts/ and are what the placement
tools read. Expected release values (paper §3.9/§9.1): PD pooled held-out
inside@p90 1375/1575 = 87.3% (full) and 1378/1575 = 87.5% (fw-only), with
the strict per-author gate FAILING on pd_fwonly (the Fitzgerald fw-only
failure) — the honest FAIL reported in the paper, so this tool exits 3.

Outputs (under --output-dir): e8_results.{json,md} + the rebuilt
lm_envelopes_*.json sidecars (--envelope-dir overrides their location).
Exit codes: 0 = all requested shelves pass; 3 = at least one author fails
the gate (results still written); 2 = usage error.

Usage:
    python3 tools/validate_lm_envelopes.py                # pd + pd_fwonly
    python3 tools/validate_lm_envelopes.py --window-words 3500
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
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from author_manifold.author_space import (
    AuthorRelativeSpace,
    LengthMatchedEnvelopes,
    LM_DEFAULT_WINDOW_WORDS,
    design_effect,
)

logger = logging.getLogger("validate_lm_envelopes")

ARTIFACT_DIR = REPO_ROOT / "data/artifacts"

# (shelf label, source artifact filename). Envelope sidecars are written as
# lm_envelopes_<label>_<window>w.json under --envelope-dir (default: the
# output dir), and verified against the released sidecars of the same name
# under data/artifacts/ when those exist.
DEFAULT_SHELVES: Tuple[Tuple[str, str], ...] = (
    ("wave2", "author_space_v1_wave2.json"),
    ("wave2_fwonly", "author_space_v1_wave2_fwonly.json"),
    ("pd", "author_space_pd_v1.json"),
    ("pd_fwonly", "author_space_pd_v1_fwonly.json"),
)
# Shelves rebuildable from data shipped in this repository (see docstring).
PUBLIC_DEFAULT_SHELVES = ("pd", "pd_fwonly")

NOMINAL_LEVEL = 90          # envelope quantile under test
NOMINAL_RATE = 0.90         # expected held-out inside rate
GATE_FLOOR = 0.80           # operative per-author floor (see module docstring)


def rel_to_repo(path: Path) -> str:
    """Repo-relative display path; absolute/outside paths pass through."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def clopper_pearson(x: float, n: float, alpha: float = 0.05) -> Tuple[float, float]:
    """Exact (Clopper-Pearson) two-sided CI for a binomial proportion.

    Implemented via beta quantiles so fractional effective counts (design-
    effect-deflated x, n) are also accepted.
    """
    from scipy.stats import beta

    if n <= 0:
        return (0.0, 1.0)
    lo = 0.0 if x <= 0 else float(beta.ppf(alpha / 2, x, n - x + 1))
    hi = 1.0 if x >= n else float(beta.ppf(1 - alpha / 2, x + 1, n - x))
    return (lo, hi)


def verify_against_released(
    envelopes: LengthMatchedEnvelopes, released_path: Path
) -> Dict[str, Any]:
    """Compare a rebuilt envelope set against a released sidecar.

    Content comparison only (per-author quantiles, window counts, and window
    distances); the meta blocks legitimately differ (generation timestamp,
    and the released sidecars pin the source artifact bytes of the run that
    built them).
    """
    released = json.loads(released_path.read_text(encoding="utf-8"))
    rel_authors = released.get("authors", {})
    mismatches: List[str] = []
    max_quantile_diff = 0.0
    if sorted(rel_authors) != sorted(envelopes.authors):
        mismatches.append(
            f"author sets differ: released {sorted(rel_authors)} vs "
            f"rebuilt {sorted(envelopes.authors)}")
    for slug, env in sorted(envelopes.authors.items()):
        rel = rel_authors.get(slug)
        if rel is None:
            continue
        if int(rel["n_windows"]) != env.n_windows:
            mismatches.append(
                f"{slug}: n_windows {env.n_windows} != released "
                f"{rel['n_windows']}")
        for level, value in env.quantiles.items():
            rel_v = float(rel["quantiles"][level])
            diff = abs(rel_v - float(value))
            max_quantile_diff = max(max_quantile_diff, diff)
            if diff > 1e-12:
                mismatches.append(
                    f"{slug}: {level} {value!r} != released {rel_v!r}")
        rel_d = [float(w["distance"]) for w in rel.get("windows", [])]
        my_d = [float(w["distance"]) for w in env.windows]
        if len(rel_d) == len(my_d):
            worst = max(
                (abs(a - b) for a, b in zip(my_d, rel_d)), default=0.0)
            if worst > 1e-12:
                mismatches.append(
                    f"{slug}: window distances differ (max |diff| {worst:g})")
    return {
        "released_sidecar": rel_to_repo(released_path),
        "match": not mismatches,
        "max_quantile_abs_diff": max_quantile_diff,
        "mismatches": mismatches,
    }


def run_shelf(
    label: str,
    artifact_path: Path,
    *,
    window_words: int,
    seed: int,
    max_windows_per_work: Optional[int],
    envelope_out: Path,
) -> Dict[str, Any]:
    """Build + persist LM envelopes for one shelf and run the E8 gate."""
    space = AuthorRelativeSpace.from_artifact(artifact_path)
    logger.info(
        "[%s] %d calibrated authors, variant=%s, vocab_filter=%s",
        label, len(space.authors), space.distance_variant,
        space.mfw.vocab_filter if space.mfw else None,
    )
    envelopes = LengthMatchedEnvelopes.build_from_space(
        space,
        window_words=window_words,
        seed=seed,
        max_windows_per_work=max_windows_per_work,
        text_root=REPO_ROOT,
        source_artifact=artifact_path,
        generated=datetime.now(timezone.utc).isoformat(),
    )
    if not envelopes.authors:
        raise SystemExit(
            f"Shelf {label!r} produced no envelopes: no work body text was "
            "resolvable. The wave2/wave2_fwonly shelves need locally held "
            "novels at the artifact-recorded text paths; only the pd shelves "
            "rebuild from data shipped in this repository (their released "
            "sidecars ship under data/artifacts/)."
        )
    envelopes.to_artifact(envelope_out)

    # Verify against the released sidecar when one ships with the repo.
    released_path = ARTIFACT_DIR / envelope_out.name
    verification: Optional[Dict[str, Any]] = None
    if released_path.is_file() and released_path.resolve() != envelope_out.resolve():
        verification = verify_against_released(envelopes, released_path)
        logger.info(
            "[%s] released-sidecar verification: %s", label,
            "MATCH" if verification["match"] else "MISMATCH",
        )

    held_out = envelopes.held_out_entry_rates(level=NOMINAL_LEVEL)
    authors: List[Dict[str, Any]] = []
    all_pass = True
    for slug in sorted(held_out):
        ho = held_out[slug]
        env = envelopes.authors[slug]
        n, inside = ho["n"], ho["inside"]
        rate = ho["rate"]
        ci = clopper_pearson(inside, n)
        ci_contains_nominal = ci[0] <= NOMINAL_RATE <= ci[1]
        passed = bool(ci_contains_nominal or (rate is not None and rate >= GATE_FLOOR))
        all_pass &= passed
        # Secondary (reported, not gated): work-level cluster-adjusted CI.
        # The held-out inside indicators cluster within works; the design-
        # effect-deflated CP CI shows whether the rate is statistically
        # consistent with 0.90 once that clustering is honored.
        indicator: List[int] = []
        labels: List[int] = []
        for work_row in ho["per_work"]:
            indicator += (
                [1] * work_row["inside"]
                + [0] * (work_row["n_windows"] - work_row["inside"])
            )
            labels += [work_row["work_index"]] * work_row["n_windows"]
        de = design_effect(indicator, labels)
        ci_adj = clopper_pearson(
            inside / de["design_effect"], n / de["design_effect"]
        )
        authors.append({
            "author": slug,
            "n_works": env.n_works,
            "n_windows": env.n_windows,
            "quantiles": env.quantiles,
            "held_out_n": n,
            "held_out_inside_p90": inside,
            "held_out_rate": rate,
            "rate_ci95": list(ci),
            "ci_contains_nominal_090": ci_contains_nominal,
            "rate_ge_gate_floor_080": bool(rate is not None and rate >= GATE_FLOOR),
            "pass": passed,
            "cluster_design_effect": de["design_effect"],
            "cluster_icc": de["icc"],
            "rate_ci95_cluster_adjusted": list(ci_adj),
            "cluster_adjusted_ci_contains_090": bool(
                ci_adj[0] <= NOMINAL_RATE <= ci_adj[1]
            ),
            "per_work": ho["per_work"],
        })
    pooled_n = sum(a["held_out_n"] for a in authors)
    pooled_inside = sum(a["held_out_inside_p90"] for a in authors)
    return {
        "shelf": label,
        "artifact": rel_to_repo(artifact_path),
        "artifact_sha256": envelopes.meta.get("source_artifact_sha256"),
        "envelope_artifact": rel_to_repo(envelope_out),
        "released_sidecar_verification": verification,
        "vocab_filter": envelopes.meta.get("vocab_filter"),
        "window_words": window_words,
        "n_authors": len(authors),
        "pooled_held_out_n": pooled_n,
        "pooled_held_out_inside_p90": pooled_inside,
        "pooled_held_out_rate": pooled_inside / pooled_n if pooled_n else None,
        "pooled_rate_ci95": list(clopper_pearson(pooled_inside, pooled_n)),
        "pass": all_pass,
        "authors": authors,
        "envelope_meta": envelopes.meta,
    }


def build_markdown(results: Dict[str, Any]) -> str:
    lines = [
        "# E8 — Length-Matched Envelopes (LM-W) + Same-Author Positive Control",
        "",
        f"- Generated: {results['meta']['generated']}",
        f"- Window length: {results['meta']['window_words']} MFW tokens; "
        f"seed {results['meta']['seed']}; "
        f"max windows/work: {results['meta']['max_windows_per_work'] or 'all'}",
        "- Envelope: window -> own-author centroid Burrows Delta, "
        "leave-one-WORK-out (window's own work never in its centroid).",
        "- Held-out test: each work's windows vs the p90 of the OTHER works' "
        "window distances (non-circular).",
        f"- Gate per author: binomial 95% CI contains {NOMINAL_RATE:.2f} "
        f"OR rate >= {GATE_FLOOR:.2f}. The floor is the operative criterion "
        "because windows cluster within works (2-7 works/author), making "
        "the window-count binomial CI anti-conservative; a single off-style "
        "work should not fail an author whose envelope otherwise captures "
        "their length-matched variation, while rate < 0.80 genuinely would.",
        "",
    ]
    for shelf in results["shelves"]:
        verdict = "PASS" if shelf["pass"] else "FAIL"
        lines += [
            f"## Shelf `{shelf['shelf']}` — **{verdict}**",
            "",
            f"- Artifact: `{shelf['artifact']}` "
            f"(sha256 `{(shelf['artifact_sha256'] or '')[:12]}…`); "
            f"vocab_filter: {shelf['vocab_filter']}",
            f"- Envelope sidecar: `{shelf['envelope_artifact']}`",
        ]
        ver = shelf.get("released_sidecar_verification")
        if ver is not None:
            lines.append(
                f"- Released-sidecar verification vs "
                f"`{ver['released_sidecar']}`: "
                f"**{'MATCH' if ver['match'] else 'MISMATCH'}** "
                f"(max |quantile diff| {ver['max_quantile_abs_diff']:g})"
            )
        lines += [
            f"- Pooled held-out inside@p90: "
            f"{shelf['pooled_held_out_inside_p90']}/{shelf['pooled_held_out_n']} "
            f"= {shelf['pooled_held_out_rate']:.3f} "
            f"(CP 95% [{shelf['pooled_rate_ci95'][0]:.3f}, "
            f"{shelf['pooled_rate_ci95'][1]:.3f}])",
            "",
            "| Author | Works | Windows | LM p50 | LM p90 | LM p95 | LM p99 "
            "| Held-out inside@p90 | Rate | CP 95% CI | Cluster-adj CI (DEFF) "
            "| Gate |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for a in shelf["authors"]:
            q = a["quantiles"]
            gate = "PASS" if a["pass"] else "**FAIL**"
            adj = a["rate_ci95_cluster_adjusted"]
            lines.append(
                f"| {a['author']} | {a['n_works']} | {a['n_windows']} "
                f"| {q['p50']:.3f} | {q['p90']:.3f} | {q['p95']:.3f} "
                f"| {q['p99']:.3f} | {a['held_out_inside_p90']}/{a['held_out_n']} "
                f"| {a['held_out_rate']:.3f} "
                f"| [{a['rate_ci95'][0]:.3f}, {a['rate_ci95'][1]:.3f}] "
                f"| [{adj[0]:.3f}, {adj[1]:.3f}] "
                f"({a['cluster_design_effect']:.1f}) "
                f"| {gate} |"
            )
        failing = [a for a in shelf["authors"] if not a["pass"]]
        if failing:
            lines += [
                "",
                "Gate-floor failures and their driver works (held-out inside "
                "per work):",
            ]
            for a in failing:
                drivers = [
                    f"{w['work']} {w['inside']}/{w['n_windows']}"
                    for w in a["per_work"] if w["inside"] < w["n_windows"]
                ]
                consistent = (
                    "cluster-adjusted CI contains 0.90"
                    if a["cluster_adjusted_ci_contains_090"]
                    else "cluster-adjusted CI does NOT contain 0.90"
                )
                lines.append(
                    f"- {a['author']}: rate {a['held_out_rate']:.3f}; "
                    f"{'; '.join(drivers)} ({consistent})"
                )
        lines.append("")
    overall = "PASS" if results["pass"] else "FAIL"
    lines += [f"**Overall E8: {overall}**", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="E8: build LM-W envelopes + same-author positive control"
    )
    parser.add_argument(
        "--window-words", type=int, default=LM_DEFAULT_WINDOW_WORDS,
        help=f"Window length in MFW tokens (default {LM_DEFAULT_WINDOW_WORDS})",
    )
    parser.add_argument("--seed", type=int, default=20260609)
    parser.add_argument(
        "--max-windows-per-work", type=int, default=None,
        help="Cap windows per work (seeded sample; default: keep all)",
    )
    parser.add_argument(
        "--shelves", default=None,
        help="Comma-separated shelf labels to run "
             f"(default: {','.join(PUBLIC_DEFAULT_SHELVES)}; also available "
             "but requiring locally held novels: wave2, wave2_fwonly)",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=REPO_ROOT / "reports/validation/author_space/pd_shelf_rerun",
    )
    parser.add_argument(
        "--envelope-dir", type=Path, default=None,
        help="Where to write the rebuilt lm_envelopes_*.json sidecars "
             "(default: the output dir)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    selected = (
        {label.strip() for label in args.shelves.split(",")}
        if args.shelves else set(PUBLIC_DEFAULT_SHELVES)
    )
    known = {label for label, _ in DEFAULT_SHELVES}
    unknown = selected - known
    if unknown:
        logger.error("Unknown shelf label(s): %s (known: %s)",
                     ", ".join(sorted(unknown)), ", ".join(sorted(known)))
        return 2
    envelope_dir = args.envelope_dir or args.output_dir
    shelves: List[Dict[str, Any]] = []
    for label, filename in DEFAULT_SHELVES:
        if label not in selected:
            continue
        artifact_path = ARTIFACT_DIR / filename
        if not artifact_path.is_file():
            logger.error("Missing artifact for shelf %s: %s", label, artifact_path)
            return 2
        envelope_out = (
            envelope_dir / f"lm_envelopes_{label}_{args.window_words}w.json"
        )
        shelves.append(run_shelf(
            label, artifact_path,
            window_words=args.window_words,
            seed=args.seed,
            max_windows_per_work=args.max_windows_per_work,
            envelope_out=envelope_out,
        ))

    results = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "tool": "validate_lm_envelopes.py",
            "window_words": args.window_words,
            "seed": args.seed,
            "max_windows_per_work": args.max_windows_per_work,
            "nominal_level": NOMINAL_LEVEL,
            "nominal_rate": NOMINAL_RATE,
            "gate_floor": GATE_FLOOR,
        },
        "experiment": "e8",
        "name": "LM-W envelopes + same-author positive control",
        "pass": all(s["pass"] for s in shelves),
        "shelves": shelves,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.output_dir / "e8_results.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    (args.output_dir / "e8_results.md").write_text(
        build_markdown(results), encoding="utf-8"
    )

    for shelf in shelves:
        ver = shelf.get("released_sidecar_verification")
        ver_str = (
            "" if ver is None else
            f"; released sidecar {'MATCH' if ver['match'] else 'MISMATCH'}"
        )
        print(f"E8 [{shelf['shelf']}]: "
              f"{'PASS' if shelf['pass'] else 'FAIL'} "
              f"(pooled {shelf['pooled_held_out_inside_p90']}/"
              f"{shelf['pooled_held_out_n']} inside@p90 = "
              f"{100 * shelf['pooled_held_out_rate']:.1f}%{ver_str})")
    print(f"Results: {out_json}")
    return 0 if results["pass"] else 3


if __name__ == "__main__":
    sys.exit(main())
