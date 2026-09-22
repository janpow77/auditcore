"""Verify the released wheel's actual CLIs, migrations and package installation paths."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import venv
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    """Keep all evidence scoped to the wheel and never equate an omitted check with PASS."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--output", type=Path, default=Path(".auditcore/installed-framework"))
    parser.add_argument("--framework", type=Path)
    parser.add_argument("--smoke-only", action="store_true")
    args = parser.parse_args()
    source_wheel = args.wheel.resolve(strict=True)
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="run-", dir=args.output.resolve()))
    # Freeze a single read: concurrent builds may replace the original dist artifact.
    wheel_bytes = source_wheel.read_bytes()
    inputs = output / "input"
    inputs.mkdir()
    wheel = inputs / source_wheel.name
    wheel.write_bytes(wheel_bytes)
    wheel.chmod(0o444)
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    results: dict[str, dict] = {}
    report = {
        "scope": "INSTALLED_PLATFORM_SMOKE" if args.smoke_only else "FRAMEWORK_TECHNICAL_FIXTURES",
        "started_at": datetime.now(UTC).isoformat(),
        "wheel": wheel.name,
        "source_wheel": str(source_wheel),
        "immutable_wheel": str(wheel),
        "wheel_sha256": hashlib.sha256(wheel_bytes).hexdigest(),
        "environment": str(output / "venv"),
        "checks": results,
        "domain_packages_created": 0,
        "real_applications_migrated": 0,
        "publication": "NOT_EXECUTED",
        "status": "RUNNING",
    }

    def save() -> None:
        data = json.dumps(report, indent=2) + "\n"
        (output / "result.json").write_text(data)
        (args.output / "latest.json").write_text(data)

    def check(name: str, command: list[str], timeout: int = 600) -> bool:
        log = output / f"{name}.log"
        with log.open("w") as stream:
            try:
                process = subprocess.run(
                    command,
                    cwd=output,
                    env=environment,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=timeout,
                )
                result = {
                    "status": "PASS" if process.returncode == 0 else "FAIL",
                    "exit_code": process.returncode,
                }
            except (OSError, subprocess.TimeoutExpired) as error:
                result = {"status": "NOT_EXECUTED", "reason": type(error).__name__}
        results[name] = {
            **result,
            "command": command,
            "output_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        }
        save()
        print(name, result["status"], flush=True)
        return result["status"] == "PASS"

    save()
    venv.EnvBuilder(with_pip=True).create(output / "venv")
    binary = output / "venv/bin"
    python = str(binary / "python")
    environment["PATH"] = str(binary) + os.pathsep + environment.get("PATH", "")
    if not check("install", [python, "-m", "pip", "install", "--upgrade", "pip", f"{wheel}[dev]"]):
        report["status"] = "FAIL"
        save()
        return 1
    expected_format = '#,##0.00 "EUR"'
    check(
        "installed_import",
        [
            python,
            "-I",
            "-c",
            "import sys; from pathlib import Path; import auditcore; "
            "from auditcore.reporting import get_number_format; "
            "assert Path(auditcore.__file__).resolve().is_relative_to(Path(sys.prefix)); "
            f"assert get_number_format('Betrag') == {expected_format!r}; "
            "print(auditcore.__file__)",
        ],
    )
    for name in (
        "auditcore-quality",
        "auditcore-bibquality",
        "auditcore-consolidate",
        "auditcore-refactor",
        "auditcore-deploy",
    ):
        check(name + "-help", [str(binary / name), "--help"])
    check(
        "package_inventory",
        [
            str(binary / "auditcore-consolidate"),
            "--state-dir",
            str(output / ".auditcore"),
            "packages",
            "inventory",
            str(root),
        ],
    )
    check(
        "package_status",
        [
            str(binary / "auditcore-consolidate"),
            "--state-dir",
            str(output / ".auditcore"),
            "packages",
            "status",
            str(root),
        ],
    )
    if not args.smoke_only:
        migration = [
            python,
            "-I",
            str(root / "scripts/framework_migration_selfcheck.py"),
            "--output",
            str(output / "migration"),
        ]
        if args.framework:
            migration.extend(["--framework", str(args.framework.resolve())])
        check("migration", migration, 1200)
        check(
            "signed_apt_lifecycle",
            [
                python,
                "-I",
                str(root / "scripts/library_apt_selfcheck.py"),
                "--platform-python",
                python,
                "--platform-wheel",
                str(wheel),
                "--output",
                str(output / "apt"),
            ],
            1200,
        )
    else:
        for name in ("migration", "signed_apt_lifecycle"):
            results[name] = {"status": "NOT_EXECUTED", "reason": "Explicit smoke-only scope"}
    applicable = [
        record["status"]
        for name, record in results.items()
        if not (args.smoke_only and name in {"migration", "signed_apt_lifecycle"})
    ]
    report["status"] = "PASS" if all(status == "PASS" for status in applicable) else "FAIL"
    report["finished_at"] = datetime.now(UTC).isoformat()
    save()
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
