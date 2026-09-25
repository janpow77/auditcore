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
#: Exactly reviewed source bindings of the extracted packages released under the
#: rights holder's MIT authorization of 2026-09-22 ("die bibliotheken sollen mit
#: sein, die anderen repos nicht"). The provenance of each wheel must list exactly
#: these repository/commit pairs; any other or missing binding fails the release.
EXPECTED_SOURCES: dict[str, frozenset[tuple[str, str]]] = {
    "auditcore_auth": frozenset(
        {
            ("janpow77/audit-portal", "72cc4b1a15fdcd5ee06ef8124d864904cc4e1312"),
            ("janpow77/audit_designer", "ccd65245182982af3ef885a7a6d43583f4f72cbb"),
            ("janpow77/flowinvoice", "5d5d8c5aded2b7eee82c0813994e9efd549277b3"),
            ("janpow77/flowlib", "aca2dc6aad25aea0720312dbcc6da00b0bcba330"),
            ("janpow77/flownavigator", "9dff858d3772e59533886dfbae70c672d574a1d4"),
            ("janpow77/flowsearch", "9ac5e0dd0c2b7363b5a077551e4fb7103f32c697"),
            ("janpow77/qaaudit", "c78be5c86454d457e5c66d0c65b5117a8528d462"),
            ("janpow77/regulierung", "ce76e48c8ad7f1cbe430948158a4e7001a02ba99"),
            ("janpow77/versteigerung", "729f9a10bc5478bd724ef40c1f4cd572e5a3dada"),
        }
    ),
    "auditcore_dataprotection": frozenset(
        {("janpow77/regulierung", "a5d48ea4b90a410210ec25e707781ef9e21ad743")}
    ),
    "auditcore_documents": frozenset(
        {
            ("janpow77/audit_designer", "030a71e083ef0feddc14545b095a4945bc0bbd7a"),
            ("janpow77/flowinvoice", "fb2d18568d2eaf64574d131ceae51a936b9aac02"),
        }
    ),
    "auditcore_entity_matching": frozenset(
        {
            ("janpow77/audit-portal", "ac1ccc779db69492db0c2c154b6ec84fdd1794b1"),
            ("janpow77/audit_designer", "030a71e083ef0feddc14545b095a4945bc0bbd7a"),
            ("janpow77/audit_designer", "1254591156d3bdf6ccdf4050dec7713a61ad4a20"),
            ("janpow77/flowinvoice", "fb2d18568d2eaf64574d131ceae51a936b9aac02"),
            ("janpow77/flowworkshop", "a05bb2143bd96d5e981f9462f05b965e1658be36"),
            ("janpow77/flowworkshop", "3d1cb40221645935c323392d70d84102d05ac7bb"),
            ("janpow77/riskanalysis", "b5c523bf7eaa326153778d9751f176f03d4d56ed"),
        }
    ),
    "auditcore_funding_sources": frozenset(
        {
            ("janpow77/audit_designer", "030a71e083ef0feddc14545b095a4945bc0bbd7a"),
            ("janpow77/flowsearch", "10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4"),
            ("janpow77/flowworkshop", "a05bb2143bd96d5e981f9462f05b965e1658be36"),
        }
    ),
    "auditcore_geo": frozenset(
        {
            ("janpow77/audit_designer", "1254591156d3bdf6ccdf4050dec7713a61ad4a20"),
            ("janpow77/flowsearch", "10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4"),
            ("janpow77/flowworkshop", "3d1cb40221645935c323392d70d84102d05ac7bb"),
            ("janpow77/osint", "d361ddb9a502bb899065e799d50104f306cfdc89"),
        }
    ),
    "auditcore_harvest": frozenset(
        {
            ("janpow77/audit_designer", "030a71e083ef0feddc14545b095a4945bc0bbd7a"),
            ("janpow77/auditdatabase", "bba911e918e102426d4ca2f88fd377fe8ca585e4"),
            ("janpow77/regulierung", "a5d48ea4b90a410210ec25e707781ef9e21ad743"),
        }
    ),
    # Neuimplementierung ohne Quellrepository (Donut-Plan, 2026-09-24): keine Bindung.
    "auditcore_invoicesynth": frozenset(),
    "auditcore_kanban": frozenset(
        {
            ("janpow77/audit_designer", "2c726f3c1481775cd34aeaa83f87137d6ab12ffe"),
            ("janpow77/cockpit", "df203d4c33e786eb8a8ad3fe53b3b7eb9241d406"),
        }
    ),
    "auditcore_legal_sources": frozenset(
        {
            ("janpow77/audit_designer", "030a71e083ef0feddc14545b095a4945bc0bbd7a"),
            ("janpow77/auditdatabase", "bba911e918e102426d4ca2f88fd377fe8ca585e4"),
        }
    ),
    "auditcore_market_indicators": frozenset(
        {("janpow77/krypto", "34d601726227f913548a118e144de5519eee0f3f")}
    ),
    "auditcore_price_analysis": frozenset(
        {("janpow77/regulierung", "853676d2b1ab792395d63c62c9f96d5edcca8c2d")}
    ),
    "auditcore_price_sources": frozenset(
        {("janpow77/regulierung", "853676d2b1ab792395d63c62c9f96d5edcca8c2d")}
    ),
    "auditcore_procurement": frozenset(
        {
            ("janpow77/audit-portal", "d8eefa426826bdecb67036774f3128ae05e7d0d0"),
            ("janpow77/audit_designer", "030a71e083ef0feddc14545b095a4945bc0bbd7a"),
            ("janpow77/flowinvoice", "fb2d18568d2eaf64574d131ceae51a936b9aac02"),
        }
    ),
    "auditcore_registry_sources": frozenset(
        {
            ("janpow77/audit-portal", "ac1ccc779db69492db0c2c154b6ec84fdd1794b1"),
            ("janpow77/audit_designer", "1254591156d3bdf6ccdf4050dec7713a61ad4a20"),
            ("janpow77/flowinvoice", "fb2d18568d2eaf64574d131ceae51a936b9aac02"),
            ("janpow77/flowsearch", "10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4"),
            ("janpow77/flowworkshop", "3d1cb40221645935c323392d70d84102d05ac7bb"),
            ("janpow77/osint", "d361ddb9a502bb899065e799d50104f306cfdc89"),
            ("janpow77/riskanalysis", "b5c523bf7eaa326153778d9751f176f03d4d56ed"),
        }
    ),
    "auditcore_property_sources": frozenset(
        {
            ("janpow77/versteigerung", "e4ad7af0eaee0b151cc5e3358f95b961d7f3a448"),
            ("janpow77/wohnungsmonitor", "76571bfaa3435bfc6858b3cbaae8c4ea3969ef91"),
        }
    ),
    "auditcore_risk": frozenset(
        {
            ("janpow77/audit-portal", "ac1ccc779db69492db0c2c154b6ec84fdd1794b1"),
            ("janpow77/audit_designer", "1254591156d3bdf6ccdf4050dec7713a61ad4a20"),
            ("janpow77/flowinvoice", "fb2d18568d2eaf64574d131ceae51a936b9aac02"),
            ("janpow77/riskanalysis", "b5c523bf7eaa326153778d9751f176f03d4d56ed"),
        }
    ),
    "auditcore_sampling": frozenset(
        {
            ("janpow77/audit-portal", "d8eefa426826bdecb67036774f3128ae05e7d0d0"),
            ("janpow77/flowstat", "d665ac221f50ba1f465b7337bdd4aa218d78ec8a"),
        }
    ),
    "auditcore_statistics": frozenset(
        {
            ("janpow77/flowinvoice", "fb2d18568d2eaf64574d131ceae51a936b9aac02"),
            ("janpow77/flowstat", "d665ac221f50ba1f465b7337bdd4aa218d78ec8a"),
        }
    ),
}
#: Renderer extras with published, hash-locked requirement files and their owner.
#: Other packages may declare extras of the same name; those stay ordinary extras.
RENDERER_OWNERS = {"pdf": "auditcore_invoicegenerator", "excel": "auditcore_reporting"}
PACKAGES = {
    "auditcore_dummygenerator",
    "auditcore_invoicegenerator",
    "auditcore_reporting",
    *EXPECTED_SOURCES,
}


