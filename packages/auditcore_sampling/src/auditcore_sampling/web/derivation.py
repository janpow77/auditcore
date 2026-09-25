"""Sample-size calculation with a step-by-step derivation (framework-free).

The sample size itself always comes from :func:`auditcore_sampling.mus_size`
or :func:`auditcore_sampling.srs_size`; the derivation re-states the
documented formula with the substituted values so that an auditor can
retrace the result. A derivation that disagrees with the library result is a
programming error and raises.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from ..sizes import METHODS, MUS_Z_ATTRIBUTE, SamplingInputError, SizePlan, mus_size, srs_size
from ._validate import ContractError, as_object, integer, number, require, text
from .profiles import LIBRARY


def _step(label: str, formula: str, value: float) -> dict[str, Any]:
    return {"label": label, "formula": formula, "value": value}


def _mus_steps(plan: SizePlan) -> list[dict[str, Any]]:
    inputs = plan.inputs
    value, mat = inputs["population_value"], inputs["materiality"]
    rate, factor = inputs["expected_error_rate"], inputs["factor"]
    level = inputs["confidence_level"]
    if plan.method == MUS_Z_ATTRIBUTE.id:
        numerator = value * factor**2 * (1 - rate)
        denominator = mat**2 + factor**2 * (1 - rate)
        steps = [
            _step(f"z-Wert bei {level:.0%} Konfidenz", "z", factor),
            _step("Zähler", "V · z² · (1 − r)", numerator),
            _step("Nenner", "M² + z² · (1 − r)", denominator),
            _step("Stichprobenumfang", "n = ⌈Zähler / Nenner⌉", math.ceil(numerator / denominator)),
        ]
    else:
        expected = value * rate
        precision = max(mat - expected, mat * 0.5)
        steps = [
            _step(f"Zuverlässigkeitsfaktor bei {level:.0%} Konfidenz", "RF", factor),
            _step("Erwarteter Fehler", "E = V · r", expected),
            _step("Präzision", "P = max(M − E, M / 2)", precision),
            _step("Stichprobenumfang", "n = ⌈RF · V / P⌉", math.ceil(factor * value / precision)),
        ]
    steps.append(_step("Stichprobenintervall", "J = V / n", plan.interval))
    return steps


def _srs_steps(plan: SizePlan) -> list[dict[str, Any]]:
    inputs = plan.inputs
    z, p, e = inputs["factor"], inputs["expected_proportion"], inputs["margin_of_error"]
    population = inputs["population_size"]
    level = inputs["confidence_level"]
    initial = z**2 * p * (1 - p) / e**2
    adjusted = 0.0 if initial == 0 else initial / (1 + (initial - 1) / population)
    return [
        _step(f"z-Wert bei {level:.0%} Konfidenz", "z", z),
        _step("Umfang ohne Endlichkeitskorrektur", "n₀ = z² · p · (1 − p) / e²", initial),
        _step("Endlichkeitskorrektur", "n₀ / (1 + (n₀ − 1) / N)", adjusted),
        _step("Stichprobenumfang", "n = min(⌈…⌉, N)", min(math.ceil(adjusted), population)),
    ]


def _plan(method_id: str, body: Mapping[str, object]) -> SizePlan:
    chosen = METHODS.get(method_id)
    if chosen is None:
        raise ContractError(
            f"Unbekannte Methode '{method_id}'. Zulässig: {', '.join(sorted(METHODS))}."
        )
    level = number(require(body, "confidence_level"), "confidence_level")
    if chosen.kind == "mus":
        return mus_size(
            method_id,
            population_value=number(require(body, "population_value"), "population_value"),
            materiality=number(require(body, "materiality"), "materiality"),
            expected_error_rate=number(require(body, "expected_error_rate"), "expected_error_rate"),
            confidence_level=level,
        )
    return srs_size(
        method_id,
        population_size=integer(require(body, "population_size"), "population_size", minimum=1),
        confidence_level=level,
        margin_of_error=number(require(body, "margin_of_error"), "margin_of_error"),
        expected_proportion=number(require(body, "expected_proportion"), "expected_proportion"),
    )


def calculate_size(payload: object) -> dict[str, Any]:
    """``POST /size``: sample size, interval, warnings and derivation."""
    body = as_object(payload)
    method_id = text(require(body, "method"), "method")
    try:
        plan = _plan(method_id, body)
    except SamplingInputError as exc:
        raise ContractError(str(exc)) from exc
    kind = METHODS[method_id].kind
    steps = _mus_steps(plan) if kind == "mus" else _srs_steps(plan)
    if plan.sample_size > 0 and steps[-2 if kind == "mus" else -1]["value"] != plan.sample_size:
        raise AssertionError("Herleitung weicht vom Bibliotheksergebnis ab.")
    result = plan.to_dict()
    result["library"] = LIBRARY
    result["kind"] = kind
    result["status"] = METHODS[method_id].status
    result["derivation"] = steps if plan.sample_size > 0 else []
    return result
