"""Framework policy integration, separated from the domain library."""

from auditcore.tools.policy.evidence import artifact_source_digest, evidence_binding
from auditcore.tools.policy.framework import GitFrameworkPolicyProvider
from auditcore.tools.policy.models import (
    ApplicabilityContext,
    FrameworkPolicyProvider,
    PolicyEvaluationResult,
)

__all__ = [
    "ApplicabilityContext",
    "FrameworkPolicyProvider",
    "GitFrameworkPolicyProvider",
    "PolicyEvaluationResult",
    "artifact_source_digest",
    "evidence_binding",
]
