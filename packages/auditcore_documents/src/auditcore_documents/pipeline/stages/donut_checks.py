"""Pflicht-Plausibilitätsprüfungen der Donut-Kandidaten (Plan 2a).

Die Reihenfolge der Prüfungen bestimmt die Reihenfolge der Meldungen je Feld.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP
from typing import Any

from auditcore_documents.pipeline.stages.donut_values import (
    ALLOWED_VAT_RATES,
    AMOUNTS,
    CENT,
    amount,
    iso_date,
    vat_id_check,
)
from auditcore_documents.pipeline.stages.validation import validate_iban

#: Pipeline-Feld → (gedruckter Rohwert, normalisierter Wert oder ``None``).
Candidates = dict[str, tuple[str, Any]]
Failed = dict[str, list[str]]


def plausibility_failures(values: Candidates, today: date) -> Failed:
    """Fehlgeschlagene Pflichtprüfungen je Feld (leere Liste = plausibel)."""
    failed: Failed = {name: [] for name in values if not name.startswith("_")}
    _check_readable(values, failed)
    _check_invoice_number(values, failed)
    _check_dates(values, failed, today)
    iban, vat_id = _check_identifiers(values, failed)
    rates = _check_vat_rates(values, failed, (vat_id or iban or "DE")[:2])
    _check_vat_lines(values, failed)
    _check_amounts(values, failed, rates)
    return failed


def _parsed(values: Candidates, name: str, default: Any = None) -> Any:
    return values.get(name, ("", default))[1]


def _check_readable(values: Candidates, failed: Failed) -> None:
    for name, (_raw, parsed) in values.items():
        if name.startswith("_"):
            continue
        if parsed is None or (isinstance(parsed, list) and None in parsed):
            failed[name].append("nicht eindeutig lesbar")


def _check_invoice_number(values: Candidates, failed: Failed) -> None:
    number = values.get("invoice_number")
    if not number or number[1] is None:
        return
    text = number[1]
    if not 1 <= len(text) <= 40:
        failed["invoice_number"].append("Länge außerhalb 1–40")
    elif iso_date(text) or amount(text) is not None:
        failed["invoice_number"].append("sieht aus wie Datum oder Betrag")


def _check_dates(values: Candidates, failed: Failed, today: date) -> None:
    invoice_date = _parsed(values, "date")
    if not invoice_date:
        return
    if date.fromisoformat(invoice_date) > today + timedelta(days=366):
        failed["date"].append("mehr als ein Jahr in der Zukunft")
    due = _parsed(values, "due_date")
    if due and due < invoice_date:
        failed["due_date"].append("Fälligkeit vor Rechnungsdatum")


def _check_identifiers(values: Candidates, failed: Failed) -> tuple[Any, Any]:
    """IBAN-Prüfsumme und USt-IdNr.-Prüfung; liefert beide Werte für die Landeswahl."""
    iban = _parsed(values, "iban")
    if iban:
        valid, message = validate_iban(iban)
        if not valid:
            failed["iban"].append(message)
    vat_id = _parsed(values, "vat_id")
    if vat_id:
        problem = vat_id_check(vat_id)
        if problem:
            failed["vat_id"].append(problem)
    return iban, vat_id


def _check_vat_rates(values: Candidates, failed: Failed, country: str) -> list[Any]:
    rates: list[Any] = _parsed(values, "vat_rates", []) or []
    allowed = ALLOWED_VAT_RATES.get(country)
    if allowed is not None and any(r is not None and r not in allowed for r in rates):
        failed["vat_rates"].append(f"Steuersatz in {country} nicht zulässig")
        failed.setdefault("vat_amount", []).append("Steuersatz unzulässig")
    return rates


def _check_vat_lines(values: Candidates, failed: Failed) -> None:
    for line_rate, base, line_amount in _parsed(values, "_vat_lines", []):
        if None in (line_rate, base, line_amount):
            continue
        expected = (base * line_rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)
        if abs(expected - line_amount) > CENT:
            failed.setdefault("vat_amount", []).append("Steuerzeile ≠ Basis × Satz")


def _check_amounts(values: Candidates, failed: Failed, rates: list[Any]) -> None:
    net = _parsed(values, "net_amount")
    if net is not None and net < 0:
        failed["net_amount"].append("negativer Nettobetrag")
    vat = _parsed(values, "vat_amount")
    total = _parsed(values, "total")
    if net is not None and vat is not None and total is not None:
        lines = max(1, len(rates))
        if abs(net + vat - total) > CENT * lines:
            for name in AMOUNTS:
                failed[name].append("netto + USt ≠ brutto")
