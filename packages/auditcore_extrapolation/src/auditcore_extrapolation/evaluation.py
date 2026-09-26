"""Total error rate (TER), upper limit of error and audit conclusion.

TER = projected random errors + delimited systemic errors + uncorrected
anomalous errors, divided by the audited population (Art. 2 Nr. 35 of
Regulation (EU) 2021/1060; guidance glossary and Appendix 1). Corrected
anomalous errors are not part of the TER. With systemic or anomalous errors
the upper limit of error is ULE = TER + SE (Appendix 1, section 1). The
conclusion follows guidance section 4.12 (statistical) or 6.4.6
(non-statistical). The residual error rate (RER) is a separate calculation,
see :mod:`auditcore_extrapolation.residual`.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .design import Stratum
from .errors import ExtrapolationInputError
from .methods import project
from .projection import Projection
from .sources import Step, cpr, guidance

#: Materiality threshold of 2 % of the expenditure (guidance section 4.9).
MATERIALITY_RATE = 0.02
MATERIAL = "material"
NOT_MATERIAL = "not_material"
INCONCLUSIVE = "inconclusive"

CONCLUSION_TEXTS = {
    MATERIAL: "Wesentlicher Fehler: Die Gesamtfehlerquote liegt über der Wesentlichkeitsschwelle.",
    NOT_MATERIAL: "Kein wesentlicher Fehler: Auch die Fehlerobergrenze liegt unter der "
    "Wesentlichkeitsschwelle.",
    INCONCLUSIVE: "Nicht schlüssig: Die Gesamtfehlerquote liegt unter, die Fehlerobergrenze über "
    "der Wesentlichkeitsschwelle. Weitere Prüfungshandlungen nach Abschn. 4.12 des Leitfadens "
    "(Klärung durch die geprüfte Stelle, Stichprobe erweitern, alternative Prüfungshandlungen).",
}


@dataclass(frozen=True)
class DifferenceFigures:
    """Corrected book value view of difference estimation (section 6.2.1.5)."""

    corrected_book_value: float
    lower_limit: float
    book_value_less_tolerable: float

    def to_dict(self) -> dict[str, float]:
        """JSON-compatible figures."""
        return {
            "corrected_book_value": self.corrected_book_value,
            "lower_limit": self.lower_limit,
            "book_value_less_tolerable": self.book_value_less_tolerable,
        }


@dataclass(frozen=True)
class TotalErrorRate:
    """TER with its components, upper limit and conclusion (not the RER)."""

    book_value: float
    materiality_rate: float
    tolerable_error: float
    projected_random_error: float
    systemic_errors: float
    anomalous_uncorrected: float
    anomalous_corrected_excluded: float
    total_error: float
    rate: float
    precision: float | None
    upper_limit: float | None
    upper_limit_rate: float | None
    conclusion: str
    explanation: tuple[str, ...]
    steps: tuple[Step, ...]
    difference: DifferenceFigures | None = None

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible TER."""
        return {
            "book_value": self.book_value,
            "materiality_rate": self.materiality_rate,
            "tolerable_error": self.tolerable_error,
            "projected_random_error": self.projected_random_error,
            "systemic_errors": self.systemic_errors,
            "anomalous_uncorrected": self.anomalous_uncorrected,
            "anomalous_corrected_excluded": self.anomalous_corrected_excluded,
            "total_error": self.total_error,
            "rate": self.rate,
            "precision": self.precision,
            "upper_limit": self.upper_limit,
            "upper_limit_rate": self.upper_limit_rate,
            "conclusion": self.conclusion,
            "explanation": list(self.explanation),
            "steps": [s.to_dict() for s in self.steps],
            "difference": None if self.difference is None else self.difference.to_dict(),
        }


def check_materiality(rate: float) -> float:
    """Materiality rate in (0, 2 %]; a higher threshold is not admissible."""
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate):
        raise ExtrapolationInputError("Die Wesentlichkeitsschwelle muss eine Zahl sein.")
    if not 0 < rate <= MATERIALITY_RATE:
        raise ExtrapolationInputError(
            "Die Wesentlichkeitsschwelle muss größer als 0 und höchstens 2 % sein "
            "(Leitfaden, Abschn. 4.9)."
        )
    return float(rate)


