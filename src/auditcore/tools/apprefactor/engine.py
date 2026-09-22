"""Transactional, preconditioned application migration and verification."""

from __future__ import annotations

import ast
import difflib
import json
import os
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from auditcore.exceptions import MigrationBlocked
from auditcore.tools.apprefactor.characterization import compare, execute_cases
from auditcore.tools.apprefactor.models import ApplicationRefactoringPlan
from auditcore.tools.common import (
    DEPLOYMENT_CHECKS,
    digest,
    now,
    read_json,
    run,
    safe_path,
    write_json,
)
from auditcore.tools.consolidator.analysis import analyze_repository, load_policy
from auditcore.tools.policy.framework import GitFrameworkPolicyProvider
from auditcore.tools.workflow import REFACTOR_STATES, StateMachine

REQUIRED_VERIFICATION = tuple(load_policy("quality")["required_verification"])


def source_digest(root: Path) -> str:
    """Fingerprint relevant source/manifests/context, excluding generated state."""
    content: dict[str, str] = {}
    excluded = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".auditcore",
        "__pycache__",
        "build",
        "dist",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "graphify-out",
    }
    for directory, folders, filenames in os.walk(root):
        folders[:] = [
            name for name in folders if name not in excluded and not name.endswith(".egg-info")
        ]
        for name in filenames:
            if name.endswith((".pyc", ".pyo")) or name in {".coverage"}:
                continue
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                content[relative] = digest("symlink:" + os.readlink(path))
            elif relative in {"auditcore-deploy.json", "auditcore-deployment-evidence.json"}:
                configuration = json.loads(path.read_text())
                configuration.pop("source_digest", None)
                content[relative] = digest(json.dumps(configuration, sort_keys=True))
            else:
                content[relative] = digest(path.read_bytes())
    return digest(json.dumps(content, sort_keys=True))


def replace_imports(source: str, old: str, new: str, symbol: str = "") -> str:
    """Rewrite only matching import AST nodes, preserving unrelated source text."""
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    replacements = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != old or node.level:
            continue
        selected = [alias for alias in node.names if not symbol or alias.name == symbol]
        if not selected:
            continue
        remaining = [alias for alias in node.names if alias not in selected]
        import_replacement = ast.ImportFrom(module=new, names=selected, level=0)
        segments = [ast.unparse(import_replacement)]
        if remaining:
            segments.insert(0, ast.unparse(ast.ImportFrom(module=old, names=remaining, level=0)))
        indent = " " * node.col_offset
        text = ("\n" + indent).join(segments)
        replacements.append((node, text))
    for node, replacement in sorted(replacements, key=lambda pair: pair[0].lineno, reverse=True):
        start, end = node.lineno - 1, (node.end_lineno or node.lineno) - 1
        prefix = lines[start][: node.col_offset]
        suffix = lines[end][node.end_col_offset :]
        lines[start : end + 1] = [prefix + replacement + suffix]
    result = "".join(lines)
    ast.parse(result)
    return result


def compatibility_wrapper(source: str, symbol: str, target: str) -> str:
    """Replace a plain function body with a signature-preserving deprecated wrapper."""
    tree = ast.parse(source)
    node = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == symbol), None)
    if node is None or node.decorator_list:
        raise MigrationBlocked("Only plain top-level functions can be wrapped automatically")
    module, name = target.split(":", 1)
    args = node.args.posonlyargs + node.args.args
    positional = [a.arg for a in args]
    if node.args.vararg:
        positional.append("*" + node.args.vararg.arg)
    keywords = [f"{a.arg}={a.arg}" for a in node.args.kwonlyargs]
    if node.args.kwarg:
        keywords.append("**" + node.args.kwarg.arg)
    call = ", ".join(positional + keywords)
    body = (
        '"""Deprecated compatibility wrapper; behavior retained by characterization."""\n'
        f"from {module} import {name} as _auditcore_target\n"
        f"return _auditcore_target({call})\n"
    )
    node.body = ast.parse(body).body
    replacement = ast.unparse(node) + "\n"
    lines = source.splitlines(keepends=True)
    lines[node.lineno - 1 : node.end_lineno] = [replacement]
    return "".join(lines)


