"""Residual error rate (RER) after financial corrections – Annex 3 template.

The RER is kept strictly apart from the total error rate (TER): Art. 2 Nr. 36
of Regulation (EU) 2021/1060 defines it as total errors less the financial
corrections applied by the Member State to reduce the risks identified by the
audit authority, divided by the expenditure to be declared in the accounts.
The rows A–M follow the calculation template CPRE_23-0013-01 Annex 3:

    F = A − E1 − E2        G = D × F           I = F − H
    J = G − H              K = J / I
    L = (J − 0.02 × I) / 0.98 and M = (J − L) / (I − L), only if ROUND(K, 4) > 2 %

Computed with :class:`decimal.Decimal` (rounding half up, as Excel ROUND).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, localcontext

from .errors import ExtrapolationInputError
from .evaluation import TotalErrorRate
from .sources import RER_TEMPLATE_ID, cpr

Number = Decimal | int | float
THRESHOLD_QUANTUM = Decimal("0.0001")
DEFAULT_MATERIALITY = Decimal("0.02")
NOT_APPLICABLE = "NA RTER not exceeding 2%"


def to_decimal(value: object, name: str) -> Decimal:
    """Exact Decimal of a finite number (floats via their shortest repr)."""
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, float)):
        raise ExtrapolationInputError(f"'{name}' muss eine Zahl sein.")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ExtrapolationInputError(f"'{name}' muss endlich sein.")
        return Decimal(repr(value))
    if isinstance(value, Decimal) and not value.is_finite():
        raise ExtrapolationInputError(f"'{name}' muss endlich sein.")
    return Decimal(value)


@dataclass(frozen=True)
class ResidualInputs:
    """Rows A–H of the template (B and C are informational only)."""

    audit_population: Number
    total_error_rate: Number
    ongoing_assessment: Number = 0
    other_negative_amounts: Number = 0
    financial_corrections: Number = 0
    expenditure_audited: Number | None = None
    sample_errors: Number | None = None


@dataclass(frozen=True)
class ResidualErrorRate:
    """Rows F–M of the template; ``rate`` is K (None if I = 0)."""

    audit_population: Decimal
    total_error_rate: Decimal
    ongoing_assessment: Decimal
    other_negative_amounts: Decimal
    financial_corrections: Decimal
    population: Decimal
    amount_at_risk: Decimal
    certifiable: Decimal
    residual_amount: Decimal
    rate: Decimal | None
    rate_rounded: Decimal | None
    exceeds_materiality: bool
    extrapolated_correction: Decimal | None
    rate_after_correction: Decimal | None
    materiality_rate: Decimal
    notes: tuple[str, ...]

    def rows(self) -> list[tuple[str, str, Decimal | None]]:
        """Template rows (row, German label, value; ``None`` for not applicable)."""
        return [
            ("A", "Prüfpopulation", self.audit_population),
            ("D", "Gesamtfehlerquote (TER)", self.total_error_rate),
            ("E1", "Beträge in laufender Bewertung (Art. 98 Abs. 6)", self.ongoing_assessment),
            ("E2", "Sonstige negative Beträge des Geschäftsjahres", self.other_negative_amounts),
            ("F=A-E1-E2", "Bereinigte Grundgesamtheit", self.population),
            ("G=D*F", "Risikobetrag", self.amount_at_risk),
            ("H", "Finanzkorrekturen", self.financial_corrections),
            ("I=F-H", "In der Rechnungslegung geltend zu machende Ausgaben", self.certifiable),
            ("J=G-H", "Verbleibender Risikobetrag", self.residual_amount),
            ("K=J/I", "Restfehlerquote (RER)", self.rate),
            (
                "L=(J-0.02*I)/0.98",
                "Hochgerechnete Finanzkorrektur bis zur Wesentlichkeit",
                self.extrapolated_correction,
            ),
            ("M=(J-L)/(I-L)", "RER nach hochgerechneter Korrektur", self.rate_after_correction),
        ]

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible result: numbers as float plus exact decimal strings."""
        return {
            "source": RER_TEMPLATE_ID,
            "rate": _float(self.rate),
            "rate_rounded": _float(self.rate_rounded),
            "exceeds_materiality": self.exceeds_materiality,
            "materiality_rate": float(self.materiality_rate),
            "extrapolated_correction": _float(self.extrapolated_correction),
            "rate_after_correction": _float(self.rate_after_correction),
            "rows": [
                {
                    "row": row,
                    "label": label,
                    "value": _float(value),
                    "exact": None if value is None else str(value),
                }
                for row, label, value in self.rows()
            ],
            "not_applicable": None if self.exceeds_materiality else NOT_APPLICABLE,
            "notes": list(self.notes),
        }


