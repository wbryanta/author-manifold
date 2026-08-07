"""
Shared attribution metric helpers.

Metric machinery for the validation harnesses. In this release the caller
is ``tools/validate_author_space.py`` (the author-relative space go/no-go
gate; docs/adr/ADR-0041-author-relative-measurement-space.md). The helpers
live here rather than inside that CLI module so they can be reused without
importing a tool module and its dependencies.

Note: a ``compute_c_llr`` helper was removed on 2026-08-06 -- its
implementation was not a valid log-likelihood-ratio cost and its values
were not interpretable. See ERRATA.md (E-1). The name survives as a stub
that raises, so code written against the 1.x API fails with the reason
rather than with a bare AttributeError.
"""

import logging
from typing import Any, List, NoReturn, Optional

logger = logging.getLogger(__name__)


def compute_roc_auc(
    y_true: List[int],
    y_scores: List[float],
) -> Optional[float]:
    """
    Compute ROC AUC score.

    Args:
        y_true: Binary labels (1 = positive, 0 = negative)
        y_scores: Prediction scores (higher = more positive)

    Returns:
        AUC score, or None when sklearn is unavailable / inputs degenerate
    """
    try:
        from sklearn.metrics import roc_auc_score
        return roc_auc_score(y_true, y_scores)
    except ImportError:
        logger.warning("sklearn not available; skipping ROC AUC")
        return None
    except ValueError as e:
        logger.warning(f"ROC AUC computation failed: {e}")
        return None


def compute_c_llr(*args: Any, **kwargs: Any) -> NoReturn:
    """Removed in 2.0.0. Retired, not reimplemented — see ERRATA.md (E-1)."""
    raise NotImplementedError(
        "compute_c_llr() was removed in author-manifold 2.0.0: the metric was "
        "not a valid log-likelihood-ratio cost and its values were not "
        "interpretable on the C_llr scale. It is retired rather than fixed "
        "(nothing published depended on it). See ERRATA.md, entry E-1."
    )
