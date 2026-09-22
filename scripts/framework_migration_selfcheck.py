"""Prove installed platform migration using synthetic packages and consumers only."""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.metadata
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from types import ModuleType
from typing import Any

from auditcore.tools.apprefactor.characterization import characterize, compare
from auditcore.tools.apprefactor.engine import REQUIRED_VERIFICATION
from auditcore.tools.apprefactor.models import CharacterizationCase
from auditcore.tools.common import digest, now, read_json, write_json
from auditcore.tools.policy import (
    ApplicabilityContext,
    GitFrameworkPolicyProvider,
    evidence_binding,
)

SCOPE = "TECHNICAL_FIXTURE"
CLASS_SOURCE = '''"""Synthetic deterministic normalization; no business domain or data access."""


class Formatter:
    """Prefix trimmed strings for a technical migration test."""

    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix

    def normalize(self, value: str) -> str:
        """Return the configured prefix and stripped input."""
        return self.prefix + value.strip()
'''
APP_SOURCE = '''"""Synthetic consumer using a separately characterized class."""

from legacy import Formatter


def render(value: str) -> str:
    """Normalize a synthetic display string."""
    return Formatter().normalize(value)
'''
TEST_APPLICATION = '''"""Synthetic application behavior."""

from app import render


def test_application() -> None:
    assert render(" x ") == "x"
    assert render("\\t") == ""
'''
TEST_SHARED = '''"""Actual installed library class behavior."""

from auditcore_fixture import Formatter


def test_installed_class() -> None:
    assert Formatter("!").normalize(" x ") == "!x"
    assert Formatter().normalize("") == ""
'''


def command_run(command: list[str], cwd: Path, *, expected: int = 0) -> dict[str, Any]:
    """Persist real subprocess evidence and reject unexpected exit codes."""
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("PIP_") and key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
    environment["PIP_CONFIG_FILE"] = os.devnull
    process = subprocess.run(
        command, cwd=cwd, env=environment, capture_output=True, text=True, timeout=300, check=False
    )
    result = {
        "command": command,
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "output_sha256": digest(process.stdout + process.stderr),
    }
    log_root = cwd / ".auditcore/selfcheck-commands"
    log_root.mkdir(parents=True, exist_ok=True)
    write_json(log_root / f"{len(list(log_root.glob('*.json'))):04d}.json", result)
    if process.returncode != expected:
        raise RuntimeError(f"Unexpected exit={process.returncode} for {command[0]}; see {log_root}")
    return result


def cli(name: str) -> str:
    """Use the console script from this interpreter's installed environment."""
    path = Path(sys.executable).parent / name
    if not path.is_file():
        raise RuntimeError(f"Installed CLI missing: {name}")
    return str(path)


def module_file(module: ModuleType) -> Path:
    """Require a concrete module source file for installation provenance."""
    if module.__file__ is None:
        raise RuntimeError("Expected a regular installed Python module")
    return Path(module.__file__).resolve()


def fixture_context() -> ApplicabilityContext:
    """Facts for a pure, synthetic CLI consumer without real users or case data."""
    return ApplicabilityContext(
        artifact_type="application",
        data_space="single_project",
        user_model="no_users",
        personal_data="none",
        binding_decisions="none",
        workflow="calculation_only",
        authentication="none",
        uploads=False,
        external_interfaces=False,
        ai_usage="none",
        deployment_target="internal_test",
        protection_need="normal",
        protection_need_source="project_configuration",
        interactive_workspace=False,
        real_data_for_test_generation=False,
        graphical_ui=False,
        international_users=False,
        modular_capabilities=False,
        versioned_artifacts=False,
        versioned_artifact_types=(),
        structured_imports=False,
        analytical_runs=False,
        exports=False,
        documents=False,
        delegation=False,
        dsfa_required=False,
    )


