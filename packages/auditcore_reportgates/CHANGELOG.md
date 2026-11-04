# Changelog – auditcore_reportgates

## 0.2.0 – 2026-11-04 – Parameter für bestehende Lesarten

Additiv; ohne die neuen Parameter rechnet alles wie 0.1.0 – mit einer
Korrektur (siehe unten).

- `ClaimSyntax` (Modul `syntax`) für `extract_claims`, `check_paragraph` und
  `ambiguous_numbers`: Einheitenmenge `units` (Standard `DEFAULT_UNITS`,
  schmal `BASIC_UNITS`: nur `%`, `Prozent`, `Prozentpunkt(e)`, `Mio.`, `Mrd.`,
  `Tsd.`), Lesart eines einzelnen Punkts `point` (`PointReading.AMBIGUOUS`
  Standard, `DECIMAL` liest „2.5“ als 2,5, `SPLIT` trennt am Punkt wie das
  FlowStat-Prosa-Gate) und `masks` (`DEFAULT_MASKS`, abschaltbar).
- `Claim` trägt zusätzlich `unit_text` (gedruckte Einheit, auch geerbt),
  `unit_inherited` und `token` (gedruckte Zahl mit Vorzeichen und Einheit).
- `scale_of(header, currency=CURRENCY)`: Betragsskala einer Überschrift
  unabhängig von Prozent- oder Punktwörtern; Mischüberschriften
  (`Veränderung Mio. Euro (%)`) behalten die Skala. `unit_of` unverändert.
- `tolerance`/`same_value(..., epsilon=0)`: absoluter Puffer für Werte aus
  Gleitkommarechnung (`15.850000000000001` gegen gedruckt `15,8`).
- `format_de(..., rounding=ROUND_HALF_UP)`: Rundungsart wählbar
  (`ROUNDING_MODES`), z. B. `ROUND_HALF_EVEN`; unbekannte Art ist
  `ValueError`. Negative Nachkommastellen bleiben `ValueError`, jetzt mit
  Meldung und Hinweis auf vorheriges Skalieren (keine Rundung auf Zehner).
- Korrektur (Standardlesart): Eine Zahl, an die unmittelbar eine weitere Ziffer
  oder Punkt/Komma mit Ziffer anschließt, wird nicht mehr abgeschnitten.
  „10.10“ war bisher die Zahl 1 und „1.2345“ die Zahl 1234; beide sind jetzt
  `zahl_mehrdeutig`.

## 0.1.0 – 2026-11-03 – Prosa-Zahlen-Gate, Wertegate und Freigabeentscheidung

- `read_number`, `read_cell`, `format_de`: gedruckte deutsche Zahlen mit
  Nachkommastellen; Fehlwert (`k. A.`) und echte Null getrennt.
- `unit_of`, `conversion_exponent`: Prozent, Prozentpunkte und skalierte
  Beträge als getrennte Dimensionen; Skala aus der Spalteneinheit.
- `extract_claims`, `check_claim`, `check_paragraph`, `combine`: Zahlen im
  Fließtext gegen Objekt- und Kontextwerte; `contradiction` und `unbound`
  sind Befunde.
- `compare_tables`: Referenzwerte je Zeile und Spalte, Datenstandsbindung.
- `release`: fail-closed über Pflicht-Gates (`passed` / `failed` / `not_run`).
- Jahreszahlen im Fließtext: `Euro`, `EUR` und `€` sind Einheiten; eine
  Einheit oder ein Zählwort (`Vorhaben`, `Teilnehmende` …) nach der Zahl oder
  ihrem Spannenpartner ist Gegenbeleg gegen „Jahr“ (`bis 2050 Vorhaben`,
  `zwischen 1950 und 2100 Euro`). Satzanfang vor Verb oder Komma
  (`2023 stieg …`) gilt als Jahr; `allowed_years` bleibt der verlässliche Weg.
- Fehlwerte (geänderte Semantik): `.` (Zahlenwert unbekannt, Destatis), `:`
  (Eurostat: nicht verfügbar) und `...` sind Fehlwertzeichen (`MISSING`),
  weder Zahl noch Text. Eine Ergebniszelle `.` gegen einen Referenzwert ergibt
  `wert_fehlt`, eine Referenzzelle `:` gegen einen Ergebniswert
  `fehlend_vs_wert`; als Referenz sind sie kein `text_in_zahlenspalte` mehr.
  Wer diese Zeichen anders liest, übergibt eigene `missing_markers`.
- Wertegate: Spalten, die sich nur in der Einheit unterscheiden, teilen den
  Schlüssel; wird er gebraucht, ist das `spalte_mehrdeutig` (dokumentiert).
- Herausgelöst aus FlowStat (audit_designer); Korrekturen in
  `docs/behavior-changes.md`.
