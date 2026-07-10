"""
Author-Relative Measurement Space

An author-relative measurement space calibrated on a shelf of known
authors, replacing any single privileged origin centroid. Distances are
no longer reported against a single privileged centroid; instead every
distance is placed on two empirical calibration distributions:

- W (within-author): how far works by the SAME author typically sit from each
  other / from their own centroid.
- B (between-author): how far works by DIFFERENT authors typically sit.

A statement like "distance to ondaatje-michael is at p38 of within-author
variation" is therefore meaningful without any privileged reference author.

Architecture (see docs/METHODOLOGY.md, derived from ADR-0041 of the parent
project; centroid-hygiene flags follow its ADR-0036):

- Feature extraction: scalar stylometric dimensions from per-work baseline
  JSONs (``d18_profile`` with ``style_features`` fallback).
- MFW frequency block (optional, Burrows Delta): per-work relative
  frequencies of the top-N most frequent words across the shelf, z-scored
  per word shelf-wide. Distance = classic Burrows Delta (mean |z_i - z_j|).
  Built from manifest-sliced raw text; see :class:`MFWBlock`.
- Distance variants: ``d18`` (pooled euclidean, the original), ``d18_weighted``
  (per-dimension eta-squared weights), ``mfw_delta`` (Burrows Delta only),
  and ``combined``:

      d = alpha * d_d18 + (1 - alpha) * scale * d_delta

  where ``scale = median(pairwise d18) / median(pairwise Delta)`` over all
  distinct calibration-work pairs, so both components contribute on the d18
  scale before alpha weighting (persisted in the ``blend`` artifact block).
- Pooled normalization: per-dimension mean/std across ALL calibration-shelf
  works (not per-author), persisted as ``shelf_norm``.
- Author aggregation: per-author centroid + Ledoit-Wolf-shrunk covariance
  (diagonal fallback below 4 works), singleton / reference-only flags,
  translator + form metadata from the Control Shelf manifest when provided.
- Calibration: W and B distance distributions with quantiles p5..p95 and
  seeded bootstrap 95% CIs.
- Placement: ``place()`` returns per-author distances with W/B percentiles
  and plain-language calibration statements.

Usage:
    from author_manifold.author_space import AuthorRelativeSpace, load_shelf

    records = load_shelf(Path("data/baselines/voice/authors_voice"))
    space = AuthorRelativeSpace.build(records, generated="2026-06-09T00:00:00Z")
    result = space.place(baseline_json_dict)
    space.to_artifact(Path("data/baselines/voice/author_space/author_space_v1.json"))
"""

import hashlib
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

ARTIFACT_VERSION = "1.1.0"
DIMENSION_SET_VERSION = "v1"

# Distance variants supported by the space (ADR-0041 Amendment: MFW block).
DISTANCE_VARIANTS: Tuple[str, ...] = ("d18", "d18_weighted", "mfw_delta", "combined")
# Variants that require the MFW feature block / raw text at placement time.
MFW_VARIANTS = frozenset({"mfw_delta", "combined"})
# Variants that require the d18 baseline feature vector.
D18_VARIANTS = frozenset({"d18", "d18_weighted", "combined"})

# MFW block defaults.
MFW_DEFAULT_N = 300
MFW_TOKENIZER_ID = "lowercase_regex_v1"

# Length-matched envelope (LM-W) defaults — red-team K1 remediation (E8).
LM_ENVELOPE_VERSION = "1.0.0"
LM_DEFAULT_WINDOW_WORDS = 3000
LM_QUANTILE_LEVELS: Tuple[int, ...] = (50, 90, 95, 99)

# Vocabulary filters for the MFW block (issue #95 P3, paper outline C1
# topic-confound control). "none" = classic top-N by raw shelf frequency;
# "function_words_only" = restrict the candidate vocabulary to the closed-
# class list below BEFORE top-N selection, so the Delta vocabulary carries
# no topical/content signal.
MFW_VOCAB_FILTERS: Tuple[str, ...] = ("none", "function_words_only")

# Closed-class (function-word) list for vocab_filter="function_words_only".
#
# Construction: this is NOT a stop-word list (spaCy/NLTK stop lists mix in
# lexical verbs and miss tokenizer-specific contraction debris). It is built
# from the closed grammatical classes, following the stylometric tradition
# of Mosteller & Wallace (1964), Burrows (2002) and the function-word
# inventories surveyed in Stamatatos (2009) / Kestemont (2014):
#
#   1. determiners, articles and quantifiers;
#   2. personal / possessive / reflexive / indefinite / wh- pronouns;
#   3. prepositions (incl. complex-preposition heads used bare);
#   4. coordinating and subordinating conjunctions;
#   5. auxiliaries, copula forms and modals;
#   6. closed-class adverbs and verb particles (negation, degree, deixis,
#      conjunctive adverbs: not/never/here/there/now/then/very/too ...);
#   7. tokenizer-compatibility extension: the ``lowercase_regex_v1``
#      tokenizer (``\b[a-z']+\b``) splits typographic-apostrophe
#      contractions ("don’t" -> "don", "t") and keeps ASCII-apostrophe ones
#      whole ("don't"), while some shelf texts (e.g. McCarthy) spell
#      contractions bare ("dont"). All three surface families of the
#      underlying auxiliary+negation forms are therefore included
#      (don't / don / dont, plus clitic fragments s t d m ll re ve em).
#
# Open lexical classes (nouns, lexical verbs incl. "said"/"say", adjectives,
# -ly manner adverbs) are deliberately excluded — they are exactly the
# content-bearing leakage this filter exists to remove.
STYLOMETRIC_FUNCTION_WORDS: frozenset = frozenset("""
a an the this that these those each every either neither some any no none
all both few fewer many more most much several enough such another other
others own same certain

i me my mine myself we us our ours ourselves you your yours yourself
yourselves he him his himself she her hers herself it its itself they them
their theirs themselves one ones oneself who whom whose which what whatever
whichever whoever whomever anybody anyone anything everybody everyone
everything nobody nothing somebody someone something

about above across after against along alongside amid amidst among amongst
around as at atop before behind below beneath beside besides between beyond
but by despite down during except for from in inside into near of off on
onto out outside over past per round since through throughout till to
toward towards under underneath until unto up upon via with within without
like unlike concerning regarding versus aboard

and or nor so yet although though because if unless while whilst whereas
when whenever where wherever whether why how than lest once

am is are was were be been being do does did doing done have has had having
can could may might must shall should will would ought need

not never ever always often soon seldom rarely again almost already also
anyway anywhere everywhere nowhere somewhere away back even else far
further hardly here there then thus hence therefore however indeed instead
just maybe perhaps merely moreover nevertheless nonetheless now only quite
rather really scarcely still too very well forth aside apart ago twice
together

ain't aren't can't cannot couldn't didn't doesn't don't hadn't hasn't
haven't he'd he'll he's here's how's i'd i'll i'm i've isn't it's let's
mustn't needn't shan't she'd she'll she's shouldn't that's there's they'd
they'll they're they've wasn't we'd we'll we're we've weren't what's
where's who's won't wouldn't you'd you'll you're you've

s t d m ll re ve em o
ain aren couldn daren didn doesn don hadn hasn haven isn mustn needn
oughtn shan shouldn wasn weren wouldn
aint cant couldnt didnt doesnt dont hadnt hasnt havent isnt wasnt werent
wont wouldnt shouldnt mustnt im ive id ill youre youve youd youll hes shes
theyre theyve theyd theyll lets thats theres whos whats heres
""".split())

# Scalar numeric stylometric dimensions usable for author discrimination.
# All 18 verified present in d18_profile across the full authors_voice shelf
# (90/90 works, 2026-06-09 audit). Unlike INFLUENCE_DIMENSIONS in
# influence_adjacency.py, length-dependent dims (ttr, vocabulary_richness,
# repetition_ratio, sentiment_score) are retained here: pooled-shelf
# normalization plus W/B calibration measures them against how much they vary
# within vs between authors instead of against a single foreign centroid, so
# they inform rather than dominate. Their behavior is re-examined in the
# Phase 3 ablation experiments (ADR-0041, forthcoming).
DIMENSION_SET_V1: List[str] = [
    "lexical_density",
    "abstract_ratio",
    "formality_index",
    "complexity_score",
    "paragraph_cv",
    "sentiment_score",
    "repetition_ratio",
    "metaphor_per_100",
    "past_ratio",
    "present_ratio",
    "future_ratio",
    "char_ngram_mean",
    "function_word_ratio_extended",
    "self_focus_ratio",
    "sentence_cv",
    "certainty_index",
    "ttr",
    "vocabulary_richness",
]

# Quantile levels reported for the W/B calibration distributions.
QUANTILE_LEVELS: Tuple[int, ...] = (5, 10, 25, 50, 75, 90, 95)

# Forms eligible for the fiction calibration shelf (mirrors the §Q4
# fiction-only filter in influence_adjacency.py, per ADR-0036 Amendment 2).
FICTION_FORMS = frozenset({"novel", "story_collection"})

# Fidelity verdicts accepted from the Control Shelf manifest.
ACCEPTED_FIDELITY = frozenset({"clean", "edge_cleaned"})

# Non-author buckets that must never enter the space (see ADR-0036).
EXCLUDED_SLUGS = frozenset({"NONFIC_ON-WRITING"})

_HASH_RE = re.compile(r"-([0-9a-f]{8})_baseline$")


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def extract_features(
    baseline: Mapping[str, Any],
    dimensions: Sequence[str],
) -> Dict[str, Optional[float]]:
    """Extract raw scalar dimension values from a per-work baseline JSON.

    Looks in ``d18_profile`` first, then ``style_features`` (some dimensions
    only exist in the extended style block). Non-numeric or absent values
    map to None — the build imputes the shelf mean and records coverage.
    """
    d18 = baseline.get("d18_profile") or {}
    style = baseline.get("style_features") or {}
    values: Dict[str, Optional[float]] = {}
    for dim in dimensions:
        raw = d18.get(dim)
        if not isinstance(raw, (int, float)) or isinstance(raw, bool):
            raw = style.get(dim)
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            values[dim] = float(raw)
        else:
            values[dim] = None
    return values


# ---------------------------------------------------------------------------
# MFW (most-frequent-word) feature block — Burrows Delta
# ---------------------------------------------------------------------------

_MFW_TOKEN_RE = re.compile(r"\b[a-z\']+\b")


def mfw_tokenize(text: str) -> List[str]:
    """Lowercase word tokenization for the MFW block.

    Uses the exact regex convention of ``stylometry.tokenize_text`` /
    ``genetic_analyzer.tokenize_words`` (their non-spaCy fallback path:
    ``\\b[a-z']+\\b`` over lowercased text). The regex is applied directly
    rather than through those helpers because they prefer spaCy when it is
    installed: MFW z-vectors are persisted in the artifact, so featurization
    of new text at ``place()`` time must be byte-for-byte deterministic
    across environments (and cheap enough for 59 novels at build time).
    """
    return _MFW_TOKEN_RE.findall(text.lower())


