"""Tests for the cross-topic probe's paper-configuration certification.

The probe stamps `is_paper_configuration` into its output. That stamp used
to rest on the artifact's filename alone, so a file from another shelf
renamed to `author_space_v1_wave2.json` was certified as the paper's C1b
configuration and its numbers published under that label. These tests pin
the structural certification that replaced it, and the integration test
pins that a renamed wrong-shelf artifact now stops the run.

Added after the cross-family review of 2026-08-07 (finding F2).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import cross_topic_probe as ctp  # noqa: E402


def test_matching_structure_certifies():
    ctp.assert_paper_configuration("author_space_v1_wave2.json", [
        ("shelf authors", ctp.PAPER_SHELF_AUTHORS, ctp.PAPER_SHELF_AUTHORS),
        ("--content-n", ctp.PAPER_CONTENT_N, ctp.PAPER_CONTENT_N),
    ])


def test_wrong_shelf_size_hard_fails():
    with pytest.raises(SystemExit) as excinfo:
        ctp.assert_paper_configuration("author_space_v1_wave2.json", [
            ("shelf authors", 9, ctp.PAPER_SHELF_AUTHORS),
            ("shelf works", 35, ctp.PAPER_SHELF_WORKS),
        ])
    message = str(excinfo.value)
    assert "STRUCTURE DOES NOT" in message
    assert "shelf authors: this run 9, paper run 15" in message
    assert "shelf works: this run 35, paper run 78" in message


def test_changed_run_parameter_hard_fails():
    with pytest.raises(SystemExit) as excinfo:
        ctp.assert_paper_configuration("author_space_v1_wave2.json", [
            ("--content-n", 500, ctp.PAPER_CONTENT_N),
        ])
    assert "--content-n: this run 500" in str(excinfo.value)


def test_pinned_expectations_match_the_committed_evidence():
    """The constants are transcribed from the recorded C1b run; check that."""
    recorded = json.loads(
        (REPO_ROOT / "reports/validation/author_space/topic_controls"
         / "cross_topic_probe.json").read_text(encoding="utf-8"))
    assert recorded["n_authors"] == ctp.PAPER_PROBE_AUTHORS
    assert recorded["n_works"] == ctp.PAPER_PROBE_WORKS
    assert recorded["min_works"] == ctp.PAPER_MIN_WORKS
    assert recorded["meta"]["content_n"] == ctp.PAPER_CONTENT_N
    assert recorded["meta"]["distance_variant"] == ctp.PAPER_DISTANCE_VARIANT


@pytest.mark.integration
def test_renamed_wrong_shelf_artifact_is_refused(tmp_path):
    """The defect itself: a PD artifact wearing the paper artifact's name."""
    impostor = tmp_path / ctp.PAPER_ARTIFACT
    shutil.copy(REPO_ROOT / "data/artifacts/author_space_pd_v1.json", impostor)
    out_dir = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools/cross_topic_probe.py"),
         "--artifact", str(impostor), "--output-dir", str(out_dir)],
        capture_output=True, text=True)
    assert proc.returncode != 0, proc.stdout
    assert "STRUCTURE DOES NOT" in proc.stderr + proc.stdout
    # And nothing was written under the paper's label.
    assert not out_dir.exists() or not list(out_dir.iterdir())
