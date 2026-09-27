"""Fraud-check signals as risk flags (``auditcore_risk.web.signals``) and their parity.

The fixture holds 268 executed runs of flowinvoice's ``FraudDetectionManager``
(flowinvoice@fb2d185, ``tools/capture_flowinvoice_fraud.py``). The evaluation
must show exactly the blockers, warnings, score and level of the manager
(legacy profile) and of ``score_signals`` for the decided profile flowinvoice
uses in production (2026.09.2).
"""

from __future__ import annotations

from typing import Any

import pytest
from conftest import fixture

pytest.importorskip("starlette")
pytest.importorskip("httpx")

from starlette.testclient import TestClient  # noqa: E402

from auditcore_risk import InputError, load_fraud_profile, score_signals  # noqa: E402
from auditcore_risk.web import create_app, signal_evaluation  # noqa: E402

MANAGER = fixture("flowinvoice_fraud_observed.json")["manager"]
LEGACY = load_fraud_profile("flowinvoice.fraud_signals", "fb2d18568d2e")
DECIDED = load_fraud_profile("flowinvoice.fraud_signals", "2026.09.2")
DISPLAY = load_fraud_profile("flowinvoice.fraud_signals", "2026.09.3")
SIGNALS: dict[str, Any] = {
    "invoice": "RE-1",
    "duplicate": {"is_duplicate": True, "matches": [{"match_type": "exact", "confidence": 1.0}]},
    "sanctions": {"failed": True},
    "pep": {"is_clean": True, "error_message": None, "matches": []},
    "company": {"risk_indicators": ["INVALID_VAT_ID", "NEW_COMPANY"], "verification_score": 0.4},
    "ted": {
        "red_flags": [{"severity": "high", "flag_type": "SINGLE_BIDDER"}],
        "legitimacy_score": 0.5,
    },
}


