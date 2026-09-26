"""Gleichheit alt ↔ neu: Endlichkeitsprüfung aus ``auditcore_common`` (Meldungen unverändert)."""

from __future__ import annotations

import math
import random

import pytest

from auditcore_geo.errors import KoordinatenFehler
from auditcore_geo.koordinaten import _endlich

WERTE: list[object] = [
    0,
    -0.0,
    1,
    52.52,
    -180.0,
    1e308,
    5e-324,
    True,
    False,
    None,
    "1.0",
    b"1",
    [1.0],
    math.nan,
    math.inf,
    -math.inf,
    10**400,
]


# auditcore_geo 0.3.0, koordinaten.py :: _endlich (wörtlich)
def alt_endlich(wert: float, name: str) -> float:
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):  # noqa: UP038
        raise KoordinatenFehler(f"{name} ist keine Zahl: {wert!r}")
    zahl = float(wert)
    if not math.isfinite(zahl):
        raise KoordinatenFehler(f"{name} ist nicht endlich: {wert!r}")
    return zahl


def _ergebnis(funktion: object, wert: object) -> tuple[str, object]:
    try:
        return "ok", funktion(wert, "Breite")  # type: ignore[operator]
    except Exception as exc:  # Fehlerklasse und Meldung werden verglichen
        return type(exc).__name__, str(exc)


@pytest.mark.parametrize("wert", WERTE, ids=repr)
def test_endlich_gleich(wert: object) -> None:
    alt, neu = _ergebnis(alt_endlich, wert), _ergebnis(_endlich, wert)
    assert repr(neu) == repr(alt)


def test_endlich_zufall() -> None:
    zufall = random.Random(20260926)
    for _ in range(2000):
        wert = zufall.choice([zufall.uniform(-1e6, 1e6), zufall.randint(-(10**20), 10**20)])
        assert _endlich(wert, "Länge") == alt_endlich(wert, "Länge")
