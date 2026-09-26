"""Recommended profiles implementing the user decisions of 23.09.2026 ("alle empfehlungen").

Legacy profiles stay bit-identical (their replay tests are unchanged); the
decisions K2, K3, K5, K8, K9, K11 live in new, approved profile versions.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from conftest import fixture

from auditcore_risk import (
    InputError,
    assess_contractor,
    evaluate,
    flatten_record,
    load_fraud_profile,
    load_profile,
    score_signals,
)

D = "2026.09.2"
RA = load_profile("riskanalysis.year_bound", D)
RA_LEGACY = load_profile("riskanalysis.legacy", "b5c523bf7eaa")


def row(**kw: Any) -> dict[str, Any]:
    base = {
        "bruttobetrag": 1000.0,
        "nettobetrag": 840.34,
        "Name": "A",
        "zahlungsempfaenger": "B",
        "rechnungsdatum_dt": date(2026, 3, 1),
    }
    base.update(kw)
    return base


def test_decided_profiles_are_approved_and_name_the_decision() -> None:
    for profile in (
        RA,
        load_profile("flowinvoice.risk_checker", D),
        load_profile("flowinvoice.rbvk_wibank", D),
    ):
        assert profile.status == "APPROVED"
        assert profile.source["decision"]["decided_on"] == "2026-09-23"
        assert profile.source["decision"]["quote"] == "alle empfehlungen"
    for pid in ("flowinvoice.fraud_signals", "flowinvoice.ted_contractor"):
        assert load_fraud_profile(pid, D).status == "APPROVED"


def test_k2_k3_net_amount_against_the_year_bound_eu_threshold() -> None:
    rows = [
        row(bruttobetrag=238_000.0, nettobetrag=200_000.0),  # 2026: [194.400; 216.000)
        row(bruttobetrag=238_000.0, nettobetrag=200_000.0, rechnungsdatum_dt=date(2025, 6, 1)),
        row(bruttobetrag=24_000.0, nettobetrag=20_168.07),
    ]
    flags = [r.flags["RF02"] for r in evaluate(rows, RA).records]
    assert flags == [True, True, False]
    legacy = [r.flags["RF02"] for r in evaluate(rows, RA_LEGACY).records]
    assert legacy == [False, False, True]  # legacy: gross against static list
    with pytest.raises(InputError):
        evaluate([{k: v for k, v in row().items() if k != "nettobetrag"}], RA)


def test_k2_rf08_uses_the_net_amount() -> None:
    rows = [
        row(bruttobetrag=29_000.0, nettobetrag=24_369.75, vergabenummer="0"),
        row(bruttobetrag=31_000.0, nettobetrag=26_050.42, vergabenummer="0"),
    ]
    assert [r.flags["RF08"] for r in evaluate(rows, RA).records] == [False, True]


def test_k5_rf12_only_within_the_same_group() -> None:
    rows = [
        row(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=1),
        row(bruttobetrag=10_000.0, abweichungen_betrag=3_000.0, antrag=2, Gruppennummer=1),
        row(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=2),
        row(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=None),
    ]
    assert [r.flags["RF12"] for r in evaluate(rows, RA).records] == [True, False, False, False]
    assert [r.flags["RF12"] for r in evaluate(rows, RA_LEGACY).records] == [True, False, True, True]


def split_request(day: str, amounts: list[float]) -> dict[str, Any]:
    return flatten_record(
        {
            "net_amount": 100.0,
            "description": "Wartung",
            "vendor_name": "X",
            "invoice_date": day,
            "service_period_start": day,
            "context": {
                "vendor_invoices": [{"net_amount": a, "invoice_date": day} for a in amounts]
            },
        }
    )


def test_k9_splitting_includes_the_year_bound_eu_threshold() -> None:
    decided = load_profile("flowinvoice.risk_checker", D)
    legacy = load_profile("flowinvoice.risk_checker", "fb2d18568d2e")
    near_eu = [180_000.0, 190_000.0, 200_000.0]  # within [172.800; 216.000] in 2026
    request = split_request("2026-04-01", near_eu)
    assert evaluate([request], decided).records[0].flags["SPLIT_INVOICE"] is True
    assert evaluate([request], legacy).records[0].flags["SPLIT_INVOICE"] is False
    hit = evaluate([request], decided).records[0].hits
    assert hit[0].evidence["threshold"] == 216000.0
    undecided = evaluate([split_request("2023-04-01", near_eu)], decided).records[0]
    assert undecided.flags["SPLIT_INVOICE"] is None
    national = evaluate([split_request("2023-04-01", [900.0, 950.0, 990.0])], decided).records[0]
    assert national.flags["SPLIT_INVOICE"] is True


def test_k11_wibank_follows_profile_file_v121() -> None:
    decided = load_profile("flowinvoice.rbvk_wibank", D)

    def score(**kw: Any) -> dict[str, Any]:
        assessment = evaluate([kw], decided).records[0].assessment
        assert assessment is not None
        return dict(assessment)

    assert score(offene_auflagen_anzahl=1)["score"] == 1
    assert score(offene_auflagen_anzahl=3)["score"] == 2  # score_max 2
    assert score(offene_auflagen_anzahl=True)["score"] == 1
    assert score(externe_kuerzung=500.0)["criteria"]["K12"] is True
    only_verwk = score(vorherige_verwk_quote=3.0)
    assert only_verwk["criteria"]["K12"] is False and only_verwk["criteria"]["K16"] is True
    assert only_verwk["score"] == 2 - 2
    codes = score(vorherige_kuerzungsgruende=["13.1", "5.2", "1.24"])["criteria"]
    assert (codes["K20"], codes["K21"], codes["K22"]) == (True, True, True)
    codes = score(vorherige_kuerzungsgruende=["13.2", "8.4"])["criteria"]
    assert (codes["K20"], codes["K21"], codes["K22"]) == (False, False, False)
    # no earlier finding family '' any more: an empty history scores nothing
    assert score(vorherige_kuerzungsgruende=[])["score"] == 0


def test_k8_signal_policy() -> None:
    decided = load_fraud_profile("flowinvoice.fraud_signals", D)
    legacy = load_fraud_profile("flowinvoice.fraud_signals", "fb2d18568d2e")
    signals = {
        "company": {
            "risk_indicators": ["NAME_MISMATCH", "NAME_MISMATCH"],
            "verification_score": 1.0,
        }
    }
    assert score_signals(signals, decided).raw_score == pytest.approx(0.1)
    assert score_signals(signals, legacy).raw_score == pytest.approx(0.2)
    ted = {"red_flags": [{"severity": "high", "flag_type": "X"}], "legitimacy_score": 40.0}
    with pytest.raises(InputError):
        score_signals({"ted": ted}, decided)
    assert score_signals({"ted": {**ted, "legitimacy_score": 0.4}}, decided).raw_score == (
        pytest.approx(0.1 + 0.6 * 0.2)
    )


def test_k8_ted_legitimacy_as_fraction() -> None:
    decided = load_fraud_profile("flowinvoice.ted_contractor", D)
    legacy = load_fraud_profile("flowinvoice.ted_contractor", "fb2d18568d2e")
    for case in fixture("flowinvoice_fraud_observed.json")["ted"][:40]:
        new = assess_contractor(case["notices"], decided).legitimacy_score
        old = assess_contractor(case["notices"], legacy).legitimacy_score
        assert new["rating"] == old["rating"]
        assert new["score"] == pytest.approx(old["score"] / 100, abs=0.0011)
        assert 0 <= new["score"] <= 1


def test_k4_rf09_uses_the_transliterating_payee_profile() -> None:
    k4 = load_profile("riskanalysis.year_bound", "2026.09.3")
    assert k4.status == "APPROVED"
    assert "K4" in k4.source["decision"]["decisions"]
    assert dict(k4.rule("RF09").params["normalization"]) == {
        "profile": "riskanalysis.payee",
        "version": "2026.09.2",
    }
    rows = [row(Name="Müller Bau GmbH", zahlungsempfaenger="Mueller Bau KG")]
    assert evaluate(rows, k4).records[0].flags["RF09"] is True
    assert evaluate(rows, RA).records[0].values["name_match"] < 1.0  # 2026.09.2: 'mu ller'
    hit = evaluate(rows, k4).records[0].hits
    rf09 = next(h for h in hit if h.code == "RF09")
    assert rf09.evidence["left"] == "mueller bau"
    assert rf09.evidence["normalization"]["version"] == "2026.09.2"
    # all other rules identical to the superseded 2026.09.2
    for a, b in zip(RA.rules, k4.rules, strict=True):
        if a.code != "RF09":
            assert a == b


C2_RA = load_profile("riskanalysis.year_bound", "2026.09.4")
C2_RC = load_profile("flowinvoice.risk_checker", "2026.09.3")


def test_c2_profiles_reference_the_historic_procurement_profile() -> None:
    k4 = load_profile("riskanalysis.year_bound", "2026.09.3")
    for new, old in ((C2_RA, k4), (C2_RC, load_profile("flowinvoice.risk_checker", D))):
        assert new.status == "APPROVED"
        assert new.source["decision"]["quote"] == "c2. ja"
        assert new.source["derived_from"] == {"profile": old.id, "version": old.version}
        assert new.fingerprint != old.fingerprint
    rf02 = C2_RA.rule("RF02").params["thresholds"]["procurement_eu"]
    assert (rf02["profile"], rf02["version"]) == ("procurement.hvtg", "2026.09.3")
    split = C2_RC.rule("SPLIT_INVOICE").params["procurement_eu"]
    assert (split["profile"], split["version"]) == ("procurement.hvtg", "2026.09.3")
    # only the procurement reference differs from the superseded versions
    for a, b in zip(k4.rules, C2_RA.rules, strict=True):
        if a.code != "RF02":
            assert a == b
        else:
            assert a.params["thresholds"]["static"] == b.params["thresholds"]["static"]
            assert a.params["field"] == b.params["field"] and a.params["lower"] == b.params["lower"]


def test_c2_rf02_2019_is_decided_instead_of_undetermined() -> None:
    k4 = load_profile("riskanalysis.year_bound", "2026.09.3")
    rows = [
        row(bruttobetrag=8_330.0, nettobetrag=7_000.0, rechnungsdatum_dt=date(2019, 5, 1)),
        row(bruttobetrag=238_000.0, nettobetrag=200_000.0, rechnungsdatum_dt=date(2019, 5, 1)),
        row(bruttobetrag=238_000.0, nettobetrag=200_000.0, rechnungsdatum_dt=date(2015, 5, 1)),
        row(bruttobetrag=238_000.0, nettobetrag=200_000.0, rechnungsdatum_dt=date(2013, 5, 1)),
        row(bruttobetrag=238_000.0, nettobetrag=200_000.0, rechnungsdatum_dt=date(2028, 1, 1)),
    ]
    before = [r.flags["RF02"] for r in evaluate(rows, k4).records]
    assert before == [None, None, None, None, None]  # 2026.09.2 covers only 2024–2027
    result = evaluate(rows, C2_RA).records
    # 2019: 221.000 € -> [198.900; 221.000); 2015: 207.000 € -> [186.300; 207.000)
    assert [r.flags["RF02"] for r in result] == [False, True, True, None, None]
    hit = next(h for h in result[1].hits if h.code == "RF02")
    match = hit.evidence["matches"][0]
    assert match["threshold"] == 221000.0 and match["version"] == "2026.09.3"
    assert match["official_journal"] == "ABl. L 337 vom 19.12.2017, S. 19"
    assert "2013" in result[3].undetermined["RF02"]


def test_c2_splitting_uses_the_threshold_of_the_invoice_year() -> None:
    near_2019 = [200_000.0, 205_000.0, 210_000.0]  # within [176.800; 221.000] in 2019
    request = split_request("2019-04-01", near_2019)
    assert evaluate([request], C2_RC).records[0].flags["SPLIT_INVOICE"] is True
    assert (
        evaluate([request], load_profile("flowinvoice.risk_checker", D))
        .records[0]
        .flags["SPLIT_INVOICE"]
        is None
    )
    hit = evaluate([request], C2_RC).records[0].hits
    assert hit[0].evidence["threshold"] == 221000.0
    early = evaluate([split_request("2013-04-01", near_2019)], C2_RC).records[0]
    assert early.flags["SPLIT_INVOICE"] is None
