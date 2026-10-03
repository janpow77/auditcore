from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from auditcore_flow_agent import (
    Gpu,
    JobSpec,
    Node,
    Outcome,
    Queue,
    ResourceRequest,
    SchedulerPolicy,
)


def gpu_job(job_id="job", **kwargs):
    return JobSpec(job_id, "x", "embed", resources=ResourceRequest(gpu_count=1), **kwargs)


def test_fast_machine_is_preferred_and_fallback_receives_overflow(queue):
    queue.policy = SchedulerPolicy(max_active_per_scope=10)
    for name in ("a", "b", "c"):
        queue.enqueue(gpu_job(name))
    leases = [queue.claim() for _ in range(3)]
    assert [lease.node_id for lease in leases] == ["fast", "fast", "fallback"]
    assert len({(lease.node_id, lease.gpu_ids) for lease in leases}) == 3


def test_training_reservation_blocks_only_its_cards(queue):
    reservation = queue.reserve("fast", ("0", "1"), reason="training")
    queue.enqueue(gpu_job())
    assert queue.claim().node_id == "fallback"
    assert queue.release_reservation(reservation)
    assert not queue.release_reservation(reservation)
    queue.enqueue(gpu_job("next"))
    assert queue.claim().node_id == "fast"


def test_two_gpu_job_is_atomic_and_does_not_block_smaller_job(queue):
    queue.reserve("fast", ("0",), reason="interactive")
    queue.enqueue(
        JobSpec("large", "x", "train", priority=100, resources=ResourceRequest(gpu_count=2))
    )
    queue.enqueue(gpu_job("small"))
    lease = queue.claim()
    assert lease.job.job_id == "small"
    assert lease.node_id == "fast" and lease.gpu_ids == ("1",)


def test_scope_limit_leaves_capacity_for_another_application(queue):
    for name in ("a", "b", "c"):
        queue.enqueue(JobSpec(name, "bulk", "embed", priority=20))
    queue.enqueue(JobSpec("interactive", "other", "chat"))
    assert [queue.claim().job.scope for _ in range(3)] == ["bulk", "bulk", "other"]


def test_aging_prevents_new_high_priority_jobs_overtaking_forever(queue, clock):
    queue.policy = SchedulerPolicy(aging_interval_s=1)
    queue.enqueue(JobSpec("old", "x", "embed"))
    clock.now += 20
    queue.enqueue(JobSpec("new", "x", "embed", priority=10))
    assert queue.claim().job.job_id == "old"


def test_stale_and_future_reports_are_not_used(queue, clock):
    clock.now += 100
    queue.enqueue(gpu_job())
    assert queue.claim() is None
    future = Node("future", clock() + 1, 4, 4000, ("embed",), (Gpu("0", 4000),))
    queue.publish_node(future)
    assert queue.claim() is None


def test_old_report_cannot_overwrite_user_block(queue, clock):
    blocked = Node("fast", clock() + 1, 8, 32000, ("embed",), (Gpu("0", 16000),), accepting=False)
    assert queue.publish_node(blocked)
    assert not queue.publish_node(replace(blocked, accepting=True, observed_at=clock()))
    clock.now += 1
    queue.enqueue(gpu_job())
    assert queue.claim().node_id == "fallback"


def test_models_and_node_restrictions_are_enforced(queue):
    queue.enqueue(gpu_job("absent-model", model="missing", priority=100))
    queue.enqueue(gpu_job("wrong-node", allowed_nodes=("nonexistent",), priority=100))
    queue.enqueue(gpu_job("soft-preference", preferred_nodes=("nonexistent",), model="bge"))
    assert queue.claim().job.job_id == "soft-preference"


def test_gpu_memory_and_user_block_are_respected(queue, clock):
    queue.publish_node(
        Node(
            "fast",
            clock() + 1,
            8,
            32000,
            ("embed",),
            (Gpu("0", 16000, blocked=True), Gpu("1", 100)),
        )
    )
    clock.now += 1
    queue.enqueue(
        JobSpec("a", "x", "embed", resources=ResourceRequest(gpu_count=1, min_vram_mb=9000))
    )
    assert queue.claim() is None


def test_cpu_ram_and_manual_reservations_share_one_budget(queue):
    reservation = queue.reserve("fast", (), reason="cpu-training", cpus=8)
    queue.enqueue(JobSpec("a", "x", "embed", resources=ResourceRequest(cpus=5)))
    assert queue.claim() is None
    queue.release_reservation(reservation)
    assert queue.claim().node_id == "fast"


def test_concurrent_coordinators_never_claim_a_gpu_twice(queue, clock):
    queue.policy = SchedulerPolicy(max_active_per_scope=20)
    for index in range(20):
        queue.enqueue(gpu_job(str(index)))

    def claim(_):
        return Queue(queue.database.path, policy=queue.policy, clock=clock).claim()

    with ThreadPoolExecutor(max_workers=8) as pool:
        leases = [lease for lease in pool.map(claim, range(20)) if lease is not None]
    assert len(leases) == 3
    assert len({(lease.node_id, lease.gpu_ids) for lease in leases}) == 3
    assert len({lease.job.job_id for lease in leases}) == 3


def test_warm_model_beats_cold_card(queue, clock):
    queue.publish_node(
        Node(
            "fast",
            clock() + 1,
            8,
            32000,
            ("embed",),
            (Gpu("0", 8000, ("bge",)), Gpu("1", 16000)),
            ("bge",),
        )
    )
    clock.now += 1
    queue.enqueue(gpu_job(model="bge", allowed_nodes=("fast",)))
    lease = queue.claim()
    assert lease.gpu_ids == ("0",)
    assert not queue.release_reservation(lease.token)
    queue.finish(lease.token, Outcome("succeeded"))
