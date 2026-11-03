"""Fail-closed number gates for generated reports.

Printed German numbers with precision (:mod:`.numbers`), units that keep
percent and percentage points apart (:mod:`.units`), the prose number gate
(:mod:`.prose`), the reference value gate for tables (:mod:`.reference`) and
the release decision over required gates (:mod:`.verdict`).

Nothing that could not be checked is reported as passed.
"""

from .numbers import (
    MISSING,
    MISSING_MARKERS,
    MISSING_TEXT,
    Missing,
    PrintedNumber,
    exact,
    format_de,
    read_cell,
    read_number,
    relative_deviation,
    same_value,
    tolerance,
)
from .prose import (
    NEIGHBOURHOOD,
    NO_CLAIMS,
    BoundValue,
    Claim,
    ClaimCheck,
    ClaimStatus,
    check_claim,
    check_paragraph,
    combine,
    extract_claims,
)
from .reference import Table, compare_tables, normalise_label
from .units import PERCENT, PERCENTAGE_POINTS, PLAIN, Dimension, Unit, conversion_exponent, unit_of
from .verdict import Finding, GateResult, ReleaseDecision, Verdict, decide, release

__version__ = "0.1.0"

__all__ = [
    "MISSING",
    "MISSING_MARKERS",
    "MISSING_TEXT",
    "NEIGHBOURHOOD",
    "NO_CLAIMS",
    "PERCENT",
    "PERCENTAGE_POINTS",
    "PLAIN",
    "BoundValue",
    "Claim",
    "ClaimCheck",
    "ClaimStatus",
    "Dimension",
    "Finding",
    "GateResult",
    "Missing",
    "PrintedNumber",
    "ReleaseDecision",
    "Table",
    "Unit",
    "Verdict",
    "__version__",
    "check_claim",
    "check_paragraph",
    "combine",
    "compare_tables",
    "conversion_exponent",
    "decide",
    "exact",
    "extract_claims",
    "format_de",
    "normalise_label",
    "read_cell",
    "read_number",
    "relative_deviation",
    "release",
    "same_value",
    "tolerance",
    "unit_of",
]
