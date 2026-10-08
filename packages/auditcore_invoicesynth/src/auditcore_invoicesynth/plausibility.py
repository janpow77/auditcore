"""Plausibilitätsprüfung für die Bewertung (Plan 2a, Zusammenführung).

Spiegelt die Regeln von ``auditcore_documents`` (``donut_checks``) auf den
flachen Feldern der Bewertung, ohne das Paket zu importieren: Prüfziffern für
IBAN (ISO 13616, mod 97) und USt-IdNr. (DE, AT), lesbares Datum, Rechnungsnummer
ohne Datums- oder Betragsform und ``netto + USt = brutto`` (± 1 Cent je
Steuerzeile; nur vollständig prüfbare Beträge). Felder, die hier durchfallen,
würde die Pipeline nicht automatisch übernehmen; daraus entsteht die
Falschwert-Quote nach Plausibilität (E6).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from auditcore_invoicesynth.formats import parse_date, parse_money
from auditcore_invoicesynth.identifiers import iban_valid, vat_id_valid

AMOUNT_FIELDS = ("net_amount", "vat_amount", "total")
DATE_FIELDS = ("invoice_date", "supply_date", "due_date")
CENT = Decimal("0.01")


def plausible_fields(flat: Mapping[str, str]) -> set[str]:
    """Felder der flachen Vorhersage, die eine Plausibilitätsprüfung übernehmen würde."""
    accepted = {name for name, value in flat.items() if _field_ok(name, value)}
    if not _amounts_consistent(flat):
        accepted -= set(AMOUNT_FIELDS)
    return accepted


def _field_ok(name: str, value: str) -> bool:
    if name == "iban":
        return iban_valid(value)
    if name == "supplier.vat_id":
        return vat_id_valid(value)
    if name in DATE_FIELDS:
        return parse_date(value) is not None
    if name in AMOUNT_FIELDS:
        amount = parse_money(value)
        return amount is not None and amount >= 0
    if name == "invoice_number":
        text = value.strip()
        return 1 <= len(text) <= 40 and parse_date(text) is None and parse_money(text) is None
    return bool(value.strip())


def _amounts_consistent(flat: Mapping[str, str]) -> bool:
    """``netto + USt = brutto`` (± 1 Cent je Steuersatz).

    Beträge werden nur übernommen, wenn alle drei lesbar sind und zusammenpassen:
    fehlt einer, ist die Summe nicht prüfbar und geht zur Prüfung (Befund Diagnosesatz
    T2b: ohne Steuerzeile wurden falsche Gesamtbeträge sonst ungeprüft übernommen).
    """
    net, vat, total = (parse_money(flat.get(name, "")) for name in AMOUNT_FIELDS)
    if net is None or vat is None or total is None:
        return False
    lines = max(1, len(flat.get("vat_rates", "").split("+")))
    return abs(net + vat - total) <= CENT * lines
