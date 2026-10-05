"""Windows-Gast steuern: Gastagent, Benutzersitzung, Austauschserver, Sperre, Fotos.

Etappe 0 enthält nur die Schnittstelle :mod:`auditcore_officebank.vm.backend`.
UTM-Backend, Austauschserver mit Token, Benutzersitzung, Sperre, Scancodes und
Einrichtung folgen in Etappe 2 (Plan, Kap. 2.1).
"""

from __future__ import annotations

from .backend import GuestBackend, GuestResult, VmState

__all__ = ["GuestBackend", "GuestResult", "VmState"]
