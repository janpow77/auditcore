"""Anreicherung eines Generator-Datensatzes zu einem vollständigen deutschen Beleg.

Grundlage ist ``auditcore_invoicegenerator.InvoiceScenario`` (Parteien,
Rechnungsnummer, Datumsangaben, Positionen). Ergänzt werden fiktive IBAN/BIC,
prüfziffer-gültige USt-IdNr./UID, Steuernummer und Steuerzeilen nach dem
gewählten Steuerschema. Beträge werden mit ``Decimal`` neu und kaufmännisch
gerundet berechnet (``netto + USt = brutto`` je Beleg exakt).

Fehlerfälle werden hier eingespielt; der gedruckte Wert weicht dann bewusst
vom richtigen ab (``printed_total``), das Ziel-JSON enthält das Gedruckte.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from decimal import Decimal
from random import Random
from typing import Any, Literal

from auditcore_invoicegenerator import InvoiceRecord

from auditcore_invoicesynth.formats import cents
from auditcore_invoicesynth.identifiers import (
    BankAccount,
    fictional_bank_account,
    fictional_tax_number,
    fictional_vat_id,
)

VatScheme = Literal[
    "de_19",
    "de_7",
    "de_mixed",
    "de_kleinunternehmer",
    "de_reverse_charge",
    "at_20",
    "at_13",
    "at_10",
    "at_mixed",
]
DocumentKind = Literal["invoice", "credit_note"]
SynthError = Literal["wrong_total", "missing_vat_id", "missing_iban"]

VAT_SCHEMES: dict[str, tuple[str, tuple[Decimal, ...]]] = {
    "de_19": ("DE", (Decimal(19),)),
    "de_7": ("DE", (Decimal(7),)),
    "de_mixed": ("DE", (Decimal(19), Decimal(7))),
    "de_kleinunternehmer": ("DE", (Decimal(0),)),
    "de_reverse_charge": ("DE", (Decimal(0),)),
    "at_20": ("AT", (Decimal(20),)),
    "at_13": ("AT", (Decimal(13),)),
    "at_10": ("AT", (Decimal(10),)),
    "at_mixed": ("AT", (Decimal(20), Decimal(10))),
}
#: Zulässige Steuersätze je Land (Plausibilitätsprüfung, Bewertung).
ALLOWED_VAT_RATES = {
    "DE": frozenset({Decimal(19), Decimal(7), Decimal(0)}),
    "AT": frozenset({Decimal(20), Decimal(13), Decimal(10), Decimal(0)}),
}
ERRORS: tuple[SynthError, ...] = ("wrong_total", "missing_vat_id", "missing_iban")


@dataclass(frozen=True)
class Party:
    name: str
    street: str
    postal_city: str
    country: str
    vat_id: str
    tax_number: str


@dataclass(frozen=True)
class Position:
    description: str
    quantity: int
    unit_price: Decimal
    amount: Decimal
    rate: Decimal


@dataclass(frozen=True)
class VatLine:
    rate: Decimal
    base: Decimal
    amount: Decimal


@dataclass(frozen=True)
class SynthInvoice:
    """Vollständiger synthetischer Beleg mit richtigen und gedruckten Werten."""

    document_id: str
    kind: DocumentKind
    country: str
    currency: str
    invoice_number: str
    invoice_date: date
    supply_date: date
    due_date: date
    supplier: Party
    recipient: Party
    bank: BankAccount | None
    positions: tuple[Position, ...]
    vat_lines: tuple[VatLine, ...]
    net_amount: Decimal
    vat_amount: Decimal
    total: Decimal
    printed_total: Decimal
    vat_scheme: str
    errors: tuple[str, ...] = ()
    source: dict[str, Any] = field(default_factory=dict)

    @property
    def vat_note_kind(self) -> str | None:
        if self.vat_scheme == "de_kleinunternehmer":
            return "kleinunternehmer"
        if self.vat_scheme == "de_reverse_charge":
            return "reverse_charge"
        return None


def _party(raw: dict[str, Any], country: str, rng: Random) -> Party:
    street, _, postal_city = str(raw["address"]).partition(", ")
    return Party(
        name=str(raw["name"]),
        street=street,
        postal_city=postal_city or str(raw.get("city", "")),
        country=country,
        vat_id=fictional_vat_id(rng, country),
        tax_number=fictional_tax_number(rng, country),
    )


def _invoice_number(rng: Random, original: str, index: int, year: int, kind: DocumentKind) -> str:
    """Zur Hälfte die Generator-Nummer, sonst gestreute Formate gegen Katalog-Lernen."""
    choice = rng.randrange(6)
    prefix = "GS" if kind == "credit_note" else "RE"
    if choice < 3:
        return original if kind == "invoice" else original.replace("RG", "GS", 1)
    if choice == 3:
        return f"{year}-{index:05d}"
    if choice == 4:
        return f"{prefix}{rng.randint(10000, 999999)}"
    return f"{prefix}/{year}/{rng.randint(1, 9999):04d}-{rng.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}"


def _split_amount(total: Decimal, parts: int, rng: Random) -> list[Decimal]:
    """Betrag in ``parts`` positive Cent-Teile zerlegen, Summe exakt."""
    total_cents = int(total * 100)
    if total_cents < parts:
        return [total]
    cuts = sorted(rng.sample(range(1, total_cents), parts - 1))
    bounds = [0, *cuts, total_cents]
    return [Decimal(bounds[i + 1] - bounds[i]) / 100 for i in range(parts)]


def enrich(
    record: InvoiceRecord,
    *,
    rng: Random,
    vat_scheme: str,
    kind: DocumentKind = "invoice",
    errors: tuple[str, ...] = (),
    expand_positions: int = 1,
    invoice_date: date | None = None,
) -> SynthInvoice:
    """Generator-Datensatz → ``SynthInvoice``.

    ``expand_positions`` > 1 zerlegt jede Position in so viele Teilpositionen
    (mehrseitige Vorlage); die Summe je Ursprungsposition bleibt gleich.
    ``invoice_date`` ersetzt die fortlaufenden Generator-Daten (Leistungs- und
    Fälligkeitsdatum werden dann relativ dazu gezogen).
    """
    _check_arguments(vat_scheme, errors)
    country, rates = VAT_SCHEMES[vat_scheme]
    recipient_country = "AT" if vat_scheme == "de_reverse_charge" else country
    supplier = _party(dict(record["supplier"]), country, rng)
    recipient = _party(dict(record["beneficiary"]), recipient_country, rng)
    bank = fictional_bank_account(rng, country)
    positions = _positions(record, rates, expand_positions, rng)
    vat_lines = _vat_lines(positions)
    net = sum((line.base for line in vat_lines), Decimal(0))
    vat = sum((line.amount for line in vat_lines), Decimal(0))
    total = net + vat
    printed_total = _printed_total(total, errors, rng)
    if "missing_vat_id" in errors:
        supplier = replace(supplier, vat_id="")
    invoice_date, supply_date, due_date = _dates(record, invoice_date, rng)
    return SynthInvoice(
        document_id=str(record["id"]),
        kind=kind,
        country=country,
        currency="EUR",
        invoice_number=_invoice_number(
            rng, str(record["invoice_number"]), int(record["id"][-5:]), invoice_date.year, kind
        ),
        invoice_date=invoice_date,
        supply_date=supply_date,
        due_date=due_date,
        supplier=supplier,
        recipient=recipient,
        bank=None if "missing_iban" in errors else bank,
        positions=tuple(positions),
        vat_lines=tuple(vat_lines),
        net_amount=net,
        vat_amount=vat,
        total=total,
        printed_total=printed_total,
        vat_scheme=vat_scheme,
        errors=tuple(sorted(errors)),
        source=_source(record),
    )


def _check_arguments(vat_scheme: str, errors: tuple[str, ...]) -> None:
    if vat_scheme not in VAT_SCHEMES:
        raise ValueError(f"Unbekanntes Steuerschema: {vat_scheme}")
    unknown = set(errors) - set(ERRORS)
    if unknown:
        raise ValueError(f"Unbekannte Fehlerfälle: {sorted(unknown)}")


def _source(record: InvoiceRecord) -> dict[str, Any]:
    """Herkunft des Generator-Datensatzes (Profil, Seed, Dokument)."""
    return {
        "generator": "auditcore_invoicegenerator.InvoiceScenario",
        "profile": record["metadata"].get("profile"),
        "seed": record["metadata"].get("seed"),
        "document_id": record["id"],
    }


def _positions(
    record: InvoiceRecord, rates: tuple[Decimal, ...], expand_positions: int, rng: Random
) -> list[Position]:
    """Positionen mit Steuersatz im Wechsel; ``expand_positions`` > 1 zerlegt jede Position."""
    positions: list[Position] = []
    for number, item in enumerate(record["line_items"]):
        rate = rates[number % len(rates)]
        quantity = int(item["quantity"])
        unit_price = cents(Decimal(str(item["unit_price"])))
        amount = cents(unit_price * quantity)
        if expand_positions > 1:
            for part_no, part in enumerate(_split_amount(amount, expand_positions, rng), 1):
                positions.append(
                    Position(f"{item['description']} (Teil {part_no})", 1, part, part, rate)
                )
        else:
            positions.append(Position(str(item["description"]), quantity, unit_price, amount, rate))
    return positions


def _vat_lines(positions: list[Position]) -> list[VatLine]:
    """Eine Steuerzeile je Satz, absteigend, Steuer je Zeile kaufmännisch gerundet."""
    vat_lines = []
    for rate in sorted({p.rate for p in positions}, reverse=True):
        base = sum((p.amount for p in positions if p.rate == rate), Decimal(0))
        vat_lines.append(VatLine(rate, base, cents(base * rate / 100)))
    return vat_lines


def _printed_total(total: Decimal, errors: tuple[str, ...], rng: Random) -> Decimal:
    """Gedruckter Gesamtbetrag; beim Fehlerfall ``wrong_total`` bewusst abweichend und positiv."""
    if "wrong_total" not in errors:
        return total
    delta = cents(Decimal(rng.choice((1, 10, 100))) * rng.choice((1, -1)) / rng.choice((1, 100)))
    return total + delta if total + delta > 0 else total + abs(delta)


def _dates(
    record: InvoiceRecord, invoice_date: date | None, rng: Random
) -> tuple[date, date, date]:
    """Rechnungs-, Leistungs- und Fälligkeitsdatum; ohne ``invoice_date`` aus dem Generator."""
    if invoice_date is None:
        return (
            date.fromisoformat(record["invoice_date"]),
            date.fromisoformat(record["supply_date"]),
            date.fromisoformat(record["due_date"]),
        )
    supply_date = invoice_date - timedelta(days=rng.randint(0, 30))
    due_date = invoice_date + timedelta(days=rng.choice((7, 10, 14, 30, 30, 45)))
    return invoice_date, supply_date, due_date
