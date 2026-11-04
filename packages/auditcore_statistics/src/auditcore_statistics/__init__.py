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
from .concentration import (
    LorenzCurve,
    concentration_ratio,
    gini,
    herfindahl_hirschman,
    lorenz_curve,
)
from .legacy_flowinvoice import legacy_flowinvoice_benford, recommended_flowinvoice_benford
from .numeric import chi2_survival
from .significance import (
    ChiSquareTest,
    DigitZTest,
    chi2_critical_value,
    chi_square_test,
    digit_z_test,
)

__version__ = "0.4.0"

__all__ = [
    "LEGACY_METHOD",
    "METHOD",
    "BenfordResult",
    "ChiSquareTest",
    "DigitRow",
    "DigitZTest",
    "LorenzCurve",
    "StatisticsInputError",
    "__version__",
    "benford_test",
    "chi2_critical_value",
    "chi2_survival",
    "chi_square_test",
    "concentration_ratio",
    "digit_z_test",
    "expected_share",
    "gini",
    "herfindahl_hirschman",
    "legacy_flowinvoice_benford",
    "legacy_run_benford",
    "lorenz_curve",
    "recommended_flowinvoice_benford",
]
