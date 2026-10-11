"""Records of processing activities (VVT) and data protection impact assessments (DSFA).

Create, edit, calculate, version, release and export registers and DPIAs
through explicit rule profiles and consumer-implemented ports. See README.md.
"""

from .assessment import AssessmentService
from .calculation import (
    Answer,
    AnswerValue,
    Proposal,
    Scenario,
    assess_risk,
    finalize_consultation,
    parse_answers,
    parse_scenarios,
    prefill_from_activity,
    propose,
    screen,
)
from .central_register import (
    CentralRegisterPort,
    CentralRegisterService,
    CentralRegisterUnavailable,
    Receipt,
    TransferRecord,
    TransferRepository,
)
from .checklist import ChecklistItem, ItemStatus, Transition
from .errors import (
    AuthorizationError,
    ConflictError,
    DataProtectionError,
    FourEyesViolation,
    LockedVersionError,
    NotFoundError,
    ProfileError,
    StaleRevisionError,
    TenantMismatchError,
    ValidationError,
)
from .evaluation import Evaluation
from .evidence import Evidence, EvidenceKind, Safeguard, SafeguardState
from .gates import GateFinding
from .model import (
    Actor,
    Assessment,
    AssessmentStatus,
    AuditEvent,
    Permission,
    RegisterStatus,
    RegisterVersion,
    ReviewItem,
)
from .operation import DecisionRequest, OperationService
from .operation_model import OperationalDecision, OperationRepository, UrgentStart
from .register import RegisterService, check_activity, check_register, normalize_content
from .review_package import review_package
from .rules import RuleProfile, available_profiles, load_profile
from .status import StatusAxes
from .wizard_catalog import WizardCatalog, catalog_for, load_catalog
from .workspace import ActivityWorkspace

__version__ = "0.6.0"

__all__ = [
    "ActivityWorkspace",
    "Actor",
    "Answer",
    "AnswerValue",
    "Assessment",
    "AssessmentService",
    "AssessmentStatus",
    "AuditEvent",
    "AuthorizationError",
    "CentralRegisterPort",
    "CentralRegisterService",
    "CentralRegisterUnavailable",
    "ChecklistItem",
    "ConflictError",
    "DataProtectionError",
    "DecisionRequest",
    "Evaluation",
    "Evidence",
    "EvidenceKind",
    "FourEyesViolation",
    "GateFinding",
    "ItemStatus",
    "LockedVersionError",
    "NotFoundError",
    "OperationRepository",
    "OperationService",
    "OperationalDecision",
    "Permission",
    "ProfileError",
    "Proposal",
    "Receipt",
    "RegisterService",
    "RegisterStatus",
    "RegisterVersion",
    "ReviewItem",
    "RuleProfile",
    "Safeguard",
    "SafeguardState",
    "Scenario",
    "StaleRevisionError",
    "StatusAxes",
    "TenantMismatchError",
    "TransferRecord",
    "TransferRepository",
    "Transition",
    "UrgentStart",
    "ValidationError",
    "WizardCatalog",
    "__version__",
    "assess_risk",
    "available_profiles",
    "catalog_for",
    "check_activity",
    "check_register",
    "finalize_consultation",
    "load_catalog",
    "load_profile",
    "normalize_content",
    "parse_answers",
    "parse_scenarios",
    "prefill_from_activity",
    "propose",
    "review_package",
    "screen",
]
