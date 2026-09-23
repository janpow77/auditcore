"""Single-value helpers the consumers need beside the frame API (RF09 score, RF08 check)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import decode, fixture

from auditcore_risk import ProfileError, identifier_missing, load_profile, name_similarity

LEGACY = load_profile("riskanalysis.legacy", "b5c523bf7eaa")
ENTITY_FIXTURE = json.loads(
    (
        Path(__file__).parents[2]
        / "auditcore_entity_matching/tests/fixtures/riskanalysis_payee_observed.json"
    ).read_text()
    if (Path(__file__).parents[2] / "auditcore_entity_matching").is_dir()
    else '{"pairs": []}'
)


def test_name_similarity_equals_original_name_match() -> None:
    rule = LEGACY.rule("RF09")
    fx = fixture("riskanalysis_observed.json")
    case = next(c for c in fx["cases"] if c["name"] == "rf09-namen")
    for row, expected in zip(case["rows"], case["name_match"], strict=True):
        row = decode(row)
        assert name_similarity(rule, row["Name"], row["zahlungsempfaenger"]) == expected
    for pair in ENTITY_FIXTURE["pairs"]:
        left, right = decode(pair["left"]), decode(pair["right"])
        assert name_similarity(rule, left, right) == pair["name_match"]


def test_identifier_missing_equals_original_placeholder_logic() -> None:
    fx = fixture("riskanalysis_observed.json")["hat_echte_vergabe"]
    rule = LEGACY.rule("RF08")
    assert [not identifier_missing(rule, v) for v in decode(fx["input"])] == fx["output"]


def test_helpers_check_the_rule_kind() -> None:
    with pytest.raises(ProfileError):
        name_similarity(LEGACY.rule("RF08"), "a", "b")
    with pytest.raises(ProfileError):
        identifier_missing(LEGACY.rule("RF09"), "0")
