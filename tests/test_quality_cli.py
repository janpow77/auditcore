"""Tests for the public quality command-line entry point."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from auditcore.tools import common
from auditcore.tools.quality import cli


def test_main_json_mode_forwards_policy_and_reports(tmp_path: Path, monkeypatch: Any) -> None:
    project = tmp_path / "project"
    metadata = project / ".auditcore"
    metadata.mkdir(parents=True)
    (metadata / "policy-evidence.json").write_text("{}", encoding="utf-8")
    (metadata / "policy-decisions.json").write_text("{}", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        "[tool.auditcore-bibquality]\nstrict = false\n", encoding="utf-8"
    )
    target = tmp_path / "src" / "module.py"
    target.parent.mkdir()
    target.write_text("value = 1\n", encoding="utf-8")
    framework = tmp_path / "framework.json"
    context = SimpleNamespace(name="test-context")
    policy = SimpleNamespace(name="test-policy")
    report = SimpleNamespace(
        status="PASS",
        findings=[],
        to_dict=lambda: {"status": "PASS"},
        exit_code=lambda strict: int(strict),
    )
    calls: dict[str, Any] = {}

    class Provider:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            calls["provider_args"] = args
            calls["provider_kwargs"] = kwargs

        def evaluate(self, value: object) -> object:
            calls["context"] = value
            return policy

    def fake_check(path: Path, **kwargs: Any) -> object:
        calls["check"] = (path, kwargs)
        return report

    monkeypatch.setattr(cli, "GitFrameworkPolicyProvider", Provider)
    monkeypatch.setattr(cli, "context_from_project", lambda path: context)
    monkeypatch.setattr(cli, "check", fake_check)
    monkeypatch.setattr(cli, "emit", lambda value, output: calls.update(emitted=(value, output)))

    result = cli.main(
        [
            str(target),
            "--format",
            "json",
            "--output",
            str(tmp_path / "report.json"),
            "--no-external-tools",
            "--framework",
            str(framework),
            "--offline",
            "--artifact",
            "stable-artifact",
            "--api-snapshot",
            str(tmp_path / "snapshot.json"),
            "--compare-api",
            str(tmp_path / "previous.json"),
            "--supply-chain-report",
            str(tmp_path / "supply-chain.json"),
            "--project",
            str(project),
        ]
    )

    assert result == 0
    assert calls["context"] is context
    assert calls["provider_kwargs"]["artifact"] == "stable-artifact"
    assert calls["provider_kwargs"]["evidence"] == {}
    assert calls["provider_kwargs"]["decisions"] == {}
    assert calls["emitted"] == ({"status": "PASS"}, tmp_path / "report.json")
    checked_path, checked = calls["check"]
    assert checked_path == target
    assert checked["policy"] is policy
    assert checked["external"] is False
    assert checked["compare_api"] == tmp_path / "previous.json"
    assert checked["snapshot_path"] == tmp_path / "snapshot.json"
    assert checked["supply_chain_report"] == tmp_path / "supply-chain.json"


def test_main_text_mode_supports_legacy_path_and_strict_output(
    tmp_path: Path, monkeypatch: Any, capsys: Any
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    context_file = tmp_path / "context.json"
    context_file.write_text("{}", encoding="utf-8")
    context = SimpleNamespace(name="explicit-context")
    finding = SimpleNamespace(
        status="PASS", code="Q001", path="src/module.py", line=3, message="checked"
    )
    report = SimpleNamespace(
        status="PASS",
        findings=[finding],
        to_dict=lambda: {"status": "PASS"},
        exit_code=lambda strict: int(strict),
    )
    checked: dict[str, Any] = {}

    monkeypatch.setattr(cli.ApplicabilityContext, "from_dict", lambda value: context)
    monkeypatch.setattr(
        cli,
        "GitFrameworkPolicyProvider",
        lambda *args, **kwargs: SimpleNamespace(evaluate=lambda value: None),
    )
    monkeypatch.setattr(
        cli, "check", lambda path, **kwargs: checked.update(path=path, kwargs=kwargs) or report
    )
    monkeypatch.setattr(
        common, "write_json", lambda output, value: checked.update(output=output, value=value)
    )

    result = cli.main(
        [
            "src/auditcore.tools.quality.sample.py",
            "--strict",
            "--output",
            str(tmp_path / "report.json"),
            "--context",
            str(context_file),
            "--project",
            str(project),
        ]
    )

    assert result == 1
    assert checked["path"] == Path("src/auditcore/tools/quality.sample.py")
    assert checked["kwargs"]["external"] is True
    assert checked["output"] == tmp_path / "report.json"
    assert "Quality: PASS; 1 findings" in capsys.readouterr().out


def test_main_reports_expected_errors_without_exception_text(
    tmp_path: Path, monkeypatch: Any, capsys: Any
) -> None:
    monkeypatch.setattr(
        cli,
        "GitFrameworkPolicyProvider",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("private details")),
    )

    result = cli.main([str(tmp_path / "missing.py"), "--project", str(tmp_path)])

    captured = capsys.readouterr()
    assert result == 2
    assert "Quality error: ValueError" in captured.err
    assert "private details" not in captured.err
