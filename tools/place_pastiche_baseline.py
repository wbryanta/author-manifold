#!/usr/bin/env python3
"""Issue #95 P5 (paper outline C2) — the human pastiche baseline.

Question: can a dedicated HUMAN imitator enter a target author's
within-author region, where style-prompted LLMs cannot (0/24)?

Test material: Sybil G. Brinton, "Old Friends and New Fancies" (1913) —
the first published Austen pastiche, novel-length, public domain
(Project Gutenberg #43741). Critical consensus calls it earnest but
"too fully Victorian in tone to really succeed" as Austen — giving the
instrument a human judgment to corroborate or contradict.

Protocol mirrors the AI placement: strip Gutenberg boilerplate, cut the
body into non-overlapping ~3,000-word chunks (E6 floor), place each in
the public-domain author space, and report the distribution of
distance-to-Austen as W-percentiles, alongside (a) Austen's own works'
LOO distances and (b) the style-prompted LLM numbers for contrast.

Outputs reports/validation/pd_shelf/pastiche_baseline.{json,md}.

Relates: ADR-0041, TIER1_PAPER_OUTLINE.md §6 C2, issue #95 P5.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

logger = logging.getLogger("place_pastiche_baseline")
REPO_ROOT = Path(__file__).resolve().parents[1]

GUTENBERG_START = re.compile(r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)
GUTENBERG_END = re.compile(r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)


def strip_gutenberg(text: str) -> str:
    m = GUTENBERG_START.search(text)
    if m:
        text = text[m.end():]
    m = GUTENBERG_END.search(text)
    if m:
        text = text[: m.start()]
    return text.strip()


def chunk_words(text: str, size: int) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), size):
        piece = words[i : i + size]
        if len(piece) >= size // 2:
            chunks.append(" ".join(piece))
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="P5: human pastiche baseline")
    parser.add_argument(
        "--artifact", type=Path,
        default=REPO_ROOT / "data/artifacts/author_space_pd_v1.json",
    )
    parser.add_argument(
        "--pastiche", type=Path,
        default=REPO_ROOT / "data/pastiche/brinton_old_friends_new_fancies_1913.txt",
    )
    parser.add_argument("--target-author", type=str, default="austen-jane",
                        help="Author slug in the artifact the pastiche imitates")
    parser.add_argument("--chunk-words", type=int, default=3000)
    parser.add_argument(
        "--output-dir", type=Path,
        default=REPO_ROOT / "reports/validation/pd_shelf",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from author_manifold.author_space import AuthorRelativeSpace

    if not args.artifact.exists():
        logger.error("PD artifact not found: %s (run P8 first)", args.artifact)
        return 2

    space = AuthorRelativeSpace.from_artifact(args.artifact)
    if args.target_author not in space.authors:
        logger.error("Target author %s not in artifact (%s)",
                     args.target_author, sorted(space.authors))
        return 2

    raw = args.pastiche.read_text(encoding="utf-8")
    body = strip_gutenberg(raw)
    chunks = chunk_words(body, args.chunk_words)
    logger.info("Pastiche body: %d words -> %d chunks of ~%d words",
                len(body.split()), len(chunks), args.chunk_words)

    placements = []
    for i, chunk in enumerate(chunks):
        res = space.place(text=chunk)
        target = next(p for p in res.placements if p.author == args.target_author)
        nearest = res.placements[0]
        placements.append({
            "chunk": i,
            "nearest_author": nearest.author,
            "nearest_distance": nearest.distance,
            "target_distance": target.distance,
            "target_w_percentile": target.w_percentile,
            "target_is_nearest": nearest.author == args.target_author,
            "entered_target_w_p90": target.w_percentile <= 90.0,
        })

    n = len(placements)
    n_nearest = sum(p["target_is_nearest"] for p in placements)
    n_entered = sum(p["entered_target_w_p90"] for p in placements)
    med_target_d = float(np.median([p["target_distance"] for p in placements]))
    med_target_wpct = float(np.median([p["target_w_percentile"] for p in placements]))

    results = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "artifact": str(args.artifact),
            "pastiche": str(args.pastiche),
            "target_author": args.target_author,
            "chunk_words": args.chunk_words,
            "provenance": "Brinton 1913, Project Gutenberg #43741, public domain",
        },
        "experiment": "p5_pastiche_baseline",
        "n_chunks": n,
        "target_is_nearest": n_nearest,
        "entered_target_w_p90": n_entered,
        "median_target_distance": med_target_d,
        "median_target_w_percentile": med_target_wpct,
        "placements": placements,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out = args.output_dir / "pastiche_baseline.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")

    lines = [
        "# P5 — Human Pastiche Baseline (Brinton 1913 vs Austen)",
        "",
        f"- Generated: {results['meta']['generated']}",
        f"- {n} chunks of ~{args.chunk_words} words; target: {args.target_author}",
        "",
        f"- Target is nearest author: **{n_nearest}/{n}** chunks",
        f"- Entered target's within-author p90 region: **{n_entered}/{n}** chunks",
        f"- Median distance to target: {med_target_d:.3f} "
        f"(median target W-percentile: {med_target_wpct:.1f})",
        "",
        "Contrast row (LLM style-prompted, contemporary shelf, pilot): "
        "9/24 nearest-is-target, **0/24** entered target W-p90.",
        "",
        "| Chunk | Nearest | Target dist | Target W-pct | Entered p90 |",
        "|---|---|---|---|---|",
    ]
    for p in placements:
        lines.append(
            f"| {p['chunk']} | {p['nearest_author']} | {p['target_distance']:.3f} "
            f"| {p['target_w_percentile']:.1f} | {'YES' if p['entered_target_w_p90'] else 'no'} |"
        )
    (args.output_dir / "pastiche_baseline.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"\nP5: {n_nearest}/{n} nearest-is-target, {n_entered}/{n} entered "
          f"W-p90; median target W-pct {med_target_wpct:.1f}. Results: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