def prove_architecture(root: Path, framework: Path) -> dict[str, Any]:
    """Execute bounded F-09 proof before issuing its source-bound fixture record."""
    from auditcore.tools.policy.framework import context_from_project

    trees = {name: ast.parse((root / name).read_text()) for name in ("app.py", "legacy.py")}
    imports = []
    for name, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                raise RuntimeError("Unexpected dependency in pure synthetic consumer")
            if isinstance(node, ast.ImportFrom):
                if node.module not in {"legacy", "auditcore_fixture"} or node.level:
                    raise RuntimeError("Unexpected import boundary")
                imports.append({"file": name, "module": node.module})
            if isinstance(node, ast.Call):
                allowed = (isinstance(node.func, ast.Name) and node.func.id == "Formatter") or (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"normalize", "strip"}
                )
                if not allowed:
                    raise RuntimeError("Unexpected side effect in synthetic consumer")
    observed = command_run(
        [sys.executable, "-m", "pytest", "tests/test_application.py", "-q"], root
    )
    context = context_from_project(root)
    if context != fixture_context():
        raise RuntimeError("Fixture facts changed; scoped architecture evidence cannot be reused")
    provider = GitFrameworkPolicyProvider(
        framework,
        artifact=root.name,
        artifact_root=root,
        cache=root / ".auditcore/framework-cache.json",
    )
    source = provider.load_requirements()
    if source.source_status != "POLICY_SOURCE_CURRENT":
        raise RuntimeError("Current framework source required")
    proof: dict[str, Any] = {
        "scope": SCOPE,
        "requirement": "F-09",
        "status": "PASS",
        "imports": imports,
        "application_test": observed,
        "source_binding": evidence_binding(root, root.name, context),
        "checked_at": now(),
        "limitations": "Pure synthetic source only; no business or production approval",
    }
    write_json(root / ".auditcore/architecture-test-result.json", proof)
    record = {
        "status": "VERIFIED",
        "source_commit": source.commit_sha,
        **proof["source_binding"],
        "references": [".auditcore/architecture-test-result.json"],
        "scope": SCOPE,
    }
    write_json(root / ".auditcore/policy-evidence.json", {"F-09": record})
    policy = provider.evaluate_project(root)
    if (
        next(row for row in policy.requirements if row.requirement_id == "F-09").gate_status
        != "PASS"
    ):
        raise RuntimeError("Fresh architecture evidence not accepted")
    write_json(root / ".auditcore/framework-policy.json", asdict(policy))
    return proof


