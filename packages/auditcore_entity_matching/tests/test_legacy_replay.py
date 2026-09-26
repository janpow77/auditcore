"""Every recorded original output is reproduced exactly by the legacy adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from auditcore_entity_matching import legacy

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "legacy_observed.json").read_text())
CASES = FIXTURE["cases"]


def run(case: dict[str, Any]) -> Any:
    op, i = case["operation"], case["inputs"]
    if op == "state_aid_normalize":
        return legacy.flowworkshop_normalize_company_name(i["text"])
    if op == "state_aid_normalize_filler":
        return legacy.flowworkshop_normalize_company_name(i["text"], drop_filler=True)
    if op == "sanctions_normalize":
        return legacy.flowworkshop_normalize_name(i["text"])
    if op == "designer_normalize":
        return legacy.designer_normalisiere_name(i["text"])
    if op == "is_valid_lei":
        return legacy.flowworkshop_is_valid_lei(i["value"])
    if op == "extract_lei":
        return legacy.flowworkshop_extract_lei_from_text(i["value"])
    if op == "sanctions_classify":
        return legacy.flowworkshop_classify(i["score"], i.get("q_norm"), i.get("matched_norm"))
    if op == "designer_classify":
        return legacy.designer_klassifiziere(i["score"], i.get("q_norm"), i.get("matched_norm"))
    if op == "fuzzy_best":
        found = legacy.flowworkshop_fuzzy_best(
            i["query"], [tuple(c) for c in i["candidates"]], min_score=i["min_score"]
        )
        return None if found is None else list(found)
    raise AssertionError(op)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_original_output_is_reproduced(case: dict[str, Any]) -> None:
    assert case["exception"] is None
    assert run(case) == case["output"]


def test_fixture_scope() -> None:
    assert len(CASES) == 440
    assert FIXTURE["environment"]["rapidfuzz"] == "3.10.1"
    assert {s["commit"] for s in FIXTURE["sources"]} == {
        "a05bb2143bd96d5e981f9462f05b965e1658be36",
        "030a71e083ef0feddc14545b095a4945bc0bbd7a",
    }
