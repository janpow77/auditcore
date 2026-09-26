"""Demo-Backend und Fixture der Belegerkennung (``<flowaudit-extraction>``).

``demo/api_server.py`` bindet ``auditcore_documents.web.extraction_routes``
unter ``/api/extraction`` ein. OCR und Donut sind hier Attrappen der Ports:
Die „Texterkennung“ liefert für die synthetischen Rechnungsbilder aus
``packages/auditcore_documents/tests/fixtures/donut`` (sichtbar als
SYNTHETISCH markiert, erzeugt mit auditcore_invoicesynth) den gedruckten Text,
Donut die Sollwerte – beim Beleg „summen_unten“ absichtlich mit falschem
Gesamtbetrag. Andere Dateien ergeben einen leeren Text mit niedriger Konfidenz.
Nicht für den Produktivbetrieb.

    python demo/extraction_demo.py --fixture ../ui-core/test/fixtures/extraction-contract.json
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from auditcore_documents.pipeline import DonutResult, FakeDonut, ParsedDocument, ParsedPage
from auditcore_documents.web import (
    ExtractionEngines,
    ExtractionService,
    ExtractionSettings,
    extraction_routes,
)
from starlette.routing import BaseRoute

REPO = Path(__file__).resolve().parents[3]
DONUT = REPO / "packages/auditcore_documents/tests/fixtures/donut"
CASES: list[dict[str, Any]] = json.loads((DONUT / "cases.json").read_text(encoding="utf-8"))[
    "cases"
]
#: Belege mit mittlerer Lesequalität (Prüfung nötig) und mit falschem Donut-Wert.
REVIEW_LAYOUT = "holdout_briefkopf"
WRONG_TOTAL_LAYOUT = "summen_unten"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


BY_HASH = {_digest((DONUT / case["file_name"]).read_bytes()): case for case in CASES}


def printed_text(gt: dict[str, Any]) -> str:
    """Gedruckte Werte mit Beschriftungen (Ersatz für eine echte Texterkennung)."""
    labels = (
        ("invoice_number", "Rechnungsnummer"),
        ("invoice_date", "Rechnungsdatum"),
        ("net_amount", "Nettobetrag"),
        ("total", "Gesamtbetrag"),
        ("iban", "IBAN"),
    )
    lines = [f"{label}: {gt[key]}" for key, label in labels if key in gt]
    vat_id = gt.get("supplier", {}).get("vat_id")
    return "\n".join([*lines, f"USt-IdNr.: {vat_id}"] if vat_id else lines)


class DemoTesseract:
    """Attrappe des ``TesseractPort``: Text der bekannten synthetischen Belege."""

    def parse(self, path: Path) -> ParsedDocument:
        case = BY_HASH.get(_digest(path.read_bytes()))
        if case is None:
            return ParsedDocument("", [ParsedPage("", 0.4)], None, None)
        confidence = 0.72 if case["meta"]["layout"] == REVIEW_LAYOUT else 0.93
        text = printed_text(case["gt_parse"])
        return ParsedDocument(text, [ParsedPage(text, confidence)], None, None)


def _donut(page_png: bytes) -> DonutResult:
    case = BY_HASH.get(_digest(page_png))
    gt = copy.deepcopy(case["gt_parse"]) if case else {}
    if case and case["meta"]["layout"] == WRONG_TOTAL_LAYOUT and "total" in gt:
        gt["total"] = "99.999,99"
    keys = ["invoice_number", "invoice_date", "total", "iban", "net_amount", "supplier.vat_id"]
    confidence = dict.fromkeys(keys, 0.97)
    confidence["invoice_date"] = 0.81
    return DonutResult(
        fields=gt,
        field_confidence=confidence,
        model_id="donut-demo",
        model_sha256="0" * 64,
        device="cpu",
    )


def build_service() -> ExtractionService:
    """Dienst mit Attrappen für Texterkennung und Donut, höchstens 5 MiB je Datei."""
    engines = ExtractionEngines(tesseract=DemoTesseract(), donut=FakeDonut(_donut), rasterizer=None)
    return ExtractionService(engines, ExtractionSettings(max_upload_bytes=5 * 1024 * 1024))


def extraction_routes_demo() -> list[BaseRoute]:
    """Routen für ``/api/extraction``."""
    return list(extraction_routes(build_service()))


def _case_bytes(layout: str) -> bytes:
    case = next(c for c in CASES if c["meta"]["layout"] == layout)
    return (DONUT / case["file_name"]).read_bytes()


def _masked(result: dict[str, Any]) -> dict[str, Any]:
    """Lauf-Kennung und Dauer sind je Lauf verschieden; für die Fixture fest."""
    result["run"]["run_id"] = "00000000-0000-4000-8000-000000000001"
    result["run"]["duration_ms"] = 12
    return result


def write_fixture(path: Path) -> None:
    """Antworten des echten Dienstes als gemeinsame Fixture für Vue und React (braucht httpx)."""
    from starlette.applications import Starlette
    from starlette.testclient import TestClient

    with TestClient(Starlette(routes=extraction_routes_demo())) as client:

        def run(layout: str, profile: str) -> dict[str, Any]:
            files = {"file": ("beleg.png", _case_bytes(layout), "image/png")}
            response = client.post("/runs", files=files, data={"profile": profile})
            response.raise_for_status()
            return _masked(response.json())

        disabled = ExtractionService()
        fixture = {
            "source": "auditcore_documents.web (Belegerkennung), Attrappen-Ports, "
            "synthetische Belege",
            "catalogue": client.get("/profile").json(),
            "catalogue_disabled": disabled.catalogue(),
            "run_ok": run("kopf_links", "auditcore.pipeline"),
            "run_review": run(REVIEW_LAYOUT, "auditcore.pipeline"),
            "run_donut": run(WRONG_TOTAL_LAYOUT, "auditcore.pipeline.donut"),
            "run_failed": _masked(
                client.post(
                    "/runs", files={"file": ("notiz.txt", b"nur Text", "text/plain")}
                ).json()
            ),
            "error_profile": client.post(
                "/runs",
                files={"file": ("beleg.png", _case_bytes("kopf_links"), "image/png")},
                data={"profile": "unbekannt"},
            ).json(),
        }
    path.write_text(json.dumps(fixture, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    write_fixture(parser.parse_args().fixture)
