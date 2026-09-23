"""Profiles are explicit, source-bound, fingerprinted; open decisions travel with them."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from auditcore_registry_sources import ProfileError, available_profiles, load_lists, load_profile
from auditcore_registry_sources.profiles import fingerprint, profile_from_dict

DATA = Path(__file__).parents[1] / "src" / "auditcore_registry_sources" / "profile_data"
V = "2026.09.1"
PINNED = {
    "janpow77/audit_designer": "1254591156d3bdf6ccdf4050dec7713a61ad4a20",
    "janpow77/flowworkshop": "3d1cb40221645935c323392d70d84102d05ac7bb",
    "janpow77/flowinvoice": "fb2d18568d2eaf64574d131ceae51a936b9aac02",
    "janpow77/flowsearch": "10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4",
}


def test_all_profiles_load_and_are_bound_to_pinned_sources() -> None:
    assert len(available_profiles()) == 13
    for profile_id, version in available_profiles():
        profile = load_profile(profile_id, version)
        assert profile.source["commit"] == PINNED[profile.source["repository"]]
        assert profile.source["rights"] == "USER_AUTHORIZED_MIT"
        assert len(profile.fingerprint) == 64
        assert profile.reference["status"] == profile.status


def test_contradictory_variants_are_marked() -> None:
    for profile_id in (
        "flowsearch.ubo",
        "flowsearch.kmu",
        "flowinvoice.sanctions_local",
        "flowinvoice.pep_bulk",
        "flowsearch.pep_risk",
        "flowinvoice.company_verification",
        "flowworkshop.sanctions_screening",
        "audit_designer.sanctions_screening",
    ):
        decisions = load_profile(profile_id, V).decisions
        assert decisions and all(d["status"] == "HUMAN_DECISION_REQUIRED" for d in decisions)
    assert load_profile("flowinvoice.sanctions_network", V).status == "LEGACY_ONLY"


def test_data_licence_is_separate_from_code_licence() -> None:
    for catalog in ("audit_designer.sanctions_lists", "flowworkshop.sanctions_lists"):
        for item in load_lists(catalog, V):
            assert item.provider == "OpenSanctions"
            assert "CC BY-NC 4.0" in item.data_licence["note"]
            assert item.data_licence["status"] == "REVIEW_REQUIRED"
    claimed = {
        i.key: i.licence_claimed_in_source for i in load_lists("audit_designer.sanctions_lists", V)
    }
    assert claimed["eu_fsf"] == "CC BY 4.0"  # stated by the source for the original list


def test_workshop_list_keys_map_to_current_datasets() -> None:
    lists = {i.key: i for i in load_lists("flowworkshop.sanctions_lists", V)}
    assert lists["gb_hmt_sanctions"].url.endswith("/gb_fcdo_sanctions/targets.simple.csv")


def test_fingerprint_changes_and_validation() -> None:
    data = json.loads((DATA / f"audit_designer.sanctions_screening-{V}.json").read_text())
    before = fingerprint(data)
    data["settings"]["default_min_score"] = 71
    assert fingerprint(data) != before
    for broken in (
        {**data, "schema": "x"},
        {**data, "kind": "x"},
        {**data, "status": "x"},
        {**data, "settings": {}},
        {**data, "source": {"repository": "x"}},
        {k: v for k, v in data.items() if k != "legal_status"},
    ):
        with pytest.raises(ProfileError):
            profile_from_dict(broken)
    with pytest.raises(ProfileError):
        load_profile("audit_designer.sanctions_screening", "1999.01.1")
    with pytest.raises(ProfileError):
        load_profile("../x", V)
    profile = load_profile("flowsearch.kmu", V)
    with pytest.raises(ProfileError):
        profile.setting("fehlt")
    with pytest.raises(ProfileError):
        profile.require_kind("screening")
