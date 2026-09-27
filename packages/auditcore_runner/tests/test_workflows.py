from __future__ import annotations

import sys

from pathlib import Path

import pytest

from auditcore_runner import workflows

GUARDED = """
on: {pull_request: {}}
jobs:
  test:
    runs-on: ${{ (github.event.pull_request.head.repo.full_name != github.repository) && 'ubuntu-latest' || fromJSON(vars.RUNNER) }}
    if: github.actor != 'dependabot[bot]'
    steps: [{run: pytest}]
"""
UNGUARDED = """
on: [pull_request]
jobs:
  test:
    runs-on: [self-hosted, auditcore]
    steps: [{run: "deploy ${{ secrets.DEPLOY_KEY }}"}]
  hosted:
    runs-on: ubuntu-latest
    steps: [{run: "echo ${{ secrets.DEPLOY_KEY }}"}]
"""
SCHEDULED = """
on: {schedule: [{cron: '0 1 * * *'}]}
jobs:
  nightly:
    runs-on: ${{ fromJSON(vars.RUNNER) }}
    steps: [{run: pytest, env: {TOKEN: "${{ secrets.GITHUB_TOKEN }}"}}]
"""


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_guarded_workflow_is_clean(tmp_path: Path) -> None:
    assert workflows.check_file(write(tmp_path, "ok.yml", GUARDED)) == []


def test_unguarded_self_hosted_job(tmp_path: Path) -> None:
    findings = workflows.check_file(write(tmp_path, "bad.yml", UNGUARDED))
    rules = {(f.job, f.rule) for f in findings}
    assert rules == {("test", "fork"), ("test", "secrets"), ("test", "dependabot")}
    assert all(f.job != "hosted" for f in findings)


def test_scheduled_workflow_needs_no_fork_guard(tmp_path: Path) -> None:
    assert workflows.check_file(write(tmp_path, "nightly.yml", SCHEDULED)) == []


def test_directory_and_hosted_labels(tmp_path: Path) -> None:
    write(tmp_path, "a.yml", GUARDED)
    write(tmp_path, "b.yaml", UNGUARDED)
    assert len(workflows.check_directory(tmp_path)) == 3
    assert not workflows.may_be_self_hosted("ubuntu-24.04")
    assert workflows.may_be_self_hosted(["self-hosted", "gpu"])


def test_runner_variable_only_in_runs_on_and_reusable_calls_skipped() -> None:
    document = {
        True: {"schedule": []},
        "jobs": {
            "n": {"runs-on": "ubuntu-latest", "env": {"R": "${{ vars.MY_RUNNER }}"}},
            "reuse": {"uses": "./.github/workflows/other.yml"},
            "ok": {"runs-on": "${{ fromJSON(vars.MY_RUNNER) }}"},
        },
    }
    findings = workflows.workflow_findings("n.yml", document, ("MY_RUNNER",))
    assert [(f.job, f.rule) for f in findings] == [("n", "runner-var")]


def test_fork_guard_direction_matters(tmp_path: Path) -> None:
    wrong = GUARDED.replace("!= github.repository", "== github.repository")
    assert [f.rule for f in workflows.check_file(write(tmp_path, "x.yml", wrong))] == ["fork"]


def test_missing_yaml_extra_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "yaml", None)
    with pytest.raises(workflows.MissingExtraError, match=r"auditcore_runner\[workflows\]"):
        workflows.check_file(write(tmp_path, "x.yml", GUARDED))
