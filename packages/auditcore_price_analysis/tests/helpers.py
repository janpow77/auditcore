"""Run a legacy calculator case through the new contract (explicit consumption, released)."""

from __future__ import annotations

from typing import Any

from replay import decode

from auditcore_price_analysis import (
    CalculationResult,
    ReleaseStatus,
    Tariff,
    calculate,
    load_calculation_profile,
)

PROFILES = {
    "calculate_nahwaerme": ("regulierung.hpp.nahwaerme", "2026.09.1"),
    "calculate_wasser": ("regulierung.hpp.wasser", "2026.09.1"),
}
LEGACY_DEFAULTS = {
    "calculate_nahwaerme": {"kw": 12.0, "kwh": 27000.0},
    "calculate_wasser": {"q3": 4.0, "m3": 150.0},
}


def run_new(case: dict[str, Any]) -> CalculationResult:
    """The legacy defaults are passed explicitly, the tariff counts as released."""
    profile = load_calculation_profile(*PROFILES[case["function"]])
    args = decode(case["args"])
    kwargs = decode(case["kwargs"])
    stichtag = kwargs.pop("stichtag", "2025-01-01")
    consumption = {**LEGACY_DEFAULTS[case["function"]], **kwargs}
    tariff = Tariff.from_mapping(args[0], profile, release=ReleaseStatus.FREIGEGEBEN)
    return calculate(tariff, profile, consumption=consumption, stichtag=stichtag)
