#!/usr/bin/env python3
"""
Author-Relative Space Build Tool

Builds the author-relative measurement space artifact from per-work baseline
JSONs, optionally filtered by a Control Shelf manifest. See docs/METHODOLOGY.md
for the measurement model.

Usage:
    python3 tools/build_author_space.py \
        [--baseline-dir DIR] [--manifest YAML] [--authors a,b,c] \
        [--min-works N] [--output PATH] [--report PATH]

Examples:
    # Rebuild the public-domain artifact (MFW-Delta identity variant)
    python3 tools/build_author_space.py \
        --baseline-dir data/pd_work_baselines \
        --manifest data/pd_manifest.yaml \
        --distance-variant mfw_delta \
        --output data/artifacts/author_space_pd_v1.json

    # Restrict to a subset of authors with a markdown report
    python3 tools/build_author_space.py \
        --authors austen-jane,woolf-virginia,... \
        --report reports/author_space_subset.md
"""

import sys
from pathlib import Path


def _ensure_repo_paths() -> None:
    """Ensure the repo root and src/ are importable when run uninstalled."""
    repo_root = Path(__file__).resolve().parents[1]
    for path in (repo_root / "src", repo_root):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_ensure_repo_paths()


import argparse
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from author_manifold.author_space import (
    AuthorRelativeSpace,
    DIMENSION_SET_V1,
    DISTANCE_VARIANTS,
    MFW_DEFAULT_N,
    MFW_VOCAB_FILTERS,
    load_shelf,
)

logger = logging.getLogger(__name__)

DEFAULT_BASELINE_DIR = "data/pd_work_baselines"
DEFAULT_OUTPUT = "data/artifacts/author_space_v1.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve(path_str: str) -> Path:
    """Resolve a path argument against cwd first, then repo root."""
    path = Path(path_str)
    if path.is_absolute() or path.exists():
        return path
    candidate = _repo_root() / path
    return candidate if candidate.exists() else path


def build_report(space: AuthorRelativeSpace, top_pairs: int = 5) -> str:
    """Markdown summary: work counts, W/B quantiles, closest pairs, coverage."""
    meta = space.meta
    lines: List[str] = [
        "# Author-Relative Space Build Report",
        "",
        f"- Generated: {meta.get('generated')}",
        f"- Dimension set: {meta.get('dimension_set_version')} "
        f"({len(space.dimensions)} dims)",
        f"- Calibrated authors: {meta.get('n_authors')} "
        f"({meta.get('n_works')} works); reference-only: "
        f"{meta.get('n_reference_authors')}",
        f"- Manifest: {meta.get('manifest_path') or 'none'}",
        "",
        "## Per-author work counts",
        "",
        "| Author | Works | Covariance | Flags |",
        "|---|---|---|---|",
    ]
    for slug in sorted(space.authors):
        entry = space.authors[slug]
        flags = [k for k, v in entry.flags().items() if v]
        lines.append(
            f"| {slug} | {entry.work_count} | {entry.covariance_kind} "
            f"| {', '.join(flags) or '-'} |"
        )
    for slug in sorted(space.reference_authors):
        entry = space.reference_authors[slug]
        flags = [k for k, v in entry.flags().items() if v]
        lines.append(
            f"| {slug} | {entry.work_count} | {entry.covariance_kind} "
            f"| {', '.join(flags) or '-'} |"
        )

    lines += ["", "## W/B calibration quantiles", "",
              "| Distribution | n | p5 | p25 | p50 | p75 | p95 |", "|---|---|---|---|---|---|---|"]
    for label, dist in [
        ("W loo", space.within.get("loo")),
        ("W pairs", space.within.get("pairs")),
        ("W pooled", space.within.get("pooled")),
        ("B pairs", space.between.get("pairs")),
        ("B work->centroid", space.between.get("work_to_centroid")),
    ]:
        if dist is None or dist.n == 0:
            continue
        q = dist.quantiles
        lines.append(
            f"| {label} | {dist.n} | {q['p5']:.3f} | {q['p25']:.3f} "
            f"| {q['p50']:.3f} | {q['p75']:.3f} | {q['p95']:.3f} |"
        )

    matrix = space.pairwise_author_matrix()
    pairs = sorted(
        ((a, b, matrix[a][b]) for a in matrix for b in matrix[a] if a < b),
        key=lambda t: t[2],
    )
    lines += ["", f"## Top {top_pairs} closest author pairs", ""]
    for a, b, dist in pairs[:top_pairs]:
        lines.append(f"- {a} <-> {b}: {dist:.3f}")

    lines += ["", "## Dimension coverage", ""]
    for dim, cov in (meta.get("dimension_coverage") or {}).items():
        lines.append(f"- {dim}: {cov:.0%}")
    lines.append("")
    return "\n".join(lines)


