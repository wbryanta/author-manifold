#!/usr/bin/env python3
"""Folk "AI tells" vs the corpora — do the popular tells discriminate?

Popular guidance (14-item tell lists circulating in 2024-2026) claims AI
text is identifiable from surface habits: em dashes, "not X, it's Y"
constructions, rule-of-three tricolons, "delve"/"leverage", corporate
jargon, hedging, sentence-initial "Let's", exclamation and superlative
density, staging adverbs ("quietly"), container words ("space",
"opportunity"), and unnamed-consensus appeals ("most people"). The R3
finding (r3_floor_compliant.md) predicts these live in the transferable
texture layer — moveable on request, shared with celebrated human prose —
and should discriminate poorly at document level in both directions.
This tool measures it and reports whichever way it falls.

Design:
- HUMAN side: the 78 wave-2 shelf works (the exact work set in
  author_space_v1_wave2.json, mapped to Control Shelf manifest rows by
  source hash; body offsets applied). Each work contributes up to 5
  seeded non-overlapping 3,500-word windows — windowed rather than
  whole-work so human documents are length-matched to AI samples
  (rare-event counts and per-document thresholds are length-sensitive
  even when rates are normalized). Whole-work rates and per-author
  medians are reported descriptively alongside.
- AI side: the 400 unprompted ai-longform samples (8 models x 50
  scenarios), truncated to the first 3,500 whitespace words for length
  symmetry.
- Each tell is operationalized as a conservative regex/heuristic count
  per 1,000 words (definitions inline below, in TELLS). Chat-register
  tells that cannot occur in fiction ("Great question", "I hope this
  helps", "As an AI") are counted only as an out-of-register note, never
  scored.
- Per tell: median/IQR both corpora; per-document AUC (Mann-Whitney,
  P(AI > human), ties 0.5) with a seeded author/model cluster bootstrap
  CI; sensitivity on AI at the threshold giving ~95% specificity on
  human windows; and the converse witch-hunt number — at a threshold
  catching 50% of AI samples, the share of celebrated-novelist windows
  flagged, with the most-flagged authors named. A combined z-sum score
  (per-tell z against human window mean/sd, summed) gets the same
  treatment. Per-model median rates are reported for every tell.

Overlap-guard note: composes with rerun_entry_analysis.py conventions
(same seed, same corpora) but measures surface-tell rates, not envelope
placement; no existing tool counts these features.

Outputs reports/validation/results2/folk_tells.{json,md}.

Relates: r3_floor_compliant.md (texture/chassis split this tests);
draft_v01.md Discussion ("the tells are the transferable layer").

Mirror note: defaults here point at the public-domain shelf (data/pd_manifest.yaml), the redistributable reproduction path. The paper's reported numbers were computed against the 15-author contemporary shelf, whose source texts cannot be redistributed; those aggregates are in reports/validation/results2/folk_tells.json.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger("analyze_folk_tells")

REPO_ROOT = Path(__file__).resolve().parents[1]

WINDOW_WORDS = 3500          # matches the AI corpus ~3,500-word target
MAX_WINDOWS_PER_WORK = 5     # seeded sample of non-overlapping windows
DEFAULT_SEED = 20260609      # repo-wide analysis seed

# ---------------------------------------------------------------------------
# Tell operationalizations. Each is a conservative regex/heuristic; rates are
# per 1,000 whitespace words. Conservatism notes inline — undercounting is
# acceptable, silent overcounting is not. All counters run on raw text
# (punctuation intact).
# ---------------------------------------------------------------------------

# -est words that are not superlatives (blocklist for the -est heuristic).
_EST_BLOCKLIST = {
    "honest", "modest", "earnest", "forest", "harvest", "arrest", "request",
    "suggest", "digest", "manifest", "protest", "interest", "tempest",
    "conquest", "contest", "invest", "infest", "divest", "detest", "behest",
    "bequest", "inquest", "everest", "northwest", "southwest", "midwest",
    "rest", "west", "test", "best",  # "best" handled separately below
    "guest", "chest", "quest", "vest", "jest", "nest", "pest", "zest",
    "crest", "wrest", "molest", "attest", "contests", "priest", "incest",
    "obsessed",  # safety: never matches but documents intent
    "dearest",  # term of address, not comparison -- still a superlative form;
                # kept OUT of the blocklist would be defensible; we block it
                # as vocative usage dominates in fiction
}
_EST_RE = re.compile(r"\b[A-Za-z]{3,}est\b")
_MOST_ADJ_RE = re.compile(
    r"\b(?:most|least)\s+[a-z]+"
    r"(?:ful|ous|ive|able|ible|ant|ent|al|ic|less|ish|some|ing|ed|y)\b",
    re.IGNORECASE,
)


def _count_superlatives(text: str) -> int:
    """-est superlatives (blocklist-filtered) + most/least + adjective-suffix
    heuristic + irregular 'best'/'worst'. Conservative: multiword adjectives
    and bare 'most + noun' are not counted ('most people' is its own tell)."""
    n = 0
    for m in _EST_RE.finditer(text):
        w = m.group(0).lower()
        if w in _EST_BLOCKLIST:
            continue
        n += 1
    n += len(re.findall(r"\b(?:best|worst)\b", text, re.IGNORECASE))
    n += len(_MOST_ADJ_RE.findall(text))
    return n


# "not X, but Y" / "not X — it's Y" contrastive reframing. Two patterns,
# both bounded at 40 chars with no sentence-internal stop punctuation, so
# cross-sentence and long-range matches are excluded. "not only ... but
# also" (classical rhetoric) is excluded explicitly.
_NOT_BUT_RE = re.compile(
    r"\bnot\b(?!\s+only\b)[^.?!;:—]{0,40}?,\s*but\b", re.IGNORECASE)
_NOT_ITS_RE = re.compile(
    r"\bnot\b[^.?!;:]{0,40}?[—,;]\s*it[’']s\b", re.IGNORECASE)


def _count_not_x_but_y(text: str) -> int:
    return len(_NOT_BUT_RE.findall(text)) + len(_NOT_ITS_RE.findall(text))


# Serial triad "X, Y, and Z" with 1-2 word items (tricolon proxy).
# Conservative: triads with longer items or no serial comma are missed.
_TRICOLON_RE = re.compile(
    r"\b[\w’']+(?:\s+[\w’']+)?,\s+[\w’']+(?:\s+[\w’']+)?,"
    r"\s+(?:and|or)\s+[\w’']+", re.IGNORECASE)

# Sentence-initial "Let's"/"Let us" (start of text, after terminal
# punctuation + optional closing quote, or on a new line).
_LETS_RE = re.compile(
    r"(?:^|[.?!][\"”’']?\s+|\n\s*)Let(?:[’']s|\s+us)\b")

_DELVE_LEVERAGE_RE = re.compile(
    r"\b(?:delv(?:e|es|ed|ing)|leverag(?:e|es|ed|ing))\b", re.IGNORECASE)

# Fixed corporate-jargon lexicon (word-bounded; multiword phrases included).
# 'leverage' is excluded here (it is its own tell); literal-use-risk words
# ('unlock', 'journey', 'robust') are excluded as too common in fiction.
_JARGON_RE = re.compile(
    r"\b(?:synerg(?:y|ies|istic)|stakeholders?|scalab(?:le|ility)"
    r"|actionable|streamlin(?:e|es|ed|ing)|seamless(?:ly)?"
    r"|holistic(?:ally)?|paradigms?|ecosystems?"
    r"|empower(?:s|ed|ing|ment)?|optimi[sz](?:e|es|ed|ing|ation)"
    r"|utili[sz](?:e|es|ed|ing)|bandwidth|deliverables?"
    r"|best\s+practices|value[-\s]add(?:ed)?|touch\s+base|circle\s+back"
    r"|deep\s+dive|game[-\s]chang(?:er|ing)|cutting[-\s]edge"
    r"|state[-\s]of[-\s]the[-\s]art|low[-\s]hanging\s+fruit"
    r"|move\s+the\s+needle|win[-\s]win|core\s+competenc(?:y|ies)"
    r"|pain\s+points?)\b", re.IGNORECASE)

# Fixed hedge lexicon. Bare modals (may/might/could) are excluded as
# uncountably polysemous; this is the essayistic-hedging subset of the
# folk lists that can be counted without parsing.
_HEDGE_RE = re.compile(
    r"\b(?:perhaps|possibly|arguably|presumably|seemingly|apparently"
    r"|somewhat|may\s+well|might\s+well|tends?\s+to"
    r"|in\s+many\s+ways|to\s+some\s+extent|more\s+often\s+than\s+not"
    r"|it\s+seems\s+that|it\s+would\s+seem)\b", re.IGNORECASE)

# Staging adverbs ("quietly devastating" register). Counted bare — the
# folk claim is about density of these adverbs, not their syntax.
_STAGING_RE = re.compile(
    r"\b(?:quietly|softly|gently|subtly|deliberately|effortlessly"
    r"|undeniably|unmistakably|profoundly)\b", re.IGNORECASE)

# Container words: abstract "space"/"opportunity" frames only — literal
# rooms and gaps are excluded by requiring the framing construction.
_CONTAINER_RE = re.compile(
    r"\b(?:h[oe]ld(?:ing)?\s+space|safe\s+spaces?"
    r"|a\s+space\s+(?:for|where|to|of|in\s+which)|the\s+space\s+to"
    r"|in\s+(?:this|that)\s+space"
    r"|(?:an?|the)\s+opportunit(?:y|ies)\s+(?:to|for)"
    r"|opportunities\s+to)\b", re.IGNORECASE)

# Unnamed-consensus appeals.
_CONSENSUS_RE = re.compile(
    r"\b(?:most\s+people|many\s+people|some\s+(?:would\s+say|say|argue)"
    r"|many\s+(?:believe|argue|say)|everyone\s+knows|people\s+often"
    r"|experts\s+(?:say|agree)|studies\s+show|we\s+all\s+know"
    r"|it\s+is\s+widely|it[’']s\s+widely)\b", re.IGNORECASE)

# Em dash: the "—" character plus standalone double-hyphen (both corpora
# use "—" natively; "--" appears residually in some shelf scans).
_DOUBLE_HYPHEN_RE = re.compile(r"(?<!-)--(?!-)")


def _count_em_dash(text: str) -> int:
    return text.count("—") + len(_DOUBLE_HYPHEN_RE.findall(text))


# Chat-register tells: cannot plausibly occur inside fiction; counted as an
# out-of-register note only, never scored.
_CHAT_REGISTER_RE = re.compile(
    r"\b(?:Great\s+question|I\s+hope\s+this\s+helps|As\s+an\s+AI"
    r"|I[’']m\s+happy\s+to\s+help|Certainly!|I\s+cannot\s+assist)\b")

# (tell_id, gloss, counter). Folk direction for every tell is AI-high.
TELLS: List[Tuple[str, str, Callable[[str], int]]] = [
    ("em_dash", "em dashes (— plus standalone --)", _count_em_dash),
    ("not_x_but_y", "contrastive reframing: 'not X, but Y' / 'not X — it's Y'",
     _count_not_x_but_y),
    ("tricolon", "serial triad 'X, Y, and Z' (1-2 word items; rule-of-three proxy)",
     lambda t: len(_TRICOLON_RE.findall(t))),
    ("exclamation", "exclamation marks", lambda t: t.count("!")),
    ("lets_opener", "sentence-initial 'Let's' / 'Let us'",
     lambda t: len(_LETS_RE.findall(t))),
    ("superlative", "superlatives (-est blocklist-filtered; best/worst; most/least+adj)",
     _count_superlatives),
    ("delve_leverage", "'delve'/'leverage' lemmas",
     lambda t: len(_DELVE_LEVERAGE_RE.findall(t))),
    ("corporate_jargon", "fixed corporate-jargon lexicon (synergy, stakeholder, ...)",
     lambda t: len(_JARGON_RE.findall(t))),
    ("hedges", "fixed hedge lexicon (perhaps, arguably, seemingly, ...)",
     lambda t: len(_HEDGE_RE.findall(t))),
    ("staging_adverbs", "staging adverbs (quietly, softly, gently, profoundly, ...)",
     lambda t: len(_STAGING_RE.findall(t))),
    ("container_words", "abstract 'space'/'opportunity' frames",
     lambda t: len(_CONTAINER_RE.findall(t))),
    ("unnamed_consensus", "unnamed-consensus appeals ('most people', 'studies show', ...)",
     lambda t: len(_CONSENSUS_RE.findall(t))),
]


# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------

def _author_display(slug: str) -> str:
    surname = slug.split("-")[0].replace("_", " ")
    return " ".join(p.capitalize() for p in surname.split())


def load_human_works(space_path: Path, manifest_path: Path) -> List[dict]:
    """The exact 78 wave-2 shelf works: hashes from the space artifact,
    text paths + body offsets from the Control Shelf manifest."""
    import yaml

    space = json.loads(space_path.read_text(encoding="utf-8"))
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    by_hash = {row["source_hash"]: row for row in manifest["works"]}
    corpus_root = REPO_ROOT / manifest.get("corpus_root", "data/pd_shelf/")

    works = []
    for slug in sorted(space["authors"]):
        for w in space["authors"][slug]["works"]:
            m = re.search(r"-([0-9a-f]{8})_baseline\.json$", w["path"])
            if not m:
                raise ValueError(f"no source hash in {w['path']}")
            row = by_hash.get(m.group(1))
            if row is None:
                raise ValueError(f"hash {m.group(1)} ({w['title']}) not in manifest")
            raw = (corpus_root / row["file_path"]).read_text(
                encoding="utf-8", errors="replace")
            start = row.get("body_start_offset") or 0
            end = row.get("body_end_offset")
            works.append({
                "author": slug,
                "title": row["title"],
                "source_hash": row["source_hash"],
                "text": raw[start:end] if end is not None else raw[start:],
            })
    return works


def iter_windows(text: str, rng: np.random.Generator,
                 window_words: int = WINDOW_WORDS,
                 max_windows: int = MAX_WINDOWS_PER_WORK):
    """Seeded sample of non-overlapping word windows, raw text preserved
    (tells need punctuation, so windows are character slices spanning
    exactly `window_words` whitespace tokens)."""
    spans = [m.span() for m in re.finditer(r"\S+", text)]
    n_slots = len(spans) // window_words
    if n_slots == 0:
        return
    chosen = range(n_slots) if n_slots <= max_windows else sorted(
        rng.choice(n_slots, size=max_windows, replace=False))
    for slot in chosen:
        lo = spans[slot * window_words][0]
        hi = spans[(slot + 1) * window_words - 1][1]
        yield int(slot), text[lo:hi]


def load_ai_samples(corpus_dir: Path, window_words: int = WINDOW_WORDS) -> List[dict]:
    """Unprompted ai-longform samples, truncated to the first
    `window_words` whitespace words for length symmetry."""
    samples = []
    for line in (corpus_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("condition") != "unprompted":
            continue
        text = (corpus_dir / rec["file_path"]).read_text(
            encoding="utf-8", errors="replace")
        spans = [m.span() for m in re.finditer(r"\S+", text)]
        if not spans:
            logger.warning("zero-length sample %s skipped", rec["sample_id"])
            continue
        if len(spans) > window_words:
            text = text[:spans[window_words - 1][1]]
            n_words = window_words
        else:
            n_words = len(spans)
        samples.append({
            "sample_id": rec["sample_id"],
            "model": rec["model_slug"],
            "scenario": rec["scenario_id"],
            "n_words": n_words,
            "text": text,
        })
    return samples


def rates_for(text: str, n_words: int) -> Dict[str, float]:
    per_k = 1000.0 / max(n_words, 1)
    return {tid: counter(text) * per_k for tid, _, counter in TELLS}


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def mann_whitney_auc(ai: np.ndarray, human: np.ndarray) -> float:
    """P(AI > human) + 0.5 P(tie), via rank sums."""
    combined = np.concatenate([ai, human])
    order = combined.argsort(kind="mergesort")
    ranks = np.empty(len(combined))
    ranks[order] = np.arange(1, len(combined) + 1)
    # midranks for ties
    for v in np.unique(combined):
        mask = combined == v
        if mask.sum() > 1:
            ranks[mask] = ranks[mask].mean()
    r_ai = ranks[: len(ai)].sum()
    u = r_ai - len(ai) * (len(ai) + 1) / 2
    return float(u / (len(ai) * len(human)))


def cluster_bootstrap_auc_ci(
    ai: np.ndarray, ai_cluster: Sequence[str],
    human: np.ndarray, human_cluster: Sequence[str],
    rng: np.random.Generator, n_boot: int = 2000,
) -> Tuple[float, float]:
    """Resample AI clusters (models) and human clusters (authors) with
    replacement; AUC distribution percentiles 2.5/97.5."""
    ai_groups = defaultdict(list)
    for v, c in zip(ai, ai_cluster):
        ai_groups[c].append(v)
    hu_groups = defaultdict(list)
    for v, c in zip(human, human_cluster):
        hu_groups[c].append(v)
    ai_keys = sorted(ai_groups)
    hu_keys = sorted(hu_groups)
    ai_arrays = {k: np.asarray(ai_groups[k]) for k in ai_keys}
    hu_arrays = {k: np.asarray(hu_groups[k]) for k in hu_keys}
    aucs = []
    for _ in range(n_boot):
        a = np.concatenate([ai_arrays[ai_keys[i]]
                            for i in rng.integers(0, len(ai_keys), len(ai_keys))])
        h = np.concatenate([hu_arrays[hu_keys[i]]
                            for i in rng.integers(0, len(hu_keys), len(hu_keys))])
        aucs.append(mann_whitney_auc(a, h))
    return float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))


def tell_stats(tid: str, ai: np.ndarray, ai_models: List[str],
               human: np.ndarray, human_authors: List[str],
               rng: np.random.Generator, n_boot: int) -> dict:
    auc = mann_whitney_auc(ai, human)
    lo, hi = cluster_bootstrap_auc_ci(ai, ai_models, human, human_authors,
                                      rng, n_boot)
    # 95% specificity on human windows: flag if rate > human p95 (strict >,
    # conservative for the detector). Report achieved specificity exactly.
    thr95 = float(np.percentile(human, 95))
    spec_achieved = float(np.mean(human <= thr95))
    sens_at_95spec = float(np.mean(ai > thr95))
    # Witch-hunt: threshold catching >=50% of AI (flag if rate >= AI median).
    # Degenerate when the AI median is 0 (tell absent from >=half the AI
    # samples): the only threshold catching 50% of AI flags every document,
    # human or machine. Flagged explicitly so the 100% is not misread.
    thr50 = float(np.median(ai))
    # Degeneracy only applies to non-negative per-1,000-word rates; the
    # combined z-sum is signed and a negative median is a real threshold.
    degenerate = thr50 <= 0.0 and bool(np.all(ai >= 0)) and bool(np.all(human >= 0))
    ai_caught = float(np.mean(ai >= thr50))
    human_flagged_mask = human >= thr50
    human_flagged = float(np.mean(human_flagged_mask))
    by_author = defaultdict(lambda: [0, 0])
    for flagged, author in zip(human_flagged_mask, human_authors):
        by_author[author][1] += 1
        if flagged:
            by_author[author][0] += 1
    flagged_authors = sorted(
        ((a, f, n, f / n) for a, (f, n) in by_author.items()),
        key=lambda t: (-t[3], t[0]))
    return {
        "human_median": float(np.median(human)),
        "human_iqr": [float(np.percentile(human, 25)), float(np.percentile(human, 75))],
        "ai_median": float(np.median(ai)),
        "ai_iqr": [float(np.percentile(ai, 25)), float(np.percentile(ai, 75))],
        "auc_ai_high": auc,
        "auc_ci95_cluster_bootstrap": [lo, hi],
        "threshold_at_95pct_specificity": thr95,
        "specificity_achieved": spec_achieved,
        "sensitivity_on_ai_at_95spec": sens_at_95spec,
        "witch_hunt": {
            "threshold_flagging_50pct_ai": thr50,
            "degenerate_threshold": degenerate,
            "ai_share_caught": ai_caught,
            "human_windows_flagged_pct": human_flagged,
            "most_flagged_authors": [] if degenerate else [
                {"author": _author_display(a), "slug": a,
                 "flagged": f, "windows": n, "share": round(s, 4)}
                for a, f, n, s in flagged_authors[:5] if f > 0
            ],
            "note": ("tell absent from >=50% of AI samples; no threshold "
                     "can catch half the AI without flagging every "
                     "document" if degenerate else None),
        },
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def fmt(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}"


def build_markdown(results: dict) -> str:
    meta = results["meta"]
    lines = [
        "# Folk \"AI Tells\" vs the Corpora — Document-Level Discrimination",
        "",
        f"- Generated: {meta['generated']}",
        f"- HUMAN: {meta['n_human_windows']} windows of {meta['window_words']} words "
        f"({meta['max_windows_per_work']} seeded non-overlapping windows/work) from the "
        f"{meta['n_human_works']} wave-2 shelf works, {meta['n_human_authors']} authors; "
        "body offsets per Control Shelf manifest",
        f"- AI: {meta['n_ai_samples']} unprompted ai-longform samples "
        f"({meta['n_ai_models']} models), truncated to {meta['window_words']} words "
        "(length symmetry; rates are per 1,000 words)",
        f"- Seed {meta['seed']}; AUC = P(AI > human window), ties 0.5; CI = seeded "
        f"author/model cluster bootstrap ({meta['n_bootstrap']} resamples)",
        "- Direction: every tell is scored in the folk direction (AI-high). "
        "AUC < 0.5 means the tell runs HUMAN-high — flagging on it selects "
        "celebrated novelists over machines.",
        "",
        "## Main table",
        "",
        "| Tell | Human median (IQR) | AI median (IQR) | AUC [95% CI] | "
        "Sens @95% spec | Human flagged @50% AI | Most-flagged authors |",
        "|---|---|---|---|---|---|---|",
    ]
    for tid, gloss, _ in TELLS:
        s = results["tells"][tid]
        wh = s["witch_hunt"]
        if wh["degenerate_threshold"]:
            flagged_cell = "degenerate†"
            top = "—"
        else:
            flagged_cell = f"{wh['human_windows_flagged_pct'] * 100:.1f}%"
            top = ", ".join(
                f"{a['author']} {a['flagged']}/{a['windows']}"
                for a in wh["most_flagged_authors"][:3]) or "—"
        lines.append(
            f"| {tid} | {fmt(s['human_median'])} "
            f"({fmt(s['human_iqr'][0])}–{fmt(s['human_iqr'][1])}) | "
            f"{fmt(s['ai_median'])} ({fmt(s['ai_iqr'][0])}–{fmt(s['ai_iqr'][1])}) | "
            f"{fmt(s['auc_ai_high'], 3)} [{fmt(s['auc_ci95_cluster_bootstrap'][0], 3)}, "
            f"{fmt(s['auc_ci95_cluster_bootstrap'][1], 3)}] | "
            f"{s['sensitivity_on_ai_at_95spec'] * 100:.1f}% | "
            f"{flagged_cell} | {top} |")
    comb = results["combined_z_sum"]
    wh = comb["witch_hunt"]
    top = ", ".join(
        f"{a['author']} {a['flagged']}/{a['windows']}"
        for a in wh["most_flagged_authors"][:3]) or "—"
    lines.append(
        f"| **combined z-sum** | {fmt(comb['human_median'])} "
        f"({fmt(comb['human_iqr'][0])}–{fmt(comb['human_iqr'][1])}) | "
        f"{fmt(comb['ai_median'])} ({fmt(comb['ai_iqr'][0])}–{fmt(comb['ai_iqr'][1])}) | "
        f"{fmt(comb['auc_ai_high'], 3)} [{fmt(comb['auc_ci95_cluster_bootstrap'][0], 3)}, "
        f"{fmt(comb['auc_ci95_cluster_bootstrap'][1], 3)}] | "
        f"{comb['sensitivity_on_ai_at_95spec'] * 100:.1f}% | "
        f"{wh['human_windows_flagged_pct'] * 100:.1f}% | {top} |")

    lines += [
        "",
        "† degenerate: the tell is absent from at least half the AI samples "
        "(AI median 0), so the only threshold catching 50% of AI flags every "
        "document, human or machine. No witch-hunt number is quotable; the "
        "tell simply does not occur often enough in unprompted AI fiction "
        "to detect anything.",
    ]

    lines += ["", "Tell glosses:", ""]
    for tid, gloss, _ in TELLS:
        lines.append(f"- `{tid}` — {gloss}")
    lines += [
        "- `combined z-sum` — sum over all 12 tells of (rate − human window "
        "mean) / human window sd",
        "",
        "## Per-model median rates (per 1,000 words)",
        "",
    ]
    models = sorted(results["per_model_medians"])
    lines.append("| Tell | human windows | " + " | ".join(models) + " |")
    lines.append("|---|---|" + "---|" * len(models))
    for tid, _, _ in TELLS:
        row = [f"| {tid}", fmt(results["tells"][tid]["human_median"])]
        row += [fmt(results["per_model_medians"][m][tid]) for m in models]
        lines.append(" | ".join(row) + " |")
    lines += [
        "",
        "## Per-author whole-work medians (per 1,000 words, descriptive)",
        "",
    ]
    tids = [t[0] for t in TELLS]
    lines.append("| Author | works | " + " | ".join(tids) + " |")
    lines.append("|---|---|" + "---|" * len(tids))
    for slug in sorted(results["per_author_work_medians"]):
        rec = results["per_author_work_medians"][slug]
        row = [f"| {_author_display(slug)}", str(rec["n_works"])]
        row += [fmt(rec["medians"][t]) for t in tids]
        lines.append(" | ".join(row) + " |")

    oor = results["out_of_register_note"]
    lines += [
        "",
        "## Out-of-register chat tells (noted, not scored)",
        "",
        f"Chat-register phrases ('Great question', 'I hope this helps', 'As an "
        f"AI', ...) cannot occur inside fiction and are noted rather than "
        f"scored: {oor['human_total_occurrences']} occurrences in "
        f"{meta['n_human_windows']} human windows; {oor['ai_total_occurrences']} "
        f"in {meta['n_ai_samples']} AI samples.",
        "",
        "## Reading",
        "",
        results["reading"],
        "",
        "## Method notes",
        "",
        "- Conservative operationalizations (documented in "
        "`analyze_folk_tells.py`): bounded-span regexes for 'not X, but Y'; "
        "1-2-word-item serial triads only; -est blocklist for superlatives; "
        "bare modals excluded from the hedge lexicon; literal 'space'/"
        "'opportunity' uses excluded by requiring the framing construction.",
        "- Human windows cluster within author (15 clusters) and AI samples "
        "within model (8 clusters); the AUC CI resamples at cluster level.",
        "- Length difference handled by windowing: human works are sampled "
        "as 3,500-word windows matched to the AI samples' ~3,500-word "
        "target; AI samples are truncated to 3,500 words. Whole-work "
        "per-author medians are reported descriptively only.",
        "- 'Sens @95% spec' = share of AI samples above the human-window "
        "95th percentile. 'Human flagged @50% AI' = share of human windows "
        "at or above the AI median (the threshold a tell-based detector "
        "needs to catch half the machine text).",
    ]
    return "\n".join(lines) + "\n"


def build_reading(results: dict) -> str:
    tells = results["tells"]
    aucs = {tid: tells[tid]["auc_ai_high"] for tid, _, _ in TELLS}
    best_tid = max(aucs, key=aucs.get)
    worst_tid = min(aucs, key=aucs.get)
    comb = results["combined_z_sum"]
    n_above_06 = sum(1 for v in aucs.values() if v >= 0.6)
    n_chance = sum(1 for v in aucs.values() if 0.45 < v < 0.6)
    wrong = sorted((v, t) for t, v in aucs.items() if v <= 0.45)
    wrong_named = ", ".join(f"`{t}` {fmt(v, 3)}" for v, t in wrong)
    n_degenerate = sum(
        1 for tid, _, _ in TELLS
        if tells[tid]["witch_hunt"]["degenerate_threshold"])
    wh = comb["witch_hunt"]
    top_named = ", ".join(
        f"{a['author']} ({a['flagged']}/{a['windows']} windows)"
        for a in wh["most_flagged_authors"][:3])
    parts = [
        f"Of the 12 folk tells, {n_above_06} reach AUC >= 0.60 at document "
        f"level, {n_chance} sit near chance (0.45-0.60), and {len(wrong)} "
        f"run materially in the WRONG direction — celebrated human prose is "
        f"higher on the tell than machine prose ({wrong_named}). "
        f"{n_degenerate} of the 12 are absent from at least half the "
        f"unprompted AI samples — too rare in machine fiction to flag "
        f"anything. The best single tell is `{best_tid}` "
        f"(AUC {fmt(aucs[best_tid], 3)}, catching "
        f"{tells[best_tid]['sensitivity_on_ai_at_95spec'] * 100:.0f}% of AI at "
        f"95% specificity); the worst is `{worst_tid}` "
        f"(AUC {fmt(aucs[worst_tid], 3)}). The combined z-sum over all 12 "
        f"reaches AUC {fmt(comb['auc_ai_high'], 3)} "
        f"[{fmt(comb['auc_ci95_cluster_bootstrap'][0], 3)}, "
        f"{fmt(comb['auc_ci95_cluster_bootstrap'][1], 3)}], catching "
        f"{comb['sensitivity_on_ai_at_95spec'] * 100:.0f}% of AI at 95% "
        f"specificity. The converse is the witch-hunt number: a combined-tell "
        f"threshold tuned to catch half the machine samples flags "
        f"{wh['human_windows_flagged_pct'] * 100:.1f}% of 3,500-word windows "
        f"by celebrated novelists — most often {top_named}.",
    ]
    em = tells["em_dash"]
    pm = results["per_model_medians"]
    claude_med = np.median([pm[m]["em_dash"] for m in pm if m.startswith("claude")])
    other_med = np.median([pm[m]["em_dash"] for m in pm if not m.startswith("claude")])
    em_top = em["witch_hunt"]["most_flagged_authors"]
    em_names = ", ".join(
        f"{a['author']} ({a['flagged']}/{a['windows']})" for a in em_top[:3])
    em_ci = em["auc_ci95_cluster_bootstrap"]
    parts.append(
        f"The em dash, the most-litigated tell, runs human median "
        f"{fmt(em['human_median'])}/1,000 words vs AI median "
        f"{fmt(em['ai_median'])} (AUC {fmt(em['auc_ai_high'], 3)}; cluster-"
        f"bootstrap CI [{fmt(em_ci[0], 3)}, {fmt(em_ci[1], 3)}]"
        + (" — crosses 0.5 once model/author clustering is respected"
           if em_ci[0] < 0.5 else "")
        + f"). Claude-family median {fmt(float(claude_med))} vs "
        f"{fmt(float(other_med))} for the other models (per-model medians in "
        f"the table above). An em-dash threshold catching half the AI flags "
        f"{em['witch_hunt']['human_windows_flagged_pct'] * 100:.1f}% of human "
        f"windows — led by {em_names}.")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Folk 'AI tells' vs corpora: document-level discrimination")
    parser.add_argument("--space-artifact", type=Path, default=REPO_ROOT /
                        "data/artifacts/author_space_pd_v1.json")
    parser.add_argument("--shelf-manifest", type=Path, default=REPO_ROOT /
                        "data/pd_manifest.yaml")
    parser.add_argument("--ai-corpus-dir", type=Path,
                        default=REPO_ROOT / "data/ai-longform")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT /
                        "reports/validation/results2")
    parser.add_argument("--window-words", type=int, default=WINDOW_WORDS)
    parser.add_argument("--max-windows-per-work", type=int,
                        default=MAX_WINDOWS_PER_WORK)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    rng = np.random.default_rng(args.seed)

    # --- HUMAN side -------------------------------------------------------
    works = load_human_works(args.space_artifact, args.shelf_manifest)
    logger.info("loaded %d shelf works", len(works))
    human_rows: List[dict] = []
    work_rates: List[dict] = []
    chat_hits_human = 0
    for work in works:  # sorted by author slug already; deterministic
        spans = [m.span() for m in re.finditer(r"\S+", work["text"])]
        n_words = len(spans)
        wr = rates_for(work["text"], n_words)
        work_rates.append({"author": work["author"], "title": work["title"],
                           "n_words": n_words, "rates": wr})
        for slot, win_text in iter_windows(
                work["text"], rng, args.window_words, args.max_windows_per_work):
            chat_hits_human += len(_CHAT_REGISTER_RE.findall(win_text))
            human_rows.append({
                "author": work["author"], "title": work["title"],
                "window": slot,
                "rates": rates_for(win_text, args.window_words),
            })
    logger.info("human windows: %d", len(human_rows))

    # --- AI side ----------------------------------------------------------
    samples = load_ai_samples(args.ai_corpus_dir, args.window_words)
    logger.info("AI unprompted samples: %d", len(samples))
    ai_rows: List[dict] = []
    chat_hits_ai = 0
    for s in samples:
        chat_hits_ai += len(_CHAT_REGISTER_RE.findall(s["text"]))
        ai_rows.append({"sample_id": s["sample_id"], "model": s["model"],
                        "scenario": s["scenario"], "n_words": s["n_words"],
                        "rates": rates_for(s["text"], s["n_words"])})

    tids = [t[0] for t in TELLS]
    human_mat = {tid: np.array([r["rates"][tid] for r in human_rows]) for tid in tids}
    ai_mat = {tid: np.array([r["rates"][tid] for r in ai_rows]) for tid in tids}
    human_authors = [r["author"] for r in human_rows]
    ai_models = [r["model"] for r in ai_rows]

    # --- per-tell stats ---------------------------------------------------
    tell_results = {}
    for tid, gloss, _ in TELLS:
        tell_results[tid] = {"gloss": gloss, **tell_stats(
            tid, ai_mat[tid], ai_models, human_mat[tid], human_authors,
            rng, args.n_bootstrap)}
        logger.info("%-18s AUC %.3f  sens@95spec %.1f%%  human-flagged@50AI %.1f%%",
                    tid, tell_results[tid]["auc_ai_high"],
                    tell_results[tid]["sensitivity_on_ai_at_95spec"] * 100,
                    tell_results[tid]["witch_hunt"]["human_windows_flagged_pct"] * 100)

    # --- combined z-sum (z against human window mean/sd, folk direction) --
    mu = {tid: float(human_mat[tid].mean()) for tid in tids}
    sd = {tid: float(human_mat[tid].std(ddof=1)) or 1.0 for tid in tids}
    human_z = np.sum([(human_mat[t] - mu[t]) / sd[t] for t in tids], axis=0)
    ai_z = np.sum([(ai_mat[t] - mu[t]) / sd[t] for t in tids], axis=0)
    combined = tell_stats("combined", ai_z, ai_models, human_z, human_authors,
                          rng, args.n_bootstrap)
    logger.info("combined z-sum AUC %.3f", combined["auc_ai_high"])

    # --- per-model medians -------------------------------------------------
    per_model = {}
    for model in sorted(set(ai_models)):
        rows = [r for r in ai_rows if r["model"] == model]
        per_model[model] = {tid: float(np.median([r["rates"][tid] for r in rows]))
                            for tid in tids}

    # --- per-author whole-work medians --------------------------------------
    per_author = {}
    for slug in sorted({w["author"] for w in work_rates}):
        rows = [w for w in work_rates if w["author"] == slug]
        per_author[slug] = {
            "n_works": len(rows),
            "medians": {tid: float(np.median([r["rates"][tid] for r in rows]))
                        for tid in tids},
        }

    results = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "tool": "tools/analyze_folk_tells.py",
            "space_artifact": str(args.space_artifact),
            "shelf_manifest": str(args.shelf_manifest),
            "ai_corpus_dir": str(args.ai_corpus_dir),
            "window_words": args.window_words,
            "max_windows_per_work": args.max_windows_per_work,
            "n_human_works": len(works),
            "n_human_authors": len(per_author),
            "n_human_windows": len(human_rows),
            "n_ai_samples": len(ai_rows),
            "n_ai_models": len(per_model),
            "seed": args.seed,
            "n_bootstrap": args.n_bootstrap,
            "direction": "AUC = P(AI > human window); folk claim is AI-high "
                         "for every tell",
        },
        "tells": tell_results,
        "combined_z_sum": combined,
        "per_model_medians": per_model,
        "per_author_work_medians": per_author,
        "out_of_register_note": {
            "phrases": _CHAT_REGISTER_RE.pattern,
            "human_total_occurrences": chat_hits_human,
            "ai_total_occurrences": chat_hits_ai,
            "note": "chat-register tells cannot occur inside fiction; "
                    "noted, not scored",
        },
        "human_window_rows": [
            {k: r[k] for k in ("author", "title", "window")} | r["rates"]
            for r in human_rows],
        "ai_sample_rows": [
            {k: r[k] for k in ("sample_id", "model", "scenario", "n_words")}
            | r["rates"] for r in ai_rows],
    }
    results["reading"] = build_reading(results)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "folk_tells.json"
    md_path = args.output_dir / "folk_tells.md"
    json_path.write_text(json.dumps(results, indent=1), encoding="utf-8")
    md_path.write_text(build_markdown(results), encoding="utf-8")
    logger.info("wrote %s and %s", json_path, md_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