def conclude(total: float, upper: float | None, tolerable: float) -> str:
    """Conclusion of guidance section 4.12, or 6.4.6 when ``upper`` is None (non-statistical)."""
    if total > tolerable:
        return MATERIAL
    if upper is None or upper < tolerable:
        return NOT_MATERIAL
    return INCONCLUSIVE


def _explanation(projection: Projection, conclusion: str) -> tuple[str, ...]:
    lines = [CONCLUSION_TEXTS[conclusion]]
    if projection.precision is None:
        lines.append(
            "Nicht-statistische Stichprobe: Präzision und Fehlerobergrenze sind nicht bestimmbar; "
            "der hochgerechnete Fehler ist die beste Schätzung (Leitfaden, Abschn. 6.4.6)."
        )
    else:
        lines.append(
            f"Konfidenzniveau {projection.confidence_level:.0%}: Die Fehlerobergrenze ist "
            "Gesamtfehler plus Präzision (Leitfaden, Abschn. 4.12 und Anhang 1)."
        )
    if projection.systemic_population:
        lines.append(
            "Abgegrenzte systemische Fehler sind nicht hochgerechnet, sondern mit ihrem "
            "abgegrenzten Betrag enthalten (Leitfaden, Anhang 1)."
        )
    if projection.error_classes.anomalous_corrected:
        lines.append("Korrigierte anomale Fehler sind nicht Teil der Gesamtfehlerquote.")
    return tuple(lines)


def evaluate(
    projection: Projection, book_value: float, materiality_rate: float = MATERIALITY_RATE
) -> TotalErrorRate:
    """TER, upper limit and conclusion for a projection over population ``book_value``."""
    rate = check_materiality(materiality_rate)
    if not math.isfinite(book_value) or book_value <= 0:
        raise ExtrapolationInputError("Der Buchwert der Grundgesamtheit muss größer als 0 sein.")
    tolerable = rate * book_value
    classes = projection.error_classes
    total = math.fsum(
        [
            projection.projected_random_error,
            projection.systemic_population,
            classes.anomalous_uncorrected,
        ]
    )
    upper = None if projection.precision is None else total + projection.precision
    conclusion = conclude(total, upper, tolerable)
    steps = [
        Step("Tolerierbarer Fehler", "TE = Wesentlichkeit × BV", tolerable, guidance("4.10")),
        Step(
            "Gesamtfehler",
            "EE + systemische + nicht korrigierte anomale Fehler",
            total,
            guidance("Anhang 1"),
        ),
        Step("Gesamtfehlerquote (TER)", "TER / BV", total / book_value, cpr("2 Nr. 35")),
    ]
    if upper is not None:
        steps.append(Step("Fehlerobergrenze", "ULE = TER + SE", upper, guidance("4.12, Anhang 1")))
    difference = None
    if projection.method == "difference" and projection.precision is not None:
        corrected = book_value - total
        difference = DifferenceFigures(
            corrected, corrected - projection.precision, book_value - tolerable
        )
        steps.append(
            Step("Korrigierter Buchwert", "CBV = BV − TER", corrected, guidance("Anhang 1, 3"))
        )
    return TotalErrorRate(
        book_value,
        rate,
        tolerable,
        projection.projected_random_error,
        projection.systemic_population,
        classes.anomalous_uncorrected,
        classes.anomalous_corrected,
        total,
        total / book_value,
        projection.precision,
        upper,
        None if upper is None else upper / book_value,
        conclusion,
        _explanation(projection, conclusion),
        tuple(steps),
        difference,
    )


@dataclass(frozen=True)
class Assessment:
    """Projection and total error rate of one audited sample."""

    projection: Projection
    total_error_rate: TotalErrorRate

    def to_dict(self) -> dict[str, object]:
        """JSON-compatible assessment."""
        return {
            "projection": self.projection.to_dict(),
            "total_error_rate": self.total_error_rate.to_dict(),
        }


def assess(
    method_id: str,
    strata: Sequence[Stratum],
    *,
    confidence_level: float | None = None,
    factor_profile: str | None = None,
    sample_size: int | None = None,
    materiality_rate: float = MATERIALITY_RATE,
) -> Assessment:
    """Project and evaluate in one step; BV is the sum of the strata book values."""
    projection = project(
        method_id,
        strata,
        confidence_level=confidence_level,
        factor_profile=factor_profile,
        sample_size=sample_size,
    )
    book_value = math.fsum(s.book_value for s in strata)
    return Assessment(projection, evaluate(projection, book_value, materiality_rate))
