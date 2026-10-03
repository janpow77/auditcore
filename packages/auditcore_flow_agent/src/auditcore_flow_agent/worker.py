"""Anbindung des Prozesswächters an lokale oder per App-Adapter entfernte Leases."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .models import Lease, Outcome
from .process import Command, ProcessNotStopped, ProcessResult, run_command


class LeaseClient(Protocol):
    def heartbeat(self, token: str, *, progress: float | None = None) -> bool: ...
    def finish(self, token: str, outcome: Outcome) -> bool: ...
    def recover_expired(self) -> tuple[str, ...]: ...
    def confirm_stopped(self, token: str) -> bool: ...


def execute(
    client: LeaseClient,
    lease: Lease,
    command: Command,
    *,
    progress: Callable[[], float] | None = None,
    stop_grace_s: float = 1,
) -> ProcessResult:
    """Nur auf dem zugewiesenen Rechner ausführen; GPUs im App-Adapter verbindlich binden.

    Der Adapter muss Fehler bei externen Aufrufen begrenzen. CPU/GPU-Isolation
    wird nicht durch Python-Kennungen ersetzt. Docker benötigt einen eigenen
    Container-Wächter, der das tatsächliche Containerende bestätigt.
    """
    if lease.job.stall_timeout_s is not None and progress is None:
        client.finish(lease.token, Outcome("permanent", "Messbare Fortschrittsquelle fehlt."))
        raise ValueError("Eine Fortschrittsfrist benötigt eine messbare Fortschrittsquelle.")

    def tick() -> bool:
        return client.heartbeat(lease.token, progress=None if progress is None else progress())

    try:
        result = run_command(
            command,
            timeout_s=lease.job.timeout_s,
            tick=tick,
            poll_s=min(0.1, lease.job.lease_s / 3),
            stop_grace_s=stop_grace_s,
        )
    except ProcessNotStopped:
        raise  # Weder Status noch Reservierung ohne bestätigtes Prozessende freigeben.
    except Exception as error:
        if not client.finish(lease.token, Outcome("retryable", type(error).__name__)):
            client.confirm_stopped(lease.token)
        raise
    if result.reason == "exited":
        outcome = Outcome(
            "succeeded" if result.returncode == 0 else "retryable",
            "" if result.returncode == 0 else f"Prozesscode {result.returncode}",
        )
    else:
        outcome = Outcome("retryable", result.reason)
    if not client.finish(lease.token, outcome):
        client.recover_expired()
        client.confirm_stopped(lease.token)
    return result
