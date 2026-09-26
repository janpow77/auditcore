"""auditcore_bpmn – BPMN 2.0 mit FlowAudit-Erweiterung (Schema 1.1) für Prüfbehörden.

Sicheres Parsen, Elementmodell, Prüfregeln, legacy-treue Kennzahlen und
Berichte aus audit_designer, Diagrammsammlung, Versions- und
Soll/Ist-Vergleich, Neutralisieren und Berichtsexporte. Keine Web-Frameworks,
keine Datenbank; optionale Extras: ``xml`` (defusedxml), ``excel``, ``pdf``,
``legal`` (auditcore_legal_sources).

Schnelleinstieg::

    from auditcore_bpmn import parse_bpmn, validate

    document = parse_bpmn(xml)
    report = validate(document)
    for item in report.issues:
        print(item.rule_id, item.message())
"""

from .citations import (
    CitationMatch,
    EuActResolver,
    NormResolution,
    NormResolver,
    enrich,
    find_citations,
    parse_citation,
)
from .collection import DiagramCollection, FileStorage, Storage
from .comparison import (
    Comparison,
    TargetActualComparison,
    apply_colors,
    colors_from_markers,
    compare,
    compare_target_actual,
)
from .enrichment import Suggestion, apply_suggestions, suggest
from .errors import (
    BpmnError,
    BpmnXmlError,
    CatalogError,
    CollectionError,
    OptionalDependencyError,
    UnsafeXmlError,
    XmlTooLargeError,
)
from .extensions import (
    Actor,
    AuditFinding,
    AuditReference,
    AuditStep,
    Control,
    CrossReference,
    Deadline,
    DiagramInfo,
    EsiRequirement,
    EsiRequirements,
    Evidence,
    Extensions,
    LegalBasis,
    Marker,
    Risk,
    Source,
)
from .legacy import BpmnAnalyzer, analyze_bpmn, validate_bpmn_bva
from .model import BpmnDocument, BpmnElement, parse_bpmn
from .namespaces import FLOWAUDIT_NAMESPACE, FLOWAUDIT_PREFIX, FLOWAUDIT_SCHEMA_VERSION
from .neutralize import NeutralizationResult, neutralize
from .profiles import STANDARD_PROFILE, Profile, ProfileRegistry, load_profile, profile_from_dict
from .reports import category_proposals, finding_list, process_table, risk_control_matrix, walkthrough_status
from .safe_xml import parse_xml
from .serialize import serialize
from .validation import ValidationConfig, ValidationIssue, ValidationReport, validate
from .writer import remove_extensions, set_diagram_info, set_extensions

__version__ = "0.1.1"

__all__ = [
    "FLOWAUDIT_NAMESPACE",
    "FLOWAUDIT_PREFIX",
    "FLOWAUDIT_SCHEMA_VERSION",
    "STANDARD_PROFILE",
    "Actor",
    "AuditFinding",
    "AuditReference",
    "AuditStep",
    "BpmnAnalyzer",
    "BpmnDocument",
    "BpmnElement",
    "BpmnError",
    "BpmnXmlError",
    "CatalogError",
    "CitationMatch",
    "CollectionError",
    "Comparison",
    "Control",
    "CrossReference",
    "Deadline",
    "DiagramCollection",
    "DiagramInfo",
    "EsiRequirement",
    "EsiRequirements",
    "EuActResolver",
    "Evidence",
    "Extensions",
    "FileStorage",
    "LegalBasis",
    "Marker",
    "NeutralizationResult",
    "NormResolution",
    "NormResolver",
    "OptionalDependencyError",
    "Profile",
    "ProfileRegistry",
    "Risk",
    "Source",
    "Storage",
    "Suggestion",
    "TargetActualComparison",
    "UnsafeXmlError",
    "ValidationConfig",
    "ValidationIssue",
    "ValidationReport",
    "XmlTooLargeError",
    "__version__",
    "analyze_bpmn",
    "apply_colors",
    "apply_suggestions",
    "category_proposals",
    "colors_from_markers",
    "compare",
    "compare_target_actual",
    "enrich",
    "find_citations",
    "finding_list",
    "load_profile",
    "neutralize",
    "parse_bpmn",
    "parse_citation",
    "parse_xml",
    "process_table",
    "profile_from_dict",
    "remove_extensions",
    "risk_control_matrix",
    "serialize",
    "set_diagram_info",
    "set_extensions",
    "suggest",
    "validate",
    "validate_bpmn_bva",
    "walkthrough_status",
]
