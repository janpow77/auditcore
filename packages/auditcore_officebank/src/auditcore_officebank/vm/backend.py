"""Schmale Schnittstelle zum Windows-Gast; UTM-Backend folgt in Etappe 2.

Jeder Seiteneffekt (Gastagent, Tastatur, Statusabfrage) läuft über
:class:`GuestBackend`, damit Tests mit :class:`auditcore_officebank.testing.FakeGuest`
ohne VM auskommen.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class VmState(Enum):
    """Zustand der VM aus Sicht des Hosts."""

    STOPPED = "gestoppt"
    STARTING = "startet"
    RUNNING = "laeuft"
    PAUSED = "pausiert"
    UNKNOWN = "unbekannt"


@dataclass(frozen=True)
class GuestResult:
    """Ergebnis eines Gastbefehls; ``exit_code`` ist ``None`` bei Zeitüberschreitung."""

    exit_code: int | None
    output: str
    duration_s: float
    job_id: str


class GuestBackend(Protocol):
    """Steuerung eines Gastes (UTM, später libvirt); Implementierungen ab Etappe 2."""

    def exec_system(self, script: str, timeout_s: int) -> GuestResult:
        """Führt ein PowerShell-Skript als SYSTEM über den Gastagenten aus."""

    def type_scancodes(self, codes: Sequence[int]) -> None:
        """Tippt PC-AT-Scancodes in die angemeldete Sitzung."""

    def status(self) -> VmState:
        """Liefert den aktuellen Zustand der VM."""
