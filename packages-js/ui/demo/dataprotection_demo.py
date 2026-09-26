"""Demo-Daten für VVT und DSFA (erfundene Behörde, keine echten Personen).

``demo/api_server.py`` bindet die Routen unter ``/api/dataprotection`` ein
(Extra ``web`` von ``auditcore_dataprotection``). Die Person bestimmt im Demo
der Kopf ``X-Demo-Actor``; eine echte Anwendung liest Mandant und Person aus
ihrer Sitzung. Nicht für den Produktivbetrieb.

    python demo/dataprotection_demo.py --fixture test/fixtures/dataprotection-contract.json
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from auditcore_dataprotection import Actor, Permission, load_profile
from auditcore_dataprotection.memory import FixedClock, RoleAuthorizer, SequentialIds
from auditcore_dataprotection.web import (
    DataProtectionApi,
    InMemoryStorage,
    Principal,
    create_backend,
)
from auditcore_dataprotection.web.http import routes
from starlette.requests import Request
from starlette.routing import BaseRoute

TENANT = "demo"
PEOPLE = {"daten-a": "Dana A. Beispiel", "daten-b": "Bernd B. Muster"}
PROFILE = load_profile("auditcore.dsgvo", "2026.10.3")


def _who(person: str) -> Principal:
    return Principal(TENANT, Actor(person, frozenset({TENANT}), frozenset({"alle"})))


def identify(request: Request) -> Principal | None:
    """Nur Demo: Person aus dem Kopf ``X-Demo-Actor``."""
    person = request.headers.get("X-Demo-Actor", "")
    return _who(person) if person in PEOPLE else None


def _activity(key: str, name: str, referat: str, **fields: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": key,
        "name": name,
        "referat": referat,
        "ansprechperson": "Sachgebietsleitung",
        "kategorien_empfaenger": "keine",
        "drittlandtransfer": False,
        "besondere_kategorien": False,
        "daten_art10": False,
        "avv_besteht": None,
    }
    return base | fields


ACTIVITIES = [
    _activity(
        "foerderung",
        "Bewilligung von Zuwendungen",
        "Referat Z 1",
        zweck="Prüfung und Bewilligung von Förderanträgen",
        ermaechtigungsgrundlage="§ 44 LHO in Verbindung mit den Förderrichtlinien",
        kategorien_betroffene="Antragstellende, Ansprechpersonen der Begünstigten",
        kategorien_daten="Kontaktdaten, Bankverbindung, Projektangaben",
        kategorien_empfaenger="Landeshauptkasse, Prüfbehörde",
        speicherdauer="10 Jahre nach Abschluss des Vorhabens",
        loeschfrist_rechtsgrundlage="Art. 82 VO (EU) 2021/1060",
        tom="Rollenkonzept, Verschlüsselung, Protokollierung",
        anzahl_betroffene=1200,
    ),
    _activity(
        "pruefung",
        "Vorhabenprüfung mit Stichprobe",
        "Referat Z 6",
        zweck="Prüfung von Vorhaben nach Art. 77 VO (EU) 2021/1060",
        ermaechtigungsgrundlage="Art. 77, 79 VO (EU) 2021/1060",
        kategorien_betroffene="Beschäftigte der Begünstigten",
        kategorien_daten="Namen, Stundennachweise, Gehaltsangaben",
        kategorien_empfaenger="Europäische Kommission, Europäischer Rechnungshof",
        speicherdauer="5 Jahre nach Rechnungsabschluss",
        tom="Zugriff nur für das Prüfteam, Vier-Augen-Prinzip",
        auftragsverarbeiter="IT-Dienstleister des Landes",
        avv_besteht=True,
        anzahl_betroffene=300,
    ),
    _activity(
        "cloud",
        "Terminplanung über Online-Dienst",
        "Referat Z 6",
        zweck="Abstimmung von Prüfterminen",
        ermaechtigungsgrundlage="Art. 6 Abs. 1 lit. e DSGVO",
        kategorien_betroffene="Ansprechpersonen der Begünstigten",
        kategorien_daten="Name, E-Mail-Adresse",
        speicherdauer="",
        tom="=Voreinstellung des Anbieters",
        drittlandtransfer=True,
        name_empfaenger_drittland="Anbieter mit Sitz in den USA",
        besondere_kategorien=None,
    ),
]


def _content(activities: list[dict[str, object]]) -> dict[str, object]:
    return {
        "deckblatt": {
            "verantwortlicher": {"name": "Musterbehörde des Landes", "ort": "Musterstadt"},
            "dsb": {"name": "Datenschutzbeauftragte der Musterbehörde"},
        },
        "referate": ["Referat Z 1", "Referat Z 6"],
        "taetigkeiten": activities,
    }


def _survey() -> dict[str, object]:
    answers = {key: {"value": "nein"} for key in PROFILE.question_keys}
    answers["dsk_nr08_beschaeftigte"] = {"value": "ja", "justification": "Gehaltsangaben"}
    answers["edsa_04_sensible_daten"] = {"value": "ja"}
    return {
        "answers": answers,
        "scenarios": [
            {
                "dimension": "vertraulichkeit",
                "description": "Unbefugte Kenntnis von Gehaltsangaben",
                "severity": 3,
                "likelihood": 3,
                "measures": ["zugriffskontrolle", "verschluesselung"],
            }
        ],
        "necessity": "Die Stichprobe verlangt die Einsicht in Stundennachweise.",
        "proportionality": "Nur Belege der gezogenen Stichprobe werden eingesehen.",
        "dossier": {"team": "Prüfteam Z 6, DSB", "umfang": "Vorhabenprüfung 2026"},
    }


def build_api() -> DataProtectionApi:
    """Demo-Backend mit freigegebenem Verzeichnis, offenem Entwurf und zwei DSFA."""
    storage = InMemoryStorage()
    roles = RoleAuthorizer({"alle": frozenset(Permission)})
    api = DataProtectionApi(
        create_backend(PROFILE, storage, roles, clock=FixedClock(), ids=SequentialIds("demo"))
    )
    a, b = _who("daten-a"), _who("daten-b")
    first = api.save_draft(a, {"content": _content(ACTIVITIES[:2])})
    api.release_register(b, {"expected_revision": first["revision"]})
    view = api.start(a, {"activity_id": "pruefung"})
    view = api.update(a, view["id"], {"expected_revision": view["revision"], **_survey()})
    view = api.decide(
        a,
        view["id"],
        {"expected_revision": view["revision"], "decision": view["proposal"]["recommendation"]},
    )
    view = api.dpo_request(
        a,
        view["id"],
        {
            "expected_revision": view["revision"],
            "requested_from": "Datenschutzbeauftragte",
            "requested_on": date(2026, 9, 10).isoformat(),
        },
    )
    api.release(b, view["id"], {"expected_revision": view["revision"]})
    draft = api.start(a, {"activity_id": "foerderung"})
    api.update(a, draft["id"], {"expected_revision": draft["revision"], "answers": {}})
    api.save_draft(a, {"content": _content(ACTIVITIES)})
    return api


def dataprotection_routes() -> list[BaseRoute]:
    """Routen für ``Mount("/api/dataprotection", routes=...)``."""
    return list(routes(build_api(), identify))


def write_fixture(path: Path) -> None:
    """Vertragsbeispiel für die Vitest-Prüfungen der Oberfläche."""
    api = build_api()
    a = _who("daten-a")
    overview = api.overview(a)
    released = next(r["dsfa"]["id"] for r in overview["items"] if r["id"] == "pruefung")
    draft = next(r["dsfa"]["id"] for r in overview["items"] if r["id"] == "foerderung")
    data = {
        "profile": api.profile_info(),
        "register": api.register(a),
        "overview": overview,
        "released_assessment": api.assessment(a, released),
        "draft_assessment": api.assessment(a, draft),
        "proposal": api.calculate(
            {k: v for k, v in _survey().items() if k in ("answers", "scenarios")}
        ),
    }
    text = json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    write_fixture(parser.parse_args().fixture)
