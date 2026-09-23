"""Framework T-31 (F-17): identical data, version and profile give identical,
self-describing results (library, profile identity and every parameter)."""

from __future__ import annotations

import json

from conftest import decode, fixture

from auditcore_risk import __version__, evaluate, load_profile


def test_repeated_evaluation_is_identical_and_self_describing() -> None:
    profile = load_profile("riskanalysis.legacy", "b5c523bf7eaa")
    case = next(
        c
        for c in fixture("riskanalysis_observed.json")["cases"]
        if c["name"] == "random-20260923-007"
    )
    rows = [decode(r) for r in case["rows"]]
    first = evaluate(rows, profile, columns=case["columns"])
    second = evaluate(
        [dict(r) for r in reversed(list(reversed(rows)))], profile, columns=case["columns"]
    )
    assert json.dumps(first.to_dict(), sort_keys=True, default=str) == json.dumps(
        second.to_dict(), sort_keys=True, default=str
    )
    data = first.to_dict()
    assert data["library"] == f"auditcore_risk {__version__}"
    assert data["profile"] == {
        "id": "riskanalysis.legacy",
        "version": "b5c523bf7eaa",
        "fingerprint": profile.fingerprint,
        "status": "LEGACY_CHARACTERIZED",
    }
    # every parameter is part of the fingerprinted profile, none is implicit
    assert all(rule.params for rule in profile.rules)


def test_version_constant_matches_the_distribution_metadata() -> None:
    from auditcore_risk.engine import LIBRARY

    assert f"auditcore_risk {__version__}" == LIBRARY
