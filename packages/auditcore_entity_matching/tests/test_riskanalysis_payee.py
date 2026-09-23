"""riskanalysis payee normaliser (profile ``riskanalysis.payee``) and ``pair_score``.

The fixture was produced by ``tools/capture_riskanalysis_payee.py`` from the
unchanged, blob-verified source at riskanalysis@b5c523b.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from auditcore_entity_matching import (
    PAIR_SCORERS,
    ProfileError,
    load_profile,
    normalize,
    pair_score,
)
from auditcore_entity_matching.profiles import profile_from_dict

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "riskanalysis_payee_observed.json").read_text()
)
PROFILE = load_profile("riskanalysis.payee", "2026.09.1")


def decode(value: Any) -> Any:
    if isinstance(value, dict) and value.get("$float") == "nan":
        return float("nan")
    return value


def as_source_text(value: Any) -> str | None:
    """The source calls ``str(value)`` for everything except ``None``."""
    return None if value is None else str(value)


@pytest.mark.parametrize("case", FIXTURE["normalize"], ids=lambda c: c["name"])
def test_normalisation_reproduces_the_original(case: dict[str, Any]) -> None:
    assert normalize(as_source_text(decode(case["input"])), PROFILE) == case["output"]


@pytest.mark.parametrize("case", FIXTURE["pairs"], ids=lambda c: c["name"])
def test_pair_normalisation_and_token_set_ratio(case: dict[str, Any]) -> None:
    left = normalize(as_source_text(decode(case["left"])), PROFILE)
    right = normalize(as_source_text(decode(case["right"])), PROFILE)
    assert (left, right) == (case["left_normalized"], case["right_normalized"])
    assert pair_score(left, right, "token_set_ratio") == case["token_set_ratio"]


def test_profile_patterns_equal_the_executed_source() -> None:
    rules = PROFILE.normalization
    assert rules is not None
    assert rules.algorithm == "nfkd_lower_regex"
    assert rules.nonword_pattern == FIXTURE["constants"]["nonword_pattern"]
    assert rules.removal_pattern == FIXTURE["constants"]["legal_pattern"]
    assert FIXTURE["constants"]["whitespace_pattern"] == r"\s+"
    assert PROFILE.source["commit"] == FIXTURE["source"]["commit"]
    assert PROFILE.source["git_blob"] == FIXTURE["source"]["git_blob"]


def test_umlaut_split_is_kept_as_characterized_legacy_behavior() -> None:
    assert normalize("Müller GmbH", PROFILE) == "mu ller"
    assert normalize("Mueller GmbH", PROFILE) == "mueller"
    assert normalize("Straße", PROFILE) == "straße"


def test_pattern_validation() -> None:
    data = json.loads(
        (
            Path(__file__).parents[1]
            / "src/auditcore_entity_matching/profile_data/riskanalysis.payee-2026.09.1.json"
        ).read_text()
    )
    norm = data["normalization"]
    for broken in (
        {**norm, "nonword_pattern": None},
        {**norm, "removal_pattern": "("},
        {**norm, "algorithm": "casefold_fold_nfkd"},
    ):
        with pytest.raises(ProfileError):
            profile_from_dict({**data, "normalization": broken})


def test_pair_score_requires_explicit_known_scorer_and_text() -> None:
    assert {"token_set_ratio", "WRatio"} <= PAIR_SCORERS
    assert pair_score("abc", "abc", "ratio") == 100.0
    with pytest.raises(ProfileError):
        pair_score("a", "b", "partial_ratio")
    with pytest.raises(TypeError):
        pair_score("a", None, "ratio")  # type: ignore[arg-type]
