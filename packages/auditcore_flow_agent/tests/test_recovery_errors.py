"""Fehler an Persistenz- und Bestätigungsgrenzen dürfen Ressourcen nicht verwechseln."""

import json

import pytest

from auditcore_flow_agent import JobSpec, Outcome, Queue, ResourceRequest, State


@pytest.mark.parametrize("pausing", [False, True])
def test_corrupt_active_contract_releases_only_after_stop(queue, pausing):
    queue.enqueue(JobSpec("a", "x", "embed"))
    lease = queue.claim()
    if pausing:
        queue.drain_node(lease.node_id)
    with queue.database.transaction() as conn:
        conn.execute("UPDATE jobs SET spec='{}'")
    queue.recover_expired()
    assert queue.pending_stops()[0].token == lease.token
    assert queue.allocations()
    assert queue.confirm_stopped(lease.token)
    assert not queue.allocations()
    assert queue.events("x", "a")[-1][1] == "failed"


@pytest.mark.parametrize("corruption", ["not-json", "wrong-id"])
def test_invalid_stored_inventory_or_identity_does_not_block(queue, corruption):
    queue.enqueue(JobSpec("a", "x", "embed"))
    queue.enqueue(JobSpec("b", "x", "embed"))
    with queue.database.transaction() as conn:
        if corruption == "not-json":
            conn.execute("UPDATE nodes SET snapshot='[]' WHERE node_id='fast'")
        else:
            spec = json.loads(conn.execute("SELECT spec FROM jobs WHERE job_id='a'").fetchone()[0])
            spec["job_id"] = "forged"
            conn.execute("UPDATE jobs SET spec=? WHERE job_id='a'", (json.dumps(spec),))
    lease = queue.claim()
    if corruption == "not-json":
        assert lease.node_id == "fallback"
    else:
        assert lease.job.job_id == "b"
        assert queue.events("x", "a")[-1][1] == "failed"


def test_exhausted_waiting_job_cannot_start_after_repair(queue):
    queue.enqueue(JobSpec("a", "x", "embed"))
    queue.enqueue(JobSpec("b", "x", "embed"))
    with queue.database.transaction() as conn:
        conn.execute("UPDATE jobs SET attempts=3 WHERE job_id='a'")
    assert queue.claim().job.job_id == "b"
    assert queue.get("x", "a").state == State.FAILED


def test_invalid_defer_and_regressing_progress_keep_original_lease(queue):
    queue.enqueue(JobSpec("a", "x", "embed"))
    lease = queue.claim()
    assert queue.heartbeat(lease.token, progress=4)
    with pytest.raises(ValueError, match="zurückgehen"):
        queue.heartbeat(lease.token, progress=3)
    with pytest.raises(ValueError, match="zukünftigen"):
        queue.finish(lease.token, Outcome("deferred", retry_at=1))
    assert queue.get("x", "a").state == State.RUNNING
    assert queue.allocations()
    assert queue.finish(lease.token, Outcome("succeeded"))


def test_unknown_or_finished_work_does_not_create_stops(queue):
    assert queue.drain_node("missing") == ()
    assert not queue.cancel("x", "missing")
    queue.enqueue(JobSpec("a", "x", "embed"))
    assert queue.cancel("x", "a")
    assert not queue.cancel("x", "a")
    assert not queue.pending_stops()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"node_id": "missing", "gpu_ids": ()},
        {"node_id": "fast", "gpu_ids": ("missing",)},
        {"node_id": "fast", "gpu_ids": (), "cpus": 9},
        {"node_id": "fast", "gpu_ids": (), "memory_mb": 40000},
    ],
)
def test_invalid_training_reservation_does_not_consume_capacity(queue, kwargs):
    with pytest.raises(ValueError):
        queue.reserve(**kwargs, reason="training")
    assert not queue.allocations()


def test_waiting_work_skips_ram_limited_node(queue):
    queue.enqueue(JobSpec("a", "x", "embed", resources=ResourceRequest(memory_mb=40000)))
    queue.enqueue(JobSpec("b", "x", "embed"))
    assert queue.claim().job.job_id == "b"


def test_queue_requires_durable_file():
    with pytest.raises(ValueError):
        Queue(":memory:")


def test_scope_limit_skips_ready_work_without_blocking_other_scope(queue):
    for name in ("a", "b", "c"):
        queue.enqueue(JobSpec(name, "x", "embed"))
    assert queue.claim() is not None
    assert queue.claim() is not None
    queue.enqueue(JobSpec("d", "y", "embed"))
    assert queue.claim().job.scope == "y"
    assert queue.get("x", "c").state == State.WAITING
