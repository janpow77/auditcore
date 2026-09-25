"""Register, sanctions and PEP sources with explicit, source-bound profiles.

Public API of contract ``auditcore_registry_sources.screening/1``. Name
normalisation comes from ``auditcore_entity_matching``; downloads run through
``auditcore_harvest`` adapters. Optional extras: ``fuzzy`` (rapidfuzz, name
screening), ``xml`` (defusedxml, official list XML and VIES), ``html``
(BeautifulSoup, chambers of crafts page).
"""

from .bulk_screening import BulkHit, BulkResult, local_screen, pep_bulk_screen
from .company import (
    CompanyVerification,
    RegisterLookup,
    VatCheck,
    check_vat,
    lookup_register,
    parse_register_rows,
    parse_vies_response,
    verify_company,
)
from .errors import DependencyError, FormatError, ProfileError, QueryError, RegistrySourcesError
from .lists import find_list, list_catalog, load_lists
from .model import ListEntry, ListSnapshot, ParsedList, RowIssue, SanctionsList
from .opensanctions_api import (
    KeyCredentials,
    MatchClient,
    MatchQuery,
    assess_pep,
    assess_sanctions,
    configuration_status,
    credentials_from_environment,
    parse_response,
    person_query,
    sanctions_query,
)
from .opensanctions_csv import parse_targets_simple_csv, serialize_targets_simple_csv
from .ownership import (
    beneficial_owners,
    ownership_chain,
    sme_status,
    traverse,
    unclassified_holders,
)
from .profiles import RegistryProfile, available_profiles, load_profile, recommended_profile
from .sanctions_xml import parse_xml_list, xml_entries
from .screening import ListFinding, ScreeningHit, ScreeningResult, screen

__version__ = "0.1.1"
CONTRACT_VERSION = "auditcore_registry_sources.screening/1"

__all__ = [
    "CONTRACT_VERSION",
    "BulkHit",
    "BulkResult",
    "CompanyVerification",
    "KeyCredentials",
    "DependencyError",
    "FormatError",
    "ListEntry",
    "ListFinding",
    "ListSnapshot",
    "MatchClient",
    "MatchQuery",
    "ParsedList",
    "ProfileError",
    "QueryError",
    "RegisterLookup",
    "RegistryProfile",
    "RegistrySourcesError",
    "RowIssue",
    "SanctionsList",
    "ScreeningHit",
    "ScreeningResult",
    "VatCheck",
    "__version__",
    "assess_pep",
    "assess_sanctions",
    "available_profiles",
    "beneficial_owners",
    "check_vat",
    "find_list",
    "list_catalog",
    "load_lists",
    "load_profile",
    "local_screen",
    "lookup_register",
    "ownership_chain",
    "parse_register_rows",
    "parse_response",
    "parse_targets_simple_csv",
    "parse_vies_response",
    "parse_xml_list",
    "pep_bulk_screen",
    "person_query",
    "sanctions_query",
    "screen",
    "serialize_targets_simple_csv",
    "sme_status",
    "traverse",
    "verify_company",
    "configuration_status",
    "credentials_from_environment",
    "recommended_profile",
    "unclassified_holders",
    "xml_entries",
]
