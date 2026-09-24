"""Deployment profiles separate build inputs from release authorization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApplicationDeploymentProfile:
    """Versioned deployment configuration with explicit runtime choices."""

    application: str
    version: str
    source_commit: str
    source_digest: str
    entrypoint: list[str]
    schema_version: int = 1
    strategy: str = "DEBIAN_NATIVE_PYTHON"
    package_architecture: str = "all"
    source_directory: str = "src"
    system_dependencies: list[str] = field(default_factory=lambda: ["python3", "adduser"])
    wheelhouse: str = ""
    wheel_hashes: dict[str, str] = field(default_factory=dict)
    python_requirements: list[str] = field(default_factory=list)
    frontend_directory: str = ""
    frontend_build_output: str = "dist"
    frontend_commands: list[list[str]] = field(default_factory=list)
    configuration_files: dict[str, str] = field(default_factory=dict)
    persistent_directories: list[str] = field(default_factory=lambda: ["data", "uploads", "cache"])
    service_user: str = ""
    health_url: str = ""
    start_on_install: bool = False
    shared_library_versions: dict[str, str] = field(default_factory=dict)
    source_date_epoch: int = 0
    deployment_target: str = "internal_test"
    database_strategy: str = "none"
    upgrade_strategy: str = "preserve data and configuration; explicit database migrations"
    ci_run: str = "local"
    #: Fachliche Rauchtest-Fälle nach dem Deploy (Pflicht außer für internal_test),
    #: siehe :mod:`auditcore.tools.deployer.smoke`.
    functional_smoke: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DeploymentPlan:
    """Reviewable package layout, runtime resolution and release evidence."""

    profile: ApplicationDeploymentProfile
    filesystem_layout: dict[str, str]
    service_definition: str
    health_check: str
    policy_status: str
    handoff_status: str
    status: str
    blockers: list[str]


@dataclass
class DebianPackageBuild:
    """Built candidate is distinct from a release validated by installation tests."""

    status: str
    package: str
    sha256: str
    manifest: str
    sbom: str
    checksums: str
    release_status: str = "NOT_EXECUTED"


@dataclass
class PackageValidation:
    """Actual package checks with explicit systemd execution limits."""

    status: str
    checks: dict[str, str]
    package_sha256: str
    environment: str


@dataclass
class UpgradeValidation:
    """Upgrade and data/configuration preservation results."""

    status: str
    old_sha256: str
    new_sha256: str
    checks: dict[str, str]


@dataclass
class AptRepositoryBuild:
    """APT metadata and signature evidence."""

    status: str
    directory: str
    packages: int
    signed: bool
