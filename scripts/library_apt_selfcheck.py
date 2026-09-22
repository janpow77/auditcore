#!/usr/bin/env python3
"""Prove installed platform packaging and signed offline APT lifecycle with technical fixtures."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    """Bind evidence to exact local artifact bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_wheel(directory: Path, version: str, value: int) -> Path:
    """Create a complete technical wheel; this contains no business functionality."""
    name = "auditcore_frameworkfixture"
    info = f"{name}-{version}.dist-info"
    payload = {
        f"{name}/__init__.py": (
            '"""Synthetic technical fixture, not a domain library."""\n'
            f"def value():\n    return {value}\n"
        ).encode(),
        f"{info}/METADATA": (
            "Metadata-Version: 2.4\nName: auditcore-frameworkfixture\n"
            f"Version: {version}\nRequires-Python: >=3.11\nLicense-Expression: MIT\n"
            "License-File: LICENSE\n"
        ).encode(),
        f"{info}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        f"{info}/licenses/LICENSE": (
            b"MIT License\nCopyright (c) 2026 auditcore technical test contributors\n\n"
            b"Permission is hereby granted, free of charge, to any person obtaining a copy\n"
            b"of this software and associated documentation files (the Software), to deal\n"
            b"in the Software without restriction, including without limitation the rights\n"
            b"to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
            b"copies of the Software, and to permit persons to whom the Software is\n"
            b"furnished to do so, subject to the following conditions:\n\n"
            b"The above copyright notice and this permission notice shall be included in all\n"
            b"copies or substantial portions of the Software.\n\n"
            b"THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
            b"IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
            b"FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
            b"AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
            b"LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
            b"OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN\n"
            b"THE SOFTWARE.\n"
        ),
    }
    records = io.StringIO()
    writer = csv.writer(records)
    for member, content in payload.items():
        encoded = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
        writer.writerow((member, "sha256=" + encoded.decode(), len(content)))
    writer.writerow((f"{info}/RECORD", "", ""))
    payload[f"{info}/RECORD"] = records.getvalue().encode()
    path = directory / f"{name}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as archive:
        for member, content in payload.items():
            entry = zipfile.ZipInfo(member, (2023, 11, 14, 22, 13, 20))
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, content)
    return path


def container_script(include_platform: bool) -> str:
    """Use only signed file repositories and the Debian system interpreter."""
    platform = ""
    if include_platform:
        platform = """
apt-get install -y python3-auditcore
/usr/bin/python3 -I - <<'PYTHON_PLATFORM'
import auditcore, auditcore.reporting, sys
assert sys.executable == '/usr/bin/python3'
assert auditcore.__file__.startswith('/usr/lib/python3/dist-packages/')
assert auditcore.reporting.get_number_format('Betrag') == '#,##0.00 "EUR"'
print('PLATFORM_IMPORT_PASS', auditcore.__file__)
PYTHON_PLATFORM
commands="auditcore-quality auditcore-bibquality auditcore-consolidate"
commands="$commands auditcore-refactor auditcore-deploy"
for command in $commands; do
    "$command" --help > /tmp/platform-help
    test -s /tmp/platform-help
done
printf 'PLATFORM_CLI_PASS\\n'
"""
    return (
        """#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME
cd /tmp
# Only this disposable container's APT sources are changed.
rm -f /etc/apt/sources.list
rm -f /etc/apt/sources.list.d/*
aptlist=/etc/apt/sources.list.d/auditcore-test.list
printf 'deb [signed-by=/packages/test-keyring.gpg] file:/packages/repository-v1 ./\\n' > "$aptlist"
apt-get -o APT::Update::Error-Mode=any update
apt-get install -y python3-auditcore-frameworkfixture=1.0.0-1
/usr/bin/python3 -I - <<'PYTHON_V1'
import auditcore_frameworkfixture as fixture, importlib.metadata, sys
assert sys.executable == '/usr/bin/python3'
assert fixture.__file__.startswith('/usr/lib/python3/dist-packages/')
assert fixture.value() == 1
assert importlib.metadata.version('auditcore-frameworkfixture') == '1.0.0'
print('INSTALL_V1_PASS', fixture.__file__)
PYTHON_V1
"""
        + platform
        + """
printf 'deb [signed-by=/packages/test-keyring.gpg] file:/packages/repository-v2 ./\\n' > "$aptlist"
apt-get -o APT::Update::Error-Mode=any update
apt-get install -y python3-auditcore-frameworkfixture=2.0.0-1
/usr/bin/python3 -I - <<'PYTHON_V2'
import auditcore_frameworkfixture as fixture, importlib.metadata
assert fixture.__file__.startswith('/usr/lib/python3/dist-packages/')
assert fixture.value() == 2
assert importlib.metadata.version('auditcore-frameworkfixture') == '2.0.0'
print('UPGRADE_V2_PASS', fixture.__file__)
PYTHON_V2
apt-get remove -y python3-auditcore-frameworkfixture
/usr/bin/python3 -I - <<'PYTHON_REMOVED'
import importlib.util
assert importlib.util.find_spec('auditcore_frameworkfixture') is None
print('REMOVE_PASS')
PYTHON_REMOVED
# APT must reject an index modified after signing.
cp -a /packages/repository-v2 /tmp/tampered-repository
printf 'tampered\\n' >> /tmp/tampered-repository/Packages
printf 'tampered\\n' >> /tmp/tampered-repository/Packages.gz
printf 'deb [signed-by=/packages/test-keyring.gpg] file:/tmp/tampered-repository ./\\n' > "$aptlist"
if apt-get -o APT::Update::Error-Mode=any update > /tmp/tampered.log 2>&1; then
    cat /tmp/tampered.log
    exit 1
fi
printf 'SIGNED_INDEX_TAMPER_REJECTED_PASS\\n'
"""
    )