def fixture_check(kind: str, root: Path, framework: Path, wheels: Path) -> None:
    """Execute distinct verification categories; never certify missing work."""
    if kind == "framework":
        prove_architecture(root, framework)
    elif kind == "regression":
        target = importlib.import_module("auditcore_fixture")
        result = compare(
            module_file(target).parent.parent,
            "auditcore_fixture:Formatter",
            root / ".auditcore/golden.json",
            module_file(target),
        )
        write_json(root / ".auditcore/regression.json", asdict(result))
        if result.status != "PASS":
            raise RuntimeError("Observed class behavior changed")
    elif kind == "integration":
        sys.path.insert(0, str(root))
        app = importlib.import_module("app")
        target = importlib.import_module("auditcore_fixture")
        origin = module_file(target)
        if (
            not origin.is_relative_to(Path(sys.prefix).resolve())
            or "site-packages" not in origin.parts
        ):
            raise RuntimeError("Replacement not imported from installed wheel")
        if app.Formatter is not target.Formatter or app.render(" x ") != "x":
            raise RuntimeError("Application does not use installed replacement")
        if (root / ".auditcore/inject-integration-failure").exists():
            write_json(
                root / ".auditcore/integration.json",
                {
                    "scope": SCOPE,
                    "status": "FAIL",
                    "injected": True,
                    "import_file": str(origin),
                    "actual_result": app.render(" x "),
                },
            )
            raise RuntimeError("Deliberate synthetic integration failure")
        write_json(
            root / ".auditcore/integration.json",
            {
                "scope": SCOPE,
                "status": "PASS",
                "import_file": str(origin),
                "class_module": app.Formatter.__module__,
                "actual_result": app.render(" x "),
            },
        )
    elif kind == "dependencies":
        wheel = next(wheels.glob("*.whl"))
        wheel_hash = digest(wheel.read_bytes())
        requirement = f"auditcore_fixture==1.0.0 --hash=sha256:{wheel_hash}"
        requirements = (root / "requirements.txt").read_text().splitlines()
        if requirement not in requirements:
            raise RuntimeError("Migration did not add pinned and hashed package requirement")
        index = read_json(wheels.parent / "fixture-index/index-manifest.json")
        install_report = root / ".auditcore/pip-reinstallation.json"
        command_run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--index-url",
                index["index_url"],
                "--force-reinstall",
                "--no-cache-dir",
                "--disable-pip-version-check",
                "--only-binary=:all:",
                "--require-hashes",
                "--report",
                str(install_report),
                "-r",
                "requirements.txt",
            ],
            root,
        )
        installation = read_json(install_report)["install"]
        if len(installation) != 1:
            raise RuntimeError(
                "Expected actual wheel reinstallation, not already-satisfied requirements"
            )
        downloaded = installation[0]["download_info"]
        if downloaded["archive_info"]["hashes"].get("sha256") != wheel_hash or not downloaded[
            "url"
        ].startswith((wheels.parent / "fixture-index/packages").as_uri() + "/"):
            raise RuntimeError(
                "Requirements installation did not use the hash-bound local index wheel"
            )
        command_run([sys.executable, "-m", "pip", "check"], root)
        if importlib.metadata.version("auditcore_fixture") != "1.0.0":
            raise RuntimeError("Installed version differs from requirement")
    elif kind == "quality":
        output = root / ".auditcore/quality.json"
        command_run(
            [
                cli("auditcore-quality"),
                str(root),
                "--project",
                str(root),
                "--artifact",
                root.name,
                "--framework",
                str(framework),
                "--no-external-tools",
                "--output",
                str(output),
            ],
            root,
        )
        report = read_json(output)
        if any(row["status"] == "FAIL" for row in report["findings"]):
            raise RuntimeError("Technical quality gate failed")
        if (
            next(
                row for row in report["policy"]["requirements"] if row["requirement_id"] == "F-09"
            )["gate_status"]
            != "PASS"
        ):
            raise RuntimeError("Quality did not check the bound architecture evidence")
    else:
        raise ValueError(f"Unknown fixture check: {kind}")


def create_package(output: Path) -> Path:
    """Build and install an original synthetic class via the installed deploy CLI."""
    source = output / "fixture-package"
    package = source / "src/auditcore_fixture"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(CLASS_SOURCE)
    (package / "py.typed").write_text("")
    (source / "pyproject.toml").write_text("""[build-system]
requires = ["setuptools>=83", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "auditcore_fixture"
version = "1.0.0"
requires-python = ">=3.11"
license = "MIT"
license-files = ["LICENSE"]
description = "Original synthetic platform installation fixture"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
auditcore_fixture = ["py.typed"]
""")
    # The fixture is original platform test code, covered by this repository's license.
    license_source = Path(__file__).resolve().parents[1] / "LICENSE"
    (source / "LICENSE").write_bytes(license_source.read_bytes())
    (source / "README.md").write_text("Synthetic technical fixture only; not a business library.\n")
    wheels = output / "fixture-artifacts"
    command_run(
        [
            cli("auditcore-deploy"),
            "build-python",
            str(source),
            "--output",
            str(wheels),
            "--source-date-epoch",
            "1700000000",
        ],
        output,
    )
    wheel = next(wheels.glob("*.whl"))
    command_run(
        [
            cli("auditcore-deploy"),
            "pip-index",
            str(wheel),
            "--output",
            str(output / "fixture-index"),
        ],
        output,
    )
    command_run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--force-reinstall",
            str(wheel),
        ],
        output,
    )
    importlib.invalidate_caches()
    return wheels


