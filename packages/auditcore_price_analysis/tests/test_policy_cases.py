"""Framework catalogue cases (verwaltung-app-framework docs/pruefkatalog.md) for this library."""

from __future__ import annotations

import ast
import json
from decimal import Decimal
from pathlib import Path

import auditcore_price_analysis
from auditcore_price_analysis import (
    ReleaseStatus,
    Tariff,
    calculate,
    group_statistics,
    load_calculation_profile,
    load_comparison_profile,
    select_tariff,
)

NW = load_calculation_profile("regulierung.hpp.nahwaerme", "2026.09.1")
CP = load_comparison_profile("regulierung.hpp.vergleich", "2026.09.1")


def test_t09_result_handover_contains_every_line_value_unit_and_profile_version() -> None:
    """Handover: all lines with unit/price/quantity/exact and rounded amount plus profile."""
    tariff = Tariff.from_mapping(
        {"grundpreis_eur_kw": "28.5", "arbeitspreis_ct_kwh": "10.82"}, NW, release="freigegeben"
    )
    result = calculate(tariff, NW, consumption={"kw": 12, "kwh": 27000}, stichtag="2025-07-01")
    data = json.loads(json.dumps(result.to_dict()))
    assert data["profile"] == {
        "profile_id": "regulierung.hpp.nahwaerme",
        "version": "2026.09.1",
        "fingerprint": NW.fingerprint,
    }
    assert [line["component"] for line in data["lines"]] == [c.name for c in NW.components]
    assert all(line["unit"] for line in data["lines"])
    assert sum(Decimal(line["amount"] or 0) for line in data["lines"]) == Decimal(data["total"])
    assert data["missing_optional"] == [
        "verrechnungspreis_eur_jahr",
        "emissionspreis_ct_kwh",
        "waermeumlagenpreis_ct_kwh",
    ]
    stats = group_statistics([1, 2], CP).to_dict()
    assert stats["profile"]["version"] == "2026.09.1" and stats["count"] == 2


def test_t09_no_release_is_ever_granted_by_the_library() -> None:
    """Freigabe: selection and calculation read the status, they never set it."""
    pending = Tariff.from_mapping({}, NW, release="ausstehend", valid_from="2025-01-01")
    result = calculate(pending, NW, consumption={"kw": 1, "kwh": 1}, stichtag="2025-02-01")
    assert result.release is ReleaseStatus.AUSSTEHEND and not result.comparable
    selection = select_tariff([pending], stichtag="2025-02-01", profile=CP)
    assert selection.tariff is None and pending.release is ReleaseStatus.AUSSTEHEND


def test_t14_library_does_not_log_or_print() -> None:
    """Protokolle: the library has no logging or print calls; results carry no environment."""
    for path in Path(auditcore_price_analysis.__file__).parent.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert not any(n.startswith("logging") for n in names), path.name
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "print", path.name
