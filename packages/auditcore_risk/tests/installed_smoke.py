"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_risk import (
    DependencyError,
    available_fraud_profiles,
    available_profiles,
    evaluate,
    flatten_record,
    load_fraud_profile,
    load_profile,
    score_signals,
)


def main() -> None:
    """Exercise both legacy profiles and the optional-extra boundaries."""
    package = distribution("auditcore_risk")
    assert package.version == "0.1.0"
    runtime = [r for r in package.requires or [] if "extra ==" not in r]
    assert runtime == ["auditcore_entity_matching==0.2.0"], runtime
    assert find_spec("auditcore") is None
    assert len(available_profiles()) == 10
    assert len(available_fraud_profiles()) == 5
    flowstat = load_profile("audit_designer.flowstat_belegliste", "1254591156d3")
    result = evaluate([{"projektbetrag": 24_500.0}, {"projektbetrag": 5_000.0}], flowstat)
    assert [dict(s) for s in result.summary] == [
        {"code": "BL_RF01_ROUND_AMOUNT", "count": 1},
        {"code": "BL_RF02_NEAR_THRESHOLD", "count": 1},
    ]
    checker = load_profile("flowinvoice.risk_checker", "fb2d18568d2e")
    request = {
        "net_amount": 60_000.0,
        "description": "Diverse Leistungen",
        "vendor_name": "X",
        "invoice_date": "2025-05-01",
        "context": {"median_amount": None},
    }
    assessment = evaluate([flatten_record(request)], checker).records[0].assessment
    assert assessment is not None and assessment["highest_severity"] == "MEDIUM"
    signals = load_fraud_profile("flowinvoice.fraud_signals", "fb2d18568d2e")
    assert score_signals({"sanctions": {"is_sanctioned": True, "matches": []}}, signals).level == (
        "critical"
    )
    wibank = load_profile("flowinvoice.rbvk_wibank", "fb2d18568d2e")
    points = evaluate([{"erstes_vorhaben": True, "hat_absch": "ja", "prior_q": 60.0}], wibank)
    assert points.records[0].assessment is not None
    assert points.records[0].assessment["score"] == 3 + 2 + 2 + 1
    legacy = load_profile("riskanalysis.legacy", "b5c523bf7eaa")
    rows = [
        {
            "bruttobetrag": 40_000.0,
            "vergabenummer": "0=ni",
            "Name": "Beispiel GmbH",
            "zahlungsempfaenger": "Beispiel GmbH",
        }
    ]
    if find_spec("rapidfuzz") is None:
        try:
            evaluate(rows, legacy)
        except DependencyError:
            pass
        else:
            raise AssertionError("Name matching must require the optional extra")
    else:
        assert evaluate(rows, legacy).records[0].codes == ("RF01", "RF08", "RF09")
    if find_spec("pandas") is not None:
        import pandas as pd

        from auditcore_risk.frame import compute_red_flags

        if find_spec("rapidfuzz") is not None:
            out = compute_red_flags(pd.DataFrame(rows), legacy)
            assert out["red_flag_codes"].tolist() == [["RF01", "RF08", "RF09"]]
    print("PASS: installed auditcore_risk profiles, evaluation and extra boundaries")


if __name__ == "__main__":
    main()
