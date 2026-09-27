"""Runner guard: self-hosted runners never see fork code, secrets or Dependabot runs.

Every job whose ``runs-on`` is not a fixed GitHub-hosted ``ubuntu-*`` label can land
on a self-hosted runner (NUC, janpow-ai). Such a job must

* keep fork pull requests on ``ubuntu-latest`` (fork condition in ``runs-on`` or a
  job ``if`` that admits only same-repository pull requests), unless the workflow is
  not triggered by pull requests at all (rule ``fork``);
* not use repository secrets, ``GITHUB_TOKEN`` excepted (rule ``secrets``);
* keep Dependabot pull requests on GitHub-hosted runners (rule ``dependabot``).

``workflow_findings`` is pure and repository-independent; it moves to the package
``auditcore_runner`` (CLI ``auditcore-runner workflows pruefen``) once that exists,
and this test then calls the package function.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

HOSTED = re.compile(r"^ubuntu-[\w.-]+$")
FORK_IN_RUNS_ON = "github.event.pull_request.head.repo.full_name != github.repository"
FORK_IN_IF = "github.event.pull_request.head.repo.full_name == github.repository"
DEPENDABOT = "dependabot[bot]"
SECRET = re.compile(r"secrets\.(\w+)")
PR_TRIGGERS = {"pull_request", "pull_request_target"}
RULES = ("fork", "secrets", "dependabot")


@dataclass(frozen=True)
class WorkflowFinding:
    """A rule violation of one job in one workflow file."""

    workflow: str
    job: str
    rule: str
    message: str


def _triggers(document: Mapping[object, object]) -> set[str]:
    # PyYAML reads the key ``on`` as boolean True.
    raw = document.get("on", document.get(True, {}))
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {str(item) for item in raw}
    return {str(key) for key in raw or {}}  # type: ignore[union-attr]


def _job_findings(
    workflow: str, name: str, body: Mapping[str, object], pr: bool
) -> list[WorkflowFinding]:
    runs_on = str(body.get("runs-on", "")).strip()
    if HOSTED.match(runs_on):
        return []
    condition = str(body.get("if", ""))
    findings: list[WorkflowFinding] = []
    if pr and not (
        (FORK_IN_RUNS_ON in runs_on and "'ubuntu-latest'" in runs_on) or FORK_IN_IF in condition
    ):
        findings.append(WorkflowFinding(workflow, name, "fork", "fork PR code on self-hosted"))
    secrets = set(SECRET.findall(yaml.safe_dump(dict(body)))) - {"GITHUB_TOKEN"}
    if secrets:
        message = f"secrets {sorted(secrets)} on self-hosted"
        findings.append(WorkflowFinding(workflow, name, "secrets", message))
    if pr and DEPENDABOT not in condition and DEPENDABOT not in runs_on:
        message = "Dependabot PRs on self-hosted"
        findings.append(WorkflowFinding(workflow, name, "dependabot", message))
    return findings


def workflow_findings(workflow: str, document: Mapping[object, object]) -> list[WorkflowFinding]:
    """All rule violations of one parsed workflow; reusable workflows are checked in place."""
    pr = bool(_triggers(document) & PR_TRIGGERS)
    jobs = document.get("jobs") or {}
    findings: list[WorkflowFinding] = []
    for name, body in jobs.items():  # type: ignore[union-attr]
        if "uses" not in body:
            findings += _job_findings(workflow, str(name), body, pr)
    return findings


def self_hosted_jobs(workflow: str, document: Mapping[object, object]) -> list[str]:
    """Names of jobs that can run on a self-hosted runner."""
    jobs = document.get("jobs") or {}
    return [
        str(name)
        for name, body in jobs.items()  # type: ignore[union-attr]
        if "uses" not in body and not HOSTED.match(str(body.get("runs-on", "")).strip())
    ]


# ------------------------------------------------------------------ this repository
WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
DOCUMENTS = {p.name: yaml.safe_load(p.read_text("utf-8")) for p in sorted(WORKFLOWS.glob("*.yml"))}
FINDINGS = [f for name, doc in DOCUMENTS.items() for f in workflow_findings(name, doc)]
JOBS = [(name, job) for name, doc in DOCUMENTS.items() for job in self_hosted_jobs(name, doc)]

# Known violations, removed by the runner phase (see PR "Prüfbank Phase 1").
# xfail(strict=True): once fixed, the case turns red and the entry must go.
KNOWN = {
    ("quality.yml", "quality", "dependabot"),
    ("domain-packages.yml", "packages", "dependabot"),
    ("js-packages.yml", "js-packages", "dependabot"),
}


def _cases() -> list[object]:
    cases = []
    for workflow, job in JOBS:
        for rule in RULES:
            marks = []
            if (workflow, job, rule) in KNOWN:
                marks.append(pytest.mark.xfail(strict=True, reason=f"known: {rule}"))
            cases.append(
                pytest.param(workflow, job, rule, id=f"{workflow}:{job}:{rule}", marks=marks)
            )
    return cases


def test_workflows_are_found() -> None:
    assert len(DOCUMENTS) >= 10
    assert JOBS, "no self-hosted capable job found; parser broken?"


@pytest.mark.parametrize(("workflow", "job", "rule"), _cases())
def test_self_hosted_job_follows_rule(workflow: str, job: str, rule: str) -> None:
    hits = [f for f in FINDINGS if (f.workflow, f.job, f.rule) == (workflow, job, rule)]
    assert not hits, hits[0].message


def test_known_entries_are_current() -> None:
    assert {(w, j) for w, j in JOBS} >= {(w, j) for w, j, _ in KNOWN}, "stale entry in KNOWN"


# ------------------------------------------------------------------ the pure function
PR_JOB = {"on": {"pull_request": {}}, "jobs": {}}
SELF = "${{ fromJSON(vars.AUDITCORE_RUNNER || '\"ubuntu-latest\"') }}"


def _doc(**job: object) -> dict[object, object]:
    return {**PR_JOB, "jobs": {"j": job}}


def test_hosted_jobs_are_never_findings() -> None:
    body = {"runs-on": "ubuntu-24.04", "steps": [{"run": "echo ${{ secrets.X }}"}]}
    assert workflow_findings("w.yml", _doc(**body)) == []


def test_unguarded_self_hosted_pr_job_violates_every_rule() -> None:
    body = {"runs-on": SELF, "steps": [{"run": "echo ${{ secrets.DEPLOY }}"}]}
    rules = [f.rule for f in workflow_findings("w.yml", _doc(**body))]
    assert rules == ["fork", "secrets", "dependabot"]


def test_guards_in_if_and_runs_on_are_accepted() -> None:
    guarded_if = f"{FORK_IN_IF} && github.actor != '{DEPENDABOT}'"
    assert workflow_findings("w.yml", _doc(**{"runs-on": SELF, "if": guarded_if})) == []
    runs_on = f"${{{{ ({FORK_IN_RUNS_ON}) && 'ubuntu-latest' || 'self' }}}}"
    rules = [f.rule for f in workflow_findings("w.yml", _doc(**{"runs-on": runs_on}))]
    assert rules == ["dependabot"]


def test_non_pr_workflows_only_check_secrets() -> None:
    document = {True: {"schedule": []}, "jobs": {"n": {"runs-on": SELF}}}
    assert workflow_findings("n.yml", document) == []
    document["jobs"] = {"n": {"runs-on": SELF, "env": {"T": "${{ secrets.GITHUB_TOKEN }}"}}}
    assert workflow_findings("n.yml", document) == []
