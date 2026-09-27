"""``POST /guidance/size`` and ``POST /guidance/draw`` (framework-free, contract ``/1``).

Every field is validated; nothing is defaulted except the materiality rate
(2 %, the regulatory maximum, returned in ``inputs``). The plan and its
derivation come unchanged from :mod:`auditcore_sampling.guidance`.
"""

from __future__ import annotations

import random
import secrets
from collections.abc import Callable, Mapping

from auditcore_common.rest import bounded_list

from .. import guidance as g
from .. import intermediate_body as zs
from ..sizes import SamplingInputError
from ._validate import MAX_ITEMS, ContractError, as_object, integer, number, optional_seed, require
from .draw import GENERATED_SEED_LIMIT
from .guidance_catalogue import CONTRACT
from .profiles import LIBRARY

MAX_STRATA = 1_000


def _text(body: Mapping[str, object], key: str) -> str:
    value = require(body, key)
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"'{key}' muss ein nicht leerer Text sein.")
    return value


def _flag(body: Mapping[str, object], key: str) -> bool:
    value = body.get(key, False)
    if not isinstance(value, bool):
        raise ContractError(f"'{key}' muss wahr oder falsch sein.")
    return value


def _optional_number(entry: Mapping[str, object], key: str, label: str) -> float | None:
    value = entry.get(key)
    return None if value is None else number(value, f"{label}.{key}")


def _stratum(position: int, raw: object) -> g.StratumInput:
    label = f"strata[{position}]"
    entry = as_object(raw, label)
    size = entry.get("population_size")
    return g.StratumInput(
        name=_text(entry, "name"),
        population_size=None
        if size is None
        else integer(size, f"{label}.population_size", minimum=1),
        book_value=_optional_number(entry, "book_value", label),
        sd=_optional_number(entry, "sd", label),
        exhaustive=_flag(entry, "exhaustive"),
    )


def _strata(body: Mapping[str, object]) -> list[g.StratumInput]:
    entries = bounded_list(
        require(body, "strata"), "strata", MAX_STRATA, "Schichten", error=ContractError
    )
    return [_stratum(i, e) for i, e in enumerate(entries)]


def _common(body: Mapping[str, object]) -> dict[str, object]:
    return {
        "confidence_level": number(require(body, "confidence_level"), "confidence_level"),
        "factor_profile": _text(body, "factor_profile"),
        "anticipated_error_rate": number(
            require(body, "anticipated_error_rate"), "anticipated_error_rate"
        ),
        "materiality_rate": number(
            body.get("materiality_rate", g.MATERIALITY_RATE), "materiality_rate"
        ),
    }


def _book_value(body: Mapping[str, object]) -> float:
    return number(require(body, "book_value"), "book_value")


def _equal(method: str) -> Callable[[Mapping[str, object]], g.GuidancePlan]:
    def plan(body: Mapping[str, object]) -> g.GuidancePlan:
        return g.equal_probability_size(
            method,
            population_size=integer(require(body, "population_size"), "population_size", minimum=1),
            book_value=_book_value(body),
            error_sd=number(require(body, "error_sd"), "error_sd"),
            finite_population_correction=_flag(body, "finite_population_correction"),
            **_common(body),  # type: ignore[arg-type]
        )

    return plan


def _stratified(method: str) -> Callable[[Mapping[str, object]], g.GuidancePlan]:
    def plan(body: Mapping[str, object]) -> g.GuidancePlan:
        return g.stratified_equal_probability_size(
            method,
            strata=_strata(body),
            book_value=_book_value(body),
            finite_population_correction=_flag(body, "finite_population_correction"),
            **_common(body),  # type: ignore[arg-type]
        )

    return plan


def _mus_standard(body: Mapping[str, object]) -> g.GuidancePlan:
    raw_values = body.get("book_values")
    values = None
    if raw_values is not None:
        entries = bounded_list(
            raw_values, "book_values", MAX_ITEMS, "Buchwerte", error=ContractError
        )
        values = [number(v, f"book_values[{i}]") for i, v in enumerate(entries)]
    return g.mus_standard_size(
        book_value=_book_value(body),
        error_rate_sd=number(require(body, "error_rate_sd"), "error_rate_sd"),
        book_values=values,
        **_common(body),  # type: ignore[arg-type]
    )


def _mus_stratified(body: Mapping[str, object]) -> g.GuidancePlan:
    return g.mus_stratified_size(strata=_strata(body), **_common(body))  # type: ignore[arg-type]


def _mus_conservative(body: Mapping[str, object]) -> g.GuidancePlan:
    return g.mus_conservative_size(book_value=_book_value(body), **_common(body))  # type: ignore[arg-type]


def _nonstatistical(body: Mapping[str, object]) -> g.GuidancePlan:
    value = body.get("book_value")
    level = body.get("assurance_level")
    if level is not None and not isinstance(level, str):
        raise ContractError("'assurance_level' muss Text sein.")
    return g.nonstatistical_minimum(
        _text(body, "rule"),
        population_size=integer(require(body, "population_size"), "population_size", minimum=1),
        book_value=None if value is None else number(value, "book_value"),
        assurance_level=level,
    )


PLANNERS: dict[str, Callable[[Mapping[str, object]], g.GuidancePlan]] = {
    g.SRS: _equal(g.SRS),
    f"{g.SRS}_stratified": _stratified(g.SRS),
    g.DIFFERENCE: _equal(g.DIFFERENCE),
    f"{g.DIFFERENCE}_stratified": _stratified(g.DIFFERENCE),
    g.MUS_STANDARD: _mus_standard,
    g.MUS_STRATIFIED: _mus_stratified,
    g.MUS_CONSERVATIVE: _mus_conservative,
    g.NONSTATISTICAL: _nonstatistical,
}


def plan_size(payload: object) -> dict[str, object]:
    """``POST /guidance/size``: plan with derivation, allocation and warnings."""
    body = as_object(payload)
    method = _text(body, "method")
    planner = PLANNERS.get(method)
    if planner is None:
        raise ContractError(f"Unbekannte Methode '{method}'. Zulässig: {', '.join(PLANNERS)}.")
    try:
        plan = planner(body)
    except SamplingInputError as exc:
        raise ContractError(str(exc)) from exc
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "status_label": g.GUIDANCE_STATUS_LABEL,
        **plan.to_dict(),
    }


def _procedure(body: Mapping[str, object]) -> zs.ValueShareProfile:
    chosen = zs.profile(_text(body, "procedure"))
    overrides = as_object(body.get("parameters", {}), "parameters")
    return chosen.with_parameters(**overrides) if overrides else chosen


def draw(payload: object) -> dict[str, object]:
    """``POST /guidance/draw``: value-share draw of a procedure profile with a visible seed."""
    body = as_object(payload)
    amounts = bounded_list(
        require(body, "amounts"), "amounts", MAX_ITEMS, "Beträge", error=ContractError
    )
    errors = bounded_list(
        body.get("errors", [0.0] * len(amounts)), "errors", MAX_ITEMS, "Fehler", error=ContractError
    )
    seed = optional_seed(body.get("seed"))
    generated = seed is None
    if seed is None:
        seed = secrets.randbelow(GENERATED_SEED_LIMIT)
    try:
        chosen = _procedure(body)
        order = zs.draw_order(random.Random(seed), len(amounts))
        result = zs.value_share_draw(amounts, errors, order, chosen)  # type: ignore[arg-type]
    except SamplingInputError as exc:
        raise ContractError(str(exc)) from exc
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "seed": seed,
        "seed_generated": generated,
        "profile": chosen.to_dict(),
        **result.to_dict(),
    }
