"""Behavior-compatible functions of the source applications (replay of the characterization).

Each function reproduces one characterized original on the recorded inputs
(``tests/fixtures/legacy_observed.json``), built on the library's profiles and
functions, so that a consumer can switch without changing results. Known
defects are reproduced here on purpose and corrected only in the library
contract (``docs/behavior-changes.md``). Where an original raised a transport
exception, the functions take the recorded error text instead of calling the
network.

The replays live in one private module per source application; this module
is the stable import path.
"""

from __future__ import annotations

from ._legacy_designer import (
    designer_dob_country,
    designer_index_search,
    designer_provider_min_score,
    designer_provider_name,
    designer_provider_schema,
    designer_records,
    designer_row,
    designer_service_search,
)
from ._legacy_flowinvoice_company import (
    flowinvoice_names_match,
    flowinvoice_normalize_company_name,
    flowinvoice_register_accepts,
    flowinvoice_register_company,
    flowinvoice_validate_vat,
    flowinvoice_verify_company,
)
from ._legacy_flowinvoice_screening import (
    LocalEntity,
    PEPMatch,
    PEPResult,
    SanctionMatch,
    flowinvoice_check_entity_local,
    flowinvoice_extract_position,
    flowinvoice_pep_check,
    flowinvoice_pep_entries,
    flowinvoice_sanctions_network,
    flowinvoice_to_list,
)
from ._legacy_flowsearch import (
    SANCTIONS_SOURCES,
    flowsearch_assess_risk,
    flowsearch_check_person,
    flowsearch_check_sanctions,
    flowsearch_entity_type,
    flowsearch_handelsregister_search,
    flowsearch_kmu,
    flowsearch_openregister_error,
    flowsearch_pep_authorization,
    flowsearch_pep_category,
    flowsearch_pep_payload,
    flowsearch_pep_type,
    flowsearch_sanctions_payload,
    flowsearch_share,
    flowsearch_ubo,
)
from ._legacy_osint import (
    osint_hwk,
    osint_ihk,
    osint_kammern,
    osint_zer,
)
from ._legacy_portal import (
    portal_parse_sanctions_csv,
    portal_record,
    portal_vat_ids,
)
from ._legacy_shared import VERSION, RawRecord
from ._legacy_shared import _profile as _profile  # used by the replay tests
from ._legacy_shared import _settings as _settings
from ._legacy_workshop import (
    workshop_dob_country,
    workshop_index_search,
    workshop_multi_search,
    workshop_record,
    workshop_records,
)
from .errors import QueryError

__all__ = [
    "LocalEntity",
    "PEPMatch",
    "PEPResult",
    "QueryError",
    "RawRecord",
    "SANCTIONS_SOURCES",
    "SanctionMatch",
    "VERSION",
    "designer_dob_country",
    "designer_index_search",
    "designer_provider_min_score",
    "designer_provider_name",
    "designer_provider_schema",
    "designer_records",
    "designer_row",
    "designer_service_search",
    "flowinvoice_check_entity_local",
    "flowinvoice_extract_position",
    "flowinvoice_names_match",
    "flowinvoice_normalize_company_name",
    "flowinvoice_pep_check",
    "flowinvoice_pep_entries",
    "flowinvoice_register_accepts",
    "flowinvoice_register_company",
    "flowinvoice_sanctions_network",
    "flowinvoice_to_list",
    "flowinvoice_validate_vat",
    "flowinvoice_verify_company",
    "flowsearch_assess_risk",
    "flowsearch_check_person",
    "flowsearch_check_sanctions",
    "flowsearch_entity_type",
    "flowsearch_handelsregister_search",
    "flowsearch_kmu",
    "flowsearch_openregister_error",
    "flowsearch_pep_authorization",
    "flowsearch_pep_category",
    "flowsearch_pep_payload",
    "flowsearch_pep_type",
    "flowsearch_sanctions_payload",
    "flowsearch_share",
    "flowsearch_ubo",
    "osint_hwk",
    "osint_ihk",
    "osint_kammern",
    "osint_zer",
    "portal_parse_sanctions_csv",
    "portal_record",
    "portal_vat_ids",
    "workshop_dob_country",
    "workshop_index_search",
    "workshop_multi_search",
    "workshop_record",
    "workshop_records",
]
