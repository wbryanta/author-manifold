#!/usr/bin/env python3
"""Issue #95 P6 (paper outline C5) — model self-consistency.

Treat each model as an "author": featurize its unprompted long-form samples
with the author space's MFW block and ask (a) how tight is its within-model
distance distribution versus human within-author variation, and (b) do
models attribute to themselves (LOO nearest-model-centroid), i.e. do models
carry stable, mutually distinguishable lexical signatures?

Outputs reports/validation/wave2/model_self_consistency.{json,md}.

Relates: ADR-0041, TIER1_PAPER_OUTLINE.md §6 C5, issue #95.
"""

from __future__ import annotations

import argparse
import itertools
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

logger = logging.getLogger("analyze_model_self_consistency")
REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="P6: model self-consistency")
    parser.add_argument(
        "--artifact", type=Path,
        default=REPO_ROOT / "data/artifacts/author_space_v1_wave2.json",
    )
    parser.add_argument(
        "--corpus-dir", type=Path, default=REPO_ROOT / "data/ai-longform",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=REPO_ROOT / "reports/validation/wave2",
    )
    parser.add_argument("--min-words", type=int, default=1500)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from author_manifold.author_space import AuthorRelativeSpace

    space = AuthorRelativeSpace.from_artifact(args.artifact)

    # Featurize unprompted samples per model
    manifest = args.corpus_dir / "manifest.jsonl"
    z_by_model: dict[str, list[np.ndarray]] = defaultdict(list)
    for line in open(manifest, encoding="utf-8"):
        rec = json.loads(line)
        if rec.get("condition") != "unprompted":
            continue
        path = args.corpus_dir / rec["file_path"]
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.split()) < args.min_words:
            continue
        z = space.mfw.featurize_text(text)
        z_by_model[rec["model"]].append(z)

    models = sorted(m for m, zs in z_by_model.items() if len(zs) >= 4)
    logger.info("Models with >=4 unprompted samples: %s", models)

    def delta(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.mean(np.abs(a - b)))

    # Human reference: within-author pairs / between-author pairs quantiles
    art = json.loads(args.artifact.read_text(encoding="utf-8"))
    w_pairs_q = art["within_author_dist"]["pairs"]["quantiles"]
    b_pairs_q = art["between_author_dist"]["pairs"]["quantiles"]

    per_model = {}
    for m in models:
        zs = z_by_model[m]
        within = [delta(a, b) for a, b in itertools.combinations(zs, 2)]
        per_model[m] = {
            "n_samples": len(zs),
            "within_median": float(np.median(within)),
            "within_p90": float(np.percentile(within, 90)),
            "centroid": np.mean(np.vstack(zs), axis=0),
        }

    # Cross-model centroid distances + LOO self-attribution
    cross = {}
    for m1, m2 in itertools.combinations(models, 2):
        cross[f"{m1}|{m2}"] = delta(per_model[m1]["centroid"], per_model[m2]["centroid"])

    correct = total = 0
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for m in models:
        zs = z_by_model[m]
        for i, z in enumerate(zs):
            best, best_d = None, float("inf")
            for cand in models:
                cz = z_by_model[cand]
                if cand == m:
                    others = [x for j, x in enumerate(cz) if j != i]
                    if not others:
                        continue
                    cen = np.mean(np.vstack(others), axis=0)
                else:
                    cen = per_model[cand]["centroid"]
                d = delta(z, cen)
                if d < best_d:
                    best, best_d = cand, d
            confusion[m][best] += 1
            correct += int(best == m)
            total += 1

    results = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "artifact": str(args.artifact),
            "min_words": args.min_words,
        },
        "experiment": "p6_self_consistency",
        "human_reference": {
            "within_author_pairs_p50": w_pairs_q["p50"],
            "within_author_pairs_p90": w_pairs_q["p90"],
            "between_author_pairs_p50": b_pairs_q["p50"],
        },
        "per_model": {
            m: {k: v for k, v in d.items() if k != "centroid"}
            for m, d in per_model.items()
        },
        "cross_model_centroid_delta": cross,
        "loo_self_attribution": {
            "accuracy": correct / total if total else None,
            "n_trials": total,
            "n_models": len(models),
            "chance": 1 / len(models) if models else None,
            "confusion": {m: dict(v) for m, v in confusion.items()},
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out = args.output_dir / "model_self_consistency.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")

    lines = [
        "# P6 — Model Self-Consistency (are LLMs narrow-variance authors?)",
        "",
        f"- Generated: {results['meta']['generated']}; artifact: wave-2 (15-author)",
        f"- Human reference: within-author pairs p50 {w_pairs_q['p50']:.3f} "
        f"(p90 {w_pairs_q['p90']:.3f}); between-author pairs p50 {b_pairs_q['p50']:.3f}",
        "",
        "| Model | n | within-model Δ p50 | vs human within p50 |",
        "|---|---|---|---|",
    ]
    for m in models:
        d = per_model[m]
        ratio = d["within_median"] / w_pairs_q["p50"]
        lines.append(
            f"| {m} | {d['n_samples']} | {d['within_median']:.3f} | {ratio:.2f}x |"
        )
    acc = results["loo_self_attribution"]["accuracy"]
    lines += [
        "",
        f"LOO self-attribution: **{acc:.1%}** over {total} trials, "
        f"{len(models)} models (chance {1/len(models):.1%}).",
        "",
        "Cross-model centroid Delta (sorted):",
        "",
    ]
    for pair, d in sorted(cross.items(), key=lambda x: x[1]):
        lines.append(f"- {pair}: {d:.3f}")
    (args.output_dir / "model_self_consistency.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"\nP6 done: self-attribution {acc:.1%} (chance {1/len(models):.1%}); "
          f"results in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
