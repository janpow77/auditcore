"""Reviewable refactoring plans and regression evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CharacterizationCase:
    """Known inputs and observed legacy outcome."""

    name: str
    args: list[Any]
    kwargs: dict[str, Any]
    expected: Any = None
    expected_exception: str | None = None


@dataclass(frozen=True)
class LegacyResult:
    """Observed legacy function outcome."""

    case: str
    value: Any
    exception: str | None


@dataclass(frozen=True)
class AuditCoreResult:
    """Observed replacement function outcome."""

    case: str
    value: Any
    exception: str | None


@dataclass(frozen=True)
class RegressionComparison:
    """Exact behavior comparison; no automatic tolerance or rule harmonization."""

    status: str
    cases: list[dict[str, Any]]
    source_digest: str
    target_digest: str


@dataclass
class ApplicationRefactoringPlan:
    """Source-bound changes with preconditions, tests and rollback strategy."""

    application: str
    source_commit: str
    source_digest: str
    target_shared_libraries: dict[str, str]
    files_to_change: list[str] = field(default_factory=list)
    imports_to_change: list[dict[str, str]] = field(default_factory=list)
    symbols_to_replace: list[dict[str, Any]] = field(default_factory=list)
    wrappers_to_create: list[dict[str, Any]] = field(default_factory=list)
    tests_to_update: list[str] = field(default_factory=list)
    dependencies_to_remove: list[str] = field(default_factory=list)
    dependencies_to_add: list[str] = field(default_factory=list)
    optimization_steps: list[dict[str, str]] = field(default_factory=list)
    risk_level: str = "REVIEW_REQUIRED"
    rollback_strategy: str = "restore exact original bytes on any failed verification"
    verification_commands: dict[str, list[str]] = field(default_factory=dict)
    policy_dependencies: list[str] = field(default_factory=lambda: ["F-07", "F-09"])
    known_conflicts: list[str] = field(default_factory=list)
    approved_human_decisions: list[dict[str, str]] = field(default_factory=list)
    policy_before: str = ""
    policy_after: str = ""
