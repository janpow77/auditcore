"""Erzeugt synthetische Eingaben für die Pipeline-Charakterisierung (einmalig, eingecheckt).

Aufruf mit installiertem ``auditcore_invoicegenerator[pdf]`` und pypdf::

    python tools/build_pipeline_fixtures.py

* ``invoice_*.pdf``: synthetische Rechnungen aus ``auditcore_invoicegenerator``
  (Seed 42, Bezugsdatum 15.01.2026, Fehler ``wrong_total``/``missing_vat_id``),
* ``pixel.png``: kleinstes gültiges PNG (Bildeingang ohne PDF),
* ``notiz.txt``: unzulässiger Dateityp,
* ``ocr_texts.json``: OCR-Antworten des Gateway-Stellvertreters. Für die
  Rechnungen ist das der mit pypdf extrahierte Seitentext der PDF; dazu frei
  erfundene deutsche Rechnungstexte für die Feldregeln. Keine Echtdaten.
"""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from datetime import date
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "pipeline"

GERMAN_TEXTS = {
    "de_gueltig": (
        "Muster Handels GmbH\nRechnungsnummer: RE-2026/0042\nRechnungsdatum: 03.02.2026\n"
        "USt-IdNr.: DE123456789\nIBAN: DE89 3704 0044 0532 0130 00\n\n\n\n"
        "Nettobetrag: 1.000,00 EUR\nMwSt 19 %: 190,00 EUR\nGesamtbetrag: 1.190,00 EUR\n"
    ),
    "de_iban_falsch": (
        "Rechnungsnummer: RE-2026/0043\nDatum: 04.02.26\nIBAN: DE89 3704 0044 0532 0130 01\n"
        "Nettobetrag: 100,00 EUR\nUSt 7%: 7,00\nGesamtbetrag: 107,00 EUR\n"
    ),
    "de_summe_falsch": (
        "Re.-Nr.: 77/2026\nDatum: 2026-02-05\nUSt-Id: ATU12345678\n"
        "Zwischensumme: 200,00\nUmsatzsteuer 20 %: 40,00\nSumme: 250,00 €\n"
    ),
    "de_land_unbekannt": (
        "Invoice No: INV-9\nDate: 06/02/2026\nVAT ID: XX123456789\nSubtotal: 10.00\n"
        "VAT 19%: 1.90\nTotal: 11.90\n"
    ),
    "de_datum_unlesbar": (
        "Rechnungsnummer: A1\nRechnungsdatum: 31.02.2026\nGesamtbetrag: abc EUR\n"
        "Netto: 0,00\nMwSt: 0,00\n"
    ),
}


def tiny_png() -> bytes:
    """1×1-PNG, weiß, byte-reproduzierbar."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
        + chunk(b"IEND", b"")
    )


def main() -> None:
    from auditcore_invoicegenerator import InvoiceScenario, render_pdf
    from pypdf import PdfReader

    OUT.mkdir(parents=True, exist_ok=True)
    scenario = InvoiceScenario(42, base_date=date(2026, 1, 15), country="DE")
    invoices = scenario.generate_batch(3, errors={2: "wrong_total", 3: "missing_vat_id"})
    texts: dict[str, list[str]] = {}
    for index, invoice in enumerate(invoices, 1):
        name = f"invoice_{index}.pdf"
        data = render_pdf(invoice)
        (OUT / name).write_bytes(data)
        texts[name] = [page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages]
    (OUT / "pixel.png").write_bytes(tiny_png())
    (OUT / "notiz.txt").write_text("Kein Beleg.\n", encoding="utf-8")
    payload = {
        "invoice_pages": texts,
        "german": GERMAN_TEXTS,
        "sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT.iterdir())
            if p.suffix in {".pdf", ".png", ".txt"}
        },
    }
    (OUT / "ocr_texts.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps({"invoices": len(invoices), "files": sorted(payload["sha256"])}))


if __name__ == "__main__":
    main()