def verify(root: Path, commands: dict[str, list[str]]) -> dict[str, Any]:
    """Run each required category; absent checks remain NOT_EXECUTED."""
    results: dict[str, dict[str, Any]] = {}
    for category in REQUIRED_VERIFICATION:
        command = commands.get(category)
        if not command:
            results[category] = {"status": "NOT_EXECUTED", "reason": "No command configured"}
            continue
        try:
            process = subprocess.run(
                command, cwd=root, capture_output=True, text=True, timeout=300, check=False
            )
            results[category] = {
                "status": "PASS" if process.returncode == 0 else "FAIL",
                "exit_code": process.returncode,
                "command": command,
                "output_digest": digest(process.stdout + process.stderr),
            }
        except (OSError, subprocess.TimeoutExpired):
            results[category] = {"status": "NOT_EXECUTED", "command": command}
    return {
        "status": "PASS"
        if all(r["status"] == "PASS" for r in results.values())
        else "MIGRATION_BLOCKED",
        "checks": results,
        "source_digest": source_digest(root),
        "checked_at": now(),
    }


class ApplicationRefactorer:
    """Apply approved technical plans with characterization, policy and rollback."""

    def __init__(self, framework: GitFrameworkPolicyProvider | None = None) -> None:
        self.framework = framework or GitFrameworkPolicyProvider()

    def inspect(self, root: Path) -> dict[str, Any]:
        """Inspect application structure without executing application code."""
        commit = run(["git", "rev-parse", "HEAD"], root).strip()
        return {
            "application": str(root),
            "commit": commit,
            "digest": source_digest(root),
            **analyze_repository(root, root.name, commit),
            "policy": asdict(self.framework.evaluate_project(root)),
        }

    def plan(
        self, root: Path, target_shared_libraries: dict[str, str] | None = None
    ) -> ApplicationRefactoringPlan:
        """Create a source-bound plan requiring concrete, reviewable transformations."""
        return ApplicationRefactoringPlan(
            str(root.resolve()),
            run(["git", "rev-parse", "HEAD"], root).strip(),
            source_digest(root),
            dict(target_shared_libraries or {}),
        )

    def _prepare(self, root: Path, plan: ApplicationRefactoringPlan) -> dict[Path, str]:
        if run(["git", "rev-parse", "HEAD"], root).strip() != plan.source_commit or (
            source_digest(root) != plan.source_digest
        ):
            raise MigrationBlocked("Source changed since planning")
        if plan.known_conflicts:
            raise MigrationBlocked(
                "HUMAN_DECISION_REQUIRED: resolve conflicts before transformation"
            )
        changes: dict[Path, str] = {}
        security_words = load_policy("human_decisions")["security_boundaries"]
        for wrapper in plan.wrappers_to_create + plan.symbols_to_replace:
            path = safe_path(root, wrapper["path"])
            source = path.read_text()
            node = next(
                (
                    n
                    for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == wrapper["symbol"]
                ),
                None,
            )
            if not node:
                raise MigrationBlocked("Legacy function not found")
            segment = ast.get_source_segment(source, node) or ""
            if any(word in segment.lower() for word in security_words):
                raise MigrationBlocked("SECURITY_OR_POLICY_REVIEW_REQUIRED")
            changes[path] = compatibility_wrapper(
                changes.get(path, source), wrapper["symbol"], wrapper["target"]
            )
        for replacement in plan.imports_to_change:
            path = safe_path(root, replacement["path"])
            changes[path] = replace_imports(
                changes.get(path, path.read_text()),
                replacement["old"],
                replacement["new"],
                replacement.get("symbol", ""),
            )
        for step in plan.optimization_steps:
            if step.get("kind") != "reviewed_patch":
                raise MigrationBlocked("Optimization requires an explicit reviewed patch")
            path = safe_path(root, step["path"])
            text = changes.get(path, path.read_text())
            if digest(text) != step["before_digest"]:
                raise MigrationBlocked("Optimization precondition mismatch")
            patched_text = step["content"]
            if any(
                text.lower().count(word) > patched_text.lower().count(word)
                for word in security_words
            ):
                raise MigrationBlocked("SECURITY_OR_POLICY_REVIEW_REQUIRED")
            ast.parse(patched_text)
            changes[path] = patched_text
        if plan.dependencies_to_add or plan.dependencies_to_remove:
            from auditcore.tools.apprefactor.optimization import edit_dependencies

            lockfiles = [root / name for name in ("uv.lock", "poetry.lock", "pdm.lock")]
            if any(path.exists() and path not in changes for path in lockfiles):
                raise MigrationBlocked("Lockfile must be updated in the same reviewed change")
            manifest = root / "pyproject.toml"
            if not manifest.exists():
                manifest = root / "requirements.txt"
            changes[manifest] = edit_dependencies(
                manifest,
                plan.dependencies_to_remove,
                plan.dependencies_to_add,
            )
        if not changes:
            raise MigrationBlocked("Plan contains no concrete changes")
        if {p.relative_to(root).as_posix() for p in changes} != set(plan.files_to_change):
            raise MigrationBlocked("Changed files differ from the reviewable plan")
        return changes

    def _check_characterized_security(
        self, source: Path, reference: str, item: dict[str, Any]
    ) -> None:
        """Require review when an import migration reduces known security controls."""

        def symbol_source(path: Path, symbol_reference: str) -> str:
            name = symbol_reference.split(":", 1)[1].split(".")[0]
            tree = ast.parse(path.read_text())
            node = next(
                (
                    node
                    for node in tree.body
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == name
                ),
                None,
            )
            if node is None:
                raise MigrationBlocked("Characterized source symbol not found")
            return ast.unparse(node).lower()

        legacy = symbol_source(source, reference)
        target = symbol_source(Path(item["target_file"]), item["target"])
        if any(
            legacy.count(word) > target.count(word)
            for word in load_policy("human_decisions")["security_boundaries"]
        ):
            raise MigrationBlocked("SECURITY_OR_POLICY_REVIEW_REQUIRED")

    def apply(self, plan: ApplicationRefactoringPlan, dry_run: bool = False) -> dict[str, Any]:
        """Preview or transactionally migrate; failures restore every original file."""
        root = Path(plan.application).resolve()
        changes = self._prepare(root, plan)
        workflow = StateMachine(REFACTOR_STATES)
        for state in ("APPLICATION_ANALYZED", "REFACTOR_PLAN_CREATED"):
            workflow.transition(state, {"status": "PASS", "reference": plan.source_digest})
        diffs = {
            p.relative_to(root).as_posix(): "".join(
                difflib.unified_diff(
                    p.read_text().splitlines(keepends=True),
                    value.splitlines(keepends=True),
                    fromfile=p.name,
                    tofile=p.name,
                )
            )
            for p, value in changes.items()
        }
        workflow.transition("DRY_RUN_COMPLETE", {"status": "PASS", "reference": digest(str(diffs))})
        if dry_run:
            return {"status": "DRY_RUN_COMPLETE", "diffs": diffs, "workflow": workflow.history}
        before = self.framework.evaluate_project(root)
        if (
            before.blocks(set(plan.policy_dependencies))
            or before.source_status != "POLICY_SOURCE_CURRENT"
        ):
            raise MigrationBlocked("Applicable policy evidence must be resolved before migration")
        if set(REQUIRED_VERIFICATION) - plan.verification_commands.keys():
            raise MigrationBlocked("Required verification commands are missing")
        transformations = plan.wrappers_to_create + plan.symbols_to_replace
        behavior_checks = transformations + plan.characterization_checks
        if not behavior_checks:
            raise MigrationBlocked("Migration requires legacy characterization evidence")
        comparisons = []
        for item in behavior_checks:
            golden = safe_path(root, item["characterization"])
            baseline = read_json(golden)
            source = safe_path(root, item["path"])
            if baseline["source_digest"] != digest(source.read_bytes()):
                raise MigrationBlocked("Legacy characterization is stale")
            current = execute_cases(root, baseline["reference"], baseline["cases"])
            if current != baseline["outcomes"]:
                raise MigrationBlocked("Legacy behavior differs from golden outcomes")
            if item in plan.characterization_checks:
                self._check_characterized_security(source, baseline["reference"], item)
            regression = compare(
                Path(item["target_root"]), item["target"], golden, Path(item["target_file"])
            )
            if regression.status != "PASS":
                raise MigrationBlocked("MIGRATION_BLOCKED: replacement behavior differs")
            comparisons.append(asdict(regression))
        workflow.transition(
            "LEGACY_CHARACTERIZED",
            {
                "status": "PASS",
                "reference": digest(str(comparisons)),
            },
        )
        originals = {p: p.read_bytes() for p in changes}
        try:
            for path, changed_source in changes.items():
                path.write_text(changed_source)
            workflow.transition(
                "MIGRATION_APPLIED",
                {
                    "status": "PASS",
                    "reference": source_digest(root),
                },
            )
            verification = verify(root, plan.verification_commands)
            # Recheck actual shared behavior after verification, before committing any change.
            for item in behavior_checks:
                regression = compare(
                    Path(item["target_root"]),
                    item["target"],
                    safe_path(root, item["characterization"]),
                    Path(item["target_file"]),
                )
                if regression.status != "PASS":
                    raise MigrationBlocked("MIGRATION_BLOCKED: replacement behavior changed")
            after = self.framework.evaluate_project(root)
            if (
                verification["status"] != "PASS"
                or after.blocks(set(plan.policy_dependencies))
                or after.source_status != "POLICY_SOURCE_CURRENT"
            ):
                raise MigrationBlocked("MIGRATION_BLOCKED: verification failed")
            workflow.transition(
                "APPLICATION_TESTED",
                {
                    "status": "PASS",
                    "reference": digest(str(verification)),
                },
            )
            workflow.transition(
                "OPTIMIZATION_APPLIED",
                {
                    "status": "PASS" if plan.optimization_steps else "NOT_APPLICABLE_WITH_REASON",
                    "reference": plan.source_digest,
                    "reason": "Only explicitly planned optimizations",
                },
            )
            for state in ("REGRESSION_VERIFIED", "INTEGRATION_VERIFIED", "QUALITY_VERIFIED"):
                workflow.transition(
                    state, {"status": "PASS", "reference": digest(str(verification))}
                )
            result = {
                "status": "VERIFIED",
                "workflow": workflow.history,
                "application": root.name,
                "source_commit": plan.source_commit,
                "target_commit": None,
                "source_digest": source_digest(root),
                "changed_files": list(diffs),
                "regression": comparisons,
                "verification": verification,
                "policy_before": asdict(before),
                "policy_after": asdict(after),
                "legacy_cleanup": "NOT_EXECUTED: legacy code retained",
                "shared_libraries": plan.target_shared_libraries,
            }
            write_json(root / ".auditcore/refactor-result.json", result)
            return result
        except BaseException:
            for path, data in originals.items():
                path.write_bytes(data)
            raise

    def handoff(self, root: Path) -> dict[str, Any]:
        """Only a current verified migration plus deployment policy can become ready."""
        result = read_json(root / ".auditcore/refactor-result.json")
        policy = self.framework.evaluate_project(root)
        if result.get("status") != "VERIFIED" or result["source_digest"] != source_digest(root):
            raise MigrationBlocked("Verification missing or stale")
        if policy.overall_status != "PASS" or policy.source_status != "POLICY_SOURCE_CURRENT":
            raise MigrationBlocked("Deployment policy requires review")
        evidence_path = root / "auditcore-deployment-evidence.json"
        evidence = read_json(evidence_path) if evidence_path.exists() else {}
        checks = evidence.get("checks", {})
        if evidence.get("source_digest") != source_digest(root):
            raise MigrationBlocked("Deployment evidence is missing or stale")
        for name in DEPLOYMENT_CHECKS:
            check = checks.get(name, {})
            if check.get("status") not in {"PASS", "NOT_APPLICABLE_WITH_REASON"} or not (
                check.get("reference") and check.get("reason")
            ):
                raise MigrationBlocked(f"Deployment evidence required: {name}")
        handoff = {
            "application": root.name,
            "status": "READY_FOR_DEPLOYMENT",
            "git_commit": run(["git", "rev-parse", "HEAD"], root).strip(),
            "source_digest": source_digest(root),
            "shared_libraries": result["shared_libraries"],
            "tests": result["verification"],
            "policy": asdict(policy),
            "deployment_checks": checks,
        }
        write_json(root / ".auditcore/deployment-handoff.json", handoff)
        return handoff
