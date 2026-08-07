"""Tests for the shared attribution metric helpers.

Mostly this module guards the *absence* of a metric. `compute_c_llr()` was
removed on 2026-08-06 (ERRATA.md E-1) because its implementation was not a
log-likelihood-ratio cost; the removal is a breaking API change, so the
package went to 2.0.0 and the name survives only as a stub that raises.
Both halves of that contract are pinned here, because a silent
reintroduction — or a silent revert of the version — is exactly the drift
the errata entry exists to prevent.

Added after the cross-family review of 2026-08-07 (finding F1).
"""

import pytest

import author_manifold
from author_manifold.attribution_metrics import compute_c_llr, compute_roc_auc


def test_package_version_records_the_breaking_removal():
    assert author_manifold.__version__ == "2.0.0"


def test_compute_c_llr_raises_and_names_the_errata_entry():
    with pytest.raises(NotImplementedError) as excinfo:
        compute_c_llr([1, 0], [0.9, 0.1])
    message = str(excinfo.value)
    assert "ERRATA.md" in message
    assert "E-1" in message


def test_compute_roc_auc_still_works():
    assert compute_roc_auc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == 1.0
