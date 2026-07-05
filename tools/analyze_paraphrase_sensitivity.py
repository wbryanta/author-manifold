#!/usr/bin/env python3
"""Issue #95 P4 (paper outline C3) — prompt-wording sensitivity readout.

The paraphrase condition regenerates the unprompted task under three
alternate phrasings of the base instruction (workshop / editor_brief /
terse) on four fixed scenarios. Question: do the placement findings move
with prompt wording? If placement (distance to nearest author, off-manifold
status) is stable across phrasings, the findings are not artifacts of one
prompt's wording.

Method: for each (model, scenario), compare the paraphrase samples'
nearest-author distances against the unprompted samples of the same
(model, scenario) cell: per-phrasing medians, the spread across phrasings,
and the off-manifold rate per phrasing. All placements via the primary
wave-2 artifact.

Outputs reports/validation/wave2/paraphrase_sensitivity.{json,md}.

Relates: ADR-0041, TIER1_PAPER_OUTLINE.md §6 C3, issue #95 P4.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

logger = logging.getLogger("analyze_paraphrase_sensitivity")
REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="P4: paraphrase sensitivity")
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
    manifest = args.corpus_dir / "manifest.jsonl"

    # nearest-author distance + min W-pct per sample, keyed by
    # (model, scenario, condition, paraphrase_id)
    rows = []
    for line in open(manifest, encoding="utf-8"):
        rec = json.loads(line)
        if rec["condition"] not in ("unprompted", "paraphrase"):
            continue
        path = args.corpus_dir / rec["file_path"]
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.split()) < args.min_words:
            continue
        res = space.place(text=text)
        nearest = res.placements[0]
        rows.append({
            "model": rec["model"],
            "scenario": rec["scenario_id"],
            "condition": rec["condition"],
            "paraphrase_id": rec.get("paraphrase_id") or "base",
            "nearest_distance": nearest.distance,
            "nearest_w_percentile": nearest.w_percentile,
            "off_manifold": nearest.w_percentile > 90.0,
        })

    # restrict the unprompted reference to the 4 paraphrase scenarios
    para_scen = sorted({r["scenario"] for r in rows if r["condition"] == "paraphrase"})
    by_phrasing: dict[str, list[float]] = defaultdict(list)
    off_by_phrasing: dict[str, list[bool]] = defaultdict(list)
    per_model_spread = {}
    models = sorted({r["model"] for r in rows if r["condition"] == "paraphrase"})

    for r in rows:
        if r["scenario"] not in para_scen:
            continue
        key = r["paraphrase_id"] if r["condition"] == "paraphrase" else "base"
        by_phrasing[key].append(r["nearest_distance"])
        off_by_phrasing[key].append(r["off_manifold"])

    for m in models:
        meds = {}
        for ph in ["base", "workshop", "editor_brief", "terse"]:
            ds = [r["nearest_distance"] for r in rows
                  if r["model"] == m and r["scenario"] in para_scen
                  and (r["paraphrase_id"] if r["condition"] == "paraphrase"
                       else "base") == ph]
            if ds:
                meds[ph] = float(np.median(ds))
        if len(meds) >= 2:
            per_model_spread[m] = {
                "per_phrasing_median": meds,
                "max_abs_spread": float(max(meds.values()) - min(meds.values())),
            }

    phr_summary = {
        ph: {
            "n": len(ds),
            "median_nearest_distance": float(np.median(ds)),
            "off_manifold_rate": float(np.mean(off_by_phrasing[ph])),
        }
        for ph, ds in by_phrasing.items() if ds
    }
    spreads = [v["max_abs_spread"] for v in per_model_spread.values()]
    results = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "artifact": str(args.artifact),
            "paraphrase_scenarios": para_scen,
            "n_rows": len(rows),
        },
        "experiment": "p4_paraphrase_sensitivity",
        "per_phrasing": phr_summary,
        "per_model_spread": per_model_spread,
        "max_model_spread": float(max(spreads)) if spreads else None,
        "reading": (
            "Placement is prompt-wording-robust if per-phrasing medians sit "
            "within the within-model sampling spread and off-manifold rates "
            "stay at 1.0 across phrasings."
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out = args.output_dir / "paraphrase_sensitivity.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")

    lines = [
        "# P4 — Prompt-Wording Sensitivity (paraphrase condition)",
        "",
        f"- Generated: {results['meta']['generated']}; scenarios: {', '.join(para_scen)}",
        "",
        "| Phrasing | n | median nearest dist | off-manifold rate |",
        "|---|---|---|---|",
    ]
    for ph in ["base", "workshop", "editor_brief", "terse"]:
        if ph in phr_summary:
            s = phr_summary[ph]
            lines.append(f"| {ph} | {s['n']} | {s['median_nearest_distance']:.3f} "
                         f"| {s['off_manifold_rate']:.3f} |")
    lines += ["", "Per-model max spread across phrasing medians:", ""]
    for m, v in sorted(per_model_spread.items()):
        lines.append(f"- {m}: {v['max_abs_spread']:.3f}")
    (args.output_dir / "paraphrase_sensitivity.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"\nP4 readout: phrasings {list(phr_summary)}; "
          f"max model spread {results['max_model_spread']}; results: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
