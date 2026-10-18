"""EU thresholds of all regimes (profile procurement.hvtg 2026.10.1, schema 3).

The reference table below was typed from the operative articles of the amending
regulations and of the directives (official German texts, Publications Office,
retrieved 13.10.2026), independently of the profile builder. Every value is
tested at the threshold and one cent below, on the first and the last day of
its validity.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import date, timedelta
from decimal import Decimal
from importlib import resources
from pathlib import Path

import pytest
from conftest import LEGACY

import auditcore_procurement
from auditcore_procurement import prechecks
from auditcore_procurement.eu_regimes import RegimeError, parse_regimes, spaced_amount

NEW = prechecks.load_profile("procurement.hvtg", "2026.10.1")
PREVIOUS = prechecks.load_profile("procurement.hvtg", "2026.09.3")
TOOLS = Path(__file__).resolve().parents[1] / "tools"

P14, P16, P18 = (
    ("2014-01-01", "2015-12-31"),
    ("2016-01-01", "2017-12-31"),
    ("2018-01-01", "2019-12-31"),
)
P16A, P16B = ("2016-01-01", "2016-04-17"), ("2016-04-18", "2017-12-31")
P20, P22 = ("2020-01-01", "2021-12-31"), ("2022-01-01", "2023-12-31")
P24, P26 = ("2024-01-01", "2025-12-31"), ("2026-01-01", "2027-12-31")
SINCE_2016 = ("2016-04-18", "2027-12-31")

#: (regime, contract type, authority type) -> [(period, EUR, CELEX of the text read)]
OFFICIAL: dict[tuple[str, str, str | None], list[tuple[tuple[str, str], int, str]]] = {
    ("public_contracts", "works", None): [
        (P14, 5186000, "32013R1336"),
        (P16A, 5225000, "32015R2342"),
        (P16B, 5225000, "32015R2170"),
        (P18, 5548000, "32017R2365"),
        (P20, 5350000, "32019R1828"),
        (P22, 5382000, "32021R1952"),
        (P24, 5538000, "32023R2495"),
        (P26, 5404000, "32025R2152"),
    ],
    ("public_contracts", "supplies_services", "central"): [
        (P14, 134000, "32013R1336"),
        (P16A, 135000, "32015R2342"),
        (P16B, 135000, "32015R2170"),
        (P18, 144000, "32017R2365"),
        (P20, 139000, "32019R1828"),
        (P22, 140000, "32021R1952"),
        (P24, 143000, "32023R2495"),
        (P26, 140000, "32025R2152"),
    ],
    ("public_contracts", "supplies_services", "sub_central"): [
        (P14, 207000, "32013R1336"),
        (P16A, 209000, "32015R2342"),
        (P16B, 209000, "32015R2170"),
        (P18, 221000, "32017R2365"),
        (P20, 214000, "32019R1828"),
        (P22, 215000, "32021R1952"),
        (P24, 221000, "32023R2495"),
        (P26, 216000, "32025R2152"),
    ],
    ("public_contracts", "social_services", None): [(SINCE_2016, 750000, "32014L0024")],
    ("utilities", "works", None): [
        (P14, 5186000, "32013R1336"),
        (P16A, 5225000, "32015R2341"),
        (P16B, 5225000, "32015R2171"),
        (P18, 5548000, "32017R2364"),
        (P20, 5350000, "32019R1829"),
        (P22, 5382000, "32021R1953"),
        (P24, 5538000, "32023R2496"),
        (P26, 5404000, "32025R2150"),
    ],
    ("utilities", "supplies_services", None): [
        (P14, 414000, "32013R1336"),
        (P16A, 418000, "32015R2341"),
        (P16B, 418000, "32015R2171"),
        (P18, 443000, "32017R2364"),
        (P20, 428000, "32019R1829"),
        (P22, 431000, "32021R1953"),
        (P24, 443000, "32023R2496"),
        (P26, 432000, "32025R2150"),
    ],
    ("utilities", "social_services", None): [(SINCE_2016, 1000000, "32014L0025")],
    ("concessions", "concession", None): [
        (P16B, 5225000, "32015R2172"),
        (P18, 5548000, "32017R2366"),
        (P20, 5350000, "32019R1827"),
        (P22, 5382000, "32021R1951"),
        (P24, 5538000, "32023R2497"),
        (P26, 5404000, "32025R2151"),
    ],
    ("defence", "works", None): [
        (P14, 5186000, "32013R1336"),
        (P16, 5225000, "32015R2340"),
        (P18, 5548000, "32017R2367"),
        (P20, 5350000, "32019R1830"),
        (P22, 5382000, "32021R1950"),
        (P24, 5538000, "32023R2510"),
        (P26, 5404000, "32025R2487"),
    ],
    ("defence", "supplies_services", None): [
        (P14, 414000, "32013R1336"),
        (P16, 418000, "32015R2340"),
        (P18, 443000, "32017R2367"),
        (P20, 428000, "32019R1830"),
        (P22, 431000, "32021R1950"),
        (P24, 443000, "32023R2510"),
        (P26, 432000, "32025R2487"),
    ],
}
CASES = [
    (regime, kind, authority, day, value, celex)
    for (regime, kind, authority), rows in OFFICIAL.items()
    for period, value, celex in rows
    for day in period
]
#: Released bytes and fingerprint of 2026.09.3 and consumer fingerprints before this change.
PREVIOUS_SHA256 = "d8378ae85c90ab17331b25ba0c3563a4351a029d594ddff61b86b90fc6d3dbb2"
PREVIOUS_FINGERPRINT = "04b7464ff17c7c3bde20e9dba3a995eec63324447bbeda6b4e4975f37890160f"
RULESET_FINGERPRINTS = {
    "2026.09.3": "cba9088791bc3bf20c29af23e9c3dd3441c7ef8c081e947d3a57b750d8eebbfc",
    "2026.09.2": "744488924db8b36da3648c330b57bf5f0263c108ab44061e1ea2ab3fcb8c2e0a",
}


def _raw(version: str) -> bytes:
    return (
        resources.files("auditcore_procurement.profiles")
        .joinpath(f"procurement.hvtg-{version}.json")
        .read_bytes()
    )


def _check(
    value: str, regime: str, kind: str, authority: str | None = None, **when: object
) -> dict:
    return auditcore_procurement.check_eu_threshold(
        NEW, Decimal(value), regime=regime, contract_type=kind, authority_type=authority, **when
    )


def _series(catalogue: dict, regime: str, kind: str, authority: str | None) -> dict:
    found = next(r for r in catalogue["regimes"] if r["id"] == regime)
    contract_type = next(c for c in found["contract_types"] if c["id"] == kind)
    if authority is None:
        return contract_type
    return next(a for a in contract_type["authority_types"] if a["id"] == authority)


def test_catalogue_matches_the_official_reference_table() -> None:
    catalogue = auditcore_procurement.eu_catalogue(NEW)
    entered = {
        (regime["id"], kind["id"], None if series is kind else series["id"]): [
            ((row["valid_from"], row["valid_to"]), row["value"], row["source"])
            for row in series["thresholds"]
        ]
        for regime in catalogue["regimes"]
        for kind in regime["contract_types"]
        for series in (kind["authority_types"] or [kind])
    }
    assert entered == OFFICIAL
    assert catalogue["profile"] == NEW.reference
    assert catalogue["comparison"] == "reached_or_exceeded"


@pytest.mark.parametrize(
    ("regime", "kind", "authority", "day", "value", "celex"),
    CASES,
    ids=[f"{c[0]}-{c[1]}-{c[2] or 'all'}-{c[3]}" for c in CASES],
)
def test_threshold_and_one_cent_below_on_period_boundaries(
    regime: str, kind: str, authority: str | None, day: str, value: int, celex: str
) -> None:
    on = date.fromisoformat(day)
    reached = _check(str(value), regime, kind, authority, reference_date=on)
    below = _check(
        str(Decimal(value) - Decimal("0.01")), regime, kind, authority, reference_date=on
    )
    assert reached["status"] == below["status"] == "PASS"
    assert reached["above_threshold"] is True and below["above_threshold"] is False
    threshold = reached["eu_threshold"]
    assert (threshold["value"], threshold["celex"]) == (value, celex)
    assert (threshold["regime"], threshold["contract_type"]) == (regime, kind)
    assert threshold["authority_type"] == authority
    assert threshold["valid_from"] <= day <= threshold["valid_to"]
    assert below["eu_threshold"] == threshold


def test_values_change_exactly_at_the_turn_of_the_year() -> None:
    assert _check("431000", "utilities", "supplies_services", reference_date=date(2023, 12, 31))[
        "above_threshold"
    ]
    assert not _check("431000", "utilities", "supplies_services", reference_date=date(2024, 1, 1))[
        "above_threshold"
    ]
    old = _check("5404000", "concessions", "concession", reference_date=date(2025, 12, 31))
    new = _check("5404000", "concessions", "concession", reference_date=date(2026, 1, 1))
    assert (old["eu_threshold"]["value"], old["above_threshold"]) == (5538000, False)
    assert (new["eu_threshold"]["value"], new["above_threshold"]) == (5404000, True)


def test_rows_are_gapless_within_their_recorded_range() -> None:
    for (regime, kind, authority), rows in OFFICIAL.items():
        for (_, before_end), (after_start, _) in zip(
            [r[0] for r in rows], [r[0] for r in rows][1:], strict=False
        ):
            gap = date.fromisoformat(after_start) - date.fromisoformat(before_end)
            assert gap == timedelta(days=1), (regime, kind, authority)
        assert rows[-1][0][1] == "2027-12-31"


@pytest.mark.parametrize(
    ("regime", "kind", "authority", "when"),
    [
        ("public_contracts", "works", None, {"reference_date": date(2013, 12, 31)}),
        ("utilities", "supplies_services", None, {"reference_date": date(2028, 1, 1)}),
        ("defence", "works", None, {"year": 2013}),
        ("defence", "supplies_services", None, {"year": 2028}),
        ("concessions", "concession", None, {"reference_date": date(2016, 4, 17)}),
        ("concessions", "concession", None, {"year": 2016}),
        ("public_contracts", "social_services", None, {"reference_date": date(2016, 4, 17)}),
        ("utilities", "social_services", None, {"year": 2015}),
        ("public_contracts", "supplies_services", "central", {"reference_date": date(2030, 6, 1)}),
        ("public_contracts", "works", None, {}),
    ],
)
def test_unrecorded_period_is_not_recorded_never_a_neighbouring_value(
    regime: str, kind: str, authority: str | None, when: dict
) -> None:
    result = _check("1000000", regime, kind, authority, **when)
    assert result["status"] == "REVIEW_REQUIRED"
    assert "above_threshold" not in result and "eu_threshold" not in result
    assert ("hinterlegt" in result["message"]) or ("Stichtag fehlt" in result["message"])


def test_year_resolves_only_if_one_value_holds_the_whole_year() -> None:
    works = _check("5225000", "public_contracts", "works", year=2016)
    assert works["above_threshold"] is True
    assert works["eu_threshold"]["celex"] == "32015R2170"  # row of 31.12.; same value before
    assert _check("1", "public_contracts", "social_services", year=2016)["status"] == (
        "REVIEW_REQUIRED"
    )
    assert _check("750000", "public_contracts", "social_services", year=2017)["above_threshold"]
    assert (
        _check("431999.99", "defence", "supplies_services", year=2027)["above_threshold"] is False
    )


def test_authority_type_decides_only_where_the_directive_distinguishes() -> None:
    day = {"reference_date": date(2026, 6, 1)}
    kind = ("public_contracts", "supplies_services")
    assert _check("140000", *kind, "central", **day)["above_threshold"] is True
    assert _check("140000", *kind, "sub_central", **day)["above_threshold"] is False
    between = _check("140000", *kind, **day)
    assert between["status"] == "REVIEW_REQUIRED" and "authority_type" in between["message"]
    assert [t["value"] for t in between["eu_thresholds"]] == [140000, 216000]
    assert _check("139999.99", *kind, **day)["above_threshold"] is False
    assert _check("216000", *kind, **day)["eu_threshold"]["authority_type"] == "sub_central"
    with pytest.raises(ValueError, match="authority_type"):
        _check("1", *kind, "federal", **day)
    with pytest.raises(ValueError, match="authority_type"):
        auditcore_procurement.eu_regime_threshold(NEW, *kind, date(2026, 6, 1))
    # Utilities, concessions and defence have one value for all buyers.
    assert _check("432000", "utilities", "supplies_services", "central", **day)["above_threshold"]


def test_unknown_regime_or_contract_type_is_an_error_not_a_result() -> None:
    with pytest.raises(ValueError, match="regime"):
        _check("1", "railways", "works", reference_date=date(2026, 1, 1))
    with pytest.raises(ValueError, match="contract_type"):
        _check("1", "concessions", "works", reference_date=date(2026, 1, 1))
    with pytest.raises(ValueError, match="contract_type"):
        _check("1", "defence", "social_services")


def test_lookup_returns_the_threshold_with_its_source() -> None:
    found = auditcore_procurement.eu_regime_threshold(
        NEW, "utilities", "social_services", date(2020, 5, 5)
    )
    assert found.value == 1000000 and found.source["celex"] == "32014L0025"
    assert "1 000 000 EUR bei Dienstleistungsaufträgen betreffend soziale" in found.source["quote"]
    with pytest.raises(prechecks.ThresholdUnavailable, match="hinterlegt"):
        auditcore_procurement.eu_regime_threshold(NEW, "defence", "works", date(2028, 1, 1))


def test_every_value_stands_in_the_quoted_official_wording() -> None:
    catalogue = auditcore_procurement.eu_catalogue(NEW)
    sources = catalogue["sources"]
    used = set()
    for (regime, kind, authority), rows in OFFICIAL.items():
        series = _series(catalogue, regime, kind, authority)
        for row, (_, value, celex) in zip(series["thresholds"], rows, strict=True):
            source = sources[celex]
            used.add(celex)
            assert spaced_amount(value) in source["quote"]
            assert source["retrieved_from"].endswith(celex) and celex in source["url"]
            assert len(source["retrieved_sha256"]) == 64 and source["retrieved_on"] == "2026-10-13"
            assert source["applies_from"] <= row["valid_from"]
            assert row["provision"] and series["legal_basis"]
    assert used == set(sources)
    assert "„414 000 EUR“ durch „418 000 EUR“" in sources["32015R2171"]["quote"]
    assert (
        "d) 750 000 EUR bei öffentlichen Dienstleistungsaufträgen"
        in (sources["32014L0024"]["quote"])
    )


def test_catalogue_has_german_and_english_terms_and_no_national_rules() -> None:
    catalogue = auditcore_procurement.eu_catalogue(NEW)
    labels = {
        (r["id"], c["id"]): (c["label"]["de"], c["label"]["en"])
        for r in catalogue["regimes"]
        for c in r["contract_types"]
    }
    assert labels["public_contracts", "social_services"] == (
        "Soziale und andere besondere Dienstleistungen (Anhang XIV)",
        "Social and other specific services (Annex XIV)",
    )
    assert labels["concessions", "concession"][0] == "Bau- und Dienstleistungskonzessionen"
    supplies = _series(catalogue, "public_contracts", "supplies_services", None)
    assert [(a["label"]["de"], a["label"]["en"]) for a in supplies["authority_types"]] == [
        ("zentrale Regierungsbehörden", "central government authorities"),
        ("subzentrale öffentliche Auftraggeber", "sub-central contracting authorities"),
    ]
    assert (
        "thresholds" not in supplies
        and "Anhang III" in supplies["authority_types"][0]["note"]["de"]
    )
    buyers = {r["id"]: r["buyer"]["de"] for r in catalogue["regimes"]}
    assert buyers["concessions"].startswith("Konzessionsgeber")
    assert "Auftraggeber" in buyers["utilities"]
    assert [r["national_reference"] for r in catalogue["regimes"]] == [
        "§ 106 Abs. 2 Nr. 1 GWB",
        "§ 106 Abs. 2 Nr. 2 GWB",
        "§ 106 Abs. 2 Nr. 4 GWB",
        "§ 106 Abs. 2 Nr. 3 GWB",
    ]
    text = json.dumps(
        [catalogue, _check("300000", "utilities", "works", reference_date=date(2020, 1, 1))],
        ensure_ascii=False,
    )
    for national in ("BELOW_1K", "BELOW_25K", "Direktvergabe", "calculated_tier", "min_bids"):
        assert national not in text
    assert json.loads(json.dumps(catalogue)) == catalogue


def test_check_threshold_accepts_a_regime_and_keeps_the_national_part_out() -> None:
    direct = _check("5404000", "concessions", "concession", reference_date=date(2026, 3, 1))
    routed = prechecks.check_threshold(
        NEW,
        Decimal("5404000"),
        "",
        None,
        "strict",
        reference_date=date(2026, 3, 1),
        regime="concessions",
        contract_type="concession",
    )
    assert routed == direct and routed["check_id"] == "precheck_eu_threshold"
    missing = prechecks.check_threshold(
        NEW, None, "", None, "strict", regime="defence", contract_type="works"
    )
    assert missing["status"] == "WARNING"
    for kwargs in (
        {"mode": "strict", "regime": "defence"},
        {"mode": "strict", "contract_type": "works"},
        {"mode": "legacy", "regime": "defence", "contract_type": "works"},
        {"mode": "strict", "regime": "defence", "contract_type": "works", "tier": "ABOVE_EU"},
    ):
        mode, tier = kwargs.pop("mode"), kwargs.pop("tier", None)
        with pytest.raises(ValueError, match="regime und contract_type"):
            prechecks.check_threshold(NEW, Decimal("1"), "", tier, mode, year=2026, **kwargs)


def test_released_profile_2026_09_3_and_pinned_consumers_are_unchanged() -> None:
    assert hashlib.sha256(_raw("2026.09.3")).hexdigest() == PREVIOUS_SHA256
    assert PREVIOUS.fingerprint == PREVIOUS_FINGERPRINT and PREVIOUS.eu_regimes is None
    for version, fingerprint in RULESET_FINGERPRINTS.items():
        bound = prechecks.profile_from_ruleset(
            LEGACY["ruleset"],
            profile_id="app",
            version="1",
            source={},
            year_bound=True,
            eu_version=version,
        )
        assert bound.fingerprint == fingerprint and bound.eu_regimes is None
    current = prechecks.profile_from_ruleset(
        LEGACY["ruleset"], profile_id="app", version="1", source={}, year_bound=True
    )
    assert current.eu_regimes == NEW.eu_regimes and current.eu_periods == PREVIOUS.eu_periods
    old = auditcore_procurement.check_eu_threshold(
        PREVIOUS, Decimal("1"), regime="utilities", contract_type="works", year=2020
    )
    assert old["status"] == "REVIEW_REQUIRED" and "2026.10.1" in old["message"]
    with pytest.raises(prechecks.ThresholdUnavailable):
        auditcore_procurement.eu_catalogue(PREVIOUS)


@pytest.mark.parametrize("mode", ["strict", "legacy"])
def test_existing_calls_give_the_same_result_with_the_new_profile(mode: str) -> None:
    assert NEW.eu_periods == PREVIOUS.eu_periods and NEW.eu_categories == PREVIOUS.eu_categories
    assert (NEW.tiers, NEW.required_documents) == (PREVIOUS.tiers, PREVIOUS.required_documents)
    values = (
        "0",
        "999",
        "25000",
        "134000",
        "206999.99",
        "207000",
        "216000",
        "5403999.99",
        "5404000",
    )
    for service in ("Liefer-/Dienstleistungen", "Bauleistungen"):
        for value in values:
            for authority in (None, "central", "sub_central"):
                for when in ({"year": 2013}, {"year": 2015}, {"reference_date": date(2026, 1, 1)}):
                    args = (Decimal(value), service, None, mode)
                    kwargs = {"authority_type": authority, **when}
                    new = prechecks.check_threshold(NEW, *args, **kwargs)
                    old = prechecks.check_threshold(PREVIOUS, *args, **kwargs)
                    new["message"] = new["message"].replace("2026.10.1", "2026.09.3")
                    assert new == old


def test_year_table_and_regime_table_cannot_drift_apart() -> None:
    raw = json.loads(_raw("2026.10.1"))
    assert raw["schema"].endswith("/3") and prechecks.SCHEMAS[2] == raw["schema"]
    broken = json.loads(json.dumps(raw))
    broken["eu_thresholds"]["periods"][3]["values"]["works"] = 5350001
    with pytest.raises(prechecks.ProfileError, match="weichen bei 'works' ab"):
        prechecks.profile_from_dict(broken)
    broken = json.loads(json.dumps(raw))
    broken["eu_regimes"]["precheck_view"]["categories"].pop("construction")
    with pytest.raises(prechecks.ProfileError, match="precheck_view"):
        prechecks.profile_from_dict(broken)
    broken = json.loads(json.dumps(raw))
    del broken["eu_regimes"]
    with pytest.raises(prechecks.ProfileError):
        prechecks.profile_from_dict(broken)


def _broken(change: str) -> dict:
    block = json.loads(_raw("2026.10.1"))["eu_regimes"]
    utilities = block["regimes"][1]
    rows = utilities["contract_types"][1]["thresholds"]
    if change == "value":
        rows[2]["value"] = 419000
    elif change == "source":
        rows[2]["source"] = "32099R0001"
    elif change == "overlap":
        rows[2]["valid_from"] = "2016-04-01"
    elif change == "order":
        rows[2]["valid_to"] = "2016-01-01"
    elif change == "duplicate":
        block["regimes"].append(utilities)
    elif change == "label":
        del utilities["contract_types"][0]["label"]["en"]
    elif change == "both":
        utilities["contract_types"][0]["authority_types"] = []
    elif change == "checksum":
        block["sources"]["32015R2171"]["retrieved_sha256"] = "abc"
    elif change == "quote":
        block["sources"]["32015R2171"]["quote"] = ""
    elif change == "comparison":
        block["comparison"] = "exceeded"
    elif change == "view-regime":
        block["precheck_view"]["regime"] = "railways"
    elif change == "view-type":
        block["precheck_view"]["categories"]["construction"] = "bridges"
    elif change == "empty":
        utilities["contract_types"] = []
    return block


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("value", "steht nicht im Wortlaut"),
        ("source", "ohne amtliche Fundstelle"),
        ("overlap", "überschneiden"),
        ("order", "Wert oder Zeitraum"),
        ("duplicate", "nicht eindeutig"),
        ("label", "'en' fehlt"),
        ("both", "entweder thresholds oder authority_types"),
        ("checksum", "Prüfsumme"),
        ("quote", "'quote' fehlt"),
        ("comparison", "Vergleichsregel"),
        ("view-regime", "unbekanntes Regime"),
        ("view-type", "unbekannte Auftragsart"),
        ("empty", "fehlt oder ist leer"),
    ],
)
def test_regime_block_without_evidence_is_rejected(change: str, message: str) -> None:
    with pytest.raises(RegimeError, match=message):
        parse_regimes(_broken(change))


def test_regime_block_must_be_an_object_and_profile_reports_the_cause() -> None:
    with pytest.raises(RegimeError, match="kein Objekt"):
        parse_regimes([])
    raw = json.loads(_raw("2026.10.1"))
    raw["eu_regimes"] = _broken("value")
    with pytest.raises(prechecks.ProfileError, match="EU-Schwellenwerte je Regime"):
        prechecks.profile_from_dict(raw)


def test_packaged_profile_is_reproducible_from_the_builder() -> None:
    spec = importlib.util.spec_from_file_location("builder", TOOLS / "build_eu_regimes_profile.py")
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    built = builder.build(json.loads(_raw("2026.09.3")))
    assert (json.dumps(built, indent=1, ensure_ascii=False) + "\n").encode() == _raw("2026.10.1")
    assert prechecks.CURRENT_PROFILE == ("procurement.hvtg", builder.VERSION)
    quotes = json.loads((TOOLS / "eu_threshold_sources.json").read_text(encoding="utf-8"))
    assert set(quotes) == set(builder.ACTS) == set(NEW.eu_regimes.sources if NEW.eu_regimes else ())
