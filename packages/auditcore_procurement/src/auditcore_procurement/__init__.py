"""Procurement notices (TED, HAD), canonical records and deterministic prechecks.

Pure core without network dependencies. Source adapters for online harvest
live in :mod:`auditcore_procurement.sources` (extra ``sources``), the HAD HTML
parser needs the extra ``html``.
"""

from .company_sources import SearchResult, had_result, ted_company_result
from .prechecks import PrecheckProfile, ThresholdUnavailable, load_profile, run_prechecks
from .records import (
    COVERAGE_ALL_NOTICES,
    COVERAGE_AWARDS_WITH_WINNER,
    NOTICE_FIELDS,
    RECORD_CONTRACT,
    Issue,
    validate_record,
)
from .ted import (
    build_ted_query,
    inspect_notice,
    normalize_notice,
    normalize_notices,
    parse_ted_file,
)

__version__ = "0.1.0"

__all__ = [
    "COVERAGE_ALL_NOTICES",
    "COVERAGE_AWARDS_WITH_WINNER",
    "NOTICE_FIELDS",
    "RECORD_CONTRACT",
    "Issue",
    "PrecheckProfile",
    "SearchResult",
    "ThresholdUnavailable",
    "__version__",
    "build_ted_query",
    "had_result",
    "inspect_notice",
    "load_profile",
    "normalize_notice",
    "normalize_notices",
    "parse_ted_file",
    "run_prechecks",
    "ted_company_result",
    "validate_record",
]
