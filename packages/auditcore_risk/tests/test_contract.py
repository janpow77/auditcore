"""Library contract and deliberate deviations from the sources (RK-C01 … RK-C06)."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import pytest

import auditcore_risk
from auditcore_risk import (
    DependencyError,
    InputError,
    ProfileError,
    evaluate,
    load_profile,
    missing_columns,
)

LEGACY = load_profile("riskanalysis.legacy", "b5c523bf7eaa")
FLOWSTAT = load_profile("audit_designer.flowstat_belegliste", "1254591156d3")


def base(**kw: Any) -> dict[str, Any]:
    row = {"bruttobetrag": 1234.0, "Name": "Alpha GmbH", "zahlungsempfaenger": "Beta KG"}
    row.update(kw)
    return row


def test_profile_must_be_explicit() -> None:
    with pytest.raises(ProfileError):
        evaluate([base()], "riskanalysis.legacy")  # type: ignore[arg-type]
    assert not hasattr(auditcore_risk, "score")
    assert not hasattr(auditcore_risk, "default_profile")


def test_every_hit_is_explained_and_bound_to_profile_and_source() -> None:
    rows = [base(bruttobetrag=40_000.0, vergabenummer="0=ni")]
    result = evaluate(rows, LEGACY)
    assert result.profile == LEGACY.reference
    assert result.records[0].codes == ("RF01", "RF08")
    rf08 = result.records[0].hits[1]
    assert rf08.label == LEGACY.rule("RF08").label
    assert "Platzhalter" in rf08.reason and "'0=ni'" in rf08.reason
    assert rf08.evidence["id_state"] == "ist ein Platzhalter"
    assert rf08.origin["symbol"].startswith("_hat_echte_vergabe")
    assert rf08.origin["lines"] == "40-47, 78-89, 258-268"
    json.dumps(result.to_dict())


def test_descriptive_priors_are_marked() -> None:
    rows = [
        base(bruttobetrag=3_000.0, payee_canonical="bau ag", antrag=1, vergabenummer="VG-1")
        for _ in range(21)
    ]
    hit = evaluate(rows, LEGACY).records[0].hits[-1]
    assert hit.code == "RF10"
    assert hit.interpretation == "descriptive_prior"
    assert hit.note is not None and "2-%-Wesentlichkeit" in hit.note
    assert hit.evidence["pair"] == {"case": 1, "payee": "bau ag", "count": 21, "sum": 63000.0}


def test_rk_c01_amounts_must_be_numbers() -> None:
    for value in ("1000", True, [1]):
        with pytest.raises(InputError):
            evaluate([base(bruttobetrag=value)], LEGACY)
    result = evaluate([base(bruttobetrag=Decimal("5000"))], LEGACY)
    assert result.records[0].flags["RF01"] is True


def test_rk_c02_required_columns() -> None:
    with pytest.raises(InputError):
        evaluate([{"Name": "A", "zahlungsempfaenger": "B"}], LEGACY)
    with pytest.raises(InputError):
        evaluate([{"bruttobetrag": 1.0}], LEGACY)
    assert missing_columns(LEGACY, ["bruttobetrag"]) == {
        "RF09": ["Name", "zahlungsempfaenger"],
        "RF11": ["Anzahl_Versionen", "Anzahl_ungueltige_Versionen"],
        "RF12": ["Gruppennummer", "antrag"],
    }
    result = evaluate([{"projektbetrag": 5000.0}], FLOWSTAT)
    assert "BL_RF03_MISSING_PAYMENT_DATE" in result.skipped
    assert [dict(s) for s in result.summary] == [{"code": "BL_RF01_ROUND_AMOUNT", "count": 1}]


def test_rk_c03_name_matching_requires_rapidfuzz(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    import auditcore_risk.rules as rules

    real = importlib.util.find_spec
    monkeypatch.setattr(
        rules, "find_spec", lambda name: None if name == "rapidfuzz" else real(name)
    )
    with pytest.raises(DependencyError):
        evaluate([base()], LEGACY)


def test_rk_c04_year_bound_profile_requires_procurement(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    import auditcore_risk.base as risk_base

    real = importlib.util.find_spec
    monkeypatch.setattr(
        risk_base, "find_spec", lambda name: None if name == "auditcore_procurement" else real(name)
    )
    year = load_profile("riskanalysis.year_bound", "2026.09.1")
    with pytest.raises(DependencyError):
        evaluate([base(rechnungsdatum_dt=None)], year)
    evaluate([base()], LEGACY)  # the legacy profile does not need it


def test_records_contract() -> None:
    with pytest.raises(InputError):
        evaluate([["not", "a", "mapping"]], LEGACY)  # type: ignore[list-item]
    with pytest.raises(InputError):
        evaluate([{1: 2}], LEGACY)  # type: ignore[dict-item]
    with pytest.raises(InputError):
        evaluate([base(antrag=[1], payee_canonical="x")], LEGACY)
    # a key absent in one record is a missing value, like a NaN cell
    rows = [base(Anzahl_Versionen=8, Anzahl_ungueltige_Versionen=6), base()]
    flags = [r.flags["RF11"] for r in evaluate(rows, LEGACY).records]
    assert flags == [True, False]
    assert (
        evaluate([], LEGACY, columns=["bruttobetrag", "Name", "zahlungsempfaenger"]).summary[0][
            "anteil_prozent"
        ]
        == 0.0
    )


def test_override_column_is_taken_over_as_in_the_source() -> None:
    rows = [
        base(Name="Selbst GmbH", zahlungsempfaenger="Selbst GmbH", _pseudonym_rf09=False),
        base(_pseudonym_rf09=True),
    ]
    result = evaluate(rows, LEGACY)
    assert [r.flags["RF09"] for r in result.records] == [False, True]
    assert result.records[0].values["name_match"] == 1.0
    assert "übernommene Vorberechnung" in result.records[1].hits[0].reason


def test_rf12_legacy_case_key_across_groups_is_reported() -> None:
    rows = [
        base(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=1),
        base(bruttobetrag=10_000.0, abweichungen_betrag=3_000.0, antrag=2, Gruppennummer=1),
        base(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=2),
    ]
    records = evaluate(rows, LEGACY).records
    assert [r.flags["RF12"] for r in records] == [True, False, True]
    assert records[2].hits[-1].evidence["matched_by_case_only"] is True
    assert "Legacyverhalten" in records[2].hits[-1].reason


def test_flowstat_dataset_finding_and_dates() -> None:
    from datetime import date, datetime

    rows = [
        {
            "projektbetrag": 600.0,
            "rechnungssteller": "A",
            "zahlungsdatum": date(2024, 1, 1),
            "rechnungsdatum": datetime(2024, 2, 1, 8, 0),
        },
        {
            "projektbetrag": 400.0,
            "rechnungssteller": "B",
            "zahlungsdatum": "2024-03-01",
            "rechnungsdatum": "2024-02-01",
        },
    ]
    result = evaluate(rows, FLOWSTAT)
    assert result.records[0].flags["BL_RF04_PAYMENT_BEFORE_INVOICE"] is True
    assert result.dataset[0].triggered and result.dataset[0].value == 0.6
    assert result.dataset[0].evidence["group"] == "A"
    with pytest.raises(InputError):
        evaluate([{"zahlungsdatum": "gestern", "rechnungsdatum": "2024-01-01"}], FLOWSTAT)


def test_evaluation_is_immutable() -> None:
    result = evaluate([base()], LEGACY)
    with pytest.raises(TypeError):
        result.records[0].flags["RF01"] = True  # type: ignore[index]
    with pytest.raises(AttributeError):
        result.records[0].index = 3  # type: ignore[misc]
