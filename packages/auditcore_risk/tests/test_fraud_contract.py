"""Contract of the fraud-check functions beyond the replay (RK-C08 … RK-C10)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from auditcore_risk import (
    InputError,
    ProfileError,
    available_fraud_profiles,
    find_duplicates,
    load_fraud_profile,
    score_signals,
    select_contracts,
)
from auditcore_risk.fraud import fraud_profile_from_dict, names_similar, parse_date

V = "fb2d18568d2e"
DATA = Path(__file__).parents[1] / "src/auditcore_risk/fraud_profiles"
SIGNALS = load_fraud_profile("flowinvoice.fraud_signals", V)
DUP = load_fraud_profile("flowinvoice.duplicates", V)


def raw(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((DATA / f"{name}-{V}.json").read_text())
    return data


def test_profiles_are_explicit_and_kind_checked() -> None:
    assert available_fraud_profiles() == (
        ("flowinvoice.duplicates", V),
        ("flowinvoice.fraud_signals", "2026.09.2"),
        ("flowinvoice.fraud_signals", V),
        ("flowinvoice.ted_contractor", "2026.09.2"),
        ("flowinvoice.ted_contractor", V),
    )
    with pytest.raises(ProfileError):
        load_fraud_profile("flowinvoice.duplicates", V, "signal_score")
    with pytest.raises(ProfileError):
        load_fraud_profile("flowinvoice.duplicates", "0")
    with pytest.raises(ProfileError):
        score_signals({}, DUP)


@pytest.mark.parametrize(
    "change",
    [
        {"schema": "x"},
        {"kind": "score"},
        {"extra": 1},
        {"parameters": {}},
        {"id": ""},
    ],
)
def test_profile_validation(change: dict[str, Any]) -> None:
    with pytest.raises(ProfileError):
        fraud_profile_from_dict({**raw("flowinvoice.fraud_signals"), **change})


def test_signal_profile_rule_validation() -> None:
    data = raw("flowinvoice.fraud_signals")
    data["parameters"]["levels"]["thresholds"].reverse()
    with pytest.raises(ProfileError):
        fraud_profile_from_dict(data)
    dup = raw("flowinvoice.duplicates")
    dup["parameters"]["fuzzy"]["amount_weight"] = 0.7
    with pytest.raises(ProfileError):
        fraud_profile_from_dict(dup)


def test_rk_c08_warnings_are_deterministic_and_components_explained() -> None:
    signals = {
        "duplicate": {"failed": True},
        "sanctions": None,
        "pep": {"is_clean": True, "error_message": "Timeout", "matches": []},
        "company": {
            "risk_indicators": ["NAME_MISMATCH", "NAME_MISMATCH", "INVALID_VAT_ID"],
            "verification_score": 0.5,
        },
        "ted": None,
    }
    result = score_signals(signals, SIGNALS)
    assert result.warnings == ("DUPLICATE_CHECK_FAILED", "PEP_CHECK_ERROR", "NAME_MISMATCH")
    assert result.blockers == ("INVALID_VAT_ID",)
    assert result.level == "critical"
    assert [c["component"] for c in result.components] == ["blockers", "warnings", "company"]
    assert result.components[1]["count"] == 4  # counted before de-duplication (legacy)
    assert result.profile["id"] == "flowinvoice.fraud_signals"


def test_rk_c09_ted_legitimacy_must_be_a_number() -> None:
    ted = {
        "red_flags": [{"severity": "low", "flag_type": "X"}],
        "legitimacy_score": {"score": 40.0},
    }
    with pytest.raises(InputError):
        score_signals({"ted": ted}, SIGNALS)
    ok = score_signals({"ted": {**ted, "legitimacy_score": 0.25}}, SIGNALS)
    assert ok.raw_score == 0.75 * 0.2
    assert ok.level == "low"


def test_select_contracts_like_the_sql() -> None:
    notices: list[dict[str, Any]] = [
        {"notice_id": "1", "contractor_name": " Bau AG ", "contract_award_date": "2024-01-01"},
        {"notice_id": "2", "contractor_name": "bau ag", "contract_award_date": None},
        {
            "notice_id": "3",
            "contractor_name": "Andere",
            "contractor_vat_id": "DE1",
            "contract_award_date": "2025-01-01",
        },
        {"notice_id": "4", "contractor_name": "Bau AG GmbH", "contract_award_date": "2025-02-01"},
    ]
    chosen = select_contracts(notices, "BAU AG", "DE1")
    assert [n["notice_id"] for n in chosen] == ["3", "1", "2"]
    assert [n["notice_id"] for n in select_contracts(notices, "bau ag", None)] == ["1", "2"]


def test_find_duplicates_prefers_exact_matches() -> None:
    invoice = {
        "invoice_number": "RE-1",
        "supplier_name": "Nord GmbH",
        "total_amount": "100.00",
        "invoice_date": "2025-05-01",
    }
    candidates = [
        {
            "id": "a",
            "invoice_number": "RE-1",
            "gross_amount": "100,00",
            "invoice_date": "02.05.2025",
            "supplier_name": "Nord GmbH",
        },
        {
            "id": "b",
            "invoice_number": "RE-9",
            "gross_amount": "101.00",
            "invoice_date": "2025-05-03",
            "supplier_name": "Nord GmbH",
        },
    ]
    assert [m.candidate_id for m in find_duplicates(invoice, candidates, DUP)] == ["a"]
    fuzzy = find_duplicates(invoice, candidates[1:], DUP)
    assert [(m.candidate_id, m.match_type) for m in fuzzy] == [("b", "fuzzy")]
    assert fuzzy[0].confidence == round(1.0 - (0.01 * 0.5 + 2 / 7 * 0.5), 3)
    with pytest.raises(InputError):
        find_duplicates({**invoice, "total_amount": "0", "invoice_number": "X"}, candidates, DUP)


def test_legacy_name_and_date_heuristics() -> None:
    assert names_similar("nord gmbh", "süd gmbh", 5, 3)  # one shared word suffices
    assert not names_similar("nord", "süd", 5, 3)
    formats = raw("flowinvoice.duplicates")["parameters"]["fuzzy"]["date_formats"]
    assert parse_date("05/01/2025", formats).isoformat() == "2025-01-05"  # type: ignore[union-attr]
    assert parse_date("", formats) is None
