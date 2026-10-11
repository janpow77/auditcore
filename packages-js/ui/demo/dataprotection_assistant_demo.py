"""Vertragsbeispiel des Datenschutz-Assistenten (erfundene Behörde, keine echten Personen).

Erzeugt die Antworten des echten Python-Backends für die Vitest-Prüfungen von
``<flowaudit-datenschutz-assistent>`` (Vue) und ``FlowauditDatenschutzAssistent``
(React). Nicht für den Produktivbetrieb.

    python demo/dataprotection_assistant_demo.py \
        --fixture ../ui-core/test/fixtures/dataprotection-assistant.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auditcore_dataprotection import Actor, Permission, load_profile
from auditcore_dataprotection.memory import FixedClock, RoleAuthorizer, SequentialIds
from auditcore_dataprotection.memory_records import (
    InMemoryOperationRepository,
    InMemoryTransferRepository,
)
from auditcore_dataprotection.web import (
    DataProtectionApi,
    InMemoryStorage,
    Principal,
    create_backend,
)

TENANT = "demo"
PROFILE = load_profile("auditcore.hdsig_ji", "2026.10.4")


def _who(person: str) -> Principal:
    return Principal(TENANT, Actor(person, frozenset({TENANT}), frozenset({"alle"})))


ACTIVITY: dict[str, object] = {
    "name": "Verfolgung von Ordnungswidrigkeiten (Demo)",
    "referat": "Referat Z 1",
    "rechtsregime": "hdsig_ji",
    "rolle": "verantwortlicher",
    "verantwortliche_stelle": "Demo-Behörde",
    "zweck": "Verfolgung und Ahndung von Ordnungswidrigkeiten nach Fachgesetz X",
    "ermaechtigungsgrundlage": "§ 1 Fachgesetz X (erfunden)",
    "kategorien_betroffene": "Betroffene des Verfahrens",
    "kategorien_daten": "Stammdaten, Verfahrensdaten",
    "kategorien_empfaenger": "Gerichte",
    "uebermittlungen": [{"empfaenger": "Amtsgericht", "rechtsgrundlage": "§ 69 OWiG"}],
    "profiling": False,
    "speicherdauer": "5 Jahre nach Abschluss",
    "tom": "Rollenkonzept, Verschlüsselung",
    "drittlandtransfer": False,
    "besondere_kategorien": False,
    "daten_art10": True,
}


def write_fixture(path: Path) -> None:
    """Übersicht vor und nach Antworten, im freien Modus und mit KI-Vorschlag."""
    api = DataProtectionApi(
        create_backend(
            PROFILE,
            InMemoryStorage(),
            RoleAuthorizer({"alle": frozenset(Permission)}),
            clock=FixedClock(),
            ids=SequentialIds("demo"),
            transfers=InMemoryTransferRepository(),
            decisions=InMemoryOperationRepository(),
        )
    )
    a = _who("daten-a")
    content = {
        "deckblatt": {"verantwortlicher": {"name": "Demo-Behörde"}, "dsb": {"name": "DSB"}},
        "referate": ["Referat Z 1"],
        "taetigkeiten": [ACTIVITY],
    }
    draft = api.save_draft(a, {"content": content})
    activity_id = str(draft["content"]["taetigkeiten"][0]["id"])  # type: ignore[index]
    fresh = api.work.overview(a, activity_id)
    api.work.answer(
        a, activity_id, {"question_id": "1.3", "value": "unklar", "expected_revision": 1}
    )
    suggested = api.work.answer(
        a,
        activity_id,
        {
            "question_id": "1.4",
            "value": "Fachanwendung, E-Mail (Vorschlag)",
            "origin": "ki_vorschlag",
            "expected_revision": 2,
        },
    )
    free = api.work.navigate(
        a, activity_id, {"mode": "frei", "step": "W07", "expected_revision": 3}
    )
    api.work.navigate(a, activity_id, {"mode": "frei", "step": "W05", "expected_revision": 4})
    table = api.work.answer(
        a, activity_id, {"question_id": "5.4", "value": "ja", "expected_revision": 5}
    )
    api.work.navigate(a, activity_id, {"mode": "frei", "step": "W03", "expected_revision": 6})
    providers = api.work.answer(
        a, activity_id, {"question_id": "3.7", "value": "ja", "expected_revision": 7}
    )
    api.work.navigate(a, activity_id, {"mode": "frei", "step": "W11", "expected_revision": 8})
    consultation = api.work.answer(
        a, activity_id, {"question_id": "11.1", "value": "ja", "expected_revision": 9}
    )
    data = {
        "activity_id": activity_id,
        "providers": providers,
        "consultation": consultation,
        "fresh": fresh,
        "suggested": suggested,
        "free": free,
        "table": table,
    }
    text = json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    write_fixture(parser.parse_args().fixture)
