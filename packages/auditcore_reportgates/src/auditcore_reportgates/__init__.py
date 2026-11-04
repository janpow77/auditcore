"""Fail-closed number gates for generated reports.

Printed German numbers with precision (:mod:`.numbers`), units that keep
percent and percentage points apart (:mod:`.units`), the prose number gate
(:mod:`.prose`) with its tokeniser settings (:mod:`.syntax`), the reference
value gate for tables (:mod:`.reference`) and the release decision over
required gates (:mod:`.verdict`).

Nothing that could not be checked is reported as passed.
"""

from .numbers import (
    MISSING,
    MISSING_MARKERS,
    MISSING_TEXT,
    ROUNDING_MODES,
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
    ambiguous_numbers,
    check_claim,
    check_paragraph,
    combine,
    extract_claims,
)
from .reference import Table, compare_tables, normalise_label
from .syntax import (
    BASIC_UNITS,
    DEFAULT_MASKS,
    DEFAULT_SYNTAX,
    DEFAULT_UNITS,
    ClaimSyntax,
    PointReading,
)
from .units import (
    CURRENCY,
    PERCENT,
    PERCENTAGE_POINTS,
    PLAIN,
    Dimension,
    Unit,
    conversion_exponent,
    scale_of,
    unit_of,
)
from .verdict import Finding, GateResult, ReleaseDecision, Verdict, decide, release

__version__ = "0.2.0"

__all__ = [
    "BASIC_UNITS",
    "CURRENCY",
    "DEFAULT_MASKS",
    "DEFAULT_SYNTAX",
    "DEFAULT_UNITS",
    "MISSING",
    "MISSING_MARKERS",
    "MISSING_TEXT",
    "NEIGHBOURHOOD",
    "NO_CLAIMS",
    "PERCENT",
    "PERCENTAGE_POINTS",
    "PLAIN",
    "ROUNDING_MODES",
    "BoundValue",
    "Claim",
    "ClaimCheck",
    "ClaimStatus",
    "ClaimSyntax",
    "Dimension",
    "Finding",
    "GateResult",
    "Missing",
    "PointReading",
    "PrintedNumber",
    "ReleaseDecision",
    "Table",
    "Unit",
    "Verdict",
    "__version__",
    "ambiguous_numbers",
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
    "scale_of",
    "tolerance",
    "unit_of",
]
