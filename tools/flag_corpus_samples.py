#!/usr/bin/env python3
"""Flag refusal and sub-floor samples in the AI long-form corpus.

Why this exists (forensic review 2026-08-06, finding D-3): DATA_LICENSES.md
described the corpus as "1,072 manifest records of machine-generated literary
fiction". Some of those records are not fiction — they are refusal messages
("Sorry, I can't continue that novel...") — and others are outputs too short
to carry any measurement. The paper's own analyses already exclude them via
the §3.7 token floors, and the completion-condition report already publishes
per-model refusal counts, but nothing in the released corpus itself marked
which files those are. A reader loading data/ai-longform/ got refusals mixed
in with fiction and no way to tell them apart.

This tool writes a SIDECAR, ``data/ai-longform/sample_flags.json``. It does
not modify ``manifest.jsonl``: the manifest is the frozen generation record
and every published number was computed against it as it stands.

The rule, stated in full
------------------------

Two orthogonal flags per sample.

1. ``refusal_class`` — whether the output opens by declining the task, and
   whether it nonetheless delivers prose. Decided by matching
   REFUSAL_PATTERNS against the first REFUSAL_WINDOW characters of the body.
   The patterns are deliberately narrow: first-person assistant speech
   declining the task ("I can't continue", "I'm unable to", "Sorry, I
   can't"), which cannot open a literary continuation. Three values:

       none                          no declination at the head
       refusal_only                  declines, and delivers no usable prose
                                     (empty or below the hard floor)
       declined_styling_then_original
                                     declines to imitate the named author,
                                     then writes substantial original prose
                                     (at or above the hard floor)

   The third class is real and matters: several gpt-5 / gpt-5-mini samples
   open "Sorry, I can't write in the exact style of X. I can, however, offer
   an original piece..." and then run to thousands of words of genuine
   fiction. Calling those plain refusals would be wrong (the prose is there
   and was measured); calling them nothing would hide that the model
   explicitly declined the styling instruction those samples are supposed to
   carry. Both facts are recorded instead.

2. ``length_class`` — computed from the sample's MFW token count against the
   paper's own floors (§3.7), so these flags reconcile with the published
   analyses rather than introducing a second standard:

       empty             0 tokens
       below_hard_floor  < 1,500 tokens  (excluded from every claim)
       sub_floor         1,500-2,999     (reported separately; no headline claim)
       compliant         >= 3,000        (the primary stratum)

``usable_as_fiction`` is the conjunction a reader most often wants: not a
refusal, and not empty.

Tokenization note (for maintainers): this tool strips leading ``#`` lines
before tokenizing, matching the featurization path, whereas
``rerun_entry_analysis.load_corpus`` tokenizes the raw file. The difference
is at most 5 tokens (a markdown title line) and **zero** samples fall on
different sides of the 0 / 1,500 / 3,000-token boundaries under the two
conventions, so the strata are identical either way. Verified 2026-08-06;
noted so the discrepancy does not have to be rediscovered.

Usage:
    python3 tools/flag_corpus_samples.py                      # write sidecar
    python3 tools/flag_corpus_samples.py --check              # verify only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _ensure_repo_paths() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    for path in (repo_root / "src", repo_root):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
    return repo_root


REPO_ROOT = _ensure_repo_paths()

CORPUS_DIR = REPO_ROOT / "data/ai-longform"
MANIFEST = CORPUS_DIR / "manifest.jsonl"
SIDECAR = CORPUS_DIR / "sample_flags.json"

HARD_FLOOR_TOKENS = 1500      # paper §3.7 hard floor
PRACTICE_FLOOR_TOKENS = 3000  # paper §3.7 practice floor (primary stratum)

REFUSAL_WINDOW = 600          # characters inspected at the head of the file

# Assistant-register refusal / redirection. Narrow on purpose: these are
# first-person declinations that cannot open a literary continuation.
REFUSAL_PATTERNS: List[str] = [
    r"\bsorry[,—\-\s]*(?:but\s+)?i\s+can(?:'|’)?t\b",
    r"\bi\s+can(?:'|’)?t\s+(?:continue|help\s+with|reproduce|provide|write\s+that)\b",
    # "I can't write in X's exact voice/style, but here's an original piece..."
    # -- a declination with no "Sorry" in front of it. The first two patterns
    # both require either "sorry" or a specific verb object, so these were
    # missed on the first pass (forensic review follow-up, 2026-08-06).
    r"\bi\s+can(?:'|’)?t\s+write\s+in\b",
    r"\bi\s+(?:am|'m|’m)\s+(?:unable|not\s+able)\s+to\b",
    r"\bi\s+won(?:'|’)?t\s+(?:continue|reproduce)\b",
    r"\bi\s+cannot\s+(?:continue|help\s+with|reproduce|provide)\b",
]
_REFUSAL_RE = re.compile("|".join(REFUSAL_PATTERNS), re.IGNORECASE)


def _runtime_versions():
    """Interpreter + numeric-library versions for this run's meta block."""
    from author_manifold.author_space import runtime_versions
    return runtime_versions()


