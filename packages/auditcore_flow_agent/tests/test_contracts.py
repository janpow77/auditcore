from dataclasses import replace

import pytest

from auditcore_flow_agent import Command, Gpu, JobSpec, Node, Outcome, ResourceRequest, RetryPolicy
from auditcore_flow_agent.codec import encode, read_job, read_node
from auditcore_flow_agent.models import payload_dict


@pytest.mark.parametrize(
    "field,value",
    [
        ("timeout_s", 0),
        ("lease_s", float("nan")),
        ("stall_timeout_s", -1),
        ("not_before", float("inf")),
        ("priority", True),
        ("priority", -1),
        ("job_id", ""),
        ("scope", " "),
        ("dependencies", ("a",)),
        ("allowed_nodes", ("same", "same")),
        ("payload", {"bad": float("nan")}),
        ("payload", ["no-object"]),
        ("resources", None),
    ],
)
def test_invalid_contracts_fail_before_enqueue(field, value):
    with pytest.raises(ValueError):
        replace(JobSpec("a", "app", "embed"), **{field: value})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_attempts": 0},
        {"max_attempts": True},
        {"initial_delay_s": 0},
        {"max_delay_s": 1},
        {"max_delay_s": float("inf")},
    ],
)
def test_retry_policy_rejects_unbounded_or_invalid_values(kwargs):
    with pytest.raises(ValueError):
        RetryPolicy(**kwargs)


def test_serialization_roundtrip_keeps_contract():
    job = JobSpec(
        "a",
        "app",
        "embed",
        payload={"text": ["a", "b"]},
        resources=ResourceRequest(2, 2000, 1, 1000),
        model="bge",
        preferred_nodes=("fast",),
        stall_timeout_s=30,
    )
    assert read_job(encode(job)) == job
    node = Node("fast", 1000, 8, 32000, ("embed",), (Gpu("0", 8000, ("bge",)),), ("bge",))
    assert read_node(encode(node)) == node


def test_cpu_request_cannot_claim_vram():
    with pytest.raises(ValueError, match="VRAM"):
        ResourceRequest(min_vram_mb=100)


def test_defer_requires_future_date_contract():
    with pytest.raises(ValueError):
        Outcome("deferred")
    with pytest.raises(ValueError):
        Outcome("succeeded", retry_at=1000)


def test_backoff_stays_bounded_for_large_attempt_count():
    assert RetryPolicy().delay(1000000) == 300


def test_mutable_payload_copy_does_not_change_stored_contract():
    job = JobSpec("a", "x", "embed", payload={"texts": ["one"]})
    payload = payload_dict(job)
    payload["texts"].append("two")
    assert payload_dict(job) == {"texts": ["one"]}


@pytest.mark.parametrize("argv", [(), ("",), ("program", "bad\x00argument")])
def test_unsafe_command_contract_is_rejected(argv):
    with pytest.raises(ValueError):
        Command(argv)


def test_invalid_flags_and_outcomes_are_rejected():
    with pytest.raises(ValueError):
        Gpu("0", 100, blocked="false")
    with pytest.raises(ValueError):
        Node("worker", 1000, 1, 1000, ("test",), accepting="false")
    with pytest.raises(ValueError):
        Outcome("unknown")


@pytest.mark.parametrize("field,value", [("dependencies", "not-list"), ("resources", [])])
def test_malformed_persisted_job_fields_are_rejected(field, value):
    import json

    data = json.loads(encode(JobSpec("a", "x", "embed")))
    data[field] = value
    with pytest.raises(ValueError):
        read_job(json.dumps(data))


def test_inventory_requires_gpu_array():
    import json

    data = json.loads(encode(Node("worker", 1000, 1, 1000, ("test",))))
    data["gpus"] = {}
    with pytest.raises(ValueError):
        read_node(json.dumps(data))
