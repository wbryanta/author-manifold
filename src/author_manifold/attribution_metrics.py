"""
Shared attribution metric helpers.

Metric machinery used by both validation harnesses:

- ``backend/pipeline/tools/validate_attribution.py`` (hybrid-model harness)
- ``backend/pipeline/tools/validate_author_space.py`` (author-relative space
  go/no-go gate, ADR-0041 forthcoming, issue #60)

The functions were lifted verbatim from validate_attribution.py so that the
author-space harness can reuse them without importing a CLI tool module (and
its model dependencies). validate_attribution.py now imports from here.

Note: a ``compute_c_llr`` helper was removed on 2026-08-06 -- its
implementation was not a valid log-likelihood-ratio cost and its values
were not interpretable. See ERRATA.md (E-1).
"""

import logging
from typing import List, Optional

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
