"""Invariants of docs/spezifikation.md as Hypothesis properties (I1–I11)."""

from __future__ import annotations

import string

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from auditcore_entity_matching import (
    PAIR_SCORERS,
    Candidate,
    ProfileError,
    available_profiles,
    best_match,
    check_lei,
    classify,
    extract_lei,
    is_lei_format,
    lei_check_digits,
    lei_checksum_ok,
    load_profile,
    normalize,
    pair_score,
)
from auditcore_entity_matching.profiles import fingerprint

PROFILES = [load_profile(i, v) for i, v in available_profiles()]
NORMALIZING = [p for p in PROFILES if p.normalization is not None]
IDEMPOTENT = [p for p in NORMALIZING if p.normalization.algorithm != "translate_then_casefold"]
TOKEN_BASED = [p for p in NORMALIZING if p.normalization.algorithm != "nfkd_lower_regex"]
CLASSIFYING = [p for p in PROFILES if p.classification is not None]
RESOLVING = [p for p in PROFILES if p.resolution is not None]
ORDER = {"low": 0, "medium": 1, "high": 2, "exact": 3}

ALPHABET = string.ascii_letters + string.digits + " .,-&'/()" + "äöüÄÖÜßéÉøØłæœçñ" + "\u0308"
NAMES = st.text(alphabet=ALPHABET, max_size=40) | st.text(max_size=20)
ALNUM = string.ascii_uppercase + string.digits
LEI_PREFIX = st.text(alphabet=ALNUM, min_size=18, max_size=18)
SCORE = st.floats(min_value=0, max_value=100, allow_nan=False)
EXAMPLES = settings(max_examples=150, deadline=None)


@EXAMPLES
@given(NAMES, st.sampled_from(NORMALIZING), st.booleans())
def test_i1_normalize_is_deterministic_text(name: str, profile, drop: bool) -> None:
    """I1: same text and profile give the same string; None and "" give ""."""
    first = normalize(name, profile, drop_filler=drop)
    assert isinstance(first, str)
    assert first == normalize(name, profile, drop_filler=drop)
    assert normalize(None, profile) == normalize("", profile) == ""


@EXAMPLES
@given(NAMES, st.sampled_from(IDEMPOTENT))
def test_i2_normalize_is_idempotent(name: str, profile) -> None:
    """I2: normalising a comparison form again does not change it (not translate_then_casefold)."""
    once = normalize(name, profile)
    assert normalize(once, profile) == once


def test_i2_translate_then_casefold_is_not_idempotent_legacy() -> None:
    """I2 (Befund): the state-aid table runs before case folding, so É → é → e."""
    profile = load_profile("flowworkshop.state_aid", "2026.09.1")
    assert normalize("É", profile) == "é"
    assert normalize("é", profile) == "e"


@EXAMPLES
@given(NAMES, st.sampled_from(NORMALIZING))
def test_i3_comparison_form_has_single_spaces_and_no_upper_case(name: str, profile) -> None:
    """I3: no leading, trailing or repeated whitespace; nothing left to lower-case."""
    result = normalize(name, profile)
    assert result == " ".join(result.split())
    assert result == result.lower()


@EXAMPLES
@given(NAMES, st.sampled_from(TOKEN_BASED), st.booleans())
def test_i4_legal_form_tokens_are_removed(name: str, profile, drop: bool) -> None:
    """I4: no token of the result is a legal-form token (filler words with drop_filler)."""
    rules = profile.normalization
    for token in normalize(name, profile, drop_filler=drop).split():
        compact = token.replace(".", "").replace("-", "") if rules.compact_tokens else token
        assert compact not in rules.legal_suffixes
        if drop:
            assert compact not in rules.filler_words


@EXAMPLES
@given(LEI_PREFIX, st.sampled_from(["", " ", "  "]), st.booleans())
def test_i5_generated_check_digits_make_a_valid_lei(prefix: str, pad: str, lower: bool) -> None:
    """I5: prefix + lei_check_digits is valid, also with case and surrounding blanks."""
    lei = prefix + lei_check_digits(prefix)
    written = pad + (lei.lower() if lower else lei) + pad
    result = check_lei(written)
    assert result.valid and result.normalized == lei
    assert extract_lei(f"LEI {lei} laut Register") == lei


