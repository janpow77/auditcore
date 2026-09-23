"""Profiles are explicit, versioned, source-bound and fingerprinted (F-15)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import fixture

from auditcore_risk import ProfileError, available_profiles, load_profile, profile_from_dict
from auditcore_risk.profiles import fingerprint

DATA = Path(__file__).parents[1] / "src" / "auditcore_risk" / "profile_data"
LEGACY = ("riskanalysis.legacy", "b5c523bf7eaa")
YEAR = ("riskanalysis.year_bound", "2026.09.1")
FLOWSTAT = ("audit_designer.flowstat_belegliste", "1254591156d3")
RISK_CHECKER = ("flowinvoice.risk_checker", "fb2d18568d2e")
VERWK = [
    (p, "fb2d18568d2e")
    for p in ("flowinvoice.rbvk_wibank", "flowinvoice.exante_basis", "flowinvoice.exante_heuristik")
]


def raw(profile_id: str, version: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((DATA / f"{profile_id}-{version}.json").read_text())
    return data


def test_packaged_profiles_and_status() -> None:
    assert available_profiles() == tuple(sorted([LEGACY, YEAR, FLOWSTAT, RISK_CHECKER, *VERWK]))
    assert load_profile(*LEGACY).status == "LEGACY_CHARACTERIZED"
    assert load_profile(*FLOWSTAT).status == "LEGACY_CHARACTERIZED"
    assert load_profile(*YEAR).status == "CANDIDATE_HUMAN_DECISION_REQUIRED"
    for pid, version in available_profiles():
        profile = load_profile(pid, version)
        assert len(profile.fingerprint) == 64
        assert profile.reference["fingerprint"] == fingerprint(raw(pid, version))
        assert profile.open_decisions
        for rule in profile.rules:
            assert rule.origin["symbol"] and rule.origin["lines"]


def test_legacy_constants_equal_the_executed_source() -> None:
    constants = fixture("riskanalysis_observed.json")["constants"]
    profile = load_profile(*LEGACY)
    assert profile.source["commit"] == "b5c523bf7eaa326153778d9751f176f03d4d56ed"
    assert profile.source["git_blob"] == "b6196a7dbd3838bd4dd361c71e3cc44c904f4980"
    assert [r.code for r in profile.rules] == constants["RED_FLAG_CODES"]
    assert {r.code: r.label for r in profile.rules} == constants["RED_FLAG_LABELS"]
    rf02 = profile.rule("RF02").params
    assert list(rf02["thresholds"]["static"]) == constants["VERGABE_SCHWELLEN"]
    assert rf02["lower"]["proximity"] == constants["_PROXIMITY"]
    rf08 = profile.rule("RF08").params
    assert rf08["amount_gt"] == constants["RF08_BAGATELLGRENZE"]
    assert rf08["placeholder_pattern"] == constants["_PLATZHALTER_VERGABE"]
    assert rf08["relevance"]["exclude_pattern"] == constants["_NICHT_VERGABERELEVANT"]
    assert profile.rule("RF10").params["relevance"] == rf08["relevance"]
    assert [r.interpretation for r in profile.rules if r.code in {"RF10", "RF11", "RF12"}] == [
        "descriptive_prior"
    ] * 3


def test_flowstat_constants_equal_the_executed_source() -> None:
    constants = fixture("flowstat_observed.json")["constants"]
    profile = load_profile(*FLOWSTAT)
    rf02 = profile.rule("BL_RF02_NEAR_THRESHOLD").params
    assert list(rf02["thresholds"]["static"]) == constants["PROCUREMENT_THRESHOLDS"]
    assert {s["commit"] for s in profile.source["sources"]} == {
        "1254591156d3bdf6ccdf4050dec7713a61ad4a20",
        "ac1ccc779db69492db0c2c154b6ec84fdd1794b1",
    }


def test_year_bound_candidate_changes_only_rf02() -> None:
    legacy, year = raw(*LEGACY), raw(*YEAR)
    for a, b in zip(legacy["rules"], year["rules"], strict=True):
        if a["code"] != "RF02":
            assert a == b
    rf02 = next(r for r in year["rules"] if r["code"] == "RF02")["params"]["thresholds"]
    assert 221000.0 not in rf02["static"]
    assert rf02["procurement_eu"]["profile"] == "procurement.hvtg"


def test_fingerprint_changes_with_any_parameter() -> None:
    data = raw(*LEGACY)
    before = fingerprint(data)
    data["rules"][1]["params"]["lower"]["proximity"] = 0.2
    assert fingerprint(data) != before
    assert profile_from_dict(data).fingerprint != load_profile(*LEGACY).fingerprint


def broken_variants() -> list[dict[str, Any]]:
    data = raw(*LEGACY)
    rule = data["rules"][0]

    def with_rule(**changes: Any) -> dict[str, Any]:
        return {**data, "rules": [{**rule, **changes}, *data["rules"][1:]]}

    return [
        {**data, "schema": "x"},
        {**data, "status": "FREIGEGEBEN"},
        {**data, "extra": 1},
        {**data, "rules": []},
        {**data, "source": {}},
        {**data, "summary": {"format": "x"}},
        {**data, "summary": {"format": "riskanalysis.red_flag_summary"}},
        {**data, "open_decisions": "keine"},
        {**data, "rules": [rule, rule]},
        with_rule(kind="score"),
        with_rule(params={**rule["params"], "weight": 2}),
        with_rule(params={k: v for k, v in rule["params"].items() if k != "multiple"}),
        with_rule(params={**rule["params"], "multiple": "1000"}),
        with_rule(params={**rule["params"], "parse": "lax"}),
        with_rule(when_missing_columns="ignore"),
        with_rule(interpretation="error_rate"),
        with_rule(origin={}),
        with_rule(label=""),
        with_rule(extra=True),
    ]


@pytest.mark.parametrize("broken", broken_variants())
def test_profile_validation(broken: dict[str, Any]) -> None:
    with pytest.raises(ProfileError):
        profile_from_dict(broken)


def test_rule_specific_validation() -> None:
    data = raw(*LEGACY)

    def change(code: str, **params: Any) -> dict[str, Any]:
        rules = [
            {**r, "params": {**r["params"], **params}} if r["code"] == code else r
            for r in data["rules"]
        ]
        return {**data, "rules": rules}

    for broken in (
        change("RF02", lower={"proximity": 1.5}),
        change("RF02", lower={"proximity": 0.1, "factor": 0.9}),
        change("RF02", count="some"),
        change("RF02", thresholds={"static": [-1]}),
        change("RF02", thresholds={"static": [1000], "manual": [5]}),
        change("RF02", thresholds={"static": [], "procurement_eu": {"profile": "x"}}),
        change("RF08", placeholder_pattern="("),
        change("RF08", relevance={"field": "x"}),
        change("RF08", id_column_missing="maybe"),
        change("RF09", scorer="partial_ratio"),
        change("RF09", normalization={"profile": "x"}),
        change("RF10", pair={"count_gt": 20}),
        change("RF13", op="eq"),
    ):
        with pytest.raises(ProfileError):
            profile_from_dict(broken)


def test_lookup_requires_explicit_known_profile() -> None:
    for args in (("unknown", "1"), (LEGACY[0], "0"), ("../x", LEGACY[1])):
        with pytest.raises(ProfileError):
            load_profile(*args)
    with pytest.raises(ProfileError):
        load_profile(None, "1")  # type: ignore[arg-type]
    with pytest.raises(ProfileError):
        load_profile(*LEGACY).rule("RF99")