@dataclass
class MFWBlock:
    """Burrows-Delta most-frequent-word frequency block.

    Math (classic Burrows 2002, mirroring ``stylometry.calculate_burrows_delta``
    conventions):

    1. Vocabulary = top-N words by total count across the calibration shelf
       (ties broken alphabetically for determinism). With
       ``vocab_filter="function_words_only"`` the candidate pool is first
       restricted to :data:`STYLOMETRIC_FUNCTION_WORDS` (closed-class list;
       see its docstring for the construction) and top-N selection applies
       AFTER that filter — a topic-confound control (issue #95 P3 / C1).
    2. Each work's feature = relative frequency per 1000 tokens of each word.
    3. Shelf-wide z-scoring per word: ``z = (f - mean) / std`` with mean/std
       over calibration works (std floored to 1.0 when ~zero).
    4. Delta distance = mean absolute z difference over the N words. Author
       centroids are mean z-vectors, so work<->work and work<->centroid use
       the same formula.
    """

    vocabulary: List[str]
    mean: np.ndarray                 # per-word mean relative frequency (per 1000)
    std: np.ndarray                  # per-word std (floored)
    tokenizer: str = MFW_TOKENIZER_ID
    vocab_filter: str = "none"       # one of MFW_VOCAB_FILTERS

    @property
    def n_mfw(self) -> int:
        return len(self.vocabulary)

    def relative_frequencies(self, tokens: Sequence[str]) -> np.ndarray:
        """Relative frequencies (per 1000 tokens) of the vocabulary words."""
        counts = Counter(tokens)
        length = len(tokens) or 1
        return np.array(
            [counts.get(word, 0) / length * 1000.0 for word in self.vocabulary],
            dtype=float,
        )

    def featurize_tokens(self, tokens: Sequence[str]) -> np.ndarray:
        """Z-score a token sequence against the stored shelf vocabulary norm."""
        return (self.relative_frequencies(tokens) - self.mean) / self.std

    def featurize_text(self, text: str) -> np.ndarray:
        """Tokenize raw text and z-score it against the stored vocabulary."""
        if self.tokenizer != MFW_TOKENIZER_ID:
            raise ValueError(f"Unsupported MFW tokenizer: {self.tokenizer!r}")
        return self.featurize_tokens(mfw_tokenize(text))

    @staticmethod
    def delta(z_a: np.ndarray, z_b: np.ndarray) -> float:
        """Classic Burrows Delta: mean |z_a - z_b| over the vocabulary."""
        return float(np.mean(np.abs(np.asarray(z_a) - np.asarray(z_b))))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_mfw": self.n_mfw,
            "tokenizer": self.tokenizer,
            "vocab_filter": self.vocab_filter,
            "frequency_unit": "per_1000_tokens",
            "vocabulary": list(self.vocabulary),
            "mean": [float(v) for v in self.mean],
            "std": [float(v) for v in self.std],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MFWBlock":
        return cls(
            vocabulary=list(data["vocabulary"]),
            mean=np.asarray(data["mean"], dtype=float),
            std=np.asarray(data["std"], dtype=float),
            tokenizer=data.get("tokenizer", MFW_TOKENIZER_ID),
            # Pre-filter artifacts carry no key -> "none" (backward compat).
            vocab_filter=data.get("vocab_filter", "none"),
        )


@dataclass
class WorkRecord:
    """One work on the shelf: raw features + provenance metadata."""

    author: str
    title: str
    path: str
    raw: Dict[str, Optional[float]]
    word_count: Optional[int] = None
    form: Optional[str] = None
    translator: Optional[str] = None
    # Raw-text provenance for the MFW block (manifest body slice; offsets are
    # CHARACTER offsets into the utf-8 decoded file):
    text_path: Optional[str] = None
    body_start: Optional[int] = None
    body_end: Optional[int] = None
    body_text: Optional[str] = field(default=None, repr=False)  # transient override
    # Populated during build:
    vector: Optional[np.ndarray] = None     # pooled-normalized
    mfw_z: Optional[np.ndarray] = None      # MFW z-vector (when block built)
    coverage: float = 1.0                   # fraction of dims present pre-imputation
    imputed_dims: List[str] = field(default_factory=list)


def record_body_text(record: WorkRecord) -> str:
    """Clean body text for a record: explicit ``body_text`` or manifest slice."""
    if record.body_text is not None:
        return record.body_text
    if not record.text_path:
        raise ValueError(
            f"MFW block needs raw text for {record.author}/{record.title}: no "
            "body_text and no text_path. Load the shelf with a Control Shelf "
            "manifest that provides corpus_root + file_path + body offsets."
        )
    text = Path(record.text_path).read_text(encoding="utf-8")
    start = record.body_start or 0
    end = record.body_end if record.body_end is not None else len(text)
    return text[start:end]


def work_record_from_baseline(
    baseline: Mapping[str, Any],
    *,
    author: str,
    path: str,
    dimensions: Sequence[str],
    form: Optional[str] = None,
    translator: Optional[str] = None,
    text_path: Optional[str] = None,
    body_start: Optional[int] = None,
    body_end: Optional[int] = None,
) -> WorkRecord:
    """Build a WorkRecord from a loaded baseline JSON dict."""
    doc = baseline.get("document") or {}
    metadata = doc.get("metadata") or {}
    title = metadata.get("title") or Path(path).stem
    word_count = doc.get("word_count")
    if not isinstance(word_count, int):
        word_count = None
    return WorkRecord(
        author=author,
        title=str(title),
        path=path,
        raw=extract_features(baseline, dimensions),
        word_count=word_count,
        form=form if form is not None else doc.get("form"),
        translator=translator if translator is not None else doc.get("translator"),
        text_path=text_path,
        body_start=body_start,
        body_end=body_end,
    )


# ---------------------------------------------------------------------------
# Shelf loading (per-work baseline JSONs, optional Control Shelf manifest)
# ---------------------------------------------------------------------------

def _baseline_source_hash(baseline_path: Path, baseline: Mapping[str, Any]) -> Optional[str]:
    """Source hash from filename (preferred) or document.metadata.output_hash."""
    match = _HASH_RE.search(baseline_path.stem)
    if match:
        return match.group(1)
    metadata = (baseline.get("document") or {}).get("metadata") or {}
    output_hash = metadata.get("output_hash")
    return str(output_hash) if output_hash else None


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the full Control Shelf manifest YAML."""
    import yaml  # local import: core stays light when no manifest is used

    with open(manifest_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_manifest_index(manifest_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load a Control Shelf manifest YAML, indexed by source_hash."""
    manifest = load_manifest(manifest_path)
    index: Dict[str, Dict[str, Any]] = {}
    for row in manifest.get("works", []):
        source_hash = row.get("source_hash")
        if source_hash:
            index[str(source_hash)] = row
    return index


def _resolve_corpus_root(
    corpus_root: Optional[str], manifest_path: Path
) -> Optional[Path]:
    """Resolve the manifest's corpus_root: absolute, cwd-relative, or relative
    to an ancestor of the manifest (the repo root in practice)."""
    if not corpus_root:
        return None
    path = Path(corpus_root)
    if path.is_absolute() or path.is_dir():
        return path
    for parent in Path(manifest_path).resolve().parents:
        candidate = parent / path
        if candidate.is_dir():
            return candidate
    logger.warning("Could not resolve manifest corpus_root %r", corpus_root)
    return path


def _manifest_row_eligible(row: Mapping[str, Any]) -> bool:
    """Centroid-eligible fiction with acceptable fidelity (ADR-0036 §Q4)."""
    if row.get("form") not in FICTION_FORMS:
        return False
    if row.get("fidelity_verdict") not in ACCEPTED_FIDELITY:
        return False
    membership = row.get("centroid_membership") or {}
    if membership.get("fiction_centroid") is False:
        return False
    return True


def load_shelf(
    baseline_dir: Path,
    *,
    dimensions: Optional[Sequence[str]] = None,
    manifest_path: Optional[Path] = None,
    authors: Optional[Sequence[str]] = None,
) -> List[WorkRecord]:
    """Load per-work baselines into WorkRecords.

    Args:
        baseline_dir: directory of ``<author_slug>/*_baseline.json``.
        dimensions: dimension list (default DIMENSION_SET_V1).
        manifest_path: optional Control Shelf manifest YAML. When given, only
            works present in the manifest that pass the centroid-eligible
            fiction filter are included, and form/translator metadata come
            from the manifest rather than the baseline JSON.
        authors: optional restriction to these author slugs.

    Returns:
        List of WorkRecords (raw features; vectors not yet normalized).
    """
    dims = list(dimensions or DIMENSION_SET_V1)
    manifest_index = None
    corpus_root: Optional[Path] = None
    if manifest_path:
        manifest = load_manifest(manifest_path)
        manifest_index = {
            str(row["source_hash"]): row
            for row in manifest.get("works", [])
            if row.get("source_hash")
        }
        corpus_root = _resolve_corpus_root(manifest.get("corpus_root"), manifest_path)
    author_filter = set(authors) if authors else None

    records: List[WorkRecord] = []
    skipped_manifest = 0
    for author_dir in sorted(p for p in Path(baseline_dir).iterdir() if p.is_dir()):
        slug = author_dir.name
        if slug in EXCLUDED_SLUGS:
            logger.debug("Skipping %s: excluded non-author bucket (ADR-0036)", slug)
            continue
        if author_filter is not None and slug not in author_filter:
            continue
        for baseline_file in sorted(author_dir.glob("*_baseline.json")):
            try:
                with open(baseline_file, "r", encoding="utf-8") as handle:
                    baseline = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Skipping unreadable baseline %s: %s", baseline_file, exc)
                continue

            form = None
            translator = None
            text_path = None
            body_start = None
            body_end = None
            if manifest_index is not None:
                source_hash = _baseline_source_hash(baseline_file, baseline)
                row = manifest_index.get(source_hash) if source_hash else None
                if row is None or not _manifest_row_eligible(row):
                    skipped_manifest += 1
                    continue
                form = row.get("form")
                translator = row.get("translator")
                if corpus_root is not None and row.get("file_path"):
                    text_path = str(corpus_root / row["file_path"])
                body_start = row.get("body_start_offset")
                body_end = row.get("body_end_offset")

            records.append(
                work_record_from_baseline(
                    baseline,
                    author=slug,
                    path=str(baseline_file),
                    dimensions=dims,
                    form=form,
                    translator=translator,
                    text_path=text_path,
                    body_start=body_start,
                    body_end=body_end,
                )
            )

    if manifest_index is not None:
        logger.info(
            "Manifest filter: kept %d works, skipped %d (non-fiction / fidelity / unlisted)",
            len(records), skipped_manifest,
        )
    return records


