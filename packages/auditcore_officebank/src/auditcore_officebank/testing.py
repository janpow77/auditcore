"""Fakes für Tests ohne VM und ohne Office.

:class:`FakeGuest` erfüllt :class:`~auditcore_officebank.vm.backend.GuestBackend`,
zeichnet alle Aufrufe auf und liefert vorher hinterlegte Ergebnisse der Reihe nach.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from .vm.backend import GuestResult, VmState


@dataclass
class FakeGuest:
    """Aufzeichnender Gast; ohne hinterlegtes Ergebnis endet ein Befehl mit Exit 0."""

    state: VmState = VmState.RUNNING
    results: deque[GuestResult] = field(default_factory=deque)
    scripts: list[str] = field(default_factory=list)
    typed: list[int] = field(default_factory=list)

    @classmethod
    def with_results(cls, results: Iterable[GuestResult]) -> FakeGuest:
        """Erzeugt einen Fake, der ``results`` nacheinander zurückgibt."""
        return cls(results=deque(results))

    def exec_system(self, script: str, timeout_s: int) -> GuestResult:
        """Zeichnet das Skript auf und gibt das nächste hinterlegte Ergebnis zurück."""
        self.scripts.append(script)
        if self.results:
            return self.results.popleft()
        return GuestResult(0, "", 0.0, f"fake-{len(self.scripts)}")

    def type_scancodes(self, codes: Sequence[int]) -> None:
        """Zeichnet die Scancodes auf."""
        self.typed.extend(codes)

    def status(self) -> VmState:
        """Gibt den eingestellten Zustand zurück."""
        return self.state
