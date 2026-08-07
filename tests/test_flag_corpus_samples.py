"""Tests for the corpus flag sidecar's published cross-check.

The cross-check exists to catch a sidecar that disagrees with the
published completion-compliance table. It used to iterate the sidecar's
models and compare each against the table, which meant a sidecar with no
completion samples at all -- a renamed condition, a partial run -- ran an
empty loop, counted zero failures, and printed PASS. These tests pin that
an empty or incomplete comparison set is itself a failure.

Added after the cross-family review of 2026-08-07 (finding F4).
"""

from collections import Counter

import pytest

from flag_corpus_samples import (
    EXPECTED_COMPLETION_MODELS,
    EXPECTED_COMPLETION_SAMPLES,
    check_against_published,
)


def sidecar_from_published(table, drop=(), extra=None):
    """Build a minimal sidecar that reproduces a published table exactly."""
    samples = {}
    counter = 0
    for model, row in table.items():
        if model in drop:
            continue
        slug = model.replace(":", "_").replace(".", "_")
        for length_class, n in (("compliant", row["compliant"]),
                                ("sub_floor", row["subfloor"]),
                                ("below_hard_floor", row["refused"])):
            for _ in range(n):
                counter += 1
                samples[f"s{counter}"] = {
                    "condition": "completion",
                    "model_slug": slug,
                    "length_class": length_class,
                }
    if extra:
        for slug, n in extra.items():
            for _ in range(n):
                counter += 1
                samples[f"s{counter}"] = {
                    "condition": "completion",
                    "model_slug": slug,
                    "length_class": "compliant",
                }
    return {"samples": samples}


@pytest.fixture(scope="module")
def published_table():
    import json
    from pathlib import Path
    path = (Path(__file__).resolve().parents[1]
            / "reports/validation/author_space/results2"
            / "completion_results.json")
    return json.loads(path.read_text(encoding="utf-8"))["compliance_per_model"]


def test_empty_sidecar_fails(capsys):
    """The regression: nothing to compare must never report PASS."""
    failures = check_against_published({"samples": {}})
    assert failures > 0
    out = capsys.readouterr().out
    assert "PASS" not in out
    assert "no completion-condition models at all" in out


def test_sidecar_with_no_completion_condition_fails():
    """Samples exist, but the condition was renamed: still nothing to compare."""
    flags = {"samples": {
        "a": {"condition": "unprompted", "model_slug": "gpt-5",
              "length_class": "compliant"},
    }}
    assert check_against_published(flags) > 0


def test_faithful_sidecar_passes(published_table):
    """The guard must not fire on a sidecar that does match the table."""
    assert check_against_published(sidecar_from_published(published_table)) == 0


def test_missing_model_fails(published_table, capsys):
    """A model present in the published table and absent from the sidecar."""
    failures = check_against_published(
        sidecar_from_published(published_table, drop=("gpt-5",)))
    assert failures > 0
    assert "gpt-5" in capsys.readouterr().out


def test_extra_model_fails(published_table, capsys):
    """A model the published table does not name must not pass unnoticed."""
    failures = check_against_published(
        sidecar_from_published(published_table, extra={"model-x": 3}))
    assert failures > 0
    assert "model-x" in capsys.readouterr().out


def test_expected_shape_matches_the_published_table(published_table):
    """The pinned constants describe the table actually shipped."""
    assert len(published_table) == EXPECTED_COMPLETION_MODELS
    total = sum(row["compliant"] + row["subfloor"] + row["refused"]
                for row in published_table.values())
    assert total == EXPECTED_COMPLETION_SAMPLES


def test_count_mismatch_is_still_caught(published_table):
    """Structural checks must not have displaced the count comparison."""
    flags = sidecar_from_published(published_table)
    # Move one sample between classes: totals and model set stay right.
    for key, sample in flags["samples"].items():
        if sample["model_slug"] == "claude-fable-5":
            sample["length_class"] = "sub_floor"
            break
    assert check_against_published(flags) > 0
