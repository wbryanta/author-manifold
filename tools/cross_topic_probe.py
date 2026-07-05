#!/usr/bin/env python3
"""Within-shelf cross-topic robustness probe for MFW-Delta attribution.

Topic-confound control C1(b) (issue #95 P3; docs/research/TIER1_PAPER_OUTLINE.md
section 6). The worry: MFW-Delta attribution might ride on subject matter
rather than authorial habit. This probe asks, for every gold-shelf author
with >= 4 works: when a held-out work's CONTENT overlaps less with the
author's other works (the work is "off-topic" for that author), does
MFW-Delta attribution get worse?

Operationalization:

- Topic vector per work: term frequencies (normalized to sum 1) over the
  CONTENT vocabulary = top --content-n (default 2000) shelf words by total
  count MINUS the closed-class STYLOMETRIC_FUNCTION_WORDS list.
- Topic similarity per work: cosine(work tf, mean tf of the author's OTHER
  works) — leave-one-out, mirroring the E2 protocol.
- Attribution per work: E2 leave-one-work-out nearest-centroid under the
  artifact's MFW Delta (own-author centroid rebuilt without the work).
  Margin = d(own LOO centroid) - min over other authors of d(centroid);
  negative margin = correct attribution with that much room.
- Verdict statistics: Spearman rho between topic similarity and (a) margin,
  (b) distance to own LOO centroid; point-biserial vs attribution error;
  quartile bins of topic similarity with per-bin top-1 accuracy.

If attribution stays high across the whole observed topic-similarity range
(and the correlations are weak), MFW identity is not riding topic.

Usage:
    python3 tools/cross_topic_probe.py \
        --artifact data/artifacts/author_space_v1_wave2.json \
        --output-dir reports/validation/topic_controls
"""

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
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from author_manifold.author_space import (
    AuthorRelativeSpace,
    MFWBlock,
    STYLOMETRIC_FUNCTION_WORDS,
    mfw_tokenize,
)

logger = logging.getLogger("cross_topic_probe")

DEFAULT_ARTIFACT = "data/artifacts/author_space_pd_v1.json"
DEFAULT_OUTPUT_DIR = "reports/validation/topic_controls"
DEFAULT_CONTENT_N = 2000
MIN_WORKS = 4


