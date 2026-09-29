# REST-Vertrag Bestandsprüfung (`documents_batch_checks/1`, `auditcore_documents.web`)

Stand 2026-09-27. Vertrag zwischen `auditcore_documents.web`
(`BatchCheckService`) und der Oberfläche `<flowaudit-batch-checks>` aus
`@auditcore/ui` (Vue `BatchChecks`, React `FlowauditBatchChecks`). Geprüft wird
ein **Bestand vieler Belege** – Zeilen einer Tabelle oder Ergebnisse der
Belegerkennung (`documents_extraction/1`) – mit dem Extraktionsqualitäts-Watchdog
und zwei Ergänzungsprüfungen. Das Ergebnis ist eine Arbeitshilfe, keine
Prüfungsentscheidung; der Dienst speichert nichts.

## Regeln und Umsetzung

Die Regeln C-01 bis C-13 stammen aus dem Verbesserungskatalog
HA-EFRE-2026-0847 von flowinvoice (`services/extraction_quality_watchdog.py`,
übernommen als `auditcore_documents.pipeline.watchdog`, Verhalten unverändert).
A-07 und B-12 gehören zum selben Watchdog. Lücken in Rechnungsnummern und die
USt-IdNr.-Konsistenz kennt der Katalog **nicht**; sie sind als ERG-01/ERG-02
ergänzt (`pipeline/watchdog/inventory_checks.py`) und abschaltbar.

| Regel | Prüfung | Art | Stufe |
|---|---|---|---|
| C-01 | Neun Pflichtangaben nach § 14 Abs. 4 UStG je Beleg (leer/Platzhalter = fehlt) | Beleg | Warnung |
| C-02 | Rechnungsdatum ohne Fehlerwert und in lesbarem Format | Beleg | Warnung |
| C-03 | Rechnungsnummer ≤ 30 Zeichen, ≤ 3 Wörter, keine fremden Angaben, ≤ 30 % Sonderzeichen | Beleg | Warnung |
| C-04 | Brutto = Netto + Steuer (Warnung), Steuer = Netto × Satz (Hinweis), Toleranz 0,02 EUR | Beleg | Warnung/Hinweis |
| C-05 | Steuersatz 0/7/19 % (§ 12 UStG); Hinweis bei einheitlichem Satz über > 5 Belege | Beleg/Bestand | Warnung/Hinweis |
| C-06 | Lieferantenname ≥ 3 Zeichen, mit Großbuchstabe, nicht nur Ziffern | Beleg | Warnung |
| C-07 | Anteil eines Lieferanten am Volumen über der Schwelle (30 %) | Bestand | Warnung |
| C-08 | Summe der Einzelbeträge gegen das ausgewiesene Gesamtvolumen (1 Cent je Beleg) – nur mit `total_volume` | Bestand | Warnung |
| C-09 | Dubletten: gleicher Lieferant (ohne Rechtsform) mit gleicher Rechnungsnummer | Bestand | Warnung |
| C-10 | Eskalation Info/Warnung/Blockade; Blockade bei Anteil fehlerhafter Belege > Schwelle (20 %) oder formaler Korrektheit ≤ 50 % | Lauf | – |
| C-11 | Maschinenlesbarer Export (JSON; zusätzlich CSV) über `POST /export` | Lauf | – |
| C-12 | Kennzahlen: Pflichtfeldquote gesamt/je Feld, Belege mit Mängeln, formale Korrektheit, OCR-Konfidenz | Lauf | – |
| C-13 | OCR-Konfidenz je Beleg unter 80 % – nur mit `ocr_confidence` | Beleg | Hinweis |
| A-07 | NaN/null/undefined/inf in Beträgen oder Steuersatz | Beleg | Warnung |
| B-12 | Formale Korrektheit des Bestands; Warnung unter 100 %, Blockade bis 50 % | Bestand | Warnung/Blockade |
| ERG-01 | Lücken im Zählteil der Rechnungsnummern je Lieferant und Nummernkreis (Abstand ≤ 50) | Bestand | Hinweis |
| ERG-02 | Lieferant mit mehreren USt-IdNr./Steuernummern (Warnung bei zwei USt-IdNr.), Kennung bei mehreren Lieferanten (Hinweis) | Bestand | Warnung/Hinweis |

ERG-01/ERG-02 gehen nicht in die Eskalation C-10 ein (sie betreffen den Inhalt,
nicht die Extraktionsqualität). Lücken sind im Bestand eines Empfängers üblich,
weil Lieferanten über alle Kunden fortlaufend nummerieren.

## Einbinden

