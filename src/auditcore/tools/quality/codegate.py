"""Discover and measure every package of the auditcore monorepo.

The platform (``src/auditcore``), every ``packages/auditcore_*`` domain package
and, when present, every ``packages-js/*`` package is measured separately so
that the ratchet can hold each package to its own baseline.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from auditcore.tools.quality.codegate_duplicates import duplicate_findings
from auditcore.tools.quality.codegate_js import measure_js_package
from auditcore.tools.quality.codegate_python import (
    PYTHON_METRICS,
    PackageMeasurement,
    complexity_findings,
    measure_source_files,
    mypy_findings,
    tool_version,
)

PLATFORM_PACKAGE = "auditcore"


@dataclass(frozen=True)
class PackageSource:
    """Location of one measured package."""

    name: str
    kind: str
    path: Path


def discover_packages(root: Path) -> list[PackageSource]:
    """Find the platform, all Python domain packages and all JS packages."""
    found: list[PackageSource] = []
    if (root / "src" / PLATFORM_PACKAGE / "__init__.py").is_file():
        found.append(PackageSource(PLATFORM_PACKAGE, "python", root / "src"))
    packages = root / "packages"
    for project in sorted(packages.glob("auditcore_*/pyproject.toml")):
        if (project.parent / "src").is_dir():
            found.append(PackageSource(project.parent.name, "python", project.parent / "src"))
    for manifest in sorted((root / "packages-js").glob("*/package.json")):
        found.append(PackageSource(f"js:{manifest.parent.name}", "js", manifest.parent))
    return found


def select_packages(found: list[PackageSource], names: Iterable[str]) -> list[PackageSource]:
    """Restrict measurement to explicitly named packages (fails on unknown names)."""
    wanted = set(names)
    if not wanted:
        return found
    unknown = wanted - {package.name for package in found}
    if unknown:
        raise ValueError(f"Unknown packages: {', '.join(sorted(unknown))}")
    return [package for package in found if package.name in wanted]


def _python_search_path(found: list[PackageSource]) -> list[Path]:
    return [package.path for package in found if package.kind == "python"]


def _python_source(package: PackageSource) -> Path:
    if package.name == PLATFORM_PACKAGE:
        return package.path / PLATFORM_PACKAGE
    return package.path


def _measure_python(
    package: PackageSource, root: Path, search_path: list[Path], with_mypy: bool
) -> PackageMeasurement:
    measurement = PackageMeasurement(name=package.name, kind="python")
    metrics = [m for m in PYTHON_METRICS if with_mypy or m != "mypy_strict_errors"]
    measurement.metrics = dict.fromkeys(metrics, 0)
    source = _python_source(package)
    measure_source_files(source, root, measurement)
    for finding in complexity_findings([source], root):
        measurement.add(finding)
    if with_mypy:
        for finding in mypy_findings(package.path, root, search_path):
            measurement.add(finding)
    return measurement


def measure(
    root: Path, packages: list[PackageSource], all_packages: list[PackageSource], with_mypy: bool
) -> list[PackageMeasurement]:
    """Measure the selected packages; mypy runs in parallel per package."""
    root = root.resolve()
    search_path = _python_search_path(all_packages)
    workers = max(1, min(8, (os.cpu_count() or 2) // 2))

    def run(package: PackageSource) -> PackageMeasurement:
        """Measure one package with the matching language rules."""
        if package.kind == "js":
            return measure_js_package(package.path, root)
        return _measure_python(package, root, search_path, with_mypy)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        measurements = list(pool.map(run, packages))
    # Duplicates are cross-package: always compare against every Python package.
    sources = [(p.name, _python_source(p)) for p in all_packages if p.kind == "python"]
    duplicates = duplicate_findings(sources, root)
    for measurement in measurements:
        for finding in duplicates.get(measurement.name, []):
            measurement.add(finding)
    return measurements


def tool_versions(with_mypy: bool) -> dict[str, str]:
    """Record the measuring tool versions next to the numbers."""
    versions = {"ruff": tool_version("ruff")}
    if with_mypy:
        versions["mypy"] = tool_version("mypy")
    return versions
