"""Synthetic lists and service factory for the review API tests (no real persons)."""

from __future__ import annotations

from datetime import UTC, datetime
from itertools import count

from auditcore_registry_sources import ListEntry, ListSnapshot, SanctionsList, load_lists
from auditcore_registry_sources.lists import find_list
from auditcore_registry_sources.web import (
    Actor,
    InMemoryReviewStore,
    ScreeningReviewService,
    StaticSnapshotProvider,
)

LISTS = load_lists("audit_designer.sanctions_lists", "2026.09.1")
SANCTIONS_PROFILE = {"id": "audit_designer.sanctions_screening", "version": "2026.09.2"}
PEP_PROFILE = {"id": "flowinvoice.pep_bulk", "version": "2026.09.2"}
NOW = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

PEP_LIST = SanctionsList(
    key="peps",
    source_key=None,
    name="Politisch exponierte Personen (synthetischer Testbestand)",
    issuer="Testdaten",
    url="https://example.invalid/peps.csv",
    format="opensanctions_targets_simple_csv",
    provider="Testdaten",
    licence_claimed_in_source=None,
    data_licence={"status": "SYNTHETIC", "note": "Erfundene Testdaten."},
)

ALICE = Actor("pruefer-a", "Prüferin A")
BOB = Actor("pruefer-b", "Prüfer B")


def _entry(list_key: str, entry_id: str, name: str, **fields: object) -> ListEntry:
    return ListEntry(list_key=list_key, entry_id=entry_id, name=name, **fields)  # type: ignore[arg-type]


def sanctions_snapshots() -> list[tuple[str, ListSnapshot]]:
    eu = (
        _entry(
            "eu_fsf",
            "eu-001",
            "Maximilian Beispielmann",
            schema="Person",
            aliases=("Max Beispielmann", "Maksim Beispielman"),
            birth_date="1970-03-14",
            countries="de",
            addresses="Musterstraße 1, 12345 Musterstadt",
            sanctions="Beispielverordnung (EU) 0000/00",
            program_ids="EU-TEST-1",
        ),
        _entry("eu_fsf", "eu-002", "Erika Probe-Muster", schema="Person", birth_date="1965"),
        _entry("eu_fsf", "eu-003", "Beispiel Handels GmbH", schema="Organization"),
    )
    un = (
        _entry(
            "un_sc",
            "un-001",
            "Maximilian Beispielman",
            schema="Person",
            birth_date="1971",
            countries="ru",
        ),
    )
    return [
        ("sanctions", ListSnapshot(find_list(LISTS, "eu_fsf"), eu, as_of="2026-09-22T18:00:00Z")),
        ("sanctions", ListSnapshot(find_list(LISTS, "un_sc"), un, as_of="2026-08-01")),
        ("sanctions", ListSnapshot(find_list(LISTS, "us_ofac_sdn"), ())),
    ]


def pep_snapshots() -> list[tuple[str, ListSnapshot]]:
    entries = (
        _entry(
            "peps",
            "pep-001",
            "Petra Musterfrau",
            schema="Person",
            aliases=("Petra Muster-Frau",),
            countries="de",
            sanctions="Mitglied eines Landesparlaments (erfunden)",
        ),
        _entry("peps", "pep-002", "Paul Beispiel", schema="Person", countries="at"),
    )
    return [("pep", ListSnapshot(PEP_LIST, entries, as_of="2026-09-24"))]


def make_service(**options: object) -> ScreeningReviewService:
    ids = count(1)
    provider = StaticSnapshotProvider(sanctions_snapshots() + pep_snapshots())
    return ScreeningReviewService(
        provider,
        InMemoryReviewStore(),
        clock=lambda: NOW,
        new_id=lambda: f"run-{next(ids)}",
        **options,  # type: ignore[arg-type]
    )


def sanctions_body(**extra: object) -> dict[str, object]:
    body: dict[str, object] = {
        "kind": "sanctions",
        "profile": SANCTIONS_PROFILE,
        "subjects": [
            {"name": "Maximilian Beispielmann", "birth_date": "1970-03-14", "country": "de"},
            {"name": "Niemand Unbekannt"},
        ],
        "case_reference": "Vorgang 2026/0001 (Test)",
    }
    body.update(extra)
    return body


def pep_body(**extra: object) -> dict[str, object]:
    body: dict[str, object] = {
        "kind": "pep",
        "profile": PEP_PROFILE,
        "subjects": [{"name": "Petra Musterfrau", "country": "de"}],
    }
    body.update(extra)
    return body
