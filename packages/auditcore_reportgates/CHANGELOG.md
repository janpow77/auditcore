# Changelog – auditcore_reportgates

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
