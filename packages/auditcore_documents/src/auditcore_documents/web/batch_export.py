"""Export der Bestandsprüfung: JSON (C-11, vollständige Antwort) und CSV (Befundliste)."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence

from auditcore_documents.web.batch_result import LEVEL_LABELS
from auditcore_documents.web.batch_rules import RULES_BY_CODE
from auditcore_documents.web.export import ExportFile

EXPORT_FORMATS = ("json", "csv")
CSV_COLUMNS = (
    "Befund",
    "Regel",
    "Prüfung",
    "Stufe",
    "Beleg-Nr.",
    "Beleg",
    "Feld",
    "Begründung",
    "Rechtsgrundlage",
)
#: Zellanfänge, die Tabellenkalkulationen als Formel lesen würden.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _spreadsheet_text(value: object) -> str:
    text = "" if value is None else str(value)
    return f"'{text}" if text.startswith(_FORMULA_PREFIXES) else text


def _level(level: object) -> str:
    return next((label for key, label in LEVEL_LABELS.items() if key == level), str(level))


def _rows(answer: Mapping[str, object]) -> list[list[str]]:
    documents = answer["documents"]
    refs = [str(d["ref"]) for d in documents] if isinstance(documents, list) else []
    findings = answer["findings"]
    rows: list[list[str]] = []
    for finding in findings if isinstance(findings, Sequence) else []:
        rule = RULES_BY_CODE.get(str(finding["rule"]))
        head = [
            str(finding["id"]),
            str(finding["rule"]),
            rule.title if rule else "",
            _level(finding["level"]),
        ]
        tail = [
            str(finding["field"] or ""),
            str(finding["message"]),
            str(finding["rule_reference"] or (rule.legal_basis if rule else "")),
        ]
        indices = finding["documents"] or [None]
        rows += [
            [*head, "" if i is None else str(i + 1), "" if i is None else refs[i], *tail]
            for i in indices
        ]
    return rows


def findings_csv(answer: Mapping[str, object]) -> bytes:
    """Befundliste: eine Zeile je Befund und betroffenem Beleg (Excel: Semikolon, UTF-8-BOM)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)
    for row in _rows(answer):
        writer.writerow([_spreadsheet_text(cell) for cell in row])
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def export_answer(answer: Mapping[str, object], fmt: str) -> ExportFile:
    """Antwort als Datei ``befunde-bestand-<Datum>.json`` bzw. ``.csv``."""
    summary = answer["summary"]
    stamp = str(summary["timestamp"])[:10] if isinstance(summary, Mapping) else ""
    stem = f"befunde-bestand-{stamp}" if stamp else "befunde-bestand"
    if fmt == "csv":
        return ExportFile(findings_csv(answer), "text/csv; charset=utf-8", f"{stem}.csv")
    content = json.dumps(answer, ensure_ascii=False, indent=2).encode("utf-8")
    return ExportFile(content, "application/json", f"{stem}.json")
