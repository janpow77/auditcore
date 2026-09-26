"""Packaged profiles are exactly the recorded source constants; no hidden default."""

from __future__ import annotations

import json

import pytest
from conftest import load, revive

from auditcore_funding_sources import profiles
from auditcore_funding_sources.errors import ProfileError


def test_available_profiles() -> None:
    assert profiles.available_profiles() == (
        ("designer.deminimis.authority_levels", "2026.09.1"),
        ("designer.deminimis.cumulation", "2026.09.1"),
        ("designer.state_aid", "2026.09.1"),
        ("flowworkshop.beneficiaries", "2026.09.1"),
    )


def test_workshop_profile_equals_recorded_constants() -> None:
    constants = revive(load("flowworkshop")["constants"])
    data = profiles.load_profile("flowworkshop.beneficiaries")
    assert dict((role, p) for role, p in data["column_patterns"]) == constants["column_patterns"]
    assert data["hash_fields"] == constants["hash_fields"]
    assert data["nameless"] == constants["nameless"]
    assert data["default_mode"] == "snapshot"
    assert data["legal_suffixes"] == constants["legal_suffixes"]


def test_designer_profiles_equal_recorded_constants() -> None:
    constants = revive(load("designer")["constants"])
    rules = profiles.load_profile("designer.deminimis.authority_levels")["rules"]
    assert rules == constants["authority_rules"]
    cumulation = profiles.load_profile("designer.deminimis.cumulation")
    assert cumulation["ceiling_eur"] == constants["ceiling_general"]
    assert cumulation["types_without_ceiling"] == constants["types_without_ceiling"]
    names = profiles.load_profile("designer.state_aid")
    assert names["legal_suffixes"] == constants["sa_legal_suffixes"]


def test_fingerprint_changes_with_content() -> None:
    data = profiles.load_profile("flowworkshop.beneficiaries")
    raw = {k: v for k, v in data.items() if k != "fingerprint"}
    assert profiles.fingerprint(raw) == data["fingerprint"]
    assert profiles.fingerprint({**raw, "hash_fields": []}) != data["fingerprint"]


@pytest.mark.parametrize("name", ["../x", "unbekannt", ".hidden", "a/b"])
def test_unknown_or_unsafe_profile_names_are_rejected(name: str) -> None:
    with pytest.raises(ProfileError):
        profiles.load_profile(name)


def test_profiles_are_json_data() -> None:
    from importlib import resources

    for entry in resources.files("auditcore_funding_sources.data").iterdir():
        if entry.name.endswith(".json"):
            assert json.loads(entry.read_text(encoding="utf-8"))["source"]["commit"]
