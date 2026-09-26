"""Audited sampling units, error classification and sample statistics.

An audited unit carries its error split into the three classes of the
guidance (Appendix 1 and glossary, Appendix 6):

* random errors – projected to the population;
* systemic errors – only if their full extent in the population has been
  delimited; they are *not* projected but added with the delimited amount
  (errors of a systemic type that were not delimited are random errors);
* anomalous errors – demonstrably not representative of the population,
  excluded from the projection only with a written reason; if not corrected
  they are added to the total error rate (TER), corrected ones are not.

The error of a unit is the irregular amount (book value minus corrected book
value). Understatements are not errors in this sense and are rejected.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .errors import ExtrapolationInputError


@dataclass(frozen=True)
class SampleUnit:
    """One audited sampling unit (operation or payment claim)."""

    id: str
    book_value: float
    random_error: float = 0.0
    systemic_error: float = 0.0
    anomalous_error: float = 0.0
    anomalous_reason: str = ""
    anomalous_corrected: bool = False

    @property
    def total_error(self) -> float:
        """Sum of the three error classes."""
        return self.random_error + self.systemic_error + self.anomalous_error

    @property
    def random_rate(self) -> float:
        """Error rate (tainting) of the random error, E_i / BV_i."""
        return self.random_error / self.book_value


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ExtrapolationInputError(f"'{name}' muss eine endliche Zahl sein.")
    return float(value)


def check_unit(unit: SampleUnit) -> SampleUnit:
    """Validate one unit; raise with the unit id in the message."""
    label = f"Einheit '{unit.id}'"
    book = _finite(unit.book_value, f"{label}: Buchwert")
    if book <= 0:
        raise ExtrapolationInputError(
            f"{label}: Der Buchwert muss größer als 0 sein; negative Stichprobeneinheiten "
            "werden gesondert behandelt (Leitfaden, Abschn. 4.6)."
        )
    for name, value in (
        ("zufälliger Fehler", unit.random_error),
        ("systemischer Fehler", unit.systemic_error),
        ("anomaler Fehler", unit.anomalous_error),
    ):
        if _finite(value, f"{label}: {name}") < 0:
            raise ExtrapolationInputError(f"{label}: {name} darf nicht negativ sein.")
    if unit.total_error > book * (1 + 1e-12):
        raise ExtrapolationInputError(f"{label}: Die Fehler übersteigen den Buchwert.")
    if unit.anomalous_error > 0 and not unit.anomalous_reason.strip():
        raise ExtrapolationInputError(
            f"{label}: Ein anomaler Fehler wird nur mit Begründung aus der Hochrechnung "
            "ausgenommen (Leitfaden, Anhang 6: nachweislich nicht repräsentativ)."
        )
    if unit.anomalous_error == 0 and unit.anomalous_corrected:
        raise ExtrapolationInputError(f"{label}: 'korrigiert' ohne anomalen Fehler.")
    return unit


def check_units(units: Sequence[SampleUnit], *, minimum: int = 1) -> tuple[SampleUnit, ...]:
    """Validate a sample; ids must be unique."""
    checked = tuple(check_unit(u) for u in units)
    if len(checked) < minimum:
        raise ExtrapolationInputError(f"Mindestens {minimum} geprüfte Einheiten erforderlich.")
    ids = [u.id for u in checked]
    if len(set(ids)) != len(ids):
        raise ExtrapolationInputError("Die Kennungen der Einheiten müssen eindeutig sein.")
    return checked


def mean(values: Sequence[float]) -> float:
    """Arithmetic mean (``AVERAGE``)."""
    return math.fsum(values) / len(values)


def sample_variance(values: Sequence[float]) -> float:
    """Sample variance with n − 1 (``VAR.S``, guidance section 6.1.1.4)."""
    if len(values) < 2:
        raise ExtrapolationInputError(
            "Für die Präzision sind mindestens zwei Einheiten je Schicht nötig "
            "(Leitfaden, Abschn. 6.1.2.2: mindestens drei empfohlen)."
        )
    centre = mean(values)
    return math.fsum((v - centre) ** 2 for v in values) / (len(values) - 1)


def sample_sd(values: Sequence[float]) -> float:
    """Sample standard deviation (``STDEV.S``)."""
    return math.sqrt(sample_variance(values))


def sample_covariance(left: Sequence[float], right: Sequence[float]) -> float:
    """Sample covariance with n − 1 (``COVARIANCE.S``)."""
    if len(left) < 2:
        raise ExtrapolationInputError("Für die Kovarianz sind mindestens zwei Einheiten nötig.")
    centre_l, centre_r = mean(left), mean(right)
    products = ((a - centre_l) * (b - centre_r) for a, b in zip(left, right, strict=True))
    return math.fsum(products) / (len(left) - 1)


@dataclass(frozen=True)
class ErrorClasses:
    """Sample totals of the error classes (for the TER breakdown)."""

    random: float
    systemic: float
    anomalous_uncorrected: float
    anomalous_corrected: float

    @classmethod
    def of(cls, units: Sequence[SampleUnit]) -> ErrorClasses:
        """Totals over all given units."""
        return cls(
            math.fsum(u.random_error for u in units),
            math.fsum(u.systemic_error for u in units),
            math.fsum(u.anomalous_error for u in units if not u.anomalous_corrected),
            math.fsum(u.anomalous_error for u in units if u.anomalous_corrected),
        )
