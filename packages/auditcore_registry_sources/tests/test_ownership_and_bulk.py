"""UBO/SME profiles with their open decisions, cycle guard and flowinvoice bulk variants."""

from __future__ import annotations

import pytest
from replay_support import FILES

from auditcore_registry_sources import (
    QueryError,
    beneficial_owners,
    load_profile,
    local_screen,
    ownership_chain,
    parse_targets_simple_csv,
    pep_bulk_screen,
    sme_status,
    traverse,
    xml_entries,
)

UBO = load_profile("flowsearch.ubo", "2026.09.1")
KMU = load_profile("flowsearch.kmu", "2026.09.1")


def test_ubo_rules_and_decisions() -> None:
    structure = {
        "id": "root",
        "name": "Ziel GmbH",
        "shareholders": [
            {"name": "A", "type": "person", "share": 30.0},
            {"name": "B", "type": "person", "share": 25.0},
            {"name": "C", "type": "person", "share": 10.0, "voting_rights": 30.0},
            {
                "id": "h",
                "name": "Holding",
                "type": "company",
                "share": 40.0,
                "has_details": True,
                "shareholders": [{"name": "D", "type": "person", "share": 80.0}],
            },
        ],
    }
    graph = traverse(structure, UBO)
    owners = beneficial_owners(graph.nodes, UBO)
    assert [(o.name, round(o.effective_share, 2)) for o in owners] == [("D", 32.0), ("A", 30.0)]
    # C holds 30 % voting rights: GwG would count it, the source profile needs > 50 %.
    assert UBO.status == "HUMAN_DECISION_REQUIRED"
    assert {d["subject"] for d in UBO.decisions} == {
        "Stimmrechte",
        "Mittelbare Beteiligung",
        "Fehlender Typ",
    }
    chain = ownership_chain(graph, "D")
    assert [n.name for n in chain.nodes] == ["Holding", "D"] and chain.cycle is None


def test_reg_c12_ownership_chain_stops_at_a_cycle() -> None:
    graph = traverse(
        {
            "id": "x",
            "name": "X",
            "shareholders": [
                {
                    "id": "x",
                    "name": "X",
                    "type": "company",
                    "share": 50.0,
                    "has_details": True,
                    "shareholders": [],
                }
            ],
        },
        UBO,
    )
    assert graph.self_references == ["x"]
    chain = ownership_chain(graph, "x")
    assert chain.cycle == "x" and len(chain.nodes) == 1


def test_sme_profile_is_legacy_with_open_decision() -> None:
    result = sme_status(
        {"employees": 9, "revenue": 3_000_000, "balance_sheet_total": 1_500_000}, KMU
    )
    assert result.category == "Kleinunternehmen"  # Anhang I AGVO would allow the balance sheet
    assert result.status == "HUMAN_DECISION_REQUIRED" and result.decisions


def test_local_and_pep_bulk_variants() -> None:
    entries = xml_entries(
        (FILES / "eu_fsf_export.xml").read_bytes(), format="eu_fsf_xml", list_key="eu_fsf"
    ).entries
    profile = load_profile("flowinvoice.sanctions_local", "2026.09.1")
    result = local_screen("iwan musterow", entries, profile)
    assert result.status == "HITS" and result.hits[0].matched_name == "Wanja Musterow"
    assert local_screen("x y z", (), profile).status == "NOT_SEARCHED"
    with pytest.raises(QueryError):
        local_screen("  ", entries, profile)
    peps = parse_targets_simple_csv(
        (FILES / "peps_targets.simple.csv").read_bytes(), list_key="peps"
    )
    pep = load_profile("flowinvoice.pep_bulk", "2026.09.1")
    found = pep_bulk_screen("Erika Musterfrau", peps.entries, pep, country="DE", as_of="2026-09-22")
    assert found.hits[0].via_alias and found.hits[0].score == 1.0 and found.as_of == "2026-09-22"
    # REG-C13: no data is "not searched", not "clean".
    assert pep_bulk_screen("Erika Beispiel", (), pep).status == "NOT_SEARCHED"
    assert [i.reason for i in peps.issues] == ["Name fehlt"]
