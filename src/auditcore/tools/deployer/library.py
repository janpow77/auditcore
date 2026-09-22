"""Install the auditcore distribution as a Debian Python library, without app handoffs."""

from __future__ import annotations

import base64
import configparser
import csv
import email.parser
import hashlib
import io
import os
import re
import stat
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from auditcore.tools.common import digest, write_json


@dataclass(frozen=True)
class LibraryWheel:
    """Validated release identity, payload, entrypoints and dependency declarations."""

    distribution: str
    version: str
    info_directory: str
    payload: dict[str, bytes]
    scripts: dict[str, str]
    dependencies: tuple[str, ...]
    extras: tuple[str, ...]
    license_expression: str
    license_status: str
    wheel_sha256: str


def _wheel_payload(wheel: Path, *, allow_unreviewed_license: bool = False) -> LibraryWheel:
    """Validate pure auditcore wheel paths, metadata and every RECORD digest."""
    match = re.fullmatch(
        r"(auditcore(?:_[a-z][a-z0-9_]*)?)-([0-9]+(?:\.[0-9]+)+)-py3-none-any\.whl", wheel.name
    )
    if not match:
        raise ValueError("Expected a stable-version auditcore py3-none-any wheel")
    import_name, version = match[1], match[2]
    distribution = import_name.replace("_", "-")
    info = f"{import_name}-{version}.dist-info"
    wheel_bytes = wheel.read_bytes()
    with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as archive:
        entries = archive.infolist()
        if sum(entry.file_size for entry in entries) > 100 * 1024 * 1024:
            raise ValueError("Wheel payload exceeds library size limit")
        payload: dict[str, bytes] = {}
        for entry in entries:
            name = entry.filename
            path = PurePosixPath(name)
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in name
                or any(ord(character) < 32 for character in name)
                or name != path.as_posix()
                or not path.parts
                or path.parts[0] not in {import_name, info}
                or len(path.parts) < 2
                or stat.S_ISLNK(entry.external_attr >> 16)
                or name in payload
                or entry.is_dir()
                or path.suffix in {".so", ".dll", ".pyd", ".pth"}
            ):
                raise ValueError("Unsafe or unsupported wheel member")
            payload[name] = archive.read(entry)
    required = {f"{info}/{name}" for name in ("RECORD", "WHEEL", "METADATA")}
    if not required.issubset(payload) or f"{import_name}/__init__.py" not in payload:
        raise ValueError("Wheel metadata or distribution import package missing")
    record_path = f"{info}/RECORD"
    rows = list(csv.reader(io.StringIO(payload[record_path].decode())))
    if any(len(row) != 3 for row in rows):
        raise ValueError("Invalid wheel RECORD row")
    if len(rows) != len(payload) or {row[0] for row in rows} != set(payload):
        raise ValueError("Wheel RECORD membership mismatch")
    for row in rows:
        name, expected, size = row
        if name == record_path:
            if expected or size:
                raise ValueError("RECORD must not hash itself")
            continue
        content = payload[name]
        encoded = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
        if expected != f"sha256={encoded.decode()}" or size != str(len(content)):
            raise ValueError("Wheel RECORD digest mismatch")
    metadata = email.parser.BytesParser().parsebytes(payload[f"{info}/METADATA"])
    wheel_metadata = email.parser.BytesParser().parsebytes(payload[f"{info}/WHEEL"])
    if (
        re.sub(r"[-_.]+", "-", metadata.get("Name", "")).lower() != distribution
        or metadata["Version"] != version
    ):
        raise ValueError("Wheel distribution metadata mismatch")
    if metadata["Requires-Python"] != ">=3.11":
        raise ValueError("Python metadata requires packaging review")
    license_expression = metadata.get("License-Expression", "UNKNOWN")
    license_status = (
        "DECLARED_LICENSE_PRESENT"
        if license_expression in {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause"}
        else "REVIEW_REQUIRED"
    )
    if license_status == "REVIEW_REQUIRED" and not allow_unreviewed_license:
        raise ValueError(
            "License review required; only explicit unreviewed local test builds allowed"
        )
    if wheel_metadata["Root-Is-Purelib"] != "true" or wheel_metadata.get_all("Tag") != [
        "py3-none-any"
    ]:
        raise ValueError("Only platform-independent pure Python wheels are supported")
    dependencies = []
    extras = []
    for requirement in metadata.get_all("Requires-Dist", []):
        if any(token in requirement for token in ("@", "://", "\\", "\r", "\n")) or not re.match(
            r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9_,.-]+\])?(?:[ ;(<>=!~]|$)", requirement
        ):
            raise ValueError("Invalid dependency or unsupported direct URL dependency")
        if re.fullmatch(r'[^;]+; extra == "[a-z][a-z0-9_-]*"', requirement):
            extras.append(requirement)
        else:
            dependencies.append(requirement)
    license_files = metadata.get_all("License-File", [])
    if not license_files:
        license_files = ["LICENSE"]
    if any(f"{info}/licenses/{name}" not in payload for name in license_files):
        raise ValueError("Wheel must include its declared license or notice files")
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(payload.get(f"{info}/entry_points.txt", b"").decode())
    scripts = dict(parser.items("console_scripts")) if parser.has_section("console_scripts") else {}
    for name, target in scripts.items():
        if not re.fullmatch(r"auditcore-[a-z][a-z0-9-]*", name) or not re.fullmatch(
            rf"{re.escape(import_name)}(?:\.[A-Za-z_][A-Za-z0-9_]*)*:[A-Za-z_][A-Za-z0-9_]*", target
        ):
            raise ValueError("Invalid console entrypoint")
        if distribution != "auditcore" and not (
            name == distribution or name.startswith(distribution + "-")
        ):
            raise ValueError("Console script must belong to its distribution")
        module = target.split(":")[0].replace(".", "/")
        if f"{module}.py" not in payload and f"{module}/__init__.py" not in payload:
            raise ValueError("Console entrypoint module missing")
    return LibraryWheel(
        distribution,
        version,
        info,
        payload,
        scripts,
        tuple(dependencies),
        tuple(extras),
        license_expression,
        license_status,
        digest(wheel_bytes),
    )


