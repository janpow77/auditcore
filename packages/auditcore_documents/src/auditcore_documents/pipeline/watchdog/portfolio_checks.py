"""Belegübergreifende Prüfungen C-07 bis C-10, B-12 und C-12/C-13."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from .document_checks import Documents
from .model import (
    MANDATORY_FIELDS_USTG_14,
    MAX_INVOICE_NUMBER_LENGTH,
    EscalationLevel,
    FindingCategory,
    WatchdogFinding,
    WatchdogResult,
)
from .values import float_is_nan_or_inf, is_empty_or_invalid, normalize_supplier_name, to_decimal

#: Datumswerte, die für die formale Korrektheit (B-12) als ungültig gelten.
FORMAL_INVALID_DATES = frozenset({"invalid date", "nan", "null", "undefined", "n/a", "none", ""})
#: Grenze der OCR-Confidence für die risikoorientierte Nachprüfung (C-13).
LOW_OCR_CONFIDENCE = 0.80


def check_supplier_concentration(
    documents: Documents, result: WatchdogResult, threshold: float
) -> None:
    """C-07: Prüft, ob ein einzelner Lieferant mehr als die Schwelle des Volumens ausmacht."""
    supplier_volumes: dict[str, Decimal] = {}
    supplier_counts: dict[str, int] = {}
    total = Decimal("0")
    for doc in documents:
        name = normalize_supplier_name(doc.get("supplier_name", ""))
        if not name:
            continue
        amount = to_decimal(doc.get("gross_amount") or doc.get("net_amount"))
        if amount is None:
            amount = Decimal("0")
        supplier_volumes[name] = supplier_volumes.get(name, Decimal("0")) + amount
        supplier_counts[name] = supplier_counts.get(name, 0) + 1
        total += amount
    if total <= 0:
        return
    for supplier, volume in supplier_volumes.items():
        share = float(volume / total)
        if share > threshold:
            count = supplier_counts.get(supplier, 0)
            result.findings.append(
                WatchdogFinding(
                    category=FindingCategory.CONCENTRATION,
                    level=EscalationLevel.WARNING,
                    document_index=None,
                    field_name="supplier_name",
                    message_de=(
                        f"Konzentrationsrisiko: '{supplier}' hat {count} "
                        f"Belege ({share:.1%} des Gesamtvolumens)."
                    ),
                    message_en=(
                        f"Concentration risk: '{supplier}' has {count} "
                        f"documents ({share:.1%} of total volume)."
                    ),
                    evidence={
                        "supplier": supplier,
                        "document_count": count,
                        "volume": str(volume),
                        "share": round(share, 4),
                    },
                )
            )


def check_sum_reconciliation(
    documents: Documents, total_volume: float, result: WatchdogResult
) -> None:
    """C-08: Summe der Einzelbeträge gegen das ausgewiesene Gesamtvolumen."""
    calculated_sum = Decimal("0")
    for doc in documents:
        amount = to_decimal(doc.get("gross_amount") or doc.get("net_amount"))
        if amount is not None:
            calculated_sum += amount
    total_dec = Decimal(str(total_volume))
    diff = abs(calculated_sum - total_dec)
    # Toleranz: 1 Cent pro Beleg (Rundungsdifferenzen)
    if diff <= Decimal(str(len(documents) * 0.01)):
        return
    result.findings.append(
        WatchdogFinding(
            category=FindingCategory.SUM_RECONCILIATION,
            level=EscalationLevel.WARNING,
            document_index=None,
            field_name=None,
            message_de=(
                f"Summenabweichung: Einzelbeträge ergeben {calculated_sum:.2f} EUR, "
                f"ausgewiesenes Gesamtvolumen ist {total_dec:.2f} EUR. "
                f"Differenz: {diff:.2f} EUR."
            ),
            message_en=(
                f"Sum discrepancy: Individual amounts total {calculated_sum:.2f} EUR, "
                f"reported total volume is {total_dec:.2f} EUR. "
                f"Difference: {diff:.2f} EUR."
            ),
            evidence={
                "calculated_sum": str(calculated_sum),
                "reported_total": str(total_dec),
                "difference": str(diff),
            },
        )
    )


def check_duplicates(documents: Documents, result: WatchdogResult) -> None:
    """C-09: identische Kombination Lieferant + Rechnungsnummer."""
    seen: dict[str, list[int]] = {}
    for idx, doc in enumerate(documents):
        supplier = normalize_supplier_name(doc.get("supplier_name", ""))
        inv_nr = str(doc.get("invoice_number", "")).strip()
        if supplier and inv_nr:
            seen.setdefault(f"{supplier}|{inv_nr}", []).append(idx)
    for key, indices in seen.items():
        if len(indices) > 1:
            result.findings.append(_duplicate_finding(key, indices))


def _duplicate_finding(key: str, indices: list[int]) -> WatchdogFinding:
    supplier, inv_nr = key.split("|", 1)
    numbers = ", ".join(str(i + 1) for i in indices)
    return WatchdogFinding(
        category=FindingCategory.DUPLICATE,
        level=EscalationLevel.WARNING,
        document_index=indices[0],
        field_name=None,
        message_de=(
            f"Mögliches Duplikat: Lieferant '{supplier}' mit "
            f"Re.-Nr. '{inv_nr}' erscheint {len(indices)}x (Belege {numbers})."
        ),
        message_en=(
            f"Possible duplicate: Supplier '{supplier}' with "
            f"invoice no. '{inv_nr}' appears {len(indices)}x (documents {numbers})."
        ),
        evidence={"supplier": supplier, "invoice_number": inv_nr, "document_indices": indices},
    )


def formal_issues(doc: Mapping[str, object]) -> list[str]:
    """B-12: Mängel eines Belegs (Pflichtfelder, Datum, Rechnungsnummer, NaN)."""
    issues = [
        f"Pflichtfeld '{field_key}' fehlt"
        for field_key in MANDATORY_FIELDS_USTG_14
        if is_empty_or_invalid(doc.get(field_key))
    ]
    if str(doc.get("invoice_date", "")).strip().lower() in FORMAL_INVALID_DATES:
        issues.append("Datum ungültig")
    inv_nr = str(doc.get("invoice_number", "")).strip()
    if inv_nr and (len(inv_nr) > MAX_INVOICE_NUMBER_LENGTH or len(inv_nr.split()) > 3):
        issues.append("Rechnungsnummer nicht plausibel")
    for fld in ("net_amount", "vat_amount", "gross_amount"):
        value = doc.get(fld)
        if value is not None and float_is_nan_or_inf(value):
            issues.append(f"NaN/Inf in '{fld}'")
    return issues


def calculate_formal_correctness(documents: Documents, result: WatchdogResult) -> None:
    """B-12: tatsächliche formale Korrektheit; Warnung bzw. Blockade unter 100 %."""
    issues_per_doc: dict[int, list[str]] = {}
    for idx, doc in enumerate(documents):
        doc_issues = formal_issues(doc)
        if doc_issues:
            issues_per_doc[idx] = doc_issues
    n = len(documents)
    formally_correct = n - len(issues_per_doc)
    rate = formally_correct / n if n > 0 else 0.0
    result.metrics.formal_correctness_rate = round(rate, 4)
    if rate < 1.0:
        result.findings.append(_formal_finding(formally_correct, n, rate, issues_per_doc))


def _formal_finding(
    formally_correct: int, n: int, rate: float, issues_per_doc: dict[int, list[str]]
) -> WatchdogFinding:
    incorrect_count = n - formally_correct
    return WatchdogFinding(
        category=FindingCategory.FORMAL_CORRECTNESS,
        level=EscalationLevel.WARNING if rate > 0.5 else EscalationLevel.BLOCKER,
        document_index=None,
        field_name=None,
        message_de=(
            f"Formale Korrektheit: {formally_correct}/{n} Belege "
            f"({rate:.1%}) sind formal korrekt. "
            f"{incorrect_count} Beleg(e) weisen Mängel auf."
        ),
        message_en=(
            f"Formal correctness: {formally_correct}/{n} documents "
            f"({rate:.1%}) are formally correct. "
            f"{incorrect_count} document(s) have deficiencies."
        ),
        evidence={
            "correct_count": formally_correct,
            "total_count": n,
            "rate": rate,
            "issues_by_document": {str(k): v for k, v in list(issues_per_doc.items())[:10]},
        },
    )


def calculate_ocr_metrics(confidences: Sequence[float | None], result: WatchdogResult) -> None:
    """C-12/C-13: Durchschnitt/Minimum und Befund je Beleg unter 80 %."""
    valid = [c for c in confidences if c is not None]
    if not valid:
        return
    result.metrics.avg_ocr_confidence = round(sum(valid) / len(valid), 4)
    result.metrics.min_ocr_confidence = round(min(valid), 4)
    low_confidence_count = 0
    for idx, conf in enumerate(confidences):
        if conf is not None and conf < LOW_OCR_CONFIDENCE:
            low_confidence_count += 1
            result.findings.append(
                WatchdogFinding(
                    category=FindingCategory.MANDATORY_FIELD,
                    level=EscalationLevel.INFO,
                    document_index=idx,
                    field_name="ocr_confidence",
                    message_de=(
                        f"Beleg {idx + 1}: OCR-Confidence niedrig "
                        f"({conf:.1%} < 80%). Risikoorientierte Nachprüfung empfohlen."
                    ),
                    message_en=(
                        f"Document {idx + 1}: OCR confidence low "
                        f"({conf:.1%} < 80%). Risk-oriented review recommended."
                    ),
                    evidence={"ocr_confidence": conf},
                )
            )
    result.metrics.escalated_documents += low_confidence_count


def determine_escalation(result: WatchdogResult, block_threshold: float) -> None:
    """C-10: Info, Warnung oder Blockade (Fehlerrate über der Schwelle oder Blocker)."""
    n = result.metrics.total_documents
    if n == 0:
        return
    levels = {f.level for f in result.findings}
    problem_levels = (EscalationLevel.WARNING, EscalationLevel.BLOCKER)
    docs_with_issues = {
        f.document_index
        for f in result.findings
        if f.level in problem_levels and f.document_index is not None
    }
    error_rate = len(docs_with_issues) / n
    if EscalationLevel.BLOCKER in levels or error_rate > block_threshold:
        result.escalation_level = EscalationLevel.BLOCKER
        result.report_blocked = True
        result.block_reason = (
            f"{len(docs_with_issues)}/{n} Belege ({error_rate:.1%}) "
            f"weisen Extraktionsfehler auf (Schwelle: {block_threshold:.0%}). "
            f"Manuelle Freigabe erforderlich."
        )
        result.metrics.escalated_documents = len(docs_with_issues)
    elif EscalationLevel.WARNING in levels:
        result.escalation_level = EscalationLevel.WARNING
        result.metrics.escalated_documents = len(docs_with_issues)
    else:
        result.escalation_level = EscalationLevel.INFO
