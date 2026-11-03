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
- Herausgelöst aus FlowStat (audit_designer); Korrekturen in
  `docs/behavior-changes.md`.
