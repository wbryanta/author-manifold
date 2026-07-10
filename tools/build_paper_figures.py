#!/usr/bin/env python3
"""Build the paper's print figures (F1-F7) from the frozen evidence files.

Renders print-quality PDF/PNG figures from the frozen evidence files for
``docs/PAPER_DRAFT.md`` (the released renders live in ``docs/figures/``).

Figures (each written as PDF + PNG, serif fonts, colorblind-safe palette):

  F1  Author manifold (UMAP of 78 wave-2 works, colored by author) with the
      400 unprompted AI samples overlaid, one marker per model family.
      UMAP hyperparameters: n_neighbors=5, min_dist=0.05, manhattan metric,
      random_state=0, fitted on the shelf works only, with AI samples
      projected in via ``transform`` — at 78+400 vectors a joint fit
      collapses the shelf into an unreadable blob (verified 2026-06-10;
      joint fits at n_neighbors 5/15/30 all do). Illustrative only; no
      claim rides on it. Needs the optional ``umap-learn`` package for the
      released projection (PCA fallback otherwise, clearly labeled).
  F2  Envelope ladder ([FIGURES-V3] regeneration of the retired W/B distance
      ladder): per target, the author's length-matched (3,000 MFW-token)
      LM-envelope quantiles (p50/p90/p95/p99) with the unprompted-control,
      styled, and completion distance distributions overlaid as horizontal
      intervals; Brinton/Austen human-pastiche panel row alongside
      (descriptive); fw-only primary panel, full-vocabulary secondary.
      Styled and unprompted-control distances are recomputed through the
      identical placement code path as rerun_entry_analysis.py (composed,
      not duplicated) and verified against results2/controls_results.json
      counts before rendering.
  F3  Capacity ceiling: feature-variant comparison (E1 AUC + E2 top-1)
      against the pre-registered gates.
  F4  R3 dimension movement ([FIGURES-V3] re-sourced to the floor-compliant
      run, n=236): forest plot of median per-dimension movement toward the
      style target with bootstrap CIs; MFW chassis highlighted; caption
      states chassis immobility.
  F5  Length sensitivity: E6 in-design curves + PAN'25 per-bin AUC echo.
  F6  ([FIGURES-V3] new) Envelope width vs unprompted-entry rate across all
      15 shelf authors as pseudo-targets — the de-circularized width test
      (fw-only primary r=+0.844, full-vocabulary secondary r=+0.729);
      imitation targets highlighted with their styled rates; Ishiguro
      annotated as the wide-but-distant outlier.
  F7  ([FIGURES-V3] new) Model-matched completion vs named-style entry:
      per-model dumbbells over the matched pools (fw-only primary, 5/5
      informative models completion-higher, sign p=0.031 one-sided;
      full-vocabulary secondary showing the 2/5 reversal); gpt-5 marked
      refused/unmeasurable.

All numbers come from frozen evidence files (Number Freeze v2 registry in
reports/validation/author_space/wave2/PRIMARY_ARTIFACT.md, plus the
Results 2.0 / v0.4 red-team remediation set under
reports/validation/author_space/results2/) — every one of which ships in
this repository:

  data/artifacts/author_space_v1_wave2.json
  data/artifacts/author_space_v1_wave2_fwonly.json
  data/artifacts/lm_envelopes_wave2_{,fwonly_}3000w.json
  reports/validation/author_space/wave2/e4_results.json
  reports/validation/author_space/variant_comparison.json
  reports/validation/author_space/results2/r3_floor_compliant.json
  reports/validation/author_space/results2/entry_results.json
  reports/validation/author_space/results2/controls_results.json
  reports/validation/author_space/results2/completion_results.json
  reports/validation/author_space/e6_results.json
  reports/validation/author_space/pan_benchmark/results.json
  data/ai-longform/manifest.jsonl (+ sample texts, F1/F2 featurization)

Usage
-----
    pip install matplotlib          # and optionally: pip install umap-learn
    python3 tools/build_paper_figures.py \
        [--out-dir docs/figures_rerun] [--skip-f1] [--skip-f2]

Deterministic: UMAP random_state=0; MFW featurization is byte-for-byte
deterministic; everything else is a pure read of frozen JSONs. F2's
recomputed distance distributions are verified against the frozen
results2 counts before rendering (a hard AssertionError otherwise).
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT / "src", ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from author_manifold.author_space import MFWBlock  # noqa: E402

ARTIFACT_DIR = ROOT / "data/artifacts"
ARTIFACT = ARTIFACT_DIR / "author_space_v1_wave2.json"
ARTIFACT_FWONLY = ARTIFACT_DIR / "author_space_v1_wave2_fwonly.json"
ENVELOPES = {
    "full": ARTIFACT_DIR / "lm_envelopes_wave2_3000w.json",
    "fwonly": ARTIFACT_DIR / "lm_envelopes_wave2_fwonly_3000w.json",
}
VALID = ROOT / "reports/validation/author_space"
E4_WAVE2 = VALID / "wave2/e4_results.json"
VARIANTS = VALID / "variant_comparison.json"
R3_FC = VALID / "results2/r3_floor_compliant.json"
ENTRY_R2 = VALID / "results2/entry_results.json"
CONTROLS_R2 = VALID / "results2/controls_results.json"
COMPLETION_R2 = VALID / "results2/completion_results.json"
E6 = VALID / "e6_results.json"
PAN = VALID / "pan_benchmark/results.json"
AI_DIR = ROOT / "data/ai-longform"

# Envelope / floor constants of the Results 2.0 runs (rerun_entry_analysis.py
# defaults; verified against results2/*.json meta blocks at render time).
WINDOW_WORDS = 3000
PRACTICE_FLOOR = 3000

UMAP_SEED = 0  # the recipe of the released renders in docs/figures/

# Print sizing (inches)
SINGLE_COL = 3.3
DOUBLE_COL = 6.8
PNG_DPI = 600

AUTHOR_NAMES = {
    "delillo-don": "DeLillo",
    "didion-joan": "Didion",
    "foster_wallace-david": "Foster Wallace",
    "ishiguro-kazuo": "Ishiguro",
    "mccarthy-cormac": "McCarthy",
    "morrison-toni": "Morrison",
    "murakami-haruki": "Murakami",
    "ondaatje-michael": "Ondaatje",
    "proulx-annie": "Proulx",
    "pynchon-thomas": "Pynchon",
    "robinson-marilynne": "Robinson",
    "saunders-george": "Saunders",
    "sebald-w_g": "Sebald",
    "tokarczuk-olga": "Tokarczuk",
    "whitehead-colson": "Whitehead",
}

# 15 author colors built from Paul Tol's muted + bright qualitative schemes
# (colorblind-aware); grays/blacks are reserved for the AI overlay, and the
# per-author identity is additionally carried by the median-position labels,
# so the palette is not load-bearing on its own.
AUTHOR_COLORS = {
    "delillo-don": "#332288",
    "didion-joan": "#88CCEE",
    "foster_wallace-david": "#44AA99",
    "ishiguro-kazuo": "#117733",
    "mccarthy-cormac": "#999933",
    "morrison-toni": "#DDCC77",
    "murakami-haruki": "#CC6677",
    "ondaatje-michael": "#882255",
    "proulx-annie": "#AA4499",
    "pynchon-thomas": "#4477AA",
    "robinson-marilynne": "#66CCEE",
    "saunders-george": "#228833",
    "sebald-w_g": "#CCBB44",
    "tokarczuk-olga": "#EE6677",
    "whitehead-colson": "#AA3377",
}

MODEL_FAMILY = {
    "claude-fable-5": "Claude",
    "claude-opus-4-8": "Claude",
    "claude-sonnet-4-6": "Claude",
    "claude-haiku-4-5": "Claude",
    "gpt-5": "GPT",
    "gpt-5-mini": "GPT",
    "gemma4:26b": "Open-weights",
    "qwen3.6:35b": "Open-weights",
}
FAMILY_MARKERS = {"Claude": "^", "GPT": "s", "Open-weights": "D"}
FAMILY_ORDER = ["Claude", "GPT", "Open-weights"]

# Okabe-Ito anchors for the quantitative figures
C_BLUE = "#0072B2"
C_VERMILLION = "#D55E00"
C_ORANGE = "#E69F00"
C_SKY = "#56B4E9"
C_GRAY = "#999999"

# Design imitation pairs (generate_ai_longform_corpus.py STYLE_TARGETS)
SCENARIO_TARGET = {
    "irrigation": "mccarthy-cormac",
    "hotel_fire": "didion-joan",
    "night_ferry": "ondaatje-michael",
    "estate_sale": "morrison-toni",
}

DIM_LABELS = {
    "lexical_density": "lexical density",
    "abstract_ratio": "abstract ratio",
    "formality_index": "formality index",
    "complexity_score": "syntactic complexity",
    "paragraph_cv": "paragraph length CV",
    "sentiment_score": "sentiment",
    "repetition_ratio": "repetition ratio",
    "metaphor_per_100": "metaphor density",
    "past_ratio": "past-tense ratio",
    "present_ratio": "present-tense ratio",
    "future_ratio": "future-tense ratio",
    "char_ngram_mean": "char-trigram texture",
    "function_word_ratio_extended": "function-word ratio",
    "self_focus_ratio": "self-focus ratio",
    "sentence_cv": "sentence length CV",
    "certainty_index": "certainty index",
    "ttr": "type-token ratio",
    "vocabulary_richness": "vocabulary richness",
}


def set_print_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [
                "Times New Roman", "Times", "STIXGeneral", "DejaVu Serif",
            ],
            "mathtext.fontset": "stix",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8.5,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 6.8,
            "axes.linewidth": 0.6,
            "axes.edgecolor": "#444444",
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "figure.facecolor": "white",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
        }
    )


def save(fig, out_dir: Path, name: str, captions: list, caption: str) -> None:
    for ext in ("pdf", "png"):
        fig.savefig(out_dir / f"{name}.{ext}", dpi=PNG_DPI)
    plt.close(fig)
    captions.append((name, caption))
    print(f"  wrote {out_dir / name}.{{pdf,png}}")


# ---------------------------------------------------------------------------
# F1 — manifold projection with unprompted AI overlay
# ---------------------------------------------------------------------------

def shelf_vectors(artifact):
    vecs, authors = [], []
    for author, entry in artifact["authors"].items():
        for work in entry["works"]:
            vecs.append(work["mfw_z"])
            authors.append(author)
    return np.asarray(vecs, dtype=float), authors


def featurize_unprompted(artifact):
    """Re-featurize the 400 unprompted AI samples with the frozen MFW block."""
    block = MFWBlock.from_dict(artifact["feature_blocks"]["mfw_delta"])
    rows, vecs = [], []
    with open(AI_DIR / "manifest.jsonl") as fh:
        for line in fh:
            row = json.loads(line)
            if row["condition"] != "unprompted":
                continue
            text = (AI_DIR / row["file_path"]).read_text()
            vecs.append(block.featurize_text(text))
            rows.append(row)
    return rows, np.asarray(vecs, dtype=float)


def project(human_z, ai_z):
    """2D embedding: UMAP fitted on shelf works, AI samples transformed in.

    Hyperparameters: n_neighbors=5, min_dist=0.05, manhattan — matching the
    Delta block's L1 geometry — random_state=0. The fit is restricted to
    the 78 shelf works because a joint fit collapses the shelf when 400 AI
    samples dominate the neighborhood graph (checked at n_neighbors 5/15/30).
    PCA fallback (joint fit) when umap-learn is unavailable.
    """
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            import umap

            mapper = umap.UMAP(
                n_neighbors=5,
                min_dist=0.05,
                metric="manhattan",
                random_state=UMAP_SEED,
            ).fit(human_z)
            emb_h = mapper.embedding_
            emb_ai = mapper.transform(ai_z)
        method = (
            f"UMAP, n_neighbors=5, min_dist=0.05, manhattan metric, seed "
            f"{UMAP_SEED}; fitted on the {len(human_z)} shelf works, AI "
            "samples projected into the fitted embedding"
        )
        return emb_h, emb_ai, method
    except ImportError:
        from sklearn.decomposition import PCA

        stacked = np.vstack([human_z, ai_z])
        emb = PCA(n_components=2, random_state=UMAP_SEED).fit_transform(stacked)
        method = "PCA (2 components, joint fit; umap-learn not installed)"
        n = len(human_z)
        return emb[:n], emb[n:], method


def figure_f1(artifact, out_dir: Path, captions: list) -> None:
    human_z, authors = shelf_vectors(artifact)
    ai_rows, ai_z = featurize_unprompted(artifact)
    emb_h, emb_ai, method = project(human_z, ai_z)
    print(f"  F1 projection: {method}; {len(emb_h)} works + {len(emb_ai)} AI samples")

    fig, ax = plt.subplots(figsize=(DOUBLE_COL, 5.0))
    # AI samples first (under the shelf points), one marker per family
    for family in FAMILY_ORDER:
        idx = [i for i, r in enumerate(ai_rows)
               if MODEL_FAMILY[r["model"]] == family]
        ax.scatter(
            emb_ai[idx, 0], emb_ai[idx, 1],
            marker=FAMILY_MARKERS[family], s=12,
            facecolors="#c8c8c8", edgecolors="#3b3b3b",
            linewidths=0.35, alpha=0.75, zorder=2,
        )
    # Shelf works
    for author in AUTHOR_NAMES:
        idx = [i for i, a in enumerate(authors) if a == author]
        ax.scatter(
            emb_h[idx, 0], emb_h[idx, 1],
            s=30, color=AUTHOR_COLORS[author],
            edgecolors="white", linewidths=0.5, zorder=3,
        )
    # Author labels at median positions (point offsets de-overlap known
    # collisions in the seeded embedding; harmless if the layout shifts)
    label_nudge = {
        "sebald-w_g": (0, 10),
        "ondaatje-michael": (0, -9),
        "proulx-annie": (-14, 6),
        "whitehead-colson": (12, -6),
        "delillo-don": (-10, 5),
        "foster_wallace-david": (0, 7),
        "saunders-george": (-4, -7),
        "robinson-marilynne": (14, 4),
        "murakami-haruki": (-6, -8),
    }
    pts = defaultdict(list)
    for p, a in zip(emb_h, authors):
        pts[a].append(p)
    for author, v in pts.items():
        c = np.median(np.asarray(v), axis=0)
        ax.annotate(
            AUTHOR_NAMES[author], c, xytext=label_nudge.get(author, (0, 0)),
            textcoords="offset points", fontsize=6.8, fontweight="bold",
            color="#1a1a1a", ha="center", va="center", zorder=4,
        )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    handles = [
        Line2D([], [], marker=FAMILY_MARKERS[f], linestyle="", markersize=4.5,
               markerfacecolor="#c8c8c8", markeredgecolor="#3b3b3b",
               markeredgewidth=0.5, label=f"{f} (unprompted AI)")
        for f in FAMILY_ORDER
    ] + [
        Line2D([], [], marker="o", linestyle="", markersize=4.5,
               markerfacecolor="#777777", markeredgecolor="white",
               label="shelf work (colored by author)"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.005),
              ncol=4, frameon=False, handletextpad=0.25, columnspacing=0.9)
    fig.tight_layout()
    save(
        fig, out_dir, "F1_manifold_overlay", captions,
        f"F1 — The author manifold with AI overlay. 2D projection ({method}) "
        "of the 78 wave-2 shelf works (filled circles, colored by author; "
        "labels at author medians) and the 400 unprompted AI samples (gray "
        "markers, one shape per model family). The projection is "
        "illustrative only: all distance and percentile claims are computed "
        "in the full 300-dimension Delta space, and apparent 2D proximity "
        "is not evidence of entry — entry is adjudicated against the "
        "per-author length-matched envelopes (§3.9, §5.2), not in this "
        "projection.",
    )


# ---------------------------------------------------------------------------
# F2 — envelope ladder (per-target LM envelopes + condition distributions)
# ---------------------------------------------------------------------------

def interval_row(ax, y, samples, color, label, n):
    q5, q25, q50, q75, q95 = np.percentile(samples, [5, 25, 50, 75, 95])
    ax.plot([q5, q95], [y, y], color=color, lw=0.9, solid_capstyle="butt",
            zorder=2)
    ax.plot([q25, q75], [y, y], color=color, lw=3.4, solid_capstyle="butt",
            zorder=3)
    ax.plot([q50], [y], marker="o", markersize=4.2, markerfacecolor="white",
            markeredgecolor=color, markeredgewidth=1.0, zorder=4)
    ax.annotate(f"{label}  (n={n})", (0.02, y + 0.34), fontsize=6.8,
                color="#222222", va="bottom",
                xycoords=("axes fraction", "data"), zorder=5,
                bbox=dict(boxstyle="square,pad=0.05", facecolor="white",
                          edgecolor="none", alpha=0.85))


def _load_entry_tool():
    """Import rerun_entry_analysis.py (COMPOSE: reuse its exact placement
    code path — corpus loading, MFW tokenization, truncation, distances —
    so F2's recomputed distributions cannot drift from the evidence run)."""
    import importlib.util

    path = ROOT / "tools/rerun_entry_analysis.py"
    spec = importlib.util.spec_from_file_location("rerun_entry_analysis", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _f2_collect(space_path, vocab, ret, records, scen2target, completion, entry):
    """Per-target distance distributions for one vocabulary, recomputed
    through rerun_entry_analysis's placement path, plus the frozen
    completion placements and Brinton/Austen chunks."""
    from author_manifold.author_space import AuthorRelativeSpace

    space = AuthorRelativeSpace.from_artifact(space_path)
    styled = defaultdict(list)
    for rec in records:
        if (rec["condition"] in ret.STYLED_CONDITIONS
                and rec["_n_tokens"] >= PRACTICE_FLOOR):
            dists = ret.author_distances(space, rec["_tokens"][:WINDOW_WORDS])
            styled[rec["style_target"]].append(dists[rec["style_target"]])
    unprompted = defaultdict(list)
    for rec in records:
        if (rec["condition"] == "unprompted"
                and rec["_n_tokens"] >= PRACTICE_FLOOR
                and rec["scenario_id"] in scen2target):
            target = scen2target[rec["scenario_id"]]
            dists = ret.author_distances(space, rec["_tokens"][:WINDOW_WORDS])
            unprompted[target].append(dists[target])
    completion_d = defaultdict(list)
    for p in completion["entry"][vocab]["placements"]:
        completion_d[p["target"]].append(p["target_distance"])
    hb = entry["human_baselines"][vocab]
    brinton = [c["target_distance"] for c in hb["chunks"]]
    return {
        "styled": styled, "unprompted": unprompted,
        "completion": completion_d,
        "brinton": brinton, "austen_quantiles": hb["lm_quantiles"],
        "brinton_entered": hb["entered_p90"],
    }


def _f2_verify(vocab, data, env, controls, completion):
    """Recomputed entry counts must reproduce the frozen evidence exactly."""
    ctl = controls["unprompted_entry_control"][vocab]
    for target, row in ctl["per_target"].items():
        p90 = env["authors"][target]["quantiles"]["p90"]
        for cond, k_key, n_key in (
            ("styled", "styled_entered", "styled_n"),
            ("unprompted", "unprompted_entered", "unprompted_n"),
        ):
            d = data[cond][target]
            entered = sum(1 for x in d if x <= p90)
            if len(d) != row[n_key] or entered != row[k_key]:
                raise AssertionError(
                    f"F2 {vocab}/{target}/{cond}: recomputed {entered}/{len(d)}"
                    f" != evidence {row[k_key]}/{row[n_key]}")
    comp_entered = sum(
        1 for t, dl in data["completion"].items()
        for x in dl if x <= env["authors"][t]["quantiles"]["p90"])
    if comp_entered != completion["entry"][vocab]["entered_p90"]:
        raise AssertionError(
            f"F2 {vocab}/completion: {comp_entered} != "
            f"{completion['entry'][vocab]['entered_p90']}")
    print(f"  F2 verify [{vocab}]: per-target styled/unprompted counts and "
          f"completion entered_p90={comp_entered} match evidence")


def _f2_panel(ax, groups, title):
    """One vocabulary panel: per group an envelope band (shaded to p90,
    ticks at p50/p90/p95/p99) and condition interval rows; quantile-level
    labels on the first group only."""
    import matplotlib.patches as mpatches

    row_h, head_h, foot_h = 0.95, 1.35, 0.55
    # x-range across all groups
    lo = min(min(g["quantiles"]["p50"] for g in groups),
             min(np.percentile(d, 5) for g in groups
                 for _, d, _ in g["rows"]))
    hi = max(max(g["quantiles"]["p99"] for g in groups),
             max(np.percentile(d, 95) for g in groups
                 for _, d, _ in g["rows"]))
    xlo, xhi = lo - 0.06, hi + 0.05

    y_top = 0.0
    first = True
    for g in groups:
        q = g["quantiles"]
        n_rows = len(g["rows"])
        band_top = y_top - head_h + 0.45
        band_bot = y_top - head_h - (n_rows - 1) * row_h - 0.45
        ax.add_patch(mpatches.Rectangle(
            (xlo, band_bot), q["p90"] - xlo, band_top - band_bot,
            facecolor="#dcebf5", edgecolor="none", zorder=0))
        for level, style, lw in (("p50", (0, (1, 1.2)), 0.7),
                                 ("p90", "solid", 1.0),
                                 ("p95", (0, (4, 2)), 0.7),
                                 ("p99", (0, (4, 2)), 0.7)):
            ax.plot([q[level], q[level]], [band_bot, band_top],
                    color=C_BLUE, lw=lw, linestyle=style, zorder=1,
                    solid_capstyle="butt")
            if first:
                ax.annotate(level, (q[level], band_top + 0.06),
                            fontsize=5.6, color=C_BLUE, ha="center",
                            va="bottom")
        ax.annotate(g["title"], (0.0, y_top - 0.42),
                    xycoords=("axes fraction", "data"), fontsize=7.0,
                    fontweight="bold", color="#111111", va="center")
        for i, (label, dist, color) in enumerate(g["rows"]):
            y = y_top - head_h - i * row_h
            q5, q25, q50, q75, q95 = np.percentile(dist, [5, 25, 50, 75, 95])
            ax.plot([q5, q95], [y, y], color=color, lw=0.9,
                    solid_capstyle="butt", zorder=3)
            ax.plot([q25, q75], [y, y], color=color, lw=3.0,
                    solid_capstyle="butt", zorder=4)
            ax.plot([q50], [y], marker="o", markersize=3.6,
                    markerfacecolor="white", markeredgecolor=color,
                    markeredgewidth=0.9, zorder=5)
            ax.annotate(label, (0.015, y + 0.30), fontsize=5.9,
                        color="#222222", va="bottom",
                        xycoords=("axes fraction", "data"), zorder=6,
                        bbox=dict(boxstyle="square,pad=0.05",
                                  facecolor="white", edgecolor="none",
                                  alpha=0.8))
        first = False
        y_top = band_bot - foot_h
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(y_top + 0.15, 0.65)
    ax.set_yticks([])
    ax.set_xlabel("Burrows Delta distance to target (3,000-token windows)")
    ax.set_title(title, fontsize=7.6)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)


def figure_f2(entry, controls, completion, out_dir: Path, captions: list,
              ) -> None:
    ret = _load_entry_tool()
    records = ret.load_corpus(AI_DIR)
    scen2target = controls["meta"]["scenario_target_binding"]
    assert scen2target == SCENARIO_TARGET, "scenario binding drifted"
    assert controls["meta"]["window_words"] == WINDOW_WORDS
    assert controls["meta"]["practice_floor"] == PRACTICE_FLOOR

    target_order = ["mccarthy-cormac", "morrison-toni", "didion-joan",
                    "ondaatje-michael"]  # descending fw-only envelope width
    cond_colors = {"unprompted control": "#5a5a5a",
                   "styled (prompt+exemplar)": C_ORANGE,
                   "completion": C_VERMILLION}

    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, 4.7))
    panel_titles = {
        "fwonly": "function words only (primary)",
        "full": "full vocabulary (secondary; topic-porous)",
    }
    space_paths = {"full": ARTIFACT, "fwonly": ARTIFACT_FWONLY}
    inc = {}
    for ax, vocab in zip(axes, ("fwonly", "full")):
        env = json.loads(ENVELOPES[vocab].read_text())
        data = _f2_collect(space_paths[vocab], vocab, ret, records,
                           scen2target, completion, entry)
        _f2_verify(vocab, data, env, controls, completion)
        ctl = controls["unprompted_entry_control"][vocab]
        inc[vocab] = ctl["increment"]
        groups = []
        for t in target_order:
            q = env["authors"][t]["quantiles"]
            row_ctl = ctl["per_target"][t]
            n_comp = len(data["completion"][t])
            k_comp = sum(1 for x in data["completion"][t] if x <= q["p90"])
            groups.append({
                "title": f"{AUTHOR_NAMES[t]}  (LM p90 = {q['p90']:.3f})",
                "quantiles": q,
                "rows": [
                    (f"unprompted control  "
                     f"{row_ctl['unprompted_entered']}/{row_ctl['unprompted_n']} enter",
                     data["unprompted"][t], cond_colors["unprompted control"]),
                    (f"styled  {row_ctl['styled_entered']}/{row_ctl['styled_n']} enter",
                     data["styled"][t], cond_colors["styled (prompt+exemplar)"]),
                    (f"completion  {k_comp}/{n_comp} enter",
                     data["completion"][t], cond_colors["completion"]),
                ],
            })
        bre = data["brinton_entered"]
        groups.append({
            "title": "Austen (PD shelf) — human-pastiche reference",
            "quantiles": data["austen_quantiles"],
            "rows": [
                (f"Brinton pastiche (1913)  {bre['entered']}/{bre['n']} enter",
                 data["brinton"], C_BLUE),
            ],
        })
        _f2_panel(ax, groups, panel_titles[vocab])
    fig.tight_layout(w_pad=1.4)

    fw, fu = inc["fwonly"], inc["full"]
    save(
        fig, out_dir, "F2_envelope_ladder", captions,
        "F2 — The envelope ladder. Per imitation target, the author's "
        "length-matched envelope (LM-W; 3,000 MFW-token windows, work-level "
        "LOO): shading marks the inside-envelope region up to p90, vertical "
        "ticks the p50/p90/p95/p99 quantiles. Horizontal intervals (5th-95th "
        "range, IQR, median) show the distance-to-target distributions of "
        "the unprompted control (gray; the base rate every styled rate is "
        "read against), styled samples (orange; prompt + exemplar, "
        "floor-compliant n=236), and model-matched completions (vermillion). "
        "Left, function-words-only (primary): styled entry 72/236 (30.5%) "
        "over an unprompted base of 13/121 (10.7%) — a controlled increment "
        f"of {fw['styled_minus_unprompted_pp']:+.1f} pp "
        f"[{fw['cluster_bootstrap_ci95_pp'][0]:+.1f}, "
        f"{fw['cluster_bootstrap_ci95_pp'][1]:+.1f}] that excludes zero. "
        "Right, full vocabulary (secondary): the increment collapses to "
        f"{fu['styled_minus_unprompted_pp']:+.1f} pp "
        f"[{fu['cluster_bootstrap_ci95_pp'][0]:+.1f}, "
        f"{fu['cluster_bootstrap_ci95_pp'][1]:+.1f}] — full-vocabulary "
        "'entry' is mostly envelope porosity to AI house style on an "
        "adjacent scenario. Envelope widths are heterogeneous (McCarthy's "
        "p90 is 1.27x Ondaatje's, fw-only), which is why no pooled rate is "
        "quoted without its per-target ladder. Bottom row: the Brinton 1913 "
        "Austen pastiche against Austen's PD-shelf envelope — a descriptive "
        "human-imitation juxtaposition (chunks of one novel, not "
        "independent), not a matched control.",
    )