def _float(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def _checked(inputs: ResidualInputs, materiality: Number) -> tuple[Decimal, ...]:
    a = to_decimal(inputs.audit_population, "audit_population")
    d = to_decimal(inputs.total_error_rate, "total_error_rate")
    e1 = to_decimal(inputs.ongoing_assessment, "ongoing_assessment")
    e2 = to_decimal(inputs.other_negative_amounts, "other_negative_amounts")
    h = to_decimal(inputs.financial_corrections, "financial_corrections")
    m = to_decimal(materiality, "materiality_rate")
    if a <= 0:
        raise ExtrapolationInputError("A (Prüfpopulation) muss größer als 0 sein.")
    if not Decimal(0) <= d <= Decimal(1):
        raise ExtrapolationInputError(
            "D (Gesamtfehlerquote) ist ein Anteil in [0, 1], z. B. 0.022 für 2,2 %."
        )
    if min(e1, e2, h) < 0:
        raise ExtrapolationInputError("E1, E2 und H werden als nicht negative Beträge angegeben.")
    if not Decimal(0) < m <= DEFAULT_MATERIALITY:
        raise ExtrapolationInputError("Die Wesentlichkeitsschwelle muss in (0, 2 %] liegen.")
    return a, d, e1, e2, h, m


def residual_error_rate(
    inputs: ResidualInputs, materiality_rate: Number = DEFAULT_MATERIALITY
) -> ResidualErrorRate:
    """RER after financial corrections (template CPRE_23-0013-01 Annex 3, Art. 2 Nr. 36 CPR)."""
    a, d, e1, e2, h, m = _checked(inputs, materiality_rate)
    notes: list[str] = []
    with localcontext() as context:
        context.rounding = ROUND_HALF_UP
        f = a - e1 - e2
        g = d * f
        i = f - h
        j = g - h
        k = None if i == 0 else j / i
        k_rounded = None if k is None else k.quantize(THRESHOLD_QUANTUM)
        exceeds = k_rounded is not None and k_rounded > m
        correction = (j - m * i) / (1 - m) if exceeds else None
        after = None
        if correction is not None and i != correction:
            after = (j - correction) / (i - correction)
    if k is None:
        notes.append("I = 0: Restfehlerquote nicht berechenbar (Vorlage: IFERROR).")
    notes.append(
        f"RER nach {cpr('2 Nr. 36')}; nicht mit der Gesamtfehlerquote (TER) zu verwechseln."
    )
    return ResidualErrorRate(
        a, d, e1, e2, h, f, g, i, j, k, k_rounded, exceeds, correction, after, m, tuple(notes)
    )


def residual_from_total(
    total: TotalErrorRate,
    *,
    financial_corrections: Number = 0,
    ongoing_assessment: Number = 0,
    other_negative_amounts: Number = 0,
) -> ResidualErrorRate:
    """RER with A = audited population and D = TER of an evaluation."""
    return residual_error_rate(
        ResidualInputs(
            audit_population=total.book_value,
            total_error_rate=total.rate,
            ongoing_assessment=ongoing_assessment,
            other_negative_amounts=other_negative_amounts,
            financial_corrections=financial_corrections,
        ),
        total.materiality_rate,
    )