# ---------------------------------------------------------------------------
# Calibration distributions
# ---------------------------------------------------------------------------

@dataclass
class DistributionSummary:
    """Empirical distance distribution: samples, quantiles, bootstrap CIs."""

    n: int
    samples: List[float]                       # sorted ascending
    quantiles: Dict[str, float]                # "p50" -> value
    ci95: Dict[str, Tuple[float, float]]       # "p50" -> (lo, hi)

    _array: Optional[np.ndarray] = field(default=None, repr=False, compare=False)

    @classmethod
    def from_samples(
        cls,
        samples: Sequence[float],
        rng: np.random.Generator,
        n_bootstrap: int = 1000,
    ) -> "DistributionSummary":
        """Summarize samples with quantiles and seeded bootstrap 95% CIs."""
        arr = np.sort(np.asarray(samples, dtype=float))
        n = int(arr.size)
        if n == 0:
            return cls(n=0, samples=[], quantiles={}, ci95={})
        quantiles = {
            f"p{q}": float(np.percentile(arr, q)) for q in QUANTILE_LEVELS
        }
        ci95: Dict[str, Tuple[float, float]] = {}
        if n >= 2:
            idx = rng.integers(0, n, size=(n_bootstrap, n))
            boot = arr[idx]                                    # (n_bootstrap, n)
            boot_q = np.percentile(boot, QUANTILE_LEVELS, axis=1)  # (Q, n_bootstrap)
            for i, q in enumerate(QUANTILE_LEVELS):
                lo, hi = np.percentile(boot_q[i], [2.5, 97.5])
                ci95[f"p{q}"] = (float(lo), float(hi))
        else:
            ci95 = {f"p{q}": (quantiles[f"p{q}"], quantiles[f"p{q}"]) for q in QUANTILE_LEVELS}
        return cls(n=n, samples=[float(v) for v in arr], quantiles=quantiles, ci95=ci95)

    def _arr(self) -> np.ndarray:
        if self._array is None:
            self._array = np.asarray(self.samples, dtype=float)
        return self._array

    def percentile_of(self, value: float) -> Optional[float]:
        """Empirical percentile (mid-rank) of a distance against the samples."""
        arr = self._arr()
        if arr.size == 0:
            return None
        below = int(np.searchsorted(arr, value, side="left"))
        upper = int(np.searchsorted(arr, value, side="right"))
        equal = upper - below
        return float(100.0 * (below + 0.5 * equal) / arr.size)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "quantiles": self.quantiles,
            "ci95": {k: list(v) for k, v in self.ci95.items()},
            "samples": self.samples,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DistributionSummary":
        return cls(
            n=int(data.get("n", 0)),
            samples=[float(v) for v in data.get("samples", [])],
            quantiles={k: float(v) for k, v in (data.get("quantiles") or {}).items()},
            ci95={k: (float(v[0]), float(v[1])) for k, v in (data.get("ci95") or {}).items()},
        )


# ---------------------------------------------------------------------------
# Author aggregation
# ---------------------------------------------------------------------------

@dataclass
class AuthorEntry:
    """Per-author aggregate in pooled-normalized space."""

    slug: str
    centroid: np.ndarray
    covariance: np.ndarray          # full matrix (LW-shrunk) or diagonal
    covariance_kind: str            # "ledoit_wolf" | "diagonal"
    work_count: int
    works: List[WorkRecord]
    singleton: bool = False
    reference_only: bool = False
    forms: List[str] = field(default_factory=list)
    translators: List[str] = field(default_factory=list)
    mfw_centroid: Optional[np.ndarray] = None   # mean MFW z-vector (when block built)

    _cov_pinv: Optional[np.ndarray] = field(default=None, repr=False, compare=False)

    def flags(self) -> Dict[str, Any]:
        return {
            "singleton": self.singleton,
            "reference_only": self.reference_only,
            "translator_mixed": len(self.translators) > 1,
            "form_mixed": len(self.forms) > 1,
        }

    def cov_pinv(self) -> np.ndarray:
        if self._cov_pinv is None:
            self._cov_pinv = np.linalg.pinv(self.covariance)
        return self._cov_pinv


def _author_covariance(vectors: np.ndarray) -> Tuple[np.ndarray, str]:
    """Ledoit-Wolf shrunk covariance; diagonal fallback below 4 works.

    Diagonal fallback uses per-dim variance with a floor of 1e-2 (normalized
    units); singletons get the identity (no within-author information).
    """
    n_works, n_dims = vectors.shape
    if n_works >= 4:
        from sklearn.covariance import LedoitWolf

        lw = LedoitWolf().fit(vectors)
        return np.asarray(lw.covariance_, dtype=float), "ledoit_wolf"
    if n_works >= 2:
        var = np.maximum(np.var(vectors, axis=0, ddof=1), 1e-2)
        return np.diag(var), "diagonal"
    return np.eye(n_dims), "diagonal"


# ---------------------------------------------------------------------------
# Placement results
# ---------------------------------------------------------------------------

@dataclass
class AuthorPlacement:
    """Distance from a placed vector to one author centroid, calibrated."""

    author: str
    distance: float
    w_percentile: Optional[float]
    b_percentile: Optional[float]
    statement: str
    reference_only: bool = False
    singleton: bool = False


@dataclass
class PlacementResult:
    """Result of placing a vector/baseline into the author-relative space."""

    method: str                              # "euclidean" | "mahalanobis"
    placements: List[AuthorPlacement]        # ranked ascending by distance
    coverage: float                          # fraction of dims present
    imputed_dims: List[str]
    dimensions: List[str]

    @property
    def nearest(self) -> Optional[AuthorPlacement]:
        return self.placements[0] if self.placements else None

    def distances(self) -> Dict[str, float]:
        return {p.author: p.distance for p in self.placements}


# ---------------------------------------------------------------------------
# Verdict bands (W-percentile threshold mapping)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VerdictBands:
    """Maps the 4-tier verdict vocabulary onto W-distribution percentiles.

    Per ADR-0041, the verdict *names* are kept but the cut points re-derive
    from the within-author (W) calibration distribution instead of raw
    σ-from-origin:

    - ``within_baseline``: distance <= W-p50 (as close as a known author's
      own works typically sit to their own centroid)
    - ``marginal``:        W-p50 < distance <= W-p90
    - ``anomaly``:         distance > W-p90
    - the hard ``anomaly`` *flag* (the 4th tier of the legacy vocabulary,
      formerly ``distance >= 2.5σ``) trips at distance > W-p95.
    """

    w_p50: float
    w_p90: float
    w_p95: float
    family: str = "loo"

    #: Ordered verdict vocabulary (4 tiers; the last is the hard flag).
    TIERS: ClassVar[Tuple[str, ...]] = (
        "within_baseline", "marginal", "anomaly", "anomaly_flag"
    )

    @classmethod
    def from_space(cls, space: "AuthorRelativeSpace", family: str = "loo") -> "VerdictBands":
        """Derive bands from a space's W distribution.

        ``family`` selects the within-author calibration family; the default
        ``"loo"`` (leave-one-out work->own-centroid) matches the family used
        by ``AuthorRelativeSpace.place()`` for work->centroid distances.
        """
        dist = space.within.get(family)
        if dist is None or not dist.quantiles:
            raise ValueError(
                f"Space has no within-author distribution for family {family!r}"
            )
        return cls(
            w_p50=dist.quantiles["p50"],
            w_p90=dist.quantiles["p90"],
            w_p95=dist.quantiles["p95"],
            family=family,
        )

    def classify(self, distance: float) -> str:
        """Return the verdict tier name for a calibrated distance."""
        if distance <= self.w_p50:
            return "within_baseline"
        if distance <= self.w_p90:
            return "marginal"
        return "anomaly"

    def anomaly_flag(self, distance: float) -> bool:
        """Hard anomaly flag (legacy ``>= 2.5σ`` tier), now > W-p95."""
        return distance > self.w_p95


# ---------------------------------------------------------------------------
# AuthorRelativeSpace
# ---------------------------------------------------------------------------

