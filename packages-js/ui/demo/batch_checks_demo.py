"""Demo-Backend und Fixture der Bestandsprüfung (``<flowaudit-batch-checks>``).

``demo/api_server.py`` bindet ``auditcore_documents.web.batch_check_routes``
unter ``/api/batch-checks`` ein. Der Beispielbestand
``packages/auditcore_documents/tests/fixtures/batch/bestand.csv`` enthält zehn
synthetische Belege erfundener Lieferanten mit gezielt eingebauten Mängeln
(Dublette, Nummernlücke, abweichende USt-IdNr., unzulässiger Steuersatz …).
Nicht für den Produktivbetrieb.

    python demo/batch_checks_demo.py --fixture ../ui-core/test/fixtures/batch-checks-contract.json
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from auditcore_documents.web import BatchCheckService, BatchCheckSettings, batch_check_routes
from auditcore_documents.web.batch_input import FIELDS
from starlette.routing import BaseRoute

REPO = Path(__file__).resolve().parents[3]
INVENTORY = REPO / "packages/auditcore_documents/tests/fixtures/batch/bestand.csv"
#: Fester Zeitpunkt der Fixture (der Demo-Dienst nimmt die Uhr).
FIXED = datetime(2026, 9, 26, 10, 0, tzinfo=UTC)


def build_service(clock: Any = None) -> BatchCheckService:
    return BatchCheckService(BatchCheckSettings(max_documents=5000), clock=clock)


def batch_check_routes_demo() -> list[BaseRoute]:
    """Routen für ``/api/batch-checks``."""
    return list(batch_check_routes(build_service()))


def inventory_documents(text: str) -> list[dict[str, Any]]:
    """Zeilen des Beispielbestands mit Spaltenzuordnung über die Spaltennamen des Katalogs."""
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    header = [name.strip().lower() for name in rows[0]]
    columns = {f.name: header.index(a) for f in FIELDS for a in f.aliases if a in header}
    return [{name: row[i] or None for name, i in columns.items()} for row in rows[1:]]


def write_fixture(path: Path) -> None:
    """Antworten des echten Dienstes als gemeinsame Fixture für Vue und React."""
    service = build_service(clock=lambda: FIXED)
    text = INVENTORY.read_text(encoding="utf-8")
    documents = inventory_documents(text)
    fixture = {
        "source": "auditcore_documents.web (Bestandsprüfung), synthetischer Beispielbestand",
        "csv": text,
        "catalogue": service.catalogue(),
        "answer": service.check({"documents": documents, "options": {"total_volume": 48500}}),
        "answer_plain": service.check(
            {"documents": documents[:2], "options": {"supplementary": False}}
        ),
    }
    path.write_text(json.dumps(fixture, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    write_fixture(parser.parse_args().fixture)
