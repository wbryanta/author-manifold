#!/usr/bin/env python3
"""Public-domain replication shelf builder — issue #95 item P8.

Builds ``data/pd_shelf/`` from Project Gutenberg plain-text
editions so paper reviewers can run the full ADR-0041 pipeline (E1-E4) on
rights-free texts. Every selected work is:

- public domain in the United States (published before 1930);
- an English ORIGINAL (no translations, so no translator-voice confound,
  per ADR-0036);
- by an author with >= 3 substantial works on the shelf.

Cleaning policy (deterministic, reviewer-reproducible):

1. Cut the Project Gutenberg header/license at the ``*** START OF ... ***``
   and ``*** END OF ... ***`` markers.
2. Anchor the body at the work's canonical opening sentence (per-work
   ``anchor`` below), rewound to the start of its containing paragraph.
   This uniformly strips title pages, tables of contents, lists of
   illustrations, transcriber notes, AND all prefatory matter — including
   editor/publisher introductions by other hands (e.g. the George
   Saintsbury introduction in the PG #1342 Pride and Prejudice) and the
   author's own prefaces. Body = the work proper, first sentence onward.
3. Trim trailing non-body paragraphs (transcriber notes, errata,
   "THE END" markers, Gutenberg residue) from the tail.
4. Remove inline ``[Illustration: ...]`` blocks, ``[Sidenote: ...]``,
   bracketed footnote markers ``[1]``, and Gutenberg italic markup
   (``_word_`` -> ``word``).

Output files carry the same ``# Key: Value`` metadata-header convention as
the contemporary ``text/`` shelf and the same ``-<hash8>.txt`` filename
suffix that the Control Shelf manifest tooling keys on.

Usage:
    python3 tools/build_pd_shelf.py            # build all
    python3 tools/build_pd_shelf.py --qc       # QC dump
    python3 tools/build_pd_shelf.py --skip-download
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


REPO_ROOT = _repo_root()
SHELF_DIR = REPO_ROOT / "data/pd_shelf"
RAW_CACHE = REPO_ROOT / "data/tmp/pd_shelf_gutenberg_raw"
GUTENBERG_TXT_URL = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"

USER_AGENT = "WritingAnalysis-pd-shelf-builder/1.0 (research replication corpus)"


@dataclass(frozen=True)
class PDWork:
    author_slug: str            # directory name, matches text/ shelf convention
    canonical_author: str       # "Last, First" (ASCII, for books.yaml matching)
    display_author: str         # for the # Author header
    title: str
    year: int                   # first publication year (PD rationale: < 1930)
    gutenberg_id: int
    anchor: str                 # canonical opening words of the work proper
    form: str = "novel"
    end_anchor: str | None = None  # canonical final words (cut after their
                                   # paragraph) for works with backmatter that
                                   # generic tail heuristics cannot classify


# ---------------------------------------------------------------------------
# The shelf: 9 authors, 35 works. All first published < 1930 (US public
# domain as of 2026), all English originals, >= 3 works per author.
# Translated authors in calibration/ (Dostoevsky, Tolstoy, Hugo, Cervantes,
# Kafka, Dumas) are excluded — translator-mixed voice (ADR-0036).
# Emily Bronte (Wuthering Heights) excluded: single work, and kept strictly
# separate from Charlotte (the historical misattribution fix).
# Faulkner excluded: only one pre-1930 work on Gutenberg (< 3 works).
# ---------------------------------------------------------------------------

WORKS: list[PDWork] = [
    # Jane Austen (5)
    PDWork("austen-jane", "Austen, Jane", "Jane Austen",
           "Sense and Sensibility", 1811, 161,
           "The family of Dashwood had long been settled in Sussex"),
    PDWork("austen-jane", "Austen, Jane", "Jane Austen",
           "Pride and Prejudice", 1813, 1342,
           "It is a truth universally acknowledged, that a single man",
           end_anchor="by bringing her into Derbyshire, had been the means of"
                      " uniting them"),
    PDWork("austen-jane", "Austen, Jane", "Jane Austen",
           "Mansfield Park", 1814, 141,
           "About thirty years ago Miss Maria Ward"),
    PDWork("austen-jane", "Austen, Jane", "Jane Austen",
           "Emma", 1815, 158,
           "Emma Woodhouse, handsome, clever, and rich"),
    PDWork("austen-jane", "Austen, Jane", "Jane Austen",
           "Persuasion", 1817, 105,
           "Sir Walter Elliot, of Kellynch Hall, in Somersetshire"),
    # Charlotte Bronte (4)
    PDWork("bronte-charlotte", "Bronte, Charlotte", "Charlotte Brontë",
           "Jane Eyre", 1847, 1260,
           "There was no possibility of taking a walk that day"),
    PDWork("bronte-charlotte", "Bronte, Charlotte", "Charlotte Brontë",
           "Shirley", 1849, 30486,
           "Of late years, an abundant shower of curates has fallen",
           end_anchor="God speed him in the quest"),
    PDWork("bronte-charlotte", "Bronte, Charlotte", "Charlotte Brontë",
           "Villette", 1853, 9182,
           "My godmother lived in a handsome house"),
    PDWork("bronte-charlotte", "Bronte, Charlotte", "Charlotte Brontë",
           "The Professor", 1857, 1028,
           "The other day, in looking over my papers"),
    # Charles Dickens (4)
    PDWork("dickens-charles", "Dickens, Charles", "Charles Dickens",
           "Oliver Twist", 1838, 730,
           "Among other public buildings in a certain town"),
    PDWork("dickens-charles", "Dickens, Charles", "Charles Dickens",
           "David Copperfield", 1850, 766,
           "Whether I shall turn out to be the hero of my own life"),
    PDWork("dickens-charles", "Dickens, Charles", "Charles Dickens",
           "Bleak House", 1853, 1023,
           "London. Michaelmas term lately over"),
    PDWork("dickens-charles", "Dickens, Charles", "Charles Dickens",
           "Great Expectations", 1861, 1400,
           "family name being Pirrip, and my Christian name Philip"),
    # F. Scott Fitzgerald (3) — all pre-1930 publications
    PDWork("fitzgerald-f_scott", "Fitzgerald, F. Scott", "F. Scott Fitzgerald",
           "This Side of Paradise", 1920, 805,
           "Amory Blaine inherited from his mother every trait",
           end_anchor="I know myself"),
    PDWork("fitzgerald-f_scott", "Fitzgerald, F. Scott", "F. Scott Fitzgerald",
           "The Beautiful and Damned", 1922, 9830,
           "In 1913, when Anthony Patch was twenty-five"),
    PDWork("fitzgerald-f_scott", "Fitzgerald, F. Scott", "F. Scott Fitzgerald",
           "The Great Gatsby", 1925, 64317,
           "In my younger and more vulnerable years my father gave me"),
    # E. M. Forster (5) — A Passage to India (1924) is pre-1930, US PD
    PDWork("forster-e_m", "Forster, E. M.", "E. M. Forster",
           "Where Angels Fear to Tread", 1905, 2948,
           "They were all at Charing Cross to see Lilia off"),
    PDWork("forster-e_m", "Forster, E. M.", "E. M. Forster",
           "The Longest Journey", 1907, 2604,
           "The cow is there"),
    PDWork("forster-e_m", "Forster, E. M.", "E. M. Forster",
           "A Room with a View", 1908, 2641,
           "The Signora had no business to do it"),
    PDWork("forster-e_m", "Forster, E. M.", "E. M. Forster",
           "Howards End", 1910, 2946,
           "One may as well begin with Helen"),
    PDWork("forster-e_m", "Forster, E. M.", "E. M. Forster",
           "A Passage to India", 1924, 61221,
           "Except for the Marabar Caves",
           end_anchor="No, not there"),
    # Nathaniel Hawthorne (3)
    PDWork("hawthorne-nathaniel", "Hawthorne, Nathaniel", "Nathaniel Hawthorne",
           "The Scarlet Letter", 1850, 25344,
           "A throng of bearded men, in sad-colored garments",
           end_anchor="THE LETTER A, GULES"),
    PDWork("hawthorne-nathaniel", "Hawthorne, Nathaniel", "Nathaniel Hawthorne",
           "The House of the Seven Gables", 1851, 77,
           "Halfway down a by-street of one of our New England towns"),
    PDWork("hawthorne-nathaniel", "Hawthorne, Nathaniel", "Nathaniel Hawthorne",
           "The Blithedale Romance", 1852, 2081,
           "The evening before my departure for Blithedale"),
    # James Joyce (3)
    PDWork("joyce-james", "Joyce, James", "James Joyce",
           "Dubliners", 1914, 2814,
           "There was no hope for him this time: it was the third stroke",
           form="story_collection"),
    PDWork("joyce-james", "Joyce, James", "James Joyce",
           "A Portrait of the Artist as a Young Man", 1916, 4217,
           "Once upon a time and a very good time it was"),
    PDWork("joyce-james", "Joyce, James", "James Joyce",
           "Ulysses", 1922, 4300,
           "Stately, plump Buck Mulligan came from the stairhead"),
    # Herman Melville (4)
    PDWork("melville-herman", "Melville, Herman", "Herman Melville",
           "Typee", 1846, 1900,
           "Six months at sea! Yes, reader, as I live, six months"),
    PDWork("melville-herman", "Melville, Herman", "Herman Melville",
           "Omoo", 1847, 4045,
           "It was the middle of a bright tropical afternoon"),
    PDWork("melville-herman", "Melville, Herman", "Herman Melville",
           "White-Jacket", 1850, 10712,
           "It was not a very white jacket, but white enough"),
    PDWork("melville-herman", "Melville, Herman", "Herman Melville",
           "Moby-Dick", 1851, 2701,
           "Call me Ishmael. Some years ago"),
    # Virginia Woolf (4) — all pre-1930 publications
    PDWork("woolf-virginia", "Woolf, Virginia", "Virginia Woolf",
           "The Voyage Out", 1915, 144,
           "As the streets that lead from the Strand to the Embankment"),
    PDWork("woolf-virginia", "Woolf, Virginia", "Virginia Woolf",
           "Night and Day", 1919, 1245,
           "It was a Sunday evening in October"),
    PDWork("woolf-virginia", "Woolf, Virginia", "Virginia Woolf",
           "Jacob's Room", 1922, 5670,
           "wrote Betty Flanders, pressing her heels rather deeper"),
    PDWork("woolf-virginia", "Woolf, Virginia", "Virginia Woolf",
           "Mrs. Dalloway", 1925, 71865,
           "said she would buy the flowers herself",
           end_anchor="For there she was"),
]


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

PG_START_RE = re.compile(
    r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^\n]*?\*\*\*",
    re.IGNORECASE,
)
PG_END_RE = re.compile(
    r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK",
    re.IGNORECASE,
)
ILLUSTRATION_RE = re.compile(r"\[Illustration[^\]]*\]", re.IGNORECASE | re.DOTALL)
SIDENOTE_RE = re.compile(r"\[Sidenote[^\]]*\]", re.IGNORECASE | re.DOTALL)
TRANSCRIBER_BLOCK_RE = re.compile(
    r"\[Transcriber'?s? note[^\]]*\]", re.IGNORECASE | re.DOTALL
)
FOOTNOTE_MARKER_RE = re.compile(r"\[\d{1,3}\]")
ITALIC_MARKUP_RE = re.compile(r"_([^_\n]{1,200}?)_")

TAIL_JUNK_RE = re.compile(
    r"(?i)(transcriber|project gutenberg|\betext\b|e-text|proofread"
    r"|errata|typographical|spelling and hyphenation|printed by"
    r"|riverside press|footnotes?\s*[:\]]|list of corrections"
    r"|^\s*(the\s+end|finis)\s*[.!]?\s*$"
    r"|^\s*\*+\s*$)"
)
# A tail paragraph is dropped only if it matches TAIL_JUNK_RE; short closing
# prose lines ("For there she was.") are preserved.


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def cut_pg_envelope(text: str, work: PDWork) -> str:
    m = PG_START_RE.search(text)
    if not m:
        raise ValueError(f"no PG START marker in #{work.gutenberg_id}")
    start = m.end()
    m2 = PG_END_RE.search(text, start)
    if not m2:
        raise ValueError(f"no PG END marker in #{work.gutenberg_id}")
    return text[start:m2.start()]


def _anchor_pattern(anchor: str) -> re.Pattern:
    """Punctuation- and whitespace-insensitive pattern over the anchor's
    alphanumeric tokens (PG editions vary in commas/em-dashes/quotes)."""
    tokens = re.findall(r"[A-Za-z0-9']+", anchor)
    return re.compile(
        r"[\W_]+".join(re.escape(tok) for tok in tokens), re.IGNORECASE
    )


def find_anchor_paragraph_start(text: str, anchor: str, work: PDWork) -> int:
    """Locate the anchor and rewind to the start of the containing paragraph."""
    m = _anchor_pattern(anchor).search(text)
    if not m:
        raise ValueError(
            f"anchor not found for {work.title!r} (#{work.gutenberg_id}): {anchor!r}"
        )
    para_break = text.rfind("\n\n", 0, m.start())
    return 0 if para_break < 0 else para_break + 2


def find_end_anchor_paragraph_end(text: str, end_anchor: str, work: PDWork) -> int:
    """Locate the LAST occurrence of the end anchor and advance to the end of
    the containing paragraph."""
    matches = list(_anchor_pattern(end_anchor).finditer(text))
    if not matches:
        raise ValueError(
            f"end anchor not found for {work.title!r} "
            f"(#{work.gutenberg_id}): {end_anchor!r}"
        )
    end = matches[-1].end()
    para_break = text.find("\n\n", end)
    return len(text) if para_break < 0 else para_break


def trim_tail(paragraphs: list[str]) -> list[str]:
    while paragraphs:
        tail = paragraphs[-1].strip()
        if not tail:
            paragraphs.pop()
            continue
        if TAIL_JUNK_RE.search(tail):
            paragraphs.pop()
            continue
        break
    return paragraphs


def clean_body(raw: str, work: PDWork) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = text.lstrip("﻿")
    text = cut_pg_envelope(text, work)

    # Inline artifacts first (so the anchor search isn't blocked by markup)
    text = ILLUSTRATION_RE.sub("", text)
    text = SIDENOTE_RE.sub("", text)
    text = TRANSCRIBER_BLOCK_RE.sub("", text)
    text = FOOTNOTE_MARKER_RE.sub("", text)
    text = ITALIC_MARKUP_RE.sub(r"\1", text)

    start = find_anchor_paragraph_start(text, work.anchor, work)
    if work.end_anchor:
        end = find_end_anchor_paragraph_end(text, work.end_anchor, work)
        if end <= start:
            raise ValueError(
                f"end anchor precedes start anchor for {work.title!r}"
            )
        body = text[start:end]
    else:
        body = text[start:]

    paragraphs = [p for p in body.split("\n\n")]
    paragraphs = trim_tail(paragraphs)
    body = "\n\n".join(p for p in paragraphs if p.strip())

    # Collapse 3+ newlines, strip trailing spaces per line
    body = re.sub(r"[ \t]+$", "", body, flags=re.MULTILINE)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


# ---------------------------------------------------------------------------
# Download + verification
# ---------------------------------------------------------------------------


def download(work: PDWork, skip_download: bool) -> str:
    RAW_CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = RAW_CACHE / f"pg{work.gutenberg_id}.txt"
    if cache_path.exists() and cache_path.stat().st_size > 10000:
        return cache_path.read_text(encoding="utf-8", errors="replace")
    if skip_download:
        raise ValueError(f"not cached and --skip-download set: #{work.gutenberg_id}")
    url = GUTENBERG_TXT_URL.format(id=work.gutenberg_id)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    text = data.decode("utf-8", errors="replace")
    cache_path.write_text(text, encoding="utf-8")
    time.sleep(1.0)  # politeness to gutenberg.org
    return text


def verify_title(raw: str, work: PDWork) -> str:
    m = re.search(r"(?im)^Title:\s*(.+)$", raw[:4000])
    pg_title = m.group(1).strip() if m else "(no Title header)"
    norm = lambda s: re.sub(
        r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s.lower())
    ).strip()
    if norm(work.title) not in norm(pg_title) and norm(pg_title) not in norm(work.title):
        # Allow subtitle variants ("Typee: A Romance...", "Omoo: Adventures...")
        head = norm(pg_title).split(":")[0]
        if norm(work.title) not in head and head not in norm(work.title):
            raise ValueError(
                f"title mismatch for #{work.gutenberg_id}: expected "
                f"{work.title!r}, PG header says {pg_title!r}"
            )
    return pg_title


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def slugify_title(title: str) -> str:
    import unicodedata

    s = unicodedata.normalize("NFKD", title)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s-]", "", s.lower())
    return re.sub(r"[\s_]+", "-", s).strip("-")


def emit_work(work: PDWork, body: str) -> Path:
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]
    word_count = len(body.split())
    paragraphs = sum(1 for p in body.split("\n\n") if p.strip())
    author_file_slug = slugify_title(work.display_author.replace(".", " "))
    filename = (
        f"{slugify_title(work.title)}-{author_file_slug}-{work.year}-{body_hash}.txt"
    )
    out_dir = SHELF_DIR / work.author_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    header = (
        f"# Title: {work.title}\n"
        f"# Author: {work.display_author}\n"
        f"# Creator: {work.canonical_author}\n"
        f"# Language: en\n"
        f"# Year: {work.year}\n"
        f"# Published: {work.year}\n"
        f"# Source: Project Gutenberg eBook #{work.gutenberg_id} "
        f"(https://www.gutenberg.org/ebooks/{work.gutenberg_id})\n"
        f"# Rights: Public domain in the USA (first published {work.year})\n"
        f"# Paragraphs: {paragraphs}\n"
        f"# Word Count: {word_count}\n"
        f"# Output Hash: {body_hash}\n"
        f"\n"
    )
    out_path = out_dir / filename
    # Remove stale versions of the same work (different hash suffix)
    stale_prefix = f"{slugify_title(work.title)}-{author_file_slug}-{work.year}-"
    for old in out_dir.glob(f"{stale_prefix}*.txt"):
        if old.name != filename:
            old.unlink()
    out_path.write_text(header + body, encoding="utf-8")
    return out_path


def emit_books_yaml(rows: list[dict]) -> Path:
    """books.yaml fragment consumed by emit_control_shelf_manifest.py
    (--books): supplies rights status + original language per work."""
    import yaml

    path = SHELF_DIR / "pd_books.yaml"
    payload = {
        "books": [
            {
                "canonical_author": r["canonical_author"],
                "canonical_title": r["title"],
                "original_language": "english",
                "status": "public_domain",
                "source": "project_gutenberg",
                "gutenberg_id": r["gutenberg_id"],
                "year_published": r["year"],
            }
            for r in rows
        ]
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-download", action="store_true",
                        help="Use only the local raw cache")
    parser.add_argument("--qc", action="store_true",
                        help="Print head/tail excerpts of each cleaned work")
    parser.add_argument("--only", default=None,
                        help="Comma-separated gutenberg ids to (re)build")
    args = parser.parse_args()

    only = {int(x) for x in args.only.split(",")} if args.only else None
    rows: list[dict] = []
    failures: list[str] = []
    for work in WORKS:
        if only and work.gutenberg_id not in only:
            continue
        try:
            raw = download(work, args.skip_download)
            pg_title = verify_title(raw, work)
            body = clean_body(raw, work)
            out_path = emit_work(work, body)
        except Exception as exc:
            failures.append(f"{work.author_slug}/{work.title}: {exc}")
            print(f"FAIL {work.title}: {exc}", file=sys.stderr)
            continue
        wc = len(body.split())
        rows.append({
            "canonical_author": work.canonical_author,
            "author_slug": work.author_slug,
            "title": work.title,
            "year": work.year,
            "gutenberg_id": work.gutenberg_id,
            "pg_title": pg_title,
            "form": work.form,
            "word_count": wc,
            "file": str(out_path.relative_to(SHELF_DIR)),
        })
        print(f"OK   {work.author_slug:22s} {work.year} {wc:>8,}w  {work.title}")
        if args.qc:
            head = normalize_ws(body[:240])
            tail = normalize_ws(body[-240:])
            print(f"     HEAD: {head[:200]}")
            print(f"     TAIL: {tail[-200:]}")

    if rows and not only:
        emit_books_yaml(rows)
        import json as _json
        (SHELF_DIR / "pd_shelf_inventory.json").write_text(
            _json.dumps(rows, indent=2, ensure_ascii=False)
        )
        by_author: dict[str, list[dict]] = {}
        for r in rows:
            by_author.setdefault(r["author_slug"], []).append(r)
        print(f"\n{len(rows)} works, {len(by_author)} authors, "
              f"{sum(r['word_count'] for r in rows):,} words total")
        for a, lst in sorted(by_author.items()):
            print(f"  {a:22s} {len(lst)} works "
                  f"{sum(r['word_count'] for r in lst):>9,}w")
    if failures:
        print(f"\n{len(failures)} FAILURES:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
