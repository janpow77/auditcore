"""Characterization from actual Flowlib inputs, captured before extraction."""

import json
from pathlib import Path

import pytest

from auditcore.reporting import get_number_format

GOLDEN = json.loads(
    (Path(__file__).parent / "fixtures/flowlib-number-format-golden.json").read_text()
)


@pytest.mark.parametrize(
    "case,observed", list(zip(GOLDEN["cases"], GOLDEN["outcomes"], strict=True))
)
def test_real_flowlib_characterization(case, observed):
    try:
        result = get_number_format(*case["args"], **case["kwargs"])
        current = {"name": case["name"], "value": result, "exception": None}
    except Exception as exc:
        current = {
            "name": case["name"],
            "value": None,
            "exception": type(exc).__module__ + "." + type(exc).__qualname__,
        }
    assert current == observed
