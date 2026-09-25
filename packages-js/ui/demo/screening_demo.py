"""Demo-Daten der Screening-Trefferprüfung, ausschließlich erfundene Personen.

``demo/api_server.py`` bindet die Routen unter ``/api/screening`` ein
(Extra ``web`` von ``auditcore_registry_sources``). Die Person bestimmt im
Demo der Kopf ``X-Demo-Actor``; eine echte Anwendung liest sie aus ihrer
Sitzung. Nicht für den Produktivbetrieb.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from auditcore_registry_sources import ListEntry, ListSnapshot, SanctionsList, load_lists
from auditcore_registry_sources.lists import find_list
from auditcore_registry_sources.web import (
    Actor,
    InMemoryReviewStore,
    ScreeningReviewService,
    StaticSnapshotProvider,
)
from auditcore_registry_sources.web.http import create_routes
from starlette.requests import Request
from starlette.routing import BaseRoute

PEOPLE = {"pruefer-a": "Prüferin A. Beispiel", "pruefer-b": "Prüfer B. Muster"}
LISTS = load_lists("audit_designer.sanctions_lists", "2026.09.1")
PEPS = SanctionsList(
    "peps",
    None,
    "Politisch exponierte Personen (Demobestand)",
    "Demodaten",
    "",
    "opensanctions_targets_simple_csv",
    "Demodaten",
    None,
    {"status": "SYNTHETIC", "note": "Erfundene Demodaten."},
)


def _e(key: str, entry_id: str, name: str, **fields: str | tuple[str, ...]) -> ListEntry:
    return ListEntry(list_key=key, entry_id=entry_id, name=name, **fields)  # type: ignore[arg-type]


def snapshots(now: datetime) -> list[tuple[str, ListSnapshot]]:
    fresh = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    old = (now - timedelta(days=45)).strftime("%Y-%m-%d")
    eu = (
        _e(
            "eu_fsf",
            "EU-DEMO-0001",
            "Maximilian Beispielmann",
            schema="Person",
            aliases=("Max Beispielmann", "Maksim Bejspilman"),
            birth_date="1970-03-14",
            countries="de",
            addresses="Musterstraße 1, 12345 Musterstadt",
            sanctions="Beispielverordnung (EU) 0000/00, Anhang I",
            program_ids="EU-DEMO-A",
        ),
        _e(
            "eu_fsf",
            "EU-DEMO-0002",
            "Erika Probe-Muster",
            schema="Person",
            birth_date="1965-07-02",
            countries="at",
            addresses="Beispielgasse 7, 1000 Musterwien",
        ),
        _e(
            "eu_fsf",
            "EU-DEMO-0003",
            "Beispiel Handels GmbH",
            schema="Organization",
            countries="de",
            identifiers="HRB 00000 (Demo)",
        ),
        _e(
            "eu_fsf",
            "EU-DEMO-0004",
            "Maximiliane Beispiel",
            schema="Person",
            birth_date="1988",
            countries="ch",
        ),
    )
    un = (
        _e(
            "un_sc",
            "UN-DEMO-001",
            "Maximilian Beispielman",
            schema="Person",
            birth_date="1971",
            countries="ru",
            sanctions="Resolution 0000 (Demo)",
        ),
    )
    gb = (
        _e(
            "gb_fcdo_sanctions",
            "GB-DEMO-01",
            "Erika Mustermann-Probe",
            schema="Person",
            birth_date="1965",
            countries="gb",
        ),
    )
    peps = (
        _e(
            "peps",
            "PEP-DEMO-1",
            "Petra Musterfrau",
            schema="Person",
            aliases=("Petra Muster-Frau",),
            countries="de",
            sanctions="Mitglied eines Landesparlaments (erfunden)",
            first_seen="2021-04-01",
        ),
        _e(
            "peps",
            "PEP-DEMO-2",
            "Paul Beispiel",
            schema="Person",
            countries="at",
            sanctions="Bürgermeister (erfunden)",
        ),
    )
    return [
        ("sanctions", ListSnapshot(find_list(LISTS, "eu_fsf"), eu, as_of=fresh)),
        ("sanctions", ListSnapshot(find_list(LISTS, "un_sc"), un, as_of=fresh)),
        ("sanctions", ListSnapshot(find_list(LISTS, "gb_fcdo_sanctions"), gb, as_of=old)),
        ("sanctions", ListSnapshot(find_list(LISTS, "us_ofac_sdn"), ())),
        ("pep", ListSnapshot(PEPS, peps, as_of=fresh)),
    ]


def identify(request: Request) -> Actor | None:
    """Demo only: the actor comes from a header, a real consumer uses its session."""
    actor_id = request.headers.get("x-demo-actor", "")
    return Actor(actor_id, PEOPLE[actor_id]) if actor_id in PEOPLE else None


def build_service() -> ScreeningReviewService:
    now = datetime.now(UTC)
    service = ScreeningReviewService(
        StaticSnapshotProvider(snapshots(now)),
        InMemoryReviewStore(),
        four_eyes_outcomes=["confirmed"],
        stale_after_days=7,
    )
    service.create_run(
        {
            "kind": "sanctions",
            "profile": {"id": "audit_designer.sanctions_screening", "version": "2026.09.2"},
            "case_reference": "Vorgang 2026/0815 – Auftragnehmer Los 2 (Demo)",
            "subjects": [
                {
                    "name": "Maximilian Beispielmann",
                    "birth_date": "1970-03-14",
                    "country": "de",
                    "reference": "Geschäftsführer",
                },
                {
                    "name": "Erika Probe Muster",
                    "birth_date": "1965",
                    "country": "at",
                    "reference": "Prokuristin",
                },
                {"name": "Beispiel Handels GmbH", "schema": "Organization"},
            ],
        },
        Actor("pruefer-a", PEOPLE["pruefer-a"]),
    )
    return service


def screening_routes() -> list[BaseRoute]:
    """Routen des Vertrags screening_review/1 mit einem vorbereiteten Demo-Prüflauf."""
    return list(create_routes(build_service(), identify))
