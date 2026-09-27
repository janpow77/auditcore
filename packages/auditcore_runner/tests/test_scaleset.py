from __future__ import annotations

import pytest
from fake_scaleset import QUEUE, FakeActions, jwt, message

from auditcore_runner import scaleset
from auditcore_runner.profile import Target


def client(fake: FakeActions, now: float = 1_000_000_000.0) -> scaleset.ScaleSetClient:
    return scaleset.ScaleSetClient(Target("repo", "owner/repo"), lambda: "gh-token", fake, clock=lambda: now)


def test_admin_connection_is_cached_until_expiry() -> None:
    fake = FakeActions()
    api = client(fake)
    assert api.runner_group_id("default") == 7
    assert api.find_scale_set("host-cpu", 7) is None
    registrations = [c for c in fake.calls if c[1].endswith("/runner-registration")]
    assert len(registrations) == 1
    assert fake.calls[0][1] == "https://api.github.com/repos/owner/repo/actions/runners/registration-token"


def test_expired_admin_token_is_renewed() -> None:
    fake = FakeActions(admin_expires=1_000_000_030)
    api = client(fake)
    api.runner_group_id("default")
    api.runner_group_id("default")
    assert len([c for c in fake.calls if c[1].endswith("/runner-registration")]) == 2


def test_ensure_scale_set_creates_once() -> None:
    fake = FakeActions()
    api = client(fake)
    first = api.ensure_scale_set("host-cpu", 7, ("host-cpu",))
    assert api.ensure_scale_set("host-cpu", 7, ("host-cpu",)) == first
    assert fake.scale_sets == {"host-cpu": first}


def test_session_messages_and_deletion() -> None:
    fake = FakeActions(messages=[message(3, assigned=4, running=1, jobs=("JobAssigned", "JobStarted"))])
    api = client(fake)
    session = api.create_session(100, "host")
    assert session.statistics.assigned == 1 and session.queue_url == QUEUE
    received = api.get_message(session, 0, 5)
    assert received is not None and received.statistics.waiting == 3
    assert received.job_types == ("JobAssigned", "JobStarted")
    api.delete_message(session, received.message_id)
    assert fake.deleted_messages == [3]
    assert api.get_message(session, 3, 5) is None
    assert fake.calls[-1][1] == QUEUE + "&lastMessageId=3" and fake.calls[-1][2]["X-ScaleSetMaxCapacity"] == "5"


def test_expired_queue_token_and_refresh() -> None:
    fake = FakeActions(expire_queue_once=True)
    api = client(fake)
    session = api.create_session(100, "host")
    with pytest.raises(scaleset.SessionExpiredError):
        api.get_message(session, 0, 1)
    refreshed = api.refresh_session(100, session)
    assert refreshed.queue_token == "queue-2" and api.get_message(refreshed, 0, 1) is None


def test_session_conflict_is_explained() -> None:
    with pytest.raises(scaleset.ScaleSetError, match="andere Sitzung"):
        client(FakeActions(session_conflict=True)).create_session(100, "host")


def test_jit_and_runner_removal() -> None:
    fake = FakeActions()
    api = client(fake)
    assert api.generate_jit(100, "host-cpu-1") == (555, "ZW5j")
    api.remove_runner(555)
    assert fake.removed_runners == [555]


@pytest.mark.parametrize(
    "url",
    [
        "http://broker.actions.githubusercontent.com/x",
        "https://evil.example.com/x",
        "https://githubusercontent.com.evil/x",
    ],
)
def test_tokens_only_go_to_trusted_hosts(url: str) -> None:
    with pytest.raises(scaleset.ScaleSetError):
        scaleset.check_url(url)


def test_statistics_and_token_expiry_parsing() -> None:
    stats = scaleset.Statistics.parse({"totalAssignedJobs": 2, "totalRunningJobs": 5, "totalIdleRunners": -1})
    assert stats.waiting == 0 and stats.idle == 0
    assert scaleset.token_expiry(jwt(123)) == 123.0 and scaleset.token_expiry("kaputt") == 0.0
    with pytest.raises(scaleset.ScaleSetError):
        scaleset.parse_message(b'{"messageType": "Anders"}')
