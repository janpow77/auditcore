"""Geprüfter Zugriff auf eingelesene JSON-Daten (ohne ``Any``).

Fehler werden als :class:`ValueError` gemeldet; die aufrufenden Lader
übersetzen sie in ihre fachliche Fehlerklasse.
"""

from __future__ import annotations

from collections.abc import Mapping

JsonObject = dict[str, object]


def mapping(value: object, what: str = "Objekt") -> Mapping[str, object]:
    """``value`` als Objekt mit Textschlüsseln."""
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{what}: Objekt erwartet.")
    return value


def optional_mapping(value: object, what: str = "Objekt") -> Mapping[str, object]:
    """Wie :func:`mapping`, ``None`` ergibt ein leeres Objekt."""
    return {} if value is None else mapping(value, what)


def items(value: object, what: str = "Liste") -> list[Mapping[str, object]]:
    """Liste von Objekten; ``None`` ergibt eine leere Liste."""
    if value is None:
        return []
    if not isinstance(value, list | tuple):
        raise ValueError(f"{what}: Liste erwartet.")
    return [mapping(entry, what) for entry in value]


def strings(value: object, what: str = "Liste") -> tuple[str, ...]:
    """Liste von Texten; ``None`` ergibt ein leeres Tupel."""
    if value is None:
        return ()
    if not isinstance(value, list | tuple):
        raise ValueError(f"{what}: Liste erwartet.")
    return tuple(str(entry) for entry in value)


def text(value: object, what: str = "Wert") -> str:
    """Pflichttext."""
    if value is None:
        raise ValueError(f"{what} fehlt.")
    return str(value)


def optional_text(value: object) -> str | None:
    """Text oder ``None``."""
    return None if value is None else str(value)


def integer(value: object, what: str = "Zahl", default: int | None = None) -> int:
    """Ganze Zahl (auch aus Text)."""
    if value is None and default is not None:
        return default
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise ValueError(f"{what}: ganze Zahl erwartet.")
    return int(value)


def optional_integer(value: object) -> int | None:
    """Ganze Zahl oder ``None``."""
    return None if value is None else integer(value)