def create_consumer(output: Path, name: str, framework: Path, wheels: Path) -> tuple[Path, Path]:
    """Prepare known source/outputs and an explicit reviewable CLI migration plan."""
    root = output / name
    tests = root / "tests"
    tests.mkdir(parents=True)
    (root / "legacy.py").write_text(CLASS_SOURCE)
    (root / "app.py").write_text(APP_SOURCE)
    (root / "requirements.txt").write_text(
        "# Synthetic consumer; migration adds its library requirement.\n"
    )
    (tests / "test_application.py").write_text(TEST_APPLICATION)
    (tests / "test_shared.py").write_text(TEST_SHARED)
    write_json(root / "auditcore-context.json", asdict(fixture_context()))
    for command in (
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Synthetic Framework Test"],
        ["git", "config", "user.email", "fixture@example.invalid"],
        ["git", "add", "."],
        ["git", "commit", "-qm", "synthetic consumer baseline"],
    ):
        command_run(command, root)
    cases = [
        CharacterizationCase("trim", [" x "], {}, method="normalize"),
        CharacterizationCase(
            "prefix", [" y "], {}, method="normalize", constructor_kwargs={"prefix": "!"}
        ),
        CharacterizationCase("empty", [""], {}, method="normalize"),
        CharacterizationCase("type-error", [7], {}, method="normalize"),
    ]
    characterize(
        root, "legacy:Formatter", cases, root / ".auditcore/golden.json", root / "legacy.py"
    )
    prove_architecture(root, framework)
    if name == "missing-evidence":
        (root / ".auditcore/policy-evidence.json").unlink()
    if name == "stale-evidence":
        with (root / "app.py").open("a") as handle:
            handle.write("\n# New source bytes after architecture proof.\n")
    if name == "rollback":
        (root / ".auditcore/inject-integration-failure").write_text("synthetic deliberate failure")
    plan_path = root / ".auditcore/plan.json"
    command_run(
        [
            cli("auditcore-refactor"),
            "--framework",
            str(framework),
            "plan",
            str(root),
            "--library",
            "auditcore_fixture==1.0.0",
            "--output",
            str(plan_path),
        ],
        root,
    )
    plan = read_json(plan_path)
    target = importlib.import_module("auditcore_fixture")
    plan["files_to_change"] = ["app.py", "requirements.txt"]
    plan["imports_to_change"] = [
        {"path": "app.py", "old": "legacy", "new": "auditcore_fixture", "symbol": "Formatter"}
    ]
    wheel_hash = digest(next(wheels.glob("*.whl")).read_bytes())
    plan["dependencies_to_add"] = [f"auditcore_fixture==1.0.0 --hash=sha256:{wheel_hash}"]
    plan["characterization_checks"] = [
        {
            "path": "legacy.py",
            "characterization": ".auditcore/golden.json",
            "target": "auditcore_fixture:Formatter",
            "target_root": str(module_file(target).parent.parent),
            "target_file": str(module_file(target)),
        }
    ]
    script = str(Path(__file__).resolve())
    helper = [
        sys.executable,
        script,
        "check",
        "--root",
        str(root),
        "--framework",
        str(framework),
        "--wheels",
        str(wheels),
    ]
    commands = {
        kind: [*helper, "--kind", kind]
        for kind in ("regression", "integration", "framework", "dependencies", "quality")
    }
    commands.update(
        {
            "shared_library": [sys.executable, "-m", "pytest", "tests/test_shared.py", "-q"],
            "application_unit": [sys.executable, "-m", "pytest", "tests/test_application.py", "-q"],
            "ruff": [sys.executable, "-m", "ruff", "check", "app.py", "legacy.py", "tests"],
            "typing": [sys.executable, "-m", "mypy", "--strict", "app.py", "legacy.py"],
            "security": [sys.executable, "-m", "bandit", "-q", "-ll", "app.py", "legacy.py"],
        }
    )
    if set(commands) != set(REQUIRED_VERIFICATION):
        raise RuntimeError("Verification contract changed; update fixture categories")
    plan["verification_commands"] = commands
    write_json(plan_path, plan)
    return root, plan_path