def _record(evaluation: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = evaluation["records"][0]
    return record


def _expect_manager(case: dict[str, Any], profile: Any) -> None:
    record = _record(signal_evaluation([case["signals"]], profile))
    assessment = record["assessment"]
    assert sorted(record["codes"]) == sorted(case["blockers"] + case["warnings"])
    assert sorted(assessment["blockers"]) == case["blockers"]
    assert sorted(assessment["warnings"]) == case["warnings"]
    hits = {h["code"]: h["severity"] for h in record["hits"]}
    assert all(hits[code] == "CRITICAL" for code in case["blockers"])
    assert record["assessment"]["score"] == case["risk_score"]
    assert record["assessment"]["level"] == case["risk_level"]
    assert record["assessment"]["checks_performed"] == ", ".join(case["checks_performed"])
    assert all(record["flags"][code] is True for code in record["codes"])


@pytest.mark.parametrize("case", MANAGER, ids=lambda c: c["name"])
def test_evaluation_shows_the_executed_flowinvoice_manager(case: dict[str, Any]) -> None:
    if case["exception"] is not None:
        with pytest.raises(InputError):
            signal_evaluation([case["signals"]], LEGACY)
        return
    _expect_manager(case, LEGACY)


@pytest.mark.parametrize("case", MANAGER, ids=lambda c: c["name"])
def test_evaluation_equals_score_signals_of_the_production_profile(case: dict[str, Any]) -> None:
    try:
        expected = score_signals(case["signals"], DECIDED)
    except InputError:
        with pytest.raises(InputError):
            signal_evaluation([case["signals"]], DECIDED)
        return
    for profile in (DECIDED, DISPLAY):  # 2026.09.3 only adds display texts
        record = _record(signal_evaluation([case["signals"]], profile))
        assert record["codes"] == [*expected.blockers, *expected.warnings]
        assert record["assessment"]["score"] == expected.score
        assert record["assessment"]["level"] == expected.level
        assert record["assessment"]["raw_score"] == expected.raw_score


def test_failed_check_leaves_its_codes_undetermined_and_dynamic_codes_become_rules() -> None:
    evaluation = signal_evaluation([SIGNALS], DISPLAY, record_key="invoice")
    record = _record(evaluation)
    assert record["key"] == "RE-1"
    assert record["flags"]["SANCTIONS_CHECK_FAILED"] is True
    assert record["flags"]["SANCTIONED_ENTITY"] is None
    assert record["undetermined"]["SANCTIONED_ENTITY"] == (
        "Teilprüfung „Sanktionslistenprüfung“ abgebrochen"
    )
    assert record["flags"]["PEP_HIT_FOUND"] is False
    hits = {h["code"]: h for h in record["hits"]}
    assert hits["EXACT_DUPLICATE_FOUND"]["severity"] == "CRITICAL"
    assert hits["EXACT_DUPLICATE_FOUND"]["label"] == "Exakte Dublette gefunden"
    assert hits["TED_SINGLE_BIDDER"]["severity"] == "HIGH"
    assert hits["TED_SINGLE_BIDDER"]["label"] == "TED-Auftragsprüfung: TED_SINGLE_BIDDER"
    assert hits["NEW_COMPANY"]["severity"] is None
    assert hits["INVALID_VAT_ID"]["evidence"]["component"]["component"] == "company"
    codes = [r["code"] for r in evaluation["rules"]]
    assert codes[-2:] == ["NEW_COMPANY", "TED_SINGLE_BIDDER"]
    assert record["assessment"]["level"] == "critical" and record["assessment"]["blocked"]


def test_switched_off_checks_are_skipped_and_labels_fall_back_to_codes() -> None:
    evaluation = signal_evaluation([{"duplicate": None, "pep": None}], DECIDED)
    assert (
        evaluation["skipped"]["SANCTIONED_ENTITY"] == "Teilprüfung „sanctions“ nicht durchgeführt"
    )
    assert _record(evaluation)["flags"] == {}
    labels = {r["code"]: r["label"] for r in evaluation["rules"]}
    assert labels["SANCTIONED_ENTITY"] == "SANCTIONED_ENTITY"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def test_rest_lists_and_describes_signal_profiles(client: TestClient) -> None:
    listed = client.get("/risk/fraud-profiles").json()["profiles"]
    assert [(p["id"], p["version"]) for p in listed] == [
        ("flowinvoice.fraud_signals", "2026.09.2"),
        ("flowinvoice.fraud_signals", "2026.09.3"),
        ("flowinvoice.fraud_signals", "fb2d18568d2e"),
    ]
    detail = client.get("/risk/profiles/flowinvoice.fraud_signals/2026.09.3").json()
    assert detail["kind"] == "signal_score" and detail["assessment"] == "signal_score"
    assert detail["status"] == "CANDIDATE_HUMAN_DECISION_REQUIRED"
    assert [f["name"] for f in detail["fields"]] == [
        "duplicate",
        "sanctions",
        "pep",
        "company",
        "ted",
    ]
    assert detail["rules"][0]["label"] == "Exakte Dublette gefunden"
    assert client.get("/risk/profiles/flowinvoice.duplicates/fb2d18568d2e").status_code == 404
    assert client.get("/risk/profiles/riskanalysis.year_bound/2026.09.5").status_code == 200


def test_rest_evaluates_signals(client: TestClient) -> None:
    body = {
        "profile": {"id": "flowinvoice.fraud_signals", "version": "2026.09.2"},
        "records": [SIGNALS, {"invoice": "RE-2"}],
        "record_key": "invoice",
    }
    answer = client.post("/risk/fraud-signals/evaluate", json=body)
    assert answer.status_code == 200
    data = answer.json()
    assert data["profile"]["version"] == "2026.09.2"
    assert [r["key"] for r in data["records"]] == ["RE-1", "RE-2"]
    assert data["records"][1]["assessment"]["level"] == "low"


@pytest.mark.parametrize(
    ("body", "status", "code"),
    [
        ([], 400, "invalid_request"),
        ({"profile": {"id": "flowinvoice.fraud_signals"}, "records": []}, 400, "invalid_request"),
        ({"profile": {"id": "x", "version": "1"}, "records": []}, 404, "profile_not_found"),
        (
            {"profile": {"id": "flowinvoice.fraud_signals", "version": "2026.09.2"}, "rows": []},
            400,
            "invalid_request",
        ),
        (
            {
                "profile": {"id": "flowinvoice.fraud_signals", "version": "2026.09.2"},
                "records": [{"ted": {"red_flags": [{}], "legitimacy_score": 5}}],
            },
            400,
            "input_error",
        ),
    ],
)
def test_rest_rejects_invalid_signal_requests(
    client: TestClient, body: object, status: int, code: str
) -> None:
    answer = client.post("/risk/fraud-signals/evaluate", json=body)
    assert answer.status_code == status
    assert answer.json()["error"]["code"] == code
