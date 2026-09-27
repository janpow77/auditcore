"""Regelkatalog der Bestandsprüfung: was C-01 bis C-13, A-07, B-12 und ERG-01/02 prüfen."""

from __future__ import annotations

from dataclasses import dataclass

from auditcore_documents.pipeline.watchdog import FindingCategory
from auditcore_documents.pipeline.watchdog.inventory_checks import (
    INVOICE_NUMBER_GAP,
    MAX_NUMBER_GAP,
    VAT_ID_CONSISTENCY,
)

#: Herkunft der Regeln: Verbesserungskatalog (flowinvoice) oder Ergänzung von auditcore.
CATALOGUE = "Verbesserungskatalog HA-EFRE-2026-0847 (flowinvoice)"
SUPPLEMENT = "Ergänzung auditcore"


@dataclass(frozen=True)
class BatchRule:
    """Eine Prüfregel: Kennung, Titel, was geprüft wird, Rechtsgrundlage und Art."""

    code: str
    title: str
    checks: str
    legal_basis: str = ""
    #: ``document`` (je Beleg), ``inventory`` (über den Bestand) oder ``run`` (Ergebnis des Laufs).
    scope: str = "document"
    categories: tuple[str, ...] = ()
    source: str = CATALOGUE

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "title": self.title,
            "checks": self.checks,
            "legal_basis": self.legal_basis,
            "scope": self.scope,
            "source": self.source,
        }