def run_selfcheck(output: Path, framework: Path) -> dict[str, Any]:
    """Exercise positive and blocked/rollback CLI paths from an installed wheel."""
    import auditcore

    platform_file = Path(auditcore.__file__).resolve()
    if (
        not platform_file.is_relative_to(Path(sys.prefix).resolve())
        or "site-packages" not in platform_file.parts
    ):
        raise RuntimeError(
            "Run with an isolated interpreter containing the installed platform wheel"
        )
    if output.exists() and any(output.iterdir()):
        raise ValueError("Selfcheck output directory must be empty")
    output.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "scope": SCOPE,
        "status": "RUNNING",
        "platform_file": str(platform_file),
        "python": sys.executable,
        "started_at": now(),
        "business_libraries_created": 0,
        "real_consumers_migrated": 0,
        "publication": "NOT_EXECUTED",
        "checks": {},
    }
    report_path = output / "framework-migration-report.json"
    write_json(report_path, report)
    try:
        wheels = create_package(output)
        for name in ("positive", "missing-evidence", "stale-evidence", "rollback"):
            root, plan = create_consumer(output, name, framework, wheels)
            originals = {
                path: (root / path).read_bytes() for path in ("app.py", "requirements.txt")
            }
            before_binding = evidence_binding(root, root.name, fixture_context())
            command = [cli("auditcore-refactor"), "--framework", str(framework), "apply", str(plan)]
            result = command_run(command, root, expected=0 if name == "positive" else 1)
            outcome = json.loads(result["stdout"])
            if name == "positive":
                if outcome["status"] != "VERIFIED" or len(outcome["verification"]["checks"]) != 10:
                    raise RuntimeError("Migration not actually verified")
                fixture_check("integration", root, framework, wheels)
                record = {
                    "status": "PASS",
                    "migration_status": outcome["status"],
                    "verification": outcome["verification"],
                    "policy_before": outcome["policy_before"],
                    "policy_after": outcome["policy_after"],
                    "integration": read_json(root / ".auditcore/integration.json"),
                    "quality": read_json(root / ".auditcore/quality.json")["status"],
                    "release_authorization": "NOT_EXECUTED",
                }
            else:
                if outcome["status"] != "MIGRATION_BLOCKED":
                    raise RuntimeError("Negative migration unexpectedly succeeded")
                if any((root / path).read_bytes() != value for path, value in originals.items()):
                    raise RuntimeError("Blocked migration did not preserve original bytes")
                if name == "rollback":
                    integration = read_json(root / ".auditcore/integration.json")
                    architecture = read_json(root / ".auditcore/architecture-test-result.json")
                    if integration.get("status") != "FAIL" or not integration.get("injected"):
                        raise RuntimeError("Intended integration failure did not execute")
                    if architecture["source_binding"] == before_binding:
                        raise RuntimeError("Post-migration framework proof did not execute")
                    if evidence_binding(root, root.name, fixture_context()) != before_binding:
                        raise RuntimeError("Rollback did not restore the complete source binding")
                elif "Applicable policy evidence" not in outcome.get("reason", ""):
                    raise RuntimeError("Negative case blocked for an unexpected reason")
                record = {
                    "status": "PASS",
                    "observed_status": outcome["status"],
                    "reason": outcome.get("reason"),
                    "original_bytes_restored": True,
                }
            report["checks"][name] = record
            write_json(report_path, report)
        report["status"] = "PASS"
    except Exception as exc:
        report["status"] = "FAIL"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        report["finished_at"] = now()
        write_json(report_path, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--framework", type=Path, default=Path(".auditcore/framework-source"))
    check = sub.add_parser("check")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--framework", type=Path, required=True)
    check.add_argument("--wheels", type=Path, required=True)
    check.add_argument("--kind", required=True)
    arguments = sys.argv[1:]
    if not arguments or arguments[0].startswith("-"):
        arguments = ["run", *arguments]
    args = parser.parse_args(arguments)
    if args.command == "check":
        fixture_check(
            args.kind, args.root.resolve(), args.framework.resolve(), args.wheels.resolve()
        )
    else:
        report = run_selfcheck(args.output.resolve(), args.framework.resolve())
        print(
            json.dumps(
                {
                    "scope": report["scope"],
                    "status": report["status"],
                    "report": str(args.output / "framework-migration-report.json"),
                }
            )
        )


if __name__ == "__main__":
    main()
