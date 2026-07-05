"""
Shared attribution metric helpers.

Metric machinery used by both validation harnesses:

- ``backend/pipeline/tools/validate_attribution.py`` (hybrid-model harness)
- ``backend/pipeline/tools/validate_author_space.py`` (author-relative space
  go/no-go gate, ADR-0041 forthcoming, issue #60)

The functions were lifted verbatim from validate_attribution.py so that the
author-space harness can reuse them without importing a CLI tool module (and
its model dependencies). validate_attribution.py now imports from here.

References:
    - Brummer & du Preez (2006): Application-independent evaluation of
      speaker detection
    - C_llr metric: standard in forensic speaker verification
"""

import logging
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def compute_c_llr(
    target_scores: List[float],
    non_target_scores: List[float],
) -> Tuple[float, float]:
    """
    Compute C_llr (Log-likelihood ratio cost).

    Standard metric in forensic speaker verification.
    Lower is better. Random system = 1.0.

    Args:
        target_scores: Confidence scores for same-author pairs
        non_target_scores: Confidence scores for different-author pairs

    Returns:
        Tuple of (C_llr, C_llr_min)
    """
    def log_lr_cost(scores: List[float], is_target: bool) -> float:
        """Compute log-likelihood ratio cost for one class."""
        if not scores:
            return 0.0

        total = 0.0
        for score in scores:
            # Clamp to avoid log(0)
            score = max(1e-10, min(1 - 1e-10, score))

            if is_target:
                # For targets, we want high scores
                total += np.log2(1 + 1/score)
            else:
                # For non-targets, we want low scores
                total += np.log2(1 + score/(1-score))

        return total / len(scores)

    if not target_scores or not non_target_scores:
        return 1.0, 1.0

    # C_llr = average of target and non-target costs
    c_llr = 0.5 * (log_lr_cost(target_scores, True) + log_lr_cost(non_target_scores, False))

    # C_llr_min is achieved by optimal calibration (PAV algorithm)
    # Simplified: use sorted scores to estimate
    all_scores = [(s, True) for s in target_scores] + [(s, False) for s in non_target_scores]
    all_scores.sort(key=lambda x: x[0])

    # Approximate C_llr_min using threshold sweep
    best_c_llr = c_llr
    for threshold in np.linspace(0.1, 0.9, 17):
        # Recalibrated scores
        recal_target = [1.0 if s > threshold else 0.5 for s in target_scores]
        recal_non_target = [0.0 if s <= threshold else 0.5 for s in non_target_scores]
        test_c_llr = 0.5 * (log_lr_cost(recal_target, True) + log_lr_cost(recal_non_target, False))
        best_c_llr = min(best_c_llr, test_c_llr)

    return c_llr, best_c_llr


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
