"""Deutsche Meldungen der Validierungsregeln mit dem englischen Wortlaut des Originals.

Die Regeln der Validierungsstufe (``VAL_*``) meldeten im Original englisch.
Seit Entscheidung D9 (2026-09-26) melden sie deutsch mit echten Umlauten;
Regelkennungen (``rule_id``), Regelnamen, Schweregrade, Ergebnisse,
Kennzeichen (``FAIL_…``, ``REVIEW_…``) und Belege (``evidence``) bleiben
unverändert. Jede Meldung steht hier einmal mit deutscher Vorlage und dem
englischen Originalwortlaut; beide Richtungen lassen sich umrechnen
(:func:`german_message`, :func:`original_message`). Die Wiedergabetests
vergleichen mit dem Original über :func:`original_message`.

Zahlen werden wie im Original formatiert (Dezimalpunkt), damit die Umrechnung
eindeutig bleibt; die Belege tragen die Rohwerte.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache

_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


@dataclass(frozen=True)
class RuleMessage:
    """Eine Meldung: Kennung, englischer Originalwortlaut und deutsche Fassung."""

    code: str
    original: str
    german: str


_MESSAGES = (
    RuleMessage(
        "iban_missing",
        "No IBAN found, skipping validation",
        "Keine IBAN gefunden, Prüfung entfällt",
    ),
    RuleMessage("iban_valid", "IBAN checksum valid: {iban}", "IBAN-Prüfsumme gültig: {iban}"),
    RuleMessage("iban_length", "Invalid IBAN length: {length}", "Ungültige IBAN-Länge: {length}"),
    RuleMessage(
        "iban_country_length",
        "Invalid IBAN length for {country}: expected {expected}, got {length}",
        "Ungültige IBAN-Länge für {country}: erwartet {expected}, gefunden {length}",
    ),
    RuleMessage("iban_checksum", "IBAN checksum invalid", "IBAN-Prüfsumme ungültig"),
    RuleMessage(
        "iban_characters", "IBAN contains invalid characters", "IBAN enthält ungültige Zeichen"
    ),
    RuleMessage(
        "vat_id_missing",
        "No VAT ID found, skipping validation",
        "Keine USt-IdNr. gefunden, Prüfung entfällt",
    ),
    RuleMessage(
        "vat_id_country",
        "Unknown VAT ID country: {country}",
        "Unbekanntes Länderkennzeichen der USt-IdNr.: {country}",
    ),
    RuleMessage(
        "vat_id_valid", "VAT ID format valid: {vat_id}", "Format der USt-IdNr. gültig: {vat_id}"
    ),
    RuleMessage(
        "vat_id_invalid",
        "VAT ID format invalid for country {country}",
        "Format der USt-IdNr. für {country} ungültig",
    ),
    RuleMessage(
        "sum_incomplete",
        "Not all amount fields available for plausibility check",
        "Nicht alle Betragsfelder für die Summenprüfung vorhanden",
    ),
    RuleMessage(
        "sum_unparsable",
        "Could not parse amount fields as numbers",
        "Betragsfelder sind keine lesbaren Zahlen",
    ),
    RuleMessage(
        "sum_plausible",
        "Sum plausible: {net} + {vat} = {calculated} (total: {total})",
        "Summe plausibel: {net} + {vat} = {calculated} (Gesamtbetrag: {total})",
    ),
    RuleMessage(
        "sum_mismatch",
        "Sum mismatch: {net} + {vat} = {calculated}, but total is {total}",
        "Summe weicht ab: {net} + {vat} = {calculated}, Gesamtbetrag ist aber {total}",
    ),
    RuleMessage("ocr_missing", "No OCR metrics available", "Keine OCR-Kennzahlen vorhanden"),
    RuleMessage(
        "ocr_ok",
        "OCR confidence OK: {confidence} >= {threshold}",
        "OCR-Konfidenz ausreichend: {confidence} ≥ {threshold}",
    ),
    RuleMessage(
        "ocr_low",
        "OCR confidence low: {confidence} < {threshold}",
        "OCR-Konfidenz niedrig: {confidence} < {threshold}",
    ),
    RuleMessage("amounts_clear", "All amounts unambiguous", "Alle Beträge eindeutig"),
    RuleMessage(
        "amounts_unclear",
        "Ambiguous or invalid amounts: {fields}",
        "Mehrdeutige oder ungültige Beträge: {fields}",
    ),
    RuleMessage(
        "fraud_disabled",
        "Fraud detection disabled in analysis modules",
        "Betrugsprüfung in den Analysemodulen abgeschaltet",
    ),
    RuleMessage(
        "fraud_insufficient",
        "Insufficient data for fraud detection (missing invoice_number or supplier_name)",
        "Zu wenig Daten für die Betrugsprüfung (Rechnungsnummer oder Lieferant fehlt)",
    ),
    RuleMessage(
        "fraud_no_session",
        "No database session for fraud detection",
        "Keine Datenbankanbindung für die Betrugsprüfung",
    ),
    RuleMessage(
        "fraud_error", "Fraud detection error: {error}", "Fehler in der Betrugsprüfung: {error}"
    ),
    RuleMessage(
        "fraud_critical",
        "CRITICAL fraud risk detected: {factors}",
        "Kritisches Betrugsrisiko erkannt: {factors}",
    ),
    RuleMessage("fraud_high", "High fraud risk: {factors}", "Hohes Betrugsrisiko: {factors}"),
    RuleMessage(
        "fraud_medium", "Medium fraud risk: {factors}", "Mittleres Betrugsrisiko: {factors}"
    ),
    RuleMessage(
        "fraud_passed",
        "Fraud detection passed (risk level: {level})",
        "Betrugsprüfung ohne Auffälligkeit (Risikostufe: {level})",
    ),
    RuleMessage("donut_missing", "No Donut result", "Kein Donut-Ergebnis"),
    RuleMessage("donut_plausible", "Donut values plausible", "Donut-Werte plausibel"),
    RuleMessage("donut_confirmed", "Donut values confirmed", "Donut-Werte bestätigt"),
)

#: Alle Meldungen nach Kennung.
RULE_MESSAGES: dict[str, RuleMessage] = {m.code: m for m in _MESSAGES}


def say(code: str, **values: object) -> str:
    """Deutsche Meldung ``code`` mit eingesetzten Werten."""
    return RULE_MESSAGES[code].german.format(**values)


def _pattern(template: str) -> re.Pattern[str]:
    parts: list[str] = []
    last = 0
    for match in _PLACEHOLDER.finditer(template):
        parts.append(re.escape(template[last : match.start()]))
        parts.append(f"(?P<{match.group(1)}>.*?)")
        last = match.end()
    parts.append(re.escape(template[last:]))
    return re.compile("".join(parts), re.DOTALL)


@cache
def _patterns(attribute: str) -> tuple[tuple[re.Pattern[str], RuleMessage], ...]:
    return tuple((_pattern(getattr(m, attribute)), m) for m in _MESSAGES)


def _convert(text: str, source: str, target: str) -> str:
    for pattern, entry in _patterns(source):
        match = pattern.fullmatch(text)
        if match:
            converted: str = getattr(entry, target).format(**match.groupdict())
            return converted
    return text


def original_message(text: str) -> str:
    """Englischer Originalwortlaut einer deutschen Meldung (unbekannte Texte unverändert)."""
    return _convert(text, "german", "original")


def german_message(text: str) -> str:
    """Deutsche Fassung eines englischen Originalwortlauts (unbekannte Texte unverändert)."""
    return _convert(text, "original", "german")
