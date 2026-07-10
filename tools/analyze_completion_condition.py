#!/usr/bin/env python3
"""Red-team K8 closure — place the completion condition against LM envelopes.

The completion condition (model continues ~600 words of the target author's
own novel, author unnamed) is the contrast literature's actual imitation
mechanism. Per the generator's analysis note, continuations carry over the
opening's proper nouns/content words, so the FW-ONLY vocabulary is the
primary measurement; full-vocab is reported as a (content-confounded)
secondary.

Refusal handling: OpenAI models refuse or truncate this condition. Samples
below the hard floor are classified non-compliant (refusal/partial) and
reported as per-model compliance rates, never placed. Zero-length outputs
(unloadable: no tokens) are counted in the refused/partial column with an
explicit meta note — the manifest count, not the loadable count, is the
denominator (v0.3 red-team G11/claims §5b: 160 recorded, 1 zero-length
qwen3.6 sample silently dropped at load in the first run).

Clustering (v0.3 red-team G2 aggravator): pooled entry rates carry the
same treatment as the styled tables — ICC/DEFF over (model x target)
cells with DEFF-adjusted CP bounds, plus cell-level bootstrap CIs.

Outputs completion_results.{json,md} under --output-dir (default
reports/validation/author_space/results2_rerun/; the released evidence run
is committed under results2/ and is what rerun_entry_analysis.py reads for
the G2 model-matched comparison by default).

Relates: docs/redteam/RED_TEAM_SYNTHESIS.md K8; redteam_stats_attack_v03.md
G2/G11; rerun_entry_analysis.py (machinery reused).

Usage:
    python3 tools/analyze_completion_condition.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("analyze_completion_condition")

REPO_ROOT = Path(__file__).resolve().parents[1]
for _path in (REPO_ROOT / "src", REPO_ROOT / "tools", REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from rerun_entry_analysis import (  # noqa: E402
    VocabRun, load_corpus, clopper_pearson, cp_one_sided_upper,
    cluster_bootstrap_ci,
)

ARTIFACT_DIR = REPO_ROOT / "data/artifacts"


def main() -> int:
    parser = argparse.ArgumentParser(description="K8: completion placement")
    parser.add_argument("--corpus-dir", type=Path,
                        default=REPO_ROOT / "data/ai-longform")
    parser.add_argument("--window-words", type=int, default=3000)
    parser.add_argument("--hard-floor", type=int, default=1500)
    parser.add_argument("--practice-floor", type=int, default=3000)
    parser.add_argument(
        "--output-dir", type=Path,
        default=REPO_ROOT / "reports/validation/author_space/results2_rerun",
        help="where to write results (default: results2_rerun, so the "
             "released evidence under results2/ stays pristine for diffing)")
    parser.add_argument("--seed", type=int, default=20260609)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    runs = {
        "full": VocabRun(
            "full",
            ARTIFACT_DIR / "author_space_v1_wave2.json",
            ARTIFACT_DIR / "lm_envelopes_wave2_3000w.json",
            ARTIFACT_DIR / "author_space_pd_v1.json",
            ARTIFACT_DIR / "lm_envelopes_pd_3000w.json",
        ),
        "fwonly": VocabRun(
            "fwonly",
            ARTIFACT_DIR / "author_space_v1_wave2_fwonly.json",
            ARTIFACT_DIR / "lm_envelopes_wave2_fwonly_3000w.json",
            ARTIFACT_DIR / "author_space_pd_v1_fwonly.json",
            ARTIFACT_DIR / "lm_envelopes_pd_fwonly_3000w.json",
        ),
    }

    # Manifest is the denominator: zero-length outputs produce no tokens and
    # are dropped by load_corpus, but they were generated and must be
    # counted (as refused/partial — a zero-length continuation is maximal
    # non-compliance, same treatment as the v0.2 qwen styled samples).
    manifest_path = args.corpus_dir / "manifest.jsonl"
    manifest_completion = [
        r for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and (r := json.loads(line)).get("condition") == "completion"
    ]
    records = [r for r in load_corpus(args.corpus_dir)
               if r.get("condition") == "completion"]
    loaded_paths = {r["file_path"] for r in records}
    zero_length = [r for r in manifest_completion
                   if r["file_path"] not in loaded_paths]
    logger.info("completion records: %d in manifest, %d loaded, %d zero-length",
                len(manifest_completion), len(records), len(zero_length))

    # Compliance classification by token count (refusals are tens of words)
    compliant, subfloor, refused = [], [], []
    for r in records:
        n = r["_n_tokens"]
        if n < args.hard_floor:
            refused.append(r)
        elif n < args.practice_floor:
            subfloor.append(r)
        else:
            compliant.append(r)

    compliance = defaultdict(lambda: {"compliant": 0, "subfloor": 0, "refused": 0})
    for r, bucket in [(x, "compliant") for x in compliant] + \
                     [(x, "subfloor") for x in subfloor] + \
                     [(x, "refused") for x in refused] + \
                     [(x, "refused") for x in zero_length]:
        compliance[r["model"]][bucket] += 1

    results = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "n_records": len(manifest_completion),
            "n_records_loaded": len(records),
            "n_zero_length_refused": len(zero_length),
            "zero_length_files": sorted(r["file_path"] for r in zero_length),
            "zero_length_note": (
                "zero-length outputs are counted in the refused/partial "
                "column; n_records is the MANIFEST count (every generation "
                "recorded), not the loadable count"),
            "window_words": args.window_words,
            "hard_floor_tokens": args.hard_floor,
            "practice_floor_tokens": args.practice_floor,
            "primary_vocab": "fwonly (content carry-over confound — see generator note)",
            "provenance": {k: v.provenance() for k, v in runs.items()},
        },
        "compliance_per_model": {m: dict(v) for m, v in sorted(compliance.items())},
        "entry": {},
    }

    from author_manifold.author_space import MFWBlock, design_effect

    for label, run in runs.items():
        placed = []
        for rec in compliant:
            tokens = rec["_tokens"][: args.window_words]
            z = run.space.mfw.featurize_tokens(tokens)
            target = rec["style_target"]
            entry_env = run.envelopes.authors.get(target)
            if entry_env is None:
                continue
            d = MFWBlock.delta(z, run.space.authors[target].mfw_centroid)
            placed.append({
                "sample_id": rec["sample_id"], "model": rec["model"],
                "target": target, "n_tokens": rec["_n_tokens"],
                "target_distance": d,
                "entered_p90": d <= entry_env.quantiles["p90"],
                "entered_p95": d <= entry_env.quantiles["p95"],
                "entered_p99": d <= entry_env.quantiles["p99"],
            })
        per_model = defaultdict(lambda: {"n": 0, "p90": 0, "p95": 0, "p99": 0})
        per_target = defaultdict(lambda: {"n": 0, "p90": 0})
        for p in placed:
            pm = per_model[p["model"]]; pm["n"] += 1
            pt = per_target[p["target"]]; pt["n"] += 1
            for lvl in ("p90", "p95", "p99"):
                pm[lvl] += int(p[f"entered_{lvl}"])
            pt["p90"] += int(p["entered_p90"])
        n = len(placed)
        k90 = sum(p["entered_p90"] for p in placed)
        # Clustering treatment (G2 aggravator): (model x target) cells.
        cells = [f"{p['model']}|{p['target']}" for p in placed]
        entered = [int(p["entered_p90"]) for p in placed]
        de = design_effect(entered, cells) if n else None
        results["entry"][label] = {
            "n_placed": n,
            "entered_p90": k90,
            "rate_p90": k90 / n if n else None,
            "cp95": clopper_pearson(k90, n) if n else None,
            "cp_upper_1s": cp_one_sided_upper(k90, n) if n else None,
            "clustering": "(model x target) cells",
            "n_cells": len(set(cells)),
            "icc_entered_p90": de["icc"] if de else None,
            "design_effect_p90": de["design_effect"] if de else None,
            "n_eff_p90": de["n_eff"] if de else None,
            "cp95_design_effect_adjusted": (
                list(clopper_pearson(k90 / de["design_effect"],
                                     n / de["design_effect"]))
                if de else None),
            "cell_bootstrap_ci95_p90": (
                list(cluster_bootstrap_ci(entered, cells,
                                          args.n_bootstrap, args.seed))
                if n else None),
            "entered_p95": sum(p["entered_p95"] for p in placed),
            "entered_p99": sum(p["entered_p99"] for p in placed),
            "per_model": {m: dict(v) for m, v in sorted(per_model.items())},
            "per_target": {t: dict(v) for t, v in sorted(per_target.items())},
            "placements": placed,
        }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "completion_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")

    def fmt_ci(ci):
        return (f"[{ci[0]*100:.1f}%, {ci[1]*100:.1f}%]"
                if ci is not None else "—")

    lines = ["# K8 — Completion Condition Placement (LM envelopes)", "",
             f"- Generated: {results['meta']['generated']}; primary vocab: fw-only",
             f"- {len(manifest_completion)} generations recorded: "
             f"{len(compliant)} compliant (>= {args.practice_floor} tokens), "
             f"{len(subfloor)} sub-floor, "
             f"{len(refused) + len(zero_length)} refused/partial "
             f"(< {args.hard_floor}, incl. {len(zero_length)} zero-length "
             "output(s) counted as refused/partial)",
             "", "## Compliance per model", "",
             "| Model | compliant | sub-floor | refused/partial |", "|---|---|---|---|"]
    for m, v in sorted(compliance.items()):
        lines.append(f"| {m} | {v['compliant']} | {v['subfloor']} | {v['refused']} |")
    if zero_length:
        lines += ["", "Zero-length outputs (in refused/partial): "
                  + ", ".join(f"`{f}`" for f in results["meta"]["zero_length_files"])]
    for label in ("fwonly", "full"):
        e = results["entry"][label]
        lines += ["", f"## Entry — {label} vocabulary"
                      f"{' (PRIMARY)' if label == 'fwonly' else ' (content-confounded secondary)'}", "",
                  f"Pooled: {e['entered_p90']}/{e['n_placed']} = "
                  f"{(e['rate_p90'] or 0)*100:.1f}% @p90 "
                  f"(CP {fmt_ci(e['cp95'])}); p95 {e['entered_p95']}, "
                  f"p99 {e['entered_p99']}",
                  f"Clustering ({e['clustering']}, {e['n_cells']} cells): "
                  f"ICC {e['icc_entered_p90']:.3f}, "
                  f"DEFF {e['design_effect_p90']:.2f}, "
                  f"n_eff {e['n_eff_p90']:.0f}; DEFF-adj CP "
                  f"{fmt_ci(e['cp95_design_effect_adjusted'])}; "
                  f"cell-bootstrap {fmt_ci(e['cell_bootstrap_ci95_p90'])}",
                  "", "| Model | n | entered p90 | p95 | p99 |", "|---|---|---|---|---|"]
        for m, v in e["per_model"].items():
            lines.append(f"| {m} | {v['n']} | {v['p90']} | {v['p95']} | {v['p99']} |")
        lines += ["", "| Target | n | entered p90 |", "|---|---|---|"]
        for t, v in e["per_target"].items():
            lines.append(f"| {t} | {v['n']} | {v['p90']} |")
    (args.output_dir / "completion_results.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    e = results["entry"]["fwonly"]
    print(f"\nK8 completion: fw-only entry {e['entered_p90']}/{e['n_placed']} "
          f"= {(e['rate_p90'] or 0)*100:.1f}% @p90; "
          f"refused {len(refused)}, sub-floor {len(subfloor)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
