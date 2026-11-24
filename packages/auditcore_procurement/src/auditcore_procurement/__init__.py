"""Procurement notices (TED, HAD), canonical records and deterministic prechecks.

Pure core without network dependencies. Source adapters for online harvest
live in :mod:`auditcore_procurement.sources` (extra ``sources``), the HAD HTML
parser needs the extra ``html``.
"""

from .authority_rules import CentralGovernmentRule, central_government_rule
from .company_sources import SearchResult, had_result, ted_company_result
from .lot_rules import Lot, VgvProvision, check_small_lots, estimation_hints, small_lots_rule
from .prechecks import (
    PrecheckProfile,
    ThresholdUnavailable,
    check_eu_threshold,
    eu_catalogue,
    eu_regime_threshold,
    load_profile,
    run_prechecks,
)
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

__version__ = "0.4.0"

__all__ = [
    "COVERAGE_ALL_NOTICES",
    "COVERAGE_AWARDS_WITH_WINNER",
    "NOTICE_FIELDS",
    "RECORD_CONTRACT",
    "CentralGovernmentRule",
    "Issue",
    "Lot",
    "PrecheckProfile",
    "VgvProvision",
    "SearchResult",
    "ThresholdUnavailable",
    "__version__",
    "build_ted_query",
    "central_government_rule",
    "check_eu_threshold",
    "check_small_lots",
    "eu_catalogue",
    "eu_regime_threshold",
    "estimation_hints",
    "had_result",
    "inspect_notice",
    "load_profile",
    "normalize_notice",
    "normalize_notices",
    "parse_ted_file",
    "run_prechecks",
    "small_lots_rule",
    "ted_company_result",
    "validate_record",
]