def strip_header(raw: str) -> str:
    """Body text: drop leading '#'-prefixed lines (samples carry at most a
    markdown title line), matching the featurization path."""
    return "".join(
        ln for ln in raw.splitlines(keepends=True) if not ln.startswith("#")
    ).strip()


def classify_length(n_tokens: int) -> str:
    if n_tokens == 0:
        return "empty"
    if n_tokens < HARD_FLOOR_TOKENS:
        return "below_hard_floor"
    if n_tokens < PRACTICE_FLOOR_TOKENS:
        return "sub_floor"
    return "compliant"


def build_flags() -> Dict[str, Any]:
    from author_manifold.author_space import mfw_tokenize

    rows = [json.loads(line) for line in
            MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]

    samples: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        rel = row["file_path"]
        path = CORPUS_DIR / rel
        if not path.is_file():
            samples[rel] = {
                "condition": row.get("condition"),
                "model_slug": row.get("model_slug"),
                "file_missing": True,
            }
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        body = strip_header(raw)
        n_tokens = len(mfw_tokenize(body))
        declines = bool(_REFUSAL_RE.search(body[:REFUSAL_WINDOW]))
        length_class = classify_length(n_tokens)
        if not declines:
            refusal_class = "none"
        elif n_tokens < HARD_FLOOR_TOKENS:
            refusal_class = "refusal_only"
        else:
            refusal_class = "declined_styling_then_original"
        samples[rel] = {
            "condition": row.get("condition"),
            "model_slug": row.get("model_slug"),
            "mfw_tokens": n_tokens,
            "word_count_manifest": row.get("word_count"),
            "stop_reason": row.get("stop_reason"),
            "refusal_class": refusal_class,
            "length_class": length_class,
            "usable_as_fiction": (
                refusal_class != "refusal_only" and length_class != "empty"),
        }

    by_class = Counter(s.get("length_class") for s in samples.values())
    by_refusal = Counter(s.get("refusal_class") for s in samples.values())
    n_usable = sum(1 for s in samples.values() if s.get("usable_as_fiction"))

    per_model: Dict[str, Dict[str, int]] = {}
    for s in samples.values():
        row = per_model.setdefault(
            s.get("model_slug") or "unknown",
            {"n": 0, "refusal_only": 0, "declined_styling_then_original": 0,
             "empty": 0, "below_hard_floor": 0, "sub_floor": 0,
             "compliant": 0})
        row["n"] += 1
        rc = s.get("refusal_class")
        if rc in row:
            row[rc] += 1
        cls = s.get("length_class")
        if cls in row:
            row[cls] += 1

    return {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "versions": _runtime_versions(),
            "tool": "tools/flag_corpus_samples.py",
            "purpose": (
                "Sidecar flags for data/ai-longform/. Marks which manifest "
                "records are refusal messages rather than fiction, and which "
                "fall below the paper's measurement floors. Does NOT modify "
                "manifest.jsonl, which is the frozen generation record every "
                "published number was computed against."),
            "added": "2026-08-06 (forensic code and data review, finding D-3)",
            "rule_refusal_class": (
                "Regex match for assistant-register declination in the first "
                f"{REFUSAL_WINDOW} characters of the body; if matched, split "
                f"by whether the sample still reaches the {HARD_FLOOR_TOKENS}-"
                "token hard floor (declined_styling_then_original) or not "
                "(refusal_only). Patterns: " + " | ".join(REFUSAL_PATTERNS)),
            "rule_length_class": (
                f"MFW token count against the paper's §3.7 floors: empty = 0; "
                f"below_hard_floor < {HARD_FLOOR_TOKENS} (excluded from every "
                f"claim); sub_floor {HARD_FLOOR_TOKENS}-{PRACTICE_FLOOR_TOKENS - 1} "
                f"(reported separately); compliant >= {PRACTICE_FLOOR_TOKENS} "
                f"(primary stratum). Tokenizer: mfw_tokenize "
                f"(lowercase_regex_v1), the same one used for every "
                f"measurement in the paper."),
            "n_records": len(samples),
            "refusal_class_counts": dict(sorted(by_refusal.items())),
            "n_usable_as_fiction": n_usable,
            "length_class_counts": dict(sorted(by_class.items())),
            "per_model": dict(sorted(per_model.items())),
        },
        "samples": dict(sorted(samples.items())),
    }