RULES: tuple[BatchRule, ...] = (
    BatchRule(
        "C-01",
        "Pflichtangaben",
        "Neun Pflichtfelder je Beleg: Leistender, Leistungsempfänger, Steuernummer oder "
        "USt-IdNr., Ausstellungsdatum, Rechnungsnummer, Leistungsbeschreibung, Entgelt, "
        "Steuersatz und Steuerbetrag; leere Werte und Platzhalter gelten als fehlend.",
        "§ 14 Abs. 4 UStG",
        categories=(FindingCategory.MANDATORY_FIELD,),
    ),
    BatchRule(
        "C-02",
        "Rechnungsdatum lesbar",
        "Kein Fehlerwert (z. B. „Invalid Date“) und ein lesbares Datumsformat "
        "(TT.MM.JJJJ, JJJJ-MM-TT, TT/MM/JJJJ, MM/TT/JJJJ, TT-MM-JJJJ).",
        categories=(FindingCategory.DATE_VALIDATION,),
    ),
    BatchRule(
        "C-03",
        "Rechnungsnummer plausibel",
        "Höchstens 30 Zeichen, höchstens drei Wörter, keine fremden Angaben (Steuer, USt-Id, "
        "Adresse, Telefon, E-Mail, Web) und höchstens 30 % Sonderzeichen.",
        categories=(FindingCategory.INVOICE_NUMBER,),
    ),
    BatchRule(
        "C-04",
        "Beträge rechnerisch stimmig",
        "Brutto = Netto + Steuerbetrag (Warnung) und Steuerbetrag = Netto × Steuersatz "
        "(Hinweis), jeweils mit Toleranz (Vorgabe 0,02 EUR).",
        categories=(FindingCategory.CROSS_FIELD,),
    ),
    BatchRule(
        "C-05",
        "Steuersatz zulässig",
        "Nur 0 %, 7 % oder 19 %; Hinweis, wenn mehr als fünf Belege alle denselben Satz "
        "tragen (möglicher Vorgabewert statt gelesenem Wert).",
        "§ 12 UStG",
        categories=(FindingCategory.VAT_RATE,),
    ),
    BatchRule(
        "C-06",
        "Lieferantenname plausibel",
        "Mindestens drei Zeichen, mindestens ein Großbuchstabe, nicht nur Ziffern.",
        categories=(FindingCategory.SUPPLIER_NAME,),
    ),
    BatchRule(
        "C-07",
        "Lieferantenkonzentration",
        "Anteil eines Lieferanten (ohne Rechtsform) am Volumen (brutto, sonst netto) über "
        "der Schwelle (Vorgabe 30 %).",
        scope="inventory",
        categories=(FindingCategory.CONCENTRATION,),
    ),
    BatchRule(
        "C-08",
        "Summenabgleich",
        "Summe der Einzelbeträge (brutto, sonst netto) gegen das ausgewiesene Gesamtvolumen; "
        "Toleranz 1 Cent je Beleg. Nur mit Angabe des Gesamtvolumens.",
        scope="inventory",
        categories=(FindingCategory.SUM_RECONCILIATION,),
    ),
    BatchRule(
        "C-09",
        "Dubletten",
        "Gleicher Lieferant (ohne Rechtsform) mit gleicher Rechnungsnummer mehrfach im Bestand.",
        scope="inventory",
        categories=(FindingCategory.DUPLICATE,),
    ),
    BatchRule(
        "C-10",
        "Eskalation",
        "Stufe Info, Warnung oder Blockade. Blockade, wenn der Anteil der Belege mit Warnung "
        "die Schwelle übersteigt (Vorgabe 20 %) oder die formale Korrektheit (B-12) höchstens "
        "50 % beträgt; dann ist eine manuelle Freigabe erforderlich.",
        scope="run",
    ),
    BatchRule(
        "C-11",
        "Maschinenlesbarer Export",
        "Ergebnis mit allen Befunden und Kennzahlen als JSON; zusätzlich Befundliste als CSV.",
        scope="run",
    ),
    BatchRule(
        "C-12",
        "Kennzahlen der Extraktionsqualität",
        "Erfüllungsquote der Pflichtfelder gesamt und je Feld, Belege mit fehlenden "
        "Pflichtfeldern, formale Korrektheit sowie mittlere und kleinste OCR-Konfidenz.",
        scope="run",
    ),
    BatchRule(
        "C-13",
        "OCR-Konfidenz je Beleg",
        "Belege unter 80 % OCR-Konfidenz werden zur risikoorientierten Nachprüfung "
        "vorgemerkt. Nur mit OCR-Konfidenzen im Bestand.",
    ),
    BatchRule(
        "A-07",
        "Ungültige Zahlenwerte",
        "NaN, null, undefined, inf oder n/a in Netto, Steuerbetrag, Brutto oder Steuersatz "
        "(Anzeige als „n/v“ erforderlich).",
        categories=(FindingCategory.NAN_VALUE,),
    ),
    BatchRule(
        "B-12",
        "Formale Korrektheit",
        "Anteil der Belege ohne fehlende Pflichtangabe, ungültiges Datum, unplausible "
        "Rechnungsnummer oder NaN-Betrag; Warnung unter 100 %, Blockade bis 50 %.",
        scope="inventory",
        categories=(FindingCategory.FORMAL_CORRECTNESS,),
    ),
    BatchRule(
        "ERG-01",
        "Lücken in Rechnungsnummern",
        "Je Lieferant und Nummernkreis (gleiches Präfix) fehlende Zählwerte zwischen zwei "
        f"vorhandenen Nummern (Abstand höchstens {MAX_NUMBER_GAP}). Hinweis: Lieferanten "
        "nummerieren über alle Kunden fortlaufend, Lücken sind im Bestand eines Empfängers "
        "üblich.",
        "§ 14 Abs. 4 Satz 1 Nr. 4 UStG",
        scope="inventory",
        categories=(INVOICE_NUMBER_GAP,),
        source=SUPPLEMENT,
    ),
    BatchRule(
        "ERG-02",
        "USt-IdNr.-Konsistenz",
        "Ein Lieferant mit verschiedenen USt-IdNr./Steuernummern (Warnung bei zwei "
        "verschiedenen USt-IdNr.) und dieselbe Kennung bei verschiedenen Lieferanten (Hinweis).",
        "§ 14 Abs. 4 Satz 1 Nr. 2 UStG",
        scope="inventory",
        categories=(VAT_ID_CONSISTENCY,),
        source=SUPPLEMENT,
    ),
)
RULES_BY_CODE = {rule.code: rule for rule in RULES}
_CODE_BY_CATEGORY = {c: rule.code for rule in RULES for c in rule.categories}


def rule_code(category: str, field_name: str | None) -> str:
    """Kennung der Regel eines Watchdog-Befunds (C-13 steht im Original unter C-01)."""
    if category == FindingCategory.MANDATORY_FIELD and field_name == "ocr_confidence":
        return "C-13"
    return _CODE_BY_CATEGORY.get(category, category)
