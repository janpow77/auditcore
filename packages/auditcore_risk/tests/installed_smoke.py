"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_risk import (
    DependencyError,
    available_profiles,
    evaluate,
    load_profile,
)


def main() -> None:
    """Exercise both legacy profiles and the optional-extra boundaries."""
    package = distribution("auditcore_risk")
    assert package.version == "0.1.0"
    runtime = [r for r in package.requires or [] if "extra ==" not in r]
    assert runtime == ["auditcore_entity_matching==0.2.0"], runtime
    assert find_spec("auditcore") is None
    assert len(available_profiles()) == 3
    flowstat = load_profile("audit_designer.flowstat_belegliste", "1254591156d3")
    result = evaluate([{"projektbetrag": 24_500.0}, {"projektbetrag": 5_000.0}], flowstat)
    assert [dict(s) for s in result.summary] == [
        {"code": "BL_RF01_ROUND_AMOUNT", "count": 1},
        {"code": "BL_RF02_NEAR_THRESHOLD", "count": 1},
    ]
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
