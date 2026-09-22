"""Static, revision-bound inventory of independently installable workspace projects."""

from __future__ import annotations

import json
import os
import re
import tomllib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from auditcore.tools.common import digest, now, read_json, run, safe_path, write_json
from auditcore.tools.policy.models import ApplicabilityContext
from auditcore.tools.quality.scanners import api_snapshot, scan_sensitive

IGNORED = {
    ".git",
    ".auditcore",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    "node_modules",
}


class WorkspaceError(ValueError):
    """Workspace validation failure whose message contains only fixed safe text."""


def canonical_name(name: str) -> str:
    """Normalize a validated Python distribution name for dependency identity."""
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?", name):
        raise WorkspaceError("Invalid distribution name")
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement(value: str, group: str) -> dict[str, str]:
    """Identify declared names without pretending to evaluate PEP 508 markers."""
    match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?=\s*(?:[\[<>=!~@;]|$))", value.strip())
    sensitive = scan_sensitive(value) or re.search(r"://[^/\s]+@", value)
    return {
        "requirement": "REDACTED_REVIEW_REQUIRED" if sensitive else value,
        "sha256": digest(value),
        "group": group,
        "name": canonical_name(match[1]) if match else "UNKNOWN",
        "status": "DECLARED_NOT_RESOLVED" if match and not sensitive else "REVIEW_REQUIRED",
        "conditional": "UNKNOWN" if ";" in value or group != "runtime" else "FALSE",
    }