@EXAMPLES
@given(st.text(max_size=30) | st.text(alphabet=ALNUM, min_size=20, max_size=20))
def test_i6_valid_implies_format_and_checksum(value: str) -> None:
    """I6: valid ⇔ format and MOD 97-10; is_lei_format never needs check digits."""
    result = check_lei(value)
    assert result.valid == (result.format_ok and result.checksum_ok)
    assert result.format_ok == is_lei_format(value)
    if result.valid:
        assert lei_checksum_ok(str(result.normalized))


@EXAMPLES
@given(st.text(alphabet=ALNUM + " -:", max_size=60))
def test_i7_extracted_lei_has_correct_check_digits(text: str) -> None:
    """I7: extract_lei returns None or a token with correct check digits."""
    found = extract_lei(text)
    assert found is None or check_lei(found).valid
    loose = extract_lei(text, require_checksum=False)
    assert loose is None or is_lei_format(loose)


@EXAMPLES
@given(SCORE, SCORE, st.sampled_from(CLASSIFYING))
def test_i8_score_class_is_monotone(a: float, b: float, profile) -> None:
    """I8: a higher score never yields a lower class."""
    low, high = sorted((a, b))
    assert ORDER[classify(low, profile)] <= ORDER[classify(high, profile)]


@EXAMPLES
@given(NAMES, NAMES, st.sampled_from(sorted(PAIR_SCORERS)))
def test_i9_pair_score_is_bounded_and_reflexive(left: str, right: str, scorer: str) -> None:
    """I9: 0 ≤ score ≤ 100; a non-empty name scores 100 against itself."""
    assert 0 <= pair_score(left, right, scorer) <= 100
    if left.strip():
        assert pair_score(left, left, scorer) == 100
    if scorer != "WRatio":
        assert pair_score(left, right, scorer) == pair_score(right, left, scorer)


@EXAMPLES
@given(
    st.text(alphabet="abcdefg ", max_size=20),
    st.lists(st.text(alphabet="abcdefg ", max_size=20), max_size=6),
    SCORE,
    SCORE,
    st.sampled_from(RESOLVING),
)
def test_i10_best_match_respects_the_explicit_threshold(
    query: str, names: list[str], a: float, b: float, profile
) -> None:
    """I10: rounded score ≥ rounded min_score; raising the threshold never creates a match."""
    candidates = [Candidate(i, n) for i, n in enumerate(names)]
    low, high = sorted((a, b))
    loose = best_match(query, candidates, profile, min_score=low)
    strict = best_match(query, candidates, profile, min_score=high)
    for result, limit in ((loose, low), (strict, high)):
        if result is not None:
            assert round(limit, 1) <= result.score <= 100
            assert result.candidate_id in range(len(names))
            assert result.profile == profile.reference
    if loose is None:
        assert strict is None


def test_i10_returned_score_is_rounded_to_one_decimal() -> None:
    """I10 (Befund): the rounded score may lie up to 0.05 below an unrounded min_score."""
    profile = load_profile("flowworkshop.entity_resolution", "2026.09.1")
    threshold = 100 * 10 / 11  # WRatio of the two names below
    result = best_match("abcdefghijk", [Candidate(1, "abcdefghijz")], profile, min_score=threshold)
    assert result is not None and result.score == 90.9 < threshold


@EXAMPLES
@given(st.text(max_size=30), st.text(max_size=12))
def test_i11_only_packaged_profiles_load(profile_id: str, version: str) -> None:
    """I11: unknown id/version raises ProfileError; packaged ones carry their fingerprint."""
    assume((profile_id, version) not in available_profiles())
    with pytest.raises(ProfileError):
        load_profile(profile_id, version)


def test_i11_packaged_profiles_are_identified() -> None:
    """I11: every packaged profile loads under its own id/version and hash."""
    for (profile_id, version), profile in zip(available_profiles(), PROFILES, strict=True):
        assert (profile.id, profile.version) == (profile_id, version)
        assert load_profile(profile_id, version) == profile
        assert len(profile.fingerprint) == 64
    assert fingerprint({"a": 1}) == fingerprint({"a": 1})
