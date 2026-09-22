"""Persistent incremental inventory; errors do not masquerade as a complete scan."""

from __future__ import annotations

import json
import tomllib
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any

from auditcore.tools.common import now, read_json, serializable, write_json
from auditcore.tools.consolidator.analysis import analyze_repository, detect_candidates
from auditcore.tools.consolidator.models import RepositoryRecord
from auditcore.tools.consolidator.providers.protocols import RepositoryProvider


class JsonInventory:
    """Private atomic JSON catalogs with revision metadata."""

    def __init__(self, root: Path = Path(".auditcore/inventory")) -> None:
        self.root = root

    def load(self, name: str) -> Any:
        """Load a catalog, returning an empty list if absent."""
        path = self.root / f"{name}.json"
        pointer = self.root / "current.json"
        if pointer.exists():
            current = read_json(pointer)
            if name in current["catalogs"]:
                path = self.root / "generations" / current["generation"] / f"{name}.json"
        return read_json(path) if path.exists() else []

    def save(self, name: str, data: Any) -> None:
        """Atomically persist a named catalog."""
        if not name.replace("_", "").isalnum():
            raise ValueError("Invalid catalog name")
        write_json(self.root / f"{name}.json", data)

    def commit(self, catalogs: dict[str, Any]) -> None:
        """Publish a consistent catalog generation via one atomic pointer switch."""
        generation = str(uuid.uuid4())
        folder = self.root / "generations" / generation
        for name, data in catalogs.items():
            if not name.replace("_", "").isalnum():
                raise ValueError("Invalid catalog name")
            write_json(folder / f"{name}.json", data)
        # Compatibility exports; programmatic readers always use the generation pointer.
        for name, data in catalogs.items():
            write_json(self.root / f"{name}.json", data)
        write_json(
            self.root / "current.json", {"generation": generation, "catalogs": sorted(catalogs)}
        )


def inspect_metadata(root: Path, record: RepositoryRecord) -> list[dict[str, str]]:
    """Inspect manifests as data; never execute setup.py or install dependencies."""
    dependencies: list[dict[str, str]] = []
    paths = [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    record.file_count = len(paths)
    record.tests = any(p.name.startswith("test_") or "tests" in p.parts for p in paths)
    record.ci = any(".github/workflows" in p.as_posix() for p in paths)
    record.packages = sorted(
        {p.parent.relative_to(root).as_posix() for p in paths if p.name == "__init__.py"}
    )
    for path in paths:
        if path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        items: list[str] = []
        try:
            if path.name == "pyproject.toml":
                data = tomllib.loads(path.read_text())
                project = data.get("project", {})
                items = project.get("dependencies", [])
                record.python_version = project.get("requires-python", "UNKNOWN")
                record.package_managers.append("pyproject")
                if data.get("tool", {}).get("poetry"):
                    items += list(data["tool"]["poetry"].get("dependencies", {}))
                    record.package_managers.append("poetry")
            elif path.name.startswith("requirements") and path.suffix == ".txt":
                items = [
                    line.strip()
                    for line in path.read_text().splitlines()
                    if line.strip() and not line.startswith(("#", "-"))
                ]
                record.package_managers.append("pip")
            elif path.name == "package.json":
                data = json.loads(path.read_text())
                items = [
                    f"{name}@{version}"
                    for name, version in {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {}),
                    }.items()
                ]
                record.package_managers.append("npm")
        except (ValueError, OSError, UnicodeError):
            record.errors.append(f"Unreadable manifest: {relative}")
        dependencies.extend(
            {
                "repository": record.repository,
                "path": relative,
                "dependency": item,
                "commit_sha": record.commit_sha,
                "kind": "declared",
            }
            for item in items
        )
    record.package_managers = sorted(set(record.package_managers))
    record.project_type = (
        "python"
        if record.packages or "Python" in record.languages
        else ("frontend" if "npm" in record.package_managers else "other")
    )
    return dependencies


