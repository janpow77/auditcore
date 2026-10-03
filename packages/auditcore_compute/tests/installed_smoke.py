"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

import datetime as dt
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_compute import engine_report, to_cents_buffer, use_python
from auditcore_compute.finance import check_quota, cofinancing, interest_cents, rate_table
from auditcore_compute.stats import deterministic_sum
from auditcore_compute.validation import double_funding, reconcile


def main() -> None:
    """Quota, interest, plausibility and statistics on the installed engine and in Python."""
    package = distribution("auditcore_compute")
    assert package.version == "0.1.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == ["numpy>=1.24"]
    assert find_spec("auditcore") is None
    eligible = to_cents_buffer(["1000.00", "333.33", "0.05"])
    split = cofinancing(eligible, "0.4")
    assert split.share.tolist() == [40000, 13333, 2]
    assert (split.share + split.rest).tolist() == eligible.tolist()
    assert check_quota(split.share, eligible, maximum="0.4").status.tolist() == [0, 0, 0]
    table = rate_table([(dt.date(2023, 1, 1), "6.62"), (dt.date(2023, 7, 1), "8.12")])
    interest = interest_cents(
        10_000_000, dt.date(2023, 3, 1), dt.date(2023, 9, 1), table, "act/360"
    )
    assert interest == 364_189, interest
    check = reconcile([100, 200], [100, 201], tolerance_cents=1)
    assert check.status.tolist() == [0, 1]
    dip = double_funding(["R1", "R1", "R2"], [5, 5, 5], ["A", "B", "A"])
    assert dip.flagged.tolist() == [True, True, False]
    total = deterministic_sum([1e16, 1.0, -1e16])
    with use_python():
        assert deterministic_sum([1e16, 1.0, -1e16]) == total == 1.0
    modes = {info.name: info.mode for info in engine_report()}
    assert set(modes.values()) <= {"jit", "numpy", "python"}
    print("PASS: installed auditcore_compute", sorted(set(modes.values())))


if __name__ == "__main__":
    main()
