import os
import sys
import time
from pathlib import Path

import pytest

from auditcore_flow_agent import (
    Command,
    JobSpec,
    Node,
    Queue,
    RetryPolicy,
    State,
    execute,
    run_command,
)

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX-Prozesswächter")


def test_hanging_process_is_killed_and_output_is_bounded():
    code = "import os,time; os.write(1,b'x'*100000); os.write(2,b'y'*100000); time.sleep(60)"
    result = run_command(
        Command((sys.executable, "-c", code)),
        timeout_s=0.3,
        poll_s=0.01,
        stop_grace_s=0.1,
        output_limit=100,
    )
    assert result.reason == "timeout"
    assert result.elapsed_s < 3
    assert result.stdout_tail == "x" * 100
    assert result.stderr_tail == "y" * 100
    assert result.returncode != 0


def test_program_exit_and_utf8_output():
    result = run_command(Command((sys.executable, "-c", "print('Erledigt: ÄÖÜ')")), timeout_s=3)
    assert result.returncode == 0 and result.reason == "exited"
    assert result.stdout_tail.strip() == "Erledigt: ÄÖÜ"


def test_revoked_lease_prevents_process_start(tmp_path: Path):
    path = tmp_path / "must-not-exist"
    code = f"from pathlib import Path; Path({str(path)!r}).touch()"
    result = run_command(Command((sys.executable, "-c", code)), timeout_s=3, tick=lambda: False)
    assert result.reason == "lease_lost"
    assert not path.exists()


def test_stubborn_child_process_is_killed_with_parent(tmp_path: Path):
    path = tmp_path / "child.pid"
    child = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)"
    parent = (
        "import subprocess,sys,time; from pathlib import Path; "
        f"p=subprocess.Popen([sys.executable,'-c',{child!r}]); "
        f"Path({str(path)!r}).write_text(str(p.pid)); time.sleep(60)"
    )
    run_command(
        Command((sys.executable, "-c", parent)), timeout_s=0.5, poll_s=0.01, stop_grace_s=0.1
    )
    pid = int(path.read_text())
    status = Path(f"/proc/{pid}/stat")
    deadline = time.monotonic() + 2
    while status.exists() and status.read_text().split()[2] != "Z":
        assert time.monotonic() < deadline, "Unterprozess blieb aktiv"
        time.sleep(0.01)


def test_tick_failure_still_terminates_process(tmp_path: Path):
    calls = 0

    def broken_tick():
        nonlocal calls
        calls += 1
        if calls > 2:
            raise RuntimeError("Koordinator nicht erreichbar")
        return True

    with pytest.raises(RuntimeError, match="Koordinator"):
        run_command(
            Command((sys.executable, "-c", "import time; time.sleep(60)")),
            timeout_s=3,
            tick=broken_tick,
            stop_grace_s=0.1,
        )


def test_end_to_end_timeout_does_not_block_good_job(tmp_path: Path):
    queue = Queue(tmp_path / "jobs.sqlite")
    queue.publish_node(Node("worker", time.time(), 1, 4000, ("test",)))
    queue.enqueue(JobSpec("a", "app", "test", timeout_s=0.2, retry=RetryPolicy(1)))
    queue.enqueue(JobSpec("b", "app", "test"))
    bad = queue.claim()
    result = execute(
        queue, bad, Command((sys.executable, "-c", "import time; time.sleep(60)")), stop_grace_s=0.1
    )
    assert result.reason in ("timeout", "lease_lost")
    assert queue.get("app", "a").state == State.FAILED
    good = queue.claim()
    assert good.job.job_id == "b"
    execute(queue, good, Command((sys.executable, "-c", "print('ok')")))
    assert queue.get("app", "b").state == State.SUCCEEDED
    assert queue.allocations() == ()


def test_unlaunchable_program_releases_claim(tmp_path: Path):
    queue = Queue(tmp_path / "jobs.sqlite")
    queue.publish_node(Node("worker", time.time(), 1, 4000, ("test",)))
    queue.enqueue(JobSpec("a", "app", "test", retry=RetryPolicy(1)))
    lease = queue.claim()
    with pytest.raises(FileNotFoundError):
        execute(queue, lease, Command((str(tmp_path / "no-program"),)))
    assert queue.get("app", "a").state == State.FAILED
    assert queue.allocations() == ()
