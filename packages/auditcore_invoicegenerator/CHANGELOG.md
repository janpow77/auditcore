# Changelog auditcore_invoicegenerator

## 0.2.3 – 2026-09-26 – Paketstand für Release v0.4.2

Keine Verhaltensänderung. README mit den Installationsangaben aus Release v0.4.1. Pins: `auditcore_dummygenerator==0.1.3`.

## 0.2.2 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. Pin `auditcore_dummygenerator==0.1.2`; README nach der Vorlage.

## 0.2.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: Die 180 beobachteten Legacyfälle
(`legacy-golden*.json`, inklusive RNG-Endzustand) und alle übrigen Tests laufen
unverändert grün. Zusätzlich lokal alte und neue Implementierung mit 30 000
zufälligen Aufrufen von `generate_invoice` (alle Lieferanten, Problemtypen,
unbekannte Länder/Kategorien) und `generate_line_items` verglichen – Datensätze
und RNG-Zustand identisch. `pdf.py` ist unverändert, PDF-Ausgaben sind damit
bytegleich.

- Synthetische Kataloge (Arbeitspakete, 117 Lieferanten, Problemlieferanten,
  Leistungsvorlagen, Produkte, Modelle, Veranstaltungen, Reiseziele) in
  `_legacy_catalog.py`; Werte, Reihenfolge, Schlüsselreihenfolge und Kommentare
  unverändert, Lieferanten als kompakte Zeilen. `_legacy` stellt `SUPPLIERS`
  und `PROBLEM_SUPPLIERS` weiter bereit.
- `generate_invoice` in Hilfen zerlegt (`_problem_base_amount` als geordnete
  Tabelle mit `==`-Vergleich, `_amounts`, `_supplier_party`, Konstante
  `BENEFICIARY`). Die Zufallsziehungen bleiben in derselben Reihenfolge,
  einschließlich des immer gezogenen Grundbetrags und der immer gezogenen
  Ersatz-Hausnummer.
- Typen: Lieferanten in den Legacy-Regeln `Mapping[str, str]`, Summen als
  `Amounts`.

Provenienz: Inhaltshashes des Legacyprofils (neu mit `_legacy_catalog.py`),
`modified_at` und Änderungsgrund erneuert; Profilversion bleibt 0.1.0, der
PDF-Renderer bleibt Template-Version 0.2.0 (siehe `docs/versioning.md`).
`tests/test_provenance.py` prüft Paket- und Rendererversion deshalb getrennt.

Abhängige Pakete: `auditcore_invoicesynth` pinnt jetzt
`auditcore_invoicegenerator==0.2.1` (Pin, Installationstest, README, NOTICE).

| Messung (nur `src/`) | 0.2.0 | 0.2.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 0 | 0 |
| Module > 400 Zeilen | 1 (`_legacy.py`, 1 296) | 0 (`_legacy_catalog.py` 357, `_legacy.py` 283) |
| Funktionen > 60 Zeilen (Code-Gate) | 1 (`generate_invoice`, 90) | 0 |
| `Any` (Textvorkommen / Code-Gate `any_usages`) | 20 / 15 | 19 / 14 |
| mypy --strict | sauber | sauber |

Keine Umbenennungen öffentlicher Namen.

## 0.2.0 – 2026-09-22

- Optionaler deterministischer PDF-Renderer `render_pdf` (Extra `pdf`,
  ReportLab), `PDFDependencyError` bei fehlendem Extra.
- Profilversionierung an Paketreleases ausgerichtet (`docs/versioning.md`).

## 0.1.0 – 2026-09-22

Erstausgabe: `InvoiceScenario` mit expliziten Fehlerfällen und
Duplikaten, JSON-Ausgabe, charakterisiertes Profil
`flowinvoice-demo-fb2d185` (180 aufgezeichnete Fälle, auch mit nativen
Summen unter Python 3.11), Profilkennungen an versionierte Provenienz
gebunden, Abhängigkeit `auditcore_dummygenerator`.