def build_library_deb(
    wheel: Path,
    output: Path,
    *,
    source_date_epoch: int,
    maintainer: str,
    dependency_mapping: dict[str, str] | None = None,
    allow_unreviewed_license: bool = False,
    debian_revision: int = 1,
) -> dict[str, Any]:
    """Build python3-auditcore from a verified wheel; this is no application release approval."""
    if source_date_epoch <= 0:
        raise ValueError("A positive reproducible source_date_epoch is required")
    if type(debian_revision) is not int or debian_revision < 1:
        raise ValueError("Debian revision must be a positive integer")
    if not re.fullmatch(r"[^\r\n<>]+ <[^\s<>@]+@[^\s<>@]+>", maintainer):
        raise ValueError("Maintainer must be a single Name <email> field")
    release = _wheel_payload(wheel, allow_unreviewed_license=allow_unreviewed_license)
    version, payload, scripts = release.version, release.payload, release.scripts
    mapping = {} if dependency_mapping is None else dependency_mapping
    if not isinstance(mapping, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in mapping.items()
    ):
        raise ValueError(
            "Dependency mapping must be a JSON object of requirement/dependency strings"
        )
    if set(mapping) != set(release.dependencies):
        raise ValueError("Every runtime requirement needs an exact Debian dependency mapping")
    for mapped in mapping.values():
        if not re.fullmatch(
            r"[a-z0-9][a-z0-9+.-]*(?: \((?:>=|<=|=|>>|<<) [0-9][A-Za-z0-9.+:~\-]*\))?", mapped
        ):
            raise ValueError("Invalid Debian dependency mapping")
    depends = ["python3 (>= 3.11)", *sorted(set(mapping.values()))]
    package_name = f"python3-{release.distribution}"
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    debian_version = f"{version}-{debian_revision}"
    package = output / f"{package_name}_{debian_version}_all.deb"
    with tempfile.TemporaryDirectory(prefix="auditcore-library-") as temporary:
        stage = Path(temporary) / "root"
        python_root = stage / "usr/lib/python3/dist-packages"
        for name, content in payload.items():
            destination = python_root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        # dpkg owns installed files; retaining wheel RECORD would claim pip ownership.
        info = python_root / release.info_directory
        (info / "RECORD").unlink()
        (info / "INSTALLER").write_text("deb\n")
        scripts_root = stage / "usr/bin"
        scripts_root.mkdir(parents=True)
        for name, target in scripts.items():
            module, function = target.split(":")
            (scripts_root / name).write_text(
                f"#!/usr/bin/python3\nfrom {module} import {function}\n"
                f"if __name__ == '__main__':\n    raise SystemExit({function}())\n"
            )
        documentation = stage / f"usr/share/doc/{package_name}"
        documentation.mkdir(parents=True)
        licenses = sorted(info.glob("licenses/**/*"))
        copyright_text = f"Upstream-Name: {release.distribution}\nSource: https://github.com/janpow77/auditcore\n\n"
        for license_file in licenses:
            if license_file.is_file():
                copyright_text += (
                    f"License file: {license_file.relative_to(info / 'licenses')}\n"
                    f"{license_file.read_text()}\n\n"
                )
        (documentation / "copyright").write_text(copyright_text)
        (documentation / "README.Debian").write_text(
            "auditcore Python library and CLI entrypoints. No service is installed.\n"
            "Optional quality/build tools are not bundled; install them separately on\n"
            "development/build systems. Application policy and deployment approval\n"
            "remain application-specific; this package grants neither.\n"
        )
        control = stage / "DEBIAN"
        control.mkdir()
        installed_size = (
            sum(p.stat().st_size for p in stage.rglob("*") if p.is_file()) + 1023
        ) // 1024
        (control / "control").write_text(
            f"Package: {package_name}\n"
            f"Version: {debian_version}\nArchitecture: all\nMaintainer: {maintainer}\n"
            f"Section: python\nPriority: optional\nDepends: {', '.join(depends)}\n"
            f"Installed-Size: {installed_size}\n"
            "Homepage: https://github.com/janpow77/auditcore\n"
            f"Description: Python library {release.distribution}\n"
            " Independently installable library maintained in the auditcore repository.\n"
        )
        # Debian's installed Python helpers manage bytecode, without pip or network access.
        (control / "postinst").write_text(
            '#!/bin/sh\nset -eu\nif [ "$1" = configure ]; then\n'
            f"    py3compile -p {package_name}\nfi\n"
        )
        (control / "prerm").write_text(f"#!/bin/sh\nset -eu\npy3clean -p {package_name}\n")
        for path in sorted(stage.rglob("*")):
            path.chmod(
                0o755
                if path.is_dir()
                or path.parent == scripts_root
                or path in {control / "postinst", control / "prerm"}
                else 0o644
            )
            os.utime(path, (source_date_epoch, source_date_epoch))
        os.utime(stage, (source_date_epoch, source_date_epoch))
        result = subprocess.run(
            ["dpkg-deb", "--root-owner-group", "--build", str(stage), str(package)],
            env={**os.environ, "SOURCE_DATE_EPOCH": str(source_date_epoch)},
            capture_output=True,
            check=False,
            timeout=120,
        )
        if result.returncode:
            raise RuntimeError("Library Debian package build failed")
    manifest: dict[str, Any] = {
        "status": "DEB_BUILT",
        "artifact_scope": "PYTHON_LIBRARY",
        "distribution": release.distribution,
        "version": version,
        "debian_version": debian_version,
        "package": str(package),
        "package_sha256": digest(package.read_bytes()),
        "wheel": wheel.name,
        "wheel_sha256": release.wheel_sha256,
        "source_date_epoch": source_date_epoch,
        "python_path": "/usr/lib/python3/dist-packages",
        "depends": depends,
        "dependency_mapping": mapping,
        "optional_requirements_not_bundled": release.extras,
        "console_scripts": scripts,
        "license_expression": release.license_expression,
        "license_status": release.license_status,
        "release_authorization": "REVIEW_REQUIRED",
        "publication_status": "BLOCKED"
        if release.license_status == "REVIEW_REQUIRED"
        else "NOT_EXECUTED",
        "local_test_build_with_unreviewed_license": release.license_status == "REVIEW_REQUIRED",
        "installation_test": "NOT_EXECUTED",
        "application_release_approval": "NOT_APPLICABLE_WITH_REASON",
        "application_release_reason": "Library distribution only; no application or service",
        "apt_publication": "NOT_EXECUTED",
    }
    write_json(output / f"{package.stem}_manifest.json", manifest)
    return manifest