# ---------------------------------------------------------------------------
# F3 — capacity ceiling (variant comparison)
# ---------------------------------------------------------------------------

def figure_f3(variants, out_dir: Path, captions: list) -> None:
    keep = ["d18", "d18_weighted", "mfw_delta", "combined_alpha0.3"]
    labels = ["D18", "D18\n($\\eta^2$-wtd)", "MFW Delta\n(selected)",
              "blend\n$\\alpha$=0.3"]
    rows = {r["label"]: r for r in variants["rows"]}
    aucs = [rows[k]["e1_auc"] for k in keep]
    top1 = [rows[k]["top1"] for k in keep]
    colors = [C_GRAY, C_GRAY, C_BLUE, C_SKY]

    fig, axes = plt.subplots(1, 2, figsize=(SINGLE_COL, 1.9))
    for ax, vals, gate, title, fmt, gate_va in (
        (axes[0], aucs, 0.90, "E1 separation AUC", "{:.3f}", "top"),
        (axes[1], top1, 0.70, "E2 top-1 attribution", "{:.0%}", "bottom"),
    ):
        x = np.arange(len(keep))
        bars = ax.bar(x, vals, width=0.62, color=colors, edgecolor="#333333",
                      linewidth=0.5, zorder=2)
        ax.axhline(gate, color=C_VERMILLION, lw=0.9, linestyle=(0, (4, 2)),
                   zorder=3)
        dy = -1.5 if gate_va == "top" else 1.5
        ax.annotate(f"gate {fmt.format(gate)}", (0.02, gate),
                    xycoords=("axes fraction", "data"),
                    xytext=(0, dy), textcoords="offset points",
                    fontsize=5.8, color=C_VERMILLION, ha="left", va=gate_va)
        for xi, v in zip(x, vals):
            ax.annotate(fmt.format(v), (xi, v), xytext=(0, 1.5),
                        textcoords="offset points", ha="center", fontsize=5.6)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=5.6)
        ax.set_ylim(0.5, 1.02)
        ax.set_title(title, fontsize=7.2)
        ax.tick_params(axis="y", labelsize=6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        bars[2].set_zorder(3)
    fig.tight_layout(w_pad=1.2)
    save(
        fig, out_dir, "F3_capacity_ceiling", captions,
        "F3 — The capacity ceiling. Feature-variant comparison on the wave-1 "
        "gold shelf (11 authors, 59 works) against the pre-registered gates "
        "(dashed): the 18 interpretable dimensions (D18) are individually "
        "valid but collectively miss both gates; the function-word MFW Delta "
        "block (selected variant, dark blue) clears them. Identity rides on "
        "function words; the dimensions carry interpretation.",
    )


# ---------------------------------------------------------------------------
# F4 — R3 dimension movement forest plot (floor-compliant run)
# ---------------------------------------------------------------------------

def figure_f4(r3, out_dir: Path, captions: list) -> None:
    assert r3["meta"]["n_styled_analyzed"] == 236, (
        "F4 must render from the floor-compliant run (n=236); the "
        "native-length n=318 source is retired")
    table = r3["table"]
    dims = [d for d in table if d != "mfw_delta"]
    dims.sort(key=lambda d: table[d]["median_movement"], reverse=True)
    order = dims + ["mfw_delta"]

    fig, ax = plt.subplots(figsize=(SINGLE_COL + 0.1, 4.5))
    ys = np.arange(len(order))[::-1]
    for y, dim in zip(ys, order):
        row = table[dim]
        med = row["median_movement"]
        lo, hi = row["median_movement_ci95"]
        sig = row.get("significant_holm_05", False)
        is_mfw = dim == "mfw_delta"
        if is_mfw:
            color = "#000000"
            ax.axhspan(y - 0.45, y + 0.45, color="#f0e6dc", zorder=0)
            label = "MFW Delta chassis"
        else:
            if not sig:
                color = "#b8b8b8"
            elif med > 0:
                color = C_BLUE
            else:
                color = C_VERMILLION
            label = DIM_LABELS.get(dim, dim)
        ax.plot([lo, hi], [y, y], color=color, lw=1.0, zorder=2,
                solid_capstyle="butt")
        ax.plot([med], [y], marker="D" if is_mfw else "o",
                markersize=4.0 if is_mfw else 3.4,
                markerfacecolor=color, markeredgecolor="white",
                markeredgewidth=0.4, zorder=3)
        weight = "bold" if is_mfw else "normal"
        ax.annotate(label, (-0.02, y), xycoords=("axes fraction", "data"),
                    ha="right", va="center", fontsize=6.6, color="#222222",
                    fontweight=weight)
    ax.axvline(0, color="#555555", lw=0.7, zorder=1)
    ax.axhline(ys[-1] + 0.6, color="#888888", lw=0.5, linestyle=(0, (2, 2)))
    ax.set_ylim(-0.7, len(order) - 0.3)
    ax.set_yticks([])
    ax.set_xlabel(
        "median movement toward target\n"
        "(pooled-shelf $\\sigma$; MFW row: Delta units)"
    )
    ax.annotate("toward target $\\rightarrow$", (0.99, 1.005),
                xycoords="axes fraction", ha="right", fontsize=6.4,
                color=C_BLUE)
    ax.annotate("$\\leftarrow$ away", (0.01, 1.005), xycoords="axes fraction",
                ha="left", fontsize=6.4, color=C_VERMILLION)
    handles = [
        Line2D([], [], marker="o", linestyle="", markersize=4,
               markerfacecolor=C_BLUE, markeredgecolor="white",
               label="toward (Holm-sig.)"),
        Line2D([], [], marker="o", linestyle="", markersize=4,
               markerfacecolor=C_VERMILLION, markeredgecolor="white",
               label="away (Holm-sig.)"),
        Line2D([], [], marker="o", linestyle="", markersize=4,
               markerfacecolor="#b8b8b8", markeredgecolor="white",
               label="not significant"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False,
              borderaxespad=0.1, handletextpad=0.2)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    mfw = table["mfw_delta"]
    med = mfw["median_movement"]
    lo_ci, hi_ci = mfw["median_movement_ci95"]
    closure_pct = 100 * mfw["median_gap_closure"]  # field is fractional
    save(
        fig, out_dir, "F4_dimension_movement", captions,
        "F4 — Where the gap lives (R3, floor-compliant run). Median "
        "per-dimension movement of styled samples toward their target "
        "author relative to matched unprompted samples (n=236 samples at or "
        "above the 3,000-MFW-token practice floor; seeded bootstrap 95% "
        "CIs; sign tests Holm-corrected across 19 tests). "
        "Lexical-diversity texture and tense/affect transfer (blue); "
        "char-trigram texture, function-word ratio, lexical density, and "
        "sentence-length CV move away (vermillion); certainty drops out of "
        "Holm significance in the floor-compliant run; the MFW Delta "
        "chassis (highlighted bottom row, "
        "Delta units) is immobile: median movement "
        f"{med:+.3f} Delta [{lo_ci:+.3f}, {hi_ci:+.3f}], Holm p = "
        f"{mfw['sign_test_p_holm']:.1f}, gap closure {closure_pct:+.1f}%.",
    )
    print(f"  F4 chassis: median={med:+.4f} ci=[{lo_ci:+.4f},{hi_ci:+.4f}] "
          f"holm_p={mfw['sign_test_p_holm']:.3f} closure={closure_pct:+.2f}%")


# ---------------------------------------------------------------------------
# F5 — length sensitivity: E6 + PAN echo
# ---------------------------------------------------------------------------

def figure_f5(e6, pan, artifact, variants, out_dir: Path, captions: list) -> None:
    wave1_authors = set(variants["meta"]["authors_filter"])
    full_words = np.median([
        w["word_count"]
        for a, entry in artifact["authors"].items() if a in wave1_authors
        for w in entry["works"]
    ])
    xs, top1, auc = [], [], []
    for r in e6["per_length"]:
        xs.append(r["window_words"])
        top1.append(r["top1_accuracy"])
        auc.append(r["auc"])
    ref = e6["full_work_reference"]
    xs.append(full_words)
    top1.append(ref["top1_accuracy"])
    auc.append(ref["auc"])

    pan_bins = pan["wave2"]["by_length"]
    pan_x = [400, 1150, 2250]  # bin midpoints (<800, 800-1500, 1500-3000)
    pan_keys = ["<800", "800-1500", "1500-3000"]
    pan_auc = [pan_bins[k]["auc"] for k in pan_keys]
    pan_n = [pan_bins[k]["n"] for k in pan_keys]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(SINGLE_COL, 3.5), sharex=True,
        gridspec_kw={"hspace": 0.12},
    )
    # Panel A — E6, in-design
    ax1.plot(xs, top1, marker="o", markersize=3.6, lw=1.1, color=C_BLUE,
             label="E6 LOO top-1 attribution")
    ax1.plot(xs, auc, marker="s", markersize=3.2, lw=1.0, color=C_SKY,
             linestyle=(0, (5, 2)), label="E6 within/between AUC")
    ax1.axhline(0.70, color=C_VERMILLION, lw=0.8, linestyle=(0, (4, 2)))
    ax1.annotate("E2 gate (top-1 $\\geq$ 0.70)", (0.98, 0.69),
                 xycoords=("axes fraction", "data"), ha="right", va="top",
                 fontsize=6.0, color=C_VERMILLION)
    ax1.set_ylim(0.3, 1.03)
    ax1.set_ylabel("in-design (shelf windows)", fontsize=6.8)
    ax1.legend(loc="lower right", frameon=False)
    # Panel B — PAN'25, out-of-design echo
    ax2.plot(pan_x, pan_auc, marker="D", markersize=3.6, lw=1.1,
             color=C_VERMILLION, label="PAN'25 detection ROC AUC")
    ax2.axhline(0.5, color="#777777", lw=0.7, linestyle=(0, (2, 2)))
    ax2.annotate("chance", (pan_x[0] * 1.02, 0.51), fontsize=6.0,
                 color="#777777")
    for x, a, n in zip(pan_x, pan_auc, pan_n):
        ax2.annotate(f"n={n}", (x, a), xytext=(2, -8),
                     textcoords="offset points", fontsize=5.8,
                     color="#444444")
    ax2.set_ylim(0.3, 1.03)
    ax2.set_xscale("log")
    ax2.set_xticks([800, 1500, 3000, 10000, 30000, 100000])
    ax2.set_xticklabels(["800", "1.5k", "3k", "10k", "30k", "100k"])
    ax2.set_xlabel("text length (words, log scale)")
    ax2.set_ylabel("out-of-design (PAN'25)", fontsize=6.8)
    ax2.legend(loc="lower right", frameon=False)
    for ax in (ax1, ax2):
        ax.tick_params(axis="both", labelsize=6.4)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.tight_layout()
    save(
        fig, out_dir, "F5_length_sensitivity", captions,
        "F5 — Length sensitivity, in-design and out. Top: E6 leave-one-out "
        "attribution and within/between AUC on non-overlapping shelf windows "
        "(800 / 1,500 / 3,000 words and full works, plotted at the median "
        f"work length, {int(full_words):,} words); attribution falls below "
        "the E2 gate at 800 words. Bottom: the external echo — nearest-"
        "author distance as a binary AI-vs-human scorer on PAN'25 recovers "
        "monotonically with length (AUC 0.402 / 0.570 / 0.856, plotted at "
        "bin midpoints), and inverts below the same floor; the benchmark "
        "has no texts above 3,000 words.",
    )


# ---------------------------------------------------------------------------
# F6 — envelope width vs unprompted entry, 15 pseudo-targets (G7)
# ---------------------------------------------------------------------------

F6_LABELED = {  # author -> annotation offset (points)
    "murakami-haruki": (-2, 6),
    "foster_wallace-david": (2, -9),
    "mccarthy-cormac": (-26, 4),
    "ishiguro-kazuo": (4, 4),
    "didion-joan": (7, -4),
    "morrison-toni": (7, -6),
    "ondaatje-michael": (-12, -10),
}


def _f6_panel(ax, width_block, styled_per_target, title, label_all):
    pa = width_block["pseudo_target_all_authors"]["per_author"]
    r = width_block["pseudo_target_all_authors"]["pearson_r_width_vs_rate"]
    r_lo, r_hi = width_block["pseudo_target_all_authors"][
        "pearson_r_ci95_fisher_z"]
    xs = np.array([row["lm_p90"] for row in pa.values()])
    ys = np.array([100 * row["rate"] for row in pa.values()])
    # least-squares trend (descriptive)
    b1, b0 = np.polyfit(xs, ys, 1)
    gx = np.linspace(xs.min() - 0.02, xs.max() + 0.02, 2)
    ax.plot(gx, b1 * gx + b0, color="#bbbbbb", lw=0.8, zorder=1)
    for author, row in pa.items():
        is_target = row["is_imitation_target"]
        ax.scatter(
            [row["lm_p90"]], [100 * row["rate"]],
            s=22 if is_target else 16,
            color=C_VERMILLION if is_target else C_BLUE,
            edgecolors="white", linewidths=0.4, zorder=3)
        if is_target:
            styled = 100 * styled_per_target[author]["styled_rate"]
            ax.plot([row["lm_p90"]] * 2, [100 * row["rate"], styled],
                    color=C_VERMILLION, lw=0.7, linestyle=(0, (2, 1.6)),
                    zorder=2)
            ax.plot([row["lm_p90"]], [styled], marker="D", markersize=3.4,
                    markerfacecolor="white", markeredgecolor=C_VERMILLION,
                    markeredgewidth=0.9, zorder=3)
        if label_all and author in F6_LABELED:
            ax.annotate(AUTHOR_NAMES[author],
                        (row["lm_p90"], 100 * row["rate"]),
                        xytext=F6_LABELED[author],
                        textcoords="offset points", fontsize=5.8,
                        color="#222222")
    if label_all:
        ish = pa["ishiguro-kazuo"]
        ax.annotate("wide but distant",
                    (ish["lm_p90"], 100 * ish["rate"]), xytext=(4, 12),
                    textcoords="offset points", fontsize=5.6,
                    color="#555555", fontstyle="italic")
    ax.annotate(f"Pearson $r$ = {r:+.3f}\n[{r_lo:+.2f}, {r_hi:+.2f}]",
                (0.03, 0.97), xycoords="axes fraction", ha="left", va="top",
                fontsize=6.4, color="#222222")
    ax.set_xlabel("LM envelope width (fw p90, Delta)"
                  if "function" in title else "LM envelope width (p90, Delta)")
    ax.set_title(title, fontsize=7.4)
    ax.set_ylim(-4, 104)
    ax.tick_params(axis="both", labelsize=6.4)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return r


def figure_f6(controls, out_dir: Path, captions: list) -> None:
    ctl = controls["unprompted_entry_control"]
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, 2.6))
    r_fw = _f6_panel(axes[0], controls["width"]["fwonly"],
                     ctl["fwonly"]["per_target"],
                     "function words only (primary)", True)
    r_full = _f6_panel(axes[1], controls["width"]["full"],
                       ctl["full"]["per_target"],
                       "full vocabulary (secondary)", False)
    axes[0].set_ylabel("unprompted samples entering @p90 (%)")
    handles = [
        Line2D([], [], marker="o", linestyle="", markersize=4,
               markerfacecolor=C_BLUE, markeredgecolor="white",
               label="shelf author (pseudo-target)"),
        Line2D([], [], marker="o", linestyle="", markersize=4.4,
               markerfacecolor=C_VERMILLION, markeredgecolor="white",
               label="imitation target"),
        Line2D([], [], marker="D", linestyle=(0, (2, 1.6)), lw=0.7,
               color=C_VERMILLION, markersize=3.6,
               markerfacecolor="white", markeredgecolor=C_VERMILLION,
               label="same target, styled rate"),
    ]
    axes[1].legend(handles=handles, loc="upper center",
                   bbox_to_anchor=(0.55, 1.0), frameon=False,
                   handletextpad=0.3, borderaxespad=0.1)
    fig.tight_layout(w_pad=1.6)
    spearman = controls["width"]["fwonly"]["pseudo_target_all_authors"]
    save(
        fig, out_dir, "F6_width_vs_entry", captions,
        "F6 — Envelope width vs entry, de-circularized. All 15 shelf "
        "authors as pseudo-targets: each of the 309 floor-compliant "
        "unprompted samples is placed against every author's LM envelope, "
        "and the per-author entry rate at p90 is plotted against the "
        "envelope's p90 width. Function-words-only (left, primary): "
        f"Pearson r = {r_fw:+.3f} [+0.59, +0.95] (Fisher z; Spearman rho = "
        f"{spearman['spearman_rho']:+.2f}, p = "
        f"{spearman['spearman_p']:.4f}); full vocabulary (right, "
        f"secondary): r = {r_full:+.3f}. Entry rates track how wide the "
        "target's envelope is, not who is being imitated: wide-envelope "
        "authors (Murakami, Foster Wallace, McCarthy) absorb 49-79% of "
        "never-prompted AI text, while Ishiguro is the informative outlier "
        "— a wide envelope that admits almost nothing (7.1%) because AI "
        "house style is far from it in direction, not just in scale. The "
        "four imitation targets (vermillion) carry their styled rates "
        "(open diamonds) for reference; the styled-minus-unprompted "
        "increment, not the raw styled rate, is the imitation effect "
        "(Figure F2).",
    )
    print(f"  F6 r: fwonly={r_fw:+.4f} full={r_full:+.4f}")


