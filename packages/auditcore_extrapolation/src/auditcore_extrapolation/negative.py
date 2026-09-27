"""Negative sampling units: separate population and reconciliation (guidance section 4.6).

Sampling units with a negative balance (mostly financial corrections) are not
sampled with the positive population; they form a separate population that is
audited to verify that the corrected amount matches the decided correction.
No error rate is computed for them, and the total error rate uses the book
value of the positive population only. The guidance describes three ways to
split the amounts of a unit (4.6, summary):

1. net amount of the unit: positive population if positive, else negative
   (acceptable, but units corrected for earlier periods are less likely to be
   selected);
2. all positive amounts to the positive, all negative amounts to the negative
   population (recommended);
3. corrections of the current sampling period are netted with its positive
   amounts; corrections of earlier periods go to the negative population
   (recommended).

The annual control report reconciles the net declared expenditure with the
positive population (4.6).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType

from .errors import ExtrapolationInputError
from .sources import Step, guidance

APPROACHES = MappingProxyType(
    {
        1: "Saldo der Einheit (zulässig, Risiko geringerer Auswahlchance korrigierter Einheiten)",
        2: "Alle positiven Beträge positiv, alle negativen negativ (empfohlen)",
        3: "Korrekturen des laufenden Zeitraums verrechnet, frühere negativ (empfohlen)",
    }
)


@dataclass(frozen=True)
class DeclaredUnit:
    """Amounts of one sampling unit in the reference period (all ≥ 0).

    ``new_expenditure``: expenditure declared; ``current_corrections``:
    corrections of expenditure of the current sampling period;
    ``previous_corrections``: corrections of earlier periods (also artificial
    negative units such as clerical errors, 4.6).
    """

    id: str
    new_expenditure: float
    current_corrections: float = 0.0
    previous_corrections: float = 0.0


@dataclass(frozen=True)
class PopulationSplit:
    """Positive and negative population with the reconciliation (guidance 4.6)."""

    approach: int
    positive: tuple[tuple[str, float], ...]
    negative: tuple[tuple[str, float], ...]
    positive_total: float
    negative_total: float
    net_declared: float
    steps: tuple[Step, ...]
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible split."""
        return {
            "approach": self.approach,
            "positive": [{"id": i, "amount": a} for i, a in self.positive],
            "negative": [{"id": i, "amount": a} for i, a in self.negative],
            "positive_total": self.positive_total,
            "negative_total": self.negative_total,
            "net_declared": self.net_declared,
            "steps": [s.to_dict() for s in self.steps],
            "notes": list(self.notes),
        }


def _check(unit: DeclaredUnit) -> None:
    if not unit.id.strip():
        raise ExtrapolationInputError("Jede Einheit braucht eine Kennung.")
    for value in (unit.new_expenditure, unit.current_corrections, unit.previous_corrections):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ExtrapolationInputError(
                f"Einheit '{unit.id}': Ausgaben und Korrekturen als Beträge ≥ 0 angeben."
            )


def _parts(unit: DeclaredUnit, approach: int) -> tuple[float, float]:
    """(positive part, negative part ≤ 0) of one unit."""
    new, current, previous = (
        unit.new_expenditure,
        unit.current_corrections,
        unit.previous_corrections,
    )
    if approach == 1:
        net = new - current - previous
        return (net, 0.0) if net > 0 else (0.0, net)
    if approach == 2:
        return new, -(current + previous)
    net_current = new - current
    return (net_current, -previous) if net_current > 0 else (0.0, net_current - previous)


def split_population(units: Sequence[DeclaredUnit], approach: int) -> PopulationSplit:
    """Separate the positive from the negative population (guidance section 4.6)."""
    if isinstance(approach, bool) or approach not in APPROACHES:
        raise ExtrapolationInputError("Aufteilung nach Leitfaden 4.6: Variante 1, 2 oder 3.")
    for unit in units:
        _check(unit)
    ids = [u.id for u in units]
    if not ids or len(set(ids)) != len(ids):
        raise ExtrapolationInputError("Mindestens eine Einheit, Kennungen eindeutig.")
    parts = [(u.id, *_parts(u, approach)) for u in units]
    positive = tuple((i, p) for i, p, _ in parts if p > 0)
    negative = tuple((i, n) for i, _, n in parts if n < 0)
    positive_total = math.fsum(p for _, p in positive)
    negative_total = math.fsum(n for _, n in negative)
    net = math.fsum(
        u.new_expenditure - u.current_corrections - u.previous_corrections for u in units
    )
    source = guidance("4.6")
    steps = (
        Step(
            "Positive Grundgesamtheit (Buchwert für Stichprobe und TER)",
            "Σ positive Beträge",
            positive_total,
            source,
        ),
        Step(
            "Negative Grundgesamtheit (gesondert prüfen)",
            "Σ negative Beträge",
            negative_total,
            source,
        ),
        Step("Geltend gemachte Ausgaben (netto)", "positiv + negativ", net, source),
    )
    notes = [
        "Keine Fehlerquote für die negative Grundgesamtheit; Auswahl dort möglichst "
        "zufällig (Leitfaden 4.6)."
    ]
    if approach == 1:
        notes.append(
            "Variante 1: Einheiten mit Korrekturen früherer Zeiträume haben eine geringere "
            "Auswahlchance; "
            "die Kommission empfiehlt Variante 2 oder 3 (Leitfaden 4.6)."
        )
    return PopulationSplit(
        approach, positive, negative, positive_total, negative_total, net, steps, tuple(notes)
    )


@dataclass(frozen=True)
class NegativeCheck:
    """Audit of one negative unit: correction carried out versus decided (4.6)."""

    id: str
    corrected_amount: float
    decided_amount: float


@dataclass(frozen=True)
class NegativeReview:
    """Shortfalls of corrections; ``disclose`` means report in the annual control report."""

    shortfalls: tuple[tuple[str, float], ...]
    total_shortfall: float
    disclose: bool

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible review."""
        return {
            "shortfalls": [{"id": i, "amount": a} for i, a in self.shortfalls],
            "total_shortfall": self.total_shortfall,
            "disclose": self.disclose,
        }


def review_negative_units(checks: Sequence[NegativeCheck]) -> NegativeReview:
    """Corrections below the decided amount are disclosed in the ACR (guidance section 4.6)."""
    shortfalls = []
    for check in checks:
        for value in (check.corrected_amount, check.decided_amount):
            if not math.isfinite(value) or value < 0:
                raise ExtrapolationInputError(f"Einheit '{check.id}': Beträge ≥ 0 angeben.")
        gap = check.decided_amount - check.corrected_amount
        if gap > 1e-9:
            shortfalls.append((check.id, gap))
    total = math.fsum(g for _, g in shortfalls)
    return NegativeReview(tuple(shortfalls), total, bool(shortfalls))
