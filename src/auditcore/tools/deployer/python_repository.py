"""Build trusted Python projects and prepare local hash-bound package repositories."""

from __future__ import annotations

import email.parser
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

from auditcore.tools.common import digest, write_json
from auditcore.tools.deployer.library import _wheel_payload
from auditcore.tools.quality.supplychain import wheel_sbom


def _empty_output(output: Path) -> Path:
    """Reserve an explicitly empty directory without following output symlinks."""
    if output.is_symlink() or any(parent.is_symlink() for parent in output.parents):
        raise ValueError("Output path must not traverse symlinks")
    output = output.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Output directory must be empty; choose a new release directory")
    output.mkdir(parents=True, exist_ok=True)
    return output


def _copy_source(source: Path, destination: Path) -> str:
    """Snapshot build inputs, excluding generated data and external symlink targets."""
    excluded = {
        ".git",
        ".venv",
        "venv",
        ".auditcore",
        "dist",
        "build",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
    }
    hashes = {}
    for directory, folders, filenames in os.walk(source):
        folders[:] = [
            name for name in folders if name not in excluded and not name.endswith(".egg-info")
        ]
        for name in folders:
            if (Path(directory) / name).is_symlink():
                raise ValueError("Build source may not contain symlink directories")
        for name in filenames:
            path = Path(directory) / name
            relative = path.relative_to(source)
            if path.suffix in {".pyc", ".pyo"}:
                continue
            if path.is_symlink() and not path.resolve().is_relative_to(source):
                raise ValueError("Build source symlink escapes source project")
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            content = path.read_bytes()
            target.write_bytes(content)
            hashes[relative.as_posix()] = digest(content)
    return digest(json.dumps(hashes, sort_keys=True))


def _validate_sdist(path: Path, distribution: str, version: str) -> None:
    """Inspect sdist members and identity without extracting untrusted archive paths."""
    expected_root = f"{distribution.replace('-', '_')}-{version}"
    if path.name != f"{expected_root}.tar.gz":
        raise ValueError("Source distribution filename mismatch")
    with tarfile.open(path, "r:gz") as archive:
        seen = set()
        members = archive.getmembers()
        if sum(member.size for member in members) > 100 * 1024 * 1024:
            raise ValueError("Source distribution exceeds size limit")
        for member in members:
            name = PurePosixPath(member.name)
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in member.name
                or not name.parts
                or name.parts[0] != expected_root
                or name.as_posix() != member.name
                or member.name in seen
                or not (member.isfile() or member.isdir())
            ):
                raise ValueError("Unsafe source distribution member")
            seen.add(member.name)
        handle = archive.extractfile(f"{expected_root}/PKG-INFO")
        if handle is None:
            raise ValueError("Source distribution metadata missing")
        metadata = email.parser.BytesParser().parsebytes(handle.read())
        if (
            re.sub(r"[-_.]+", "-", metadata.get("Name", "")).lower() != distribution
            or metadata["Version"] != version
        ):
            raise ValueError("Source distribution metadata mismatch")


