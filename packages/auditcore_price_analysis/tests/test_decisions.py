"""User decisions of 2026-09-23 ("alle empfehlungen … p3 180") in the recommended profiles.

The characterized 2026.09.1 profiles and the legacy module stay unchanged;
the decided rules live in the recommended 2026.09.2 profiles.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from auditcore_price_analysis import (
    ProfileError,
    ReleaseStatus,
    Tariff,
    calculate,
    group_statistics,
    legacy,
    load_calculation_profile,
    load_comparison_profile,
    load_recommended_calculation_profile,
    load_recommended_comparison_profile,
    recommended_version,
    select_tariff,
    standard_consumption,
    traffic_light,
)

NW = load_recommended_calculation_profile("regulierung.hpp.nahwaerme")
WA = load_recommended_calculation_profile("regulierung.hpp.wasser")
CP = load_recommended_comparison_profile("regulierung.hpp.vergleich")


def _decisions(profile: object) -> dict[str, dict[str, str]]:
    raw = profile.raw  # type: ignore[attr-defined]
    return {d["code"]: d for d in raw["decisions"]}


def test_recommended_versions_are_the_decided_profiles() -> None:
    for pid in ("regulierung.hpp.nahwaerme", "regulierung.hpp.wasser", "regulierung.hpp.vergleich"):
        assert recommended_version(pid) == "2026.09.2"
    for profile in (NW, WA, CP):
        assert profile.recommended and profile.status == "DECIDED"
        for decision in _decisions(profile).values():
            assert decision["status"] == "DECIDED" and decision["date"] == "2026-09-23"
            assert "p3 180" in decision["quote"]
    assert not load_calculation_profile("regulierung.hpp.wasser", "2026.09.1").recommended
    with pytest.raises(ProfileError):
        recommended_version("regulierung.hpp.unbekannt")


def test_pa_h01_optional_gap_stays_comparable_but_marked_incomplete() -> None:
    tariff = Tariff.from_mapping(
        {"grundpreis_eur_kw": "28.5", "arbeitspreis_ct_kwh": "10.82"}, NW, release="freigegeben"
    )
    result = calculate(tariff, NW, consumption=standard_consumption(NW), stichtag="2025-07-01")
    assert result.comparable and result.completeness == "unvollstaendig"
    assert result.to_dict()["vollstaendigkeit"] == "unvollstaendig"
    assert "PA-H01" in _decisions(NW)


def test_pa_h02_comparisons_are_exact() -> None:
    assert traffic_light(Decimal("1.1"), Decimal("1.0"), CP) == "gruen"
    assert traffic_light(Decimal("3.6"), Decimal("3.0"), CP) == "gelb"
    assert group_statistics([2.675, 2.675], CP).median == Decimal("2.68")
    assert "PA-H02" in _decisions(CP)


def test_pa_h03_water_standard_is_180_from_the_setting() -> None:
    standard = standard_consumption(WA)
    assert standard == {"q3": Decimal(4), "m3": Decimal(180)}
    rule = next(c for c in WA.consumption if c.name == "m3")
    assert "wasser_standard_m3" in (rule.standard_source or "")
    # legacy stays bit-exact: the old calculator default remains 150 m³
    assert legacy.calculate_wasser({"arbeitspreis_eur_m3": 1})["parameter"]["m3"] == 150.0
    with pytest.raises(ProfileError):
        standard_consumption(load_calculation_profile("regulierung.hpp.wasser", "2026.09.1"))


def test_pa_h04_valid_to_is_respected() -> None:
    rows = [
        Tariff(
            kind="wasser",
            components={},
            valid_from=date(2025, 1, 1),
            valid_to=date(2025, 3, 31),
            release=ReleaseStatus.FREIGEGEBEN,
            source_ref="alt",
        ),
        Tariff(
            kind="wasser",
            components={},
            valid_from=date(2024, 1, 1),
            release=ReleaseStatus.FREIGEGEBEN,
            source_ref="gueltig",
        ),
    ]
    selection = select_tariff(rows, stichtag="2025-06-01", profile=CP)
    assert selection.tariff is rows[1] and selection.excluded == ((0, "abgelaufen"),)
    old = load_comparison_profile("regulierung.hpp.vergleich", "2026.09.1")
    assert select_tariff(rows, stichtag="2025-06-01", profile=old).tariff is rows[0]


def test_levy_switch_date_stays_with_documented_research() -> None:
    (legal,) = NW.raw["legal_dates"]
    assert legal["date"] == "2025-07-01" and legal["status"] == "REVIEW_REQUIRED"
    assert "§ 35e EnWG" in legal["research"]["result"] and legal["research"]["sources"]
    assert NW.component("waermeumlagenpreis_ct_kwh").valid_from == date(2025, 7, 1)
