"""Prepare explicit, verified preview assets; never upload or publish them."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import zipfile
from datetime import UTC, datetime
from email.parser import BytesParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {"auditcore_dummygenerator", "auditcore_invoicegenerator", "auditcore_reporting"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def bound_bytes(path: Path, root: Path, expected: str) -> bytes:
    """Read once, reject escapes and bind exactly the bytes later copied."""
    if not path.resolve().is_relative_to(root) or path.is_symlink():
        raise ValueError("Artifact path escapes verification output or is a symlink")
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"Evidence digest mismatch: {path.name}")
    return data


def prepare_inputs(source: Path, version: str) -> dict[str, bytes]:
    """Fail closed before creating assets or signing keys."""
    report = read_json(source / "result.json")
    if report.get("scope") != "REAL_DOMAIN_PACKAGE_INSTALLATION" or report.get("status") != "PASS":
        raise ValueError("Successful real-domain installation report required")
    packages = report.get("packages", [])
    if {p["name"] for p in packages} != PACKAGES or len(packages) != len(PACKAGES):
        raise ValueError("Exactly the three reviewed preview distributions are required")
    checks = report["checks"]
    required = {
        "installed-platform",
        "requirements-install",
        "pip-check",
        "isolated-origins",
        "pip-remove",
        "pip-removed-imports",
        "apt-lifecycle",
        "sign-apt-1",
        "sign-apt-2",
    }
    for package in packages:
        name = package["name"]
        distribution = name.replace("_", "-")
        if package["distribution"] != distribution or package["version"] != version:
            raise ValueError("Unexpected distribution identity or release version")
        required.update(
            {
                f"build-{name}",
                f"pip-smoke-{name}",
                f"deb-{name}-1",
                f"deb-{name}-2",
                f"selective-install-{distribution}",
                f"selective-smoke-{distribution}",
                f"selective-remove-{distribution}",
            }
        )
    for name in sorted(required):
        check = checks.get(name, {})
        if check.get("status") != "PASS" or check.get("exit_code") != 0:
            raise ValueError(f"Executed passing check required: {name}")
        bound_bytes(source / f"{name}.log", source, check["log_sha256"])
    assets: dict[str, bytes] = {}
    for package in packages:
        name = package["name"]
        build = read_json(source / "builds" / name / "python-build-manifest.json")
        if (
            build.get("license_expression") != "MIT"
            or build.get("license_status") != "DECLARED_LICENSE_PRESENT"
            or package.get("license_status") != "DECLARED_LICENSE_PRESENT"
        ):
            raise ValueError(f"Reviewed MIT package required: {name}")
        if build["distribution"] != package["distribution"] or build["version"] != version:
            raise ValueError("Build/report identity mismatch")
        wheel = Path(build["wheel"])
        if wheel.name != f"{name}-{version}-py3-none-any.whl":
            raise ValueError("Unexpected wheel filename")
        wheel_bytes = bound_bytes(wheel, source, package["wheel_sha256"])
        if digest(wheel_bytes) != build["wheel_sha256"]:
            raise ValueError("Wheel installation/build digest mismatch")
        import io

        with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as archive:
            metadata = BytesParser().parsebytes(
                archive.read(f"{name}-{version}.dist-info/METADATA")
            )
            if metadata.get("License-Expression") != "MIT":
                raise ValueError("Wheel itself must declare MIT")
            license_text = archive.read(f"{name}-{version}.dist-info/licenses/LICENSE")
            if b"Permission is hereby granted, free of charge" not in license_text:
                raise ValueError("Actual MIT license text is missing")
            if name != "auditcore_reporting":
                provenance = json.loads(archive.read(f"{name}/provenance.json"))
                authorization = provenance.get("license_authorization") or provenance.get(
                    "rights", {}
                ).get("authorization", {})
                expected_source = {
                    "auditcore_dummygenerator": (
                        "janpow77/flowaudit_testdatengenerator_frontend",
                        "backend/generator.py",
                    ),
                    "auditcore_invoicegenerator": (
                        "janpow77/flowinvoice",
                        "docs/demo_data/generate_demo_invoices.py",
                    ),
                }[name]
                scope = authorization.get("scope", {})
                if (
                    authorization.get("status") != "USER_AUTHORIZED_MIT"
                    or (scope.get("repository"), scope.get("path")) != expected_source
                    or not re.fullmatch(r"[0-9a-f]{40}", scope.get("commit", ""))
                ):
                    raise ValueError("Source-scoped user MIT authorization missing")
        assets[wheel.name] = wheel_bytes
        sbom = build.get("sbom", {})
        if (
            sbom.get("status") != "PASS"
            or sbom.get("validation", {}).get("status") != "PASS"
            or sbom.get("artifact_sha256") != digest(wheel_bytes)
            or sbom.get("artifact") != wheel.name
        ):
            raise ValueError("Validated SBOM for the exact installed wheel required")
        sbom_name = sbom.get("sbom", "")
        if sbom_name != f"{name}-{version}-py3-none-any_sbom.json":
            raise ValueError("Unexpected SBOM filename")
        assets[sbom_name] = bound_bytes(
            source / "builds" / name / sbom_name, source, sbom["sbom_sha256"]
        )
        sdist = Path(build["sdist"])
        if sdist.name != f"{name}-{version}.tar.gz":
            raise ValueError("Unexpected source archive name")
        assets[sdist.name] = bound_bytes(sdist, source, build["sdist_sha256"])
        stem = f"python3-{package['distribution']}_{version}-1_all"
        deb = read_json(source / "apt-1" / f"{stem}_manifest.json")
        if (
            deb.get("wheel_sha256") != digest(wheel_bytes)
            or deb.get("license_expression") != "MIT"
            or deb.get("local_test_build_with_unreviewed_license") is not False
            or deb.get("debian_version") != f"{version}-1"
        ):
            raise ValueError("Debian package is not the licensed, tested wheel revision")
        assets[f"{stem}.deb"] = bound_bytes(
            source / "apt-1" / f"{stem}.deb", source, deb["package_sha256"]
        )
        public_deb = {
            "scope": "PYTHON_LIBRARY_PREVIEW",
            "distribution": package["distribution"],
            "version": version,
            "debian_version": deb["debian_version"],
            "artifact": f"{stem}.deb",
            "artifact_sha256": deb["package_sha256"],
            "wheel": wheel.name,
            "wheel_sha256": digest(wheel_bytes),
            "license_expression": "MIT",
            "depends": deb["depends"],
            "python_path": "/usr/lib/python3/dist-packages",
            "source_digest": build["source_digest"],
            "installation_evidence": "VERIFIED_PIP_AND_APT_INSTALL_UPGRADE_REMOVE",
            "application_release": "NOT_EVALUATED",
        }
        assets[f"{stem}_public-manifest.json"] = (json.dumps(public_deb, indent=2) + "\n").encode()
    return assets


def run(command: list[str], environment: dict[str, str]) -> bytes:
    """Never print key-generation input, inherited secrets or full subprocess output."""
    result = subprocess.run(command, env=environment, capture_output=True, timeout=120, check=False)
    if result.returncode:
        raise RuntimeError(f"Release preparation command failed: {Path(command[0]).name}")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("verification_output", type=Path)
    parser.add_argument("--platform-python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", default="0.1.0")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version):
        raise ValueError("Explicit numeric release version required")
    source, output = args.verification_output.resolve(), args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Release assets require a new empty output directory")
    if source == output or source.is_relative_to(output) or output.is_relative_to(source):
        raise ValueError("Release assets must be separate from verification evidence")
    assets = prepare_inputs(source, args.version)
    python = args.platform_python.absolute()
    environment = {
        k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME", "GNUPGHOME"}
    }
    environment["PATH"] = str(python.parent) + os.pathsep + environment.get("PATH", "")
    run(
        [
            str(python),
            "-I",
            "-c",
            "import auditcore,sys; from pathlib import Path; "
            "p=Path(auditcore.__file__).resolve(); assert p.is_relative_to(Path(sys.prefix)) "
            "and 'site-packages' in p.parts",
        ],
        environment,
    )
    key_home = ROOT / ".auditcore/release-signing"
    if key_home.is_symlink() or output.is_relative_to(key_home) or key_home.is_relative_to(output):
        raise ValueError("Signing keys must remain isolated from release assets")
    key_home.mkdir(parents=True, exist_ok=True, mode=0o700)
    key_home.chmod(0o700)
    environment["GNUPGHOME"] = str(key_home)
    fingerprints = run(["gpg", "--batch", "--with-colons", "--list-secret-keys"], environment)
    if b"sec:" not in fingerprints:
        run(
            [
                "gpg",
                "--batch",
                "--pinentry-mode",
                "loopback",
                "--passphrase",
                "",
                "--quick-generate-key",
                "auditcore preview package signing",
                "ed25519",
                "sign",
                "0",
            ],
            environment,
        )
        fingerprints = run(["gpg", "--batch", "--with-colons", "--list-secret-keys"], environment)
    rows = fingerprints.decode().splitlines()
    if sum(row.startswith("sec:") for row in rows) != 1:
        raise ValueError("Dedicated signing home must contain exactly one release signing key")
    fingerprint = next(row.split(":")[9] for row in rows if row.startswith("fpr:"))
    for path in key_home.rglob("*"):
        if path.is_symlink():
            raise ValueError("Unexpected signing-home symlink")
        if path.is_dir():
            path.chmod(0o700)
        elif path.is_file():
            path.chmod(0o600)
    output.mkdir(parents=True, exist_ok=True)
    for name, content in assets.items():
        (output / name).write_bytes(content)
    (output / "auditcore-preview-keyring.gpg").write_bytes(
        run(["gpg", "--batch", "--export", fingerprint], environment)
    )
    result = json.loads(
        run(
            [
                str(python.parent / "auditcore-deploy"),
                "apt-repo",
                "build",
                str(output),
                "--signing-key",
                fingerprint,
            ],
            environment,
        )
    )
    if result.get("status") != "PASS":
        raise ValueError("Signed APT metadata build did not pass")
    base = f"https://github.com/janpow77/auditcore/releases/download/v{args.version}"
    wheel_links = "--no-index\n" + "".join(
        f"--find-links {base}/{name}#sha256={digest(content)}\n"
        for name, content in sorted(assets.items())
        if name.endswith(".whl")
    )
    for package in sorted(PACKAGES):
        (output / f"requirements-{package}.txt").write_text(
            wheel_links + f"{package}=={args.version}\n"
        )
    (output / "requirements-all-locked.txt").write_text(
        wheel_links
        + "--require-hashes\n"
        + "".join(
            f"{package}=={args.version} --hash=sha256:"
            f"{digest(assets[f'{package}-{args.version}-py3-none-any.whl'])}\n"
            for package in sorted(PACKAGES)
        )
    )
    manifest = {
        "status": "PREVIEW_ASSETS_PREPARED",
        "publication": "NOT_EXECUTED",
        "public_installation": "NOT_EXECUTED",
        "application_release": "NOT_EVALUATED",
        "version": args.version,
        "prepared_at": datetime.now(UTC).isoformat(),
        "verification_report_sha256": digest((source / "result.json").read_bytes()),
        "signing_key_fingerprint": fingerprint,
        "proposed_base_url": base,
        "assets": {p.name: digest(p.read_bytes()) for p in sorted(output.iterdir()) if p.is_file()},
    }
    (output / "preview-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "SHA256SUMS").write_text(
        "".join(
            f"{digest(p.read_bytes())}  {p.name}\n" for p in sorted(output.iterdir()) if p.is_file()
        )
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "output": str(output),
                "signing_key_fingerprint": fingerprint,
                "publication": "NOT_EXECUTED",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
