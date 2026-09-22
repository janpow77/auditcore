"""Build real domain packages through installed auditcore and verify pip/APT consumers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import venv
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    """Bind reports to the exact tested artifact."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    """Use an explicit installed platform; never infer publication from installation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", nargs="+", type=Path)
    parser.add_argument("--platform-python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-unreviewed-license", action="store_true")
    parser.add_argument("--apt", action="store_true")
    parser.add_argument("--image", default="auditcore-package-test:bookworm")
    args = parser.parse_args()
    # Preserve the venv executable path: resolving its symlink loses its environment.
    platform_python = args.platform_python.absolute()
    cli = platform_python.parent / "auditcore-deploy"
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose an empty verification output directory")
    output.mkdir(parents=True, exist_ok=True)
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONPATH", "PYTHONHOME"} and not key.startswith("PIP_")
    }
    environment["PATH"] = str(platform_python.parent) + os.pathsep + environment.get("PATH", "")
    checks: dict[str, Any] = {}
    report: dict[str, Any] = {
        "scope": "REAL_DOMAIN_PACKAGE_INSTALLATION",
        "status": "RUNNING",
        "started_at": datetime.now(UTC).isoformat(),
        "checks": checks,
        "publication": "NOT_EXECUTED",
        "application_migration": "NOT_EVALUATED",
        "release_authorization": "REVIEW_REQUIRED",
        "packages": [],
    }

    def save() -> None:
        (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name: str, command: list[str], *, env: dict[str, str] | None = None) -> str:
        log = output / f"{name}.log"
        try:
            process = subprocess.run(
                command,
                cwd=output,
                env=env or environment,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
            log.write_text(process.stdout + process.stderr)
            checks[name] = {
                "status": "PASS" if process.returncode == 0 else "FAIL",
                "exit_code": process.returncode,
                "command": command,
                "log_sha256": sha256(log),
            }
            save()
            if process.returncode:
                raise RuntimeError(f"{name} failed; see {log}")
            print(name, "PASS", flush=True)
            return process.stdout
        except (OSError, subprocess.TimeoutExpired) as error:
            checks[name] = {"status": "NOT_EXECUTED", "reason": type(error).__name__}
            save()
            raise

    license_option = ["--allow-unreviewed-license"] if args.allow_unreviewed_license else []
    try:
        run(
            "installed-platform",
            [
                str(platform_python),
                "-I",
                "-c",
                "import sys; from pathlib import Path; import auditcore; "
                "p=Path(auditcore.__file__).resolve(); "
                "assert p.is_relative_to(Path(sys.prefix)) and 'site-packages' in p.parts; "
                "print(p)",
            ],
        )
        wheels = []
        for package in args.packages:
            source = package.resolve()
            name = source.name
            if not re.fullmatch(r"auditcore_[a-z][a-z0-9_]*", name):
                raise ValueError("Expected an auditcore domain package directory")
            artifacts = output / "builds" / name
            run(
                f"build-{name}",
                [
                    str(cli),
                    "build-python",
                    str(source),
                    "--output",
                    str(artifacts),
                    "--source-date-epoch",
                    "1700000000",
                    *license_option,
                ],
            )
            manifest = json.loads((artifacts / "python-build-manifest.json").read_text())
            wheel = Path(manifest["wheel"])
            smoke = source / "tests/installed_smoke.py"
            if not smoke.is_file():
                raise ValueError(f"Missing actual installed-domain smoke contract: {name}")
            copied_smoke = output / f"smoke-{name}.py"
            shutil.copyfile(smoke, copied_smoke)
            record = {
                "name": name,
                "distribution": manifest["distribution"],
                "version": manifest["version"],
                "wheel_sha256": sha256(wheel),
                "source_digest": manifest["source_digest"],
                "license_status": manifest["license_status"],
                "runtime_requirements": manifest["runtime_requirements"],
                "smoke_sha256": sha256(copied_smoke),
            }
            report["packages"].append(record)
            wheels.append(wheel)
        index = output / "pip-index"
        run(
            "pip-index",
            [str(cli), "pip-index", *map(str, wheels), "--output", str(index), *license_option],
        )
        requirements = output / "requirements.txt"
        requirements.write_text(
            "".join(
                f"{p['distribution']}=={p['version']} --hash=sha256:{p['wheel_sha256']}\n"
                for p in report["packages"]
            )
        )
        consumer = output / "consumer"
        venv.EnvBuilder(with_pip=True).create(consumer)
        python = str(consumer / "bin/python")
        run(
            "requirements-install",
            [
                python,
                "-I",
                "-m",
                "pip",
                "--isolated",
                "install",
                "--index-url",
                (index / "simple").as_uri() + "/",
                "--require-hashes",
                "--only-binary=:all:",
                "--no-cache-dir",
                "--disable-pip-version-check",
                "--report",
                str(output / "pip-install.json"),
                "-r",
                str(requirements),
            ],
        )
        install = json.loads((output / "pip-install.json").read_text())["install"]
        if {p["download_info"]["archive_info"]["hashes"]["sha256"] for p in install} != {
            p["wheel_sha256"] for p in report["packages"]
        } or any(
            not p["download_info"]["url"].startswith((index / "packages").as_uri() + "/")
            for p in install
        ):
            raise RuntimeError("Installation did not resolve exactly the local hash-bound wheels")
        run("pip-check", [python, "-I", "-m", "pip", "check"])
        names = [p["name"] for p in report["packages"]]
        origins = (
            "import importlib, importlib.util, sys; from pathlib import Path; "
            "assert importlib.util.find_spec('auditcore') is None; "
            f"modules=[importlib.import_module(n) for n in {names!r}]; "
            "assert all(Path(m.__file__).resolve().is_relative_to(Path(sys.prefix)) "
            "for m in modules); "
            "print([m.__file__ for m in modules])"
        )
        run("isolated-origins", [python, "-I", "-c", origins])
        for name in names:
            run(f"pip-smoke-{name}", [python, "-I", str(output / f"smoke-{name}.py")])
        run("pip-remove", [python, "-I", "-m", "pip", "uninstall", "-y", *names])
        run(
            "pip-removed-imports",
            [
                python,
                "-I",
                "-c",
                "import importlib.util; "
                f"assert all(importlib.util.find_spec(n) is None for n in {names!r})",
            ],
        )
        by_distribution = {p["distribution"]: p for p in report["packages"]}
        for package in report["packages"]:
            selected = package["distribution"]
            expected = {selected}
            pending = [selected]
            while pending:
                for requirement in by_distribution[pending.pop()]["runtime_requirements"]:
                    match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([0-9.]+)", requirement)
                    if not match:
                        raise ValueError("Selective proof requires pinned internal dependencies")
                    dependency = re.sub(r"[-_.]+", "-", match[1]).lower()
                    if dependency not in by_distribution:
                        raise ValueError("Dependency missing from the local package index")
                    if dependency not in expected:
                        expected.add(dependency)
                        pending.append(dependency)
            selected_requirements = output / f"requirements-{selected}.txt"
            selected_requirements.write_text(f"{selected}=={package['version']}\n")
            selected_report = output / f"pip-selected-{selected}.json"
            run(
                f"selective-install-{selected}",
                [
                    python,
                    "-I",
                    "-m",
                    "pip",
                    "--isolated",
                    "install",
                    "--index-url",
                    (index / "simple").as_uri() + "/",
                    "--only-binary=:all:",
                    "--no-cache-dir",
                    "--disable-pip-version-check",
                    "--report",
                    str(selected_report),
                    "-r",
                    str(selected_requirements),
                ],
            )
            installed = json.loads(selected_report.read_text())["install"]
            observed = {
                re.sub(r"[-_.]+", "-", row["metadata"]["name"]).lower() for row in installed
            }
            if observed != expected or {
                row["download_info"]["archive_info"]["hashes"]["sha256"] for row in installed
            } != {by_distribution[name]["wheel_sha256"] for name in expected}:
                raise RuntimeError("Selective install pulled unexpected code or dependencies")
            run(
                f"selective-smoke-{selected}",
                [python, "-I", str(output / f"smoke-{package['name']}.py")],
            )
            run(
                f"selective-remove-{selected}",
                [python, "-I", "-m", "pip", "uninstall", "-y", *sorted(expected)],
            )
            package["selective_installed_distributions"] = sorted(observed)
        if args.apt:
            versions = {p["distribution"]: p["version"] for p in report["packages"]}
            for revision in (1, 2):
                repository = output / f"apt-{revision}"
                for package, wheel in zip(report["packages"], wheels, strict=True):
                    mapping = {}
                    for requirement in package["runtime_requirements"]:
                        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([0-9.]+)", requirement)
                        if not match:
                            raise ValueError(
                                "Selfcheck needs explicit pinned internal dependencies"
                            )
                        normalized = re.sub(r"[-_.]+", "-", match[1]).lower()
                        if versions.get(normalized) != match[2]:
                            raise ValueError("Dependency is not among the verified wheels")
                        mapping[requirement] = f"python3-{normalized} (= {match[2]}-{revision})"
                    mapping_file = output / f"mapping-{package['name']}-{revision}.json"
                    mapping_file.write_text(json.dumps(mapping))
                    run(
                        f"deb-{package['name']}-{revision}",
                        [
                            str(cli),
                            "build-library",
                            str(wheel),
                            "--output",
                            str(repository),
                            "--maintainer",
                            "Local Package Verification <packages@example.invalid>",
                            "--source-date-epoch",
                            "1700000000",
                            "--debian-revision",
                            str(revision),
                            "--dependency-mapping",
                            str(mapping_file),
                            *license_option,
                        ],
                    )
            with tempfile.TemporaryDirectory(prefix="auditcore-domain-test-key-") as temporary:
                key_home = Path(temporary)
                key_home.chmod(0o700)
                signing_env = {**environment, "GNUPGHOME": str(key_home)}
                try:
                    run(
                        "create-test-key",
                        [
                            "gpg",
                            "--batch",
                            "--pinentry-mode",
                            "loopback",
                            "--passphrase",
                            "",
                            "--quick-generate-key",
                            "Local Package Test <packages@example.invalid>",
                            "rsa2048",
                            "sign",
                            "1d",
                        ],
                        env=signing_env,
                    )
                    listing = run(
                        "test-key-fingerprint",
                        ["gpg", "--batch", "--with-colons", "--list-keys"],
                        env=signing_env,
                    )
                    fingerprint = next(
                        line.split(":")[9]
                        for line in listing.splitlines()
                        if line.startswith("fpr:")
                    )
                    run(
                        "export-test-key",
                        [
                            "gpg",
                            "--batch",
                            "--output",
                            str(output / "test-keyring.gpg"),
                            "--export",
                            fingerprint,
                        ],
                        env=signing_env,
                    )
                    for revision in (1, 2):
                        run(
                            f"sign-apt-{revision}",
                            [
                                str(cli),
                                "apt-repo",
                                "build",
                                str(output / f"apt-{revision}"),
                                "--signing-key",
                                fingerprint,
                            ],
                            env=signing_env,
                        )
                finally:
                    subprocess.run(
                        ["gpgconf", "--homedir", str(key_home), "--kill", "gpg-agent"],
                        capture_output=True,
                        check=False,
                    )
            # Signatures require only the public key; temporary private key is already deleted.
            package_names = ["python3-" + p["distribution"] for p in report["packages"]]
            commands = [
                "#!/bin/sh",
                "set -eu",
                "unset PYTHONPATH PYTHONHOME",
                "cd /tmp",
                "rm -f /etc/apt/sources.list /etc/apt/sources.list.d/*",
            ]
            for revision in (1, 2):
                commands.append(
                    f"printf '%s\\n' 'deb [signed-by=/packages/test-keyring.gpg] "
                    f"file:/packages/apt-{revision} ./' > /etc/apt/sources.list.d/auditcore.list"
                )
                commands.append("apt-get -o APT::Update::Error-Mode=any update")
                versions_to_install = [
                    f"python3-{p['distribution']}={p['version']}-{revision}"
                    for p in report["packages"]
                ]
                commands.append("apt-get install -y " + shlex.join(versions_to_install))
                for package in report["packages"]:
                    commands.append(
                        "test \"$(dpkg-query -W -f='${Version}' "
                        f'python3-{package["distribution"]})" '
                        f"= {shlex.quote(package['version'] + '-' + str(revision))}"
                    )
                    commands.append(f"/usr/bin/python3 -I /packages/smoke-{package['name']}.py")
                apt_origins = (
                    "import importlib, importlib.util; "
                    "assert importlib.util.find_spec('auditcore') is None; "
                    f"assert all(importlib.import_module(n).__file__.startswith("
                    f"'/usr/lib/python3/dist-packages/') for n in {names!r})"
                )
                commands.append("/usr/bin/python3 -I -c " + shlex.quote(apt_origins))
                commands.append(f"echo APT_REVISION_{revision}_PASS")
            commands.append("apt-get remove -y " + shlex.join(package_names))
            commands.append(
                "/usr/bin/python3 -I -c "
                + shlex.quote(
                    "import importlib.util; "
                    f"assert all(importlib.util.find_spec(n) is None for n in {names!r})"
                )
            )
            commands.append("echo APT_REMOVE_PASS")
            script = output / "apt-lifecycle.sh"
            script.write_text("\n".join(commands) + "\n")
            image = run(
                "apt-image", ["docker", "image", "inspect", args.image, "--format", "{{.Id}}"]
            )
            report["apt_image_digest"] = image.strip()
            transcript = run(
                "apt-lifecycle",
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
                    "/packages/apt-lifecycle.sh",
                ],
            )
            if not all(
                marker in transcript
                for marker in ("APT_REVISION_1_PASS", "APT_REVISION_2_PASS", "APT_REMOVE_PASS")
            ):
                raise RuntimeError("APT lifecycle evidence is incomplete")
            report["apt_upgrade_scope"] = "DEBIAN_PACKAGING_REVISION_1_TO_2_SAME_UPSTREAM_WHEEL"
        else:
            checks["apt-lifecycle"] = {"status": "NOT_EXECUTED", "reason": "--apt not selected"}
        report["status"] = "PASS"
    except Exception as error:
        report["status"] = "FAIL"
        report["failure"] = {"type": type(error).__name__, "message": str(error)}
    report["finished_at"] = datetime.now(UTC).isoformat()
    save()
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
