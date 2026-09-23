"""Library contract, including the corrected LEI check (EM-C01..EM-C03)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from auditcore_entity_matching import (
    Candidate,
    ProfileError,
    available_profiles,
    best_match,
    check_lei,
    classify,
    extract_lei,
    is_lei_format,
    legacy,
    lei_check_digits,
    lei_checksum_ok,
    load_profile,
    normalize,
)
from auditcore_entity_matching.profiles import fingerprint, profile_from_dict

V = "2026.09.1"
PUBLIC_LEIS = [
    "HWUPKR0MPOU8FGXBT394",
    "529900T8BM49AURSDO55",
    "5493001KJTIIGC8Y1R12",
    "7LTWFZYICNSX8D621K86",
]
DATA = Path(__file__).parents[1] / "src" / "auditcore_entity_matching" / "profile_data"


def test_em_c01_checksum_is_verified_legacy_only_checks_format() -> None:
    wrong = "7LTWFZYICNSX8D621K87"
    assert legacy.flowworkshop_is_valid_lei(wrong) is True
    assert legacy.flowworkshop_is_valid_lei("0" * 20) is True
    assert check_lei(wrong).valid is False and check_lei(wrong).format_ok is True
    assert check_lei("0" * 20).valid is False
    for lei in PUBLIC_LEIS:
        assert check_lei(lei).valid and lei_checksum_ok(lei)
        assert check_lei(f"  {lei.lower()} ").normalized == lei


def test_em_c02_extraction_skips_tokens_with_wrong_check_digits() -> None:
    text = "IDs: 7LTWFZYICNSX8D621K87, 529900T8BM49AURSDO55"
    assert legacy.flowworkshop_extract_lei_from_text(text) == "7LTWFZYICNSX8D621K87"
    assert extract_lei(text) == "529900T8BM49AURSDO55"
    assert extract_lei(text, require_checksum=False) == "7LTWFZYICNSX8D621K87"
    assert extract_lei(None) is None and extract_lei("HRB 1") is None


@pytest.mark.parametrize("prefix", [lei[:18] for lei in PUBLIC_LEIS])
def test_check_digit_generation_round_trips(prefix: str) -> None:
    lei = prefix + lei_check_digits(prefix)
    assert lei in PUBLIC_LEIS and check_lei(lei).valid


def test_check_digit_input_validation() -> None:
    with pytest.raises(ValueError):
        lei_check_digits("SHORT")
    assert is_lei_format(12345) is False and lei_checksum_ok("x") is False


def test_em_c03_variants_stay_separate() -> None:
    state_aid = load_profile("flowworkshop.state_aid", V)
    sanctions = load_profile("flowworkshop.sanctions", V)
    assert normalize("Müller GmbH", state_aid) == "mueller"
    assert normalize("Müller GmbH", sanctions) == "muller"
    assert normalize("SOCIÉTÉ", state_aid) == "société"
    assert normalize("SOCIÉTÉ", sanctions) == "societe"
    assert normalize("ACME Holding", state_aid, drop_filler=True) == "acme"


def test_profiles_are_explicit_source_bound_and_fingerprinted() -> None:
    assert available_profiles() == (
        ("audit_designer.sanctions", V),
        ("flowworkshop.entity_resolution", V),
        ("flowworkshop.sanctions", V),
        ("flowworkshop.state_aid", V),
        ("riskanalysis.payee", V),
    )
    for profile_id, version in available_profiles():
        profile = load_profile(profile_id, version)
        assert profile.status == "SOURCE_CHARACTERIZED"
        assert profile.source["rights"] == "USER_AUTHORIZED_MIT"
        assert len(profile.fingerprint) == 64
    data = json.loads((DATA / f"flowworkshop.sanctions-{V}.json").read_text())
    before = fingerprint(data)
    data["classification"]["high_from"] = 91
    assert fingerprint(data) != before


def test_profile_constants_equal_the_executed_source() -> None:
    constants = json.loads(
        (Path(__file__).parent / "fixtures" / "legacy_observed.json").read_text()
    )["constants"]
    sa = load_profile("flowworkshop.state_aid", V).normalization
    sn = load_profile("flowworkshop.sanctions", V).normalization
    ds = load_profile("audit_designer.sanctions", V).normalization
    assert sa and sn and ds
    assert sorted(sa.legal_suffixes) == constants["flowworkshop.state_aid.legal_suffixes"]
    assert sorted(sa.filler_words) == constants["flowworkshop.state_aid.filler_words"]
    assert sorted(sn.legal_suffixes) == constants["flowworkshop.sanctions.legal_suffixes"]
    assert dict(sn.fold_map) == constants["flowworkshop.sanctions.fold_map"]
    assert sorted(ds.legal_suffixes) == constants["audit_designer.sanctions.legal_suffixes"]
    assert dict(ds.fold_map) == constants["audit_designer.sanctions.fold_map"]
    resolution = load_profile("flowworkshop.entity_resolution", V).resolution
    assert resolution is not None
    assert resolution.fuzzy_threshold == constants["flowworkshop.entity_resolution.fuzzy_threshold"]
    assert resolution.lei_pattern == constants["flowworkshop.entity_resolution.lei_pattern"]


def test_profile_validation_and_lookup_errors() -> None:
    data = json.loads((DATA / f"flowworkshop.sanctions-{V}.json").read_text())
    for broken in (
        {**data, "schema": "x"},
        {**data, "normalization": {**data["normalization"], "algorithm": "x"}},
        {**data, "classification": {**data["classification"], "high_from": 99}},
        {k: v for k, v in data.items() if k not in ("normalization",)},
        {**data, "normalization": {**data["normalization"], "legal_suffixes": "gmbh"}},
    ):
        with pytest.raises(ProfileError):
            profile_from_dict(broken)
    for args in (("unknown", V), ("flowworkshop.sanctions", "0"), ("../x", V)):
        with pytest.raises(ProfileError):
            load_profile(*args)
    resolution = load_profile("flowworkshop.entity_resolution", V)
    with pytest.raises(ProfileError):
        normalize("x", resolution)
    with pytest.raises(ProfileError):
        classify(99, resolution)
    with pytest.raises(ProfileError):
        best_match(
            "abc", [Candidate(1, "abc")], load_profile("flowworkshop.sanctions", V), min_score=0
        )
    with pytest.raises(TypeError):
        normalize(123, load_profile("flowworkshop.sanctions", V))  # type: ignore[arg-type]


def test_best_match_exposes_components_and_profile() -> None:
    profile = load_profile("flowworkshop.entity_resolution", V)
    result = best_match(
        "muller logistik",
        [Candidate("a", "mueller logistik"), Candidate("b", "muller logistic")],
        profile,
        min_score=75,
    )
    assert result is not None and result.candidate_id == "a"
    assert set(result.components) == {"token_set_ratio", "WRatio"}
    assert result.score == max(round(v, 1) for v in result.components.values())
    assert result.profile["id"] == "flowworkshop.entity_resolution"
    assert best_match("muller logistik", [], profile, min_score=75) is None
    assert best_match("ab", [Candidate(1, "ab")], profile, min_score=0) is None
    raised = replace(profile.resolution, min_token_length=1)  # type: ignore[type-var]
    assert raised.min_token_length == 1


def test_classification_token_subset_is_not_exact() -> None:
    sanctions = load_profile("flowworkshop.sanctions", V)
    assert classify(100, sanctions, "putin", "vladimir vladimirovich putin") == "high"
    assert classify(100, sanctions, "vladimir putin", "putin vladimir") == "exact"
    assert classify(100, sanctions) == "exact"
    assert [classify(s, sanctions) for s in (90, 89.99, 80, 79.99)] == [
        "high",
        "medium",
        "medium",
        "low",
    ]


def test_inputs_are_not_mutated() -> None:
    candidates = [Candidate(1, "siemens")]
    before = list(candidates)
    best_match(
        "siemens", candidates, load_profile("flowworkshop.entity_resolution", V), min_score=75
    )
    assert candidates == before
