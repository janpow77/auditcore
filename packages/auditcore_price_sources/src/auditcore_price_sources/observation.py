"""Normalized record shapes with explicit unit, time reference and value status.

Every price or market record states *what* the number is (series and unit),
*when* it applies (time reference and its kind) and *whether* a value exists.
A missing source value is ``None`` with status ``fehlwert``; it is never 0.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation

from auditcore_harvest import JSON

OBSERVATION_SCHEMA = "auditcore_price_sources.observation/1"
STATION_SCHEMA = "auditcore_price_sources.station/1"
SNAPSHOT_SCHEMA = "auditcore_price_sources.snapshot/1"

#: kinds of time reference; ``abrufzeitpunkt`` is only the retrieval time, not a price change time
TIME_KINDS = ("tag", "handelstag", "monat", "jahr", "abrufzeitpunkt", "datenstand", "unbekannt")
#: time reference of current-state sources: the retrieval time in ``provenance.retrieved_at``
#: (kept out of the normalized payload so that an unchanged state is not a new record)
RETRIEVAL_TIME = {"art": "abrufzeitpunkt", "wert": None, "quelle": "provenance.retrieved_at"}
PRESENT = "vorhanden"
MISSING = "fehlwert"


def exact(value: object) -> Decimal | None:
    """Exact decimal from a JSON number or plain text; ``None``/``""``/``False`` → ``None``.

    Raises ``ValueError`` for text that is not a number, so callers can report it.
    """
    if value is None or value is False or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("Wahrheitswert ist kein Zahlenwert")
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(repr(value))
    if isinstance(value, str):
        try:
            result = Decimal(value.strip())
        except InvalidOperation as exc:
            raise ValueError(f"kein Zahlenwert: {value[:40]!r}") from exc
        if not result.is_finite():
            raise ValueError("Zahlenwert nicht endlich")
        return result
    raise ValueError(f"unerwarteter Typ {type(value).__name__}")


def unit(
    text: str | None,
    *,
    source_text: str | None = None,
    origin: str,
    numerator: str | None = None,
    denominator: str | None = None,
    multiplier: int | None = None,
) -> dict[str, JSON]:
    """Unit block; ``origin`` says whether the source or the profile stated it."""
    return {
        "text": text,
        "quelle_text": source_text,
        "herkunft": origin,
        "zaehler": numerator,
        "nenner": denominator,
        "multiplikator": multiplier,
    }


def observation(
    *,
    series: str,
    time_kind: str,
    period: str | None,
    value: Decimal | None,
    unit_block: Mapping[str, JSON],
    source_status: str | None = None,
    extra: Mapping[str, JSON] | None = None,
) -> dict[str, JSON]:
    """One observation of a time series in the common shape."""
    if time_kind not in TIME_KINDS:
        raise ValueError(f"Unbekannte Zeitbezugsart {time_kind}")
    return {
        "schema": OBSERVATION_SCHEMA,
        "reihe": series,
        "zeitbezug": {"art": time_kind, "wert": period},
        "wert": None if value is None else str(value),
        "status": PRESENT if value is not None else MISSING,
        "status_quelle": source_status,
        "einheit": dict(unit_block),
        **dict(extra or {}),
    }
