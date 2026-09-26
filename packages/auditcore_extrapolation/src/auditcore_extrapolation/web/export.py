"""``POST /evaluate/export``: the evaluation as CSV (Excel) or JSON file.

The export recomputes the evaluation from the request; it never copies client
state. CSV: semicolon, UTF-8 with BOM, decimal comma; cells starting with a
formula character are neutralised with an apostrophe.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import cast

from ._contract import ContractError, Reader
from .requests import evaluate

_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
_CONCLUSIONS = {
    "material": "Wesentlicher Fehler",
    "not_material": "Kein wesentlicher Fehler",
    "inconclusive": "Nicht schlüssig",
}
_SUMMARY = (
    ("Buchwert der Grundgesamtheit (BV)", "book_value"),
    ("Wesentlichkeitsschwelle", "materiality_rate"),
    ("Tolerierbarer Fehler (TE)", "tolerable_error"),
    ("Hochgerechneter zufälliger Fehler (EE)", "projected_random_error"),
    ("Abgegrenzte systemische Fehler", "systemic_errors"),
    ("Nicht korrigierte anomale Fehler", "anomalous_uncorrected"),
    ("Korrigierte anomale Fehler (nicht in TER)", "anomalous_corrected_excluded"),
    ("Gesamtfehler", "total_error"),
    ("Gesamtfehlerquote (TER)", "rate"),
    ("Präzision (SE)", "precision"),
    ("Fehlerobergrenze (ULE)", "upper_limit"),
    ("Quote der Fehlerobergrenze", "upper_limit_rate"),
)


@dataclass(frozen=True)
class ExportFile:
    """Rendered export with media type and download name."""

    content: bytes
    media_type: str
    filename: str


def _cell(value: object) -> str:
    """Spreadsheet text: decimal comma, formula prefixes neutralised."""
    if isinstance(value, float):
        return f"{value!r}".replace(".", ",")
    text = "" if value is None else str(value)
    return f"'{text}" if text[:1] in _FORMULA_START else text


def _rows(result: Mapping[str, object]) -> Iterator[list[object]]:
    method = cast(Mapping[str, object], result["method"])
    ter = cast(Mapping[str, object], result["total_error_rate"])
    projection = cast(Mapping[str, object], result["projection"])
    yield ["Hochrechnung und Gesamtfehlerquote", ""]
    yield ["Methode", method["label"]]
    yield ["Quelle", method["source"]]
    yield ["Konfidenzniveau", projection["confidence_level"]]
    yield ["Fingerabdruck der Eingabe (SHA-256)", result["fingerprint"]]
    for label, key in _SUMMARY:
        yield [label, ter[key]]
    yield ["Ergebnis", _CONCLUSIONS[str(ter["conclusion"])]]
    for line in cast(list[str], ter["explanation"]):
        yield ["Erläuterung", line]
    for warning in cast(list[str], projection["warnings"]):
        yield ["Hinweis", warning]
    yield []
    yield ["Herleitung", "Formel", "Wert", "Quelle"]
    steps = cast(list[Mapping[str, object]], projection["steps"])
    steps += cast(list[Mapping[str, object]], ter["steps"])
    for step in steps:
        yield [step["label"], step["formula"], step["value"], step["source"]]


def export_evaluation(payload: object) -> ExportFile:
    """CSV or JSON file of the evaluation requested in ``payload``."""
    body = Reader(payload)
    fmt = body.text("format")
    if fmt not in ("csv", "json"):
        raise ContractError("'format' muss csv oder json sein.")
    result = evaluate({k: v for k, v in body.body.items() if k != "format"})
    stem = f"hochrechnung-{cast(Mapping[str, object], result['method'])['id']}"
    stem += f"-{str(result['fingerprint'])[:12]}"
    if fmt == "json":
        content = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
        return ExportFile(content, "application/json", f"{stem}.json")
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    for row in _rows(result):
        writer.writerow([_cell(cell) for cell in row])
    return ExportFile(
        ("﻿" + buffer.getvalue()).encode("utf-8"), "text/csv; charset=utf-8", f"{stem}.csv"
    )
