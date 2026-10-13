"""Field types of the free table and their parameters, as data.

The same table drives the strict recipe check and the catalogue a user
interface builds its forms from. ``kind`` of a parameter is one of ``int``,
``decimal``, ``text``, ``date``, ``bool``, ``choice``, ``field``, ``fields``
and ``values``; ``field``/``fields`` name other columns of the same table.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Param:
    """One parameter of a field type or rule."""

    name: str
    kind: str
    label: str
    default: object = None
    low: int = 0
    high: int = 0
    options: tuple[str, ...] = ()
    required: bool = False


@dataclass(frozen=True)
class FieldType:
    """One field type: identifier, German label, output cell kind and parameters."""

    id: str
    label: str
    cell: str
    params: tuple[Param, ...] = ()
    note: str = ""


_DAYS = 3650
_MAX_AMOUNT = 1_000_000_000

FIELD_TYPES: tuple[FieldType, ...] = (
    FieldType("sequence", "Laufende Nummer", "int", (
        Param("start", "int", "Start", 1, -1_000_000, 1_000_000_000),
        Param("step", "int", "Schrittweite", 1, 1, 1_000_000),
    )),
    FieldType("pattern", "Nummer mit Muster", "text", (
        Param("pattern", "text", "Muster", "RE-{JJJJ}-{NNNN}", 1, 60, required=True),
        Param("date_field", "field", "Datumsspalte für das Jahr"),
    ), "Platzhalter: {JJJJ}, {JJ}, {MM}, {NNNN} laufende Nummer, {ZZZ} Zufallsziffern, "
       "{AA} Zufallsbuchstaben. Für Aktenzeichen, Steuer- und Registernummern nur "
       "erkennbar unechte Muster verwenden."),
    FieldType("person", "Person", "text", (
        Param("source", "choice", "Quelle", "role", options=("role", "catalog")),
        Param("part", "choice", "Bestandteil", "full", options=("full", "first", "last")),
    ), "Standard sind Rollenbezeichnungen. Die Namenskataloge enthalten häufige echte "
       "Vor- und Nachnamen; Kombinationen treffen lebende Personen."),
    FieldType("company", "Firma mit Rechtsform", "text", (),
              "Generischer Beispielname aus einer kurzen Liste; Namen wiederholen sich. "
              "Ähnlichkeiten mit bestehenden Unternehmen sind zufällig und nicht beabsichtigt."),
    FieldType("address", "Anschrift", "text", (
        Param("part", "choice", "Bestandteil", "full",
              options=("full", "street", "postal_code", "city", "country")),
    ), "Erfundene Straße, echte zusammengehörige Postleitzahl und Stadt; alle "
       "Anschriftsspalten einer Zeile gehören zusammen."),
    FieldType("nuts", "Gebietskennung (NUTS 3)", "text", (),
              "Passend zur Stadt der Zeile."),
    FieldType("email", "E-Mail-Adresse", "text", (),
              "Immer in der reservierten Beispieldomäne example.org."),
    FieldType("date", "Datum im Bereich", "date", (
        Param("start", "date", "von"),
        Param("end", "date", "bis"),
    ), "Ohne Angabe: die 365 Tage bis zum Bezugsdatum."),
    FieldType("date_offset", "Datum nach oder vor anderer Spalte", "date", (
        Param("field", "field", "Bezugsspalte", required=True),
        Param("min_days", "int", "Mindestabstand in Tagen", 0, -_DAYS, _DAYS),
        Param("max_days", "int", "Höchstabstand in Tagen", 30, -_DAYS, _DAYS),
    ), "Negative Abstände liegen vor dem Bezugsdatum."),
    FieldType("amount", "Betrag", "amount", (
        Param("min", "decimal", "Minimum", "100.00", 0, _MAX_AMOUNT),
        Param("max", "decimal", "Maximum", "10000.00", 0, _MAX_AMOUNT),
        Param("decimals", "int", "Nachkommastellen", 2, 0, 2),
        Param("distribution", "choice", "Verteilung", "uniform", options=("uniform", "skewed")),
    )),
    FieldType("amount_factor", "Betrag aus anderer Spalte", "amount", (
        Param("field", "field", "Bezugsspalte", required=True),
        Param("min_factor", "decimal", "kleinster Faktor", "0.50", 0, 100),
        Param("max_factor", "decimal", "größter Faktor", "1.00", 0, 100),
    )),
    FieldType("computed", "Berechnete Spalte", "amount", (
        Param("operation", "choice", "Rechenart", "sum",
              options=("sum", "difference", "product", "rate")),
        Param("fields", "fields", "Spalten", low=1, high=2, required=True),
        Param("rate", "decimal", "Satz (nur Rechenart „rate“)", "0.19", 0, 100),
    ), "Summe, Differenz oder Produkt zweier Spalten oder Spalte mal Satz, auf Cent gerundet."),
    FieldType("integer", "Ganze Zahl", "int", (
        Param("min", "int", "Minimum", 0, -_MAX_AMOUNT, _MAX_AMOUNT),
        Param("max", "int", "Maximum", 100, -_MAX_AMOUNT, _MAX_AMOUNT),
    )),
    FieldType("decimal", "Dezimalzahl", "decimal", (
        Param("min", "decimal", "Minimum", "0", -_MAX_AMOUNT, _MAX_AMOUNT),
        Param("max", "decimal", "Maximum", "1", -_MAX_AMOUNT, _MAX_AMOUNT),
        Param("decimals", "int", "Nachkommastellen", 2, 0, 6),
    )),
    FieldType("choice", "Auswahl", "text", (
        Param("values", "values", "Werte mit Gewichten", low=1, high=50, required=True),
    )),
    FieldType("boolean", "Wahrheitswert", "text", (
        Param("probability", "decimal", "Anteil „wahr“", "0.50", 0, 1),
        Param("style", "choice", "Darstellung", "ja_nein",
              options=("ja_nein", "true_false", "one_zero")),
    )),
    FieldType("text", "Text", "text", (
        Param("min_parts", "int", "Bausteine mindestens", 1, 1, 8),
        Param("max_parts", "int", "Bausteine höchstens", 2, 1, 8),
    )),
    FieldType("iban", "IBAN", "text", (
        Param("valid", "bool", "formal gültig", False),
    ), "Standard: Prüfziffer gezielt verfehlt, die Kennung besteht keine Prüfung."),
    FieldType("bic", "BIC", "text", (), "Fester, erkennbar synthetischer Bankteil SYNT."),
    FieldType("vat_id", "USt-IdNr.", "text", (
        Param("valid", "bool", "formal gültig", False),
    ), "Standard: Prüfziffer gezielt verfehlt, die Kennung besteht keine Prüfung."),
    FieldType("constant", "Konstante", "text", (
        Param("value", "text", "Wert", "", 0, 200),
    )),
)  # fmt: skip

#: Rules a field may carry in addition to its type.
RULES: tuple[FieldType, ...] = (
    FieldType("when", "Wert abhängig von anderer Spalte", "", (
        Param("field", "field", "Spalte", required=True),
        Param("equals", "text", "hat den Wert", "", 0, 200, required=True),
        Param("value", "text", "dann", "", 0, 200),
        Param("otherwise", "text", "sonst (leer lassen: erzeugter Wert)", None, 0, 200),
    )),
    FieldType("sum_to", "Summe der Spalte bindet an Vorgabewert", "", (
        Param("total", "decimal", "Summe", "10000.00", 0, _MAX_AMOUNT, required=True),
        Param("group_by", "field", "je Gruppe nach Spalte"),
    ), "Nur für Spalten des Typs Betrag; der Rest geht in die letzte Zeile."),
)  # fmt: skip

TYPES_BY_ID = {item.id: item for item in FIELD_TYPES}
RULES_BY_ID = {item.id: item for item in RULES}
