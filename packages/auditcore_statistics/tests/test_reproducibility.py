"""Framework T-31 (F-17): identical data and version give identical, self-describing results."""

from __future__ import annotations

import json
import random

from auditcore_statistics import METHOD, __version__, benford_test


def test_repeated_analysis_is_identical_and_names_method_version_and_parameters() -> None:
    rng = random.Random(9)
    values = [round(rng.lognormvariate(6, 2), 2) for _ in range(2000)]
    first = benford_test(values, digits=2, short_values="exclude", significance_level=0.01)
    second = benford_test(list(values), digits=2, short_values="exclude", significance_level=0.01)
    assert first == second
    data = first.to_dict()
    assert data["library"] == f"auditcore_statistics {__version__}" and data["method"] == METHOD
    assert (data["digits"], data["short_values"], data["significance_level"]) == (
        2,
        "exclude",
        0.01,
    )
    assert json.dumps(data, sort_keys=True) == json.dumps(second.to_dict(), sort_keys=True)
