"""Evidence-based quality engine with policy-first security gates."""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import tomllib
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from auditcore.models import CheckResult, CheckStatus
from auditcore.tools.common import digest, now, read_json, write_json
from auditcore.tools.policy import PolicyEvaluationResult
from auditcore.tools.quality.scanners import (
    api_snapshot,
    architecture,
    documentation_complexity,
    python_sources,
    scan_sensitive,
    text_resources,
)


@dataclass
class QualityReport:
    """Deterministic findings plus explicit external-tool execution records."""

    path: str
    generated_at: str
    source_digest: str
    findings: list[CheckResult]
    ignored: list[CheckResult]
    policy: dict[str, Any] | None
    api: dict[str, dict[str, str]]

    @property
    def status(self) -> str:
        """Aggregate without claiming missing checks passed."""
        statuses = {r.status for r in self.findings}
        for status in (
            CheckStatus.FAIL,
            CheckStatus.REVIEW_REQUIRED,
            CheckStatus.WARNING,
            CheckStatus.NOT_EXECUTED,
            CheckStatus.NOT_CONFIGURED,
        ):
            if status in statuses:
                return status.value
        return "PASS"

    def exit_code(self, strict: bool = False) -> int:
        """Strict rejects technical warnings; unresolved policy stays REVIEW_REQUIRED."""
        bad = {CheckStatus.FAIL}
        if strict:
            bad |= {CheckStatus.WARNING}
        return int(any(f.status in bad for f in self.findings))

    def to_dict(self) -> dict[str, Any]:
        """Serialize with aggregate status."""
        return {**asdict(self), "status": self.status}


def _dependency_diagnostics(output: str) -> str:
    """Expose package/advisory identifiers without copying arbitrary tool output."""

    def identifier(value: object) -> str:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.+!-]{1,120}", value):
            return "[redacted]"
        if any(f.code == "AC-SEC-001" for f in scan_sensitive(value)):
            return "[redacted]"
        return value

    try:
        report = json.loads(output)
        findings = []
        for package in report["dependencies"]:
            for vulnerability in package.get("vulns", []):
                fixes = ",".join(identifier(v) for v in vulnerability["fix_versions"])
                findings.append(
                    f"{identifier(package['name'])} {identifier(package['version'])}: "
                    f"{identifier(vulnerability['id'])}; fixed in {fixes or 'not available'}"
                )
        return "; ".join(dict.fromkeys(findings)) or "No vulnerability details returned"
    except (ValueError, TypeError, KeyError, AttributeError):
        return "Invalid dependency audit JSON; inspect the dedicated CI audit step"


def _external(command: list[str], code: str, cwd: Path) -> CheckResult:
    if not shutil.which(command[0]):
        return CheckResult(code, CheckStatus.NOT_EXECUTED, f"Not installed: {command[0]}")
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=180, check=False
        )
        message = f"{command[0]} exit={result.returncode}"
        if command[0] == "pip-audit" and result.returncode:
            message += ": " + _dependency_diagnostics(result.stdout)
        return CheckResult(
            code,
            CheckStatus.PASS
            if result.returncode == 0
            else CheckStatus.NOT_EXECUTED
            if result.returncode == 2
            else CheckStatus.FAIL,
            message,
            evidence=(" ".join(command),),
        )
    except (OSError, subprocess.TimeoutExpired):
        return CheckResult(code, CheckStatus.NOT_EXECUTED, f"Unavailable/timeout: {command[0]}")