def _resolve(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute() or path.exists():
        return path
    candidate = REPO_ROOT / path
    return candidate if candidate.exists() else path


def _work_tokens(work) -> Optional[List[str]]:
    """MFW tokens of a work's body text (manifest slice via text_path)."""
    if work.body_text is not None:
        return mfw_tokenize(work.body_text)
    if not work.text_path:
        return None
    path = _resolve(work.text_path)
    if not path.is_file():
        # text_path may be absolute from another checkout; retry tail-relative
        parts = Path(work.text_path).parts
        for i in range(len(parts)):
            candidate = REPO_ROOT.joinpath(*parts[i:])
            if candidate.is_file():
                path = candidate
                break
        else:
            return None
    text = path.read_text(encoding="utf-8")
    start = work.body_start or 0
    end = work.body_end if work.body_end is not None else len(text)
    return mfw_tokenize(text[start:end])


def _spearman(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    from scipy.stats import spearmanr

    rho, p = spearmanr(x, y)
    return float(rho), float(p)


def run_probe(
    space: AuthorRelativeSpace,
    content_n: int = DEFAULT_CONTENT_N,
    min_works: int = MIN_WORKS,
) -> Dict[str, Any]:
    if space.mfw is None:
        raise ValueError("Probe requires an artifact with the MFW block")
    slugs = sorted(space.authors)

    # --- tokenize all calibrated works, build the content vocabulary -------
    tokens_by: Dict[Tuple[str, int], List[str]] = {}
    shelf_counts: Counter = Counter()
    for slug in slugs:
        for idx, work in enumerate(space.authors[slug].works):
            tokens = _work_tokens(work)
            if not tokens:
                raise ValueError(
                    f"No body text for {slug}/{work.title} "
                    f"(text_path={work.text_path!r})"
                )
            tokens_by[(slug, idx)] = tokens
            shelf_counts.update(tokens)
    top = [
        w for w, _ in sorted(shelf_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ][:content_n]
    content_vocab = [w for w in top if w not in STYLOMETRIC_FUNCTION_WORDS]
    vocab_index = {w: i for i, w in enumerate(content_vocab)}

    def tf_vector(tokens: List[str]) -> np.ndarray:
        vec = np.zeros(len(content_vocab), dtype=float)
        for token, count in Counter(tokens).items():
            i = vocab_index.get(token)
            if i is not None:
                vec[i] = count
        total = vec.sum()
        return vec / total if total > 0 else vec

    tf_by = {key: tf_vector(tokens) for key, tokens in tokens_by.items()}

    def cosine(a: np.ndarray, b: np.ndarray) -> float:
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        return float(a @ b / denom) if denom > 0 else 0.0

    # --- E2 LOO attribution + LOO topic similarity per work ----------------
    mfw_by = {
        slug: np.vstack([w.mfw_z for w in space.authors[slug].works])
        for slug in slugs
    }
    mfw_centroids = {slug: mfw_by[slug].mean(axis=0) for slug in slugs}

    rows: List[Dict[str, Any]] = []
    between_topic_sims: List[float] = []
    eligible = [s for s in slugs if space.authors[s].work_count >= min_works]
    for slug in eligible:
        works = space.authors[slug].works
        matrix = mfw_by[slug]
        n = matrix.shape[0]
        mfw_total = matrix.sum(axis=0)
        tf_stack = np.vstack([tf_by[(slug, i)] for i in range(n)])
        tf_total = tf_stack.sum(axis=0)
        for i in range(n):
            held = matrix[i]
            distances = {}
            for other in slugs:
                centroid = (
                    (mfw_total - held) / (n - 1) if other == slug
                    else mfw_centroids[other]
                )
                distances[other] = MFWBlock.delta(held, centroid)
            ranked = sorted(distances, key=distances.get)
            d_own = distances[slug]
            d_best_other = min(d for s, d in distances.items() if s != slug)
            topic_sim = cosine(tf_by[(slug, i)], (tf_total - tf_stack[i]) / (n - 1))
            # context: this work's topic similarity to OTHER authors
            for other in eligible:
                if other == slug:
                    continue
                other_n = space.authors[other].work_count
                other_mean = np.vstack(
                    [tf_by[(other, j)] for j in range(other_n)]
                ).mean(axis=0)
                between_topic_sims.append(cosine(tf_by[(slug, i)], other_mean))
            rows.append({
                "author": slug,
                "title": works[i].title,
                "n_author_works": n,
                "topic_similarity_loo": topic_sim,
                "d_own_loo": d_own,
                "d_best_other": d_best_other,
                "margin": d_own - d_best_other,
                "top1_correct": ranked[0] == slug,
                "own_rank": ranked.index(slug) + 1,
            })

    # --- statistics ---------------------------------------------------------
    sims = np.array([r["topic_similarity_loo"] for r in rows])
    margins = np.array([r["margin"] for r in rows])
    d_owns = np.array([r["d_own_loo"] for r in rows])
    errors = np.array([0.0 if r["top1_correct"] else 1.0 for r in rows])

    rho_margin, p_margin = _spearman(sims, margins)
    rho_down, p_down = _spearman(sims, d_owns)
    if errors.std() > 0:
        from scipy.stats import pointbiserialr

        r_err, p_err = pointbiserialr(errors, sims)
        r_err, p_err = float(r_err), float(p_err)
    else:
        r_err = p_err = None

    # Quartile bins of topic similarity (scatter summary).
    quartiles = np.percentile(sims, [25, 50, 75])
    bins: List[Dict[str, Any]] = []
    edges = [-np.inf, *quartiles, np.inf]
    for b in range(4):
        mask = (sims > edges[b]) & (sims <= edges[b + 1])
        sub = [r for r, m in zip(rows, mask) if m]
        bins.append({
            "bin": f"Q{b + 1}",
            "topic_sim_range": [
                float(sims[mask].min()), float(sims[mask].max())
            ] if mask.any() else None,
            "n": int(mask.sum()),
            "top1_accuracy": (
                float(np.mean([r["top1_correct"] for r in sub])) if sub else None
            ),
            "median_margin": (
                float(np.median([r["margin"] for r in sub])) if sub else None
            ),
            "median_d_own": (
                float(np.median([r["d_own_loo"] for r in sub])) if sub else None
            ),
        })

    return {
        "experiment": "cross_topic_probe",
        "name": "Within-shelf cross-topic robustness of MFW-Delta attribution",
        "content_vocabulary": {
            "candidate_top_n": content_n,
            "n_content_words": len(content_vocab),
            "n_function_words_removed": content_n - len(content_vocab),
            "definition": "top shelf words minus STYLOMETRIC_FUNCTION_WORDS, "
                          "per-work tf normalized to sum 1",
        },
        "n_authors": len(eligible),
        "min_works": min_works,
        "n_works": len(rows),
        "top1_accuracy": float(np.mean(1 - errors)),
        "n_errors": int(errors.sum()),
        "topic_similarity": {
            "within_author_loo": {
                "min": float(sims.min()), "p25": float(quartiles[0]),
                "p50": float(quartiles[1]), "p75": float(quartiles[2]),
                "max": float(sims.max()),
            },
            "between_author_context": {
                "n": len(between_topic_sims),
                "p25": float(np.percentile(between_topic_sims, 25)),
                "p50": float(np.percentile(between_topic_sims, 50)),
                "p75": float(np.percentile(between_topic_sims, 75)),
            },
        },
        "correlations": {
            "spearman_topic_sim_vs_margin": {"rho": rho_margin, "p": p_margin},
            "spearman_topic_sim_vs_d_own_loo": {"rho": rho_down, "p": p_down},
            "pointbiserial_error_vs_topic_sim": {"r": r_err, "p": p_err},
        },
        "bins": bins,
        "errors": [r for r in rows if not r["top1_correct"]],
        "rows": rows,
    }


def build_markdown(result: Dict[str, Any], meta: Dict[str, Any]) -> str:
    cv = result["content_vocabulary"]
    ts = result["topic_similarity"]
    corr = result["correlations"]
    lines = [
        "# Cross-Topic Robustness Probe (C1b, issue #95 P3)",
        "",
        f"- Generated: {meta['generated']}",
        f"- Artifact: {meta['artifact']} (variant {meta['distance_variant']})",
        f"- Authors with >= {result['min_works']} works: "
        f"{result['n_authors']} ({result['n_works']} held-out works)",
        f"- Content vocabulary: top {cv['candidate_top_n']} shelf words minus "
        f"function words = {cv['n_content_words']} content words "
        f"({cv['n_function_words_removed']} function words removed); "
        "per-work tf normalized.",
        "",
        "**Question:** does MFW-Delta LOO attribution degrade when a held-out "
        "work shares less subject matter (content-word profile) with its "
        "author's other works?",
        "",
        "## Headline",
        "",
        f"- Top-1 accuracy: {result['top1_accuracy']:.1%} "
        f"({result['n_works'] - result['n_errors']}/{result['n_works']}; "
        f"{result['n_errors']} errors)",
        f"- Within-author LOO topic similarity range: "
        f"{ts['within_author_loo']['min']:.3f} - "
        f"{ts['within_author_loo']['max']:.3f} "
        f"(p50 {ts['within_author_loo']['p50']:.3f}); between-author context "
        f"p50 {ts['between_author_context']['p50']:.3f}",
        f"- Spearman(topic sim, attribution margin): "
        f"rho = {corr['spearman_topic_sim_vs_margin']['rho']:.3f} "
        f"(p = {corr['spearman_topic_sim_vs_margin']['p']:.3f})",
        f"- Spearman(topic sim, distance to own LOO centroid): "
        f"rho = {corr['spearman_topic_sim_vs_d_own_loo']['rho']:.3f} "
        f"(p = {corr['spearman_topic_sim_vs_d_own_loo']['p']:.3f})",
    ]
    pb = corr["pointbiserial_error_vs_topic_sim"]
    if pb["r"] is not None:
        lines.append(
            f"- Point-biserial(error, topic sim): r = {pb['r']:.3f} "
            f"(p = {pb['p']:.3f})"
        )
    lines += [
        "",
        "## Scatter summary (quartile bins of LOO topic similarity)",
        "",
        "| Bin | Topic-sim range | n | Top-1 | Median margin | Median d_own |",
        "|---|---|---|---|---|---|",
    ]
    for b in result["bins"]:
        rng = b["topic_sim_range"]
        rng_s = f"{rng[0]:.3f} - {rng[1]:.3f}" if rng else "n/a"
        lines.append(
            f"| {b['bin']} | {rng_s} | {b['n']} "
            f"| {b['top1_accuracy']:.1%} | {b['median_margin']:.3f} "
            f"| {b['median_d_own']:.3f} |"
        )
    if result["errors"]:
        lines += ["", "## Attribution errors", ""]
        for r in result["errors"]:
            lines.append(
                f"- {r['author']} / {r['title']}: own rank {r['own_rank']}, "
                f"margin {r['margin']:+.3f}, topic sim "
                f"{r['topic_similarity_loo']:.3f}"
            )
    lines += ["", "## Reading", ""]
    rho = corr["spearman_topic_sim_vs_margin"]["rho"]
    p = corr["spearman_topic_sim_vs_margin"]["p"]
    spread = ts["within_author_loo"]["max"] - ts["within_author_loo"]["min"]
    low_bin = result["bins"][0]
    coupled = abs(rho) >= 0.3 and p < 0.05
    survives_low = (
        low_bin["top1_accuracy"] is not None
        and low_bin["top1_accuracy"] >= 0.80
    )
    lines.append(
        f"Within-author content similarity spans {spread:.3f} of cosine "
        "(works genuinely differ in subject matter), while LOO attribution "
        f"stays at {result['top1_accuracy']:.1%} overall and "
        f"{low_bin['top1_accuracy']:.1%} in the LOWEST topic-similarity "
        f"quartile (works most off-topic for their author). The "
        f"topic-similarity vs attribution-margin correlation is "
        f"rho = {rho:.3f} (p = {p:.3f})."
    )
    if coupled and survives_low:
        lines += [
            "",
            "There is a graded coupling: works that are more topically "
            "typical of their author also sit closer in MFW Delta. This is "
            "expected even under purely stylistic attribution, because topic "
            "and style co-drift within a career (and atypical-topic works "
            "are often atypical-register works, e.g. a dialogue-only novel). "
            "The decisive observation is that attribution does NOT collapse "
            "at the off-topic end of the range: MFW identity degrades "
            "gracefully with topical atypicality but is not riding topic. "
            "Cross-check with the function-words-only probe (zero content "
            "words in the vocabulary) to close the loop.",
        ]
    elif survives_low:
        lines += [
            "",
            "Attribution survives across the observed topic range with no "
            "meaningful topic-margin coupling: MFW identity is not riding "
            "topic on this shelf.",
        ]
    else:
        lines += [
            "",
            "Attribution weakens substantially for off-topic works: treat "
            "MFW attribution claims on this shelf with a topic caveat.",
        ]
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Cross-topic robustness probe")
    parser.add_argument("--artifact", default=DEFAULT_ARTIFACT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--content-n", type=int, default=DEFAULT_CONTENT_N)
    parser.add_argument("--min-works", type=int, default=MIN_WORKS)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    artifact = _resolve(args.artifact)
    space = AuthorRelativeSpace.from_artifact(artifact)
    result = run_probe(space, content_n=args.content_n, min_works=args.min_works)
    meta = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "artifact": str(artifact),
        "distance_variant": space.distance_variant,
        "content_n": args.content_n,
    }

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cross_topic_probe.json"
    json_path.write_text(
        json.dumps({"meta": meta, **result}, indent=1), encoding="utf-8"
    )
    logger.info("Wrote %s", json_path)
    md_path = output_dir / "cross_topic_probe.md"
    md_path.write_text(build_markdown(result, meta), encoding="utf-8")
    logger.info("Wrote %s", md_path)

    print(f"\nCross-topic probe: top-1 {result['top1_accuracy']:.1%} over "
          f"{result['n_works']} works; "
          f"rho(topic, margin) = "
          f"{result['correlations']['spearman_topic_sim_vs_margin']['rho']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
