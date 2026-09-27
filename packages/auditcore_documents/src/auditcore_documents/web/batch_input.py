"""Eingabe der Bestandsprüfung ``documents_batch_checks/1``: Belege, Optionen, Felder.

Ein Beleg ist entweder ein flacher Datensatz mit den Feldern aus
:data:`FIELDS` (z. B. aus einer CSV-Tabelle) oder die Antwort eines Laufs der
Belegerkennung ``documents_extraction/1`` (erkennbar an ``fields``); diese wird
auf dieselben Felder abgebildet. Unbekannte Schlüssel werden ignoriert.
Beträge in deutscher Schreibweise (``"1.234,56"``) werden gelesen; was sich
nicht eindeutig lesen lässt, bleibt unverändert und wird von den Regeln als
ungültig gemeldet (A-07, C-04).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from auditcore_common.numbers_de import parse_number
from auditcore_common.rest import ContractError, bounded_list, json_object

from auditcore_documents.pipeline.watchdog import (
    CROSS_FIELD_TOLERANCE,
    ERROR_RATE_BLOCK_THRESHOLD,
    SUPPLIER_CONCENTRATION_THRESHOLD,
)


class BatchCheckError(ContractError):
    """Anfrage erfüllt den Vertrag ``documents_batch_checks/1`` nicht."""


@dataclass(frozen=True)
class FieldSpec:
    """Ein Feld des Bestands: Kennung, deutsche Bezeichnung, Spaltennamen für die Zuordnung."""

    name: str
    label: str
    aliases: tuple[str, ...]
    numeric: bool = False


FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        "ref",
        "Beleg (Kennung)",
        (
            "beleg",
            "belegnummer",
            "beleg-nr.",
            "belegnr",
            "ref",
            "kennung",
            "id",
            "datei",
            "dateiname",
            "filename",
        ),
    ),
    FieldSpec(
        "invoice_number",
        "Rechnungsnummer",
        ("rechnungsnummer", "rechnungsnr.", "re.-nr.", "rechnungs-nr.", "invoice_number"),
    ),
    FieldSpec(
        "invoice_date",
        "Rechnungsdatum",
        ("rechnungsdatum", "ausstellungsdatum", "datum", "invoice_date", "date"),
    ),
    FieldSpec(
        "supplier_name",
        "Leistender (Lieferant)",
        ("lieferant", "leistender", "rechnungssteller", "kreditor", "supplier_name", "supplier"),
    ),
    FieldSpec(
        "customer_name",
        "Leistungsempfänger",
        ("leistungsempfänger", "rechnungsempfänger", "empfänger", "begünstigter", "customer_name"),
    ),
    FieldSpec(
        "supplier_vat_id",
        "Steuernummer oder USt-IdNr.",
        ("ust-idnr.", "ust-idnr", "ust-id", "steuernummer", "supplier_vat_id", "vat_id"),
    ),
    FieldSpec(
        "description",
        "Leistungsbeschreibung",
        ("leistungsbeschreibung", "beschreibung", "leistung", "description"),
    ),
    FieldSpec(
        "net_amount",
        "Entgelt (netto)",
        ("netto", "nettobetrag", "entgelt", "net_amount"),
        numeric=True,
    ),
    FieldSpec(
        "vat_rate",
        "Steuersatz (%)",
        ("steuersatz", "ust-satz", "mwst-satz", "vat_rate"),
        numeric=True,
    ),
    FieldSpec(
        "vat_amount",
        "Steuerbetrag",
        ("steuerbetrag", "umsatzsteuer", "ust", "mwst", "vat_amount"),
        numeric=True,
    ),
    FieldSpec(
        "gross_amount",
        "Bruttobetrag",
        ("brutto", "bruttobetrag", "gesamtbetrag", "gross_amount", "total"),
        numeric=True,
    ),
    FieldSpec(
        "ocr_confidence",
        "OCR-Konfidenz (0–1)",
        ("ocr-konfidenz", "konfidenz", "ocr_confidence"),
        numeric=True,
    ),
)
FIELD_NAMES = tuple(f.name for f in FIELDS)
_NUMERIC = frozenset(f.name for f in FIELDS if f.numeric)
#: Felder eines Laufs der Belegerkennung → Felder des Bestands.
EXTRACTION_FIELDS = {
    "invoice_number": "invoice_number",
    "date": "invoice_date",
    "invoice_date": "invoice_date",
    "supplier_name": "supplier_name",
    "customer_name": "customer_name",
    "vat_id": "supplier_vat_id",
    "supplier_vat_id": "supplier_vat_id",
    "description": "description",
    "net_amount": "net_amount",
    "vat_rate": "vat_rate",
    "vat_amount": "vat_amount",
    "total": "gross_amount",
    "gross_amount": "gross_amount",
}
MAX_TEXT = 2000


@dataclass(frozen=True)
class BatchOptions:
    """Schwellen des Prüflaufs (Vorgaben des Katalogs) und Ergänzungsprüfungen."""

    total_volume: float | None = None
    tolerance: Decimal = CROSS_FIELD_TOLERANCE
    concentration_threshold: float = SUPPLIER_CONCENTRATION_THRESHOLD
    block_threshold: float = ERROR_RATE_BLOCK_THRESHOLD
    supplementary: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "total_volume": self.total_volume,
            "tolerance": float(self.tolerance),
            "concentration_threshold": self.concentration_threshold,
            "block_threshold": self.block_threshold,
            "supplementary": self.supplementary,
        }


@dataclass(frozen=True)
class Inventory:
    """Geprüfter Bestand: Kennungen, Datensätze, OCR-Konfidenzen und Optionen."""

    refs: tuple[str, ...]
    documents: tuple[dict[str, object], ...]
    confidences: tuple[float | None, ...]
    options: BatchOptions


def _number(value: object, name: str) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise BatchCheckError(f"'{name}' muss eine Zahl sein.")
    if isinstance(value, int | float):
        return float(value)
    parsed = parse_number(value, "auto", max_fraction_digits=None)
    if parsed is None:
        raise BatchCheckError(f"'{name}' muss eine Zahl sein.")
    return float(parsed)


def _bounded(body: Mapping[str, object], name: str, default: float, upper: float) -> float:
    value = _number(body.get(name), name)
    if value is None:
        return default
    if not 0 < value <= upper:
        raise BatchCheckError(f"'{name}' muss größer als 0 und höchstens {upper:g} sein.")
    return value


def parse_options(raw: object) -> BatchOptions:
    """``options`` der Anfrage (alle Angaben optional)."""
    body = json_object(raw if raw is not None else {}, "options", error=BatchCheckError)
    supplementary = body.get("supplementary", True)
    if not isinstance(supplementary, bool):
        raise BatchCheckError("'supplementary' muss true oder false sein.")
    total = _number(body.get("total_volume"), "total_volume")
    return BatchOptions(
        total_volume=total,
        tolerance=Decimal(str(_bounded(body, "tolerance", float(CROSS_FIELD_TOLERANCE), 1000))),
        concentration_threshold=_bounded(
            body, "concentration_threshold", SUPPLIER_CONCENTRATION_THRESHOLD, 1
        ),
        block_threshold=_bounded(body, "block_threshold", ERROR_RATE_BLOCK_THRESHOLD, 1),
        supplementary=supplementary,
    )


def _cell(value: object, name: str, row: int) -> object:
    if value is None or isinstance(value, int | float) and not isinstance(value, bool):
        return value
    if not isinstance(value, str):
        raise BatchCheckError(f"Beleg {row}: '{name}' muss Text oder Zahl sein.")
    if len(value) > MAX_TEXT:
        raise BatchCheckError(f"Beleg {row}: '{name}' ist länger als {MAX_TEXT} Zeichen.")
    if name in _NUMERIC and value.strip():
        parsed = parse_number(value, "auto", max_fraction_digits=None)
        return str(parsed) if parsed is not None else value
    return value


def _from_extraction(item: Mapping[str, object]) -> dict[str, object]:
    """Antwort von ``POST /runs`` der Belegerkennung als flacher Datensatz."""
    record: dict[str, object] = {}
    fields = item.get("fields")
    for entry in fields if isinstance(fields, list) else []:
        if isinstance(entry, Mapping) and entry.get("name") in EXTRACTION_FIELDS:
            record.setdefault(EXTRACTION_FIELDS[str(entry["name"])], entry.get("value"))
    document = item.get("document")
    if isinstance(document, Mapping) and document.get("filename"):
        record["ref"] = document["filename"]
    ocr = item.get("ocr")
    if isinstance(ocr, Mapping):
        record["ocr_confidence"] = ocr.get("avg_confidence")
    return record


def _confidence(value: object, row: int) -> float | None:
    number = _number(value, f"Beleg {row}: ocr_confidence")
    if number is not None and not 0 <= number <= 1:
        raise BatchCheckError(f"Beleg {row}: 'ocr_confidence' muss zwischen 0 und 1 liegen.")
    return number


def parse_document(raw: object, row: int) -> tuple[str, dict[str, object], float | None]:
    """Kennung, Datensatz für die Regeln und OCR-Konfidenz eines Belegs (``row`` ab 1)."""
    item = json_object(raw, f"documents[{row - 1}]", error=BatchCheckError)
    source = _from_extraction(item) if isinstance(item.get("fields"), list) else item
    record = {n: _cell(source.get(n), n, row) for n in FIELD_NAMES if n in source}
    ref = str(record.pop("ref", None) or f"Beleg {row}")
    confidence = _confidence(record.pop("ocr_confidence", None), row)
    return ref, record, confidence


def parse_inventory(payload: object, max_documents: int) -> Inventory:
    """Anfrage ``{"documents": [...], "options": {...}}`` als geprüfter Bestand."""
    body = json_object(payload, "Anfrage", error=BatchCheckError)
    items = bounded_list(
        body.get("documents"), "documents", max_documents, "Belege", error=BatchCheckError
    )
    parsed = [parse_document(item, row) for row, item in enumerate(items, start=1)]
    return Inventory(
        refs=tuple(p[0] for p in parsed),
        documents=tuple(p[1] for p in parsed),
        confidences=tuple(p[2] for p in parsed),
        options=parse_options(body.get("options")),
    )


def field_catalogue() -> list[dict[str, object]]:
    """Felder mit Bezeichnung und Spaltennamen für die Zuordnung in der Oberfläche."""
    return [
        {"name": f.name, "label": f.label, "aliases": list(f.aliases), "numeric": f.numeric}
        for f in FIELDS
    ]
