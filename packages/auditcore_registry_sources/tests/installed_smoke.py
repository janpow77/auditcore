"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from dataclasses import replace
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_registry_sources import (
    DependencyError,
    ListEntry,
    ListSnapshot,
    SanctionsList,
    available_profiles,
    beneficial_owners,
    load_lists,
    load_profile,
    parse_register_rows,
    parse_response,
    parse_targets_simple_csv,
    screen,
    traverse,
    verify_company,
    xml_entries,
)
from auditcore_registry_sources.chambers import parse_ihk_locations
from auditcore_registry_sources.lists import find_list
from auditcore_registry_sources.web import (
    Actor,
    InMemoryReviewStore,
    ScreeningReviewService,
    StaticSnapshotProvider,
)

CSV = (
    '"id","schema","name","aliases","birth_date","countries"\n'
    '"demo-1","Organization","Müller-Lüdenscheidt Handels GmbH","MLH GmbH","","de"\n'
    '"","Person","Ohne Kennung","","",""\n'
).encode()


def main() -> None:
    """Exercise parsing, profiles, the screening boundary, API/register parsing and UBO."""
    package = distribution("auditcore_registry_sources")
    assert package.version == "0.2.3"
    required = sorted(r for r in package.requires or [] if "extra ==" not in r)
    assert required == [
        "auditcore_common==0.2.0",
        "auditcore_entity_matching==0.2.4",
        "auditcore_harvest==0.1.3",
    ], required
    assert find_spec("auditcore") is None
    assert len(available_profiles()) == 20
    parsed = parse_targets_simple_csv(CSV, list_key="eu_fsf")
    assert len(parsed.entries) == 1 and parsed.issues[0].reason == "Kennung fehlt"
    lists = load_lists("audit_designer.sanctions_lists", "2026.09.1")
    snapshot = ListSnapshot(find_list(lists, "eu_fsf"), parsed.entries, as_of="2026-09-22")
    profile = load_profile("audit_designer.sanctions_screening", "2026.09.1")
    if find_spec("rapidfuzz") is None:
        try:
            screen("Mueller Luedenscheidt", [snapshot], profile)
        except DependencyError:
            pass
        else:
            raise AssertionError("Screening must require the optional extra 'fuzzy'")
    else:
        result = screen("Mueller Luedenscheidt", [snapshot], profile)
        assert result.status == "HITS" and result.hits[0].raw_score == 100.0
    if find_spec("defusedxml") is None:
        try:
            xml_entries(b"<export/>", format="eu_fsf_xml", list_key="eu_fsf")
        except DependencyError:
            pass
        else:
            raise AssertionError("XML must require the optional extra 'xml'")
    answer = parse_response(
        b'{"responses": {"q": {"results": [{"id": "x", "score": 0.9, "properties": {}}], '
        b'"total": {"value": 1}}}}'
    )
    assert answer["q"].candidates[0].score == 0.9
    company = load_profile("flowinvoice.company_verification", "2026.09.1")
    register = parse_register_rows(
        b'{"rows": [{"name": "Beispiel GmbH", "current_status": "in Liquidation"}]}', company
    )
    assert verify_company("Beispiel GmbH", company, register=register).indicators == (
        "COMPANY_DISSOLVED",
    )
    ubo = load_profile("flowsearch.ubo", "2026.09.1")
    graph = traverse(
        {"id": "r", "shareholders": [{"name": "P", "type": "person", "share": 30}]}, ubo
    )
    assert [n.name for n in beneficial_owners(graph.nodes, ubo)] == ["P"]
    chambers = parse_ihk_locations(b'[{"name": "IHK Beispiel", "zip": "60313", "geodata": [1, 2]}]')
    assert chambers.records[0]["lat"] == 1.0
    review_smoke(parsed.entries)
    print("PASS: installed auditcore_registry_sources parsing, profiles, screening boundary")


def review_smoke(entries: tuple[ListEntry, ...]) -> None:
    """Framework-free review API: PEP run (no extra needed), decision, log."""
    peps = SanctionsList("peps", None, "PEP (Rauchtest)", "Test", "", "csv", "Test", None, {})
    pep_entries = tuple(replace(e, list_key="peps") for e in entries)
    service = ScreeningReviewService(
        StaticSnapshotProvider([("pep", ListSnapshot(peps, pep_entries, as_of="2026-09-22"))]),
        InMemoryReviewStore(),
    )
    actor = Actor("rauchtest")
    run = service.create_run(
        {
            "kind": "pep",
            "profile": {"id": "flowinvoice.pep_bulk", "version": "2026.09.2"},
            "subjects": [{"name": "Müller-Lüdenscheidt Handels GmbH"}],
        },
        actor,
    )
    hit = run["subjects"][0]["hits"][0]
    assert hit["breakdown"]["consistent"] is True
    decided = service.decide(
        run["run_id"], hit["hit_id"], {"outcome": "dismissed", "reason": "Rauchtest"}, actor
    )
    assert decided["review"]["status"] == "dismissed"
    assert len(service.log(run["run_id"])["events"]) == 2
    assert find_spec("starlette") is None or create_app_available()


def create_app_available() -> bool:
    """With the extra ``web`` the Starlette adapter imports."""
    from auditcore_registry_sources.web.http import create_app

    return callable(create_app)


if __name__ == "__main__":
    main()
