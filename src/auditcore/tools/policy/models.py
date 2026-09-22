"""Applicability models; unknown is a value, never an implicit false."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import StrEnum
from typing import Any, Protocol


class Truth(StrEnum):
    """Three-valued applicability logic."""

    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class BindingLevel(StrEnum):
    """Framework obligation levels."""

    MUSS = "MUSS"
    BEDINGT = "BEDINGT"
    SOLL = "SOLL"


@dataclass(frozen=True)
class ApplicabilityContext:
    """Explicit project facts; missing answers remain UNKNOWN."""

    artifact_type: str = "UNKNOWN"
    data_space: str = "UNKNOWN"
    user_model: str = "UNKNOWN"
    personal_data: str = "UNKNOWN"
    binding_decisions: str = "UNKNOWN"
    workflow: str = "UNKNOWN"
    authentication: str = "UNKNOWN"
    uploads: bool | str = "UNKNOWN"
    external_interfaces: bool | str = "UNKNOWN"
    ai_usage: str = "UNKNOWN"
    deployment_target: str = "UNKNOWN"
    protection_need: str = "UNKNOWN"
    interactive_workspace: bool | str = "UNKNOWN"
    real_data_for_test_generation: bool | str = "UNKNOWN"
    graphical_ui: bool | str = "UNKNOWN"
    international_users: bool | str = "UNKNOWN"
    modular_capabilities: bool | str = "UNKNOWN"
    versioned_artifacts: bool | str = "UNKNOWN"
    versioned_artifact_types: tuple[str, ...] | str = "UNKNOWN"
    structured_imports: bool | str = "UNKNOWN"
    analytical_runs: bool | str = "UNKNOWN"
    exports: bool | str = "UNKNOWN"
    documents: bool | str = "UNKNOWN"
    delegation: bool | str = "UNKNOWN"
    dsfa_required: bool | str = "UNKNOWN"
    protection_need_source: str = "UNKNOWN"

    def __post_init__(self) -> None:
        artifact_types = self.versioned_artifact_types
        if isinstance(artifact_types, str) and artifact_types.lower() == "unknown":
            object.__setattr__(self, "versioned_artifact_types", "UNKNOWN")
        else:
            allowed = {
                "prompt",
                "agent",
                "rulebook",
                "checklist",
                "strategy",
                "template",
                "notebook_template",
            }
            if not isinstance(artifact_types, (tuple, list)) or not all(
                isinstance(item, str) and item in allowed for item in artifact_types
            ):
                raise ValueError(
                    "versioned_artifact_types must be an explicit type list or UNKNOWN"
                )
            normalized = tuple(sorted(set(artifact_types)))
            if self.versioned_artifacts is False and normalized:
                raise ValueError("Artifact types contradict versioned_artifacts=false")
            if self.versioned_artifacts is True and not normalized:
                raise ValueError("Versioned artifacts require at least one explicit type")
            object.__setattr__(self, "versioned_artifact_types", normalized)
        choices = {
            "artifact_type": "library prototype application service deployment_package",
            "data_space": "single_project multi_tenant shared",
            "user_model": "no_users single_user multi_user external_users",
            "personal_data": "none possible yes",
            "binding_decisions": "none drafts_only yes",
            "workflow": "calculation_only simple_crud procedural state_machine",
            "authentication": "none local oidc other",
            "ai_usage": "none local external_provider multiple_providers byok",
            "deployment_target": "prototype internal_test pilot production",
            "protection_need": "normal high very_high",
        }
        for item in fields(self):
            value = getattr(self, item.name)
            if isinstance(value, str) and value.lower() == "unknown":
                object.__setattr__(self, item.name, "UNKNOWN")
            elif item.name in choices and value not in choices[item.name].split():
                raise ValueError(f"Invalid {item.name}: expected an explicit enum value")
            elif item.type == "bool | str" and not isinstance(value, bool):
                raise ValueError(f"Invalid {item.name}: use boolean or UNKNOWN")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ApplicabilityContext:
        """Validate a context loaded from project configuration."""
        return cls(**data)

    def profiles(self) -> list[str]:
        """Derive convenience groups without changing requirement applicability."""
        result: list[str] = []
        if self.artifact_type == "library":
            result.append("LIBRARY")
        if self.artifact_type == "prototype" or self.deployment_target == "prototype":
            result.append("PROTOTYPE")
        if self.artifact_type in {"application", "service"}:
            result.append("INTERNAL_APP")
        if self.binding_decisions == "yes" or self.workflow in {"procedural", "state_machine"}:
            result.append("PROCEDURAL_APP")
        if self.ai_usage not in {"none", "UNKNOWN"}:
            result.append("AI_ENABLED")
        if self.protection_need in {"high", "very_high"} and self.protection_need_source in {
            "project_configuration",
            "protection_assessment",
            "HUMAN_CONFIRMED",
            "policy",
        }:
            result.append("HIGH_PROTECTION")
        return result


@dataclass(frozen=True)
class Requirement:
    """Source-backed requirement or its conditional implementation."""

    requirement_id: str
    source_repository: str
    source_path: str
    commit_sha: str
    classification: BindingLevel
    scope: str
    text: str
    trigger: dict[str, Any]
    derived_checks: tuple[str, ...] = ()
    adapter_current: bool = True


@dataclass(frozen=True)
class RequirementSet:
    """Loaded framework with explicit freshness and provenance."""

    repository: str
    commit_sha: str
    captured_at: str
    source_status: str
    requirements: tuple[Requirement, ...]
    tests: dict[str, dict[str, Any]]
    source_digests: dict[str, str]


@dataclass(frozen=True)
class RequirementEvaluation:
    """Applicability, implementation status and actual evidence stay distinct."""

    requirement_id: str
    source_path: str
    source_commit: str
    binding_level: str
    trigger: dict[str, Any]
    applicable: Truth
    applicability_reason: str
    status: str
    gate_status: str
    evidence: tuple[str, ...] = ()
    derived_checks: tuple[str, ...] = ()
    decision_reference: str | None = None


@dataclass(frozen=True)
class PolicyEvaluationResult:
    """Complete policy report suitable for quality, migration and deployment."""

    framework_repository: str
    framework_commit: str
    source_status: str
    artifact: str
    applicability_context: ApplicabilityContext
    profiles: list[str]
    requirements: tuple[RequirementEvaluation, ...]
    overall_status: str
    blocking_requirements: tuple[str, ...]
    review_required: tuple[str, ...]
    approved_deviations: tuple[str, ...]
    tests: dict[str, dict[str, Any]] = field(default_factory=dict)

    def blocks(self, requirement_ids: set[str]) -> bool:
        """Block only work depending on unresolved requirements."""
        return bool(requirement_ids.intersection(self.blocking_requirements + self.review_required))


class FrameworkPolicyProvider(Protocol):
    """External policy source contract."""

    def load_requirements(self) -> RequirementSet:
        """Load source content and freshness evidence."""
        ...

    def evaluate(self, context: ApplicabilityContext) -> PolicyEvaluationResult:
        """Evaluate applicability before creating technical failures."""
        ...
