"""Plausibility checks on booking rows: target/actual, outliers, double funding.

Thresholds, tolerances and outlier factors are always inputs of the caller;
the library does not build in any business threshold.
"""

from __future__ import annotations

from ._duplicates import (
    DEVIATION,
    MATCH,
    MISSING,
    WITHIN_TOLERANCE,
    DoubleFunding,
    Reconciliation,
    double_funding,
    factorize,
    reconcile,
)
from ._outliers import (
    MAD_CONSTANT,
    OutlierResult,
    exceeds_threshold,
    iqr_outliers,
    mad_outliers,
)

__all__ = [
    "DEVIATION",
    "MAD_CONSTANT",
    "MATCH",
    "MISSING",
    "WITHIN_TOLERANCE",
    "DoubleFunding",
    "OutlierResult",
    "Reconciliation",
    "double_funding",
    "exceeds_threshold",
    "factorize",
    "iqr_outliers",
    "mad_outliers",
    "reconcile",
]
