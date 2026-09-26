"""Demo-Backend und Fixture für die Vergleichsverwaltung (``<flowaudit-comparisons>``).

``demo/api_server.py`` bindet die Routen von ``auditcore_documents.web`` unter
``/api/synopsis`` ein (Extras ``docx``, ``fuzzy`` und ``web``). Alle Anfragen
gehören im Demo einer Person (``single_user``); eine echte Anwendung liest den
Eigentümer aus ihrer Sitzung. Die Beispieldateien sind synthetische
Test-Dokumente des Pakets. Nicht für den Produktivbetrieb.

    python demo/documents_demo.py --fixture ../ui-core/test/fixtures/documents-comparisons.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from auditcore_documents.web import (
    ServiceSettings,
    SynopsisService,
    Upload,
    create_app,
    single_user,
)
from starlette.routing import BaseRoute

REPO = Path(__file__).resolve().parents[3]
SYNTHETIC = REPO / "packages/auditcore_documents/tests/fixtures/synthetic"
PAIRS = (
    ("cl_rich_alt.docx", "cl_rich_neu.docx", {"title": "Prüfcheckliste – Fassungen 1 und 2"}),
    ("tx_block_alt.docx", "tx_block_neu.docx", {"mode": "text", "threshold": "90"}),
    ("al_stamm.docx", "al_befehle.docx", {"comparison_type": "article_law"}),
)


def build_service() -> SynopsisService:
    """Dienst mit 5 MiB je Datei (die Oberfläche zeigt die Grenze an)."""
    return SynopsisService(settings=ServiceSettings(max_upload_bytes=5 * 1024 * 1024))


def comparison_routes() -> list[BaseRoute]:
    """Routen für ``/api/synopsis``, vorbefüllt mit drei Vergleichen."""
    service = build_service()
    for old, new, fields in PAIRS:
        uploads = [Upload(name, (SYNTHETIC / name).read_bytes()) for name in (old, new)]
        service.create("local", uploads[0], uploads[1], fields)
    return list(create_app(service, identify=single_user).routes)


def _files(old: str, new: str) -> dict[str, tuple[str, bytes, str]]:
    kind = "application/octet-stream"
    return {
        "old_file": (old, (SYNTHETIC / old).read_bytes(), kind),
        "new_file": (new, (SYNTHETIC / new).read_bytes(), kind),
    }


def _create(client: Any, old: str, new: str, fields: dict[str, str]) -> dict[str, Any]:
    response = client.post("/comparisons", files=_files(old, new), data=fields)
    response.raise_for_status()
    body: dict[str, Any] = response.json()
    return body


def _error(client: Any, **kwargs: Any) -> dict[str, object]:
    response = client.post("/comparisons", **kwargs)
    return {"status": response.status_code, "body": response.json()}


def write_fixture(path: Path) -> None:
    """Antworten des echten Dienstes als gemeinsame Fixture für Vue und React (braucht httpx)."""
    from starlette.testclient import TestClient

    app = create_app(build_service(), identify=single_user)
    with TestClient(app) as client:
        created = [_create(client, old, new, fields) for old, new, fields in PAIRS]
        imported = client.post(
            "/comparisons/import",
            json={"title": "Import aus der Auftragssteuerung", "result": created[1]["result"]},
        ).json()
        fixture = {
            "source": "auditcore_documents.web (single_user), synthetische Dokumente",
            "profiles": client.get("/profiles").json(),
            "list": client.get("/comparisons").json(),
            "created": created[0],
            "imported": {"id": imported["id"], "title": imported["title"]},
            "errors": {
                "unsupported_type": _error(
                    client,
                    files={
                        "old_file": ("a.txt", b"x", "text/plain"),
                        "new_file": ("b.txt", b"y", "text/plain"),
                    },
                ),
                "threshold": _error(client, files=_files(*PAIRS[0][:2]), data={"threshold": "50"}),
            },
        }
    path.write_text(json.dumps(fixture, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    write_fixture(parser.parse_args().fixture)
