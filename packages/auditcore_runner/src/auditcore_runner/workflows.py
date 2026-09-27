"""Check GitHub workflow files for safe use of self-hosted runners.

General workflow security (template injection, unpinned actions …) is left to
zizmor and actionlint; these rules cover what they do not (each finding names
workflow, job and rule):

* ``fork`` – in a pull-request workflow, a job that can land on a self-hosted
  runner keeps fork PRs on hosted runners: ``runs-on`` routes
  ``head.repo.full_name != github.repository`` to ``ubuntu-latest``, or ``if``
  requires ``head.repo.full_name == github.repository``.
* ``dependabot`` – Dependabot PRs must not reach self-hosted runners.
* ``secrets`` – a job using secrets (other than ``GITHUB_TOKEN``) runs hosted.
* ``runner-var`` – configured runner-selection variables (e.g.
  ``vars.MY_RUNNER``) appear only in ``runs-on``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

PR_TRIGGERS = {
    "pull_request",
    "pull_request_target",
    "pull_request_review",
    "pull_request_review_comment",
    "issue_comment",
    "workflow_run",
}
HOSTED = re.compile(r"^(ubuntu|windows|macos)-[\w.-]+$")
FORK_IN_RUNS_ON = re.compile(r"head\.repo\.full_name\s*!=\s*github\.repository")
FORK_IN_IF = re.compile(r"head\.repo\.full_name\s*==\s*github\.repository")
SECRET = re.compile(r"secrets\.(?!GITHUB_TOKEN\b)[A-Za-z_][A-Za-z0-9_]*")
DEPENDABOT = re.compile(r"dependabot\[bot\]")


@dataclass(frozen=True)
class WorkflowFinding:
    workflow: str
    job: str
    rule: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"workflow": self.workflow, "job": self.job, "regel": self.rule, "meldung": self.message}


def _triggers(document: Mapping[object, object]) -> set[str]:
    # PyYAML reads the key ``on`` as boolean True.
    raw = document.get("on", document.get(True, {}))
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {str(x) for x in raw}
    return {str(k) for k in raw} if isinstance(raw, dict) else set()


def may_be_self_hosted(runs_on: object) -> bool:
    """False only for plain hosted labels like ``ubuntu-latest``."""
    if isinstance(runs_on, str):
        return "${{" in runs_on or not HOSTED.match(runs_on.strip())
    if isinstance(runs_on, list):
        return any(may_be_self_hosted(x) for x in runs_on)
    return True


def _runner_variable_findings(
    workflow: str, name: str, job: Mapping[str, object], runner_variables: tuple[str, ...]
) -> list[WorkflowFinding]:
    rest = json.dumps({k: v for k, v in job.items() if k != "runs-on"})
    return [
        WorkflowFinding(workflow, name, "runner-var", f"vars.{variable} außerhalb von runs-on")
        for variable in runner_variables
        if f"vars.{variable}" in rest
    ]


def _job_findings(
    workflow: str, name: str, job: Mapping[str, object], pr_triggered: bool, runner_variables: tuple[str, ...]
) -> list[WorkflowFinding]:
    findings = _runner_variable_findings(workflow, name, job, runner_variables)
    runs_on = job.get("runs-on", "")
    if not may_be_self_hosted(runs_on):
        return findings
    condition, runs_text = str(job.get("if", "")), json.dumps(runs_on)
    if pr_triggered:
        routed = FORK_IN_RUNS_ON.search(runs_text) and "ubuntu-latest" in runs_text
        if not (routed or FORK_IN_IF.search(condition)):
            findings.append(
                WorkflowFinding(workflow, name, "fork", "Fork-PRs könnten den self-hosted Runner erreichen")
            )
        if not DEPENDABOT.search(condition) and not DEPENDABOT.search(runs_text):
            message = "Dependabot-PRs könnten den self-hosted Runner erreichen"
            findings.append(WorkflowFinding(workflow, name, "dependabot", message))
    body = json.dumps(job.get("steps", [])) + json.dumps(job.get("env", {})) + json.dumps(job.get("with", {}))
    secrets = sorted(set(SECRET.findall(body)))
    if secrets:
        findings.append(
            WorkflowFinding(workflow, name, "secrets", "Secrets auf self-hosted Runner: " + ", ".join(secrets))
        )
    return findings


def workflow_findings(
    workflow: str, document: Mapping[object, object], runner_variables: tuple[str, ...] = ()
) -> list[WorkflowFinding]:
    """All findings of one parsed workflow (pure); reusable-workflow calls (``uses``) are skipped."""
    pr_triggered = bool(_triggers(document) & PR_TRIGGERS)
    jobs = document.get("jobs", {})
    findings: list[WorkflowFinding] = []
    for name, job in jobs.items() if isinstance(jobs, dict) else []:
        if isinstance(job, dict) and "uses" not in job:
            findings += _job_findings(workflow, str(name), cast(dict[str, object], job), pr_triggered, runner_variables)
    return findings


class MissingExtraError(RuntimeError):
    """Reading YAML files needs the optional extra ``workflows`` (PyYAML)."""


def check_file(path: Path, runner_variables: tuple[str, ...] = ()) -> list[WorkflowFinding]:
    try:
        import yaml
    except ImportError as error:
        hint = "Workflow-Prüfung braucht das Extra: pip install 'auditcore_runner[workflows]'"
        raise MissingExtraError(hint) from error
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(document, dict):
        return []
    return workflow_findings(path.name, cast(dict[object, object], document), runner_variables)


def check_directory(directory: Path, runner_variables: tuple[str, ...] = ()) -> list[WorkflowFinding]:
    files = sorted([*directory.glob("*.yml"), *directory.glob("*.yaml")]) if directory.is_dir() else [directory]
    return [finding for file in files for finding in check_file(file, runner_variables)]
