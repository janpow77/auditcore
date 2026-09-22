"""Inventory and consolidation records with immutable source identities."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WorkflowMode(StrEnum):
    """Repository analysis scopes."""

    GLOBAL = "GLOBAL"
    REPO = "REPO"
    REPO_AUDITCORE = "REPO_AUDITCORE"


@dataclass
class RepositoryRecord:
    """GitHub metadata and explicit structural-analysis coverage."""

    repository: str
    owner: str
    visibility: str
    default_branch: str
    archived: bool
    fork: bool
    primary_language: str | None
    commit_sha: str = "UNKNOWN"
    languages: list[str] = field(default_factory=list)
    project_type: str = "UNKNOWN"
    package_managers: list[str] = field(default_factory=list)
    python_version: str = "UNKNOWN"
    frameworks: list[str] = field(default_factory=list)
    tests: bool = False
    ci: bool = False
    license: str = "UNKNOWN"
    packages: list[str] = field(default_factory=list)
    structural_status: str = "NOT_EXECUTED"
    reason: str = ""
    file_count: int = 0
    source_url: str = ""
    affiliation: str = "OWNED"
    errors: list[str] = field(default_factory=list)


@dataclass
class SymbolRecord:
    """AST-observed symbol, never inferred semantic equivalence."""

    repository: str
    path: str
    module: str
    symbol: str
    symbol_type: str
    signature: str
    docstring_summary: str
    imports: list[str]
    callers: list[str]
    callees: list[str]
    framework_dependencies: list[str]
    database_dependencies: list[str]
    domain_category: str
    commit_sha: str
    line: int
    end_line: int
    fingerprint: str
    shape_fingerprint: str
    constants: list[str]
    security_sensitive: bool
    test_coverage: str = "UNKNOWN"
    last_change: str = "UNKNOWN"
    classification: str = "OBSERVED"


@dataclass
class LibraryCandidate:
    """Cross-repository candidate requiring characterization before extraction."""

    target_module: str
    symbols: list[dict[str, str]]
    repositories: list[str]
    similarity: str
    conflict_status: str
    decision_status: str
    consumers: list[str]
    technical_dependencies: list[str]
    known_tests: list[str]
    recommendation: str
    classification: str = "DERIVED"


@dataclass
class ConsolidationPlan:
    """Analysis handoff; source transformations belong to apprefactor."""

    target_module: str
    target_symbols: list[str]
    sources: list[dict[str, str]]
    technical_dependencies: list[str]
    domain_dependencies: list[str]
    conflicts: list[str]
    human_decisions: list[str]
    tests_required: list[str]
    migration_strategy: str = "characterize_then_compatibility_wrapper"
    status: str = "PLANNED"
    policy_impact: str = "REVIEW_REQUIRED"
    run_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
