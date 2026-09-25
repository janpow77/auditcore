"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

import math
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_statistics import (
    benford_test,
    chi2_survival,
    legacy_flowinvoice_benford,
    legacy_run_benford,
)


def main() -> None:
    """Benford analysis, chi-square p-value and the legacy contract from the installed package."""
    package = distribution("auditcore_statistics")
    assert package.version == "0.3.2"
    runtime = [r for r in package.requires or [] if "extra ==" not in r]
    assert runtime == ["auditcore_common==0.1.0"], runtime
    assert find_spec("auditcore") is None
    result = benford_test([123, 187, 2450, 31, 4.2, 1.9, 0, None], digits=1)
    assert result.analysed == 6 and result.zero == 1 and result.missing == 1
    assert result.rows[0].observed_count == 3 and result.deviates_at_level is None
    assert math.isclose(chi2_survival(15.507313055865453, 8), 0.05, rel_tol=1e-9)
    legacy = legacy_run_benford([1, 2, 3, 5, 9, 12], dtype="int", digit=1, column="x")
    assert legacy["meta"]["sample_size"] == 6 and legacy["meta"]["analysis"] == "core_benford"
    small = legacy_flowinvoice_benford([123, 0, None, "45.6"])
    assert small["sample_size"] == 2 and small["sample_size_sufficient"] is False
    print("PASS: installed auditcore_statistics Benford and chi-square contract")


if __name__ == "__main__":
    main()
