"""Vertragstest über die installierte öffentliche API ohne Quellbaum."""

import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from auditcore_flow_agent import Command, JobSpec, Node, Queue, State, execute

with TemporaryDirectory() as directory:
    queue = Queue(Path(directory) / "jobs.sqlite3")
    queue.publish_node(Node("worker", time.time(), 2, 1024, ("smoke",)))
    queue.enqueue(JobSpec("one", "smoke", "smoke", timeout_s=10))
    lease = queue.claim()
    assert lease is not None
    result = execute(queue, lease, Command((sys.executable, "-c", "print('fertig')")))
    assert result.returncode == 0 and result.stdout_tail.strip() == "fertig"
    recovered = Queue(Path(directory) / "jobs.sqlite3").get("smoke", "one")
    assert recovered is not None and recovered.state == State.SUCCEEDED