# The published completion condition, pinned. A comparison whose two sides
# do not have this shape is not comparing the published table against the
# sidecar -- it is comparing something else, or nothing at all -- so it
# fails before any per-model count is inspected. Without this, a sidecar
# carrying no completion samples (a renamed condition, a partial run) put
# an empty set through an empty loop body and reported PASS.
EXPECTED_COMPLETION_MODELS = 8
EXPECTED_COMPLETION_SAMPLES = 160

# The published table keys use the raw model names (e.g. "qwen3.6:35b");
# sidecar model slugs spell the separator as ".".
MODEL_KEY_ALIASES = {"gemma4.26b": "gemma4:26b", "qwen3.6.35b": "qwen3.6:35b"}


def check_against_published(flags: Dict[str, Any]) -> int:
    """Cross-check the completion condition against the published per-model
    compliance table in results2/completion_results.json.

    Returns the number of failures. Both sides must carry the expected
    number of models and samples, and name the same models, before any
    count is compared: a missing or extra model is a failure in itself,
    not a row that is quietly skipped.
    """
    published_path = (REPO_ROOT / "reports/validation/author_space/results2"
                      / "completion_results.json")
    published = json.loads(published_path.read_text(encoding="utf-8"))
    table = published["compliance_per_model"]

    mine: Dict[str, Counter] = {}
    for rel, s in flags["samples"].items():
        if s.get("condition") != "completion":
            continue
        model = (s.get("model_slug") or "").replace("_", ".")
        mine.setdefault(MODEL_KEY_ALIASES.get(model, model),
                        Counter())[s["length_class"]] += 1

    failures = 0

    def fail(message: str) -> None:
        nonlocal failures
        failures += 1
        print(f"FAIL  {message}")

    published_total = sum(row["compliant"] + row["subfloor"] + row["refused"]
                          for row in table.values())
    sidecar_total = sum(sum(counts.values()) for counts in mine.values())

    for label, models, total in (
            ("published table", set(table), published_total),
            ("sidecar", set(mine), sidecar_total)):
        if not models:
            fail(f"{label}: no completion-condition models at all "
                 f"(expected {EXPECTED_COMPLETION_MODELS})")
        elif len(models) != EXPECTED_COMPLETION_MODELS:
            fail(f"{label}: {len(models)} models, expected "
                 f"{EXPECTED_COMPLETION_MODELS}: {sorted(models)}")
        if total != EXPECTED_COMPLETION_SAMPLES:
            fail(f"{label}: {total} completion samples, expected "
                 f"{EXPECTED_COMPLETION_SAMPLES}")

    missing = sorted(set(table) - set(mine))
    extra = sorted(set(mine) - set(table))
    if missing:
        fail(f"models in the published table with no sidecar rows: {missing}")
    if extra:
        fail("models in the sidecar the published table does not name: "
             f"{extra}")

    if failures:
        print("\nCross-check vs published completion compliance table: "
              f"{failures} STRUCTURAL FAILURE(S) -- the two sides do not "
              "describe the same set of samples, so per-model counts were "
              "not compared.")
        return failures

    print(f"{'model':20s} {'published (comp/sub/ref)':>26s} "
          f"{'sidecar (comp/sub/ref)':>24s}")
    for key in sorted(table):
        counts = mine[key]
        pub = table[key]
        # Published "refused/partial" = below the hard floor, including empty.
        ref = counts["below_hard_floor"] + counts["empty"]
        got = (counts["compliant"], counts["sub_floor"], ref)
        exp = (pub["compliant"], pub["subfloor"], pub["refused"])
        ok = got == exp
        failures += 0 if ok else 1
        print(f"{key:20s} {str(exp):>26s} {str(got):>24s}  "
              f"{'OK' if ok else 'MISMATCH'}")
    print("\nCross-check vs published completion compliance table: "
          f"{'PASS' if failures == 0 else f'{failures} MISMATCH(ES)'}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Flag refusal / sub-floor samples in the AI corpus")
    parser.add_argument("--output", type=Path, default=SIDECAR)
    parser.add_argument("--check", action="store_true",
                        help="Cross-check against the published completion "
                             "compliance table; do not write the sidecar")
    args = parser.parse_args()

    flags = build_flags()
    meta = flags["meta"]
    print(f"{meta['n_records']} records: "
          f"{meta['n_usable_as_fiction']} usable as fiction")
    print(f"refusal classes: {meta['refusal_class_counts']}")
    print(f"length classes: {meta['length_class_counts']}")
    print()
    failures = check_against_published(flags)

    if not args.check:
        args.output.write_text(json.dumps(flags, indent=1), encoding="utf-8")
        print(f"\nWrote {args.output}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
