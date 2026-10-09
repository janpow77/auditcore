"""Checks of table answers in the register (catalogue 2026.10.3).

Retention periods are recorded per data category (``speicherdauer`` as a list
of rows). A row without a period needs a justification and the body that
clarifies it; it then stays an open, non-blocking task (§ 65 Abs. 1 Nr. 8
HDSIG, Art. 30 Abs. 1 Satz 2 lit. f DSGVO: "wenn möglich").

Service providers are recorded as facts by IT operations and classified
legally in a second table. A processor without a contract under Art. 28
Abs. 3 DSGVO (§ 57 HDSIG) is reported as an open, non-blocking finding.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

Report = Callable[..., None]

PROCESSOR = "Auftragsverarbeiter"
CONTRACT_OPEN = ("fehlt", "in Vorbereitung")


def _text(row: Mapping[str, object], key: str) -> str:
    value = row.get(key)
    return value.strip() if isinstance(value, str) else ""


def _rows(activity: Mapping[str, object], field: str) -> list[Mapping[str, object]]:
    raw = activity.get(field)
    return [r for r in raw if isinstance(r, Mapping)] if isinstance(raw, list) else []


def check_retention_rows(activity: Mapping[str, object], issue: Report) -> None:
    """Per category: a period, or a justification with the clarifying body."""
    for index, row in enumerate(_rows(activity, "speicherdauer"), start=1):
        category = _text(row, "kategorie") or f"Zeile {index}"
        if _text(row, "frist"):
            continue
        if _text(row, "begruendung") and _text(row, "pruefstelle"):
            issue(
                "open_justified",
                f"speicherdauer[{index}]",
                f"Frist für „{category}“ noch offen (begründet)",
                False,
            )
        else:
            issue(
                "missing_field",
                f"speicherdauer[{index}]",
                f"Frist für „{category}“ fehlt; ohne Frist sind Begründung und Prüfstelle "
                "zu nennen",
            )


def check_service_providers(activity: Mapping[str, object], issue: Report) -> None:
    """Processors without a concluded contract are an open finding."""
    for index, row in enumerate(_rows(activity, "dienstleister_einordnung"), start=1):
        if _text(row, "einordnung") != PROCESSOR:
            continue
        if _text(row, "vertrag") in CONTRACT_OPEN:
            name = _text(row, "dienstleister") or f"Zeile {index}"
            issue(
                "missing_contract",
                f"dienstleister_einordnung[{index}]",
                f"Für den Auftragsverarbeiter „{name}“ liegt kein Vertrag vor "
                f"({_text(row, 'vertrag')})",
                False,
            )


#: Fields recorded as tables; ``speicherdauer`` may also be free text (older entries).
TABLE_FIELDS = ("dienstleister", "dienstleister_einordnung")
TEXT_OR_TABLE = ("speicherdauer",)


def _is_table(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(r, Mapping) for r in value)


def table_type_errors(activity: Mapping[str, object]) -> list[str]:
    """Type errors of table fields; the caller raises ``ValidationError``."""
    errors = [
        f"Feld '{name}' muss eine Tabelle (Liste von Zeilen) sein."
        for name in TABLE_FIELDS
        if activity.get(name) is not None and not _is_table(activity.get(name))
    ]
    errors.extend(
        f"Feld '{name}' muss Text oder eine Tabelle (Liste von Zeilen) sein."
        for name in TEXT_OR_TABLE
        if activity.get(name) is not None
        and not isinstance(activity.get(name), str)
        and not _is_table(activity.get(name))
    )
    return errors