```python
from auditcore_documents.web import (
    BatchCheckService,
    BatchCheckSettings,
    batch_check_routes,
    create_batch_check_app,
    create_batch_check_router,
)

service = BatchCheckService(BatchCheckSettings(max_documents=5000))
app.mount("/api/batch-checks", create_batch_check_app(service))  # Starlette
fastapi_app.include_router(create_batch_check_router(service, prefix="/api/batch-checks"))
```

Extras `web` bzw. `fastapi` wie die Belegerkennung. Anmeldung, CORS und
Ratenbegrenzung sind Sache der Anwendung; ein Lauf läuft im Thread-Pool.

## Endpunkte

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/catalogue` | Vertrag, Regeln (`code`, `title`, `checks`, `legal_basis`, `scope`, `source`), Felder mit Spaltennamen, Vorgaben, Stufen, Grenzen, Exportformate |
| POST | `/runs` | Bestand prüfen |
| POST | `/export` | wie `/runs` plus `format` (`json` = vollständige Antwort, C-11; `csv` = Befundliste, Excel: Semikolon, UTF-8-BOM, eine Zeile je Befund und Beleg) |

### Anfrage

```json
{"documents": [
   {"ref": "B-001", "invoice_number": "RE-2026-0101", "invoice_date": "15.01.2026",
    "supplier_name": "Muster Bau GmbH", "customer_name": "…", "supplier_vat_id": "DE100000001",
    "description": "…", "net_amount": 10000, "vat_rate": 19, "vat_amount": 1900,
    "gross_amount": "11.900,00", "ocr_confidence": 0.97},
   {"contract": "documents_extraction/1", "document": {"filename": "rechnung.pdf"},
    "ocr": {"avg_confidence": 0.91}, "fields": [{"name": "invoice_number", "value": "A-1"}]}
 ],
 "options": {"total_volume": 48500, "tolerance": 0.02, "concentration_threshold": 0.3,
             "block_threshold": 0.2, "supplementary": true}}
```

Belege sind flache Datensätze oder Antworten der Belegerkennung (erkannt an
`fields`; `date` → `invoice_date`, `total` → `gross_amount`, `vat_id` →
`supplier_vat_id`, `ocr.avg_confidence` → `ocr_confidence`,
`document.filename` → `ref`). Unbekannte Schlüssel werden ignoriert. Beträge
dürfen deutsch geschrieben sein; Unlesbares bleibt stehen und wird gemeldet.
`ref` fehlt → „Beleg n“. Alle Optionen sind optional.

### Antwort

| Feld | Inhalt |
|---|---|
| `summary` | `documents`, `findings`, `documents_with_findings`, `escalation_level` (`info`/`warning`/`blocker`), `report_blocked`, `block_reason`, `timestamp` |
| `metrics` | Kennzahlen C-12 des Watchdogs |
| `rules[]` | jede Regel mit `status` (`passed`, `findings`, `not_checked`, `result`), `note` (Grund für „nicht geprüft“ bzw. Ergebnis von C-10 bis C-12), `findings`, `documents`, `level` |
| `findings[]` | `id` (B-0001 …, in Regelreihenfolge), `rule`, `category`, `level`, `field`, `message` (Begründung, deutsch), `documents` (betroffene Belege, 0-basiert; leer = Gesamtbestand), `evidence`, `rule_reference` |
| `documents[]` | `index`, `ref`, Kerndaten, `findings`, `level`, `rules` |
| `options`, `contract`, `library`, `stored` (`false`) | |

## Fehler

`{"error": {"code", "message"}}` mit deutscher Meldung: 400 `invalid_json`,
413 `too_large` (Körper über `max_body_bytes` oder mehr als `max_documents`
Belege), 422 `invalid_input` (z. B. „Beleg 3: 'ocr_confidence' muss zwischen 0
und 1 liegen.“, unzulässige Option, unbekanntes Exportformat).

## Oberfläche

`createBatchchecksRestPort({ baseUrl: '/api/batch-checks' })` aus
`@auditcore/ui-core` (auch über `@auditcore/ui` und `@auditcore/ui-react`).
Die Datei liest der gemeinsame TableImport-Controller (CSV/TSV) bzw. der Kern
(JSON); Spalten werden über die Spaltennamen des Katalogs zugeordnet, das
Dezimaltrennzeichen aus allen Zahlenspalten erkannt. Eigenschaften `port`,
`result`, `locale`; Ereignisse `checks-completed` und `error` (React:
`onChecksCompleted`, `onError`). Paritätsfälle:
`packages-js/ui-core/test/parity/cases-batchchecks.ts`; Demo:
`packages-js/ui/demo/batch_checks_demo.py` mit dem synthetischen Beispielbestand
`packages/auditcore_documents/tests/fixtures/batch/bestand.csv`.
