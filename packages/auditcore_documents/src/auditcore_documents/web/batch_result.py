"""Antwort der Bestandsprüfung: Befunde je Regel mit Begründung und betroffenen Belegen."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict

from auditcore_documents.pipeline.watchdog import (
    EscalationLevel,
    FindingCategory,
    WatchdogFinding,
    WatchdogResult,
)
from auditcore_documents.pipeline.watchdog.portfolio_checks import formal_issues
from auditcore_documents.pipeline.watchdog.values import normalize_supplier_name, to_float
from auditcore_documents.web.batch_input import Inventory
from auditcore_documents.web.batch_rules import RULES, SUPPLEMENT, BatchRule, rule_code

_RANK: dict[str, int] = {
    EscalationLevel.INFO: 1,
    EscalationLevel.WARNING: 2,
    EscalationLevel.BLOCKER: 3,
}
LEVEL_LABELS: dict[str, str] = {
    EscalationLevel.INFO: "Hinweis",
    EscalationLevel.WARNING: "Warnung",
    EscalationLevel.BLOCKER: "Blockade",
}
Documents = Sequence[Mapping[str, object]]


def _concentration_docs(finding: WatchdogFinding, documents: Documents) -> list[int]:
    supplier = finding.evidence.get("supplier")
    return [
        i
        for i, doc in enumerate(documents)
        if normalize_supplier_name(doc.get("supplier_name", "")) == supplier
    ]


def _uniform_rate_docs(documents: Documents) -> list[int]:
    return [i for i, doc in enumerate(documents) if to_float(doc.get("vat_rate")) is not None]


def affected_documents(finding: WatchdogFinding, documents: Documents) -> list[int]:
    """Betroffene Belege (0-basiert); leer bei reinen Gesamtbefunden (C-08)."""
    listed = finding.evidence.get("document_indices")
    if isinstance(listed, list):
        return [int(i) for i in listed]
    if finding.category == FindingCategory.CONCENTRATION:
        return _concentration_docs(finding, documents)
    if finding.category == FindingCategory.FORMAL_CORRECTNESS:
        return [i for i, doc in enumerate(documents) if formal_issues(doc)]
    if finding.category == FindingCategory.VAT_RATE and finding.document_index is None:
        return _uniform_rate_docs(documents)
    return [] if finding.document_index is None else [finding.document_index]


def _in_rule_order(findings: Sequence[WatchdogFinding]) -> list[WatchdogFinding]:
    order = {rule.code: position for position, rule in enumerate(RULES)}
    return sorted(
        findings, key=lambda f: order.get(rule_code(f.category, f.field_name), len(order))
    )


def finding_entries(result: WatchdogResult, documents: Documents) -> list[dict[str, object]]:
    """Befunde mit laufender Nummer, Regel, Stufe, Begründung und betroffenen Belegen."""
    return [
        {
            "id": f"B-{number:04d}",
            "rule": rule_code(f.category, f.field_name),
            "category": str(f.category),
            "level": str(f.level),
            "field": f.field_name,
            "message": f.message_de,
            "documents": affected_documents(f, documents),
            "evidence": f.evidence,
            "rule_reference": f.rule_reference,
        }
        for number, f in enumerate(_in_rule_order(result.findings), start=1)
    ]


def _indices(finding: Mapping[str, object]) -> list[int]:
    value = finding["documents"]
    return [int(i) for i in value] if isinstance(value, list) else []


def _worst(levels: Sequence[str]) -> str | None:
    return max(levels, key=lambda level: _RANK.get(level, 0)) if levels else None


def _not_checked_note(rule: BatchRule, inventory: Inventory) -> str | None:
    if rule.code == "C-08" and inventory.options.total_volume is None:
        return "Nicht geprüft: kein Gesamtvolumen angegeben."
    if rule.code == "C-13" and not any(c is not None for c in inventory.confidences):
        return "Nicht geprüft: keine OCR-Konfidenzen im Bestand."
    if rule.source == SUPPLEMENT and not inventory.options.supplementary:
        return "Nicht geprüft: Ergänzungsprüfungen abgeschaltet."
    return None


def _run_note(code: str, result: WatchdogResult) -> str:
    metrics = result.metrics
    if code == "C-10":
        label = LEVEL_LABELS.get(EscalationLevel(result.escalation_level), "")
        return f"Stufe: {label}." + (f" {result.block_reason}" if result.block_reason else "")
    if code == "C-11":
        return "Export über POST /export (json oder csv)."
    return (
        f"Pflichtfelder erfüllt: {metrics.mandatory_fields_success_rate:.1%}; "
        f"formal korrekt: {metrics.formal_correctness_rate:.1%}."
    )


def rule_entries(
    findings: list[dict[str, object]], result: WatchdogResult, inventory: Inventory
) -> list[dict[str, object]]:
    """Alle Regeln mit Status (``passed``, ``findings``, ``not_checked``, ``result``)."""
    entries = []
    for rule in RULES:
        own = [f for f in findings if f["rule"] == rule.code]
        docs = {i for f in own for i in _indices(f)}
        note = _not_checked_note(rule, inventory)
        if rule.scope == "run":
            status, note = "result", _run_note(rule.code, result)
        elif note is not None:
            status = "not_checked"
        else:
            status = "findings" if own else "passed"
        entries.append(
            {
                **rule.to_dict(),
                "status": status,
                "note": note,
                "findings": len(own),
                "documents": len(docs),
                "level": _worst([str(f["level"]) for f in own]),
            }
        )
    return entries


def document_entries(
    findings: list[dict[str, object]], inventory: Inventory
) -> list[dict[str, object]]:
    """Belege mit Kerndaten, Zahl der Befunde, schwerster Stufe und Regeln."""
    by_doc: dict[int, list[dict[str, object]]] = {}
    for finding in findings:
        for index in _indices(finding):
            by_doc.setdefault(index, []).append(finding)
    entries = []
    for index, (ref, doc) in enumerate(zip(inventory.refs, inventory.documents, strict=True)):
        own = by_doc.get(index, [])
        entries.append(
            {
                "index": index,
                "ref": ref,
                "supplier_name": doc.get("supplier_name"),
                "invoice_number": doc.get("invoice_number"),
                "invoice_date": doc.get("invoice_date"),
                "gross_amount": doc.get("gross_amount"),
                "ocr_confidence": inventory.confidences[index],
                "findings": len(own),
                "level": _worst([str(f["level"]) for f in own]),
                "rules": sorted({str(f["rule"]) for f in own}),
            }
        )
    return entries


def summary(
    result: WatchdogResult, findings: list[dict[str, object]], documents: int
) -> dict[str, object]:
    """Kopfzahlen und Eskalation (C-10) des Laufs."""
    touched = {i for f in findings for i in _indices(f)}
    return {
        "documents": documents,
        "findings": len(findings),
        "documents_with_findings": len(touched),
        "escalation_level": str(result.escalation_level),
        "report_blocked": result.report_blocked,
        "block_reason": result.block_reason,
        "timestamp": result.timestamp,
    }


def metrics(result: WatchdogResult) -> dict[str, object]:
    """Kennzahlen der Extraktionsqualität (C-12)."""
    return asdict(result.metrics)