# ---------------------------------------------------------------------------
# F7 — model-matched completion vs named-style entry (G2)
# ---------------------------------------------------------------------------

MODEL_NAMES = {
    "claude-fable-5": "Claude Fable 5",
    "claude-opus-4-8": "Claude Opus 4.8",
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "claude-haiku-4-5": "Claude Haiku 4.5",
    "gpt-5": "GPT-5",
    "gpt-5-mini": "GPT-5-mini",
    "gemma4:26b": "Gemma 4 26B",
    "qwen3.6:35b": "Qwen 3.6 35B",
}


def _f7_panel(ax, mm, gpt5_styled, title, show_labels, order):
    per_model = mm["per_model"]
    ys = np.arange(len(order) + 1)[::-1] + 0.6  # +1 row for refused gpt-5
    for y, model in zip(ys[:-1], order):
        row = per_model[model]
        c = 100 * row["completion_rate"]
        s = 100 * row["styled_rate"]
        ax.plot([s, c], [y, y], color="#888888", lw=1.0, zorder=2,
                solid_capstyle="butt")
        ax.plot([s], [y], marker="s", markersize=3.8,
                markerfacecolor="white", markeredgecolor=C_BLUE,
                markeredgewidth=1.0, zorder=3)
        ax.plot([c], [y], marker="o", markersize=4.0,
                markerfacecolor=C_VERMILLION, markeredgecolor="white",
                markeredgewidth=0.4, zorder=4)
        ax.annotate(
            f"{row['completion_entered']}/{row['completion_n']} vs "
            f"{row['styled_entered']}/{row['styled_n']}",
            (max(c, s), y), xytext=(5, 0), textcoords="offset points",
            fontsize=5.4, color="#555555", va="center")
        if show_labels:
            ax.annotate(MODEL_NAMES[model], (-0.02, y),
                        xycoords=("axes fraction", "data"), ha="right",
                        va="center", fontsize=6.4, color="#222222")
    # gpt-5: refused all completions; styled point only
    y = ys[-1]
    ax.axhline(y + 0.5, color="#aaaaaa", lw=0.5, linestyle=(0, (2, 2)))
    s = 100 * gpt5_styled["rate_p90"]
    ax.plot([s], [y], marker="s", markersize=3.8, markerfacecolor="white",
            markeredgecolor=C_BLUE, markeredgewidth=1.0, zorder=3)
    ax.annotate("completion refused (0/20 compliant)", (s, y),
                xytext=(-5, 0), textcoords="offset points", fontsize=5.4,
                color="#999999", va="center", ha="right", fontstyle="italic")
    if show_labels:
        ax.annotate(MODEL_NAMES["gpt-5"], (-0.02, y),
                    xycoords=("axes fraction", "data"), ha="right",
                    va="center", fontsize=6.4, color="#999999")
    st = mm["sign_test"]
    ax.annotate(
        f"sign test: {st['completion_higher']}/{st['n_informative']} "
        f"completion-higher\none-sided p = "
        f"{st['exact_p_one_sided_greater']:.4f}",
        (0.98, 0.40), xycoords="axes fraction", ha="right", va="center",
        fontsize=5.8, color="#222222")
    ax.set_xlim(-3, 100)
    ax.set_ylim(0, ys[0] + 0.7)
    ax.set_yticks([])
    ax.set_xlabel("entry @p90 (%)")
    ax.set_title(title, fontsize=7.4)
    ax.tick_params(axis="x", labelsize=6.4)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)


