"""Sample-size methods for monetary-unit (MUS) and simple random sampling (SRS).

Two MUS methods exist in the source applications and give very different
results; neither is chosen silently:

* ``flowstat.mus_z_attribute`` — ``flowstat@d665ac2`` formula
  ``n = ceil(V·z²·(1-r) / (M² + z²·(1-r)))``. For realistic materiality the
  result collapses to 1; ``audit-portal`` labels it mathematically wrong
  ("Audit H KRIT-1"). Kept as characterized method profile.
* ``portal.mus_poisson`` — ``audit-portal@d8eefa4`` formula
  ``n = ceil(RF·V / max(M - V·r, M/2))`` with Poisson reliability factors.

Decision of the rights holder and user on 2026-09-23 ("mus 30"):
``portal.mus_poisson`` is the authoritative MUS sample-size method
(``RECOMMENDED_MUS_METHOD``, ``recommended_mus_size``). ``flowstat.mus_z_attribute``
stays available as a named, superseded legacy method for replay and
migration; existing named functions keep their behavior.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

FLOWSTAT_COMMIT = "d665ac221f50ba1f465b7337bdd4aa218d78ec8a"
PORTAL_COMMIT = "d8eefa426826bdecb67036774f3128ae05e7d0d0"


class SamplingInputError(ValueError):
    """Input or method choice does not satisfy the documented contract."""


@dataclass(frozen=True)
class Method:
    """A named, source-bound sample-size method."""

    id: str
    kind: str
    source: str
    factors: MappingProxyType[float, float]
    status: str
    note: str


MUS_Z_ATTRIBUTE = Method(
    "flowstat.mus_z_attribute",
    "mus",
    f"janpow77/flowstat@{FLOWSTAT_COMMIT}:backend/app/services/sampling_service.py"
    ":_calculate_mus_sample_size",
    MappingProxyType({0.90: 1.645, 0.95: 1.96, 0.99: 2.576}),
    "SUPERSEDED",
    "Nenner M² + z²(1-r): bei üblicher Wesentlichkeit Stichprobenumfang 1. "
    "Fachlich abgelöst durch portal.mus_poisson (Nutzerentscheidung vom 23.09.2026); "
    "nur noch für Nachvollzug und Migration.",
)
MUS_POISSON = Method(
    "portal.mus_poisson",
    "mus",
    f"janpow77/audit-portal@{PORTAL_COMMIT}:backend/app/modules/flowstat/services/"
    "sampling_service.py:_calculate_mus_sample_size",
    MappingProxyType({0.50: 0.70, 0.80: 1.61, 0.90: 2.31, 0.95: 3.00, 0.97: 3.51, 0.99: 4.61}),
    "RECOMMENDED",
    "Poisson-Zuverlässigkeitsfaktoren; die Quelle nennt EU-KOM Guidance Note "
    "'Sampling for Audit' / ISA 530 Annex II (fachlich nicht durch diese Bibliothek geprüft).",
)
SRS_FLOWSTAT = Method(
    "flowstat.srs_normal",
    "srs",
    f"janpow77/flowstat@{FLOWSTAT_COMMIT}:backend/app/services/sampling_service.py"
    ":_calculate_srs_sample_size",
    MappingProxyType({0.90: 1.645, 0.95: 1.96, 0.99: 2.576}),
    "LEGACY_CHARACTERIZED",
    "n = z²p(1-p)/e² mit Endlichkeitskorrektur.",
)
SRS_PORTAL = Method(
    "portal.srs_normal",
    "srs",
    f"janpow77/audit-portal@{PORTAL_COMMIT}:backend/app/modules/flowstat/services/"
    "sampling_service.py:_calculate_srs_sample_size",
    MappingProxyType({0.50: 0.674, 0.80: 1.282, 0.90: 1.645, 0.95: 1.960, 0.99: 2.576}),
    "LEGACY_CHARACTERIZED",
    "Gleiche Formel, größere z-Tabelle (50/80 %).",
)
#: Authoritative MUS method, decided by the user on 2026-09-23.
RECOMMENDED_MUS_METHOD = MUS_POISSON.id
MUS_DECISION = MappingProxyType(
    {
        "method": MUS_POISSON.id,
        "superseded": MUS_Z_ATTRIBUTE.id,
        "decided_on": "2026-09-23",
        "decided_by": "Rechteinhaber/Nutzer (janpow77)",
        "statement": "mus 30",
        "reference_case": (
            "475.478,94 € Grundgesamtheit, 50.000 € Wesentlichkeit, 0,5 %, 95 % → n = 30 "
            "(aufgezeichneter Fall portal-run_mus_standard-uniform100-50000.0-0)"
        ),
    }
)

METHODS = MappingProxyType(
    {m.id: m for m in (MUS_Z_ATTRIBUTE, MUS_POISSON, SRS_FLOWSTAT, SRS_PORTAL)}
)


@dataclass(frozen=True)
class SizePlan:
    """Result of a sample-size calculation with its method and inputs."""

    method: str
    sample_size: int
    interval: float
    inputs: MappingProxyType[str, Any]
    warnings: tuple[str, ...] = field(default=())

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible plan."""
        return {
            "library": "auditcore_sampling 0.2.1",
            "method": self.method,
            "sample_size": self.sample_size,
            "interval": self.interval,
            "inputs": dict(self.inputs),
            "warnings": list(self.warnings),
        }


