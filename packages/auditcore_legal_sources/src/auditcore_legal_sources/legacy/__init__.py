"""Behavior-compatible adapters of the two characterized source applications.

``auditdatabase@bba911e`` (``app/harvester``) and ``audit_designer@030a71e``
(``app/modules/vp_ai/harvester``) are reproduced exactly, including defects
this package corrects in its own contract (``docs/behavior-changes.md``):
no string date is ever parsed, all-failing DIP searches report success and
the DIP document dictionary uses keys the ingestion service does not read.

The functions exist so consumers can switch to the installed package without
changing stored results and so every difference stays testable.

The flows are split by source: :mod:`.common` (dates, detection rules,
document shape), :mod:`.dip`, :mod:`.eurlex` and :mod:`.feeds`. Every name
stays importable from ``auditcore_legal_sources.legacy``.
"""

from .common import (
    _LEGACY_FORMATS,
    designer_detect_funding_period,
    legacy_content_hash,
    legacy_detect_fund,
    legacy_detect_funding_period,
    legacy_harvested_document,
    legacy_is_relevant,
    legacy_normalize_document,
    legacy_parse_date,
)
from .dip import (
    designer_dip_drucksache,
    designer_dip_vorgang,
    legacy_dip_harvest,
    legacy_dip_normalize,
    legacy_dip_query,
)
from .eurlex import (
    legacy_celex_type,
    legacy_eurlex_harvest,
    legacy_eurlex_normalize,
    legacy_sparql_rows,
    legacy_update_query,
)
from .feeds import (
    LEGACY_ECA_PLACEHOLDERS,
    _legacy_entry_parts,
    legacy_bafin_entry,
    legacy_curia_entry,
    legacy_eca_core_reports,
)

__all__ = [
    "LEGACY_ECA_PLACEHOLDERS",
    "_LEGACY_FORMATS",
    "_legacy_entry_parts",
    "designer_detect_funding_period",
    "designer_dip_drucksache",
    "designer_dip_vorgang",
    "legacy_bafin_entry",
    "legacy_celex_type",
    "legacy_content_hash",
    "legacy_curia_entry",
    "legacy_detect_fund",
    "legacy_detect_funding_period",
    "legacy_dip_harvest",
    "legacy_dip_normalize",
    "legacy_dip_query",
    "legacy_eca_core_reports",
    "legacy_eurlex_harvest",
    "legacy_eurlex_normalize",
    "legacy_harvested_document",
    "legacy_is_relevant",
    "legacy_normalize_document",
    "legacy_parse_date",
    "legacy_sparql_rows",
    "legacy_update_query",
]
