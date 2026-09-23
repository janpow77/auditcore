"""Descriptive audit statistics with named, source-bound method profiles.

Results are statistics, not findings: nothing here marks records or data sets
as suspicious. See README.md and docs/behavior-changes.md.
"""

from .benford import (
    LEGACY_METHOD,
    METHOD,
    BenfordResult,
    DigitRow,
    StatisticsInputError,
    benford_test,
    expected_share,
    legacy_run_benford,
)
from .legacy_flowinvoice import legacy_flowinvoice_benford
from .numeric import chi2_survival

__version__ = "0.2.0"

__all__ = [
    "LEGACY_METHOD",
    "METHOD",
    "BenfordResult",
    "DigitRow",
    "StatisticsInputError",
    "__version__",
    "benford_test",
    "chi2_survival",
    "expected_share",
    "legacy_flowinvoice_benford",
    "legacy_run_benford",
]
