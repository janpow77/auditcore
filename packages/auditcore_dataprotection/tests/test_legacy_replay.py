"""Every recorded original output is reproduced exactly by the legacy adapter."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from auditcore_dataprotection import legacy
from auditcore_dataprotection.errors import ValidationError

CASES = json.loads(
    (Path(__file__).parent / "fixtures" / "regulierung_legacy_observed.json").read_text()
)["cases"]


def _answers(raw: list[dict[str, Any]]) -> list[legacy.LegacyAnswer]:
    return [legacy.LegacyAnswer(**v) for v in raw]


def _scenarios(raw: list[dict[str, Any]]) -> list[legacy.LegacyScenario]:
    return [
        legacy.LegacyScenario(**{**v, "massnahmen": tuple(v.get("massnahmen", ()))}) for v in raw
    ]


def run(case: dict[str, Any]) -> Any:
    op, i = case["operation"], case["inputs"]
    if op == "threshold":
        return asdict(legacy.legacy_threshold(_answers(i["answers"]), i.get("regime", "dsgvo")))
    if op == "suggestion":
        return legacy.legacy_proposal(
            _answers(i["answers"]), _scenarios(i.get("scenarios", [])), i.get("regime", "dsgvo")
        )
    if op == "risk":
        return legacy.legacy_risk(_scenarios(i["scenarios"]))
    if op == "risk_level":
        return legacy.legacy_risk_level(i["value"])
    if op == "prefill":
        return legacy.legacy_prefill(i)
    if op == "answers_from_json":
        return [asdict(a) for a in legacy.legacy_answers_from_json(i)]
    if op == "scenarios_from_json":
        return [
            {**asdict(s), "massnahmen": list(s.massnahmen)}
            for s in legacy.legacy_scenarios_from_json(i)
        ]
    if op == "check_regime":
        return legacy.legacy_check_regime(i["value"])
    if op == "regime_suggestion":
        return legacy.legacy_regime_suggestion(i)
    if op == "compare_activity":
        return legacy.legacy_compare_activity(i["before"], i["after"])
    if op == "preview":
        return legacy.legacy_preview(i["antworten"], i["szenarien"], i["regime"])
    if op == "activity_identifier":
        return legacy.legacy_activity_identifier(i["name"], i["position"])
    if op == "activities_with_identifiers":
        return legacy.legacy_activities_with_identifiers(i["activities"])
    if op == "placeholders":
        return legacy.legacy_fill_placeholders(i["value"], i["values"])
    raise AssertionError(op)


def normalise(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_original_output_is_reproduced(case: dict[str, Any]) -> None:
    if case["exception"]:
        with pytest.raises(ValidationError) as caught:
            run(case)
        assert case["exception"]["type"] == "ValidationError"
        assert str(caught.value) == case["exception"]["message"]
    else:
        assert normalise(run(case)) == case["output"]


def test_catalog_json_is_reproduced(legacy: dict[str, Any]) -> None:
    assert normalise(legacy_catalog()) == legacy["catalog"]["katalog_als_json"]


def legacy_catalog() -> dict[str, Any]:
    from auditcore_dataprotection.legacy import legacy_catalog_json

    return legacy_catalog_json()


def test_fixture_covers_every_operation() -> None:
    assert len(CASES) == 241
    assert {c["operation"] for c in CASES} == {
        "threshold",
        "suggestion",
        "risk",
        "risk_level",
        "prefill",
        "answers_from_json",
        "scenarios_from_json",
        "check_regime",
        "regime_suggestion",
        "compare_activity",
        "preview",
        "activity_identifier",
        "activities_with_identifiers",
        "placeholders",
    }