def print_summary(space: AuthorRelativeSpace, output: Path) -> None:
    meta = space.meta
    w50 = space.within["pooled"].quantiles.get("p50")
    b50 = space.between["pairs"].quantiles.get("p50")
    matrix = space.pairwise_author_matrix()
    pairs = sorted(
        ((a, b, matrix[a][b]) for a in matrix for b in matrix[a] if a < b),
        key=lambda t: t[2],
    )
    print()
    print("=" * 64)
    print("AUTHOR-RELATIVE SPACE BUILD SUMMARY")
    print("=" * 64)
    print(f"  Calibrated authors : {meta['n_authors']} ({meta['n_works']} works)")
    print(f"  Reference-only     : {meta['n_reference_authors']}")
    print(f"  Dimensions         : {len(space.dimensions)} ({meta['dimension_set_version']})")
    print(f"  Distance variant   : {meta.get('distance_variant', 'd18')} "
          f"({meta.get('distance_method')})")
    if space.mfw is not None:
        print(f"  MFW block          : top-{space.mfw.n_mfw} words "
              f"({space.mfw.tokenizer})")
    print(f"  W pooled p50       : {w50:.3f}  (loo p50 {space.within['loo'].quantiles.get('p50'):.3f})")
    print(f"  B pairs  p50       : {b50:.3f}  (work->centroid p50 "
          f"{space.between['work_to_centroid'].quantiles.get('p50'):.3f})")
    if pairs:
        a, b, dist = pairs[0]
        print(f"  Closest author pair: {a} <-> {b} ({dist:.3f})")
    print(f"  Artifact           : {output}")
    print("=" * 64)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the author-relative measurement space artifact "
                    "(ADR-0041, forthcoming)"
    )
    parser.add_argument(
        "--baseline-dir", default=DEFAULT_BASELINE_DIR,
        help=f"Directory of <author>/<work>_baseline.json (default: {DEFAULT_BASELINE_DIR})",
    )
    parser.add_argument(
        "--manifest", default=None,
        help="Control Shelf manifest YAML; filters to centroid-eligible fiction "
             "with fidelity clean/edge_cleaned",
    )
    parser.add_argument(
        "--authors", default=None,
        help="Comma-separated author slugs to restrict to (e.g. the gold shelf)",
    )
    parser.add_argument(
        "--min-works", type=int, default=3,
        help="Authors below this become reference-only, excluded from W/B "
             "calibration (default: 3)",
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT,
        help=f"Artifact output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--report", default=None,
        help="Optional markdown report output path",
    )
    parser.add_argument(
        "--seed", type=int, default=20260609,
        help="RNG seed for bootstrap CIs (default: 20260609)",
    )
    parser.add_argument(
        "--distance-variant", default="d18", choices=DISTANCE_VARIANTS,
        help="Distance variant the artifact is calibrated under (W/B "
             "distributions, place()); mfw_delta/combined need a manifest "
             "with raw-text paths (default: d18)",
    )
    parser.add_argument(
        "--mfw-n", type=int, default=None,
        help=f"MFW vocabulary size for the Burrows-Delta block (default: "
             f"{MFW_DEFAULT_N} when the variant needs it, else off)",
    )
    parser.add_argument(
        "--mfw-vocab-filter", default="none", choices=MFW_VOCAB_FILTERS,
        help="MFW vocabulary filter: 'function_words_only' restricts the "
             "candidate vocabulary to the closed-class stylometric "
             "function-word list BEFORE top-N selection (topic-confound "
             "control, issue #95 P3; default: none)",
    )
    parser.add_argument(
        "--alpha", type=float, default=0.5,
        help="Blend weight for the combined variant (default: 0.5)",
    )
    parser.add_argument(
        "--e3-results", default=None,
        help="e3_results.json providing eta^2 dimension weights "
             "(required for --distance-variant d18_weighted)",
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
    authors = [a.strip() for a in args.authors.split(",") if a.strip()] if args.authors else None

    records = load_shelf(
        baseline_dir,
        dimensions=DIMENSION_SET_V1,
        manifest_path=manifest_path,
        authors=authors,
    )
    if not records:
        parser.error(f"No work baselines loaded from {baseline_dir}")
    logger.info("Loaded %d work records from %s", len(records), baseline_dir)

    dimension_weights: Optional[Dict[str, float]] = None
    if args.distance_variant == "d18_weighted":
        if not args.e3_results:
            parser.error("--distance-variant d18_weighted requires --e3-results")
        e3_path = _resolve(args.e3_results)
        if not e3_path.is_file():
            parser.error(f"e3 results not found: {e3_path}")
        table = json.loads(e3_path.read_text(encoding="utf-8")).get(
            "dimension_table", []
        )
        dimension_weights = {
            row["dimension"]: float(row["eta_squared"]) for row in table
        }

    space = AuthorRelativeSpace.build(
        records,
        dimensions=DIMENSION_SET_V1,
        min_works=args.min_works,
        seed=args.seed,
        generated=datetime.now(timezone.utc).isoformat(),
        manifest_path=str(manifest_path) if manifest_path else None,
        mfw_n=args.mfw_n,
        distance_variant=args.distance_variant,
        alpha=args.alpha,
        dimension_weights=dimension_weights,
        mfw_vocab_filter=args.mfw_vocab_filter,
    )

    output = Path(args.output)
    if not output.is_absolute():
        output = _repo_root() / output
    space.to_artifact(output)

    if args.report:
        report_path = Path(args.report)
        if not report_path.is_absolute():
            report_path = _repo_root() / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_report(space), encoding="utf-8")
        logger.info("Wrote report: %s", report_path)

    print_summary(space, output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