def figure_f7(controls, entry, out_dir: Path, captions: list) -> None:
    mm = controls["model_matched_completion"]["vocab"]
    # One shared row order (fw-only completion rate, descending) so the
    # left-panel model labels are valid for both panels.
    order = sorted(
        mm["fwonly"]["per_model"],
        key=lambda m: mm["fwonly"]["per_model"][m]["completion_rate"],
        reverse=True)
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COL, 2.5),
                             gridspec_kw={"wspace": 0.06})
    _f7_panel(axes[0], mm["fwonly"],
              entry["entry"]["fwonly"]["primary"]["per_model"]["gpt-5"],
              "function words only (primary)", True, order)
    _f7_panel(axes[1], mm["full"],
              entry["entry"]["full"]["primary"]["per_model"]["gpt-5"],
              "full vocabulary (secondary)", False, order)
    handles = [
        Line2D([], [], marker="s", linestyle="", markersize=4,
               markerfacecolor="white", markeredgecolor=C_BLUE,
               markeredgewidth=1.0, label="named-style (styled)"),
        Line2D([], [], marker="o", linestyle="", markersize=4.2,
               markerfacecolor=C_VERMILLION, markeredgecolor="white",
               label="completion (no author named)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
               bbox_to_anchor=(0.53, -0.14), handletextpad=0.3,
               columnspacing=1.2)
    fig.tight_layout()
    st = mm["fwonly"]["sign_test"]
    pooled_c = mm["fwonly"]["pooled_matched"]["completion"]
    pooled_s = mm["fwonly"]["pooled_matched"]["styled"]
    save(
        fig, out_dir, "F7_completion_vs_styled", captions,
        "F7 — Model-matched completion vs named-style entry (G2). Per-model "
        "dumbbells over the matched pools (models with at least one "
        "compliant completion and at least one primary styled sample); "
        "annotations give entered/n for completion vs styled. "
        "Function-words-only (left, primary): every informative model "
        f"enters more under completion than under named-style prompting "
        f"({st['completion_higher']}/{st['n_informative']}, exact one-sided "
        f"p = {st['exact_p_one_sided_greater']:.4f}; Haiku 4.5 ties at "
        f"0/2 vs 0/17); pooled matched, completion "
        f"{pooled_c['entered']}/{pooled_c['n']} "
        f"({100 * pooled_c['rate']:.1f}%) vs styled "
        f"{pooled_s['entered']}/{pooled_s['n']} "
        f"({100 * pooled_s['rate']:.1f}%). Naming the author adds nothing "
        "that continuing the author's own text does not already achieve. "
        "Full vocabulary (right, secondary): the direction reverses for "
        "2 of 5 informative models — the completion prompt carries the "
        "source passage's content, so the fw-only framing is primary. "
        "GPT-5, the best styled model, refused every completion prompt "
        "(0/20 compliant) and is unmeasurable in this comparison; the "
        "pooled 'parity' previously reported was that composition "
        "artifact.",
    )


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build Tier 1 paper print figures F1-F7 (PDF+PNG) from "
                    "the frozen evidence files (Number Freeze v2 + "
                    "Results 2.0).")
    parser.add_argument(
        "--out-dir", type=Path,
        default=ROOT / "docs/figures_rerun",
        help="output directory (default: docs/figures_rerun, so the "
             "released renders under docs/figures/ stay pristine for "
             "comparison)")
    parser.add_argument(
        "--skip-f1", action="store_true",
        help="skip F1 (re-featurizes the 400 unprompted sample texts)")
    parser.add_argument(
        "--skip-f2", action="store_true",
        help="skip F2 (re-featurizes the styled + unprompted samples "
             "through the rerun_entry_analysis placement path)")
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    set_print_style()

    artifact = json.loads(ARTIFACT.read_text())
    variants = json.loads(VARIANTS.read_text())
    r3 = json.loads(R3_FC.read_text())
    e6 = json.loads(E6.read_text())
    pan = json.loads(PAN.read_text())
    entry = json.loads(ENTRY_R2.read_text())
    controls = json.loads(CONTROLS_R2.read_text())
    completion = json.loads(COMPLETION_R2.read_text())

    captions: list = []
    if not args.skip_f1:
        figure_f1(artifact, out_dir, captions)
    if not args.skip_f2:
        figure_f2(entry, controls, completion, out_dir, captions)
    figure_f3(variants, out_dir, captions)
    figure_f4(r3, out_dir, captions)
    figure_f5(e6, pan, artifact, variants, out_dir, captions)
    figure_f6(controls, out_dir, captions)
    figure_f7(controls, entry, out_dir, captions)

    cap_path = out_dir / "captions.md"
    lines = [
        "# Paper figures — generated captions",
        "",
        "Generated by `tools/build_paper_figures.py` "
        "(seeded; all numbers from the frozen evidence files — Number "
        "Freeze v2 registry in "
        "`reports/validation/author_space/wave2/PRIMARY_ARTIFACT.md` plus "
        "the Results 2.0 set in "
        "`reports/validation/author_space/results2/`). Regenerate with:",
        "",
        "    python3 tools/build_paper_figures.py",
        "",
    ]
    for name, caption in captions:
        lines += [f"## {name}", "", caption, ""]
    cap_path.write_text("\n".join(lines))
    print(f"  wrote {cap_path}")


if __name__ == "__main__":
    main()