class AuthorRelativeSpace:
    """Author-relative measurement space calibrated on a gold shelf.

    Build with :meth:`build` from WorkRecords, or load a persisted artifact
    with :meth:`from_artifact`. See module docstring and ADR-0041
    (forthcoming) for the measurement model; ADR-0036 for centroid hygiene.
    """

    def __init__(
        self,
        *,
        dimensions: List[str],
        shelf_mean: np.ndarray,
        shelf_std: np.ndarray,
        authors: Dict[str, AuthorEntry],
        reference_authors: Dict[str, AuthorEntry],
        within: Dict[str, DistributionSummary],
        between: Dict[str, DistributionSummary],
        meta: Dict[str, Any],
        mfw: Optional[MFWBlock] = None,
        distance_variant: str = "d18",
        alpha: float = 0.5,
        dimension_weights: Optional[Mapping[str, float]] = None,
        blend: Optional[Dict[str, float]] = None,
    ):
        if distance_variant not in DISTANCE_VARIANTS:
            raise ValueError(
                f"Unknown distance variant: {distance_variant!r} "
                f"(expected one of {DISTANCE_VARIANTS})"
            )
        if distance_variant in MFW_VARIANTS and mfw is None:
            raise ValueError(
                f"Distance variant {distance_variant!r} requires the MFW block"
            )
        if distance_variant == "combined" and not blend:
            raise ValueError("Distance variant 'combined' requires blend scales")
        self.dimensions = dimensions
        self.shelf_mean = shelf_mean
        self.shelf_std = shelf_std
        self.authors = authors
        self.reference_authors = reference_authors
        self.within = within      # families: "loo", "pairs", "pooled"
        self.between = between    # families: "pairs", "work_to_centroid"
        self.meta = meta
        self.mfw = mfw
        self.distance_variant = distance_variant
        self.alpha = float(alpha)
        self.dimension_weights = dict(dimension_weights) if dimension_weights else None
        self.blend = dict(blend) if blend else None
        # Lazily-computed d18-sub-distance calibration distributions for
        # consumers that must fall back to the d18 feature block when the
        # active variant requires raw text (see d18_fallback_calibration).
        self._d18_fallback_calib: Optional[Dict[str, DistributionSummary]] = None
        # Per-dimension weighting (d18_weighted only). Weights are normalized
        # to mean 1 so weighted distances stay on the unweighted d18 scale;
        # applied as sqrt(w) per-dim scaling => weighted euclidean
        # d = sqrt(sum_i w_i (a_i - b_i)^2).
        self._weight_sqrt: Optional[np.ndarray] = None
        if distance_variant == "d18_weighted":
            if not self.dimension_weights:
                raise ValueError(
                    "Distance variant 'd18_weighted' requires dimension_weights"
                )
            w = np.array(
                [float(self.dimension_weights.get(d, 0.0)) for d in dimensions],
                dtype=float,
            )
            if not np.all(np.isfinite(w)) or w.sum() <= 0:
                raise ValueError("dimension_weights must be finite with positive sum")
            self._weight_sqrt = np.sqrt(w * (len(w) / w.sum()))

    # -- distance components ------------------------------------------------

    def d18_component(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Pooled-normalized euclidean distance (eta^2-weighted for
        d18_weighted; plain otherwise — the combined blend always uses the
        plain pooled d18 per the ADR-0041 amendment formula)."""
        delta = np.asarray(vec_a, dtype=float) - np.asarray(vec_b, dtype=float)
        if self._weight_sqrt is not None:
            delta = delta * self._weight_sqrt
        return float(np.linalg.norm(delta))

    def work_distance(
        self,
        vec_a: Optional[np.ndarray],
        mfw_a: Optional[np.ndarray],
        vec_b: Optional[np.ndarray],
        mfw_b: Optional[np.ndarray],
    ) -> float:
        """Active-variant distance between two feature points.

        Each point is a (d18 pooled-normalized vector, MFW z-vector) pair;
        either element may be an author centroid (both blocks aggregate by
        arithmetic mean). Variants:

        - ``d18`` / ``d18_weighted``: (weighted) euclidean on the d18 block.
        - ``mfw_delta``: Burrows Delta = mean |z_i - z_j| over the MFW vocab.
        - ``combined``: ``alpha * d_d18 + (1 - alpha) * scale * d_delta``
          with ``scale = blend['scale'] = median(pairwise d18) /
          median(pairwise Delta)`` over all distinct calibration-work pairs,
          putting both components on the d18 scale before alpha weighting.
        """
        variant = self.distance_variant
        if variant in ("d18", "d18_weighted"):
            return self.d18_component(vec_a, vec_b)
        if mfw_a is None or mfw_b is None:
            raise ValueError(
                f"Distance variant {variant!r} requires MFW z-vectors on both points"
            )
        delta_d = MFWBlock.delta(mfw_a, mfw_b)
        if variant == "mfw_delta":
            return delta_d
        # combined
        return (
            self.alpha * self.d18_component(vec_a, vec_b)
            + (1.0 - self.alpha) * float(self.blend["scale"]) * delta_d
        )

    # -- construction -------------------------------------------------------

    @classmethod
    def build(
        cls,
        records: Sequence[WorkRecord],
        *,
        dimensions: Optional[Sequence[str]] = None,
        min_works: int = 3,
        seed: int = 20260609,
        n_bootstrap: int = 1000,
        generated: Optional[str] = None,
        manifest_path: Optional[str] = None,
        mfw_n: Optional[int] = None,
        distance_variant: str = "d18",
        alpha: float = 0.5,
        dimension_weights: Optional[Mapping[str, float]] = None,
        mfw_vocab_filter: str = "none",
    ) -> "AuthorRelativeSpace":
        """Build the space from WorkRecords.

        Authors with fewer than ``min_works`` works become reference-only:
        present in the artifact but excluded from shelf normalization and
        from the W/B calibration distributions.

        Args (MFW extension; ADR-0041 amendment):
            mfw_n: build the Burrows-Delta MFW block over the top ``mfw_n``
                shelf words (requires raw text per record: ``body_text`` or
                manifest-derived ``text_path`` + body offsets). Defaults to
                ``MFW_DEFAULT_N`` when the variant needs it, else off.
            distance_variant: one of ``DISTANCE_VARIANTS``; the W/B
                calibration distributions are computed under this distance.
            alpha: blend weight for the ``combined`` variant.
            dimension_weights: per-dimension weights (e.g. E3 eta-squared)
                for ``d18_weighted``.
            mfw_vocab_filter: one of ``MFW_VOCAB_FILTERS``;
                ``"function_words_only"`` restricts the MFW candidate
                vocabulary to :data:`STYLOMETRIC_FUNCTION_WORDS` BEFORE
                top-N selection (topic-confound control, issue #95 P3).
                Persisted in the artifact (``feature_blocks.mfw_delta``).
        """
        dims = list(dimensions or DIMENSION_SET_V1)
        rng = np.random.default_rng(seed)
        if distance_variant not in DISTANCE_VARIANTS:
            raise ValueError(f"Unknown distance variant: {distance_variant!r}")
        if mfw_vocab_filter not in MFW_VOCAB_FILTERS:
            raise ValueError(
                f"Unknown MFW vocab filter: {mfw_vocab_filter!r} "
                f"(expected one of {MFW_VOCAB_FILTERS})"
            )
        if mfw_n is None and distance_variant in MFW_VARIANTS:
            mfw_n = MFW_DEFAULT_N

        by_author: Dict[str, List[WorkRecord]] = {}
        for record in records:
            by_author.setdefault(record.author, []).append(record)

        calibrated_slugs = sorted(s for s, w in by_author.items() if len(w) >= min_works)
        reference_slugs = sorted(s for s, w in by_author.items() if len(w) < min_works)
        if len(calibrated_slugs) < 2:
            raise ValueError(
                f"Need >= 2 authors with >= {min_works} works to calibrate; "
                f"got {len(calibrated_slugs)}"
            )

        # Pooled normalization from the calibration shelf only (reference
        # authors are measured in the space, not allowed to define it).
        calib_records = [r for slug in calibrated_slugs for r in by_author[slug]]
        raw_matrix = np.array(
            [[np.nan if r.raw.get(d) is None else r.raw[d] for d in dims] for r in calib_records],
            dtype=float,
        )
        with np.errstate(invalid="ignore"):
            shelf_mean = np.nanmean(raw_matrix, axis=0)
            shelf_std = np.nanstd(raw_matrix, axis=0)
        dim_coverage: Dict[str, float] = {}
        for i, dim in enumerate(dims):
            present = int(np.sum(~np.isnan(raw_matrix[:, i])))
            dim_coverage[dim] = present / len(calib_records) if calib_records else 0.0
            if present == 0:
                logger.warning("Dimension %s absent from entire calibration shelf", dim)
                shelf_mean[i] = 0.0
                shelf_std[i] = 1.0
            elif shelf_std[i] < 1e-9:
                logger.warning("Dimension %s has ~zero shelf variance; std floored", dim)
                shelf_std[i] = 1.0

        # Normalize every record (calibrated + reference) against shelf_norm,
        # imputing missing dims at the shelf mean (z = 0) and recording coverage.
        for record in records:
            cls._normalize_record(record, dims, shelf_mean, shelf_std)

        # Author aggregation.
        authors: Dict[str, AuthorEntry] = {}
        reference_authors: Dict[str, AuthorEntry] = {}
        for slug, works in sorted(by_author.items()):
            entry = cls._aggregate_author(slug, works, reference_only=slug in reference_slugs)
            (reference_authors if entry.reference_only else authors)[slug] = entry

        # MFW frequency block (Burrows Delta). Vocabulary + per-word norm come
        # from the calibration shelf only; every record (calibrated +
        # reference) gets a z-vector against that norm.
        mfw_block: Optional[MFWBlock] = None
        blend: Optional[Dict[str, float]] = None
        if mfw_n:
            mfw_block = cls._build_mfw_block(
                records, calib_records, mfw_n, vocab_filter=mfw_vocab_filter
            )
            for entry in list(authors.values()) + list(reference_authors.values()):
                entry.mfw_centroid = np.vstack(
                    [w.mfw_z for w in entry.works]
                ).mean(axis=0)
            blend = cls._blend_scales(calib_records, mfw_block, alpha)

        space = cls(
            dimensions=dims,
            shelf_mean=shelf_mean,
            shelf_std=shelf_std,
            authors=authors,
            reference_authors=reference_authors,
            within={},
            between={},
            meta={},
            mfw=mfw_block,
            distance_variant=distance_variant,
            alpha=alpha,
            dimension_weights=dimension_weights,
            blend=blend,
        )

        # Calibration distributions (calibrated authors only), computed under
        # the ACTIVE distance variant so W/B percentiles match place().
        w_loo, w_pairs = space._within_samples()
        b_pairs, b_w2c = space._between_samples()
        space.within = {
            "loo": DistributionSummary.from_samples(w_loo, rng, n_bootstrap),
            "pairs": DistributionSummary.from_samples(w_pairs, rng, n_bootstrap),
            "pooled": DistributionSummary.from_samples(w_loo + w_pairs, rng, n_bootstrap),
        }
        space.between = {
            "pairs": DistributionSummary.from_samples(b_pairs, rng, n_bootstrap),
            "work_to_centroid": DistributionSummary.from_samples(b_w2c, rng, n_bootstrap),
        }

        fw_suffix = "_fwonly" if mfw_vocab_filter == "function_words_only" else ""
        method_label = {
            "d18": "euclidean_pooled_norm",
            "d18_weighted": "weighted_euclidean_pooled_norm",
            "mfw_delta": f"burrows_delta_mfw{mfw_n}{fw_suffix}",
            "combined": f"blended_d18_mfw_delta_alpha{alpha:g}{fw_suffix}",
        }[distance_variant]
        feature_blocks: Dict[str, Any] = {
            "d18": {"n_dims": len(dims), "dimension_set_version": DIMENSION_SET_VERSION},
        }
        if mfw_block is not None:
            feature_blocks["mfw_delta"] = {
                "n_mfw": mfw_block.n_mfw,
                "tokenizer": mfw_block.tokenizer,
                "vocab_filter": mfw_block.vocab_filter,
                "frequency_unit": "per_1000_tokens",
            }
        space.meta = {
            "version": ARTIFACT_VERSION,
            "generated": generated,
            "manifest_path": manifest_path,
            "dimension_set_version": DIMENSION_SET_VERSION,
            "n_authors": len(authors),
            "n_works": sum(e.work_count for e in authors.values()),
            "n_reference_authors": len(reference_authors),
            "min_works": min_works,
            "seed": seed,
            "n_bootstrap": n_bootstrap,
            "distance_method": method_label,
            "distance_variant": distance_variant,
            "alpha": alpha,
            "feature_blocks": feature_blocks,
            "dimension_coverage": dim_coverage,
        }
        return space

    @staticmethod
    def _build_mfw_block(
        records: Sequence[WorkRecord],
        calib_records: Sequence[WorkRecord],
        n_mfw: int,
        vocab_filter: str = "none",
    ) -> MFWBlock:
        """Tokenize body texts, pick shelf MFW vocab, z-score every record.

        ``vocab_filter="function_words_only"`` restricts the candidate pool
        to :data:`STYLOMETRIC_FUNCTION_WORDS` before top-N selection.
        """
        if vocab_filter not in MFW_VOCAB_FILTERS:
            raise ValueError(f"Unknown MFW vocab filter: {vocab_filter!r}")
        counts: Dict[int, Counter] = {}
        lengths: Dict[int, int] = {}
        for record in records:
            tokens = mfw_tokenize(record_body_text(record))
            counts[id(record)] = Counter(tokens)
            lengths[id(record)] = len(tokens)
            if not tokens:
                logger.warning(
                    "MFW: no tokens for %s/%s", record.author, record.title
                )

        shelf_counts: Counter = Counter()
        for record in calib_records:
            shelf_counts.update(counts[id(record)])
        if vocab_filter == "function_words_only":
            shelf_counts = Counter({
                word: count
                for word, count in shelf_counts.items()
                if word in STYLOMETRIC_FUNCTION_WORDS
            })
        # Deterministic vocabulary: by descending count, ties alphabetical.
        vocabulary = [
            word
            for word, _ in sorted(
                shelf_counts.items(), key=lambda kv: (-kv[1], kv[0])
            )[:n_mfw]
        ]
        if len(vocabulary) < n_mfw:
            logger.warning(
                "MFW: shelf has only %d distinct words%s (< requested %d)",
                len(vocabulary),
                " after function-word filtering"
                if vocab_filter == "function_words_only" else "",
                n_mfw,
            )

        def rel_freqs(record: WorkRecord) -> np.ndarray:
            length = lengths[id(record)] or 1
            c = counts[id(record)]
            return np.array(
                [c.get(w, 0) / length * 1000.0 for w in vocabulary], dtype=float
            )

        calib_matrix = np.vstack([rel_freqs(r) for r in calib_records])
        mean = calib_matrix.mean(axis=0)
        std = calib_matrix.std(axis=0)
        std = np.where(std < 1e-9, 1.0, std)
        block = MFWBlock(
            vocabulary=vocabulary, mean=mean, std=std, vocab_filter=vocab_filter
        )
        for record in records:
            record.mfw_z = (rel_freqs(record) - mean) / std
        return block

    @staticmethod
    def _blend_scales(
        calib_records: Sequence[WorkRecord], mfw_block: MFWBlock, alpha: float
    ) -> Dict[str, float]:
        """Blend normalizers: shelf-wide between-work medians of each metric.

        ``scale = d18_between_median / delta_between_median`` so that
        ``alpha * d18 + (1 - alpha) * scale * delta`` weighs the two blocks
        equally (per unit alpha) at the typical work-pair separation. Medians
        are over ALL distinct calibration-work pairs (within- and cross-
        author), using the PLAIN pooled d18 euclidean (no eta^2 weighting).
        """
        from scipy.spatial.distance import pdist

        d18_matrix = np.vstack([r.vector for r in calib_records])
        mfw_matrix = np.vstack([r.mfw_z for r in calib_records])
        d18_median = float(np.median(pdist(d18_matrix, metric="euclidean")))
        delta_median = float(
            np.median(pdist(mfw_matrix, metric="cityblock") / mfw_block.n_mfw)
        )
        if delta_median <= 0:
            raise ValueError("Degenerate MFW block: zero median pairwise Delta")
        return {
            "d18_between_median": d18_median,
            "delta_between_median": delta_median,
            "scale": d18_median / delta_median,
        }

    @staticmethod
    def _normalize_record(
        record: WorkRecord,
        dims: List[str],
        shelf_mean: np.ndarray,
        shelf_std: np.ndarray,
    ) -> None:
        values = np.empty(len(dims), dtype=float)
        imputed: List[str] = []
        for i, dim in enumerate(dims):
            raw = record.raw.get(dim)
            if raw is None:
                values[i] = shelf_mean[i]   # impute shelf mean -> z = 0
                imputed.append(dim)
            else:
                values[i] = raw
        record.vector = (values - shelf_mean) / shelf_std
        record.imputed_dims = imputed
        record.coverage = 1.0 - (len(imputed) / len(dims)) if dims else 0.0

    @staticmethod
    def _aggregate_author(
        slug: str, works: List[WorkRecord], *, reference_only: bool
    ) -> AuthorEntry:
        vectors = np.vstack([w.vector for w in works])
        covariance, kind = _author_covariance(vectors)
        forms = sorted({w.form for w in works if w.form})
        translators = sorted({w.translator for w in works if w.translator})
        return AuthorEntry(
            slug=slug,
            centroid=vectors.mean(axis=0),
            covariance=covariance,
            covariance_kind=kind,
            work_count=len(works),
            works=works,
            singleton=len(works) == 1,
            reference_only=reference_only,
            forms=forms,
            translators=translators,
        )

    @staticmethod
    def _entry_arrays(
        entry: AuthorEntry,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Stacked (d18, mfw) matrices for an author's works."""
        vectors = np.vstack([w.vector for w in entry.works])
        mfw = None
        if entry.works and entry.works[0].mfw_z is not None:
            mfw = np.vstack([w.mfw_z for w in entry.works])
        return vectors, mfw

    def _within_samples(self) -> Tuple[List[float], List[float]]:
        """W families under the active distance: leave-one-out
        work->other-works-centroid, and work pairs."""
        loo: List[float] = []
        pairs: List[float] = []
        for entry in self.authors.values():
            vectors, mfw = self._entry_arrays(entry)
            n = vectors.shape[0]
            if n >= 3:
                total = vectors.sum(axis=0)
                mfw_total = mfw.sum(axis=0) if mfw is not None else None
                for i in range(n):
                    centroid = (total - vectors[i]) / (n - 1)
                    mfw_centroid = (
                        (mfw_total - mfw[i]) / (n - 1) if mfw is not None else None
                    )
                    loo.append(
                        self.work_distance(
                            vectors[i], mfw[i] if mfw is not None else None,
                            centroid, mfw_centroid,
                        )
                    )
            for i in range(n):
                for j in range(i + 1, n):
                    pairs.append(
                        self.work_distance(
                            vectors[i], mfw[i] if mfw is not None else None,
                            vectors[j], mfw[j] if mfw is not None else None,
                        )
                    )
        return loo, pairs

    def _between_samples(self) -> Tuple[List[float], List[float]]:
        """B families under the active distance: cross-author work pairs, and
        work->other-author-centroid."""
        slugs = sorted(self.authors.keys())
        arrays = {slug: self._entry_arrays(self.authors[slug]) for slug in slugs}
        pairs: List[float] = []
        work_to_centroid: List[float] = []
        for i, slug_a in enumerate(slugs):
            vec_a, mfw_a = arrays[slug_a]
            n_a = vec_a.shape[0]
            for slug_b in slugs:
                if slug_a == slug_b:
                    continue
                entry_b = self.authors[slug_b]
                for k in range(n_a):
                    work_to_centroid.append(
                        self.work_distance(
                            vec_a[k], mfw_a[k] if mfw_a is not None else None,
                            entry_b.centroid, entry_b.mfw_centroid,
                        )
                    )
            for slug_b in slugs[i + 1:]:
                vec_b, mfw_b = arrays[slug_b]
                for k in range(n_a):
                    for m in range(vec_b.shape[0]):
                        pairs.append(
                            self.work_distance(
                                vec_a[k], mfw_a[k] if mfw_a is not None else None,
                                vec_b[m], mfw_b[m] if mfw_b is not None else None,
                            )
                        )
        return pairs, work_to_centroid

    def d18_fallback_calibration(self) -> Dict[str, DistributionSummary]:
        """W/B calibration families recomputed under the plain d18 sub-distance.

        When the active ``distance_variant`` requires raw text (``mfw_delta``
        / ``combined``) but a caller holds only a D18 observation dict, the
        honest fallback is: measure plain pooled-euclidean distances on the
        d18 feature block AND read percentiles against d18-scale W/B
        distributions — never against the active variant's (e.g.
        Burrows-Delta-scaled) distributions, which live on a different scale.

        Recomputed from the persisted per-work d18 vectors on first access
        and cached on the space. Families mirror the persisted ones:

        - ``within_loo``: leave-one-out work -> own-author centroid (n >= 3)
        - ``within_pairs``: same-author work pairs
        - ``between_work_to_centroid``: work -> other-author centroid
        - ``between_pairs``: cross-author work pairs

        For a ``d18`` space these are byte-identical to the persisted
        distributions, so they are returned directly (no recompute).
        """
        if self._d18_fallback_calib is not None:
            return self._d18_fallback_calib
        if self.distance_variant == "d18":
            self._d18_fallback_calib = {
                "within_loo": self.within["loo"],
                "within_pairs": self.within["pairs"],
                "between_work_to_centroid": self.between["work_to_centroid"],
                "between_pairs": self.between["pairs"],
            }
            return self._d18_fallback_calib

        loo: List[float] = []
        w_pairs: List[float] = []
        slugs = sorted(self.authors)
        arrays = {
            slug: np.vstack([w.vector for w in self.authors[slug].works])
            for slug in slugs
        }
        for slug in slugs:
            vectors = arrays[slug]
            n = vectors.shape[0]
            if n >= 3:
                total = vectors.sum(axis=0)
                for i in range(n):
                    centroid = (total - vectors[i]) / (n - 1)
                    loo.append(float(np.linalg.norm(vectors[i] - centroid)))
            for i in range(n):
                for j in range(i + 1, n):
                    w_pairs.append(float(np.linalg.norm(vectors[i] - vectors[j])))
        b_pairs: List[float] = []
        b_w2c: List[float] = []
        for i, slug_a in enumerate(slugs):
            vec_a = arrays[slug_a]
            for slug_b in slugs:
                if slug_a == slug_b:
                    continue
                centroid_b = self.authors[slug_b].centroid
                for k in range(vec_a.shape[0]):
                    b_w2c.append(float(np.linalg.norm(vec_a[k] - centroid_b)))
            for slug_b in slugs[i + 1:]:
                vec_b = arrays[slug_b]
                for k in range(vec_a.shape[0]):
                    for m in range(vec_b.shape[0]):
                        b_pairs.append(float(np.linalg.norm(vec_a[k] - vec_b[m])))

        rng = np.random.default_rng(int(self.meta.get("seed") or 20260609))
        n_bootstrap = int(self.meta.get("n_bootstrap") or 1000)
        self._d18_fallback_calib = {
            "within_loo": DistributionSummary.from_samples(loo, rng, n_bootstrap),
            "within_pairs": DistributionSummary.from_samples(w_pairs, rng, n_bootstrap),
            "between_work_to_centroid": DistributionSummary.from_samples(
                b_w2c, rng, n_bootstrap
            ),
            "between_pairs": DistributionSummary.from_samples(b_pairs, rng, n_bootstrap),
        }
        return self._d18_fallback_calib

    # -- measurement --------------------------------------------------------

    def normalize_raw(
        self, raw: Mapping[str, Optional[float]]
    ) -> Tuple[np.ndarray, float, List[str]]:
        """Normalize a raw dim->value mapping. Returns (vector, coverage, imputed)."""
        values = np.empty(len(self.dimensions), dtype=float)
        imputed: List[str] = []
        for i, dim in enumerate(self.dimensions):
            value = raw.get(dim)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values[i] = float(value)
            else:
                values[i] = self.shelf_mean[i]
                imputed.append(dim)
        vector = (values - self.shelf_mean) / self.shelf_std
        coverage = 1.0 - (len(imputed) / len(self.dimensions)) if self.dimensions else 0.0
        return vector, coverage, imputed

    def _coerce_vector(
        self,
        vector_or_baseline: Union[Mapping[str, Any], Sequence[float], np.ndarray, str, Path],
    ) -> Tuple[np.ndarray, float, List[str]]:
        """Accept a baseline JSON dict/path, a dim->value mapping, or a raw vector."""
        obj = vector_or_baseline
        if isinstance(obj, (str, Path)):
            with open(obj, "r", encoding="utf-8") as handle:
                obj = json.load(handle)
        if isinstance(obj, Mapping):
            if "d18_profile" in obj or "style_features" in obj:
                raw = extract_features(obj, self.dimensions)
            else:
                raw = {dim: obj.get(dim) for dim in self.dimensions}
            return self.normalize_raw(raw)
        arr = np.asarray(obj, dtype=float)
        if arr.shape != (len(self.dimensions),):
            raise ValueError(
                f"Raw vector must have shape ({len(self.dimensions)},); got {arr.shape}"
            )
        return (arr - self.shelf_mean) / self.shelf_std, 1.0, []

    def distance_to_author(
        self,
        vector: Optional[np.ndarray],
        slug: str,
        method: str = "euclidean",
        *,
        mfw_z: Optional[np.ndarray] = None,
    ) -> float:
        """Distance from a normalized vector to an author centroid.

        ``method='euclidean'`` means the active calibrated distance (the
        space's ``distance_variant``); variants that include the MFW block
        additionally need ``mfw_z``. ``method='mahalanobis'`` is a secondary
        d18-only diagnostic (always on the d18 block, never blended).
        """
        entry = self.authors.get(slug) or self.reference_authors.get(slug)
        if entry is None:
            raise KeyError(f"Unknown author: {slug}")
        if method == "euclidean":
            if self.distance_variant in MFW_VARIANTS:
                if mfw_z is None:
                    raise ValueError(
                        f"Distance variant {self.distance_variant!r} requires "
                        "an MFW z-vector (featurize raw text via the MFW block)"
                    )
                if entry.mfw_centroid is None:
                    raise ValueError(
                        f"Author {slug} has no MFW centroid in this space"
                    )
            return self.work_distance(vector, mfw_z, entry.centroid, entry.mfw_centroid)
        if method == "mahalanobis":
            if vector is None:
                raise ValueError("mahalanobis requires a d18 feature vector")
            delta = vector - entry.centroid
            return float(np.sqrt(max(float(delta @ entry.cov_pinv() @ delta), 0.0)))
        raise ValueError(f"Unknown distance method: {method}")

    def place(
        self,
        vector_or_baseline: Optional[
            Union[Mapping[str, Any], Sequence[float], np.ndarray, str, Path]
        ] = None,
        *,
        text: Optional[str] = None,
        method: str = "euclidean",
        include_reference: bool = False,
    ) -> PlacementResult:
        """Place a work into the space.

        Accepts a baseline JSON dict (or ``.json`` path), a dim->value
        mapping, or a raw-value vector ordered as ``self.dimensions``. When
        the MFW block is active (``mfw_delta`` / ``combined`` variants), raw
        text is also required: pass ``text=...`` or give a ``.txt`` path as
        the positional argument (its full contents are featurized against the
        stored MFW vocabulary). ``mfw_delta`` placements may be text-only;
        baseline-JSON-only input raises a clear error when the active variant
        needs text.

        W/B percentiles compare the work->centroid distance against the
        matching calibration families: W uses the leave-one-out family
        (work vs own-author centroid) and B uses the work-to-other-author-
        centroid family — both are work->centroid distances under the active
        variant, so the comparison is apples-to-apples. Percentiles are only
        calibrated for the primary (euclidean/active-variant) method;
        mahalanobis placements return d18-only distances without percentiles.
        """
        needs_mfw = self.distance_variant in MFW_VARIANTS
        needs_d18 = self.distance_variant in D18_VARIANTS or method == "mahalanobis"

        obj = vector_or_baseline
        if isinstance(obj, (str, Path)) and str(obj).lower().endswith(".txt"):
            if text is not None:
                raise ValueError("Pass either a .txt path or text=, not both")
            text = Path(obj).read_text(encoding="utf-8")
            obj = None

        mfw_z: Optional[np.ndarray] = None
        if text is not None and self.mfw is not None:
            mfw_z = self.mfw.featurize_text(text)
        if needs_mfw and mfw_z is None:
            raise ValueError(
                f"Distance variant {self.distance_variant!r} requires raw text "
                "to featurize the MFW block: pass text=... or a .txt path "
                "(baseline JSON alone is only sufficient for the 'd18' / "
                "'d18_weighted' variants)"
            )

        if obj is not None:
            vector, coverage, imputed = self._coerce_vector(obj)
        elif needs_d18:
            raise ValueError(
                f"Distance variant {self.distance_variant!r} requires baseline "
                "features (d18 dimensions); raw text alone is only sufficient "
                "for the 'mfw_delta' variant"
            )
        else:
            vector, coverage, imputed = None, 1.0, []

        w_dist = self.within.get("loo")
        b_dist = self.between.get("work_to_centroid")

        entries: List[Tuple[str, AuthorEntry]] = list(self.authors.items())
        if include_reference:
            entries += list(self.reference_authors.items())

        placements: List[AuthorPlacement] = []
        for slug, entry in entries:
            distance = self.distance_to_author(vector, slug, method=method, mfw_z=mfw_z)
            w_pct = b_pct = None
            if method == "euclidean":
                w_pct = w_dist.percentile_of(distance) if w_dist else None
                b_pct = b_dist.percentile_of(distance) if b_dist else None
            placements.append(
                AuthorPlacement(
                    author=slug,
                    distance=distance,
                    w_percentile=w_pct,
                    b_percentile=b_pct,
                    statement=self._statement(slug, distance, w_pct, b_pct, entry),
                    reference_only=entry.reference_only,
                    singleton=entry.singleton,
                )
            )
        placements.sort(key=lambda p: p.distance)
        return PlacementResult(
            method=method,
            placements=placements,
            coverage=coverage,
            imputed_dims=imputed,
            dimensions=list(self.dimensions),
        )

    @staticmethod
    def _statement(
        slug: str,
        distance: float,
        w_pct: Optional[float],
        b_pct: Optional[float],
        entry: AuthorEntry,
    ) -> str:
        """Plain-language calibration statement for one author distance."""
        parts = [f"distance to {slug} is {distance:.2f}"]
        if w_pct is not None:
            parts.append(f"at p{w_pct:.0f} of within-author variation")
        if b_pct is not None:
            parts.append(f"at p{b_pct:.0f} of between-author separation")
        caveats = []
        if entry.singleton:
            caveats.append("singleton centroid")
        if entry.reference_only:
            caveats.append("reference-only, uncalibrated")
        statement = ", ".join(parts)
        if caveats:
            statement += f" ({'; '.join(caveats)})"
        return statement

    def pairwise_author_matrix(self, method: str = "euclidean") -> Dict[str, Dict[str, float]]:
        """Symmetric centroid-to-centroid distance matrix (calibrated authors).

        ``method='euclidean'`` uses the active calibrated distance variant
        (identical to the historical plain d18 euclidean for ``d18`` spaces).
        """
        if method != "euclidean":
            raise ValueError("pairwise_author_matrix supports euclidean only")
        slugs = sorted(self.authors.keys())
        matrix: Dict[str, Dict[str, float]] = {s: {} for s in slugs}
        for i, slug_a in enumerate(slugs):
            entry_a = self.authors[slug_a]
            matrix[slug_a][slug_a] = 0.0
            for slug_b in slugs[i + 1:]:
                entry_b = self.authors[slug_b]
                dist = self.work_distance(
                    entry_a.centroid, entry_a.mfw_centroid,
                    entry_b.centroid, entry_b.mfw_centroid,
                )
                matrix[slug_a][slug_b] = dist
                matrix[slug_b][slug_a] = dist
        return matrix

    # -- serialization -------------------------------------------------------

    def _author_to_dict(self, entry: AuthorEntry) -> Dict[str, Any]:
        def work_dict(w: WorkRecord) -> Dict[str, Any]:
            data: Dict[str, Any] = {
                "title": w.title,
                "path": w.path,
                "vector": [float(v) for v in w.vector],
                "raw": w.raw,
                "word_count": w.word_count,
                "form": w.form,
                "translator": w.translator,
                "coverage": w.coverage,
                "imputed_dims": w.imputed_dims,
            }
            if w.text_path is not None:
                data["text_path"] = w.text_path
                data["body_start"] = w.body_start
                data["body_end"] = w.body_end
            if w.mfw_z is not None:
                data["mfw_z"] = [float(v) for v in w.mfw_z]
            return data

        data = {
            "centroid": [float(v) for v in entry.centroid],
            "covariance": [[float(v) for v in row] for row in entry.covariance],
            "covariance_kind": entry.covariance_kind,
            "work_count": entry.work_count,
            "works": [work_dict(w) for w in entry.works],
            "flags": entry.flags(),
            "forms": entry.forms,
            "translators": entry.translators,
        }
        if entry.mfw_centroid is not None:
            data["mfw_centroid"] = [float(v) for v in entry.mfw_centroid]
        return data

    @staticmethod
    def _author_from_dict(slug: str, data: Mapping[str, Any]) -> AuthorEntry:
        works = [
            WorkRecord(
                author=slug,
                title=w["title"],
                path=w["path"],
                raw={k: (float(v) if v is not None else None) for k, v in (w.get("raw") or {}).items()},
                word_count=w.get("word_count"),
                form=w.get("form"),
                translator=w.get("translator"),
                text_path=w.get("text_path"),
                body_start=w.get("body_start"),
                body_end=w.get("body_end"),
                vector=np.asarray(w["vector"], dtype=float),
                mfw_z=(
                    np.asarray(w["mfw_z"], dtype=float)
                    if w.get("mfw_z") is not None else None
                ),
                coverage=float(w.get("coverage", 1.0)),
                imputed_dims=list(w.get("imputed_dims", [])),
            )
            for w in data.get("works", [])
        ]
        flags = data.get("flags") or {}
        return AuthorEntry(
            slug=slug,
            centroid=np.asarray(data["centroid"], dtype=float),
            covariance=np.asarray(data["covariance"], dtype=float),
            covariance_kind=data.get("covariance_kind", "diagonal"),
            work_count=int(data.get("work_count", len(works))),
            works=works,
            singleton=bool(flags.get("singleton", False)),
            reference_only=bool(flags.get("reference_only", False)),
            forms=list(data.get("forms", [])),
            translators=list(data.get("translators", [])),
            mfw_centroid=(
                np.asarray(data["mfw_centroid"], dtype=float)
                if data.get("mfw_centroid") is not None else None
            ),
        )

    def to_artifact(self, path: Optional[Path] = None) -> Dict[str, Any]:
        """Serialize to the artifact dict; write JSON when path is given."""
        artifact: Dict[str, Any] = {
            "meta": self.meta,
            "dimensions": list(self.dimensions),
            "shelf_norm": {
                dim: {"mean": float(self.shelf_mean[i]), "std": float(self.shelf_std[i])}
                for i, dim in enumerate(self.dimensions)
            },
            "authors": {slug: self._author_to_dict(e) for slug, e in self.authors.items()},
            "reference_authors": {
                slug: self._author_to_dict(e) for slug, e in self.reference_authors.items()
            },
            "distance_matrix": self.pairwise_author_matrix(),
            "within_author_dist": {k: v.to_dict() for k, v in self.within.items()},
            "between_author_dist": {k: v.to_dict() for k, v in self.between.items()},
        }
        # MFW feature block + blend config (ADR-0041 amendment). Artifacts
        # without these keys load as D18-only spaces (backward compatible).
        feature_blocks: Dict[str, Any] = {
            "d18": {
                "n_dims": len(self.dimensions),
                "dimension_set_version": self.meta.get(
                    "dimension_set_version", DIMENSION_SET_VERSION
                ),
            },
        }
        if self.mfw is not None:
            feature_blocks["mfw_delta"] = self.mfw.to_dict()
            artifact["blend"] = {
                "alpha": self.alpha,
                **(self.blend or {}),
            }
        artifact["feature_blocks"] = feature_blocks
        artifact["distance_variant"] = self.distance_variant
        if self.dimension_weights:
            artifact["dimension_weights"] = {
                k: float(v) for k, v in self.dimension_weights.items()
            }
        if path is not None:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(artifact, handle, indent=1)
            logger.info("Wrote author-space artifact: %s", path)
        return artifact

    @classmethod
    def from_artifact(cls, source: Union[str, Path, Mapping[str, Any]]) -> "AuthorRelativeSpace":
        """Load a space from an artifact JSON path (or already-loaded dict)."""
        if isinstance(source, (str, Path)):
            with open(source, "r", encoding="utf-8") as handle:
                artifact = json.load(handle)
        else:
            artifact = dict(source)
        dims = list(artifact["dimensions"])
        shelf_norm = artifact["shelf_norm"]
        shelf_mean = np.array([shelf_norm[d]["mean"] for d in dims], dtype=float)
        shelf_std = np.array([shelf_norm[d]["std"] for d in dims], dtype=float)

        # MFW block + blend (absent in pre-1.1.0 artifacts -> D18-only space).
        feature_blocks = artifact.get("feature_blocks") or {}
        mfw = (
            MFWBlock.from_dict(feature_blocks["mfw_delta"])
            if "mfw_delta" in feature_blocks else None
        )
        meta = dict(artifact.get("meta", {}))
        distance_variant = (
            artifact.get("distance_variant")
            or meta.get("distance_variant")
            or "d18"
        )
        blend_raw = dict(artifact.get("blend") or {})
        alpha = float(blend_raw.pop("alpha", meta.get("alpha", 0.5)))
        return cls(
            dimensions=dims,
            shelf_mean=shelf_mean,
            shelf_std=shelf_std,
            authors={
                slug: cls._author_from_dict(slug, data)
                for slug, data in artifact.get("authors", {}).items()
            },
            reference_authors={
                slug: cls._author_from_dict(slug, data)
                for slug, data in artifact.get("reference_authors", {}).items()
            },
            within={
                k: DistributionSummary.from_dict(v)
                for k, v in artifact.get("within_author_dist", {}).items()
            },
            between={
                k: DistributionSummary.from_dict(v)
                for k, v in artifact.get("between_author_dist", {}).items()
            },
            meta=meta,
            mfw=mfw,
            distance_variant=distance_variant,
            alpha=alpha,
            dimension_weights=artifact.get("dimension_weights"),
            blend=blend_raw or None,
        )


# ---------------------------------------------------------------------------
# Length-matched per-author envelopes (LM-W) — red-team K1 remediation
# ---------------------------------------------------------------------------
#
# The full-novel W LOO distribution is not a valid entry criterion for
# ~3,000-word texts: Burrows Delta inflates at sample length, so the target
# authors' OWN windows cannot satisfy a full-novel-calibrated threshold
# (docs/redteam/RED_TEAM_SYNTHESIS.md K1 and redteam_claims_attack.md §1 —
# Austen 0/74 against her own W-p90). The LM envelope is the length-matched
# replacement:
# for each calibrated author, slice each work's body text into
# non-overlapping windows at a fixed token length, featurize each window
# against the artifact's MFW block, and take the distribution of
# window -> author-centroid Burrows-Delta distances where the centroid
# EXCLUDES the window's own work (leave-one-work-out — no self-inflation).
#
# E8 (the permanent same-author positive control) is built on the same
# construction: an author's own held-out windows must enter their own LM
# envelope at ~the nominal rate, otherwise the criterion is a length
# detector, not an authorship envelope.


def sha256_of_file(path: Union[str, Path]) -> str:
    """SHA-256 hex digest of a file's bytes (artifact provenance pinning)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_record_text_path(
    record: WorkRecord, text_root: Optional[Union[str, Path]] = None
) -> Optional[Path]:
    """Resolve a record's ``text_path``: as-is, then relative to ``text_root``.

    Artifacts persist repo-root-relative text paths; consumers loading an
    artifact from elsewhere pass the repo root (or another base) as
    ``text_root``.
    """
    if not record.text_path:
        return None
    path = Path(record.text_path)
    if path.is_file():
        return path
    if not path.is_absolute() and text_root is not None:
        candidate = Path(text_root) / path
        if candidate.is_file():
            return candidate
    return None


def record_body_tokens(
    record: WorkRecord, text_root: Optional[Union[str, Path]] = None
) -> Optional[List[str]]:
    """MFW tokens of a record's body text.

    Uses the transient ``body_text`` override when present, else the
    manifest body slice (``text_path`` + character offsets). Returns None
    when no text is resolvable (caller decides whether that is an error).
    """
    if record.body_text is not None:
        return mfw_tokenize(record.body_text)
    path = resolve_record_text_path(record, text_root)
    if path is None:
        return None
    text = path.read_text(encoding="utf-8")
    start = record.body_start or 0
    end = record.body_end if record.body_end is not None else len(text)
    return mfw_tokenize(text[start:end])


@dataclass
class AuthorLMEnvelope:
    """One author's length-matched window-distance envelope.

    ``windows`` carries per-window provenance: work index/title, window
    index within the work, and the window's Burrows-Delta distance to the
    author's leave-one-work-out centroid. Quantiles are np.percentile
    (linear interpolation) over all window distances at
    :data:`LM_QUANTILE_LEVELS`.
    """

    author: str
    n_works: int
    works_used: List[str]
    windows: List[Dict[str, Any]]      # {work_index, work, window, distance}
    quantiles: Dict[str, float]        # "p50"/"p90"/"p95"/"p99"

    _sorted: Optional[np.ndarray] = field(default=None, repr=False, compare=False)

    @property
    def n_windows(self) -> int:
        return len(self.windows)

    def distances(self) -> np.ndarray:
        """Sorted window distances (cached)."""
        if self._sorted is None:
            self._sorted = np.sort(
                np.asarray([w["distance"] for w in self.windows], dtype=float)
            )
        return self._sorted

    def percentile_of(self, distance: float) -> Optional[float]:
        """Mid-rank empirical percentile of a distance against the envelope."""
        arr = self.distances()
        if arr.size == 0:
            return None
        below = int(np.searchsorted(arr, distance, side="left"))
        upper = int(np.searchsorted(arr, distance, side="right"))
        return float(100.0 * (below + 0.5 * (upper - below)) / arr.size)

    def entered(self, distance: float, level: int = 90) -> bool:
        """Is ``distance`` inside the envelope's p``level`` threshold?"""
        return bool(distance <= self.quantiles[f"p{level}"])

    def held_out_entry(self, level: int = 90) -> Dict[str, Any]:
        """E8 positive control: leave-WORK-out entry of the author's own windows.

        For each work, the threshold is the p``level`` of the OTHER works'
        window distances (whose own distances already exclude their own work
        from the centroid — work-level LOO throughout). Comparing each
        window against the quantile of the full distribution including
        itself would be circular (~nominal rate by construction); this is
        the genuine held-out check.
        """
        by_work: Dict[int, List[float]] = {}
        titles: Dict[int, str] = {}
        for w in self.windows:
            by_work.setdefault(int(w["work_index"]), []).append(float(w["distance"]))
            titles[int(w["work_index"])] = str(w["work"])
        per_work: List[Dict[str, Any]] = []
        inside_total = 0
        n_total = 0
        for idx in sorted(by_work):
            others = [
                d for j, ds in by_work.items() if j != idx for d in ds
            ]
            if not others:
                continue
            threshold = float(np.percentile(others, level))
            own = by_work[idx]
            inside = int(sum(d <= threshold for d in own))
            per_work.append({
                "work_index": idx,
                "work": titles[idx],
                "n_windows": len(own),
                "threshold": threshold,
                "inside": inside,
            })
            inside_total += inside
            n_total += len(own)
        return {
            "level": level,
            "n": n_total,
            "inside": inside_total,
            "rate": (inside_total / n_total) if n_total else None,
            "per_work": per_work,
        }

    def bootstrap_quantile_ci(
        self,
        level: int,
        n_bootstrap: int = 2000,
        seed: int = 20260609,
        alpha: float = 0.05,
    ) -> Tuple[float, float]:
        """Bootstrap CI on the envelope's p``level`` threshold itself.

        Resamples envelope windows with replacement (K9: entry claims must
        carry threshold-estimation uncertainty). Note the windows cluster
        within works, so this CI is mildly anti-conservative; the E8
        leave-work-out gate is the structural complement.
        """
        arr = self.distances()
        if arr.size < 2:
            value = self.quantiles[f"p{level}"]
            return (value, value)
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, arr.size, size=(n_bootstrap, arr.size))
        boot = np.percentile(arr[idx], level, axis=1)
        lo, hi = np.percentile(boot, [100 * alpha / 2, 100 * (1 - alpha / 2)])
        return (float(lo), float(hi))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_works": self.n_works,
            "works_used": list(self.works_used),
            "n_windows": self.n_windows,
            "quantiles": {k: float(v) for k, v in self.quantiles.items()},
            "windows": [
                {
                    "work_index": int(w["work_index"]),
                    "work": str(w["work"]),
                    "window": int(w["window"]),
                    "distance": float(w["distance"]),
                }
                for w in self.windows
            ],
        }

    @classmethod
    def from_dict(cls, author: str, data: Mapping[str, Any]) -> "AuthorLMEnvelope":
        return cls(
            author=author,
            n_works=int(data["n_works"]),
            works_used=list(data.get("works_used", [])),
            windows=[dict(w) for w in data.get("windows", [])],
            quantiles={k: float(v) for k, v in data.get("quantiles", {}).items()},
        )


