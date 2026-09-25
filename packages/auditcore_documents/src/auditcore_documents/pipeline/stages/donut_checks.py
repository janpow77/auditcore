"""Donut-Kandidaten und ihre Pflicht-Plausibilitätsprüfungen (Plan 2a).

Die Reihenfolge der Prüfungen bestimmt die Reihenfolge der Meldungen je Feld.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, cast

from auditcore_documents.pipeline.stages.donut_values import (
    ALLOWED_VAT_RATES,
    AMOUNTS,
    CENT,
    amount,
    compact,
    iso_date,
    rate,
    vat_id_check,
)
from auditcore_documents.pipeline.stages.validation import validate_iban

#: Steuerzeile: (Satz, Basis, Betrag), jeweils ``None``, wenn nicht eindeutig lesbar.
VatLine = tuple[Decimal | None, Decimal | None, Decimal | None]
#: Normalisierter Wert: Betrag, Text/Datum/Kennung, Steuersätze oder Steuerzeilen.
Parsed = Decimal | str | list[Decimal | None] | list[VatLine] | None
#: Pipeline-Feld → (gedruckter Rohwert, normalisierter Wert oder ``None``).
Candidates = dict[str, tuple[str, Parsed]]
Failed = dict[str, list[str]]
DATE_FIELDS = frozenset({"date", "supply_date", "due_date"})
IDENTIFIER_FIELDS = frozenset({"iban", "vat_id", "bic"})


def _parse_simple(name: str, value: str) -> Parsed:
    if name in AMOUNTS:
        return amount(value)
    if name in DATE_FIELDS:
        return iso_date(value)
    if name in IDENTIFIER_FIELDS:
        return compact(value)
    return " ".join(value.split())


def _simple_fields(donut: Mapping[str, Any]) -> dict[str, object]:
    supplier = donut.get("supplier") if isinstance(donut.get("supplier"), dict) else {}
    return {
        "invoice_number": donut.get("invoice_number"),
        "date": donut.get("invoice_date"),
        "net_amount": donut.get("net_amount"),
        "total": donut.get("total"),
        "iban": donut.get("iban"),
        "vat_id": supplier.get("vat_id") if supplier else None,
        "supplier_name": supplier.get("name") if supplier else None,
        "supply_date": donut.get("supply_date"),
        "due_date": donut.get("due_date"),
        "bic": donut.get("bic"),
    }


def _vat_line_candidates(lines: list[Any]) -> Candidates:
    amounts = [amount(str(line.get("amount", ""))) for line in lines]
    total = (
        sum((a for a in amounts if a is not None), Decimal(0))
        if all(a is not None for a in amounts)
        else None
    )
    vat_lines: list[VatLine] = [
        (
            rate(str(line.get("rate", ""))),
            amount(str(line.get("base", ""))) if line.get("base") else None,
            amount(str(line.get("amount", ""))),
        )
        for line in lines
    ]
    return {
        "vat_amount": (" + ".join(str(line.get("amount", "")) for line in lines), total),
        "vat_rates": (
            " + ".join(str(line.get("rate", "")) for line in lines),
            [rate(str(line.get("rate", ""))) for line in lines],
        ),
        "_vat_lines": ("", vat_lines),
    }


def donut_candidates(donut: Mapping[str, Any]) -> Candidates:
    """Pipeline-Feld → (gedruckter Rohwert, normalisierter Wert oder ``None``)."""
    result: Candidates = {
        name: (value, _parse_simple(name, value))
        for name, value in _simple_fields(donut).items()
        if isinstance(value, str) and value.strip()
    }
    lines = donut.get("vat_lines")
    if isinstance(lines, list) and lines:
        result.update(_vat_line_candidates(lines))
    return result


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


def _text(values: Candidates, name: str) -> str | None:
    parsed = values.get(name, ("", None))[1]
    return parsed if isinstance(parsed, str) else None


def _decimal(values: Candidates, name: str) -> Decimal | None:
    parsed = values.get(name, ("", None))[1]
    return parsed if isinstance(parsed, Decimal) else None


def _rates(values: Candidates) -> list[Decimal | None]:
    return cast(list[Decimal | None], values.get("vat_rates", ("", []))[1] or [])


def vat_lines(values: Candidates) -> list[VatLine]:
    """Steuerzeilen der Kandidaten (leer, wenn Donut keine geliefert hat)."""
    return cast(list[VatLine], values.get("_vat_lines", ("", []))[1])


def _check_readable(values: Candidates, failed: Failed) -> None:
    for name, (_raw, parsed) in values.items():
        if name.startswith("_"):
            continue
        if parsed is None or (isinstance(parsed, list) and None in parsed):
            failed[name].append("nicht eindeutig lesbar")


def _check_invoice_number(values: Candidates, failed: Failed) -> None:
    text = _text(values, "invoice_number")
    if text is None:
        return
    if not 1 <= len(text) <= 40:
        failed["invoice_number"].append("Länge außerhalb 1–40")
    elif iso_date(text) or amount(text) is not None:
        failed["invoice_number"].append("sieht aus wie Datum oder Betrag")


def _check_dates(values: Candidates, failed: Failed, today: date) -> None:
    invoice_date = _text(values, "date")
    if not invoice_date:
        return
    if date.fromisoformat(invoice_date) > today + timedelta(days=366):
        failed["date"].append("mehr als ein Jahr in der Zukunft")
    due = _text(values, "due_date")
    if due and due < invoice_date:
        failed["due_date"].append("Fälligkeit vor Rechnungsdatum")


def _check_identifiers(values: Candidates, failed: Failed) -> tuple[str | None, str | None]:
    """IBAN-Prüfsumme und USt-IdNr.-Prüfung; liefert beide Werte für die Landeswahl."""
    iban = _text(values, "iban")
    if iban:
        valid, message = validate_iban(iban)
        if not valid:
            failed["iban"].append(message)
    vat_id = _text(values, "vat_id")
    if vat_id:
        problem = vat_id_check(vat_id)
        if problem:
            failed["vat_id"].append(problem)
    return iban, vat_id


def _check_vat_rates(values: Candidates, failed: Failed, country: str) -> list[Decimal | None]:
    rates = _rates(values)
    allowed = ALLOWED_VAT_RATES.get(country)
    if allowed is not None and any(r is not None and r not in allowed for r in rates):
        failed["vat_rates"].append(f"Steuersatz in {country} nicht zulässig")
        failed.setdefault("vat_amount", []).append("Steuersatz unzulässig")
    return rates


def _check_vat_lines(values: Candidates, failed: Failed) -> None:
    for line_rate, base, line_amount in vat_lines(values):
        if line_rate is None or base is None or line_amount is None:
            continue
        expected = (base * line_rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)
        if abs(expected - line_amount) > CENT:
            failed.setdefault("vat_amount", []).append("Steuerzeile ≠ Basis × Satz")


def _check_amounts(values: Candidates, failed: Failed, rates: list[Decimal | None]) -> None:
    net = _decimal(values, "net_amount")
    if net is not None and net < 0:
        failed["net_amount"].append("negativer Nettobetrag")
    vat = _decimal(values, "vat_amount")
    total = _decimal(values, "total")
    if net is not None and vat is not None and total is not None:
        lines = max(1, len(rates))
        if abs(net + vat - total) > CENT * lines:
            for name in AMOUNTS:
                failed[name].append("netto + USt ≠ brutto")
