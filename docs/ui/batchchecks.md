# Bestandsprüfung (`BatchChecks` ↔ `FlowauditBatchChecks`)

Gerüst erzeugt mit `npm run ui:neu -- batchchecks BatchChecks`, danach
fachlich ausgebaut. REST-Vertrag und Regelliste:
[batch-checks-rest.md](batch-checks-rest.md).

| Schicht | Datei |
|---|---|
| Kern | `packages-js/ui-core/src/batchchecks/` (`createBatchchecksController`, `buildBatchchecksRequest`, `batchchecksMessages`, `createBatchchecksRestPort`, Anzeige) |
| Stil | `packages-js/ui-core/styles/batchchecks.css` |
| Vue / Web Component | `BatchChecks` / `<flowaudit-batch-checks>` (`packages-js/ui/src/batchchecks/`) |
| React | `FlowauditBatchChecks` (`packages-js/ui-react/src/batchchecks/`) |
| Paritätsfälle | `packages-js/ui-core/test/parity/cases-batchchecks.ts` (5 Fälle, 2 Interaktionsfolgen) |
| Demo | Seite „Bestandsprüfung“ (`demo/pages/batchchecks/`), Backend `demo/batch_checks_demo.py` unter `/api/batch-checks` |

## Vertrag

Eigenschaften: `port`, `result` (vorhandenes Ergebnis anzeigen), `locale`.
Ereignisse: `checks-completed` (React `onChecksCompleted`), `error` (React `onError`).

Ablauf: Datei wählen (CSV/TSV über den TableImport-Controller oder JSON),
Spalten zuordnen (automatisch über die Spaltennamen des Katalogs, änderbar),
Gesamtvolumen für C-08 und Ergänzungsprüfungen einstellen, „Bestand prüfen“.
Ergebnis: Eskalationsstufe, Kennzahlen, Regelübersicht mit Status aller
Regeln, Befunde mit Begründung und betroffenen Belegen (nach Regel filterbar),
Export JSON/CSV.
