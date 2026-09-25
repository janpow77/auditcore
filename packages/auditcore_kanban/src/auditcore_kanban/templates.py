"""Board templates: the seven WorkspaceSidebar templates of audit_designer and the
cockpit job board (status aliases, restricted transitions, locked column)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .errors import JsonObject
from .model import DEFAULT_COLUMNS, Column, TransitionPolicy


@dataclass(frozen=True)
class BoardTemplate:
    key: str
    name: str
    icon: str
    description: str
    columns: tuple[Column, ...]
    transitions: TransitionPolicy = TransitionPolicy()

    def to_json(self) -> JsonObject:
        return {
            "key": self.key,
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "columns": [
                {"id": c.id, "label": c.label, "color": c.color, "wip_limit": c.wip_limit,
                 "done": c.done, "status_aliases": list(c.status_aliases)}
                for c in self.columns
            ],
        }


def _cols(rows: Sequence[tuple[str, str, str]]) -> tuple[Column, ...]:
    return tuple(Column(column_id, label, color) for column_id, label, color in rows)


GRAY, BLUE, VIOLET = "#6b7280", "#3b82f6", "#8b5cf6"
AMBER, RED, GREEN = "#f59e0b", "#ef4444", "#10b981"

TEMPLATES: tuple[BoardTemplate, ...] = (
    BoardTemplate("standard", "Standard", "📋", "Offen, In Arbeit, Erledigt", DEFAULT_COLUMNS),
    BoardTemplate(
        "vorhabenpruefung", "Vorhabenprüfung", "🔍",
        "Auswahl, Prüfung, Entwurf, Kontradiktorisch, Abschluss, Follow-Up",
        _cols([("auswahl", "Auswahl", GRAY), ("pruefung", "Prüfung", BLUE),
               ("entwurf", "Entwurf", AMBER), ("kontradiktorisch", "Kontradiktorisch", RED),
               ("abschluss", "Abschluss", VIOLET), ("followup", "Follow-Up", GREEN)]),
    ),
    BoardTemplate(
        "sprint", "Sprint", "🏃", "Backlog, Sprint, In Arbeit, Review, Done",
        _cols([("backlog", "Backlog", GRAY), ("sprint", "Sprint", BLUE),
               ("in_arbeit", "In Arbeit", AMBER), ("review", "Review", VIOLET),
               ("done", "Done", GREEN)]),
    ),
    BoardTemplate(
        "einfach", "Einfach", "✅", "To-Do, Erledigt",
        _cols([("todo", "To-Do", BLUE), ("erledigt", "Erledigt", GREEN)]),
    ),
    BoardTemplate(
        "systempruefung", "Systemprüfung", "🏛️",
        "Auswahl, Erhebung, Prüfung, Entwurf, Kontradiktorisch, Abschluss",
        _cols([("auswahl", "Auswahl", GRAY), ("erhebung", "Erhebung", BLUE),
               ("pruefung", "Prüfung", "#7c3aed"), ("entwurf", "Entwurf", AMBER),
               ("kontradiktorisch", "Kontradiktorisch", RED), ("abschluss", "Abschluss", GREEN)]),
    ),
    BoardTemplate(
        "teamplanung", "Teamplanung", "👥", "Ideen, Geplant, In Arbeit, Erledigt",
        _cols([("ideen", "Ideen", "#ec4899"), ("geplant", "Geplant", BLUE),
               ("in_arbeit", "In Arbeit", AMBER), ("erledigt", "Erledigt", GREEN)]),
    ),
    BoardTemplate(
        "jahresplanung", "Jahresplanung", "📅", "Q1, Q2, Q3, Q4, Abgeschlossen",
        _cols([("q1", "Q1", BLUE), ("q2", "Q2", VIOLET), ("q3", "Q3", AMBER),
               ("q4", "Q4", RED), ("abgeschlossen", "Abgeschlossen", GREEN)]),
    ),
    BoardTemplate(
        "cockpit-auftraege", "Aufträge (cockpit)", "🤖",
        "Eingang, Geplant, Läuft, Rückfrage / Freigabe, Fertig",
        (
            Column("eingang", "Eingang", GRAY),
            Column("geplant", "Geplant", BLUE),
            Column("laeuft", "Läuft", AMBER),
            Column("rueckfrage", "Rückfrage / Freigabe", RED,
                   status_aliases=("freigabe", "unterbrochen")),
            Column("fertig", "Fertig", GREEN, done=True,
                   status_aliases=("fehler", "abgebrochen")),
        ),
        TransitionPolicy(
            allowed=frozenset({("eingang", "geplant"), ("geplant", "eingang")}),
            locked_columns=frozenset({"laeuft"}),
        ),
    ),
)


def template(key: str) -> BoardTemplate | None:
    return next((t for t in TEMPLATES if t.key == key), None)