#: Checks every release evidence must contain as executed PASS (plus per-package checks).
REQUIRED_CHECKS = frozenset(
    {
        "installed-platform",
        # Release blocker: the code-quality ratchet must have passed for these packages.
        "code-quality-gate",
        "requirements-install",
        "pip-check",
        "isolated-origins",
        "pip-remove",
        "pip-removed-imports",
        "apt-lifecycle",
        "sign-apt-1",
        "sign-apt-2",
    }
)


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


def _source_bindings(value: Any) -> set[tuple[str, str]]:
    """All repository/commit pairs recorded anywhere in a provenance document."""
    found: set[tuple[str, str]] = set()
    if isinstance(value, dict):
        repository = value.get("repository")
        commit = value.get("commit") or value.get("commit_sha")
        if isinstance(repository, str) and isinstance(commit, str):
            found.add((repository, commit))
        for item in value.values():
            found |= _source_bindings(item)
    elif isinstance(value, list):
        for item in value:
            found |= _source_bindings(item)
    return found


def check_extracted_authorization(name: str, provenance: dict[str, Any]) -> None:
    """Dated USER_AUTHORIZED_MIT statement and exactly the reviewed source commits."""
    authorization = provenance.get("rights", {}).get("authorization", {})
    statement = authorization.get("confirmation")
    if (
        authorization.get("status") != "USER_AUTHORIZED_MIT"
        or authorization.get("date") != "2026-09-22"
        or not isinstance(statement, str)
        or "mit" not in statement.casefold()
        or _source_bindings(provenance) != EXPECTED_SOURCES[name]
    ):
        raise ValueError(f"Source-scoped user MIT authorization missing: {name}")


