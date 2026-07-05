# Public-Domain Replication Shelf (pd_shelf)

A fully redistributable calibration corpus for replicating the ADR-0041
author-relative measurement space experiments (E1–E4) without any
rights-encumbered texts. Built for paper reviewers (TIER1 paper outline §9;
issue #95 item P8).

Every file on this shelf is **public domain in the United States** (first
published before 1930) and may be redistributed without restriction. The
texts are Project Gutenberg plain-text editions, cleaned to body-only prose.

## Contents

9 authors, 35 works, ~4.68M words. All works are English **originals**
(no translations — translated authors such as Dostoevsky, Tolstoy, Hugo,
Cervantes, Kafka, and Dumas were deliberately excluded so the shelf carries
no translator-voice confound, per ADR-0036). Emily Brontë is excluded
(single work; kept strictly distinct from Charlotte — the historical
Wuthering Heights misattribution). Faulkner was considered and excluded:
only one pre-1930 work is available on Project Gutenberg (< 3-work minimum).

| Author | Works (first-publication year) |
|---|---|
| Jane Austen | Sense and Sensibility (1811), Pride and Prejudice (1813), Mansfield Park (1814), Emma (1815), Persuasion (1817) |
| Charlotte Brontë | Jane Eyre (1847), Shirley (1849), Villette (1853), The Professor (1857) |
| Charles Dickens | Oliver Twist (1838), David Copperfield (1850), Bleak House (1853), Great Expectations (1861) |
| F. Scott Fitzgerald | This Side of Paradise (1920), The Beautiful and Damned (1922), The Great Gatsby (1925) |
| E. M. Forster | Where Angels Fear to Tread (1905), The Longest Journey (1907), A Room with a View (1908), Howards End (1910), A Passage to India (1924) |
| Nathaniel Hawthorne | The Scarlet Letter (1850), The House of the Seven Gables (1851), The Blithedale Romance (1852) |
| James Joyce | Dubliners (1914), A Portrait of the Artist as a Young Man (1916), Ulysses (1922) |
| Herman Melville | Typee (1846), Omoo (1847), White-Jacket (1850), Moby-Dick (1851) |
| Virginia Woolf | The Voyage Out (1915), Night and Day (1919), Jacob's Room (1922), Mrs. Dalloway (1925) |

Full machine-readable inventory (Gutenberg IDs, word counts, file names):
`pd_shelf_inventory.json`. Rights metadata: `pd_books.yaml`. Control-Shelf
manifest (body offsets, fidelity verdicts, centroid membership):
`pd_shelf_manifest.yaml`.

## Provenance and cleaning

Source: Project Gutenberg (https://www.gutenberg.org), plain-text editions,
fetched from `https://www.gutenberg.org/cache/epub/<id>/pg<id>.txt`. Each
file's `# Source:` header records its eBook number.

Cleaning is deterministic and reviewer-reproducible
(`tools/build_pd_shelf.py`):

1. Project Gutenberg header/license boilerplate cut at the
   `*** START/END OF THE PROJECT GUTENBERG EBOOK ***` markers.
2. Body anchored at the work's canonical opening sentence (per-work anchor
   in the script), which uniformly strips title pages, tables of contents,
   illustration lists, transcriber notes, and ALL prefatory matter —
   including editor/publisher introductions by other hands (e.g. the George
   Saintsbury introduction in the PG #1342 Pride and Prejudice).
3. Tail trimmed of transcriber notes, errata lists, printer colophons,
   publisher advertisements, and "THE END" markers (generic heuristics plus
   per-work end anchors where the residue is unmarked).
4. Inline `[Illustration]` / `[Sidenote]` / `[Transcriber's note]` blocks,
   bracketed footnote markers, and Gutenberg `_italic_` markup removed.

Each cleaned file carries the same `# Key: Value` metadata-header convention
as the contemporary `text/` shelf, and the `-<hash8>.txt` filename suffix
(SHA-256 prefix of the body) that the manifest tooling keys on.

## Reproducing the experiments (this release)

The shelf texts, the build manifest (`data/pd_manifest.yaml`), the per-work
D18 baselines (`data/pd_work_baselines/`), and the derived artifact
(`data/artifacts/author_space_pd_v1.json`) are all shipped, so the
experiments run directly. From the repository root (after `pip install -e .`):

```bash
# Rebuild the shelf from Project Gutenberg (optional; idempotent, ~35
# downloads — the cleaned texts are already shipped)
python3 tools/build_pd_shelf.py

# Rebuild the author-relative space artifact (MFW-Delta identity variant)
python3 tools/build_author_space.py \
    --baseline-dir data/pd_work_baselines \
    --manifest data/pd_manifest.yaml \
    --distance-variant mfw_delta \
    --output data/artifacts/author_space_pd_v1.json

# Validation experiments E1 (clustering), E2 (LOO attribution),
# E3 (dimension discrimination); add e6 for length sensitivity
python3 tools/validate_author_space.py \
    --baseline-dir data/pd_work_baselines \
    --manifest data/pd_manifest.yaml \
    --distance-variant mfw_delta \
    --experiments e1,e2,e3 \
    --output-dir reports/validation/pd_shelf

# E4: AI long-form placement against the PD manifold
python3 tools/run_e4_ai_placement.py \
    --artifact data/artifacts/author_space_pd_v1.json \
    --output-dir reports/validation/pd_shelf
```

The D18 per-work baseline *generation* pipeline (steps that produced
`data/pd_work_baselines/` from the raw texts) depends on a heavier stack
(spaCy/transformers) and is not part of this release; the baselines ship
precomputed. The MFW-Delta identity layer — which carries all headline
results — is computed from raw text by this package alone.

Gate definitions are in `docs/METHODOLOGY.md`; recorded results for this
shelf are under `reports/validation/pd_shelf/`.

## Redistribution

All 35 texts are public domain in the United States (publication before
1930). The shelf — raw texts, cleaned bodies, manifest, baselines, and the
derived `author_space_pd_v1.json` artifact — is fully redistributable with
no rights gating. (Readers outside the US should check the copyright term
applicable in their jurisdiction; several Fitzgerald/Forster/Woolf titles
are recent US PD entries.)