def check(
    root: Path,
    *,
    policy: PolicyEvaluationResult | None = None,
    external: bool = True,
    compare_api: Path | None = None,
    snapshot_path: Path | None = None,
    project: Path | None = None,
    supply_chain_report: Path | None = None,
) -> QualityReport:
    """Run syntax/architecture first; security findings require policy evaluation."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("Quality target must be an existing directory")
    project = (project or Path.cwd()).resolve()
    config_path = project / "pyproject.toml"
    config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    options = config.get("tool", {}).get("auditcore-bibquality", {})
    sources = python_sources(root, options.get("exclude", []))
    resources = text_resources(root, options.get("exclude", []))
    if root.name == "auditcore":
        # Four tool components have their own self-check scopes.
        sources = {name: text for name, text in sources.items() if not name.startswith("tools/")}
        resources = {
            name: text for name, text in resources.items() if not name.startswith("tools/")
        }
    findings: list[CheckResult] = []
    ignored: list[CheckResult] = []
    valid_sources = {}
    policy_data = asdict(policy) if policy else None
    if policy:
        findings.append(
            CheckResult(
                "AC-POL-001",
                CheckStatus(policy.overall_status),
                "Framework applicability evaluated before security gates",
                evidence=(policy.framework_commit,),
            )
        )
    else:
        findings.append(
            CheckResult(
                "AC-POL-001",
                CheckStatus.REVIEW_REQUIRED,
                "Policy evaluation required before security enforcement",
            )
        )
    for path, source in sources.items():
        try:
            tree = ast.parse(source, filename=path)
            valid_sources[path] = source
        except SyntaxError as exc:
            findings.append(
                CheckResult(
                    "AC-SYN-001", CheckStatus.FAIL, "Invalid Python syntax", path, exc.lineno or 0
                )
            )
            continue
        is_core = "tools" not in (root / path).parts
        file_findings = architecture(tree, path, options.get("forbidden-imports", []), is_core)
        file_findings += documentation_complexity(
            tree,
            path,
            detailed=options.get("documentation-details", False),
            bilingual=options.get("bilingual-documentation", False),
        )
        if policy:
            file_findings += scan_sensitive(source, path)
        for finding in file_findings:
            lines = source.splitlines()
            line = lines[finding.line - 1] if finding.line else ""
            file_ignore = f"# auditcore-quality: ignore-file {finding.code}"
            local_ignore = f"# auditcore-quality: ignore {finding.code}"
            # Secret failures may not be suppressed by a source file under inspection.
            if finding.code != "AC-SEC-001" and (
                any(file_ignore in x for x in lines) or local_ignore in line
            ):
                ignored.append(finding)
            else:
                findings.append(finding)
    if policy:
        for path, content in resources.items():
            findings.extend(scan_sensitive(content, path))
    if not sources:
        findings.append(CheckResult("AC-SYN-001", CheckStatus.NOT_EXECUTED, "No Python files"))
    elif not any(f.code == "AC-SYN-001" and f.status == CheckStatus.FAIL for f in findings):
        findings.append(CheckResult("AC-SYN-001", CheckStatus.PASS, f"Parsed {len(sources)} files"))
    snapshot = api_snapshot(valid_sources)
    if snapshot_path:
        write_json(snapshot_path, snapshot)
    if compare_api:
        previous = read_json(compare_api)
        for name, signature in previous.items():
            if snapshot.get(name) != signature:
                findings.append(
                    CheckResult("AC-API-001", CheckStatus.FAIL, f"BREAKING_CHANGE: {name}")
                )
        if not any(f.code == "AC-API-001" for f in findings):
            findings.append(CheckResult("AC-API-001", CheckStatus.PASS, "API baseline preserved"))
    else:
        findings.append(
            CheckResult(
                "AC-API-001", CheckStatus.NOT_EXECUTED, "No API comparison baseline supplied"
            )
        )
    commands = [(["ruff", "check", str(root)], "AC-LINT-001"), (["mypy", str(root)], "AC-TYPE-001")]
    if policy:
        commands += [
            (["bandit", "-q", "-ll", "-r", str(root)], "AC-SEC-002"),
            (["pip-audit", "--format", "json"], "AC-DEP-001"),
        ]
    if external:
        findings.extend(_external(command, code, project) for command, code in commands)
    else:
        findings.extend(
            CheckResult(code, CheckStatus.NOT_EXECUTED, f"External tool disabled: {command[0]}")
            for command, code in commands
        )
    regression_command = options.get("regression-command")
    if external and isinstance(regression_command, list) and regression_command:
        findings.append(_external(regression_command, "AC-TEST-001", project))
    else:
        findings.append(
            CheckResult(
                "AC-TEST-001", CheckStatus.NOT_EXECUTED, "No explicit regression command executed"
            )
        )
    if supply_chain_report and policy:
        supply = read_json(supply_chain_report)
        artifact = supply_chain_report.parent / supply["artifact"]
        sbom = supply_chain_report.parent / supply["sbom"]
        from auditcore.tools.quality.supplychain import validate_schema

        valid = supply.get("status") == "PASS" and (
            digest(artifact.read_bytes()) == supply.get("artifact_sha256")
            and digest(sbom.read_bytes()) == supply.get("sbom_sha256")
            and validate_schema(read_json(sbom))["status"] == "PASS"
        )
        if artifact.suffix == ".whl" and root.is_relative_to(project / "src"):
            prefix = root.relative_to(project / "src").as_posix()
            with zipfile.ZipFile(artifact) as archive:
                valid = valid and all(
                    f"{prefix}/{name}" in archive.namelist()
                    and archive.read(f"{prefix}/{name}") == (root / name).read_bytes()
                    for name in {**sources, **resources}
                )
        else:
            valid = False
        findings.append(
            CheckResult(
                "AC-SUPPLY-001",
                CheckStatus.PASS if valid else CheckStatus.FAIL,
                "Artifact/SBOM digest and schema-validation evidence checked",
                evidence=(str(supply_chain_report),),
            )
        )
    else:
        findings.append(
            CheckResult(
                "AC-SUPPLY-001",
                CheckStatus.REVIEW_REQUIRED if policy else CheckStatus.NOT_EXECUTED,
                "Release artifact/SBOM validation evidence required",
            )
        )
    return QualityReport(
        str(root),
        now(),
        digest(str(sorted({**sources, **resources}.items()))),
        findings,
        ignored,
        policy_data,
        snapshot,
    )
