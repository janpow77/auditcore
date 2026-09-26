"""Tabellarische Synopse als reine Datensätze (aus dem ecohesion-Worker).

Die Datensätze haben deutschsprachige Spaltennamen und lassen optionale
Spaltenpaare weg, wenn beide Seiten leer sind. Sie eignen sich unmittelbar
für ``auditcore_reporting.ReportTable`` (XLSX) oder einen PDF-Renderer der
Anwendung; die Bibliothek selbst rendert hier nichts.
"""

from __future__ import annotations

from typing import Any

from auditcore_documents.model import ComparisonResult

STATUS_LABELS = {
    "changed": "Geändert",
    "added": "Neu",
    "removed": "Entfallen",
    "moved": "Verschoben",
    "unchanged": "Unverändert",
}


def synopsis_records(result: ComparisonResult) -> tuple[list[str], list[dict[str, str]]]:
    """(Spalten, Zeilen) aller nicht unveränderten Zeilen in Ergebnisreihenfolge."""
    rows: list[dict[str, str]] = [
        {
            "Änderung": STATUS_LABELS.get(r.status, r.status),
            "Fundstelle": r.location,
            "Bisherige Fassung": r.old_text,
            "Neue Fassung": r.new_text,
            **(
                {"Antwort bisher": r.old_answer, "Antwort neu": r.new_answer}
                if r.old_answer or r.new_answer
                else {}
            ),
            **(
                {"Bemerkung bisher": r.old_comment, "Bemerkung neu": r.new_comment}
                if r.old_comment or r.new_comment
                else {}
            ),
            **(
                {"Hinweis bisher": r.old_note, "Hinweis neu": r.new_note}
                if r.old_note or r.new_note
                else {}
            ),
        }
        for r in result.rows
        if r.status != "unchanged"
    ]
    columns = list(dict.fromkeys(k for row in rows for k in row))
    return columns, rows


def synopsis_extra(result: ComparisonResult) -> dict[str, Any]:
    """Kopfangaben und Hinweise wie im ecohesion-Worker."""
    return {
        "notes": [result.metadata["pdf_notice"]] if result.metadata.get("pdf_notice") else [],
        "extra": {
            "Bisherige Datei": result.old_filename,
            "Neue Datei": result.new_filename,
            "SHA-256 bisher": result.old_sha256,
            "SHA-256 neu": result.new_sha256,
        },
    }