def main() -> int:
    """Create fresh local artifacts, run offline container checks and persist honest evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform-python", type=Path, default=Path(sys.executable))
    parser.add_argument("--platform-wheel", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", default="auditcore-package-test:bookworm")
    parser.add_argument("--prepare-image", action="store_true")
    args = parser.parse_args()
    output = args.output.absolute()
    if output.is_symlink() or (output.exists() and any(output.iterdir())):
        parser.error("Output must be a new empty directory")
    output.mkdir(parents=True, exist_ok=True)
    python = args.platform_python.absolute()
    cli = python.parent / "auditcore-deploy"
    log: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "scope": "SYNTHETIC_TECHNICAL_FIXTURE",
        "status": "NOT_EXECUTED",
        "started_at": datetime.now(UTC).isoformat(),
        "image": args.image,
        "checks": {},
        "remote_publication": "NOT_EXECUTED",
        "host_apt_install": "NOT_EXECUTED",
        "business_library_created": False,
    }

    def execute(
        command: list[str], *, environment: dict[str, str] | None = None, timeout: int = 300
    ) -> str:
        result = subprocess.run(
            command,
            cwd=output,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        log.append(
            {
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        (output / "commands.json").write_text(json.dumps(log, indent=2) + "\n")
        if result.returncode:
            raise RuntimeError(f"Command failed: {command[0]}, exit={result.returncode}")
        return result.stdout

    try:
        if not cli.is_file():
            raise RuntimeError("auditcore-deploy must exist beside --platform-python")
        proof = execute(
            [
                str(python),
                "-I",
                "-c",
                "import auditcore,importlib.metadata,json; "
                "d=importlib.metadata.distribution('auditcore'); "
                "print(json.dumps({'module':auditcore.__file__,'version':d.version,"
                "'direct_url':json.loads(d.read_text('direct_url.json') or '{}')}))",
            ]
        )
        report["platform"] = json.loads(proof)
        report["platform"]["installation_mode"] = (
            "EDITABLE_DEVELOPMENT"
            if report["platform"]["direct_url"].get("dir_info", {}).get("editable")
            else "INSTALLED_DISTRIBUTION"
        )
        if args.prepare_image:
            execute(
                [
                    str(python),
                    "-I",
                    "-c",
                    "from auditcore.tools.deployer.validation import DockerPackageTester; "
                    "import sys; print(DockerPackageTester(sys.argv[1]).prepare())",
                    args.image,
                ]
            )
        report["image_id"] = execute(
            ["docker", "image", "inspect", args.image, "--format", "{{.Id}}"]
        ).strip()
        artifacts = []
        for label, version, value in (("v1", "1.0.0", 1), ("v2", "2.0.0", 2)):
            wheel = fixture_wheel(output, version, value)
            repository = output / f"repository-{label}"
            build = json.loads(
                execute(
                    [
                        str(cli),
                        "build-library",
                        str(wheel),
                        "--output",
                        str(repository),
                        "--source-date-epoch",
                        "1700000000",
                        "--maintainer",
                        "auditcore Technical Test <packaging@example.invalid>",
                    ]
                )
            )
            artifacts.append(build)
        if args.platform_wheel:
            platform_build = json.loads(
                execute(
                    [
                        str(cli),
                        "build-library",
                        str(args.platform_wheel.absolute()),
                        "--output",
                        str(output / "repository-v1"),
                        "--source-date-epoch",
                        "1700000000",
                        "--maintainer",
                        "auditcore Technical Test <packaging@example.invalid>",
                    ]
                )
            )
            artifacts.append(platform_build)
            package = Path(platform_build["package"])
            shutil.copyfile(package, output / "repository-v2" / package.name)
        report["artifacts"] = artifacts
        with tempfile.TemporaryDirectory(prefix="auditcore-apt-test-key-") as key_directory:
            key_home = Path(key_directory)
            key_home.chmod(0o700)
            environment = {**os.environ, "GNUPGHOME": str(key_home)}
            try:
                execute(
                    [
                        "gpg",
                        "--batch",
                        "--pinentry-mode",
                        "loopback",
                        "--passphrase",
                        "",
                        "--quick-generate-key",
                        "auditcore isolated APT test <apt@example.invalid>",
                        "rsa2048",
                        "sign",
                        "1d",
                    ],
                    environment=environment,
                )
                listing = execute(
                    ["gpg", "--batch", "--with-colons", "--list-keys"], environment=environment
                )
                fingerprint = next(
                    line.split(":")[9] for line in listing.splitlines() if line.startswith("fpr:")
                )
                report["test_signing_fingerprint"] = fingerprint
                execute(
                    [
                        "gpg",
                        "--batch",
                        "--output",
                        str(output / "test-keyring.gpg"),
                        "--export",
                        fingerprint,
                    ],
                    environment=environment,
                )
                (output / "test-keyring.gpg").chmod(0o644)
                for label in ("v1", "v2"):
                    execute(
                        [
                            str(cli),
                            "apt-repo",
                            "build",
                            str(output / f"repository-{label}"),
                            "--signing-key",
                            fingerprint,
                        ],
                        environment=environment,
                    )
                report["checks"]["repository_signatures"] = "PASS"
            finally:
                subprocess.run(
                    ["gpgconf", "--homedir", str(key_home), "--kill", "gpg-agent"],
                    capture_output=True,
                    check=False,
                )
        script = output / "container-test.sh"
        script.write_text(container_script(bool(args.platform_wheel)))
        transcript = execute(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--mount",
                f"type=bind,src={output},dst=/packages,readonly",
                args.image,
                "sh",
                "/packages/container-test.sh",
            ]
        )
        (output / "container-test.log").write_text(transcript)
        markers = {
            "install": "INSTALL_V1_PASS",
            "upgrade": "UPGRADE_V2_PASS",
            "remove": "REMOVE_PASS",
            "signed_index_tamper_rejected": "SIGNED_INDEX_TAMPER_REJECTED_PASS",
        }
        if args.platform_wheel:
            markers.update(platform_import="PLATFORM_IMPORT_PASS", platform_cli="PLATFORM_CLI_PASS")
        for check, marker in markers.items():
            report["checks"][check] = "PASS" if marker in transcript else "FAIL"
        report["status"] = (
            "PASS" if all(value == "PASS" for value in report["checks"].values()) else "FAIL"
        )
        report["container_network"] = "none"
        report["apt_trust"] = "signed-by dedicated temporary test key; no trusted=yes"
        report["keyring_sha256"] = sha256(output / "test-keyring.gpg")
        report["container_script_sha256"] = sha256(script)
        report["container_log_sha256"] = sha256(output / "container-test.log")
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired, StopIteration) as exc:
        report["status"] = "FAIL"
        report["reason"] = str(exc)
    report["completed_at"] = datetime.now(UTC).isoformat()
    if (output / "commands.json").exists():
        report["command_log_sha256"] = sha256(output / "commands.json")
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
