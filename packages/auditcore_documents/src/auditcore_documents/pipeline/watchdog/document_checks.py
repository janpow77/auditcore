"""Belegbezogene Prüfungen C-01 bis C-06 und A-07 (je Beleg ein Befund)."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from decimal import Decimal

from .model import (
    MANDATORY_FIELDS_USTG_14,
    MAX_INVOICE_NUMBER_LENGTH,
    VALID_VAT_RATES_DE,
    EscalationLevel,
    FindingCategory,
    WatchdogFinding,
    WatchdogResult,
)
from .values import (
    INVALID_DATE_MARKERS,
    NAN_MARKERS,
    float_is_nan_or_inf,
    is_empty_or_invalid,
    to_decimal,
    to_float,
    try_parse_date,
)

Documents = Sequence[Mapping[str, object]]

DATE_PATTERNS = (
    re.compile(r"^\d{2}\.\d{2}\.\d{4}$"),  # TT.MM.JJJJ
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),  # JJJJ-MM-TT
)
#: Bekannte Fehlmuster in Rechnungsnummern (C-03), erste Fundstelle zählt.
SUSPICIOUS_INVOICE_PATTERNS = (
    "erneuerbar",
    "ust:",
    "ust-id",
    "steuer",
    "adresse",
    "telefon",
    "email",
    "www.",
    "http",
)
NUMERIC_FIELDS = ("net_amount", "vat_amount", "gross_amount", "vat_rate")


def check_mandatory_fields(documents: Documents, result: WatchdogResult) -> None:
    """C-01: Prüft jeden Beleg gegen die Pflichtfeldliste nach § 14 UStG."""
    field_success_counts: dict[str, int] = dict.fromkeys(MANDATORY_FIELDS_USTG_14, 0)
    docs_with_missing = 0
    for idx, doc in enumerate(documents):
        missing = []
        for field_key, field_desc in MANDATORY_FIELDS_USTG_14.items():
            if is_empty_or_invalid(doc.get(field_key)):
                missing.append(field_desc)
            else:
                field_success_counts[field_key] += 1
        if missing:
            docs_with_missing += 1
            result.findings.append(_missing_fields_finding(idx, missing))

    n = len(documents)
    total_checks = n * len(MANDATORY_FIELDS_USTG_14)
    metrics = result.metrics
    metrics.mandatory_fields_success_rate = (
        sum(field_success_counts.values()) / total_checks if total_checks > 0 else 0.0
    )
    metrics.per_field_success = {
        k: v / n if n > 0 else 0.0 for k, v in field_success_counts.items()
    }
    metrics.documents_with_errors = docs_with_missing
    metrics.documents_with_errors_rate = docs_with_missing / n if n > 0 else 0.0


def _missing_fields_finding(idx: int, missing: list[str]) -> WatchdogFinding:
    return WatchdogFinding(
        category=FindingCategory.MANDATORY_FIELD,
        level=EscalationLevel.WARNING,
        document_index=idx,
        field_name=None,
        message_de=(
            f"Beleg {idx + 1}: {len(missing)} Pflichtfeld(er) fehlen: {', '.join(missing)}"
        ),
        message_en=(
            f"Document {idx + 1}: {len(missing)} mandatory "
            f"field(s) missing: {', '.join(missing)}"
        ),
        evidence={"missing_fields": missing},
        rule_reference="§ 14 UStG",
    )


def check_dates(documents: Documents, result: WatchdogResult) -> None:
    """C-02: kein „Invalid Date“, gültiges oder zumindest parsebares Format."""
    for idx, doc in enumerate(documents):
        date_val = doc.get("invoice_date", "")
        if not date_val:
            continue
        date_str = str(date_val).strip()
        if date_str.lower() in INVALID_DATE_MARKERS:
            result.findings.append(
                _date_finding(
                    idx,
                    date_str,
                    f"Datum nicht extrahierbar (Wert: '{date_str}'). "
                    "Manuelle Nachprüfung erforderlich.",
                    f"Date not extractable (value: '{date_str}'). Manual review required.",
                )
            )
        elif not any(p.match(date_str) for p in DATE_PATTERNS) and not try_parse_date(date_str):
            result.findings.append(
                _date_finding(
                    idx,
                    date_str,
                    f"Datumsformat unbekannt (Wert: '{date_str}'). "
                    "Erwartet: TT.MM.JJJJ oder JJJJ-MM-TT.",
                    f"Unknown date format (value: '{date_str}'). "
                    "Expected: DD.MM.YYYY or YYYY-MM-DD.",
                )
            )


def _date_finding(idx: int, date_str: str, detail_de: str, detail_en: str) -> WatchdogFinding:
    return WatchdogFinding(
        category=FindingCategory.DATE_VALIDATION,
        level=EscalationLevel.WARNING,
        document_index=idx,
        field_name="invoice_date",
        message_de=f"Beleg {idx + 1}: {detail_de}",
        message_en=f"Document {idx + 1}: {detail_en}",
        evidence={"raw_value": date_str},
    )


def invoice_number_issues(inv_str: str) -> list[str]:
    """C-03: Gründe, aus denen eine Rechnungsnummer nicht plausibel ist."""
    issues: list[str] = []
    if len(inv_str) > MAX_INVOICE_NUMBER_LENGTH:
        issues.append(f"zu lang ({len(inv_str)} > {MAX_INVOICE_NUMBER_LENGTH} Zeichen)")
    if len(inv_str.split()) > 3:
        issues.append("sieht nach Fließtext aus, nicht nach Rechnungsnummer")
    lower = inv_str.lower()
    pattern = next((p for p in SUSPICIOUS_INVOICE_PATTERNS if p in lower), None)
    if pattern is not None:
        issues.append(f"verdächtiger Inhalt (enthält '{pattern}')")
    cleaned = re.sub(r"[A-Za-z0-9\-_/.]", "", inv_str)
    if len(cleaned) > len(inv_str) * 0.3:
        issues.append("zu viele Sonderzeichen für eine Rechnungsnummer")
    return issues


def check_invoice_numbers(documents: Documents, result: WatchdogResult) -> None:
    """C-03: Prüft Rechnungsnummern auf plausible Muster."""
    for idx, doc in enumerate(documents):
        inv_nr = doc.get("invoice_number", "")
        if not inv_nr:
            continue
        inv_str = str(inv_nr).strip()
        issues = invoice_number_issues(inv_str)
        if issues:
            result.findings.append(
                WatchdogFinding(
                    category=FindingCategory.INVOICE_NUMBER,
                    level=EscalationLevel.WARNING,
                    document_index=idx,
                    field_name="invoice_number",
                    message_de=(
                        f"Beleg {idx + 1}: Rechnungsnummer '{inv_str}' "
                        f"nicht plausibel: {'; '.join(issues)}"
                    ),
                    message_en=(
                        f"Document {idx + 1}: Invoice number '{inv_str}' "
                        f"implausible: {'; '.join(issues)}"
                    ),
                    evidence={"value": inv_str, "issues": issues},
                )
            )


def check_cross_field_plausibility(
    documents: Documents, result: WatchdogResult, tolerance: Decimal
) -> None:
    """C-04: Brutto = Netto + Steuerbetrag und Steuerbetrag = Netto × Steuersatz."""
    for idx, doc in enumerate(documents):
        net = to_decimal(doc.get("net_amount"))
        vat = to_decimal(doc.get("vat_amount"))
        gross = to_decimal(doc.get("gross_amount"))
        if net is None or vat is None or gross is None:
            continue
        calculated = net + vat
        diff = abs(gross - calculated)
        if diff > tolerance:
            result.findings.append(_gross_finding(idx, net, vat, gross, calculated, diff))
        vat_rate = to_decimal(doc.get("vat_rate"))
        if vat_rate is not None:
            expected_vat = net * vat_rate / Decimal("100")
            if abs(vat - expected_vat) > tolerance:
                result.findings.append(_vat_amount_finding(idx, net, vat, vat_rate, expected_vat))


def _gross_finding(
    idx: int, net: Decimal, vat: Decimal, gross: Decimal, calculated: Decimal, diff: Decimal
) -> WatchdogFinding:
    return WatchdogFinding(
        category=FindingCategory.CROSS_FIELD,
        level=EscalationLevel.WARNING,
        document_index=idx,
        field_name=None,
        message_de=(
            f"Beleg {idx + 1}: Brutto ({gross}) != "
            f"Netto ({net}) + USt ({vat}) = {calculated}. "
            f"Differenz: {diff} EUR."
        ),
        message_en=(
            f"Document {idx + 1}: Gross ({gross}) != "
            f"Net ({net}) + VAT ({vat}) = {calculated}. "
            f"Difference: {diff} EUR."
        ),
        evidence={
            "net": str(net),
            "vat": str(vat),
            "gross": str(gross),
            "calculated": str(calculated),
            "difference": str(diff),
        },
    )


def _vat_amount_finding(
    idx: int, net: Decimal, vat: Decimal, vat_rate: Decimal, expected_vat: Decimal
) -> WatchdogFinding:
    return WatchdogFinding(
        category=FindingCategory.CROSS_FIELD,
        level=EscalationLevel.INFO,
        document_index=idx,
        field_name="vat_amount",
        message_de=(
            f"Beleg {idx + 1}: USt ({vat}) != Netto ({net}) x {vat_rate}% = {expected_vat:.2f}."
        ),
        message_en=(
            f"Document {idx + 1}: VAT ({vat}) != Net ({net}) x {vat_rate}% = {expected_vat:.2f}."
        ),
        evidence={
            "vat": str(vat),
            "expected_vat": str(expected_vat),
            "vat_rate": str(vat_rate),
        },
    )


def check_vat_rates(documents: Documents, result: WatchdogResult) -> None:
    """C-05: Steuersätze gegen gesetzlich zulässige Werte, Hinweis auf Einheitssatz."""
    rates_seen: dict[float, int] = {}
    for idx, doc in enumerate(documents):
        rate = to_float(doc.get("vat_rate"))
        if rate is None:
            continue
        rates_seen[rate] = rates_seen.get(rate, 0) + 1
        if rate not in VALID_VAT_RATES_DE:
            result.findings.append(
                WatchdogFinding(
                    category=FindingCategory.VAT_RATE,
                    level=EscalationLevel.WARNING,
                    document_index=idx,
                    field_name="vat_rate",
                    message_de=(
                        f"Beleg {idx + 1}: Steuersatz {rate}% entspricht "
                        f"keinem gesetzlich zulässigen Satz (0%, 7%, 19%)."
                    ),
                    message_en=(
                        f"Document {idx + 1}: VAT rate {rate}% does not match "
                        f"any legally permitted rate (0%, 7%, 19%)."
                    ),
                    evidence={"vat_rate": rate, "valid_rates": sorted(VALID_VAT_RATES_DE)},
                    rule_reference="§ 12 UStG",
                )
            )
    # Hinweis: Wenn alle den gleichen Satz haben, könnte es ein Default sein
    if len(rates_seen) == 1 and len(documents) > 5:
        result.findings.append(_uniform_rate_finding(next(iter(rates_seen)), len(documents)))


def _uniform_rate_finding(rate: float, count: int) -> WatchdogFinding:
    return WatchdogFinding(
        category=FindingCategory.VAT_RATE,
        level=EscalationLevel.INFO,
        document_index=None,
        field_name="vat_rate",
        message_de=(
            f"Alle {count} Belege zeigen identischen "
            f"Steuersatz ({rate}%). Möglicherweise Default-Wert "
            f"statt tatsächlich extrahiertem Wert."
        ),
        message_en=(
            f"All {count} documents show identical "
            f"VAT rate ({rate}%). Possibly default value "
            f"instead of actually extracted value."
        ),
        evidence={"uniform_rate": rate, "document_count": count},
    )


def supplier_name_issues(name_str: str) -> list[str]:
    """C-06: Gründe, aus denen ein Lieferantenname nicht plausibel ist."""
    issues: list[str] = []
    if name_str == name_str.lower() and len(name_str) > 2:
        issues.append("kein Großbuchstabe (kein plausibler Firmen-/Personenname)")
    if len(name_str) < 3:
        issues.append(f"zu kurz ({len(name_str)} Zeichen)")
    if name_str.replace(" ", "").isdigit():
        issues.append("besteht nur aus Zahlen")
    return issues


def check_supplier_names(documents: Documents, result: WatchdogResult) -> None:
    """C-06: Prüft Lieferantennamen auf Plausibilität."""
    for idx, doc in enumerate(documents):
        name = doc.get("supplier_name", "")
        if not name:
            continue
        name_str = str(name).strip()
        issues = supplier_name_issues(name_str)
        if issues:
            result.findings.append(
                WatchdogFinding(
                    category=FindingCategory.SUPPLIER_NAME,
                    level=EscalationLevel.WARNING,
                    document_index=idx,
                    field_name="supplier_name",
                    message_de=(
                        f"Beleg {idx + 1}: Lieferantenname '{name_str}' "
                        f"nicht plausibel: {'; '.join(issues)}"
                    ),
                    message_en=(
                        f"Document {idx + 1}: Supplier name '{name_str}' "
                        f"implausible: {'; '.join(issues)}"
                    ),
                    evidence={"value": name_str, "issues": issues},
                )
            )


def is_nan_value(value: object) -> bool:
    """A-07: Platzhalter oder NaN/Inf in einem numerischen Feld."""
    return str(value).strip().lower() in NAN_MARKERS or float_is_nan_or_inf(value)


def check_nan_values(documents: Documents, result: WatchdogResult) -> None:
    """A-07: Prüft auf NaN, null, undefined in numerischen Feldern."""
    for idx, doc in enumerate(documents):
        for fld in NUMERIC_FIELDS:
            value = doc.get(fld)
            if value is not None and is_nan_value(value):
                result.findings.append(
                    WatchdogFinding(
                        category=FindingCategory.NAN_VALUE,
                        level=EscalationLevel.WARNING,
                        document_index=idx,
                        field_name=fld,
                        message_de=(
                            f"Beleg {idx + 1}: Feld '{fld}' enthält "
                            f"ungültigen Wert '{value}'. "
                            f"Anzeige als 'n/v' (nicht verfügbar) erforderlich."
                        ),
                        message_en=(
                            f"Document {idx + 1}: Field '{fld}' contains "
                            f"invalid value '{value}'. "
                            f"Must display as 'n/a' (not available)."
                        ),
                        evidence={"field": fld, "raw_value": str(value)},
                    )
                )
