from __future__ import annotations

import threading
from dataclasses import replace
from pathlib import Path

from fake_scaleset import FakeActions, message

from auditcore_runner import nachfrage, pool, scaleset, scaleset_listener
from auditcore_runner.hardware import HostFacts
from auditcore_runner.profile import Profile
from auditcore_runner.propose import propose


def profile(facts: HostFacts) -> Profile:
    base = propose(facts, "owner/repo")
    name = next(iter(base.classes))
    classes = {name: replace(base.classes[name], min_instances=1, max_instances=4, enabled=True)}
    return replace(base, host="build-01", backend="scaleset", classes=classes)


def listener(
    prof: Profile, fake: FakeActions, published: dict[str, nachfrage.ClassDemand], targets: dict[str, int] | None = None
) -> scaleset_listener.ClassListener:
    api = scaleset.ScaleSetClient(prof.target, lambda: "gh-token", fake, clock=lambda: 1_000_000_000.0)
    current = pool.Pool(targets) if targets is not None else None
    return scaleset_listener.ClassListener(prof, next(iter(prof.classes)), api, published.__setitem__, lambda: current)


def test_desired_follows_the_reference_scaler() -> None:
    stats = scaleset.Statistics(assigned=5)
    assert scaleset_listener.desired(stats, 1, 4) == 4
    assert scaleset_listener.desired(scaleset.Statistics(), 1, 4) == 1
    assert scaleset_listener.desired(stats, 0, 0) == 0


def test_listener_publishes_demand_and_deletes_messages(workstation_facts: HostFacts) -> None:
    prof = profile(workstation_facts)
    name = next(iter(prof.classes))
    fake = FakeActions(messages=[message(9, assigned=2, running=1)])
    published: dict[str, nachfrage.ClassDemand] = {}
    item = listener(prof, fake, published)
    session = item.start()
    assert fake.scale_sets == {f"build-01-{name}": 100} and session.statistics.assigned == 1
    assert published[name].target == 2 and published[name].scale_set == f"build-01-{name}"
    item.step()
    assert published[name].target == 3 and published[name].waiting == 1
    assert fake.deleted_messages == [9] and item.last_message_id == 9
    item.step()  # 202: nothing new, the old numbers are published again (freshness)
    assert published[name].target == 3
    item.stop()
    assert fake.deleted_sessions == 1


def test_pool_and_disabled_class_cap_the_demand(workstation_facts: HostFacts) -> None:
    prof = profile(workstation_facts)
    name = next(iter(prof.classes))
    published: dict[str, nachfrage.ClassDemand] = {}
    capped = listener(prof, FakeActions(messages=[message(1, assigned=9)]), published, {name: 2})
    capped.step()
    capped.step()
    assert published[name].target == 2
    off = replace(prof, classes={name: replace(prof.classes[name], enabled=False)})
    assert scaleset_listener.capacity(off, name, None) == 0


def test_expired_queue_token_is_refreshed(workstation_facts: HostFacts) -> None:
    prof = profile(workstation_facts)
    fake = FakeActions(messages=[message(4, assigned=1)])
    item = listener(prof, fake, {})
    item.step()
    fake.expire_queue_once = True
    item.step()
    assert item.session is not None and item.session.queue_token == "queue-2"
    assert fake.deleted_messages == [4]


def test_serve_class_restarts_after_errors(workstation_facts: HostFacts) -> None:
    prof = profile(workstation_facts)
    stop, logged = threading.Event(), []
    item = listener(prof, FakeActions(session_conflict=True), {})

    def log(text: str) -> None:
        logged.append(text)
        stop.set()

    scaleset_listener.serve_class(item, stop, log)
    assert "andere Sitzung" in logged[0] and item.session is None


def test_jit_config_uses_the_scale_set(workstation_facts: HostFacts) -> None:
    prof = profile(workstation_facts)
    name = next(iter(prof.classes))
    fake = FakeActions(scale_sets={f"build-01-{name}": 100})
    api = scaleset.ScaleSetClient(prof.target, lambda: "gh-token", fake, clock=lambda: 1_000_000_000.0)
    config = scaleset_listener.jit_config(prof, name, "build-01-x-1", api)
    assert config == {"runner": {"id": 555, "name": "build-01-x-1"}, "encoded_jit_config": "ZW5j"}


def test_demand_file_round_trip_and_merge(tmp_path: Path) -> None:
    path = tmp_path / "nachfrage.json"
    nachfrage.merge(nachfrage.Demand("scaleset", 100.0, {"cpu": nachfrage.ClassDemand(1, 2, {"zugewiesen": 3})}), path)
    nachfrage.merge(nachfrage.Demand("scaleset", 200.0, {"gpu": nachfrage.ClassDemand(0, 0)}), path)
    loaded = nachfrage.load(path)
    assert loaded is not None and set(loaded.classes) == {"cpu", "gpu"}
    assert loaded.classes["cpu"].statistics == {"zugewiesen": 3} and loaded.written == 200.0
    assert loaded.fresh(now=400.0) and not loaded.fresh(now=600.0)
    assert nachfrage.parse({"schema": "anders"}) is None
