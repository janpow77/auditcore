"""``POST /evaluate`` and ``POST /residual`` (framework-free).

The evaluation always comes from :func:`auditcore_extrapolation.assess`; the
residual error rate from :func:`auditcore_extrapolation.residual_error_rate`.
Both answers carry the contract id, the library version and a SHA-256
fingerprint of the canonical request, so that a report can be tied to its
input.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from ..attribute_variants import evaluate_discovery, evaluate_stop_or_go
from ..attributes import evaluate_attributes
from ..confidence import recalculate_confidence, system_confidence_level
from ..errors import ExtrapolationInputError
from ..evaluation import MATERIALITY_RATE, Assessment, assess
from ..groups import GroupsAssessment, assess_groups, assess_groups_over_periods
from ..methods import METHODS
from ..negative import DeclaredUnit, NegativeCheck, review_negative_units, split_population
from ..periods import assess_periods
from ..residual import ResidualInputs, residual_error_rate
from ._contract import CONTRACT, MAX_UNITS, ContractError, Reader
from ._design import Design, read_design
from .catalogue import LIBRARY


def fingerprint(payload: object) -> str:
    """SHA-256 over the request in canonical JSON (sorted keys, no spaces)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _required_level(body: Reader) -> float | None:
    if body.has("system_assessment") and body.has("required_confidence_level"):
        raise ContractError(
            "'system_assessment' und 'required_confidence_level' schließen sich aus."
        )
    if body.has("system_assessment"):
        return system_confidence_level(body.whole("system_assessment", minimum=1))
    return body.optional_number("required_confidence_level")


def _assess(
    method_id: str, body: Reader, design: Design
) -> tuple[Assessment, GroupsAssessment | None]:
    level = body.optional_number("confidence_level")
    profile = body.text("factor_profile") if body.has("factor_profile") else None
    materiality = body.number("materiality_rate", MATERIALITY_RATE)
    if design.periods is not None and design.period_groups is not None:
        grouped = assess_groups_over_periods(
            method_id,
            design.periods,
            design.period_groups,
            confidence_level=level,
            factor_profile=profile,
            population_units=design.population_units,
            materiality_rate=materiality,
        )
        return grouped.overall, grouped
    if design.periods is not None:
        return assess_periods(
            method_id,
            design.periods,
            confidence_level=level,
            factor_profile=profile,
            population_units=design.population_units,
            materiality_rate=materiality,
        ), None
    if design.groups is not None:
        grouped = assess_groups(
            method_id,
            design.groups,
            confidence_level=level,
            factor_profile=profile,
            materiality_rate=materiality,
        )
        return grouped.overall, grouped
    single = assess(
        method_id,
        design.strata,
        confidence_level=level,
        factor_profile=profile,
        sample_size=body.optional_whole("sample_size", minimum=1),
        materiality_rate=materiality,
    )
    return single, None


def evaluate(payload: object) -> dict[str, object]:
    """``POST /evaluate``: projection, precision, TER, upper limit and conclusion.

    Optional: several periods (guidance 7.3), groups of programmes (7.8),
    sub-samples of units (7.6, 6.5.3) and the recalculation of the
    confidence level for inconclusive results (7.7).
    """
    body = Reader(payload)
    method_id = body.text("method")
    if method_id not in METHODS:
        raise ContractError(f"Unbekannte Methode '{method_id}'. Zulässig: {', '.join(METHODS)}.")
    design = read_design(body)
    try:
        required = _required_level(body)
        assessment, grouped = _assess(method_id, body, design)
        recalculation = recalculate_confidence(
            assessment.projection, assessment.total_error_rate, required_level=required
        )
    except ExtrapolationInputError as exc:
        raise ContractError(str(exc)) from exc
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "fingerprint": fingerprint(payload),
        "method": METHODS[method_id].to_dict(),
        "design": design.kind,
        **assessment.to_dict(),
        "confidence_recalculation": recalculation.to_dict(),
        "subsamples": [s.to_dict() for s in design.subsamples],
        "groups": [] if grouped is None else [g.to_dict() for g in grouped.groups],
    }


def _attribute_result(body: Reader) -> dict[str, object]:
    approach = body.text("approach") if body.has("approach") else "normal"
    deviations, size = body.whole("deviations"), body.whole("sample_size", minimum=1)
    level, rate = body.number("confidence_level"), body.number("tolerable_rate")
    if approach == "normal":
        return evaluate_attributes(
            deviations,
            size,
            confidence_level=level,
            factor_profile=body.text("factor_profile"),
            tolerable_rate=rate,
        ).to_dict() | {"approach": "normal"}
    if approach == "discovery":
        return evaluate_discovery(
            deviations, size, confidence_level=level, critical_rate=rate
        ).to_dict()
    if approach == "stop_or_go":
        return evaluate_stop_or_go(
            deviations, size, confidence_level=level, tolerable_rate=rate
        ).to_dict()
    raise ContractError("'approach' muss normal, discovery oder stop_or_go sein.")


def attributes(payload: object) -> dict[str, object]:
    """``POST /attributes``: tests of controls (guidance 7.9; discovery and stop-or-go 7.9.6)."""
    body = Reader(payload)
    try:
        result = _attribute_result(body)
    except ExtrapolationInputError as exc:
        raise ContractError(str(exc)) from exc
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "fingerprint": fingerprint(payload),
        "attributes": result,
    }


def negative_units(payload: object) -> dict[str, object]:
    """``POST /negative-units``: positive and negative population (guidance 4.6)."""
    body = Reader(payload)
    try:
        split = split_population(
            [
                DeclaredUnit(
                    entry.text("id"),
                    entry.number("new_expenditure"),
                    entry.number("current_corrections", 0.0),
                    entry.number("previous_corrections", 0.0),
                )
                for entry in body.items("units", MAX_UNITS)
            ],
            body.whole("approach", minimum=1),
        )
        checks = body.items("checks", MAX_UNITS) if body.has("checks") else []
        review = review_negative_units(
            [
                NegativeCheck(
                    e.text("id"), e.number("corrected_amount"), e.number("decided_amount")
                )
                for e in checks
            ]
        )
    except ExtrapolationInputError as exc:
        raise ContractError(str(exc)) from exc
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "fingerprint": fingerprint(payload),
        "population": split.to_dict(),
        "review": review.to_dict(),
    }


def residual(payload: object) -> dict[str, object]:
    """``POST /residual``: RER after financial corrections (Annex 3 template)."""
    body = Reader(payload)
    zero = Decimal(0)
    try:
        result = residual_error_rate(
            ResidualInputs(
                audit_population=body.decimal("audit_population"),
                total_error_rate=body.decimal("total_error_rate"),
                ongoing_assessment=body.decimal("ongoing_assessment", zero),
                other_negative_amounts=body.decimal("other_negative_amounts", zero),
                financial_corrections=body.decimal("financial_corrections", zero),
            ),
            body.decimal("materiality_rate", Decimal("0.02")),
        )
    except ExtrapolationInputError as exc:
        raise ContractError(str(exc)) from exc
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "fingerprint": fingerprint(payload),
        "residual_error_rate": result.to_dict(),
    }
