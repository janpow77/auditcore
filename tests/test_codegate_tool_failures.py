"""Failures of the measuring tools (ruff, mypy) are reported with their cause."""

from __future__ import annotations

import signal
import subprocess
import sys

import pytest

from auditcore.tools.quality import codegate_python
from auditcore.tools.quality.codegate_python import ToolError, run_measuring_tool


def _exit(code: int, stderr: str = "") -> list[str]:
    script = f"import sys; sys.stderr.write({stderr!r}); sys.exit({code})"
    return [sys.executable, "-c", script]


def _killed_by(signum: int) -> list[str]:
    return [sys.executable, "-c", f"import os; os.kill(os.getpid(), {signum})"]


def test_accepted_exit_code_passes() -> None:
    assert run_measuring_tool("mypy", _exit(1), (0, 1)).returncode == 1


def test_unexpected_exit_code_names_code_and_output() -> None:
    with pytest.raises(ToolError, match=r"ruff failed \(exit code 2\): kaputt"):
        run_measuring_tool("ruff", _exit(2, "kaputt"), (0,))


def test_silent_failure_says_so() -> None:
    with pytest.raises(ToolError, match=r"\(exit code 3\): no output"):
        run_measuring_tool("ruff", _exit(3), (0,))


def test_signal_is_named_after_one_repeat(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    real_run = subprocess.run

    def counting_run(command: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return real_run(command, **options)  # type: ignore[no-any-return, call-overload]

    monkeypatch.setattr(codegate_python.subprocess, "run", counting_run)
    with pytest.raises(ToolError, match=r"terminated by signal SIGTERM"):
        run_measuring_tool("ruff", _killed_by(signal.SIGTERM), (0,))
    assert len(calls) == 2


def test_signal_once_then_success_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    results = iter((-signal.SIGKILL, 0))

    def flaky_run(command: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, next(results), "[]", "")

    monkeypatch.setattr(codegate_python.subprocess, "run", flaky_run)
    assert run_measuring_tool("ruff", ["ruff"], (0,)).returncode == 0


def test_exit_code_is_not_repeated(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def failing_run(command: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        calls.append(1)
        return subprocess.CompletedProcess(command, 2, "", "")

    monkeypatch.setattr(codegate_python.subprocess, "run", failing_run)
    with pytest.raises(ToolError):
        run_measuring_tool("ruff", ["ruff"], (0,))
    assert calls == [1]


def test_unknown_signal_number_is_reported() -> None:
    process = subprocess.CompletedProcess(["ruff"], -250, "", "")
    assert "terminated by signal 250" in codegate_python._describe_failure("ruff", process)
