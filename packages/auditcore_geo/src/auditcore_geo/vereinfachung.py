"""Linien- und Ringvereinfachung nach Douglas-Peucker.

Ergebnisgleich mit ``osint`` ``werkzeuge/bundeslaender_holen.py``
(``douglas_peucker``, ``ring_vereinfachen``), aber ohne Rekursion (keine
Rekursionsgrenze bei langen Linien) und mit geprüften Eingaben. Die Toleranz
hat die Einheit der Koordinaten (im Original Grad nach der Projektion).
Der Abstand wird zur **Geraden** durch die Endpunkte gemessen, nicht zur
Strecke – so rechnet das Original.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from .errors import GeometrieFehler

Punktfolge = Sequence[tuple[float, float]]


def _pruefen(punkte: Punktfolge, toleranz: float) -> None:
    if isinstance(toleranz, bool) or not math.isfinite(toleranz) or toleranz < 0:
        raise GeometrieFehler(f"Toleranz muss endlich und nicht negativ sein: {toleranz!r}")
    for x, y in punkte:
        if not (math.isfinite(x) and math.isfinite(y)):
            raise GeometrieFehler(f"Punkt ({x!r}, {y!r}) ist nicht endlich.")


def _behalten(punkte: Punktfolge, toleranz: float) -> list[int]:
    behalten = {0, len(punkte) - 1}
    offen = [(0, len(punkte) - 1)]
    while offen:
        anfang, ende = offen.pop()
        if ende - anfang < 2:
            continue
        (x1, y1), (x2, y2) = punkte[anfang], punkte[ende]
        dx, dy = x2 - x1, y2 - y1
        laenge = math.hypot(dx, dy)
        bester, abstand = anfang, -1.0
        for i in range(anfang + 1, ende):
            x, y = punkte[i]
            if laenge:
                d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / laenge
            else:
                d = math.hypot(x - x1, y - y1)
            if d > abstand:
                bester, abstand = i, d
        if abstand > toleranz:
            behalten.add(bester)
            offen.append((anfang, bester))
            offen.append((bester, ende))
    return sorted(behalten)


def douglas_peucker(punkte: Punktfolge, toleranz: float) -> list[tuple[float, float]]:
    """Vereinfachte Punktfolge; Anfangs- und Endpunkt bleiben stets erhalten."""
    _pruefen(punkte, toleranz)
    return _douglas_peucker(punkte, toleranz)


def _douglas_peucker(punkte: Punktfolge, toleranz: float) -> list[tuple[float, float]]:
    if len(punkte) < 3:
        return [(float(x), float(y)) for x, y in punkte]
    return [punkte[i] for i in _behalten(punkte, toleranz)]


def ring_vereinfachen(
    ring: Punktfolge, toleranz: float, *, stellen: int | None
) -> list[list[float]] | None:
    """Geschlossenen Ring vereinfachen; ``None``, wenn weniger als vier Punkte bleiben.

    Wie im Original wird der Ring am vom ersten Punkt entferntesten Punkt
    geteilt, beide Hälften vereinfacht und wieder geschlossen. ``stellen``
    rundet die Ergebnisse (Original: 4); die Rundung erfolgt nach der
    Punktzahlprüfung, sie kann aufeinanderfolgende gleiche Punkte erzeugen.
    """
    _pruefen(ring, toleranz)
    return _ring_vereinfachen(ring, toleranz, stellen)


def _ring_vereinfachen(
    ring: Punktfolge, toleranz: float, stellen: int | None
) -> list[list[float]] | None:
    if len(ring) < 4:
        return None
    punkte = list(ring)
    offen = punkte[:-1] if punkte[0] == punkte[-1] else punkte
    x0, y0 = offen[0]
    fern = max(range(len(offen)), key=lambda i: math.hypot(offen[i][0] - x0, offen[i][1] - y0))
    a = _douglas_peucker(offen[: fern + 1], toleranz)
    b = _douglas_peucker([*offen[fern:], offen[0]], toleranz)
    neu = a[:-1] + b
    if len(neu) < 4:
        return None
    if stellen is None:
        return [[x, y] for x, y in neu]
    return [[round(x, stellen), round(y, stellen)] for x, y in neu]
