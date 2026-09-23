"""Historic EU thresholds 2014–2023 (profile procurement.hvtg 2026.09.3).

Every value is checked against the amending (delegated) regulation it was read
from; 2026.09.2 stays byte-identical (fingerprint) and keeps returning
REVIEW_REQUIRED before 2024.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from importlib import resources

import pytest

from auditcore_procurement import prechecks

HIST = prechecks.load_profile("procurement.hvtg", "2026.09.3")
OLD = prechecks.load_profile("procurement.hvtg", "2026.09.2")
SUPPLY, WORKS = "Liefer-/Dienstleistungen", "Bauleistungen"

#: (valid_from, valid_to, works, central, sub_central, CELEX, ABl.) read in the official text.
OFFICIAL = [
    (
        "2014-01-01",
        "2015-12-31",
        5186000,
        134000,
        207000,
        "32013R1336",
        "ABl. L 335 vom 14.12.2013, S. 17",
    ),
    (
        "2016-01-01",
        "2017-12-31",
        5225000,
        135000,
        209000,
        "32015R2170",
        "ABl. L 307 vom 25.11.2015, S. 5",
    ),
    (
        "2018-01-01",
        "2019-12-31",
        5548000,
        144000,
        221000,
        "32017R2365",
        "ABl. L 337 vom 19.12.2017, S. 19",
    ),
    (
        "2020-01-01",
        "2021-12-31",
        5350000,
        139000,
        214000,
        "32019R1828",
        "ABl. L 279 vom 31.10.2019, S. 25",
    ),
    (
        "2022-01-01",
        "2023-12-31",
        5382000,
        140000,
        215000,
        "32021R1952",
        "ABl. L 398 vom 11.11.2021, S. 23",
    ),
    (
        "2024-01-01",
        "2025-12-31",
        5538000,
        143000,
        221000,
        "32023R2495",
        "ABl. L, 2023/2495, 16.11.2023",
    ),
    (
        "2026-01-01",
        "2027-12-31",
        5404000,
        140000,
        216000,
        "32025R2152",
        "ABl. L, 2025/2152, 23.10.2025",
    ),
]
#: Released bytes of 2026.09.2 (tag v0.3.0) and its profile fingerprint.
OLD_SHA256 = "ac28af97a936319218029fe3dbc70f859ac08a75ca790f13622c3c38d8aa30fd"
OLD_FINGERPRINT = "fbb7f26e3e673df49d13a9ddb8a84ee15a8582103f9834dbe5b916e8a2cc084d"


def _raw(version: str) -> bytes:
    return (
        resources.files("auditcore_procurement.profiles")
        .joinpath(f"procurement.hvtg-{version}.json")
        .read_bytes()
    )


def test_every_period_matches_the_official_text_with_source() -> None:
    rows = [
        (
            p.valid_from.isoformat(),
            p.valid_to.isoformat(),
            p.values["works"],
            p.values["supplies_services_central"],
            p.values["supplies_services_sub_central"],
            p.source["celex"],
            p.source["official_journal"],
        )
        for p in HIST.eu_periods
    ]
    assert rows == OFFICIAL
    for period in HIST.eu_periods:
        source = period.source
        assert source["url"].startswith("https://eur-lex.europa.eu/")
        assert source["celex"] in source["url"] or source["celex"][1:5] in source["url"]
        assert source["retrieved_from"].endswith(source["celex"])
        assert len(source["retrieved_sha256"]) == 64
        assert source["applies_from"] == period.valid_from.isoformat()
        assert set(period.values) == {
            "works",
            "supplies_services_central",
            "supplies_services_sub_central",
        }


def test_periods_are_gapless_from_2014_to_2027() -> None:
    periods = HIST.eu_periods
    assert periods[0].valid_from == date(2014, 1, 1)
    assert periods[-1].valid_to == date(2027, 12, 31)
    for before, after in zip(periods, periods[1:], strict=False):
        assert (after.valid_from - before.valid_to).days == 1
    for year in range(2014, 2028):
        assert prechecks.eu_period_for_year(HIST, year).valid_from.year in (year, year - 1)


def test_2016_transition_has_both_directives_with_equal_values() -> None:
    period = prechecks.eu_period(HIST, date(2016, 2, 1))
    assert period.source["celex"] == "32015R2170"
    concurrent = period.source["concurrent_source"]
    assert concurrent["celex"] == "32015R2342" and "2004/18/EG" in concurrent["amends"]
    assert prechecks.eu_period(HIST, date(2016, 4, 18)) is period
    assert "2004/18/EG" in HIST.eu_periods[0].source["amends"]


@pytest.mark.parametrize(
    ("day", "value", "authority", "expected", "limit"),
    [
        (date(2014, 1, 1), "206999", "sub_central", "BELOW_EU", 207000),
        (date(2015, 12, 31), "207000", "sub_central", "ABOVE_EU", 207000),
        (date(2016, 1, 1), "208999", "sub_central", "BELOW_EU", 209000),
        (date(2017, 12, 31), "135000", "central", "ABOVE_EU", 135000),
        (date(2018, 1, 1), "220999.99", "sub_central", "BELOW_EU", 221000),
        (date(2019, 6, 30), "144000", "central", "ABOVE_EU", 144000),
        (date(2020, 1, 1), "214000", "sub_central", "ABOVE_EU", 214000),
        (date(2021, 12, 31), "138999", "central", "BELOW_EU", 139000),
        (date(2022, 1, 1), "215000", "sub_central", "ABOVE_EU", 215000),
        (date(2023, 12, 31), "214999", "sub_central", "BELOW_EU", 215000),
    ],
)
def test_historic_supply_boundaries(
    day: date, value: str, authority: str, expected: str, limit: int
) -> None:
    result = prechecks.check_threshold(
        HIST, Decimal(value), SUPPLY, None, "strict", reference_date=day, authority_type=authority
    )
    assert result["status"] == "PASS" and result["calculated_tier"] == expected
    assert result["eu_threshold"]["value"] == limit


@pytest.mark.parametrize(
    ("year", "value", "expected"),
    [(2014, "5186000", "ABOVE_EU"), (2019, "5547999", "BELOW_EU"), (2022, "5382000", "ABOVE_EU")],
)
def test_historic_works(year: int, value: str, expected: str) -> None:
    result = prechecks.check_threshold(HIST, Decimal(value), WORKS, None, "strict", year=year)
    assert result["calculated_tier"] == expected


@pytest.mark.parametrize(
    "kwargs", [{"year": 2013}, {"year": 2028}, {"reference_date": date(2013, 12, 31)}]
)
def test_outside_2014_2027_stays_review_required(kwargs: dict) -> None:
    result = prechecks.check_threshold(HIST, Decimal("100000"), SUPPLY, None, "strict", **kwargs)
    assert result["status"] == "REVIEW_REQUIRED" and "calculated_tier" not in result


def test_released_profile_2026_09_2_is_unchanged() -> None:
    assert hashlib.sha256(_raw("2026.09.2")).hexdigest() == OLD_SHA256
    assert OLD.fingerprint == OLD_FINGERPRINT
    assert [p.valid_from.year for p in OLD.eu_periods] == [2024, 2026]
    result = prechecks.check_threshold(OLD, Decimal("7000"), SUPPLY, None, "strict", year=2019)
    assert result["status"] == "REVIEW_REQUIRED"


def test_2024_to_2027_identical_in_both_versions() -> None:
    assert [(p.valid_from, p.valid_to, dict(p.values)) for p in HIST.eu_periods[-2:]] == [
        (p.valid_from, p.valid_to, dict(p.values)) for p in OLD.eu_periods
    ]
    for period in HIST.eu_periods[-2:]:
        assert period.source["rechecked_on"] == "2026-09-23"


def test_schema_does_not_invent_categories() -> None:
    raw = json.loads(_raw("2026.09.3"))
    assert "Konzessionen" in raw["eu_thresholds"]["not_entered"]
    assert HIST.fingerprint != OLD.fingerprint
