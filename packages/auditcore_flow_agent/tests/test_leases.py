from auditcore_flow_agent import JobSpec, Outcome, Queue, ResourceRequest, RetryPolicy, State


def test_expired_lease_keeps_gpu_fenced_until_stop_confirmation(queue, clock):
    queue.enqueue(JobSpec("a", "x", "embed", resources=ResourceRequest(gpu_count=1), lease_s=2))
    lease = queue.claim()
    clock.now += 3
    assert queue.recover_expired() == (lease.token,)
    assert queue.get("x", "a").state == State.RECOVERING
    assert len(queue.allocations()) == 1
    assert not queue.heartbeat(lease.token)
    assert not queue.finish(lease.token, Outcome("succeeded"))
    restarted = Queue(queue.database.path, clock=clock)
    assert restarted.pending_stops()[0].token == lease.token
    assert restarted.confirm_stopped(lease.token)
    assert restarted.allocations() == ()
    assert restarted.get("x", "a").state == State.RETRY
    assert not restarted.confirm_stopped(lease.token)


def test_old_attempt_cannot_finish_new_attempt(queue, clock):
    queue.enqueue(JobSpec("a", "x", "embed", retry=RetryPolicy(3, 1, 2)))
    old = queue.claim()
    queue.finish(old.token, Outcome("retryable"))
    clock.now += 1
    new = queue.claim()
    assert old.token != new.token
    assert not queue.finish(old.token, Outcome("succeeded"))
    assert not queue.heartbeat(old.token)
    assert queue.finish(new.token, Outcome("succeeded"))


def test_heartbeat_cannot_extend_absolute_deadline(queue, clock):
    queue.enqueue(JobSpec("a", "x", "embed", timeout_s=5, lease_s=2))
    lease = queue.claim()
    for step in range(1, 5):
        clock.now += 1
        assert queue.heartbeat(lease.token, progress=step)
    clock.now += 1
    assert not queue.heartbeat(lease.token, progress=5)
    assert queue.get("x", "a").state == State.RECOVERING


def test_heartbeat_is_not_progress(queue, clock):
    queue.enqueue(JobSpec("a", "x", "embed", lease_s=2, stall_timeout_s=4))
    lease = queue.claim()
    for _ in range(3):
        clock.now += 1
        assert queue.heartbeat(lease.token, progress=0)
    clock.now += 1
    assert not queue.heartbeat(lease.token, progress=1)
    assert "Fortschritt" in queue.get("x", "a").error


def test_real_progress_resets_only_progress_deadline(queue, clock):
    queue.enqueue(JobSpec("a", "x", "embed", lease_s=10, stall_timeout_s=4))
    lease = queue.claim()
    clock.now += 3
    assert queue.heartbeat(lease.token, progress=1)
    clock.now += 3
    assert queue.heartbeat(lease.token, progress=2)
    assert queue.finish(lease.token, Outcome("succeeded"))


def test_repeated_worker_crashes_consume_attempt_budget(queue, clock):
    queue.enqueue(JobSpec("a", "x", "embed", lease_s=1, retry=RetryPolicy(2, 1, 1)))
    for _ in range(2):
        lease = queue.claim()
        clock.now += 2
        queue.recover_expired()
        queue.confirm_stopped(lease.token)
        clock.now += 1
    assert queue.get("x", "a").state == State.FAILED
    assert queue.get("x", "a").attempts == 2
    assert queue.claim() is None


def test_cancellation_holds_resources_until_actual_stop(queue):
    queue.enqueue(JobSpec("a", "x", "embed", resources=ResourceRequest(gpu_count=1)))
    lease = queue.claim()
    assert queue.cancel("x", "a")
    assert queue.get("x", "a").state == State.CANCELLING
    assert not queue.heartbeat(lease.token)
    assert queue.allocations()
    assert queue.confirm_stopped(lease.token)
    assert queue.get("x", "a").state == State.CANCELLED
    assert not queue.allocations()


def test_drain_returns_work_to_queue_and_uses_other_node(queue, clock):
    queue.enqueue(JobSpec("a", "x", "embed", retry=RetryPolicy(3, 1, 1)))
    lease = queue.claim()
    assert queue.drain_node("fast") == (lease.token,)
    assert queue.confirm_stopped(lease.token)
    clock.now += 1
    assert queue.claim().node_id == "fallback"


def test_dead_worker_does_not_exhaust_scope_limit_on_healthy_worker(queue, clock):
    for name in ("a", "b", "c"):
        queue.enqueue(
            JobSpec(name, "x", "embed", resources=ResourceRequest(gpu_count=1), lease_s=2)
        )
    first, second = queue.claim(), queue.claim()
    assert first.node_id == second.node_id == "fast"
    clock.now += 3
    healthy = queue.claim()
    assert healthy is not None and healthy.node_id == "fallback"
    assert healthy.job.job_id == "c"
    assert len(queue.pending_stops()) == 2
    assert len(queue.allocations()) == 3
