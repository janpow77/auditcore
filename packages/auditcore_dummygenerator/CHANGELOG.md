# Changelog auditcore_dummygenerator

## 0.1.2 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. README nach der Vorlage (docs/bibliotheken/readme-vorlage.md).

## 0.1.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: Die 58 beobachteten Originalfälle
(`tests/fixtures/legacy_observed.json`) und alle übrigen Tests laufen
unverändert grün. Zusätzlich wurden alte und neue Implementierung mit 4 500
zufällig erzeugten Anfragen und Einzelaufrufen (alle Feldtypen,
Belegliste-Kriterien, Abweichungsszenarien, Fehlerfälle) sowie parallelen
Läufen mit 250 bis 2 200 Zeilen verglichen: Ausgaben, Ausnahmen und
RNG-Endzustand sind identisch.

- `generate_field` als Regeltabelle: Die wörtlichen Vergleiche
  `field_type == "..."` bleiben erhalten, weil das Profilregister seine
  Feldkennungen daraus ableitet; Erzeuger laufen nur für den gewählten Typ.
  Parameterauflösung für Datum, Betrag und Zweck in kleinen Hilfsmethoden.
- `apply_deviation` ruft je Szenario einen eigenen Schritt auf
  (`_raise_eligible_above_paid`, `_pay_before_invoice`, `_negate_amounts`).
- Neues Modul `rows.py`: Zeilenzusammenstellung (Auto-Increment,
  Belegliste-Kriterien als Tabelle `RECEIPT_LIST_CRITERIA` in der bisherigen
  Vorrangfolge),
  Batch-Aufteilung und die beiden Worker-Backends.
  `BatchGenerationError`, `get_optimal_workers` und `_generate_batch` bleiben
  über `auditcore_dummygenerator.generator` erreichbar; das Objekt ist
  jeweils dasselbe.
- Kataloge kompakter notiert (gleiche Werte und Reihenfolge), IBAN-, Telefon-
  und Rechnungsnummern-Ziffern über eine Hilfe `_digits` mit derselben Zahl und
  Reihenfolge von Zufallsziehungen.
- `JsonObject` als benannter Grenztyp für die Legacy-Anfragen und -Zeilen.

Profile: Die Regeln stehen weiter in `generator.py`. Weil sich dessen Bytes
geändert haben, sind `implementation_sha256`, `content_hash`, `updated_at` und
`change_reason` aller 27 Profile erneuert; der alte Fingerabdruck steht im
Änderungsgrund. Die Profilversionen bleiben 0.1.0 (keine fachliche Änderung,
siehe `docs/profile-versioning.md`).

Abhängige Pakete: `auditcore_invoicegenerator` pinnt jetzt
`auditcore_dummygenerator==0.1.1` (nur Pin, Provenienzfeld, README und
Installationstest).

| Messung (nur `src/`) | 0.1.0 | 0.1.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 4 | 0 |
| Module > 400 Zeilen | 1 (`generator.py`, 654) | 0 (`generator.py` 399, `rows.py` 257) |
| Funktionen > 60 Zeilen (Code-Gate) | 4 | 0 |
| `Any` (Textvorkommen / Code-Gate `any_usages`) | 21 / 19 | 10 / 7 |
| mypy --strict | sauber | sauber |

Code-Gate-Baseline (`quality/baseline.json`) für das Paket entsprechend
abgesenkt.

Keine Umbenennungen öffentlicher Namen.
