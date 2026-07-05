"""
Tests for the MFW vocabulary filter (issue #95 P3 / paper outline C1).

The function-words-only filter is a topic-confound control: it restricts the
Burrows-Delta MFW candidate vocabulary to a closed-class stylometric
function-word list BEFORE top-N selection, so the Delta block carries no
content/topic signal. Filter choice must persist through the artifact.
"""

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pytest

from author_manifold.author_space import (
    AuthorRelativeSpace,
    DIMENSION_SET_V1,
    MFWBlock,
    MFW_VOCAB_FILTERS,
    STYLOMETRIC_FUNCTION_WORDS,
    WorkRecord,
    work_record_from_baseline,
)

SEED = 20260609


def _make_baseline(values: Dict[str, float], title: str) -> Dict:
    return {
        "document": {"word_count": 50000, "metadata": {"title": title}},
        "pipeline": {"version": "synthetic"},
        "d18_profile": dict(values),
        "style_features": {},
    }


# Content words that will be MORE frequent than some function words in the
# synthetic shelf — the filter must still exclude them from the vocabulary.
_CONTENT = ["river", "stone", "ledger", "office", "orchid", "violin"]
_FUNCTION = ["the", "and", "of", "a", "to", "in", "was", "it", "not", "but"]


def _author_text(rng: np.random.Generator, author: int, n: int = 800) -> str:
    # Content words deliberately dominate: 8 copies vs 3 of function words.
    pool = _FUNCTION * 3 + [_CONTENT[author % len(_CONTENT)]] * 80 + _CONTENT * 8
    return " ".join(rng.choice(pool, size=n))


def _records(seed: int = SEED) -> List[WorkRecord]:
    rng = np.random.default_rng(seed)
    records: List[WorkRecord] = []
    for a in range(3):
        center = rng.normal(0.0, 3.0, size=len(DIMENSION_SET_V1))
        for w in range(4):
            values = center + rng.normal(0.0, 0.1, size=len(DIMENSION_SET_V1))
            baseline = _make_baseline(dict(zip(DIMENSION_SET_V1, values)), f"a{a}-w{w}")
            record = work_record_from_baseline(
                baseline,
                author=f"author-{a}",
                path=f"synthetic/author-{a}/w{w}_baseline.json",
                dimensions=DIMENSION_SET_V1,
            )
            record.body_text = _author_text(rng, a)
            records.append(record)
    return records


def _build(vocab_filter: str, mfw_n: int = 12) -> AuthorRelativeSpace:
    return AuthorRelativeSpace.build(
        _records(),
        min_works=3,
        seed=SEED,
        mfw_n=mfw_n,
        distance_variant="mfw_delta",
        mfw_vocab_filter=vocab_filter,
        generated="2026-06-09T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# The function-word list itself
# ---------------------------------------------------------------------------

def test_function_word_list_is_closed_class():
    # Plausible size for a stylometric function-word list.
    assert 250 <= len(STYLOMETRIC_FUNCTION_WORDS) <= 450
    # All lowercase, tokenizer-compatible (letters + ASCII apostrophe only).
    for word in STYLOMETRIC_FUNCTION_WORDS:
        assert word == word.lower()
        assert all(c.isalpha() or c == "'" for c in word), word
    # Core closed-class members present.
    for word in ["the", "of", "and", "to", "she", "him", "between", "would",
                 "not", "very", "don't", "didn", "dont", "s", "t"]:
        assert word in STYLOMETRIC_FUNCTION_WORDS, word
    # Open-class content words absent (incl. the classic MFW leakers).
    for word in ["said", "man", "eyes", "house", "water", "father", "time",
                 "room", "looked", "mr", "tengo", "river", "ledger"]:
        assert word not in STYLOMETRIC_FUNCTION_WORDS, word


# ---------------------------------------------------------------------------
# Build-time filtering
# ---------------------------------------------------------------------------

def test_filter_applies_before_top_n_selection():
    unfiltered = _build("none")
    filtered = _build("function_words_only")

    # Without the filter, the dominant content words win top-N slots.
    assert any(w in _CONTENT for w in unfiltered.mfw.vocabulary)
    # With the filter, the vocabulary is pure closed-class — even though the
    # content words are far more frequent on this shelf (i.e. selection
    # happened AFTER filtering, not by post-hoc removal from the top-N).
    assert all(w in STYLOMETRIC_FUNCTION_WORDS for w in filtered.mfw.vocabulary)
    assert not set(filtered.mfw.vocabulary) & set(_CONTENT)
    # Top-N still honored: shelf has 10 distinct function words < requested 12.
    assert filtered.mfw.n_mfw == len(set(_FUNCTION))
    assert set(filtered.mfw.vocabulary) == set(_FUNCTION)


def test_filter_default_is_none_and_unfiltered_build_unchanged():
    default_build = AuthorRelativeSpace.build(
        _records(), min_works=3, seed=SEED, mfw_n=12,
        distance_variant="mfw_delta",
    )
    explicit_none = _build("none")
    assert default_build.mfw.vocab_filter == "none"
    assert default_build.mfw.vocabulary == explicit_none.mfw.vocabulary
    assert np.array_equal(default_build.mfw.mean, explicit_none.mfw.mean)


def test_unknown_filter_rejected():
    with pytest.raises(ValueError, match="vocab filter"):
        _build("stopwords")
    assert "none" in MFW_VOCAB_FILTERS
    assert "function_words_only" in MFW_VOCAB_FILTERS


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_filter_persisted_in_artifact_and_round_trips(tmp_path: Path):
    space = _build("function_words_only")
    assert space.meta["feature_blocks"]["mfw_delta"]["vocab_filter"] == \
        "function_words_only"
    assert space.meta["distance_method"].endswith("_fwonly")

    path = tmp_path / "fwonly_space.json"
    space.to_artifact(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["feature_blocks"]["mfw_delta"]["vocab_filter"] == \
        "function_words_only"

    loaded = AuthorRelativeSpace.from_artifact(path)
    assert loaded.mfw.vocab_filter == "function_words_only"
    assert loaded.mfw.vocabulary == space.mfw.vocabulary
    # Placement identical through the round trip.
    text = " ".join(_FUNCTION * 10 + ["river"] * 30)
    before = space.place(text=text)
    after = loaded.place(text=text)
    assert [p.author for p in before.placements] == \
        [p.author for p in after.placements]
    assert [p.distance for p in before.placements] == \
        pytest.approx([p.distance for p in after.placements])


def test_pre_filter_artifacts_load_as_none():
    # MFWBlock dicts written before the filter existed have no vocab_filter
    # key; they must load with vocab_filter="none" (backward compatible).
    block = MFWBlock.from_dict({
        "vocabulary": ["the", "and"],
        "mean": [100.0, 50.0],
        "std": [10.0, 5.0],
    })
    assert block.vocab_filter == "none"


def test_filtered_delta_ignores_content_vocabulary():
    """Same function-word profile + different topics => Delta ~ 0."""
    space = _build("function_words_only")
    rng = np.random.default_rng(SEED + 1)
    base = list(rng.choice(_FUNCTION, size=2000))
    text_topic_a = " ".join(base + ["river"] * 400)
    text_topic_b = " ".join(base + ["ledger"] * 400)
    z_a = space.mfw.featurize_text(text_topic_a)
    z_b = space.mfw.featurize_text(text_topic_b)
    # Identical function-word counts, but different token totals (length
    # normalization) — the topic words affect Delta only through length.
    assert MFWBlock.delta(z_a, z_b) == pytest.approx(0.0, abs=1e-12)
