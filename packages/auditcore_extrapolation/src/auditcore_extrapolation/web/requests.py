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

from ..design import Stratum
from ..errors import ExtrapolationInputError
from ..evaluation import MATERIALITY_RATE, assess
from ..methods import METHODS
from ..residual import ResidualInputs, residual_error_rate
from ..units import SampleUnit
from ._contract import CONTRACT, MAX_STRATA, MAX_UNITS, ContractError, Reader
from .catalogue import LIBRARY


def fingerprint(payload: object) -> str:
    """SHA-256 over the request in canonical JSON (sorted keys, no spaces)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _unit(entry: Reader) -> tuple[str, bool, SampleUnit]:
    unit = SampleUnit(
        id=entry.text("id"),
        book_value=entry.number("book_value"),
        random_error=entry.number("random_error", 0.0),
        systemic_error=entry.number("systemic_error", 0.0),
        anomalous_error=entry.number("anomalous_error", 0.0),
        anomalous_reason=entry.text("anomalous_reason", required=False),
        anomalous_corrected=entry.flag("anomalous_corrected"),
    )
    return entry.text("stratum"), entry.flag("exhaustive"), unit


def _strata(body: Reader) -> list[Stratum]:
    units = [_unit(entry) for entry in body.items("units", MAX_UNITS)]
    strata = []
    for entry in body.items("strata", MAX_STRATA):
        name = entry.text("name")
        members = [(exhaustive, unit) for stratum, exhaustive, unit in units if stratum == name]
        strata.append(
            Stratum(
                name=name,
                book_value=entry.number("book_value"),
                units=tuple(u for exhaustive, u in members if not exhaustive),
                exhaustive_units=tuple(u for exhaustive, u in members if exhaustive),
                population_size=entry.optional_whole("population_size", minimum=1),
                systemic_error=entry.number("systemic_error", 0.0),
            )
        )
    known = {s.name for s in strata}
    unknown = sorted({stratum for stratum, _, _ in units} - known)
    if unknown:
        raise ContractError(f"Einheiten verweisen auf unbekannte Schichten: {', '.join(unknown)}.")
    return strata


def evaluate(payload: object) -> dict[str, object]:
    """``POST /evaluate``: projection, precision, TER, upper limit and conclusion."""
    body = Reader(payload)
    method_id = body.text("method")
    if method_id not in METHODS:
        raise ContractError(f"Unbekannte Methode '{method_id}'. Zulässig: {', '.join(METHODS)}.")
    try:
        assessment = assess(
            method_id,
            _strata(body),
            confidence_level=body.optional_number("confidence_level"),
            factor_profile=body.text("factor_profile") if body.has("factor_profile") else None,
            sample_size=body.optional_whole("sample_size", minimum=1),
            materiality_rate=body.number("materiality_rate", MATERIALITY_RATE),
        )
    except ExtrapolationInputError as exc:
        raise ContractError(str(exc)) from exc
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "fingerprint": fingerprint(payload),
        "method": METHODS[method_id].to_dict(),
        **assessment.to_dict(),
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