def _project_files(
    root: Path, project: Path, members: set[Path]
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """Hash project inputs, excluding generated state and other distribution roots."""
    result = {}
    links = {}
    for current, directories, filenames in os.walk(project, followlinks=False):
        folder = Path(current)
        selected = []
        for name in sorted(directories):
            child = folder / name
            if name in IGNORED or name.endswith(".egg-info") or child in members:
                continue
            safe_path(root, child.relative_to(root).as_posix())
            selected.append(name)
        directories[:] = selected
        for name in sorted(filenames):
            if name.endswith((".pyc", ".pyo")) or name in {".coverage", ".DS_Store"}:
                continue
            path = folder / name
            relative = path.relative_to(project).as_posix()
            if path.is_symlink():
                try:
                    target = path.resolve(strict=True)
                except (OSError, RuntimeError) as exc:
                    raise WorkspaceError(
                        "Project contains a broken or cyclic file symlink"
                    ) from exc
                if not target.is_relative_to(project):
                    raise WorkspaceError("Project contains an external symlinked file")
                if any(
                    member.is_relative_to(project) and target.is_relative_to(member)
                    for member in members
                ):
                    raise WorkspaceError(
                        "Project file symlink points into another package or state"
                    )
                if not target.is_file():
                    raise WorkspaceError("Project file symlink does not target a regular file")
                links[relative] = {
                    "target": target.relative_to(project).as_posix(),
                    "link_sha256": digest(os.readlink(path)),
                }
            else:
                safe_path(root, path.relative_to(root).as_posix())
            if not path.is_file():
                raise WorkspaceError("Project contains a nonregular file")
            result[relative] = digest(path.read_bytes())
    return result, links


class PackageWorkspace:
    """Read metadata without importing packages, running backends or resolving networks."""

    def __init__(self, root: Path, state_dir: Path | None = None) -> None:
        if root.is_symlink():
            raise WorkspaceError("Workspace root may not be a symlink")
        self.root = root.resolve(strict=True)
        self.state = (
            (state_dir or self.root / ".auditcore").resolve()
            / "workspaces"
            / digest(str(self.root))
        )

    def _configuration(self) -> tuple[dict[str, Any], list[Path]]:
        path = safe_path(self.root, "auditcore-workspace.toml")
        config = tomllib.loads(path.read_text()) if path.exists() else {}
        workspace = config.get("workspace", {})
        if workspace.get("version", 1) != 1:
            raise WorkspaceError("Unsupported workspace configuration version")
        entries = workspace.get("members", [".", "packages/*"])
        if not isinstance(entries, list) or any(not isinstance(entry, str) for entry in entries):
            raise WorkspaceError("workspace.members must be paths")
        members = set()
        for entry in entries:
            if entry == "packages/*":
                folder = safe_path(self.root, "packages")
                candidates = sorted(folder.iterdir()) if folder.exists() else []
            else:
                candidates = [safe_path(self.root, entry)]
            for candidate in candidates:
                candidate = safe_path(self.root, candidate.relative_to(self.root).as_posix())
                manifest = safe_path(
                    self.root, (candidate / "pyproject.toml").relative_to(self.root).as_posix()
                )
                if manifest.is_file():
                    members.add(candidate)
                elif entry != "packages/*":
                    raise WorkspaceError("Configured member lacks pyproject.toml")
        if not members:
            raise WorkspaceError("No installable project manifests found")
        settings = config.get("package", [])
        if not isinstance(settings, list) or any(not isinstance(item, dict) for item in settings):
            raise WorkspaceError("package must be an array of configuration tables")
        configured_paths = [item.get("path") for item in settings]
        if len(configured_paths) != len(set(configured_paths)):
            raise WorkspaceError("Duplicate package configuration")
        if any(safe_path(self.root, str(path)) not in members for path in configured_paths):
            raise WorkspaceError("Package configuration does not identify a member")
        return config, sorted(members)

    def _package(self, path: Path, members: set[Path], settings: dict[str, Any]) -> dict[str, Any]:
        settings = dict(settings)
        for key, filename in (
            ("applicability", "auditcore-context.json"),
            ("provenance", "provenance.json"),
        ):
            if key not in settings and (path / filename).exists():
                settings[key] = (path / filename).relative_to(self.root).as_posix()
        data = tomllib.loads((path / "pyproject.toml").read_text())
        project = data.get("project", {})
        name = project.get("name")
        if not isinstance(name, str):
            raise WorkspaceError("Installable project requires a static PEP 621 name")
        files, links = _project_files(self.root, path, (members - {path}) | {self.state})
        source_roots = settings.get("source_roots")
        source_status = "CONFIGURED"
        if source_roots is None:
            source_roots = (
                (
                    data.get("tool", {})
                    .get("setuptools", {})
                    .get("packages", {})
                    .get("find", {})
                    .get("where")
                )
                if isinstance(data.get("tool", {}).get("setuptools", {}).get("packages", {}), dict)
                else None
            )
            source_status = "BUILD_CONFIGURATION" if source_roots else "CONVENTIONAL_DISCOVERY"
            source_roots = source_roots or (["src"] if (path / "src").is_dir() else ["."])
        if not isinstance(source_roots, list) or any(not isinstance(s, str) for s in source_roots):
            raise WorkspaceError("source_roots must be relative paths")
        api: dict[str, dict[str, str]] = {}
        api_errors = []
        for relative in source_roots:
            source_root = safe_path(path, relative)
            if not source_root.is_dir():
                raise WorkspaceError("Source root does not exist")
            sources = {}
            for filename in files:
                source = path / filename
                if source.suffix == ".py" and source.is_relative_to(source_root):
                    local = source.relative_to(source_root)
                    if "tests" not in local.parts and not local.name.startswith("test_"):
                        sources[local.as_posix()] = source.read_text(encoding="utf-8")
            for filename, source_text in sources.items():
                try:
                    snapshot = api_snapshot({filename: source_text})
                    if api.keys() & snapshot.keys():
                        raise WorkspaceError("Overlapping source roots or import APIs")
                    api.update(snapshot)
                except SyntaxError:
                    api_errors.append(filename)
        declared = project.get("dependencies", [])
        extras = project.get("optional-dependencies", {})
        if not isinstance(declared, list) or any(not isinstance(item, str) for item in declared):
            raise WorkspaceError("Project dependencies must be requirement strings")
        if not isinstance(extras, dict):
            raise WorkspaceError("Optional dependencies must be named groups")
        dependencies = [_requirement(item, "runtime") for item in declared]
        for group, requirements in extras.items():
            if not isinstance(requirements, list) or any(
                not isinstance(item, str) for item in requirements
            ):
                raise WorkspaceError("Optional dependency groups must contain requirement strings")
            dependencies += [_requirement(item, "extra:" + group) for item in requirements]
        requirements_files = []
        for filename in files:
            if Path(filename).name.startswith("requirements") and filename.endswith(".txt"):
                declarations = [
                    _requirement(line.strip(), "requirements_file")
                    for line in (path / filename).read_text().splitlines()
                    if line.strip() and not line.lstrip().startswith("#")
                ]
                requirements_files.append(
                    {"path": filename, "sha256": files[filename], "declarations": declarations}
                )
        context = ApplicabilityContext()
        context_path = settings.get("applicability")
        evidence_files = {}
        if context_path:
            reference = safe_path(self.root, context_path)
            try:
                context = ApplicabilityContext.from_dict(read_json(reference))
            except TypeError as exc:
                raise WorkspaceError("Invalid applicability context fields") from exc
            evidence_files[context_path] = digest(reference.read_bytes())
        provenance_path = settings.get("provenance")
        if provenance_path:
            reference = safe_path(self.root, provenance_path)
            evidence_files[provenance_path] = digest(reference.read_bytes())
        return {
            "path": path.relative_to(self.root).as_posix(),
            "name": name,
            "canonical_name": canonical_name(name),
            "version": project.get("version", "UNKNOWN"),
            "requires_python": project.get("requires-python", "UNKNOWN"),
            "metadata_status": "REVIEW_REQUIRED" if project.get("dynamic") else "OBSERVED",
            "build_backend": data.get("build-system", {}).get("build-backend", "UNKNOWN"),
            "source_roots": source_roots,
            "source_roots_status": source_status,
            "source_sha256": digest(
                json.dumps(
                    {"files": files, "symlinks": links, "evidence": evidence_files}, sort_keys=True
                )
            ),
            "files": files,
            "symlinks": links,
            "import_api": api,
            "api_status": "PARTIAL" if api_errors else "STATIC_OBSERVATION" if api else "NOT_FOUND",
            "api_errors": api_errors,
            "dependencies": dependencies,
            "requirements_files": requirements_files,
            "consumers": settings.get("consumers", []),
            "consumer_status": "DECLARED_NOT_VERIFIED" if settings.get("consumers") else "UNKNOWN",
            "provenance": {
                "path": provenance_path or "UNKNOWN",
                "status": "DECLARED_NOT_VERIFIED" if provenance_path else "UNKNOWN",
                "evidence_sha256": evidence_files.get(provenance_path),
            },
            "applicability": {
                "path": context_path or "UNKNOWN",
                "context": asdict(context),
                "profiles": context.profiles(),
                "status": "REVIEW_REQUIRED",
                "policy_evaluation": "NOT_EXECUTED",
            },
            "status": "REVIEW_REQUIRED",
        }

    def inspect(self) -> dict[str, Any]:
        """Produce an observed package/dependency catalog without changing disk or code."""
        config, members = self._configuration()
        settings = {item["path"]: item for item in config.get("package", [])}
        packages = [
            self._package(
                path, set(members), settings.get(path.relative_to(self.root).as_posix(), {})
            )
            for path in members
        ]
        names = [package["canonical_name"] for package in packages]
        if len(names) != len(set(names)):
            raise WorkspaceError("Duplicate canonical distribution names")
        graph: dict[str, list[str]] = {name: [] for name in names}
        edges = []
        for package in packages:
            for dependency in package["dependencies"]:
                if dependency["name"] in graph:
                    edge = {
                        "consumer": package["canonical_name"],
                        "provider": dependency["name"],
                        "group": dependency["group"],
                        "conditional": dependency["conditional"],
                    }
                    edges.append(edge)
                    if dependency["group"] == "runtime" and dependency["conditional"] == "FALSE":
                        graph[package["canonical_name"]].append(dependency["name"])
        cycles: list[list[str]] = []
        visited: set[str] = set()

        def visit(name: str, stack: list[str]) -> None:
            if name in stack:
                cycles.append(stack[stack.index(name) :] + [name])
            elif name not in visited:
                for target in graph[name]:
                    visit(target, stack + [name])
                visited.add(name)

        for name in names:
            visit(name, [])
        try:
            revision = run(["git", "rev-parse", "HEAD"], self.root).strip()
        except RuntimeError:
            revision = "UNKNOWN"
        fingerprint = digest(json.dumps({"config": config, "packages": packages}, sort_keys=True))
        return {
            "schema_version": 1,
            "status": "FAIL" if cycles else "REVIEW_REQUIRED",
            "source_sha256": fingerprint,
            "commit_sha": revision,
            "configuration": "auditcore-workspace.toml" if config else "DEFAULT_DISCOVERY",
            "packages": packages,
            "internal_dependencies": edges,
            "runtime_cycles": cycles,
            "conditional_dependencies_status": "REVIEW_REQUIRED"
            if any(e["conditional"] == "UNKNOWN" for e in edges)
            else "NONE_OBSERVED",
            "build_verification": "NOT_EXECUTED",
            "policy_evaluation": "NOT_EXECUTED",
        }

    def inventory(self) -> dict[str, Any]:
        """Atomically persist an immutable source/revision snapshot and current pointer."""
        result = self.inspect()
        snapshot = digest(result["commit_sha"] + result["source_sha256"])
        result["observed_at"] = now()
        result["snapshot_id"] = snapshot
        location = self.state / "snapshots" / (snapshot + ".json")
        if not location.exists():
            write_json(location, result)
        else:
            result = read_json(location)
        write_json(self.state / "current.json", {"snapshot_id": snapshot})
        return result

    def status(self) -> dict[str, Any]:
        """Compare live inputs against persisted evidence; never update stale evidence."""
        pointer = self.state / "current.json"
        if not pointer.exists():
            return {
                "status": "NOT_INVENTORIED",
                "packages": [],
                "policy_evaluation": "NOT_EXECUTED",
            }
        identifier = read_json(pointer)["snapshot_id"]
        if not re.fullmatch(r"[0-9a-f]{64}", identifier):
            raise WorkspaceError("Invalid workspace snapshot identity")
        saved = read_json(self.state / "snapshots" / (identifier + ".json"))
        current = self.inspect()
        fresh = all(saved[key] == current[key] for key in ("source_sha256", "commit_sha"))
        return {
            **saved,
            "status": saved["status"]
            if fresh and saved["status"] == "FAIL"
            else "CURRENT"
            if fresh
            else "STALE",
            "freshness": "CURRENT" if fresh else "STALE",
            "inventory_status": saved["status"],
            "current_source_sha256": current["source_sha256"],
            "current_commit_sha": current["commit_sha"],
        }
