"""Demo-Backend und Fixture von „PDF schwärzen“ (``<flowaudit-pdf-redaction>``).

``demo/api_server.py`` bindet ``auditcore_pdf.web`` unter ``/api/redaction``
ein, die synthetische Beispiel-PDF liegt unter ``/api/redaction-demo/beispiel.pdf``.
Alle Namen, Adressen und Kontonummern sind erfunden (Domain ``.example``,
Prüf-IBAN aus der Norm). Die KI-Namenserkennung ist eine Attrappe, die nur
die erfundenen Namen meldet. Nicht für den Produktivbetrieb.

    python demo/redaction_demo.py --fixture ../ui-core/test/fixtures/redaction-contract.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pymupdf
from auditcore_pdf.redaction import Criteria, build_plan
from auditcore_pdf.web import Limits, RedactionService
from auditcore_pdf.web import routes as redaction_routes
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

PERSONS = ("Erika Beispiel", "Max Mustermann")
PAGES = [
    [
        "SYNTHETISCHES BEISPIEL – Prüfvermerk",
        "Rückfragen an max.muster@beispiel-firma.example",
        "Bankverbindung: IBAN DE89 3704 0044 0532 0130 00",
        "Ansprechpartnerin Erika Beispiel, Telefon 0611 123456",
        "Erika Beispiel hat die Unterlagen am 03.05.2026 nachgereicht.",
    ],
    [
        "Seite zwei: Stellungnahme",
        "Max Mustermann bestätigt die Angaben.",
        "Kopie an max.muster@beispiel-firma.example",
    ],
]


def demo_ner(texts: list[str]) -> list[list[tuple[int, int]]]:
    """Attrappe der KI-Namenserkennung: meldet nur die erfundenen Namen."""
    return [
        sorted({m.span() for name in PERSONS for m in re.finditer(re.escape(name), text)})
        for text in texts
    ]


def sample_pdf() -> bytes:
    """Zwei Textseiten, eine Seite nur mit Bild (ohne Textebene), Metadaten mit Adresse."""
    doc = pymupdf.open()
    for lines in PAGES:
        page = doc.new_page()
        for row, line in enumerate(lines):
            page.insert_text((72, 90 + 22 * row), line, fontsize=11)
    scan = doc.new_page()
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 40, 20), False)
    pix.set_rect(pix.irect, (220, 220, 220))
    scan.insert_image(pymupdf.Rect(72, 72, 520, 300), pixmap=pix)
    doc.set_metadata({"author": "max.muster@beispiel-firma.example", "title": "Prüfvermerk"})
    data: bytes = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return data


SERVICE = RedactionService(ner=demo_ner, limits=Limits(max_upload_bytes=20 * 1024 * 1024))


async def _sample(_: Request) -> Response:
    headers = {"Content-Disposition": 'inline; filename="beispiel.pdf"'}
    return Response(sample_pdf(), media_type="application/pdf", headers=headers)


def redaction_routes_demo() -> tuple[list[Route], list[Route]]:
    """Routen des Vertrags und der Beispiel-PDF."""
    return redaction_routes(SERVICE), [Route("/beispiel.pdf", _sample, methods=["GET"])]


def fixture() -> dict[str, object]:
    """Antworten des echten Dienstes für die Paritätstests der Oberfläche."""
    data = sample_pdf()
    criteria = Criteria.from_input(["email", "iban", "ki_namen"], ["Prüfvermerk"])
    plan = build_plan(data, criteria, demo_ner).to_dict()
    return {
        "catalogue": SERVICE.catalogue(),
        "catalogue_without_ner": RedactionService().catalogue(),
        "plan": {"contract": "pdf_redaction/1", **plan},
        "empty_plan": {
            "contract": "pdf_redaction/1",
            **build_plan(data, Criteria.from_input([], ["gibt es nicht"])).to_dict(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    target = parser.parse_args().fixture
    text = json.dumps(fixture(), ensure_ascii=False, indent=1) + "\n"
    target.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
