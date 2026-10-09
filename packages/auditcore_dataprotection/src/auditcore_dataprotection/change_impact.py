"""Consequences of a change: which checks must be done again (GUI-14, LIB-17, T-24).

A new recipient or purpose reopens the legal, register, transfer and risk
checks it touches; settled checklist items become "erneut zu prüfen". Purely
editorial fields (comments, wizard navigation) do not invalidate anything.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from .checklist import items_from_data, reopen

#: Register field → checklist items that depend on it.
FIELD_ITEMS: Mapping[str, tuple[str, ...]] = {
    "zweck": ("CHK-03", "CHK-04", "CHK-05", "CHK-20", "CHK-29"),
    "weitere_zwecke": ("CHK-04", "CHK-29"),
    "rechtsregime": ("CHK-03", "CHK-05", "CHK-10", "CHK-24"),
    "ermaechtigungsgrundlage": ("CHK-03",),
    "verantwortliche_stelle": ("CHK-02",),
    "rolle": ("CHK-02", "CHK-05", "CHK-08"),
    "kategorien_betroffene": ("CHK-06", "CHK-20"),
    "kategorien_daten": ("CHK-06", "CHK-20", "CHK-12"),
    "besondere_kategorien": ("CHK-06", "CHK-20"),
    "kategorien_empfaenger": ("CHK-06", "CHK-07", "CHK-08", "CHK-20"),
    "name_empfaenger": ("CHK-03", "CHK-06", "CHK-07", "CHK-08", "CHK-20"),
    "uebermittlungen": ("CHK-03", "CHK-05", "CHK-07", "CHK-08", "CHK-20"),
    "drittlandtransfer": ("CHK-08", "CHK-20"),
    "name_empfaenger_drittland": ("CHK-08",),
    "auftragsverarbeiter": ("CHK-08",),
    "speicherdauer": ("CHK-12", "CHK-13"),
    "tom": ("CHK-15", "CHK-22"),
    "profiling": ("CHK-05", "CHK-20", "CHK-24"),
    "ki_einsatz": ("CHK-19", "CHK-20"),
    "testdaten": ("CHK-17",),
    "dienste": ("CHK-07", "CHK-08", "CHK-19"),
    "umgebung": ("CHK-01", "CHK-17"),
}


def changed_fields(before: Mapping[str, object], after: Mapping[str, object]) -> tuple[str, ...]:
    """Relevant fields whose value differs; ``None``, ``""`` and missing are equal."""

    def norm(value: object) -> object:
        return None if value in ("", [], None) else value

    return tuple(f for f in FIELD_ITEMS if norm(before.get(f)) != norm(after.get(f)))


def affected_items(fields: tuple[str, ...]) -> tuple[str, ...]:
    """Checklist items touched by the changed fields, in catalogue order."""
    return tuple(sorted({item for f in fields for item in FIELD_ITEMS[f]}))


def apply_change_impact(
    before: Mapping[str, object], after: Mapping[str, object], at: datetime
) -> dict[str, object]:
    """Activity data with dependent checklist items reopened."""
    fields = changed_fields(before, after)
    result = dict(after)
    if not fields:
        return result
    items = items_from_data(after.get("pruefpunkte"))
    reason = f"Geändert: {', '.join(fields)}"
    reopened = reopen(items, affected_items(fields), reason, at)
    result["pruefpunkte"] = {k: v.to_dict() for k, v in reopened.items()}
    return result