class LengthMatchedEnvelopes:
    """Per-author length-matched (LM-W) envelope collection.

    Build with :meth:`build_from_space` from an MFW-Delta
    :class:`AuthorRelativeSpace`, persist with :meth:`to_artifact`, reload
    with :meth:`from_artifact`. The envelope distance is Burrows Delta on
    the space's persisted MFW block — the same featurization used by
    ``place()`` for the ``mfw_delta`` variant — so a sample's distance to a
    target centroid is directly comparable to the target's envelope.
    """

    def __init__(self, *, authors: Dict[str, AuthorLMEnvelope], meta: Dict[str, Any]):
        self.authors = authors
        self.meta = meta

    @property
    def window_words(self) -> int:
        return int(self.meta["window_words"])

    def quantile(self, author: str, level: int = 90) -> float:
        return self.authors[author].quantiles[f"p{level}"]

    def held_out_entry_rates(self, level: int = 90) -> Dict[str, Dict[str, Any]]:
        """E8 per-author leave-work-out entry rates (see AuthorLMEnvelope)."""
        return {
            slug: env.held_out_entry(level)
            for slug, env in sorted(self.authors.items())
        }

    @classmethod
    def build_from_space(
        cls,
        space: AuthorRelativeSpace,
        *,
        window_words: int = LM_DEFAULT_WINDOW_WORDS,
        seed: int = 20260609,
        max_windows_per_work: Optional[int] = None,
        text_root: Optional[Union[str, Path]] = None,
        source_artifact: Optional[Union[str, Path]] = None,
        generated: Optional[str] = None,
    ) -> "LengthMatchedEnvelopes":
        """Build LM envelopes from a calibrated space.

        Per calibrated author: each work's body text (``body_text`` override
        or manifest slice via ``text_path`` + offsets, relative paths
        resolved against ``text_root``) is MFW-tokenized and cut into
        non-overlapping ``window_words``-token windows (trailing partial
        dropped). Each window is z-scored against the space's MFW norm and
        its Burrows-Delta distance taken to the author's leave-one-WORK-out
        centroid (mean of the OTHER works' whole-work z-vectors — the
        window's own work never contributes to its centroid).

        Requires ``distance_variant == "mfw_delta"``: the envelope must live
        on the same scale as ``place()`` distances, and raw-text windows can
        only be featurized through the MFW block (d18 features need the full
        baseline pipeline).

        ``max_windows_per_work`` caps windows per work by seeded sampling
        without replacement (sorted, deterministic); default None keeps all.
        """
        if space.mfw is None:
            raise ValueError("LM envelopes require the MFW block")
        if space.distance_variant != "mfw_delta":
            raise ValueError(
                "LM envelopes are only defined for distance_variant='mfw_delta' "
                f"(got {space.distance_variant!r}): envelope distances must be "
                "on the same scale as place() distances, and raw-text windows "
                "can only be featurized via the MFW block"
            )
        if window_words < 1:
            raise ValueError(f"window_words must be >= 1 (got {window_words})")
        rng = np.random.default_rng(seed)

        authors: Dict[str, AuthorLMEnvelope] = {}
        skipped_authors: List[str] = []
        works_without_text: List[str] = []
        works_too_short: List[str] = []
        for slug in sorted(space.authors):
            entry = space.authors[slug]
            works = [w for w in entry.works if w.mfw_z is not None]
            if len(works) < 2:
                skipped_authors.append(slug)
                logger.warning(
                    "LM envelopes: skipping %s (< 2 works with MFW vectors)", slug
                )
                continue
            mfw_matrix = np.vstack([w.mfw_z for w in works])
            total = mfw_matrix.sum(axis=0)
            n_works = mfw_matrix.shape[0]
            windows: List[Dict[str, Any]] = []
            works_used: List[str] = []
            for idx, work in enumerate(works):
                tokens = record_body_tokens(work, text_root=text_root)
                if tokens is None:
                    works_without_text.append(f"{slug}/{work.title}")
                    continue
                n_win = len(tokens) // window_words
                if n_win == 0:
                    works_too_short.append(f"{slug}/{work.title}")
                    continue
                chosen = np.arange(n_win)
                if max_windows_per_work and n_win > max_windows_per_work:
                    chosen = np.sort(
                        rng.choice(n_win, size=max_windows_per_work, replace=False)
                    )
                # Leave-one-WORK-out centroid: own work excluded.
                loo_centroid = (total - mfw_matrix[idx]) / (n_works - 1)
                works_used.append(work.title)
                for w_i in chosen:
                    chunk = tokens[w_i * window_words:(w_i + 1) * window_words]
                    z = space.mfw.featurize_tokens(chunk)
                    windows.append({
                        "work_index": int(idx),
                        "work": work.title,
                        "window": int(w_i),
                        "distance": float(MFWBlock.delta(z, loo_centroid)),
                    })
            if not windows:
                skipped_authors.append(slug)
                logger.warning("LM envelopes: no windows for %s", slug)
                continue
            dists = np.asarray([w["distance"] for w in windows], dtype=float)
            quantiles = {
                f"p{q}": float(np.percentile(dists, q)) for q in LM_QUANTILE_LEVELS
            }
            authors[slug] = AuthorLMEnvelope(
                author=slug,
                n_works=len(works_used),
                works_used=works_used,
                windows=windows,
                quantiles=quantiles,
            )

        artifact_path = Path(source_artifact) if source_artifact else None
        meta = {
            "version": LM_ENVELOPE_VERSION,
            "generated": generated,
            "window_words": int(window_words),
            "window_unit": "mfw_tokens",
            "seed": int(seed),
            "max_windows_per_work": max_windows_per_work,
            "loo": "work_level (window's own work excluded from its centroid)",
            "distance_variant": space.distance_variant,
            "n_mfw": space.mfw.n_mfw,
            "tokenizer": space.mfw.tokenizer,
            "vocab_filter": space.mfw.vocab_filter,
            "quantile_levels": list(LM_QUANTILE_LEVELS),
            "source_artifact": str(artifact_path) if artifact_path else None,
            "source_artifact_sha256": (
                sha256_of_file(artifact_path)
                if artifact_path and artifact_path.is_file() else None
            ),
            "n_authors": len(authors),
            "skipped_authors": skipped_authors,
            "works_without_text": works_without_text,
            "works_too_short": works_too_short,
        }
        return cls(authors=authors, meta=meta)

    def to_artifact(self, path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Serialize; write JSON sidecar when ``path`` is given."""
        artifact = {
            "meta": dict(self.meta),
            "authors": {
                slug: env.to_dict() for slug, env in sorted(self.authors.items())
            },
        }
        if path is not None:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(artifact, handle, indent=1)
            logger.info("Wrote LM envelope artifact: %s", path)
        return artifact

    @classmethod
    def from_artifact(
        cls, source: Union[str, Path, Mapping[str, Any]]
    ) -> "LengthMatchedEnvelopes":
        if isinstance(source, (str, Path)):
            with open(source, "r", encoding="utf-8") as handle:
                artifact = json.load(handle)
        else:
            artifact = dict(source)
        return cls(
            authors={
                slug: AuthorLMEnvelope.from_dict(slug, data)
                for slug, data in artifact.get("authors", {}).items()
            },
            meta=dict(artifact.get("meta", {})),
        )


# ---------------------------------------------------------------------------
# Cluster-robust inference helpers (red-team K4: ICC / design effect)
# ---------------------------------------------------------------------------

def anova_icc(values: Sequence[float], clusters: Sequence[Any]) -> float:
    """One-way random-effects ICC(1), ANOVA estimator, clipped to [0, 1].

    Standard one-way ANOVA decomposition (Donner 1986 convention for
    unequal cluster sizes):

        MSB = SSB / (K - 1),  MSW = SSW / (N - K)
        k0  = (N - sum(n_i^2) / N) / (K - 1)
        ICC = (MSB - MSW) / (MSB + (k0 - 1) * MSW)

    Works for binary indicators too (the ANOVA estimator on 0/1 data is the
    standard cluster-randomized-trial ICC). Degenerate inputs (fewer than 2
    clusters, all singleton clusters, zero total variance) return 0.0.
    """
    y = np.asarray(values, dtype=float)
    labels = np.asarray(clusters)
    if y.size != labels.size:
        raise ValueError("values and clusters must have equal length")
    n_total = y.size
    uniq = {}
    for value, label in zip(y, labels):
        uniq.setdefault(label, []).append(value)
    k = len(uniq)
    if k < 2 or n_total <= k:
        return 0.0
    grand = float(y.mean())
    ssb = ssw = 0.0
    sum_sq_sizes = 0.0
    for members in uniq.values():
        arr = np.asarray(members, dtype=float)
        ssb += arr.size * (arr.mean() - grand) ** 2
        ssw += float(((arr - arr.mean()) ** 2).sum())
        sum_sq_sizes += arr.size ** 2
    msb = ssb / (k - 1)
    msw = ssw / (n_total - k)
    k0 = (n_total - sum_sq_sizes / n_total) / (k - 1)
    denom = msb + (k0 - 1) * msw
    if denom <= 0:
        return 0.0
    return float(np.clip((msb - msw) / denom, 0.0, 1.0))


def design_effect(values: Sequence[float], clusters: Sequence[Any]) -> Dict[str, float]:
    """Cluster design effect for a mean/proportion estimated from clustered data.

    DEFF = 1 + (m_bar - 1) * ICC with m_bar = N / K (mean cluster size);
    effective sample size n_eff = N / DEFF. Returns the full accounting so
    reports can show their work:
    {icc, n, n_clusters, mean_cluster_size, design_effect, n_eff}.
    """
    y = np.asarray(values, dtype=float)
    labels = np.asarray(clusters)
    icc = anova_icc(y, labels)
    n_total = int(y.size)
    k = len(set(labels.tolist()))
    m_bar = n_total / k if k else float("nan")
    deff = 1.0 + (m_bar - 1.0) * icc if k else float("nan")
    deff = max(deff, 1.0)
    return {
        "icc": icc,
        "n": n_total,
        "n_clusters": k,
        "mean_cluster_size": float(m_bar),
        "design_effect": float(deff),
        "n_eff": float(n_total / deff) if deff else float("nan"),
    }
