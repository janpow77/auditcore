"""Abnahme gegen unabhängige Sollwerte (Etappe 4, Plan Kap. 2.7).

Die Sollwerte entstehen im Projekt-Repo unabhängig von Office; die officebank
liefert nur Schema, Vergleich, Toleranzen und Bericht.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tolerances:
    """Vergleichstoleranzen je Art der Kennzahl (Standardwerte laut Plan)."""

    count: float = 0.0
    amount: float = 0.005
    ratio: float = 5e-7
    rel_stat: float = 1e-6
    days: float = 0.5


__all__ = ["Tolerances"]
