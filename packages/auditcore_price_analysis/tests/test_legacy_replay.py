"""Every observed legacy case replays exactly through ``auditcore_price_analysis.legacy``."""

from __future__ import annotations

import sys
from typing import Any

import pytest
from replay import decode, encode_result, load_fixture

from auditcore_price_analysis import legacy

FIXTURE = load_fixture()
CASES = FIXTURE["cases"]
#: errors raised by the Python interpreter itself (not by the source code); their
#: wording changed between Python versions (3.12: "can't compare datetime.datetime
#: to datetime.date", 3.13: "'>=' not supported between instances of ..."), so
#: only the exception type is part of the contract on other Python versions
INTERPRETER_MESSAGES = {"nw-stichtag-008"}


def test_fixture_is_bound_to_the_verified_source() -> None:
    assert FIXTURE["repository"] == "janpow77/regulierung"
    assert FIXTURE["commit"] == "853676d2b1ab792395d63c62c9f96d5edcca8c2d"
    assert {f["path"]: f["git_blob"] for f in FIXTURE["files"]} == {
        "backend/app/services/calculator.py": "1d40c9ef739e8933b4ec8195226f5eef117389ba",
        "backend/app/services/preisauswahl.py": "89b5cec43867794918cfcb851878eb6dfddf1abc",
    }
    assert len(CASES) == 274
    assert len({c["id"] for c in CASES}) == len(CASES)


def test_legacy_constants_match() -> None:
    constants = FIXTURE["constants"]
    assert legacy.UMLAGEN_STICHTAG.isoformat() == constants["UMLAGEN_STICHTAG"]
    assert str(legacy.CENT) == constants["CENT"] and str(legacy.ZEHNTEL) == constants["ZEHNTEL"]
    assert constants["Q3_TOLERANZ"] == legacy.Q3_TOLERANZ
    assert constants["DATENSTATUS_KEIN_Q3_TARIF"] == legacy.DATENSTATUS_KEIN_Q3_TARIF


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_exact_replay(case: dict[str, Any]) -> None:
    function = getattr(legacy, case["function"])
    try:
        observed: dict[str, Any] = {
            "ok": encode_result(function(*decode(case["args"]), **decode(case["kwargs"])))
        }
    except Exception as exc:  # noqa: BLE001 - errors are part of the legacy contract
        observed = {"error": {"type": type(exc).__name__, "message": str(exc)}}
    expected = {k: case[k] for k in ("ok", "error") if k in case}
    same_python = sys.version.split()[0].rsplit(".", 1)[0] == FIXTURE["python"].rsplit(".", 1)[0]
    if case["id"] in INTERPRETER_MESSAGES and not same_python:
        assert observed["error"]["type"] == expected["error"]["type"]
        return
    assert observed == expected