def build_python_package(
    source: Path,
    output: Path,
    *,
    source_date_epoch: int,
    allow_unreviewed_license: bool = False,
) -> dict[str, Any]:
    """Build wheel and sdist using installed build tools, never auto-installing a backend."""
    if source_date_epoch <= 0:
        raise ValueError("A positive reproducible source_date_epoch is required")
    source = source.resolve()
    project = tomllib.loads((source / "pyproject.toml").read_text()).get("project", {})
    name, version = project.get("name", ""), project.get("version", "")
    normalized = re.sub(r"[-_.]+", "-", name).lower()
    if not re.fullmatch(r"auditcore(?:-[a-z][a-z0-9]*(?:-[a-z0-9]+)*)?", normalized):
        raise ValueError("Expected an explicitly named auditcore distribution")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", version):
        raise ValueError("Build requires an explicit stable numeric project version")
    if importlib.util.find_spec("build") is None:
        raise RuntimeError("Python build is not configured; install auditcore[deploy]")
    output = _empty_output(output)
    with tempfile.TemporaryDirectory(prefix="auditcore-python-build-") as temporary:
        work = Path(temporary)
        snapshot = work / "source"
        source_hash = _copy_source(source, snapshot)
        artifacts = work / "artifacts"
        command = [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--wheel",
            "--sdist",
            "--outdir",
            str(artifacts),
            str(snapshot),
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
            env={**os.environ, "SOURCE_DATE_EPOCH": str(source_date_epoch), "PIP_NO_INDEX": "1"},
        )
        if result.returncode:
            raise RuntimeError(
                "Python build failed; install declared build-system requirements locally "
                f"(exit={result.returncode}, output_sha256={digest(result.stdout + result.stderr)})"
            )
        wheels, sdists = list(artifacts.glob("*.whl")), list(artifacts.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            raise ValueError("Expected exactly one wheel and one source distribution")
        release = _wheel_payload(wheels[0], allow_unreviewed_license=allow_unreviewed_license)
        if release.distribution != normalized or release.version != version:
            raise ValueError("Built wheel differs from requested project metadata")
        _validate_sdist(sdists[0], normalized, version)
        for artifact in (wheels[0], sdists[0]):
            shutil.copyfile(artifact, output / artifact.name)
    wheel = output / wheels[0].name
    sdist = output / sdists[0].name
    sbom = wheel_sbom(wheel, output / f"{wheel.stem}_sbom.json")
    manifest: dict[str, Any] = {
        "status": "PYTHON_ARTIFACTS_BUILT",
        "distribution": normalized,
        "version": version,
        "source_digest": source_hash,
        "source_date_epoch": source_date_epoch,
        "wheel": str(wheel),
        "wheel_sha256": digest(wheel.read_bytes()),
        "sdist": str(sdist),
        "sdist_sha256": digest(sdist.read_bytes()),
        "sbom": sbom,
        "runtime_requirements": release.dependencies,
        "optional_requirements": release.extras,
        "license_expression": release.license_expression,
        "license_status": release.license_status,
        "release_authorization": "REVIEW_REQUIRED",
        "publication": "NOT_EXECUTED",
        "build_isolation": "PREINSTALLED_BACKEND_NO_AUTOMATIC_DOWNLOADS",
        "installation_test": "NOT_EXECUTED",
    }
    write_json(output / "python-build-manifest.json", manifest)
    return manifest


def build_pip_index(
    wheels: list[Path],
    output: Path,
    *,
    allow_unreviewed_license: bool = False,
) -> dict[str, Any]:
    """Prepare a local Simple API index with validated wheels and SHA256 URL fragments."""
    if not wheels:
        raise ValueError("At least one wheel is required")
    validated = []
    names = set()
    for wheel in wheels:
        if wheel.is_symlink() or not wheel.is_file():
            raise ValueError("Index inputs must be regular wheel files")
        if wheel.name in names:
            raise ValueError("Duplicate wheel filename in package repository")
        names.add(wheel.name)
        validated.append(
            (wheel, _wheel_payload(wheel, allow_unreviewed_license=allow_unreviewed_license))
        )
    output = _empty_output(output)
    packages = output / "packages"
    packages.mkdir()
    simple = output / "simple"
    simple.mkdir()
    by_project: dict[str, list[str]] = {}
    artifacts = []
    for wheel, release in validated:
        content = wheel.read_bytes()
        sha = digest(content)
        if sha != release.wheel_sha256:
            raise ValueError("Wheel changed after validation")
        (packages / wheel.name).write_bytes(content)
        link = f"../../packages/{wheel.name}#sha256={sha}"
        by_project.setdefault(release.distribution, []).append(
            f'<a href="{html.escape(link, quote=True)}" data-requires-python="&gt;=3.11">'
            f"{html.escape(wheel.name)}</a>"
        )
        artifacts.append(
            {
                "filename": wheel.name,
                "sha256": sha,
                "distribution": release.distribution,
                "version": release.version,
                "runtime_requirements": release.dependencies,
                "optional_requirements": release.extras,
                "license_status": release.license_status,
            }
        )
    prefix = '<!DOCTYPE html>\n<html><head><meta name="pypi:repository-version" content="1.0">'
    prefix += "<title>auditcore local package repository</title></head><body>\n"
    root_links = []
    for distribution, links in sorted(by_project.items()):
        directory = simple / distribution
        directory.mkdir()
        (directory / "index.html").write_text(
            prefix + "\n".join(sorted(links)) + "\n</body></html>\n"
        )
        root_links.append(f'<a href="{distribution}/">{distribution}</a>')
    (simple / "index.html").write_text(prefix + "\n".join(root_links) + "\n</body></html>\n")
    manifest = {
        "status": "LOCAL_INDEX_BUILT",
        "index_url": simple.as_uri() + "/",
        "projects": sorted(by_project),
        "wheels": artifacts,
        "release_authorization": "REVIEW_REQUIRED",
        "publication": "NOT_EXECUTED",
        "dependency_resolution": "NOT_EXECUTED: verified by consumer installation",
        "publication_status": "BLOCKED"
        if any(release.license_status == "REVIEW_REQUIRED" for _, release in validated)
        else "NOT_EXECUTED",
    }
    write_json(output / "index-manifest.json", manifest)
    return manifest
