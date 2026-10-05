"""Fehlerklassen der officebank; Meldungen sind deutsch und enthalten keine Secrets."""

from __future__ import annotations


class OfficebankError(Exception):
    """Basisklasse aller erwarteten Fehler der officebank."""


class ConfigError(OfficebankError):
    """Rechnerprofil oder Projektdatei ist unlesbar, unvollständig oder ungültig."""


class StageNotImplemented(OfficebankError):
    """Der Baustein ist geplant, gehört aber zu einer späteren Etappe."""

    def __init__(self, group: str, stage: int) -> None:
        super().__init__(f"„{group}“ ist für Etappe {stage} geplant und noch nicht umgesetzt.")
        self.group = group
        self.stage = stage
