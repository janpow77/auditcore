"""Runner guard for this repository's workflows, using ``auditcore_runner``.

The rules (``fork``, ``dependabot``, ``secrets``, ``runner-var``) live in
``auditcore_runner.workflows.workflow_findings``; general workflow security is
checked by zizmor and actionlint in ``code-quality-gate``. What remains here is
auditcore-specific: the runner variable ``AUDITCORE_RUNNER`` and the expectation
that every job that can land on the own runners (NUC, janpow-ai) is clean.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
RUNNER_VARIABLES = ("AUDITCORE_RUNNER",)

# The package is not a dependency of the platform; load its pure module directly.
_SPEC = importlib.util.spec_from_file_location(
    "auditcore_runner_workflows",
    ROOT / "packages/auditcore_runner/src/auditcore_runner/workflows.py",
)
assert _SPEC is not None and _SPEC.loader is not None
workflows = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = workflows  # dataclasses resolve the module by name
_SPEC.loader.exec_module(workflows)

DOCUMENTS = {p.name: yaml.safe_load(p.read_text("utf-8")) for p in sorted(WORKFLOWS.glob("*.yml"))}
FINDINGS = {
    name: workflows.workflow_findings(name, document, RUNNER_VARIABLES)
    for name, document in DOCUMENTS.items()
}


def test_self_hosted_capable_jobs_exist() -> None:
    capable = [
        (name, job)
        for name, document in DOCUMENTS.items()
        for job, body in (document.get("jobs") or {}).items()
        if "uses" not in body and workflows.may_be_self_hosted(body.get("runs-on", ""))
    ]
    assert len(capable) >= 5, "the own runners must still be selectable; parser broken?"


@pytest.mark.parametrize("workflow", sorted(DOCUMENTS))
def test_workflow_is_safe_for_own_runners(workflow: str) -> None:
    findings = [f"{f.job} [{f.rule}] {f.message}" for f in FINDINGS[workflow]]
    assert not findings, "\n".join(findings)


def test_dependabot_is_routed_to_hosted_runners() -> None:
    for name in ("quality.yml", "domain-packages.yml", "js-packages.yml"):
        jobs = DOCUMENTS[name]["jobs"]
        runs_on = [str(body.get("runs-on", "")) for body in jobs.values() if "uses" not in body]
        assert any("github.actor == 'dependabot[bot]'" in r for r in runs_on), name