def method(method_id: str, kind: str) -> Method:
    """Look up an explicitly named method of the given kind."""
    found = METHODS.get(method_id)
    if found is None or found.kind != kind:
        allowed = ", ".join(sorted(k for k, v in METHODS.items() if v.kind == kind))
        raise SamplingInputError(
            f"Unbekannte {kind.upper()}-Methode '{method_id}'. Zulässig: {allowed}."
        )
    return found


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SamplingInputError(f"'{name}' muss eine endliche Zahl sein.")
    return float(value)


def _factor(chosen: Method, confidence_level: object) -> float:
    level = _number(confidence_level, "confidence_level")
    try:
        return chosen.factors[level]
    except KeyError as exc:
        allowed = ", ".join(str(k) for k in sorted(chosen.factors))
        raise SamplingInputError(
            f"Konfidenzniveau {level} ist in {chosen.id} nicht definiert; zulässig: {allowed}. "
            "Es wird kein Ersatzwert angenommen."
        ) from exc


def mus_size(
    method_id: str,
    *,
    population_value: float,
    materiality: float,
    expected_error_rate: float,
    confidence_level: float,
) -> SizePlan:
    """MUS sample size and sampling interval with strict inputs.

    Raises:
        SamplingInputError: unknown method, undefined confidence level,
            materiality ≤ 0, population value < 0 or error rate outside [0, 1).
    """
    chosen = method(method_id, "mus")
    value = _number(population_value, "population_value")
    mat = _number(materiality, "materiality")
    rate = _number(expected_error_rate, "expected_error_rate")
    factor = _factor(chosen, confidence_level)
    if mat <= 0:
        raise SamplingInputError("Die Wesentlichkeit muss größer als 0 sein.")
    if value < 0:
        raise SamplingInputError("Der Wert der Grundgesamtheit darf nicht negativ sein.")
    if not 0 <= rate < 1:
        raise SamplingInputError("Die erwartete Fehlerrate muss in [0, 1) liegen.")
    inputs = MappingProxyType(
        {
            "population_value": value,
            "materiality": mat,
            "expected_error_rate": rate,
            "confidence_level": float(confidence_level),
            "factor": factor,
        }
    )
    if value == 0:
        return SizePlan(chosen.id, 0, 0.0, inputs, ("Grundgesamtheit ohne Wert.",))
    warnings: list[str] = []
    if chosen is MUS_Z_ATTRIBUTE:
        numerator = value * factor**2 * (1 - rate)
        size = math.ceil(numerator / (mat**2 + factor**2 * (1 - rate)))
        warnings.append(chosen.note)
    else:
        precision = max(mat - value * rate, mat * 0.5)
        size = math.ceil(factor * value / precision)
        if mat - value * rate < mat * 0.5:
            warnings.append("Präzision auf 50 % der Wesentlichkeit begrenzt.")
    interval = value / size if size > 0 else 0.0
    return SizePlan(chosen.id, int(size), interval, inputs, tuple(warnings))


def srs_size(
    method_id: str,
    *,
    population_size: int,
    confidence_level: float,
    margin_of_error: float,
    expected_proportion: float = 0.5,
) -> SizePlan:
    """SRS sample size n = z²p(1-p)/e² with finite population correction, capped at N.

    Raises:
        SamplingInputError: unknown method/level, N < 1, e outside (0, 1),
            p outside [0, 1].
    """
    chosen = method(method_id, "srs")
    if isinstance(population_size, bool) or not isinstance(population_size, int):
        raise SamplingInputError("'population_size' muss eine ganze Zahl sein.")
    if population_size < 1:
        raise SamplingInputError("Die Grundgesamtheit muss mindestens ein Element enthalten.")
    z = _factor(chosen, confidence_level)
    e = _number(margin_of_error, "margin_of_error")
    p = _number(expected_proportion, "expected_proportion")
    if not 0 < e < 1:
        raise SamplingInputError("Die Fehlertoleranz muss in (0, 1) liegen.")
    if not 0 <= p <= 1:
        raise SamplingInputError("Der erwartete Anteil muss in [0, 1] liegen.")
    n = z**2 * p * (1 - p) / e**2
    adjusted = 0.0 if n == 0 else n / (1 + (n - 1) / population_size)
    size = min(math.ceil(adjusted), population_size)
    warnings = ("Erwarteter Anteil 0 oder 1 ergibt keine Varianz.",) if p in (0.0, 1.0) else ()
    return SizePlan(
        chosen.id,
        int(size),
        0.0,
        MappingProxyType(
            {
                "population_size": population_size,
                "confidence_level": float(confidence_level),
                "margin_of_error": e,
                "expected_proportion": p,
                "factor": z,
            }
        ),
        warnings,
    )


def recommended_mus_method() -> Method:
    """The decided MUS method (``portal.mus_poisson``), see ``MUS_DECISION``."""
    return METHODS[RECOMMENDED_MUS_METHOD]


def recommended_mus_size(
    *,
    population_value: float,
    materiality: float,
    expected_error_rate: float,
    confidence_level: float,
) -> SizePlan:
    """MUS sample size with the decided method; same contract as :func:`mus_size`."""
    return mus_size(
        RECOMMENDED_MUS_METHOD,
        population_value=population_value,
        materiality=materiality,
        expected_error_rate=expected_error_rate,
        confidence_level=confidence_level,
    )
