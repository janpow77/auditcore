"""Ergänzende Bestandsprüfungen außerhalb des Katalogs C-01 bis C-13 (auditcore).

Der Verbesserungskatalog kennt Dubletten (C-09), aber weder Lücken in
Nummernkreisen noch widersprüchliche USt-IdNr. eines Lieferanten. Beide
Prüfungen ergänzt auditcore für die Bestandsprüfung (``documents_batch_checks/1``);
:class:`~auditcore_documents.pipeline.watchdog.ExtractionQualityWatchdog`
ruft sie nicht auf, damit der Watchdog dem Original gleich bleibt.

- **ERG-01 Nummernlücken:** Rechnungsnummern desselben Lieferanten mit
  gleichem Präfix (Nummernkreis) werden nach ihrem Zählteil sortiert; fehlende
  Zählwerte zwischen zwei vorhandenen Nummern sind ein Hinweis (Stufe
  ``info``). Ein Lieferant nummeriert über alle seine Kunden fortlaufend
  (§ 14 Abs. 4 Satz 1 Nr. 4 UStG); Lücken im Bestand eines Empfängers sind
  deshalb üblich und für sich kein Mangel. Sprünge über ``max_gap`` gelten
  als anderer Nummernbereich und werden nicht gemeldet.
- **ERG-02 USt-IdNr.-Konsistenz:** derselbe Lieferant mit verschiedenen
  USt-IdNr./Steuernummern und dieselbe Kennung bei verschiedenen
  Lieferantennamen. Stufe ``warning`` nur, wenn ein Lieferant mindestens zwei
  verschiedene USt-IdNr. (mit Länderpräfix) trägt; Steuernummer neben
  USt-IdNr. ist zulässig und bleibt ``info``.

Beide Prüfungen gehen nicht in die Eskalation C-10 ein: Sie betreffen den
Inhalt des Bestands, nicht die Extraktionsqualität.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .model import EscalationLevel, WatchdogFinding, WatchdogResult
from .values import is_empty_or_invalid, normalize_supplier_name

Documents = Sequence[Mapping[str, object]]

#: Kategorien der ergänzenden Befunde (nicht Teil von ``FindingCategory``).
INVOICE_NUMBER_GAP = "invoice_number_gap"
VAT_ID_CONSISTENCY = "vat_id_consistency"
#: Größter Abstand zweier Zählwerte, der noch als Lücke gilt.
MAX_NUMBER_GAP = 50
#: Höchstzahl aufgezählter Lücken je Nummernkreis in der Meldung.
LISTED_GAPS = 10
_VAT_ID_PREFIX = re.compile(r"^[A-Z]{2}[0-9A-Z]")
_COUNTER = re.compile(r"^(?P<prefix>.*?)(?P<counter>\d+)(?P<suffix>\D*)$")


@dataclass(frozen=True)
class _Numbered:
    index: int
    counter: int
    width: int


def _series_entry(doc: Mapping[str, object]) -> tuple[tuple[str, str, str], str] | None:
    """(Lieferant, Präfix, Suffix) und Zählteil einer Rechnungsnummer."""
    supplier = normalize_supplier_name(doc.get("supplier_name", ""))
    match = _COUNTER.match(str(doc.get("invoice_number") or "").strip())
    if not supplier or match is None:
        return None
    return (supplier, match.group("prefix"), match.group("suffix")), match.group("counter")


def _series(documents: Documents) -> dict[tuple[str, str, str], list[_Numbered]]:
    series: dict[tuple[str, str, str], list[_Numbered]] = {}
    for idx, doc in enumerate(documents):
        entry = _series_entry(doc)
        if entry is not None:
            key, digits = entry
            series.setdefault(key, []).append(_Numbered(idx, int(digits), len(digits)))
    return series


def _gaps(entries: list[_Numbered], max_gap: int) -> list[tuple[int, int]]:
    counters = sorted({e.counter for e in entries})
    return [
        (low + 1, high - 1)
        for low, high in zip(counters, counters[1:], strict=False)
        if 1 < high - low <= max_gap
    ]


def _gap_text(gap: tuple[int, int], width: int, prefix: str, suffix: str) -> str:
    low, high = (f"{prefix}{n:0{width}d}{suffix}" for n in gap)
    return low if gap[0] == gap[1] else f"{low} bis {high}"


def _gap_finding(
    key: tuple[str, str, str], entries: list[_Numbered], gaps: list[tuple[int, int]]
) -> WatchdogFinding:
    supplier, prefix, suffix = key
    width = min(e.width for e in entries)
    missing = sum(high - low + 1 for low, high in gaps)
    listed = "; ".join(_gap_text(g, width, prefix, suffix) for g in gaps[:LISTED_GAPS])
    more = f" (und {len(gaps) - LISTED_GAPS} weitere)" if len(gaps) > LISTED_GAPS else ""
    indices = sorted(e.index for e in entries)
    return WatchdogFinding(
        category=INVOICE_NUMBER_GAP,
        level=EscalationLevel.INFO,
        document_index=indices[0],
        field_name="invoice_number",
        message_de=(
            f"Nummernlücken bei Lieferant '{supplier}' (Nummernkreis "
            f"'{prefix}…{suffix}'): {missing} Nummer(n) fehlen im Bestand: {listed}{more}."
        ),
        message_en=(
            f"Invoice number gaps for supplier '{supplier}' (series "
            f"'{prefix}…{suffix}'): {missing} number(s) missing from the inventory."
        ),
        evidence={
            "supplier": supplier,
            "prefix": prefix,
            "suffix": suffix,
            "missing_count": missing,
            "gaps": [list(g) for g in gaps],
            "document_indices": indices,
        },
        rule_reference="§ 14 Abs. 4 Satz 1 Nr. 4 UStG",
    )


def check_invoice_number_gaps(
    documents: Documents, result: WatchdogResult, max_gap: int = MAX_NUMBER_GAP
) -> None:
    """ERG-01: Lücken im Zählteil der Rechnungsnummern je Lieferant und Nummernkreis."""
    for key, entries in _series(documents).items():
        gaps = _gaps(entries, max_gap)
        if gaps:
            result.findings.append(_gap_finding(key, entries, gaps))


def normalize_vat_id(value: object) -> str:
    """USt-IdNr./Steuernummer ohne Leerzeichen, Punkte und Bindestriche, groß geschrieben."""
    if is_empty_or_invalid(value):
        return ""
    return re.sub(r"[\s./-]", "", str(value)).upper()


def _groups(
    documents: Documents,
) -> tuple[dict[str, dict[str, list[int]]], dict[str, dict[str, list[int]]]]:
    by_supplier: dict[str, dict[str, list[int]]] = {}
    by_vat: dict[str, dict[str, list[int]]] = {}
    for idx, doc in enumerate(documents):
        supplier = normalize_supplier_name(doc.get("supplier_name", ""))
        vat_id = normalize_vat_id(doc.get("supplier_vat_id"))
        if not supplier or not vat_id:
            continue
        by_supplier.setdefault(supplier, {}).setdefault(vat_id, []).append(idx)
        by_vat.setdefault(vat_id, {}).setdefault(supplier, []).append(idx)
    return by_supplier, by_vat


def _listing(variants: dict[str, list[int]]) -> str:
    return "; ".join(
        f"{value} (Beleg {', '.join(str(i + 1) for i in indices)})"
        for value, indices in sorted(variants.items())
    )


def _consistency_level(variants: dict[str, list[int]], by_supplier: bool) -> str:
    vat_ids = [value for value in variants if _VAT_ID_PREFIX.match(value)]
    return EscalationLevel.WARNING if by_supplier and len(vat_ids) > 1 else EscalationLevel.INFO


def _consistency_finding(
    key: str, variants: dict[str, list[int]], by_supplier: bool
) -> WatchdogFinding:
    indices = sorted(i for group in variants.values() for i in group)
    if by_supplier:
        text_de = f"Lieferant '{key}' mit {len(variants)} verschiedenen USt-IdNr./Steuernummern"
        text_en = f"Supplier '{key}' with {len(variants)} different VAT IDs/tax numbers"
    else:
        text_de = f"USt-IdNr./Steuernummer '{key}' bei {len(variants)} verschiedenen Lieferanten"
        text_en = f"VAT ID/tax number '{key}' used by {len(variants)} different suppliers"
    return WatchdogFinding(
        category=VAT_ID_CONSISTENCY,
        level=_consistency_level(variants, by_supplier),
        document_index=indices[0],
        field_name="supplier_vat_id",
        message_de=f"{text_de}: {_listing(variants)}.",
        message_en=f"{text_en}.",
        evidence={
            "supplier" if by_supplier else "vat_id": key,
            "variants": {k: v for k, v in sorted(variants.items())},
            "document_indices": indices,
        },
        rule_reference="§ 14 Abs. 4 Satz 1 Nr. 2 UStG",
    )


def check_vat_id_consistency(documents: Documents, result: WatchdogResult) -> None:
    """ERG-02: USt-IdNr./Steuernummer je Lieferant eindeutig und umgekehrt."""
    by_supplier, by_vat = _groups(documents)
    for supplier, variants in by_supplier.items():
        if len(variants) > 1:
            result.findings.append(_consistency_finding(supplier, variants, by_supplier=True))
    for vat_id, variants in by_vat.items():
        if len(variants) > 1:
            result.findings.append(_consistency_finding(vat_id, variants, by_supplier=False))
