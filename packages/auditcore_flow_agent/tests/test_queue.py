from dataclasses import replace
from pathlib import Path

import pytest

from auditcore_flow_agent import JobSpec, Outcome, Queue, ResourceRequest, RetryPolicy, State


def test_broken_job_does_not_block_next(queue):
    queue.enqueue(JobSpec("bad", "video", "embed", priority=10))
    queue.enqueue(JobSpec("good", "video", "embed"))
    first = queue.claim()
    assert first.job.job_id == "bad"
    assert queue.finish(first.token, Outcome("permanent", "Ungültige Eingabe"))
    second = queue.claim()
    assert second.job.job_id == "good"
    assert queue.finish(second.token, Outcome("succeeded"))
    assert queue.get("video", "bad").state == State.FAILED
    assert queue.get("video", "good").state == State.SUCCEEDED


def test_unavailable_or_future_work_does_not_block_images(queue):
    queue.enqueue(JobSpec("transcript", "video", "transcribe", priority=100))
    queue.enqueue(JobSpec("material", "video", "chat", not_before=9999, priority=100))
    queue.enqueue(JobSpec("picture", "video", "image"))
    assert queue.claim().job.job_id == "picture"


def test_dependencies_are_local_and_do_not_block_unrelated_jobs(queue):
    queue.enqueue(JobSpec("input", "one", "embed"))
    queue.enqueue(JobSpec("dependent", "one", "chat", dependencies=("input",)))
    queue.enqueue(JobSpec("input", "two", "embed"))
    first = queue.claim()
    assert first.job.scope == "one"
    queue.finish(first.token, Outcome("permanent", "Defekt"))
    other = queue.claim()
    assert other.job.scope == "two"
    assert queue.get("one", "dependent").state == State.BLOCKED


def test_missing_or_cross_scope_dependencies_are_rejected(queue):
    queue.enqueue(JobSpec("parent", "other", "embed"))
    with pytest.raises(ValueError, match="Voraussetzung"):
        queue.enqueue(JobSpec("child", "mine", "embed", dependencies=("parent",)))
    assert queue.get("mine", "child") is None


def test_success_unblocks_child_and_failure_propagates_transitively(queue):
    for spec in (
        JobSpec("a", "x", "embed"),
        JobSpec("b", "x", "embed", dependencies=("a",)),
        JobSpec("c", "x", "embed", dependencies=("b",)),
    ):
        queue.enqueue(spec)
    first = queue.claim()
    queue.finish(first.token, Outcome("succeeded"))
    second = queue.claim()
    assert second.job.job_id == "b"
    queue.finish(second.token, Outcome("permanent", "Defekt"))
    assert queue.claim() is None
    assert queue.get("x", "c").state == State.BLOCKED


def test_bounded_retries_survive_coordinator_restart(queue, clock):
    spec = JobSpec("bad", "x", "embed", retry=RetryPolicy(3, 1, 10))
    queue.enqueue(spec)
    for attempt in range(1, 4):
        queue = Queue(queue.database.path, clock=clock)
        lease = queue.claim()
        assert lease.attempt == attempt
        queue.finish(lease.token, Outcome("retryable", "Netzfehler"))
        if attempt < 3:
            assert queue.claim() is None
            clock.now += spec.retry.delay(attempt)
    assert queue.claim() is None
    assert queue.get("x", "bad").state == State.FAILED
    assert queue.get("x", "bad").attempts == 3


def test_capacity_wait_releases_resources_without_consuming_attempt(queue, clock):
    queue.enqueue(JobSpec("a", "x", "embed", resources=ResourceRequest(gpu_count=1)))
    lease = queue.claim()
    queue.finish(lease.token, Outcome("deferred", "Modell lädt", retry_at=clock() + 10))
    assert queue.allocations() == ()
    assert queue.get("x", "a").attempts == 0
    assert queue.claim() is None
    clock.now += 10
    assert queue.claim().attempt == 1


def test_duplicate_submission_is_idempotent_but_conflict_fails(queue):
    job = JobSpec("a", "x", "embed", payload={"text": ["one", "two"]})
    assert queue.enqueue(job) == queue.enqueue(job)
    with pytest.raises(ValueError, match="anderen Vertrag"):
        queue.enqueue(replace(job, capability="chat"))
    assert len(queue.events("x", "a")) == 1


def test_payload_is_deep_frozen(queue):
    source = {"list": [1, 2]}
    spec = JobSpec("a", "x", "embed", payload=source)
    source["list"].append(3)
    assert spec.payload["list"] == (1, 2)
    with pytest.raises(TypeError):
        spec.payload["more"] = 1
    queue.enqueue(spec)
    assert queue.get("x", "a").spec.payload["list"] == (1, 2)


def test_corrupt_job_is_quarantined_instead_of_stopping_selection(queue):
    queue.enqueue(JobSpec("a", "x", "embed"))
    queue.enqueue(JobSpec("b", "x", "embed"))
    with queue.database.transaction() as conn:
        conn.execute("UPDATE jobs SET spec='broken json' WHERE job_id='a'")
    assert queue.claim().job.job_id == "b"
    assert queue.events("x", "a")[-1][1] == "failed"


def test_schema_version_is_checked(tmp_path: Path):
    queue = Queue(tmp_path / "db")
    with queue.database.transaction() as conn:
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(ValueError, match="Datenbankversion"):
        Queue(tmp_path / "db")
