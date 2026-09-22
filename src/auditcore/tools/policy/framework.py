"""Git-backed framework adapter with source drift detection and offline cache."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import asdict
from importlib.resources import files
from pathlib import Path
from typing import Any

from auditcore.tools.common import digest, now, read_json, run, write_json
from auditcore.tools.policy.models import (
    ApplicabilityContext,
    BindingLevel,
    PolicyEvaluationResult,
    Requirement,
    RequirementEvaluation,
    RequirementSet,
    Truth,
)

SOURCE_FILES = (
    "AGENTS.md",
    "docs/anforderungen.md",
    "docs/verbindlichkeit.md",
    "docs/pruefkatalog.md",
    "docs/standards.md",
    "docs/standards-register.json",
    "docs/security/bsi-baseline.md",
    "docs/security/lieferkette.md",
    "docs/security/sicherheitsvorfaelle.md",
)


def trigger_value(trigger: dict[str, Any], context: ApplicabilityContext) -> Truth:
    """Evaluate declarative predicates using Kleene three-valued logic."""
    if "all" in trigger or "any" in trigger:
        key = "all" if "all" in trigger else "any"
        values = [trigger_value(t, context) for t in trigger[key]]
        decisive = Truth.FALSE if key == "all" else Truth.TRUE
        if decisive in values:
            return decisive
        if Truth.UNKNOWN in values:
            return Truth.UNKNOWN
        return Truth.TRUE if key == "all" else Truth.FALSE
    if "constant" in trigger:
        return Truth(trigger["constant"])
    value = getattr(context, trigger["field"], "UNKNOWN")
    if value == "UNKNOWN":
        return Truth.UNKNOWN
    if "known" in trigger:
        return Truth.TRUE
    return Truth.TRUE if value in trigger["in"] else Truth.FALSE


def table_rows(content: str, prefix: str) -> dict[str, list[str]]:
    """Parse identified framework Markdown table rows deterministically."""
    result = {}
    for line in content.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and re.fullmatch(rf"{prefix}-\d+", cells[0]):
            result[cells[0]] = cells[1:]
    return result


class GitFrameworkPolicyProvider:
    """Read immutable Git content; cached content is never silently current."""

    def __init__(
        self,
        checkout: Path | None = None,
        *,
        repository: str = "janpow77/verwaltung-app-framework",
        cache: Path = Path(".auditcore/framework-cache.json"),
        offline: bool = False,
        evidence: dict[str, dict[str, Any]] | None = None,
        decisions: dict[str, dict[str, Any]] | None = None,
        artifact: str = "auditcore",
    ) -> None:
        self.checkout = checkout
        self.repository = repository
        self.cache = cache
        self.offline = offline
        self.evidence = evidence or {}
        self.decisions = decisions or {}
        self.artifact = artifact
        self._loaded: RequirementSet | None = None

    def _source(self) -> dict[str, Any]:
        if self.offline:
            if self.cache.exists():
                data: dict[str, Any] = read_json(self.cache)
                data["source_status"] = "POLICY_SOURCE_STALE"
                return data
            return {}
        try:
            checkout = self.checkout or self.cache.parent / "framework-source"
            remote = f"https://github.com/{self.repository}.git"
            if not checkout.exists():
                checkout.parent.mkdir(parents=True, exist_ok=True)
                run(["git", "clone", "--depth", "1", remote, str(checkout)])
            head = run(["git", "rev-parse", "HEAD"], checkout).strip()
            remote_head = run(["git", "ls-remote", remote, "HEAD"]).split()[0]
            content = {p: run(["git", "show", f"{head}:{p}"], checkout) for p in SOURCE_FILES}
            data = {
                "repository": self.repository,
                "commit_sha": head,
                "captured_at": now(),
                "source_status": "POLICY_SOURCE_CURRENT"
                if head == remote_head
                else "POLICY_SOURCE_STALE",
                "content": content,
            }
            write_json(self.cache, data)
            return data
        except (RuntimeError, OSError, IndexError):
            if self.cache.exists():
                data = read_json(self.cache)
                data["source_status"] = "POLICY_SOURCE_STALE"
                return data
            return {}

    def load_requirements(self) -> RequirementSet:
        """Load matrix and test catalog; guard executable mappings by content hashes."""
        if self._loaded:
            return self._loaded
        source = self._source()
        if not source or source.get("repository") != self.repository:
            return RequirementSet(
                self.repository, "UNKNOWN", now(), "POLICY_SOURCE_UNAVAILABLE", (), {}, {}
            )
        content = source["content"]
        adapter = json.loads(files("auditcore.tools.policy").joinpath("adapter.json").read_text())
        rows = table_rows(content["docs/verbindlichkeit.md"], "F")
        checks = table_rows(content["docs/pruefkatalog.md"], "T")
        registry = json.loads(content["docs/standards-register.json"])
        requirements: list[Requirement] = []
        source_hashes = {p: digest(text) for p, text in content.items()}
        global_current = all(
            source_hashes.get(p) == sha for p, sha in adapter["source_digests"].items()
        )
        for identifier, row in rows.items():
            mapping = adapter["requirements"].get(identifier, {})
            current = global_current and mapping.get("row_hash") == digest(json.dumps(row))
            associated: list[str] = next(
                (m["tests"] for m in registry["mappings"] if m["requirement"] == identifier), []
            )
            for suffix, level, text, trigger in (
                (".ASSESS", BindingLevel.MUSS, row[0], mapping.get("assessment", {})),
                ("", BindingLevel.BEDINGT, row[1], mapping.get("trigger", {})),
            ):
                requirements.append(
                    Requirement(
                        identifier + suffix,
                        self.repository,
                        "docs/verbindlichkeit.md",
                        source["commit_sha"],
                        level,
                        "project",
                        text,
                        trigger or {"constant": "UNKNOWN"},
                        tuple(associated),
                        current,
                    )
                )
        recommendations = [
            x for x in content["docs/verbindlichkeit.md"].splitlines() if x.startswith("SOLL:")
        ]
        for index, recommendation in enumerate(recommendations):
            requirements.append(
                Requirement(
                    f"SOLL-{index + 1:02d}",
                    self.repository,
                    "docs/verbindlichkeit.md",
                    source["commit_sha"],
                    BindingLevel.SOLL,
                    "project",
                    recommendation,
                    {"constant": "TRUE"},
                    adapter_current=global_current,
                )
            )
        tests = {
            identifier: {
                "text": row,
                "source_path": "docs/pruefkatalog.md",
                "source_commit": source["commit_sha"],
                "trigger": adapter["tests"]
                .get(identifier, {})
                .get("trigger", {"constant": "UNKNOWN"}),
                "adapter_current": global_current
                and adapter["tests"].get(identifier, {}).get("row_hash") == digest(json.dumps(row)),
            }
            for identifier, row in checks.items()
        }
        self._loaded = RequirementSet(
            self.repository,
            source["commit_sha"],
            source["captured_at"],
            source["source_status"],
            tuple(requirements),
            tests,
            source_hashes,
        )
        return self._loaded

    def _evaluate_requirement(
        self,
        requirement: Requirement,
        context: ApplicabilityContext,
    ) -> RequirementEvaluation:
        applicable = trigger_value(requirement.trigger, context)
        if not requirement.adapter_current:
            applicable = Truth.UNKNOWN
        reason = json.dumps(requirement.trigger, sort_keys=True)
        status, gate = "APPLICABLE", "REVIEW_REQUIRED"
        evidence = self.evidence.get(requirement.requirement_id, {})
        references = tuple(evidence.get("references", []))
        decision_ref = None
        if applicable == Truth.UNKNOWN:
            status, gate = "OPEN", "REVIEW_REQUIRED"
            reason = "Unknown context or framework adapter drift: " + reason
        elif applicable == Truth.FALSE:
            status = gate = "NOT_APPLICABLE_WITH_REASON"
            reason = "Trigger not present in explicit context: " + reason
        elif requirement.requirement_id.endswith(".ASSESS"):
            status, gate = "IMPLEMENTED", "PASS"
            reason = "Required scoping facts supplied; no technical implementation inferred"
            references = ("applicability_context",)
        elif (
            evidence.get("status") == "VERIFIED"
            and references
            and (evidence.get("source_commit") == requirement.commit_sha)
        ):
            status, gate = "VERIFIED", "PASS"
        elif evidence.get("status") == "IMPLEMENTED" and references:
            status = "IMPLEMENTED"
        elif evidence.get("status") == "MISSING":
            status, gate = "BLOCKED", "FAIL"
        elif requirement.classification == BindingLevel.SOLL:
            status, gate = "OPEN", "WARNING"
        decision = self.decisions.get(requirement.requirement_id)
        if decision and applicable == Truth.TRUE:
            required = ("authority", "reference", "reason", "consequences", "compensation")
            if (
                decision.get("classification") == "HUMAN_CONFIRMED"
                and all(decision.get(k) for k in required)
                and decision.get("framework_commit") == requirement.commit_sha
            ):
                status, gate = "DEVIATION_APPROVED", "PASS_WITH_DEVIATION"
                decision_ref = decision["reference"]
            else:
                status, gate = "DEVIATION_PENDING", "REVIEW_REQUIRED"
        return RequirementEvaluation(
            requirement.requirement_id,
            requirement.source_path,
            requirement.commit_sha,
            requirement.classification,
            requirement.trigger,
            applicable,
            reason,
            status,
            gate,
            references,
            requirement.derived_checks,
            decision_ref,
        )

    def evaluate_project(self, root: Path) -> PolicyEvaluationResult:
        """Load explicit per-project evidence without sharing it across project evaluations."""
        provider = copy.copy(self)
        for filename, attribute in (
            ("policy-evidence.json", "evidence"),
            ("policy-decisions.json", "decisions"),
        ):
            path = root / ".auditcore" / filename
            if path.exists():
                value = read_json(path)
                if not isinstance(value, dict):
                    raise ValueError("Policy evidence must map requirement IDs to records")
                setattr(provider, attribute, value)
        return provider.evaluate(context_from_project(root))

    def evaluate(self, context: ApplicabilityContext) -> PolicyEvaluationResult:
        """Determine applicability before emitting any security or compliance gate."""
        source = self.load_requirements()
        evaluations = tuple(self._evaluate_requirement(r, context) for r in source.requirements)
        blocked = tuple(r.requirement_id for r in evaluations if r.gate_status == "FAIL")
        review = tuple(r.requirement_id for r in evaluations if r.gate_status == "REVIEW_REQUIRED")
        if source.source_status != "POLICY_SOURCE_CURRENT":
            review += (source.source_status,)
        if context.protection_need in {"high", "very_high"} and (
            "HIGH_PROTECTION" not in context.profiles()
        ):
            review += ("protection_need_source",)
        tests: dict[str, dict[str, Any]] = {}
        for identifier, test in source.tests.items():
            applicability = (
                trigger_value(test["trigger"], context)
                if test["adapter_current"]
                else Truth.UNKNOWN
            )
            tests[identifier] = {
                **test,
                "applicable": applicability,
                "status": "NOT_EXECUTED"
                if applicability == Truth.TRUE
                else (
                    "REVIEW_REQUIRED"
                    if applicability == Truth.UNKNOWN
                    else "NOT_APPLICABLE_WITH_REASON"
                ),
                "reason": json.dumps(test["trigger"], sort_keys=True),
            }
        overall = "FAIL" if blocked else "REVIEW_REQUIRED" if review else "PASS"
        return PolicyEvaluationResult(
            source.repository,
            source.commit_sha,
            source.source_status,
            self.artifact,
            context,
            context.profiles(),
            evaluations,
            overall,
            blocked,
            review,
            tuple(r.requirement_id for r in evaluations if r.status == "DEVIATION_APPROVED"),
            tests,
        )


def context_from_project(root: Path) -> ApplicabilityContext:
    """Load declared applicability; do not guess security facts from imports."""
    path = root / "auditcore-context.json"
    return (
        ApplicabilityContext.from_dict(read_json(path)) if path.exists() else ApplicabilityContext()
    )


def policy_report(root: Path, framework: Path | None = None) -> dict[str, Any]:
    """Evaluate the current project using its declared context."""
    provider = GitFrameworkPolicyProvider(
        framework,
        cache=root / ".auditcore/framework-cache.json",
        artifact=root.name,
    )
    return asdict(provider.evaluate(context_from_project(root)))
