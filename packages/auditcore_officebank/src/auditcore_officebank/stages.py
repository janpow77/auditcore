"""Etappenplan der officebank: welche CLI-Gruppe in welcher Etappe kommt.

Die Zuordnung folgt dem Plan ``docs/projekt/20261005_Plan_auditcore_officebank_0.1.md``
(Kap. 7.1). Etappe 0 liefert nur Gerüst, Konfiguration und Ausgabe-Maskierung.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import StageNotImplemented


@dataclass(frozen=True)
class Stage:
    """Eine Etappe mit Nummer, Titel und den CLI-Gruppen, die sie liefert."""

    number: int
    title: str
    groups: tuple[str, ...]


STAGES: tuple[Stage, ...] = (
    Stage(0, "Gerüst", ("konfig", "status")),
    Stage(1, "Gates", ("gate",)),
    Stage(2, "VM", ("vm",)),
    Stage(3, "Office", ("excel", "access", "word")),
    Stage(4, "Build, Abnahme, Lieferung", ("build", "abnahme", "liefern")),
    Stage(5, "SQL-Server-Dienst", ("mssql",)),
    Stage(6, "Runner, Plugin, CI-Vorlage", ("projekt", "runner-profil")),
)

#: Etappe, die in dieser Fassung umgesetzt ist.
IMPLEMENTED_STAGE = 0


def stage_of(group: str) -> Stage:
    """Etappe einer CLI-Gruppe; ``KeyError`` bei unbekannter Gruppe."""
    for stage in STAGES:
        if group in stage.groups:
            return stage
    raise KeyError(group)


def planned_groups() -> tuple[str, ...]:
    """CLI-Gruppen, die geplant, aber noch nicht umgesetzt sind."""
    return tuple(
        group for stage in STAGES if stage.number > IMPLEMENTED_STAGE for group in stage.groups
    )


def require(group: str) -> None:
    """Bricht mit :class:`StageNotImplemented` ab, wenn die Gruppe noch fehlt."""
    stage = stage_of(group)
    if stage.number > IMPLEMENTED_STAGE:
        raise StageNotImplemented(group, stage.number)
