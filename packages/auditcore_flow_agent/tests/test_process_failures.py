"""Fehler im Wächter müssen den Ressourcenvertrag erhalten."""

import os
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from auditcore_flow_agent import (
    Command,
    JobSpec,
    ProcessNotStopped,
    State,
    execute,
    process,
    run_command,
    worker,
)


def test_term_resistant_main_process_requires_kill():
    code = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)"
    result = run_command(Command((sys.executable, "-c", code)), timeout_s=0.4, stop_grace_s=0.1)
    assert result.reason == "timeout" and result.returncode == -9


def test_closed_output_channels_do_not_disable_timeout():
    code = "import os,time; os.close(1); os.close(2); time.sleep(60)"
    result = run_command(Command((sys.executable, "-c", code)), timeout_s=0.2, stop_grace_s=0.1)
    assert result.reason == "timeout" and result.elapsed_s < 3


def test_unconfirmed_process_end_retains_lease(queue, monkeypatch):
    queue.enqueue(JobSpec("a", "x", "embed"))
    lease = queue.claim()

    def cannot_stop(*args, **kwargs):
        raise ProcessNotStopped("Stop nicht bestätigt")

    monkeypatch.setattr(worker, "run_command", cannot_stop)
    with pytest.raises(ProcessNotStopped):
        execute(queue, lease, Command((sys.executable,)))
    assert queue.allocations()
    assert queue.get("x", "a").state == State.RUNNING


def test_kill_without_wait_confirmation_is_not_success(monkeypatch):
    def stuck_wait(*, timeout):
        raise subprocess.TimeoutExpired("test", timeout)

    monkeypatch.setattr(process, "_signal_group", lambda *args: None)
    with pytest.raises(ProcessNotStopped):
        process._stop(SimpleNamespace(pid=1, wait=stuck_wait), 0.1)


def test_open_writer_prevents_false_stop_confirmation():
    read_fd, write_fd = os.pipe()
    other_read, other_write = os.pipe()
    output = process._Output((os.fdopen(read_fd, "rb"), os.fdopen(other_read, "rb")), 100)
    try:
        with pytest.raises(ProcessNotStopped):
            output.drain(0.02)
    finally:
        output.close()
        os.close(write_fd)
        os.close(other_write)


def test_missing_progress_source_fails_before_execution(queue):
    queue.enqueue(JobSpec("a", "x", "embed", stall_timeout_s=2))
    lease = queue.claim()
    with pytest.raises(ValueError, match="Fortschrittsquelle"):
        execute(queue, lease, Command((sys.executable,)))
    assert queue.get("x", "a").state == State.FAILED
    assert not queue.allocations()


def test_exception_after_revocation_confirms_stopped_attempt(queue, monkeypatch):
    queue.enqueue(JobSpec("a", "x", "embed"))
    lease = queue.claim()

    def revoked(*args, **kwargs):
        queue.cancel("x", "a")
        raise RuntimeError("Verbindung unterbrochen")

    monkeypatch.setattr(worker, "run_command", revoked)
    with pytest.raises(RuntimeError):
        execute(queue, lease, Command((sys.executable,)))
    assert queue.get("x", "a").state == State.CANCELLED
    assert not queue.allocations()


def test_non_posix_is_rejected_before_start(monkeypatch):
    monkeypatch.setattr(process, "os", SimpleNamespace(name="nt"))
    with pytest.raises(NotImplementedError):
        run_command(Command((sys.executable,)), timeout_s=1)


def test_lease_lost_after_launch_terminates_process():
    started = time.monotonic()
    result = run_command(
        Command((sys.executable, "-c", "import time; time.sleep(60)")),
        timeout_s=3,
        tick=lambda: time.monotonic() - started < 0.1,
        stop_grace_s=0.1,
    )
    assert result.reason == "lease_lost" and result.elapsed_s < 3