def prepare_inputs(source: Path, release_version: str) -> dict[str, bytes]:
    """Fail closed before creating assets or signing keys."""
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", release_version):
        raise ValueError("Explicit numeric release version required")
    report = read_json(source / "result.json")
    if report.get("scope") != "REAL_DOMAIN_PACKAGE_INSTALLATION" or report.get("status") != "PASS":
        raise ValueError("Successful real-domain installation report required")
    packages = report.get("packages", [])
    if {p["name"] for p in packages} != PACKAGES or len(packages) != len(PACKAGES):
        raise ValueError("Exactly the reviewed release distributions are required")
    checks = report["checks"]
    required = set(REQUIRED_CHECKS)
    for package in packages:
        name = package["name"]
        distribution = name.replace("_", "-")
        if package["distribution"] != distribution or not re.fullmatch(
            r"[0-9]+\.[0-9]+\.[0-9]+", package["version"]
        ):
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
        version = package["version"]
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
            if name in EXPECTED_SOURCES:
                check_extracted_authorization(
                    name, json.loads(archive.read(f"{name}/provenance.json"))
                )
            elif name != "auditcore_reporting":
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
            "suggests": deb.get("suggests", []),
            "python_path": "/usr/lib/python3/dist-packages",
            "source_digest": build["source_digest"],
            "installation_evidence": "VERIFIED_PIP_AND_APT_INSTALL_UPGRADE_REMOVE",
            "application_release": "NOT_EVALUATED",
        }
        assets[f"{stem}_public-manifest.json"] = (json.dumps(public_deb, indent=2) + "\n").encode()
    return assets


