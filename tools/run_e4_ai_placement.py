#!/usr/bin/env python3
"""Experiment E4 — AI long-form fiction placement in the author-relative space.

Places every sample from the AI long-form corpus (generate_ai_longform_corpus.py)
into the validated AuthorRelativeSpace and answers:

1. Do unprompted AI samples sit off the human author manifold? Gate: every
   unprompted sample's distance to EVERY gold-shelf author exceeds that
   author's within-author p90 (no confident misattribution anywhere).
2. Do style-prompted samples ("in the manner of McCarthy") enter the target
   author's region (a measurement failure mode worth knowing) or stay
   off-manifold (the space resists style mimicry)? Reported either way,
   not gated.
3. Per-model placement profiles — substrate for the cross-model map.

Outputs reports/validation/e4_results.json + e4_report.md.

Relates: ADR-0041 experiment E4.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("run_e4_ai_placement")

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="E4: AI placement in author space")
    parser.add_argument(
        "--artifact", type=Path,
        default=REPO_ROOT / "data/artifacts/author_space_v1.json",
    )
    parser.add_argument(
        "--corpus-dir", type=Path,
        default=REPO_ROOT / "data/ai-longform",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=REPO_ROOT / "reports/validation",
    )
    parser.add_argument(
        "--min-words", type=int, default=800,
        help="Skip samples shorter than this (too short for stable MFW freqs)",
    )
    parser.add_argument(
        "--truncate-words", type=int, default=None,
        help="Length-matching control: truncate every sample to its first N "
             "words before placement (gpt-5 over-writes the ~3,500-word "
             "target by 2x+; longer samples bias closer under Delta)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from author_manifold.author_space import AuthorRelativeSpace

    space = AuthorRelativeSpace.from_artifact(args.artifact)
    manifest_path = args.corpus_dir / "manifest.jsonl"
    records = [json.loads(line) for line in open(manifest_path, encoding="utf-8")]
    logger.info("Loaded %d corpus records, space variant=%s",
                len(records), space.distance_variant)

    placements = []
    for rec in records:
        path = args.corpus_dir / rec["file_path"]
        if not path.exists():
            logger.warning("missing sample file: %s", path)
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.split()) < args.min_words:
            logger.warning("skipping short sample %s (%d words)",
                           rec["sample_id"], len(text.split()))
            continue
        if args.truncate_words:
            text = " ".join(text.split()[: args.truncate_words])
        result = space.place(text=text)
        per_author = {
            p.author: {
                "distance": p.distance,
                "w_percentile": p.w_percentile,
                "b_percentile": p.b_percentile,
            }
            for p in result.placements
        }
        nearest = result.placements[0]
        # Gate condition per sample: min over authors of W-percentile.
        # > 90 means the sample is farther from every author than that
        # author's own works at the p90 of within-author variation.
        min_w_pct = min(p.w_percentile for p in result.placements)
        placements.append({
            "model": rec["model"],
            "sample_id": rec["sample_id"],
            "condition": rec["condition"],
            "style_target": rec.get("style_target"),
            "word_count": rec["word_count"],
            "nearest_author": nearest.author,
            "nearest_distance": nearest.distance,
            "nearest_w_percentile": nearest.w_percentile,
            "min_w_percentile": min_w_pct,
            "per_author": per_author,
        })

    unprompted = [p for p in placements if p["condition"] == "unprompted"]
    # Both imitation conditions count as "styled" for the enter-rate gate;
    # exemplar (few-shot in-context passages) is the strongest imitation
    # condition (issue #95 P4; Jemama & Kumar 2025 reconciliation).
    styled = [p for p in placements
              if p["condition"] in ("style_prompted", "exemplar")]

    # Gate: every unprompted sample's nearest-author W-percentile > 90
    violations = [p for p in unprompted if p["nearest_w_percentile"] <= 90.0]
    gate_pass = len(violations) == 0 and len(unprompted) > 0

    # Style-prompted analysis: did the sample's nearest author become the target?
    style_hits = [
        p for p in styled
        if p["style_target"] and p["nearest_author"] == p["style_target"]
    ]
    style_entered = [
        p for p in styled
        if p["style_target"]
        and p["per_author"].get(p["style_target"], {}).get("w_percentile", 101) <= 90.0
    ]

    results = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "artifact": str(args.artifact),
            "distance_variant": space.distance_variant,
            "n_placed": len(placements),
        },
        "experiment": "e4",
        "name": "AI long-form fiction placement",
        "pass": gate_pass,
        "criteria": [{
            "criterion": "unprompted_nearest_author_w_percentile_gt_90_all_samples",
            "threshold": 90.0,
            "comparison": ">",
            "observed_min": (
                min(p["nearest_w_percentile"] for p in unprompted)
                if unprompted else None
            ),
            "violations": [
                {k: p[k] for k in ("model", "sample_id", "nearest_author",
                                   "nearest_w_percentile")}
                for p in violations
            ],
            "pass": gate_pass,
        }],
        "style_prompted": {
            "n": len(styled),
            "nearest_is_target": len(style_hits),
            "entered_target_region_w_p90": len(style_entered),
            "details": [
                {k: p[k] for k in ("model", "sample_id", "style_target",
                                   "nearest_author", "nearest_w_percentile")}
                | {"target_w_percentile":
                   p["per_author"].get(p["style_target"], {}).get("w_percentile")}
                for p in styled
            ],
        },
        "placements": placements,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.output_dir / "e4_results.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Markdown report
    lines = [
        "# E4 — AI Long-Form Fiction Placement",
        "",
        f"- Generated: {results['meta']['generated']}",
        f"- Space variant: {space.distance_variant}; samples placed: {len(placements)}",
        f"- **Gate (unprompted off-manifold): {'PASS' if gate_pass else 'FAIL'}**",
        "",
        "## Unprompted samples (per model)",
        "",
        "| Model | Sample | Nearest author | dist | nearest W-pct |",
        "|---|---|---|---|---|",
    ]
    for p in sorted(unprompted, key=lambda x: (x["model"], x["sample_id"])):
        lines.append(
            f"| {p['model']} | {p['sample_id']} | {p['nearest_author']} | "
            f"{p['nearest_distance']:.3f} | {p['nearest_w_percentile']:.1f} |"
        )
    lines += [
        "",
        "## Style-prompted samples",
        "",
        f"- Nearest author == target: {len(style_hits)}/{len(styled)}",
        f"- Entered target's within-author p90 region: {len(style_entered)}/{len(styled)}",
        "",
        "| Model | Sample | Target | Nearest | nearest W-pct | target W-pct |",
        "|---|---|---|---|---|---|",
    ]
    for p in sorted(styled, key=lambda x: (x["model"], x["sample_id"])):
        tgt_pct = p["per_author"].get(p["style_target"], {}).get("w_percentile")
        tgt_pct_s = f"{tgt_pct:.1f}" if tgt_pct is not None else "—"
        lines.append(
            f"| {p['model']} | {p['sample_id']} | {p['style_target']} | "
            f"{p['nearest_author']} | {p['nearest_w_percentile']:.1f} | {tgt_pct_s} |"
        )
    (args.output_dir / "e4_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(f"\nE4 gate: {'PASS' if gate_pass else 'FAIL'} "
          f"({len(unprompted)} unprompted, {len(violations)} violations; "
          f"{len(styled)} style-prompted, {len(style_hits)} nearest-is-target)")
    print(f"Results: {out_json}")
    return 0 if gate_pass else 3


if __name__ == "__main__":
    sys.exit(main())
