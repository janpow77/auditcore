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
from .register import RegisterService, check_activity, check_register, normalize_content
from .rules import RuleProfile, available_profiles, load_profile

__version__ = "0.4.0"

__all__ = [
    "Actor",
    "Answer",
    "AnswerValue",
    "Assessment",
    "AssessmentService",
    "AssessmentStatus",
    "AuditEvent",
    "AuthorizationError",
    "ConflictError",
    "DataProtectionError",
    "FourEyesViolation",
    "LockedVersionError",
    "NotFoundError",
    "Permission",
    "ProfileError",
    "Proposal",
    "RegisterService",
    "RegisterStatus",
    "RegisterVersion",
    "ReviewItem",
    "RuleProfile",
    "Scenario",
    "StaleRevisionError",
    "TenantMismatchError",
    "ValidationError",
    "__version__",
    "assess_risk",
    "available_profiles",
    "check_activity",
    "check_register",
    "finalize_consultation",
    "load_profile",
    "normalize_content",
    "parse_answers",
    "parse_scenarios",
    "prefill_from_activity",
    "propose",
    "screen",
]
