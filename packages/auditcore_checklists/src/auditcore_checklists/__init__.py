"""Checklisten-Kern: hierarchische Prüfbäume, Antwort- und
Auswertungsvertrag sowie portabler Paketaustausch.
"""

from .answers import ExecutionState
from .errors import (
    ChecklistError,
    CycleDetectedError,
    InvalidBranchError,
    NodeNotFoundError,
    PackageFormatError,
    TreeStructureError,
)
from .evaluation import EvaluationResult, FindingSummary, evaluate_checklist
from .models import (
    AnswerType,
    CategoryDefinition,
    CategoryItemDefinition,
    ChecklistAnswer,
    ChecklistNode,
    FindingSeverity,
    FindingType,
    HistoryAction,
    NodeContent,
    NodeInternal,
    NodeStatus,
    NodeType,
    ProjectMetadata,
    TeamNote,
    TreeValidationFinding,
    VersionSnapshot,
)
from .package import (
    FORMAT_VERSION,
    PACKAGE_FORMAT,
    compute_canonical_tree,
    compute_package_checksum,
    export_package,
    import_package,
    normalize_package_payload,
    validate_package,
)
from .tree import ChecklistTree

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "PACKAGE_FORMAT",
    "FORMAT_VERSION",
    "ChecklistError",
    "TreeStructureError",
    "NodeNotFoundError",
    "CycleDetectedError",
    "InvalidBranchError",
    "PackageFormatError",
    "NodeType",
    "AnswerType",
    "FindingType",
    "FindingSeverity",
    "NodeStatus",
    "HistoryAction",
    "TeamNote",
    "NodeContent",
    "NodeInternal",
    "ChecklistNode",
    "CategoryDefinition",
    "CategoryItemDefinition",
    "ChecklistAnswer",
    "TreeValidationFinding",
    "ProjectMetadata",
    "VersionSnapshot",
    "ChecklistTree",
    "ExecutionState",
    "EvaluationResult",
    "FindingSummary",
    "evaluate_checklist",
    "compute_canonical_tree",
    "compute_package_checksum",
    "export_package",
    "import_package",
    "normalize_package_payload",
    "validate_package",
]