def optional_assets(
    assets: dict[str, bytes], evidence: Path | None, release_version: str
) -> dict[str, bytes]:
    """Require actual installation and lock replay for published renderer extras."""
    import io

    features: dict[str, str] = {}
    wheels: dict[str, dict[str, Any]] = {}
    for name, content in assets.items():
        if name.endswith(".whl"):
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                metadata_name = next(n for n in archive.namelist() if n.endswith("/METADATA"))
                metadata = BytesParser().parsebytes(archive.read(metadata_name))
                package = re.sub(r"[-_.]+", "_", metadata["Name"]).lower()
                if package not in PACKAGES or package in wheels:
                    raise ValueError("Unexpected or duplicate wheel identity")
                wheels[package] = {
                    "name": name,
                    "version": metadata["Version"],
                    "sha256": digest(content),
                    "all_requires": metadata.get_all("Requires-Dist", []),
                    "requires": [r for r in metadata.get_all("Requires-Dist", []) if ";" not in r],
                }
                for extra in set(metadata.get_all("Provides-Extra", [])) & set(RENDERER_OWNERS):
                    if RENDERER_OWNERS[extra] != package:
                        continue  # same extra name, ordinary extra without a published lock
                    if extra in features:
                        raise ValueError("Renderer extra has ambiguous package ownership")
                    features[extra] = package
    if not features:
        return {}
    if evidence is None:
        raise ValueError("Renderer extras require verified optional installation evidence")
    report = read_json(evidence / "result.json")
    if (
        report.get("scope") != "OPTIONAL_RENDERER_INSTALLATION"
        or report.get("status") != "PASS"
        or report.get("release_version") != release_version
        or set(report.get("features", {})) != set(features)
    ):
        raise ValueError("Optional renderer verification does not match the release")
    apt_check = report["checks"].get("apt-renderers", {})
    if apt_check.get("status") != "PASS" or apt_check.get("exit_code") != 0:
        raise ValueError("Actual Debian renderer installation verification required")
    bound_bytes(evidence / "apt-renderers.log", evidence, apt_check["log_sha256"])
    result = {}
    for extra, feature in report["features"].items():
        package = feature["package"]
        if (
            package != features[extra]
            or feature.get("status") != "PASS"
            or feature.get("version") != wheels[package]["version"]
        ):
            raise ValueError("Unexpected renderer package/version or failed verification")
        closure = {package}
        pending = [package]
        while pending:
            for requirement in wheels[pending.pop()]["requires"]:
                match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([0-9.]+)", requirement)
                if not match:
                    raise ValueError("Pinned internal renderer dependency required")
                dependency = re.sub(r"[-_.]+", "_", match[1]).lower()
                if dependency not in wheels or wheels[dependency]["version"] != match[2]:
                    raise ValueError("Missing matching renderer dependency wheel")
                if dependency not in closure:
                    closure.add(dependency)
                    pending.append(dependency)
        expected_wheels = {wheels[p]["name"]: wheels[p]["sha256"] for p in closure}
        if feature.get("wheel_hashes") != expected_wheels:
            raise ValueError("Optional renderer did not verify the exact wheel closure")
        for stage in (
            "install",
            "smoke",
            "independence",
            "pip-check",
            "remove",
            "locked-install",
            "locked-smoke",
        ):
            name = f"{extra}-{stage}"
            check = report["checks"].get(name, {})
            if check.get("status") != "PASS" or check.get("exit_code") != 0:
                raise ValueError("Missing actual renderer verification")
            bound_bytes(evidence / f"{name}.log", evidence, check["log_sha256"])
        filename = f"requirements-{package}-{extra}.txt"
        if feature.get("requirements") != filename:
            raise ValueError("Unexpected optional requirements filename")
        content = bound_bytes(evidence / filename, evidence, feature["requirements_sha256"])
        text = content.decode()
        lines = text.splitlines()
        if lines[:2] != ["--index-url https://pypi.org/simple", "--require-hashes"]:
            raise ValueError("Hash-locked PyPI dependency requirements required")
        base = f"https://github.com/janpow77/auditcore/releases/download/v{release_version}"
        expected_direct = {
            p.replace("_", "-")
            + (f"[{extra}]" if p == package else "")
            + f" @ {base}/{wheels[p]['name']} --hash=sha256:{wheels[p]['sha256']}"
            for p in closure
        }
        dependencies = feature.get("dependencies", {})
        declared_extra_names = {
            re.sub(r"[-_.]+", "-", re.match(r"[A-Za-z0-9_.-]+", r)[0]).lower()
            for r in wheels[package]["all_requires"]
            if r.endswith(f'; extra == "{extra}"') and re.match(r"[A-Za-z0-9_.-]+", r)
        }
        installed_names = set(dependencies) | {p.replace("_", "-") for p in closure}
        if not declared_extra_names or not declared_extra_names.issubset(installed_names):
            raise ValueError("Declared renderer dependencies missing from verified installation")
        if len(lines[2:]) != len(expected_direct) + len(dependencies):
            raise ValueError("Unexpected renderer requirement count")
        remaining = set(lines[2:])
        if not expected_direct.issubset(remaining):
            raise ValueError("Renderer requirement URLs/hashes do not match release wheels")
        remaining -= expected_direct
        observed_dependencies = {}
        for line in remaining:
            match = re.fullmatch(
                r"([a-z0-9][a-z0-9.-]*)==([A-Za-z0-9.!+_-]+)"
                r"(?: --hash=sha256:[0-9a-f]{64})+",
                line,
            )
            if not match or match[1] in observed_dependencies:
                raise ValueError("Invalid or duplicated locked renderer dependency")
            observed_dependencies[match[1]] = match[2]
        if observed_dependencies != dependencies:
            raise ValueError("Renderer dependency lock differs from verified installation")
        result[filename] = content
    result["optional-renderer-verification.json"] = (json.dumps(report, indent=2) + "\n").encode()
    return result


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
    parser.add_argument("--optional-verification-output", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version):
        raise ValueError("Explicit numeric release version required")
    source, output = args.verification_output.resolve(), args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Release assets require a new empty output directory")
    if source == output or source.is_relative_to(output) or output.is_relative_to(source):
        raise ValueError("Release assets must be separate from verification evidence")
    assets = prepare_inputs(source, args.version)
    assets.update(
        optional_assets(
            assets,
            args.optional_verification_output.resolve()
            if args.optional_verification_output
            else None,
            args.version,
        )
    )
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
    package_versions = {
        p["name"]: p["version"] for p in read_json(source / "result.json")["packages"]
    }
    for package in sorted(PACKAGES):
        (output / f"requirements-{package}.txt").write_text(
            wheel_links + f"{package}=={package_versions[package]}\n"
        )
    (output / "requirements-all-locked.txt").write_text(
        wheel_links
        + "--require-hashes\n"
        + "".join(
            f"{package}=={package_versions[package]} --hash=sha256:"
            f"{digest(assets[f'{package}-{package_versions[package]}-py3-none-any.whl'])}\n"
            for package in sorted(PACKAGES)
        )
    )
    manifest = {
        "status": "PREVIEW_ASSETS_PREPARED",
        "publication": "NOT_EXECUTED",
        "public_installation": "NOT_EXECUTED",
        "application_release": "NOT_EVALUATED",
        "version": args.version,
        "package_versions": package_versions,
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
