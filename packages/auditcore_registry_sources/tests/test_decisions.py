"""User decisions of 23.09.2026 (R1–R8, A2, A3) as recommended profiles and contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from auditcore_harvest import AuthError, Response
from replay_support import FILES

from auditcore_registry_sources import (
    KeyCredentials,
    ListSnapshot,
    MatchClient,
    ProfileError,
    beneficial_owners,
    configuration_status,
    credentials_from_environment,
    load_lists,
    load_profile,
    parse_targets_simple_csv,
    recommended_profile,
    screen,
    sme_status,
    traverse,
    unclassified_holders,
)
from auditcore_registry_sources.lists import find_list

ROOT = Path(__file__).parents[1]
PURPOSES = {
    "sanctions_screening": "audit_designer.sanctions_screening",
    "pep_bulk": "flowinvoice.pep_bulk",
    "pep_risk": "flowsearch.pep_risk",
    "ubo": "flowsearch.ubo",
    "sme": "flowsearch.kmu",
    "company_verification": "flowinvoice.company_verification",
}


@pytest.mark.parametrize(("purpose", "profile_id"), sorted(PURPOSES.items()))
def test_recommended_profiles_are_decided_successors(purpose: str, profile_id: str) -> None:
    profile = recommended_profile(purpose)
    assert (profile.id, profile.version, profile.status) == (
        profile_id,
        "2026.09.2",
        "USER_DECIDED",
    )
    assert profile.decisions and all(d["status"] == "DECIDED" for d in profile.decisions)
    assert all(d["date"] == "2026-09-23" for d in profile.decisions)
    legacy = load_profile(profile_id, "2026.09.1")
    assert legacy.status != "USER_DECIDED"  # the characterized source profile stays as it was
    with pytest.raises(ProfileError):
        recommended_profile("unbekannt")


def test_r6_r7_keep_the_legacy_settings() -> None:
    for profile_id in ("flowsearch.pep_risk", "flowinvoice.company_verification"):
        assert dict(load_profile(profile_id, "2026.09.2").settings) == dict(
            load_profile(profile_id, "2026.09.1").settings
        )


def test_r1_r2_designer_screening_with_nfc() -> None:
    parsed = parse_targets_simple_csv(
        (FILES / "eu_fsf_targets.simple.csv").read_bytes(), list_key="eu_fsf"
    )
    lists = load_lists("audit_designer.sanctions_lists", "2026.09.1")
    snapshot = [ListSnapshot(find_list(lists, "eu_fsf"), parsed.entries, as_of="2026-09-22")]
    result = screen("Müller-Lüdenscheidt", snapshot, recommended_profile("sanctions_screening"))
    assert result.normalization["version"] == "2026.09.3"
    assert result.hits[0].raw_score == 100.0 and result.min_score == 70.0
    workshop = screen(
        "Müller-Lüdenscheidt",
        snapshot,
        load_profile("flowworkshop.sanctions_screening", "2026.09.2"),
    )
    assert workshop.hits[0].raw_score == 100.0  # 2026.09.1 gave 79.2 (no NFC)


def test_r4_ubo_gwg_voting_25_and_unknown_type() -> None:
    structure = {
        "id": "root",
        "shareholders": [
            {"name": "C", "type": "person", "share": 10.0, "voting_rights": 30.0},
            {"name": "Ohne Typ", "share": 40.0},
            {
                "id": "h",
                "name": "Holding",
                "type": "company",
                "share": 40.0,
                "has_details": True,
                "shareholders": [{"name": "D", "type": "person", "share": 70.0}],
            },
        ],
    }
    new, old = recommended_profile("ubo"), load_profile("flowsearch.ubo", "2026.09.1")
    graph = traverse(structure, new)
    assert [o.name for o in beneficial_owners(graph.nodes, new)] == ["D", "C"]  # D: 28 % mittelbar
    assert [n.name for n in unclassified_holders(graph.nodes, new)] == ["Ohne Typ"]
    legacy = traverse(structure, old)
    assert [o.name for o in beneficial_owners(legacy.nodes, old)] == ["Ohne Typ", "D"]


@pytest.mark.parametrize(
    ("company", "category", "is_sme"),
    [
        (
            {"employees": 9, "revenue": 3_000_000, "balance_sheet_total": 1_500_000},
            "Kleinstunternehmen",
            True,
        ),
        (
            {"employees": 49, "revenue": 12_000_000, "balance_sheet_total": 9_000_000},
            "Kleinunternehmen",
            True,
        ),
        (
            {"employees": 249, "revenue": 60_000_000, "balance_sheet_total": 43_000_000},
            "Mittleres Unternehmen",
            True,
        ),
        (
            {"employees": 249, "revenue": 60_000_000, "balance_sheet_total": 44_000_000},
            "Großunternehmen",
            False,
        ),
        ({"employees": 250, "revenue": 1, "balance_sheet_total": 1}, "Großunternehmen", False),
        ({"employees": 40, "revenue": 60_000_000}, "Nicht bestimmbar", None),
        ({"revenue": 1_000}, "Nicht bestimmbar", None),
    ],
)
def test_r5_sme_agvo_annex_i(company: dict[str, int], category: str, is_sme: bool | None) -> None:
    result = sme_status(company, recommended_profile("sme"))
    assert (result.category, result.is_sme) == (category, is_sme)
    assert result.notes


def test_r5_linked_and_partner_enterprises_are_aggregated() -> None:
    company = {
        "employees": 30,
        "revenue": 5_000_000,
        "balance_sheet_total": 4_000_000,
        "linked": [{"employees": 15, "revenue": 3_000_000, "balance_sheet_total": 2_000_000}],
        "partners": [
            {"employees": 20, "revenue": 10_000_000, "balance_sheet_total": 8_000_000, "share": 30}
        ],
    }
    result = sme_status(company, recommended_profile("sme"))
    assert result.employees == 51.0 and result.turnover == 11_000_000.0
    assert result.category == "Mittleres Unternehmen"
    legacy = sme_status(company, load_profile("flowsearch.kmu", "2026.09.1"))
    assert legacy.category == "Kleinunternehmen"


def test_a3_key_by_parameter_or_environment() -> None:
    assert configuration_status(credentials_from_environment({})) == "NOT_CONFIGURED"
    assert configuration_status(credentials_from_environment({"OPENSANCTIONS_API_KEY": " "})) == (
        "NOT_CONFIGURED"
    )
    creds = credentials_from_environment({"OPENSANCTIONS_API_KEY": "k-1"})
    assert configuration_status(creds) == "CONFIGURED" and "k-1" not in repr(
        configuration_status(creds)
    )
    calls = []

    class Recorder:
        def request(self, method: str, url: str, **kwargs: object) -> Response:
            calls.append(kwargs)
            return Response(200, (FILES / "opensanctions_match_pep.json").read_bytes(), {}, url)

    from auditcore_registry_sources import person_query

    client = MatchClient(Recorder(), api_key="k-2")
    assert client.status == "CONFIGURED"
    client.match({"q": person_query("Anna Beispiel")})
    assert calls[0]["headers"]["Authorization"] == "ApiKey k-2"
    missing = MatchClient(Recorder())
    assert missing.status == "NOT_CONFIGURED"
    with pytest.raises(AuthError, match="opensanctions.org/api"):
        missing.match({"q": person_query("Anna Beispiel")})
    assert KeyCredentials("x").get("anders", "api_key") is None


def test_a2_catalog_records_the_user_decision() -> None:
    catalog = json.loads((ROOT / "docs" / "source-catalog.json").read_text(encoding="utf-8"))
    by_id = {s["source_id"]: s for s in catalog["sources"]}
    for source_id in ("registry.opensanctions_lists", "registry.opensanctions_match"):
        note = by_id[source_id]["licence_access"]["note"]
        assert "CC BY-NC 4.0" in note and "abgedeckt durch Nutzung" in note
    assert "OPENSANCTIONS_API_KEY" in json.dumps(by_id["registry.opensanctions_match"])
