"""Corrected and explicit behavior of the new calculation contract (PA-L01 … PA-L16)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pytest

from auditcore_price_analysis import (
    PriceAnalysisError,
    ReleaseStatus,
    Tariff,
    calculate,
    load_calculation_profile,
    tiered_amount,
)
from auditcore_price_analysis.tariff import Tier

NW = load_calculation_profile("regulierung.hpp.nahwaerme", "2026.09.1")
WA = load_calculation_profile("regulierung.hpp.wasser", "2026.09.1")
NW_DATA = {
    "grundpreis_eur_kw": "28.50",
    "arbeitspreis_ct_kwh": "10.82",
    "verrechnungspreis_eur_jahr": "154.80",
    "emissionspreis_ct_kwh": "0.68",
    "umlagenpreis_ct_kwh": "0.39",
    "waermeumlagenpreis_ct_kwh": "0.54",
}
WA_DATA = {
    "grundpreis_eur_monat": "10.00",
    "arbeitspreis_staffel": [
        {"bis_m3": 50, "preis": "1.80"},
        {"bis_m3": 200, "preis": "2.20"},
        {"bis_m3": 500, "preis": "2.50"},
    ],
    "verrechnungspreis_eur_monat": "2.50",
    "wasserentnahmeentgelt_eur_m3": "0.15",
}


def nw(data: dict[str, Any] | None = None, **kwargs: Any) -> Any:
    tariff = Tariff.from_mapping(
        NW_DATA if data is None else data, NW, release=kwargs.pop("release", "freigegeben")
    )
    return calculate(
        tariff,
        NW,
        consumption=kwargs.pop("consumption", {"kw": 12, "kwh": 27000}),
        stichtag=kwargs.pop("stichtag", "2025-01-01"),
    )


def test_reference_values_and_levy_switch() -> None:
    before = nw(stichtag="2025-06-30")
    after = nw(stichtag="2025-07-01")
    assert before.total == Decimal("3707.1") and before.total_rounded == Decimal("3707.10")
    assert after.total_rounded == Decimal("3747.60")
    assert before.line("umlagenpreis_anteil").label == "gasspeicherumlage"
    assert after.line("umlagenpreis_anteil").label == "waermeumlagenpreis"
    assert after.profile["profile_id"] == "regulierung.hpp.nahwaerme"
    assert after.mixed_price == Decimal("13.88") and after.fixed_share_pct == Decimal("13.3")


def test_pa_l01_missing_consumption_is_an_error_not_zero() -> None:
    with pytest.raises(PriceAnalysisError) as error:
        nw(consumption={"kwh": 27000})
    assert error.value.code == "missing_value" and error.value.field == "kw"
    with pytest.raises(PriceAnalysisError, match="Unbekannte Verbrauchsgrößen"):
        nw(consumption={"kw": 12, "kwh": 1, "m3": 3})


def test_pa_l02_missing_optional_component_is_visible_lower_bound() -> None:
    data = {k: v for k, v in NW_DATA.items() if k != "emissionspreis_ct_kwh"}
    result = nw(data)
    assert result.missing_optional == ("emissionspreis_ct_kwh",)
    assert result.total_is_lower_bound and result.comparable  # PA-H01: Profil blockiert nicht
    assert result.line("emissionspreis_anteil").status == "fehlt"
    assert result.line("emissionspreis_anteil").amount is None


def test_pa_h01_profile_can_block_comparison_for_optional_gaps() -> None:
    from auditcore_price_analysis import calculation_profile_from_dict

    raw = dict(NW.raw)
    raw["missing"] = {"optional_missing_blocks_comparison": True}
    strict = calculation_profile_from_dict(raw)
    assert strict.fingerprint != NW.fingerprint
    data = {k: v for k, v in NW_DATA.items() if k != "emissionspreis_ct_kwh"}
    result = calculate(
        Tariff.from_mapping(data, strict, release="freigegeben"),
        strict,
        consumption={"kw": 12, "kwh": 27000},
        stichtag="2025-01-01",
    )
    assert not result.comparable
    assert result.not_comparable_reasons == ("fehlt:emissionspreis_ct_kwh",)


def test_missing_required_component_is_named_and_blocks_comparison() -> None:
    result = nw({"grundpreis_eur_kw": 25})
    assert result.missing_required == ("arbeitspreis_ct_kwh",)
    assert "fehlt:arbeitspreis_ct_kwh" in result.not_comparable_reasons
    assert not result.comparable and result.total_is_lower_bound


def test_explicit_zero_is_not_missing() -> None:
    result = nw({**NW_DATA, "verrechnungspreis_eur_jahr": 0})
    assert result.missing_optional == ()
    assert result.line("verrechnungspreis_anteil").amount_rounded == Decimal("0.00")


def test_release_status_is_reported_never_granted() -> None:
    for status in ("ausstehend", "abgelehnt", "unbekannt"):
        result = nw(release=status)
        assert result.release is ReleaseStatus(status)
        assert not result.comparable and f"freigabe:{status}" in result.not_comparable_reasons
    assert nw(release="freigegeben").comparable


def test_legacy_release_values_are_mapped() -> None:
    assert ReleaseStatus.from_legacy("approved") is ReleaseStatus.FREIGEGEBEN
    assert ReleaseStatus.from_legacy("pending") is ReleaseStatus.AUSSTEHEND
    assert ReleaseStatus.from_legacy("rejected") is ReleaseStatus.ABGELEHNT
    assert ReleaseStatus.from_legacy(None) is ReleaseStatus.UNBEKANNT
    assert ReleaseStatus.from_legacy("APPROVED") is ReleaseStatus.UNBEKANNT


def test_tariff_validity_window_is_checked() -> None:
    tariff = Tariff.from_mapping(
        NW_DATA, NW, release="freigegeben", valid_from="2025-02-01", valid_to="2025-12-31"
    )
    early = calculate(tariff, NW, consumption={"kw": 12, "kwh": 1}, stichtag="2025-01-31")
    late = calculate(tariff, NW, consumption={"kw": 12, "kwh": 1}, stichtag="2026-01-01")
    inside = calculate(tariff, NW, consumption={"kw": 12, "kwh": 1}, stichtag="2025-12-31")
    assert early.not_comparable_reasons == ("noch_nicht_gueltig",)
    assert late.not_comparable_reasons == ("nicht_mehr_gueltig",)
    assert inside.comparable


def test_pa_l03_tier_without_price_is_an_error() -> None:
    with pytest.raises(PriceAnalysisError) as error:
        Tariff.from_mapping({"arbeitspreis_staffel": [{"bis_m3": 50, "preis": None}]}, WA)
    assert error.value.code == "missing_value"


def test_pa_l04_open_last_tier_is_accepted_only_last() -> None:
    tariff = Tariff.from_mapping(
        {**WA_DATA, "arbeitspreis_staffel": [{"bis_m3": 50, "preis": 1.5}, {"preis": 2}]}, WA
    )
    assert tariff.tiers == (Tier(Decimal(50), Decimal("1.5")), Tier(None, Decimal(2)))
    result = calculate(tariff, WA, consumption={"q3": 4, "m3": 150}, stichtag="2025-01-01")
    assert result.line("arbeitspreis_anteil").amount == Decimal("275.0")
    with pytest.raises(PriceAnalysisError, match="nur die letzte Stufe"):
        Tariff.from_mapping({"arbeitspreis_staffel": [{"preis": 1}, {"preis": 2}]}, WA)


@pytest.mark.parametrize(
    "shape", [{"stufen": []}, {}, "50:1.8", 7, {"staffeln": [], "x": 1}, [["50", "1.8"]], ["50"]]
)
def test_pa_l05_unknown_tier_shapes_are_errors(shape: Any) -> None:
    with pytest.raises(PriceAnalysisError) as error:
        Tariff.from_mapping({**WA_DATA, "arbeitspreis_staffel": shape}, WA)
    assert error.value.code == "invalid_tiers"


def test_pa_l06_tier_supersedes_single_price_visibly() -> None:
    tariff = Tariff.from_mapping({**WA_DATA, "arbeitspreis_eur_m3": "9.99"}, WA)
    result = calculate(tariff, WA, consumption={"q3": 4, "m3": 150}, stichtag="2025-01-01")
    assert result.line("arbeitspreis_anteil").status == "gestaffelt"
    assert result.line("arbeitspreis_anteil").amount == Decimal("310.00")
    assert any("überlagert" in issue for issue in result.issues)


def test_pa_l07_last_tier_open_by_profile_and_reported() -> None:
    tariff = Tariff.from_mapping(WA_DATA, WA)
    result = calculate(tariff, WA, consumption={"q3": 4, "m3": 750}, stichtag="2025-01-01")
    uses = result.line("arbeitspreis_anteil").tiers
    assert [u.quantity for u in uses] == [Decimal(50), Decimal(150), Decimal(550)]
    assert any("letzten Staffelgrenze" in issue for issue in result.issues)
    with pytest.raises(PriceAnalysisError) as error:
        tiered_amount(tariff.tiers or (), Decimal(750), open_last=False)
    assert error.value.code == "beyond_last_tier"


@pytest.mark.parametrize(
    ("m3", "expected"),
    [(0, "0"), (50, "90.00"), ("50.001", "90.00220"), (200, "420.00"), (500, "1170.00")],
)
def test_tier_boundaries(m3: Any, expected: str) -> None:
    tariff = Tariff.from_mapping(WA_DATA, WA)
    result = calculate(tariff, WA, consumption={"q3": 4, "m3": m3}, stichtag="2025-01-01")
    assert result.line("arbeitspreis_anteil").amount == Decimal(expected)


def test_extra_tier_keys_are_reported_not_used() -> None:
    raw = [{"bis_m3": 50, "preis": 1, "hinweis": "x"}, {"bis_m3": 100, "preis": 2}]
    tariff = Tariff.from_mapping({**WA_DATA, "arbeitspreis_staffel": raw}, WA)
    result = calculate(tariff, WA, consumption={"q3": 4, "m3": 10}, stichtag="2025-01-01")
    assert "arbeitspreis_staffel: Angabe hinweis nicht ausgewertet" in result.issues


def test_pa_l08_undefined_ratios_are_none() -> None:
    zero = nw(consumption={"kw": 12, "kwh": 0})
    assert zero.mixed_price is None and zero.fixed_share_pct == Decimal("100.0")
    empty = nw({}, consumption={"kw": 0, "kwh": 0})
    assert empty.total == 0 and empty.fixed_share_pct is None and empty.variable_share_pct is None


@pytest.mark.parametrize(
    "day", [datetime(2025, 7, 1, 12), "01.07.2025", "2025-07-01T00:00", None, 20250701]
)
def test_pa_l09_reference_day_must_be_a_calendar_day(day: Any) -> None:
    with pytest.raises(PriceAnalysisError) as error:
        nw(stichtag=day)
    assert error.value.code == "invalid_date"


def test_pa_l10_rounding_per_line_and_exact_total() -> None:
    result = nw(
        {"grundpreis_eur_kw": 1, "arbeitspreis_ct_kwh": 1, "verrechnungspreis_eur_jahr": 1},
        consumption={"kw": 1, "kwh": 3},
    )
    assert result.total == Decimal("2.03")
    assert result.mixed_price == Decimal("67.67")
    half = nw(
        {"grundpreis_eur_kw": 0, "arbeitspreis_ct_kwh": "1.005", "verrechnungspreis_eur_jahr": 0},
        consumption={"kw": 0, "kwh": 100},
    )
    assert half.total == Decimal("1.00500") and half.total_rounded == Decimal("1.01")


def test_pa_l14_inactive_regime_component_is_still_validated() -> None:
    with pytest.raises(PriceAnalysisError) as error:
        nw({**NW_DATA, "waermeumlagenpreis_ct_kwh": "-0.1"}, stichtag="2025-01-01")
    assert error.value.code == "negative"


@pytest.mark.parametrize("value", ["1e2", "10,82", "", "abc", True, float("nan"), [1]])
def test_pa_l15_numbers_are_strict(value: Any) -> None:
    with pytest.raises(PriceAnalysisError) as error:
        nw({**NW_DATA, "arbeitspreis_ct_kwh": value})
    assert error.value.code == "invalid_number"


def test_pa_l16_unknown_component_is_rejected() -> None:
    with pytest.raises(PriceAnalysisError) as error:
        nw({**NW_DATA, "arbeitsprais_ct_kwh": 1})
    assert error.value.code == "unknown_component"


def test_profile_kind_must_match() -> None:
    tariff = Tariff.from_mapping(WA_DATA, WA)
    with pytest.raises(PriceAnalysisError) as error:
        calculate(tariff, NW, consumption={"kw": 1, "kwh": 1}, stichtag=date(2025, 1, 1))
    assert error.value.code == "profile_mismatch"


def test_result_is_json_serializable_without_precision_loss() -> None:
    import json

    data = nw().to_dict()
    text = json.dumps(data, ensure_ascii=False)
    assert Decimal(json.loads(text)["total"]) == Decimal("3707.1")
    assert data["total_rounded"] == "3707.10" and data["lines"][1]["amount"] == "2921.4000"
    assert data["profile"]["fingerprint"] == NW.fingerprint