class GlobalInventory:
    """Two-stage full-account inventory with commit-based incremental reuse."""

    def __init__(self, provider: RepositoryProvider, store: JsonInventory, workers: int = 4):
        self.provider = provider
        self.store = store
        self.workers = workers

    def scan_authenticated_account(self, update: bool = True) -> dict[str, Any]:
        """Discover all repositories, then structurally analyze active code repositories."""
        records = self.provider.repositories()
        previous = {r["repository"]: r for r in self.store.load("repositories")}
        old_symbols = self.store.load("symbols")
        old_dependencies = self.store.load("dependencies")
        # Persist metadata first, so interruption cannot erase discovery evidence.
        self.store.save("repositories_pending", records)
        results: dict[str, dict[str, Any]] = {}

        def scan(record: RepositoryRecord) -> dict[str, Any]:
            """Analyze one immutable revision or reuse the matching persisted catalog."""
            try:
                if record.structural_status == "NOT_APPLICABLE_WITH_REASON":
                    return {"record": asdict(record), "symbols": [], "dependencies": []}
                metadata = getattr(self.provider, "metadata", None)
                if metadata:
                    metadata(record)
                old = previous.get(record.repository)
                if (
                    update
                    and old
                    and old["commit_sha"] == record.commit_sha
                    and (old["structural_status"] in {"COMPLETE", "PARTIAL"})
                ):
                    return {
                        "record": old,
                        "symbols": [s for s in old_symbols if s["repository"] == record.repository],
                        "dependencies": [
                            d for d in old_dependencies if d["repository"] == record.repository
                        ],
                        "cached": True,
                    }
                if record.archived:
                    record.structural_status = "NOT_APPLICABLE_WITH_REASON"
                    record.reason = (
                        "Archived repository: metadata retained, active-code scan excluded"
                    )
                    return {"record": asdict(record), "symbols": [], "dependencies": []}
                root = self.provider.checkout(record)
                dependencies = inspect_metadata(root, record)
                analysis = analyze_repository(root, record.repository, record.commit_sha)
                symbols = serializable(analysis["symbols"])
                record.frameworks = sorted(
                    {dep.split(".")[0] for s in symbols for dep in s["framework_dependencies"]}
                )
                record.errors += analysis["errors"]
                record.structural_status = "PARTIAL" if record.errors else "COMPLETE"
                if not analysis["python_files"]:
                    record.reason = (
                        "No Python sources; manifest catalog only; Graphify for other languages"
                    )
                return {
                    "record": asdict(record),
                    "symbols": symbols,
                    "dependencies": dependencies + analysis["dependencies"],
                    "cached": False,
                }
            except (RuntimeError, OSError, ValueError) as exc:
                record.structural_status = "NOT_EXECUTED"
                record.reason = f"Source analysis failed: {type(exc).__name__}"
                return {"record": asdict(record), "symbols": [], "dependencies": []}

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {pool.submit(scan, record): record.repository for record in records}
            for future in as_completed(futures):
                name = futures[future]
                results[name] = future.result()
                # Pending checkpoint never replaces the published complete generation.
                self.store.save(
                    "repositories_pending",
                    [
                        results[r.repository]["record"] if r.repository in results else asdict(r)
                        for r in records
                    ],
                )
        ordered = [results[r.repository] for r in records]
        symbols = [s for r in ordered for s in r["symbols"]]
        dependencies = [d for r in ordered for d in r["dependencies"]]
        repository_rows = [r["record"] for r in ordered]
        libraries = [
            {
                "repository": r["repository"],
                "packages": r["packages"],
                "commit_sha": r["commit_sha"],
            }
            for r in repository_rows
            if r["packages"]
        ]
        consumers = [
            {
                "provider": d["target"],
                "consumer": d["repository"],
                "source": d["source"],
                "commit_sha": d["commit_sha"],
            }
            for d in dependencies
            if d.get("kind") == "import"
        ]
        candidates = detect_candidates(symbols)
        metadata = {
            "inventory_version": 1,
            "scanner_version": "0.1.0",
            "generated_at": now(),
            "run_id": str(uuid.uuid4()),
            "scan_scope": "GLOBAL",
            "repositories_found": len(records),
            "repositories_complete": sum(
                r["structural_status"] == "COMPLETE" for r in repository_rows
            ),
            "reused": sum(bool(r.get("cached")) for r in ordered),
            "repository_revision": {r["repository"]: r["commit_sha"] for r in repository_rows},
            "discovery_complete": True,
            "analysis_completed": all(
                r["structural_status"] != "NOT_EXECUTED" for r in repository_rows
            ),
            "status": "COMPLETE"
            if all(
                r["structural_status"] in {"COMPLETE", "NOT_APPLICABLE_WITH_REASON"}
                for r in repository_rows
            )
            else "PARTIAL",
            "symbols": len(symbols),
            "candidates": len(candidates),
            "coverage": "Python AST and dependency manifests; dynamic edges unresolved",
        }
        self.store.commit(
            {
                "repositories": repository_rows,
                "symbols": symbols,
                "dependencies": dependencies,
                "libraries": libraries,
                "consumers": consumers,
                "candidates": candidates,
                "inventory_metadata": metadata,
            }
        )
        if not self.store.load("migrations"):
            self.store.save("migrations", [])
        return metadata
