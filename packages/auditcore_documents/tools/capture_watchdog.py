"""Führt den flowinvoice-Extraktionsqualitäts-Watchdog tatsächlich aus und zeichnet ihn auf.

Aufruf im Wegwerf-Container (Python 3.11, nur Standardbibliothek nötig)::

    python tools/capture_watchdog.py --source <flowinvoice-Checkout@fb2d185>/backend \
        --output tests/fixtures/watchdog_observed.json

Das unveränderte Modul ``app/services/extraction_quality_watchdog.py`` wird
direkt aus der Datei geladen (ohne ``app``-Paket). Nur der Zeitstempel
hängt vom Lauf ab und wird maskiert.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "janpow77/flowinvoice"
COMMIT = "fb2d18568d2eaf64574d131ceae51a936b9aac02"
RELATIVE = "app/services/extraction_quality_watchdog.py"
BLOB = "16f5e7a071e7e59b6f862d2a1ac1416132cdea76"


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # noqa: S324


def valid(idx: int, **changes: Any) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "supplier_name": f"Lieferant {idx} GmbH",
        "customer_name": "Stadtwerke Beispiel AG",
        "supplier_vat_id": f"DE{100000000 + idx}",
        "invoice_date": "15.01.2026",
        "invoice_number": f"2026-{idx:04d}",
        "description": f"Dienstleistung {idx}",
        "net_amount": 1000.00 + idx,
        "vat_rate": 19.0,
        "vat_amount": round((1000.00 + idx) * 0.19, 2),
        "gross_amount": round((1000.00 + idx) * 1.19, 2),
    }
    doc.update(changes)
    return doc


def scenarios() -> list[dict[str, Any]]:
    """Synthetische Belegsätze: jede Prüfung C-01 … C-13, A-07, B-12 mindestens einmal."""
    return [
        {"name": "leer", "documents": []},
        {"name": "alle_gueltig", "documents": [valid(i) for i in range(1, 4)]},
        {
            "name": "pflichtfelder_fehlen",
            "documents": [
                valid(1, customer_name=None, description="", vat_amount="n/a"),
                valid(2, supplier_vat_id="-", invoice_number=None),
                valid(3),
            ],
        },
        {
            "name": "datum",
            "documents": [
                valid(1, invoice_date="Invalid Date"),
                valid(2, invoice_date="2026/01/15"),
                valid(3, invoice_date="15/01/2026"),
                valid(4, invoice_date="2026-01-15"),
                valid(5, invoice_date="Januar 2026"),
            ],
        },
        {
            "name": "rechnungsnummer",
            "documents": [
                valid(1, invoice_number="X" * 31),
                valid(2, invoice_number="Leistung für erneuerbare Energien im Januar"),
                valid(3, invoice_number="USt-ID DE123"),
                valid(4, invoice_number="#!?*§$%&"),
                valid(5, invoice_number="Steuer-Nr 12/345"),
                valid(6, invoice_number="www.beispiel.de"),
            ],
        },
        {
            "name": "querfeld",
            "documents": [
                valid(1, net_amount=1000, vat_amount=190, gross_amount=1250),
                valid(2, net_amount="1000,00", vat_amount="70,00", gross_amount="1070,00"),
                valid(3, net_amount=100, vat_amount=20, gross_amount=120, vat_rate=19),
            ],
        },
        {
            "name": "steuersatz",
            "documents": [
                valid(1, vat_rate=16.0),
                valid(2, vat_rate="7%"),
                valid(3, vat_rate="19,0"),
                valid(4, vat_rate="abc"),
            ],
        },
        {"name": "einheitlicher_satz", "documents": [valid(i) for i in range(1, 8)]},
        {
            "name": "lieferantenname",
            "documents": [
                valid(1, supplier_name="müller und söhne"),
                valid(2, supplier_name="AB"),
                valid(3, supplier_name="12345 678"),
                valid(4, supplier_name="Größe & Maß KG"),
            ],
        },
        {
            "name": "konzentration_duplikat",
            "documents": [
                valid(1, supplier_name="Bäckerei Groß GmbH", invoice_number="A-1"),
                valid(2, supplier_name="bäckerei groß", invoice_number="A-1"),
                valid(3, supplier_name="Bäckerei Groß AG", invoice_number="A-2"),
                valid(4),
            ],
        },
        {
            "name": "summenabgleich",
            "documents": [valid(1), valid(2), valid(3, gross_amount=None)],
            "total_volume": 5000.0,
        },
        {
            "name": "summenabgleich_passt",
            "documents": [valid(1), valid(2)],
            "total_volume": round(valid(1)["gross_amount"] + valid(2)["gross_amount"], 2),
        },
        {
            "name": "nan_werte",
            "documents": [
                valid(1, net_amount=float("nan")),
                valid(2, vat_amount="undefined", gross_amount=float("inf")),
                valid(3, vat_rate="NaN"),
                valid(4),
            ],
        },
        {
            "name": "blockade_formale_korrektheit",
            "documents": [
                valid(1, invoice_date="null", customer_name="none"),
                valid(2, description=None),
                valid(3, invoice_number="eins zwei drei vier fünf"),
            ],
        },
        {
            "name": "ocr_konfidenz",
            "documents": [valid(1), valid(2), valid(3)],
            "ocr_confidences": [0.95, 0.5, None],
        },
        {
            "name": "ocr_konfidenz_leer",
            "documents": [valid(1)],
            "ocr_confidences": [None],
        },
        {
            "name": "schwellen_angepasst",
            "documents": [valid(1, invoice_date="nan"), *(valid(i) for i in range(2, 11))],
            "watchdog": {"block_threshold": 0.05, "concentration_threshold": 0.9},
        },
        {
            "name": "zeitraum_und_toleranz",
            "documents": [valid(1, gross_amount=round(valid(1)["gross_amount"] + 0.5, 2))],
            "watchdog": {
                "tolerance": "1.00",
                "execution_period_start": "2026-01-01",
                "execution_period_end": "2026-12-31",
            },
        },
    ]


def watchdog_kwargs(raw: dict[str, Any]) -> dict[str, Any]:
    from decimal import Decimal

    kwargs = dict(raw)
    if "tolerance" in kwargs:
        kwargs["tolerance"] = Decimal(kwargs["tolerance"])
    for key in ("execution_period_start", "execution_period_end"):
        if key in kwargs:
            kwargs[key] = date.fromisoformat(kwargs[key])
    return kwargs


def run(module: Any, scenario: dict[str, Any]) -> dict[str, Any]:
    watchdog = module.ExtractionQualityWatchdog(**watchdog_kwargs(scenario.get("watchdog", {})))
    result = watchdog.validate(
        scenario["documents"],
        total_volume=scenario.get("total_volume"),
        ocr_confidences=scenario.get("ocr_confidences"),
    )
    observed = json.loads(result.to_json())
    observed["timestamp"] = "<masked>" if observed["timestamp"] else ""
    return observed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="flowinvoice backend")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "tests" / "fixtures" / "watchdog_observed.json"
    )
    args = parser.parse_args()
    path = args.source.resolve() / RELATIVE
    actual = git_blob(path)
    if actual != BLOB:
        raise SystemExit(f"Blob-Abweichung {RELATIVE}: {actual} != {BLOB}")
    spec = importlib.util.spec_from_file_location("legacy_watchdog", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["legacy_watchdog"] = module
    spec.loader.exec_module(module)
    cases = scenarios()
    output = {
        "schema_version": 1,
        "source": {"repository": REPOSITORY, "commit": COMMIT, "blobs": {RELATIVE: actual}},
        "environment": {"python": platform.python_version()},
        "scenarios": [{"name": case["name"], "observed": run(module, case)} for case in cases],
    }
    args.output.resolve().write_text(
        json.dumps(output, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"scenarios": len(cases), "written": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
