"""Scale set listener: one long-poll session per runner class (backend ``scaleset``).

Each enabled class gets a scale set ``<praefix>-<klasse>`` (label = name, so
workflows select it with ``runs-on: <name>``). The listener long-polls the
session queue, derives the demand ``min(capacity, min + totalAssignedJobs)``
like the reference scaler, publishes it with the queue statistics in the
demand file and deletes every handled message. Capacity is the class maximum,
lowered by the pool file of the configured target source. Runners themselves
are still started by the supervisors (``auditcore-runner supervisor``); they
obtain their JIT configuration from the scale set.
"""

from __future__ import annotations

import contextlib
import signal
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from . import github, nachfrage, pool
from .profile import Profile
from .scaleset import ScaleSetClient, ScaleSetError, Session, SessionExpiredError, Statistics

Publish = Callable[[str, nachfrage.ClassDemand], None]


def desired(statistics: Statistics, minimum: int, capacity: int) -> int:
    """Runners wanted now: the minimum plus every assigned job, never above capacity."""
    return max(0, min(capacity, minimum + statistics.assigned))


def capacity(profile: Profile, runner_class: str, current: pool.Pool | None) -> int:
    settings = profile.classes[runner_class]
    if not settings.enabled:
        return 0
    limit = settings.max_instances
    if current is not None and runner_class in current.targets:
        limit = min(limit, current.targets[runner_class])
    return limit


def client_for(profile: Profile) -> ScaleSetClient:
    return ScaleSetClient(profile.target, lambda: github.resolve_token(profile.auth))


@dataclass
class ClassListener:
    """Session and message loop of one class; ``step`` handles one long-poll."""

    profile: Profile
    runner_class: str
    api: ScaleSetClient
    publish: Publish
    load_pool: Callable[[], pool.Pool | None]
    scale_set_id: int = 0
    session: Session | None = None
    last_message_id: int = 0
    statistics: Statistics = field(default_factory=Statistics)

    @property
    def name(self) -> str:
        return self.profile.scale_set_name(self.runner_class)

    def start(self) -> Session:
        group = self.api.runner_group_id(self.profile.scale_set.runner_group)
        self.scale_set_id = self.api.ensure_scale_set(self.name, group, (self.name,))
        session = self.api.create_session(self.scale_set_id, self.profile.host)
        self.session, self.last_message_id = session, 0
        self._publish(session.statistics)
        return session

    def _publish(self, statistics: Statistics) -> None:
        self.statistics = statistics
        settings = self.profile.classes[self.runner_class]
        limit = capacity(self.profile, self.runner_class, self.load_pool())
        target = desired(statistics, settings.min_instances, limit)
        self.publish(
            self.runner_class,
            nachfrage.ClassDemand(statistics.waiting, target, statistics.as_dict(), self.name),
        )

    def _refresh(self, expired: Session) -> Session:
        self.session = self.api.refresh_session(self.scale_set_id, expired)
        return self.session

    def step(self) -> None:
        session = self.session or self.start()
        limit = capacity(self.profile, self.runner_class, self.load_pool())
        try:
            message = self.api.get_message(session, self.last_message_id, limit)
        except SessionExpiredError:
            session = self._refresh(session)
            message = self.api.get_message(session, self.last_message_id, limit)
        if message is None:
            self._publish(self.statistics)
            return
        self._publish(message.statistics)
        try:
            self.api.delete_message(session, message.message_id)
        except SessionExpiredError:
            self.api.delete_message(self._refresh(session), message.message_id)
        self.last_message_id = message.message_id

    def stop(self) -> None:
        if self.session is not None:
            with contextlib.suppress(ScaleSetError):
                self.api.delete_session(self.scale_set_id, self.session)
            self.session = None


def serve_class(listener: ClassListener, stop: threading.Event, log: Callable[[str], None]) -> None:
    """Keep one class listening until ``stop``; errors restart the session after a pause."""
    pause = 15.0
    while not stop.is_set():
        try:
            listener.step()
            pause = 15.0
        except (ScaleSetError, OSError, ValueError, KeyError) as error:
            log(f"{listener.runner_class}: {error} – neuer Versuch in {int(pause)} s")
            listener.session = None
            stop.wait(pause)
            pause = min(pause * 2, 600.0)
    listener.stop()


def run_forever(profile: Profile, log: Callable[[str], None] = print) -> None:  # pragma: no cover - threads, signals
    api, lock, stop = client_for(profile), threading.Lock(), threading.Event()

    def publish(runner_class: str, demand: nachfrage.ClassDemand) -> None:
        with lock:
            nachfrage.merge(nachfrage.Demand("scaleset", time.time(), {runner_class: demand}))

    def load_pool() -> pool.Pool | None:
        return pool.load(profile.pool_path())

    listeners = [
        ClassListener(profile, name, api, publish, load_pool)
        for name, settings in sorted(profile.classes.items())
        if settings.enabled
    ]
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    threads = [threading.Thread(target=serve_class, args=(item, stop, log), daemon=True) for item in listeners]
    for thread in threads:
        thread.start()
    try:
        while any(thread.is_alive() for thread in threads):
            stop.wait(5)
    except KeyboardInterrupt:
        stop.set()
    for thread in threads:
        thread.join(timeout=90)


def jit_config(
    profile: Profile, runner_class: str, runner_name: str, api: ScaleSetClient | None = None
) -> dict[str, object]:
    """JIT configuration from the class' scale set, shaped like GitHub's ``generate-jitconfig`` answer."""
    client = api or client_for(profile)
    group = client.runner_group_id(profile.scale_set.runner_group)
    scale_set_id = client.find_scale_set(profile.scale_set_name(runner_class), group)
    if scale_set_id is None:
        raise ScaleSetError(f"Scale-Set {profile.scale_set_name(runner_class)} fehlt – läuft der Listener?")
    runner_id, encoded = client.generate_jit(scale_set_id, runner_name)
    return {"runner": {"id": runner_id, "name": runner_name}, "encoded_jit_config": encoded}
