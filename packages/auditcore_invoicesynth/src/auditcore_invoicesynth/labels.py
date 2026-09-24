"""Beschriftungs-Synonyme je Feld (deutsch überwiegend, englischer Anteil über den Plan)."""

from __future__ import annotations

from random import Random
from typing import Literal

Language = Literal["de", "en"]

LABELS: dict[str, dict[Language, tuple[str, ...]]] = {
    "title_invoice": {"de": ("Rechnung", "RECHNUNG", "Rechnung Nr."), "en": ("Invoice", "INVOICE")},
    "title_credit_note": {"de": ("Gutschrift", "GUTSCHRIFT"), "en": ("Credit Note",)},
    "invoice_number": {
        "de": ("Rechnungsnummer", "Rechnungs-Nr.", "Rechnungsnr.", "Beleg-Nr.", "Re.-Nr."),
        "en": ("Invoice No.", "Invoice Number", "Invoice #"),
    },
    "credit_note_number": {
        "de": ("Gutschriftsnummer", "Gutschrift-Nr.", "Beleg-Nr."),
        "en": ("Credit Note No.",),
    },
    "invoice_date": {
        "de": ("Rechnungsdatum", "Datum", "Belegdatum", "Ausstellungsdatum"),
        "en": ("Invoice Date", "Date"),
    },
    "supply_date": {
        "de": ("Leistungsdatum", "Lieferdatum", "Leistungszeitraum bis"),
        "en": ("Delivery Date", "Service Date"),
    },
    "due_date": {
        "de": ("Fällig am", "Zahlbar bis", "Fälligkeit", "Zahlungsziel"),
        "en": ("Due Date", "Payable by"),
    },
    "net_amount": {
        "de": ("Nettobetrag", "Summe netto", "Zwischensumme", "Netto", "Warenwert netto"),
        "en": ("Net Amount", "Subtotal", "Net Total"),
    },
    "vat": {
        "de": ("USt.", "MwSt.", "Umsatzsteuer", "zzgl. USt.", "Mehrwertsteuer"),
        "en": ("VAT", "Tax"),
    },
    "total": {
        "de": ("Gesamtbetrag", "Rechnungsbetrag", "zu zahlen", "Summe brutto", "Endbetrag"),
        "en": ("Total", "Amount Due", "Grand Total"),
    },
    "iban": {"de": ("IBAN",), "en": ("IBAN",)},
    "bic": {"de": ("BIC", "SWIFT-BIC", "BIC/SWIFT"), "en": ("BIC", "SWIFT")},
    "vat_id": {
        "de": ("USt-IdNr.", "USt.-ID", "Umsatzsteuer-ID", "USt-ID-Nr."),
        "en": ("VAT ID", "VAT Reg. No."),
    },
    "vat_id_at": {"de": ("UID", "UID-Nr.", "USt-IdNr."), "en": ("VAT ID",)},
    "tax_number": {"de": ("Steuernummer", "St.-Nr."), "en": ("Tax No.",)},
    "bank": {"de": ("Bankverbindung", "Bank"), "en": ("Bank details", "Bank")},
    "recipient_vat_id": {
        "de": ("Ihre USt-IdNr.", "USt-IdNr. Empfänger"),
        "en": ("Customer VAT ID",),
    },
    "position": {"de": ("Pos.", "Nr."), "en": ("Item", "No.")},
    "description": {"de": ("Bezeichnung", "Leistung", "Beschreibung"), "en": ("Description",)},
    "quantity": {"de": ("Menge", "Anz."), "en": ("Qty",)},
    "unit_price": {"de": ("Einzelpreis", "E-Preis"), "en": ("Unit Price",)},
    "line_amount": {"de": ("Gesamt", "Betrag"), "en": ("Amount",)},
    "page": {"de": ("Seite",), "en": ("Page",)},
    "carry_over": {"de": ("Übertrag",), "en": ("Carried forward",)},
}

SYNTHETIC_MARKER = "SYNTHETISCH – kein echter Beleg, Kennungen fiktiv"
SYNTHETIC_FOOTER = "SYNTHETISCHE TRAININGSDATEN – nicht zahlen, keine Steuerwirkung"

VAT_NOTES = {
    "kleinunternehmer": (
        "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.",
        "Kein Ausweis der Umsatzsteuer aufgrund der Kleinunternehmerregelung (§ 19 UStG).",
    ),
    "reverse_charge": (
        "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge).",
        "Innergemeinschaftliche Leistung – Steuerschuldnerschaft des Leistungsempfängers.",
    ),
}


def pick(rng: Random, key: str, language: Language) -> str:
    """Zufälliges Synonym; für fehlende Sprachvarianten die deutsche Liste."""
    options = LABELS[key].get(language) or LABELS[key]["de"]
    return rng.choice(options)
