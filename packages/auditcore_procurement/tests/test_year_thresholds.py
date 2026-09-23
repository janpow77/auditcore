"""Year-bound EU thresholds (profile procurement.hvtg 2026.09.2), P-C10…P-C12."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from importlib import resources

import pytest
from conftest import LEGACY, normalise, revive

from auditcore_procurement import prechecks

HVTG = prechecks.load_profile("procurement.hvtg", "2026.09.2")
LEGACY_PROFILE = prechecks.load_profile("procurement.hvtg-legacy", "2026.09.1")
SUPPLY, WORKS = "Liefer-/Dienstleistungen", "Bauleistungen"


def tier(value: str, service: str = SUPPLY, **kwargs: object) -> dict:
    return prechecks.check_threshold(HVTG, Decimal(value), service, None, "strict", **kwargs)


def test_only_verified_periods_with_sources_are_entered() -> None:
    rows = [
        (p.valid_from.isoformat(), p.valid_to.isoformat(), dict(p.values)) for p in HVTG.eu_periods
    ]
    assert rows == [
        (
            "2024-01-01",
            "2025-12-31",
            {
                "works": 5538000,
                "supplies_services_central": 143000,
                "supplies_services_sub_central": 221000,
            },
        ),
        (
            "2026-01-01",
            "2027-12-31",
            {
                "works": 5404000,
                "supplies_services_central": 140000,
                "supplies_services_sub_central": 216000,
            },
        ),
    ]
    assert [p.source["regulation"][:39] for p in HVTG.eu_periods] == [
        "Delegierte Verordnung (EU) 2023/2495 de",
        "Delegierte Verordnung (EU) 2025/2152 de",
    ]
    assert all(p.source["url"].startswith("https://eur-lex.europa.eu/") for p in HVTG.eu_periods)
    assert HVTG.national_status == "REVIEW_REQUIRED"
    assert HVTG.national_tiers == ("BELOW_1K", "BELOW_25K")


@pytest.mark.parametrize(
    ("day", "value", "expected"),
    [
        (date(2025, 12, 31), "220999", "BELOW_EU"),
        (date(2025, 12, 31), "221000", "ABOVE_EU"),
        (date(2026, 1, 1), "215999", "BELOW_EU"),
        (date(2026, 1, 1), "216000", "ABOVE_EU"),
        (date(2026, 1, 1), "220000", "ABOVE_EU"),
        (date(2024, 1, 1), "220000", "BELOW_EU"),
    ],
)
def test_year_boundaries_sub_central(day: date, value: str, expected: str) -> None:
    result = tier(value, reference_date=day, authority_type="sub_central")
    assert result["status"] == "PASS" and result["calculated_tier"] == expected


@pytest.mark.parametrize(
    ("day", "value", "expected", "limit"),
    [
        (date(2025, 12, 31), "5537999", "BELOW_EU", 5538000),
        (date(2025, 12, 31), "5538000", "ABOVE_EU", 5538000),
        (date(2026, 1, 1), "5404000", "ABOVE_EU", 5404000),
        (date(2026, 1, 1), "5403999.99", "BELOW_EU", 5404000),
    ],
)
def test_year_boundaries_works(day: date, value: str, expected: str, limit: int) -> None:
    result = tier(value, WORKS, reference_date=day)
    assert result["calculated_tier"] == expected and result["eu_threshold"]["value"] == limit


def test_central_authorities_and_explicit_year() -> None:
    assert tier("141000", year=2026, authority_type="central")["calculated_tier"] == "ABOVE_EU"
    assert tier("141000", year=2024, authority_type="central")["calculated_tier"] == "BELOW_EU"
    unknown = tier("141000", year=2026)
    assert unknown["status"] == "REVIEW_REQUIRED" and "authority_type" in unknown["message"]
    assert tier("139000", year=2026)["calculated_tier"] == "BELOW_EU"
    assert tier("216000", year=2026)["calculated_tier"] == "ABOVE_EU"
    with pytest.raises(ValueError):
        tier("1", year=2026, authority_type="bund")


@pytest.mark.parametrize(
    "kwargs", [{"year": 2023}, {"year": 2028}, {"reference_date": date(2023, 12, 31)}, {}]
)
def test_missing_period_is_review_required_without_fallback(kwargs: dict) -> None:
    result = tier("100000", **kwargs)
    assert result["status"] == "REVIEW_REQUIRED" and "calculated_tier" not in result
    report = prechecks.run_prechecks(
        HVTG, Decimal("100000"), None, None, SUPPLY, None, None, [], mode="strict", **kwargs
    )
    assert report["overall_status"] == "REVIEW_REQUIRED"


def test_lookup_functions_raise_clear_errors() -> None:
    with pytest.raises(prechecks.ThresholdUnavailable, match="31.12.2023"):
        prechecks.eu_period(HVTG, date(2023, 12, 31))
    with pytest.raises(prechecks.ThresholdUnavailable, match="keine jahresbezogenen"):
        prechecks.eu_period(LEGACY_PROFILE, date(2026, 1, 1))
    period = prechecks.eu_period_for_year(HVTG, 2027)
    assert prechecks.eu_threshold(HVTG, "construction", period, "sub_central").value == 5404000


def test_national_tiers_stay_application_rules() -> None:
    result = tier("25000", year=2026, authority_type="sub_central")
    assert result["calculated_tier"] == "BELOW_25K"
    assert result["national_tiers_status"] == "REVIEW_REQUIRED"
    assert tier("1000", year=2026)["calculated_tier"] == "BELOW_1K"


def test_schema1_profile_in_strict_mode_is_review_required() -> None:
    result = prechecks.check_threshold(
        LEGACY_PROFILE, Decimal("5"), SUPPLY, None, "strict", year=2026
    )
    assert result["status"] == "REVIEW_REQUIRED"


@pytest.mark.parametrize("case", LEGACY["prechecks"], ids=[c["name"] for c in LEGACY["prechecks"]])
def test_legacy_mode_is_unchanged_with_new_profile_and_ignores_dates(case: dict) -> None:
    result = prechecks.run_prechecks(
        HVTG,
        *revive(case["args"]),
        mode="legacy",
        reference_date=date(2026, 6, 1),
        authority_type="central",
    )
    result["timestamp"] = "<wall-clock>"
    assert normalise(result) == case["output"]


def test_profile_from_ruleset_year_bound_and_legacy() -> None:
    rules = LEGACY["ruleset"]
    plain = prechecks.profile_from_ruleset(rules, profile_id="app", version="1", source={})
    assert plain.eu_periods == ()
    bound = prechecks.profile_from_ruleset(
        rules, profile_id="app", version="1", source={}, year_bound=True
    )
    assert bound.eu_periods == HVTG.eu_periods and bound.tiers == HVTG.tiers
    result = prechecks.check_threshold(
        bound,
        Decimal("218000"),
        SUPPLY,
        None,
        "strict",
        reference_date=date(2026, 3, 1),
        authority_type="sub_central",
    )
    assert result["calculated_tier"] == "ABOVE_EU"
    legacy = prechecks.check_threshold(bound, Decimal("218000"), SUPPLY, None, "legacy")
    assert legacy["calculated_tier"] == "BELOW_EU"  # source table 221.000 unchanged


def test_profile_validation_of_year_table() -> None:
    raw = json.loads(
        resources.files("auditcore_procurement.profiles")
        .joinpath("procurement.hvtg-2026.09.2.json")
        .read_text(encoding="utf-8")
    )
    broken = json.loads(json.dumps(raw))
    broken["eu_thresholds"]["periods"][1]["valid_from"] = "2025-06-01"
    with pytest.raises(prechecks.ProfileError, match="überschneiden"):
        prechecks.profile_from_dict(broken)
    broken = json.loads(json.dumps(raw))
    broken["eu_thresholds"]["periods"][0]["source"]["url"] = ""
    with pytest.raises(prechecks.ProfileError, match="Fundstelle"):
        prechecks.profile_from_dict(broken)
    broken = json.loads(json.dumps(raw))
    broken["national_tiers"]["tiers"] = ["BELOW_5K"]
    with pytest.raises(prechecks.ProfileError):
        prechecks.profile_from_dict(broken)
