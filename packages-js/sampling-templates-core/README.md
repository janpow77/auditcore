# @auditcore/sampling-templates-core

## Zweck

Framework-freier Kern der Webfassung der „Stichprobenvorlagen 2021–2027“ nach DelVO (EU) 2023/67: Rechenkerne je Blatt mit den Zelladressen der Vorlage, Methodendefinitionen, Arbeitsstand als Datei und Excel-Austausch.

Für Anwendungen, in denen Prüfbehörden ihre Stichprobenberechnungen im Browser
durchführen (zuerst ECOHESION im audit_designer). Das Prinzip: eingeben,
Ergebnisse herunterladen, den Arbeitsstand als Datei speichern und später
wieder öffnen – ohne Server, ohne Anmeldung, ohne Netzanfragen. Die Oberfläche
liegt in [`@auditcore/sampling-templates-vue`](../sampling-templates-vue/README.md).

**Stand 0.1.2:** Alle Blätter der Vorlage sind gebaut und gegen sie
abgeglichen: Grundgesamtheit (02), MUS-Standardansatz (03–07), einfaches
Zufallsstichprobenverfahren (08–12), nichtstatistische Verfahren (13–16),
Unterstichproben (17), Gesamtfehlerquote nach Anhang III (18), Bericht (20) und
die Altvorlagen von 2017 (X1–X4; X1a als Datentabelle). Blatt 01 liegt als
Daten vor. Ein Blatt ergänzen oder ändern:
[docs/blatt-ergaenzen.md](docs/blatt-ergaenzen.md).

**Abgrenzung zu `auditcore_sampling` (Python):** Dort stehen allgemeine
Stichprobenverfahren (Umfänge, systematische MUS-Auswahl, Schichtung, Planung
nach dem Leitfaden EGESIF_16-0014-01) mit REST-Vertrag; die Oberfläche dazu ist
`SampleSizePlanner`/`SamplingPanel` in `@auditcore/ui`. Dieses Paket bildet
dagegen eine bestimmte Arbeitsmappe Zelle für Zelle nach – einschließlich
ihrer Rundungen, Prüfhinweise und Blattbezüge – und rechnet ausschließlich im
Browser. Es zieht keine Stichprobe und ersetzt keine der dortigen Methoden;
gemeinsame Formeln werden nicht geteilt, weil hier die Vorlage maßgeblich ist.

Die Berechnung ersetzt nicht die fachliche Würdigung der Prüfbehörde und ist
kein Dokument der Europäischen Kommission.

## Installation

Standardweg ist die npm-Registry; npm löst die übrigen `@auditcore`-Pakete
der Abhängigkeitshülle selbst auf:

```sh
npm install @auditcore/sampling-templates-core
```

Ohne Registry-Zugang (Intranet, offline) bleibt der Tarball aus dem
GitHub-Release von auditcore; dann gehört jedes Paket der Hülle ausdrücklich
in die `package.json`:

```sh
npm install @auditcore/sampling-templates-core@https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore-sampling-templates-core-0.1.2.tgz
```

Version 0.1.2 ist noch nicht veröffentlicht (siehe „Lizenz und
Herkunftsnachweis“). Anleitung mit Integritätsprüfung und `vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

Abhängigkeitshülle: `@auditcore/common` und `fflate` (nur vom Einstieg
`./workbook` geladen). Keine Peer-Abhängigkeiten. Stil für Oberflächen:
`@auditcore/sampling-templates-core/style.css`.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @auditcore/sampling-templates-core`).

## Schnellstart

```ts run
import { createContext, findAvailableSheet, named, openWorkspace, saveWorkspace, emptyWorkspace } from '@auditcore/sampling-templates-core'

// Blatt 03 mit den erfundenen Beispielwerten rechnen; Schlüssel sind Zelladressen der Vorlage
const sheet = findAvailableSheet('03_MUS_1Z')
if (!sheet) throw new Error('Blatt 03 fehlt')
const results = sheet.compute(sheet.sample.inputs, createContext())
if (results.C27 !== 92) throw new Error('Anzuwendender Stichprobenumfang')

// dieselben Werte unter lesbaren Namen
const { sampleSize, totalErrorRate, assessment } = named(sheet.definition, results)
console.log(sampleSize, Number(totalErrorRate).toFixed(5), assessment) // 92 0.00652 ✔ GFQ und obere Fehlergrenze unter der Schwelle

// Arbeitsstand speichern und wieder öffnen: Prüfsumme über die kanonisch sortierten Eingaben
const state = { ...emptyWorkspace(), activeMethod: '03_MUS_1Z', sheets: { '03_MUS_1Z': sheet.sample.inputs } }
const saved = await saveWorkspace(state)
const opened = await openWorkspace(saved.text)
if (!opened.ok || opened.notices.length > 0) throw new Error('Rundlauf')

// außerhalb der Anwendung verändert → Hinweis
const tampered = await openWorkspace(saved.text.replace('"C7": 48500000', '"C7": 58500000'))
if (!tampered.ok || tampered.notices[0]?.kind !== 'checksum-mismatch') throw new Error('Prüfsumme')
```

Excel-Austausch aus dem getrennten Einstieg:

```ts
import { emptyWorkspace } from '@auditcore/sampling-templates-core'
import { exportWorkbook, importWorkbook } from '@auditcore/sampling-templates-core/workbook'

const exported = await exportWorkbook(emptyWorkspace())
const imported = importWorkbook(exported.data)
if (imported.kind !== 'workspace') throw new Error('Arbeitsstand fehlt')
```

## Einbindung

- **Direkt** in TypeScript/JavaScript (Browser, Node ≥ 20.19): alles ist rein
  und ohne DOM; nur `checksumOf` nutzt Web Crypto (mit eingebautem Rückfall für
  Seiten ohne HTTPS).
- **Vue 3:** `@auditcore/sampling-templates-vue` (Komponente
  `SamplingCalculator` und Bausteine).
- **Excel** erst bei Bedarf laden:
  `const xlsx = await import('@auditcore/sampling-templates-core/workbook')`. So
  bleibt fflate außerhalb des Startpakets.
- **Eigene Oberfläche:** `buildSections` und `buildSummary` liefern die
  Anzeigemodelle (Zeilen des Formulars, Ergebnisspalte, Prüfhinweise);
  `parseFieldInput`/`formatFieldValue` die deutsche Zahleneingabe und -ausgabe.

## Aufbau

| Bereich | Inhalt |
|---|---|
| `excel` | Excel-Semantik: `roundUp` und die Vergleiche `eq`/`lt`/`le`/`gt`/`ge` mit dem gemessenen Verhalten der Tabellenkalkulation, `n`, `guard` (= `IFERROR(…;"")` → `null`), `ifError`, `required`, Bereichs- und Textfunktionen. Inventar: [docs/excel-funktionen.md](docs/excel-funktionen.md) |
| `sheets/<Blatt>/` | je Blatt ein Verzeichnis: `compute` (reine Funktion `compute(eingaben, kontext) → ergebnisse`), `definition`, `deviations`, Beispielwerte, englische Arbeitsübersetzung; `shared/` hält Formeln, die mehrere Blätter wortgleich verwenden; `registry.ts` führt alle 23 Blätter |
| `model` | Richtlinie für fehlende Angaben (`policy`, `evaluate`), Schichtspalten (`strata`), Listenblätter (`list`), Datentabellen (`table`), `MethodDefinition` (Abschnitte, Felder, Zelle, Art, Format, Auswahlliste, Fundstelle, Kurzformel), `SheetContext` (Blatt 01, Ergebnisse anderer Blätter, Ergebnisübersicht für Blatt 18) |
| `catalog` | Verfahrensfamilien und Varianten nach Blatt 00, Arbeitsschritte |
| `workspace` | Arbeitsstandsdatei: speichern, öffnen, Prüfsumme, Migrationen, strenge Prüfung; Schema `arbeitsstand.schema.json` |
| `view`, `format`, `i18n` | Anzeigemodelle (Formular, Ergebnisspalte, Liste, Datentabelle, Bericht), deutsche Zahlen, Texte der Oberfläche |
| `./workbook` | Ergebnisexport (formatiertes Blatt „Ergebnis“, ausgeblendetes Blatt `_Arbeitsstand`) und Import |

Nachweise: [docs/abgleich.md](docs/abgleich.md) (Golden-Abgleich),
[docs/abweichungen.md](docs/abweichungen.md) (begründete Abweichungen),
[docs/schichten-und-listen.md](docs/schichten-und-listen.md) (Schichttabelle, Listenblatt).

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (201):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@auditcore/sampling-templates-core` | `Adaptation` | Schnittstelle | Bewusst anders gebildete Zelle: was die Webfassung zeigt, ausgedrückt durch den Wert der Vorlage. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `AvailableSheet` | Schnittstelle | Blatt mit Rechenkern und Methodendefinition. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `CATALOG_TEXTS` | Konstante | Arbeitsübersetzungen des Katalogs je Sprache. | `catalog/catalog` |
| `@auditcore/sampling-templates-core` | `CellAddress` | Typ | Zelladresse ohne Blatt, z. B. `C27`. | `model/types` |
| `@auditcore/sampling-templates-core` | `CellMap` | Typ | Zellwerte eines Blatts. | `model/types` |
| `@auditcore/sampling-templates-core` | `CellValue` | Typ | Wert einer Zelle: Zahl, Text oder leer. Fehlerwerte und `""` der Vorlage sind `null`. | `model/types` |
| `@auditcore/sampling-templates-core` | `CellView` | Schnittstelle | Wert einer einzelnen Zelle in der Anzeige. | `view/sheetView` |
| `@auditcore/sampling-templates-core` | `Cells` | Typ | Veränderliche Zellwerte während der Berechnung eines Blatts. | `model/types` |
| `@auditcore/sampling-templates-core` | `ChoiceOption` | Schnittstelle | Eintrag einer Auswahlliste. | `format/numbers` |
| `@auditcore/sampling-templates-core` | `Compute` | Typ | Rechenkern eines Blatts: reine Funktion ohne Seiteneffekte. | `model/types` |
| `@auditcore/sampling-templates-core` | `DataTable` | Schnittstelle | – | `model/table` |
| `@auditcore/sampling-templates-core` | `DataTableColumn` | Schnittstelle | Spalte einer Nachschlagetabelle. | `model/table` |
| `@auditcore/sampling-templates-core` | `DataTableView` | Schnittstelle | – | `view/tableView` |
| `@auditcore/sampling-templates-core` | `Deviation` | Schnittstelle | Begründete Abweichung vom Verhalten der Vorlage: Ist eine der Eingaben in `whenEmpty` leer, liefert die Webfassung an `cell` `null` („Angabe fehlt“), während die Vorlage mit 0 weit … | `model/types` |
| `@auditcore/sampling-templates-core` | `ENGINE_VERSION` | Konstante | Fassung des Rechenkerns (gleich der Paketversion); steht in jeder Datei. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `EXTRA_STRATA` | Konstante | Zusätzliche Schichtspalten der Webfassung (8. bis 20. Schicht). | `model/strata` |
| `@auditcore/sampling-templates-core` | `FAMILIES` | Konstante | – | `catalog/catalog` |
| `@auditcore/sampling-templates-core` | `Family` | Schnittstelle | – | `catalog/catalog` |
| `@auditcore/sampling-templates-core` | `FieldDefinition` | Schnittstelle | – | `model/definition` |
| `@auditcore/sampling-templates-core` | `FieldKind` | Typ | Art der Zelle wie in der Legende der Vorlage: Eingabe, Verknüpfung, Formel, Ergebnis. | `model/definition` |
| `@auditcore/sampling-templates-core` | `FieldTexts` | Schnittstelle | Übersetzte Texte eines Felds. | `model/texts` |
| `@auditcore/sampling-templates-core` | `FormulaError` | Klasse | Fehlerwert einer Formel (`#DIV/0!`, `#WERT!`, `#NV`); `guard` macht daraus `null`. | `excel/index` |
| `@auditcore/sampling-templates-core` | `GaugeView` | Schnittstelle | – | `view/summaryView` |
| `@auditcore/sampling-templates-core` | `GuideItem` | Schnittstelle | – | `view/guide` |
| `@auditcore/sampling-templates-core` | `GuideView` | Schnittstelle | – | `view/guide` |
| `@auditcore/sampling-templates-core` | `HintView` | Schnittstelle | – | `view/summaryView` |
| `@auditcore/sampling-templates-core` | `INPUT_FAILURE_HINTS` | Konstante | Erklärende Texte zu abgelehnten Eingaben; `integer` ergänzt die gemeinsamen Hinweise. | `format/numbers` |
| `@auditcore/sampling-templates-core` | `InputFailure` | Typ | – | `format/numbers` |
| `@auditcore/sampling-templates-core` | `InputResult` | Typ | Ergebnis einer Feldeingabe: Wert (leer = `null`) oder Grund der Ablehnung. | `format/numbers` |
| `@auditcore/sampling-templates-core` | `LEGAL_STATE` | Konstante | Rechtsstand der Vorlage. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `Limitation` | Schnittstelle | – | `view/limits` |
| `@auditcore/sampling-templates-core` | `LimitationKind` | Typ | – | `view/limits` |
| `@auditcore/sampling-templates-core` | `ListKey` | Typ | Schlüssel einer Auswahlliste aus Blatt 01; `confidence` kommt aus der z-Tabelle. | `model/types` |
| `@auditcore/sampling-templates-core` | `ListView` | Schnittstelle | – | `view/listView` |
| `@auditcore/sampling-templates-core` | `MAX_LIST_ROWS` | Konstante | Höchstzahl der Einheiten einer Liste (wie in der Prüfung der Arbeitsstandsdatei). | `model/list` |
| `@auditcore/sampling-templates-core` | `MAX_STRATA` | Konstante | Höchstzahl der Schichten in der Webfassung. | `model/strata` |
| `@auditcore/sampling-templates-core` | `MAX_WORKSPACE_SIZE` | Konstante | Größte Datei, die geöffnet wird (Zeichen der JSON-Datei). | `workspace/types` |
| `@auditcore/sampling-templates-core` | `MIGRATIONS` | Konstante | – | `workspace/migrate` |
| `@auditcore/sampling-templates-core` | `MISSING_POLICY` | Konstante | Geltende Richtlinie (vorläufige Vorgabe des Auftraggebers): | `model/policy` |
| `@auditcore/sampling-templates-core` | `MatrixGap` | Schnittstelle | Kombination der Matrix, für die die Vorlage kein Blatt enthält. | `catalog/catalog` |
| `@auditcore/sampling-templates-core` | `MessageKey` | Typ | Schlüssel aller Texte. | `i18n/messages` |
| `@auditcore/sampling-templates-core` | `MessageParams` | Typ | Platzhalterwerte eines Texts. | `i18n/messages` |
| `@auditcore/sampling-templates-core` | `MethodDefinition` | Schnittstelle | – | `model/definition` |
| `@auditcore/sampling-templates-core` | `MethodSummary` | Schnittstelle | Ergebnisübersicht eines Methodenblatts (feste Zellen N3–N11 der Vorlage). Blatt 18 liest sie über den Kontext; das ersetzt den INDIRECT-Bezug. | `model/types` |
| `@auditcore/sampling-templates-core` | `Migration` | Typ | Hebt eine Datei von der Fassung des Schlüssels auf die nächste Fassung. | `workspace/migrate` |
| `@auditcore/sampling-templates-core` | `Migrations` | Typ | – | `workspace/migrate` |
| `@auditcore/sampling-templates-core` | `MissingPolicy` | Schnittstelle | Richtlinie für fehlende Angaben je Fallart; die geltende steht in `model/policy.ts`. | `model/types` |
| `@auditcore/sampling-templates-core` | `MissingTreatment` | Typ | Behandlung einer fehlenden Angabe: Wert offen lassen oder wie die Vorlage mit 0 rechnen und das ausweisen. | `model/types` |
| `@auditcore/sampling-templates-core` | `OpenError` | Schnittstelle | Grund, aus dem eine Datei nicht geöffnet wird. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `OpenErrorCode` | Typ | – | `workspace/types` |
| `@auditcore/sampling-templates-core` | `OpenNotice` | Typ | Hinweis beim Öffnen; die Oberfläche formuliert daraus den Text. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `OpenOptions` | Schnittstelle | – | `workspace/open` |
| `@auditcore/sampling-templates-core` | `OpenResult` | Typ | – | `workspace/types` |
| `@auditcore/sampling-templates-core` | `PARAMETERS` | Konstante | – | `sheets/01_Parameter/index` |
| `@auditcore/sampling-templates-core` | `PERCENT_DIGITS` | Konstante | Nachkommastellen der Prozentausgabe (Gesamtfehlerquote 0,652 %). | `format/numbers` |
| `@auditcore/sampling-templates-core` | `POPULATION_SHEET` | Konstante | Blatt, aus dem der Wegweiser liest. | `view/guide` |
| `@auditcore/sampling-templates-core` | `PROJECTION_WITHOUT_ERRORS` | Konstante | Anzeige der Vorlage und Begründung für die Hochrechnung der Zufallsschicht ohne Fehlersumme (Abweichung `withoutBasis`). | `model/policy` |
| `@auditcore/sampling-templates-core` | `ParameterLists` | Schnittstelle | Auswahllisten aus Blatt 01 („nicht ändern“). | `model/types` |
| `@auditcore/sampling-templates-core` | `Parameters` | Schnittstelle | Parameter aus Blatt 01: z-Werte und Auswahllisten. | `model/types` |
| `@auditcore/sampling-templates-core` | `PastedRows` | Schnittstelle | – | `model/list` |
| `@auditcore/sampling-templates-core` | `PlannedSheet` | Schnittstelle | Blatt ohne Rechenkern: entweder noch geplant oder – mit `table` – eine Nachschlagetabelle der Vorlage (Blatt X1a), die als Datentabelle angezeigt wird. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `ReportBlock` | Typ | – | `view/reportView` |
| `@auditcore/sampling-templates-core` | `ReportCell` | Schnittstelle | Zelle einer Tabelle des Berichts. | `view/reportView` |
| `@auditcore/sampling-templates-core` | `ReportHint` | Schnittstelle | Hinweis zum Bericht; `printed`: steht auf dem Ausdruck. | `view/reportView` |
| `@auditcore/sampling-templates-core` | `ReportPage` | Schnittstelle | Die Berichtsseite als Daten. | `view/reportView` |
| `@auditcore/sampling-templates-core` | `ReportRow` | Schnittstelle | – | `view/reportView` |
| `@auditcore/sampling-templates-core` | `ReportSection` | Schnittstelle | – | `view/reportView` |
| `@auditcore/sampling-templates-core` | `ResultDifference` | Schnittstelle | Abweichung zwischen gespeichertem und neu berechnetem Ergebnis. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `RowControl` | Typ | Bedienelement einer Zeile. | `view/sheetView` |
| `@auditcore/sampling-templates-core` | `RowView` | Schnittstelle | – | `view/sheetView` |
| `@auditcore/sampling-templates-core` | `SHARED_TEXTS` | Konstante | Arbeitsübersetzungen zu Blatt 01 (Listeneinträge, Merksätze); sie gelten für alle Blätter. | `sheets/01_Parameter/index` |
| `@auditcore/sampling-templates-core` | `SHEETS` | Konstante | Alle Blätter in der Reihenfolge der Vorlage. | `sheets/registry` |
| `@auditcore/sampling-templates-core` | `STRATA_COLUMNS` | Konstante | Alle Schichtspalten in der Reihenfolge der Schichten. | `model/strata` |
| `@auditcore/sampling-templates-core` | `STRICT_POLICY` | Konstante | Variante „streng“: jede fehlende Angabe lässt die abhängigen Werte offen. | `model/policy` |
| `@auditcore/sampling-templates-core` | `SUMMARY_CELLS` | Konstante | Feste Zellen der Ergebnisübersicht, die jedes Methodenblatt für Blatt 18 füllt. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `SampleInputs` | Schnittstelle | Erfundene Beispielwerte eines Blatts; die Oberfläche kennzeichnet sie als Beispiel. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `SaveOptions` | Schnittstelle | – | `workspace/save` |
| `@auditcore/sampling-templates-core` | `SavedWorkspace` | Schnittstelle | Geschriebene Datei mit Text und vorgeschlagenem Namen. | `workspace/save` |
| `@auditcore/sampling-templates-core` | `SectionDefinition` | Schnittstelle | – | `model/definition` |
| `@auditcore/sampling-templates-core` | `SectionView` | Schnittstelle | – | `view/sheetView` |
| `@auditcore/sampling-templates-core` | `SheetContext` | Schnittstelle | Alles, was ein Blatt von außerhalb braucht. Verweise zwischen Blättern laufen ausdrücklich hierüber, es gibt keine Formel-Engine. | `model/types` |
| `@auditcore/sampling-templates-core` | `SheetEvaluation` | Schnittstelle | Ergebnis der Auswertung eines Blatts. | `model/evaluate` |
| `@auditcore/sampling-templates-core` | `SheetId` | Typ | Blattname der Vorlage, z. B. `03_MUS_1Z`. | `model/types` |
| `@auditcore/sampling-templates-core` | `SheetInputs` | Typ | Eingaben eines Blatts: Zellwerte, bei Blatt 17 eine Liste von Stichprobeneinheiten. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `SheetModule` | Typ | – | `model/sheet` |
| `@auditcore/sampling-templates-core` | `SheetTexts` | Schnittstelle | Übersetzung eines Blatts; Schlüssel sind Abschnittsbuchstaben, Zelladressen und deutsche Wortlaute. | `model/texts` |
| `@auditcore/sampling-templates-core` | `SheetTranslations` | Typ | – | `model/texts` |
| `@auditcore/sampling-templates-core` | `SubsampleGroup` | Typ | Summen der Einheiten einer Schicht und eines Zeitraums; `null` heißt „nicht unterschieden“. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `SubsampleNeeds` | Schnittstelle | Wonach das Methodenblatt die Summen der Unterstichproben unterscheidet. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `SubsampleRole` | Typ | Summen aus Blatt 17, die ein Methodenblatt per Schaltfläche übernimmt: Fehler der hochwertigen Einheiten, Summe der Fehlerquoten bzw. Fehler und Buchwerte der Zufallsschicht. | `model/definition` |
| `@auditcore/sampling-templates-core` | `SubsampleTotals` | Typ | Summen der Unterstichproben je Rolle; `null`, solange keine Einheit dazu beiträgt. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `SummaryDefinition` | Schnittstelle | Mitlaufende Ergebnisspalte: Hauptgröße, Kennzahlen und Skala gegen die Wesentlichkeitsschwelle. | `model/definition` |
| `@auditcore/sampling-templates-core` | `SummaryRow` | Schnittstelle | Zeile der mitlaufenden Ergebnisspalte. | `model/definition` |
| `@auditcore/sampling-templates-core` | `SummaryView` | Schnittstelle | – | `view/summaryView` |
| `@auditcore/sampling-templates-core` | `TEMPLATE_NAME` | Konstante | Nachgebildete Vorlage. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `TEMPLATE_POLICY` | Konstante | Variante „wie die Vorlage“: jede fehlende Angabe mit 0 gerechnet und ausgewiesen, Prüfhinweise wie in der Vorlage. | `model/policy` |
| `@auditcore/sampling-templates-core` | `TEMPLATE_STRATA` | Konstante | Schichtspalten der Vorlage. | `model/strata` |
| `@auditcore/sampling-templates-core` | `Tone` | Typ | Einstufung eines Prüfhinweises (✔ / ⚠ / ✖ / ohne Zeichen). | `model/types` |
| `@auditcore/sampling-templates-core` | `Translate` | Typ | Übersetzungsfunktion, wie sie `useI18n` aus `@auditcore/ui` liefert. | `i18n/messages` |
| `@auditcore/sampling-templates-core` | `TranslationLocale` | Typ | Sprachen neben Deutsch. | `model/texts` |
| `@auditcore/sampling-templates-core` | `ValueType` | Typ | Darstellung und Eingabeprüfung eines Werts. | `model/definition` |
| `@auditcore/sampling-templates-core` | `Variant` | Schnittstelle | Eine Variante = ein Blatt der Vorlage. | `catalog/catalog` |
| `@auditcore/sampling-templates-core` | `WORKFLOW_STEPS` | Konstante | Arbeitsablauf: Grundgesamtheit → Verfahren → Unterstichproben → Gesamtfehlerquote → Bericht. | `catalog/catalog` |
| `@auditcore/sampling-templates-core` | `WORKSPACE_FORMAT` | Konstante | Formatkennung der Arbeitsstandsdatei. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `WORKSPACE_FORMAT_VERSION` | Konstante | Aktuelle Fassung des Dateiformats; ältere werden angehoben, neuere abgelehnt. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `WebHint` | Schnittstelle | Zusätzlicher Hinweis der Webfassung; verändert kein Rechenergebnis. | `model/types` |
| `@auditcore/sampling-templates-core` | `WorkflowStep` | Schnittstelle | Schritt des Arbeitsablaufs der Vorlage. | `catalog/catalog` |
| `@auditcore/sampling-templates-core` | `WorkspaceFile` | Schnittstelle | Arbeitsstandsdatei (`.json`), beschrieben durch `schema/arbeitsstand.schema.json`. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `WorkspaceHeader` | Schnittstelle | Kopfangaben der Datei (Schlüssel wie im Dateiformat). | `workspace/types` |
| `@auditcore/sampling-templates-core` | `WorkspaceState` | Schnittstelle | Arbeitsstand im Speicher. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `ZRow` | Schnittstelle | Eine Zeile der z-Tabelle aus Blatt 01 (Anhang I Nr. 3 DelVO). | `model/types` |
| `@auditcore/sampling-templates-core` | `ZeroAssumption` | Schnittstelle | Eine fehlende Eingabe, mit der wie in der Vorlage als 0 gerechnet wurde. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `applySubsamples` | Funktion | Summen der Unterstichproben in die gekennzeichneten Felder eines Methodenblatts schreiben – bei geschichteten Verfahren je Schicht, bei mehreren Zeiträumen je Zeitraum (`totals.gro … | `model/list` |
| `@auditcore/sampling-templates-core` | `assumedCells` | Funktion | Betroffene Zelle → fehlende Eingaben, die wie in der Vorlage als 0 gerechnet sind. | `view/sheetView` |
| `@auditcore/sampling-templates-core` | `availableSheets` | Funktion | Blätter mit Rechenkern. | `sheets/registry` |
| `@auditcore/sampling-templates-core` | `buildDataTable` | Funktion | – | `view/tableView` |
| `@auditcore/sampling-templates-core` | `buildGuide` | Funktion | Hinweise aus der angepassten Grundgesamtheit: Zulässigkeit eines nichtstatistischen Verfahrens (02!C53), Mindestumfang von 10 % (02!C54) und der Merksatz zum begrenzten Stichproben … | `view/guide` |
| `@auditcore/sampling-templates-core` | `buildHints` | Funktion | Prüfhinweise der Vorlage in Blattreihenfolge, danach die Hinweise der Webfassung: mit 0 gerechnete Eingaben, Werte ohne Grundlage, eigene Hinweise und – in Blatt 18 und im Bericht … | `view/summaryView` |
| `@auditcore/sampling-templates-core` | `buildListView` | Funktion | Übersicht der Einheiten und die Summen, die das Methodenblatt `method` übernehmen kann. | `view/listView` |
| `@auditcore/sampling-templates-core` | `buildReport` | Funktion | Berichtsseite aus dem Blatt 20, seinen Eingaben und Ergebnissen. | `view/reportView` |
| `@auditcore/sampling-templates-core` | `buildSections` | Funktion | Abschnitte und Zeilen eines Blatts in der Reihenfolge der Vorlage. | `view/sheetView` |
| `@auditcore/sampling-templates-core` | `buildSummary` | Funktion | Mitlaufende Ergebnisspalte eines Blatts. | `view/summaryView` |
| `@auditcore/sampling-templates-core` | `canonicalInputs` | Funktion | Kanonischer JSON-Text der Eingaben einer Arbeitsstandsdatei (Kopf, aktive Methode, Blätter). | `workspace/canonical` |
| `@auditcore/sampling-templates-core` | `carriedLimitations` | Funktion | Einschränkungen, die ein Blatt von den Blättern übernimmt, aus denen es sein Ergebnis bezieht – je mit der Blattnummer davor („Blatt 03: …“). | `view/limits` |
| `@auditcore/sampling-templates-core` | `cellsOf` | Funktion | Alle Zellen eines Felds: die Zelle selbst oder, bei Schichtzeilen, eine Zelle je Schichtspalte. | `model/definition` |
| `@auditcore/sampling-templates-core` | `checksumOf` | Funktion | Prüfsumme `sha256:<hex>` über einen Text (Web Crypto, UTF-8). | `workspace/canonical` |
| `@auditcore/sampling-templates-core` | `choiceValue` | Funktion | Wert einer Auswahl aus dem Text des Auswahlfelds (Zahlen bleiben Zahlen). | `format/numbers` |
| `@auditcore/sampling-templates-core` | `cleanInputs` | Funktion | Eingaben ohne leere Werte; leere Blätter entfallen. | `workspace/save` |
| `@auditcore/sampling-templates-core` | `computeLikeTemplate` | Funktion | Gegenrechnung „wie die Vorlage“: Alle leeren Eingaben, die in den begründeten Abweichungen des Blatts genannt sind, zählen als 0. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `computeWithZeros` | Funktion | Rechnet das Blatt noch einmal; die genannten leeren Eingaben zählen dabei wie in der Vorlage als 0. | `model/evaluate` |
| `@auditcore/sampling-templates-core` | `computeWorkspace` | Funktion | Berechnet jedes Blatt mit Rechenkern. Die Reihenfolge des Registers ist die der Vorlage, sodass Verknüpfungen (Blatt 02 → Methodenblatt → Blatt 18) auf bereits berechnete Blätter t … | `workspace/compute` |
| `@auditcore/sampling-templates-core` | `computedCells` | Funktion | Nur die berechneten Zellen eines Blatts (ohne Eingabezellen), wie sie in `ergebnisse` stehen. | `workspace/compute` |
| `@auditcore/sampling-templates-core` | `contextFor` | Funktion | Kontext, in dem ein Blatt des Arbeitsstands gerechnet wird: Ergebnisse der anderen Blätter und – für Blatt 18 – die Ergebnisübersicht des gewählten Methodenblatts. | `workspace/compute` |
| `@auditcore/sampling-templates-core` | `countRow` | Funktion | `ANZAHL(D<zeile>:J<zeile>)`, in der Webfassung über alle Schichtspalten. | `model/strata` |
| `@auditcore/sampling-templates-core` | `createContext` | Funktion | Kontext mit den Parametern aus Blatt 01; weitere Angaben überschreiben die Vorgaben. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `createTranslate` | Funktion | Übersetzungsfunktion ohne Framework (Export, Tests): `{name}`-Platzhalter, Rückfall auf Deutsch. | `i18n/messages` |
| `@auditcore/sampling-templates-core` | `defaultInputs` | Funktion | Vorgaben der Vorlage für ein leeres Formular. | `model/definition` |
| `@auditcore/sampling-templates-core` | `defineSheet` | Funktion | Blatt mit Rechenkern anmelden. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `describeNotice` | Funktion | Hinweis nach dem Öffnen als Satz. | `view/notices` |
| `@auditcore/sampling-templates-core` | `describeOpenError` | Funktion | Fehlermeldung: was falsch ist und wie es sich beheben lässt. | `view/notices` |
| `@auditcore/sampling-templates-core` | `emptyWorkspace` | Funktion | Leerer Arbeitsstand. | `workspace/types` |
| `@auditcore/sampling-templates-core` | `evaluateSheet` | Funktion | Blatt rechnen und die Richtlinie für fehlende Angaben anwenden. | `model/evaluate` |
| `@auditcore/sampling-templates-core` | `excel` | Re-Export | – | `–` |
| `@auditcore/sampling-templates-core` | `exportFileName` | Funktion | – | `workspace/filenames` |
| `@auditcore/sampling-templates-core` | `familyOf` | Funktion | Familie, zu der ein Blatt gehört. | `catalog/catalog` |
| `@auditcore/sampling-templates-core` | `fieldOptions` | Funktion | Auswahl eines Felds: Liste aus Blatt 01 oder eigene Einträge; ohne Auswahl leer. | `format/numbers` |
| `@auditcore/sampling-templates-core` | `fieldsOf` | Funktion | Alle Felder in der Reihenfolge der Vorlage. | `model/definition` |
| `@auditcore/sampling-templates-core` | `fileStem` | Funktion | Namensstamm aus Blatt und Geschäftsjahr; ohne Geschäftsjahr das Tagesdatum. | `workspace/filenames` |
| `@auditcore/sampling-templates-core` | `fillRow` | Funktion | Füllt eine Schichtzeile: je Schichtspalte ein Wert aus `formula(spalte)`. | `model/strata` |
| `@auditcore/sampling-templates-core` | `findAvailableSheet` | Funktion | Blatt mit Rechenkern oder `undefined`, wenn es fehlt oder noch geplant ist. | `sheets/registry` |
| `@auditcore/sampling-templates-core` | `findField` | Funktion | Feld zu einer Zelle; auch Schichtzellen und Summenzellen einer Schichtzeile werden gefunden. | `model/definition` |
| `@auditcore/sampling-templates-core` | `findSheet` | Funktion | Blatt zu einem Blattnamen der Vorlage. | `sheets/registry` |
| `@auditcore/sampling-templates-core` | `findVariant` | Funktion | Variante zu einem Blatt. | `catalog/catalog` |
| `@auditcore/sampling-templates-core` | `formatFieldInput` | Funktion | Text eines Werts im Eingabefeld (ohne Einheit): `48.500.000,00`, `2`, `0,12`. | `format/numbers` |
| `@auditcore/sampling-templates-core` | `formatFieldValue` | Funktion | Anzeige eines Werts mit Einheit: `480.681,82 €`, `92`, `1,036`, `0,652 %`; Texte der Vorlage bleiben unverändert. | `format/numbers` |
| `@auditcore/sampling-templates-core` | `inputCells` | Funktion | Alle Eingabezellen eines Blatts (Schichtzeilen aufgelöst). | `model/definition` |
| `@auditcore/sampling-templates-core` | `inputFields` | Funktion | Felder, die die Prüfbehörde ausfüllt (Eingaben und überschreibbare Verknüpfungen). | `model/definition` |
| `@auditcore/sampling-templates-core` | `inputName` | Funktion | Bezeichnung einer Eingabe für Hinweise: „Bezeichnung (Zelle)“, bei anderen Blättern „Blatt!Zelle“; mit `t` bei Schichtzellen mit der Schicht davor. | `view/limits` |
| `@auditcore/sampling-templates-core` | `isEmptyForm` | Funktion | Leeres Formular: Keine Eingabe weicht von den Vorgaben der Vorlage ab und keine Verknüpfung liefert einen Wert. | `view/summaryView` |
| `@auditcore/sampling-templates-core` | `isEmptyReference` | Funktion | Ist die Zelle leer? Ohne Blattangabe eine Zelle des eigenen Blatts, `Blatt!Zelle` eine Zelle eines anderen Blatts aus dem Kontext. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `isQualified` | Funktion | Schränkt etwas das Ergebnis ein (Warnfarbe)? Dann erscheint ein bestandener Befund nicht uneingeschränkt grün. | `view/limits` |
| `@auditcore/sampling-templates-core` | `limitationsOf` | Funktion | Einschränkungen des Blatts selbst, in der Reihenfolge: mit 0 gerechnet, stille Lücken, ohne Grundlage, negative Ergebnisse, Warnhinweise, Auslegung, Altvorlage. | `view/limits` |
| `@auditcore/sampling-templates-core` | `listRows` | Funktion | Einheiten eines Listenblatts (Blatt 17) aus dem Arbeitsstand. | `workspace/compute` |
| `@auditcore/sampling-templates-core` | `localizeDefinition` | Funktion | Methodendefinition mit übersetzten Texten; Zellen, Arten und Formate bleiben unverändert. | `model/texts` |
| `@auditcore/sampling-templates-core` | `localizeFamilies` | Funktion | Katalog in der Sprache der Oberfläche; Deutsch und fehlende Texte bleiben unverändert. | `catalog/catalog` |
| `@auditcore/sampling-templates-core` | `localizeSheet` | Funktion | Blatt in der Sprache der Oberfläche: Definition mit übersetzten Texten; `shared` sind Übersetzungen, die für alle Blätter gelten (Listen aus Blatt 01). | `model/sheet` |
| `@auditcore/sampling-templates-core` | `migrate` | Funktion | Datei schrittweise von `from` auf `to` anheben. | `workspace/migrate` |
| `@auditcore/sampling-templates-core` | `named` | Funktion | Zellwerte unter den lesbaren Namen der Definition; bei Schichtzeilen die Summenzelle, sonst die erste Schicht. | `model/definition` |
| `@auditcore/sampling-templates-core` | `openWorkspace` | Funktion | Öffnet den Text einer Arbeitsstandsdatei. Ältere Fassungen werden angehoben, neuere abgelehnt; unbekannte Felder werden ignoriert und gemeldet; weicht die Prüfsumme ab, ist die Dat … | `workspace/open` |
| `@auditcore/sampling-templates-core` | `optionsOf` | Funktion | Einträge einer Auswahlliste aus Blatt 01; das Konfidenzniveau kommt aus der z-Tabelle. | `format/numbers` |
| `@auditcore/sampling-templates-core` | `parseFieldInput` | Funktion | Liest die Texteingabe eines Felds; Prozentfelder werden in Prozent eingegeben und als Anteil gespeichert. | `format/numbers` |
| `@auditcore/sampling-templates-core` | `parsePastedRows` | Funktion | Liest eingefügten Text (Tabulator, Semikolon oder Komma als Trenner) als Liste von Einheiten. Zahlen in deutscher Schreibweise; Prozentfelder in Prozent. | `model/list` |
| `@auditcore/sampling-templates-core` | `pasteColumns` | Funktion | Spalten beim Einfügen ohne Kopfzeile: die Eingabezellen der Vorlage in Blattreihenfolge. | `model/list` |
| `@auditcore/sampling-templates-core` | `percentToFraction` | Funktion | „2“ Prozent → 0.02, ohne Gleitkommarauschen (Verschieben des Kommas im Dezimaltext). | `format/numbers` |
| `@auditcore/sampling-templates-core` | `plannedSheet` | Funktion | Platzhalter für ein Blatt ohne Rechenkern. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `policyOf` | Funktion | Richtlinie des Kontexts; ohne Angabe die geltende. | `model/policy` |
| `@auditcore/sampling-templates-core` | `projectionWithoutErrors` | Funktion | Hochrechnung der Zufallsschicht: Ist keine Fehlersumme eingetragen (`entered`), rechnet die Vorlage mit `N(…)` = 0 und zeigt 0 € – ein Wert ohne Grundlage. | `model/policy` |
| `@auditcore/sampling-templates-core` | `resolveInputs` | Funktion | Eingaben eines Blatts auflösen: eigene Werte der Eingabezellen, bei Verknüpfungen der Wert des anderen Blatts aus dem Kontext, solange die Prüfbehörde ihn nicht überschrieben hat. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `rowNumber` | Funktion | Zeilennummer einer Zelle (`D9` → `9`). | `model/definition` |
| `@auditcore/sampling-templates-core` | `rowValues` | Funktion | Werte einer Schichtzeile über alle Schichtspalten. | `model/strata` |
| `@auditcore/sampling-templates-core` | `samplingTemplatesMessages` | Konstante | Texte je Sprache; Deutsch vollständig, Englisch als Arbeitsübersetzung (`messages.en.ts`). | `i18n/messages` |
| `@auditcore/sampling-templates-core` | `saveWorkspace` | Funktion | Arbeitsstandsdatei mit Prüfsumme über die kanonisch sortierten Eingaben erzeugen. | `workspace/save` |
| `@auditcore/sampling-templates-core` | `sha256Fallback` | Funktion | SHA-256 in reinem JavaScript; nur für Umgebungen ohne Web Crypto (Seiten ohne HTTPS). | `workspace/canonical` |
| `@auditcore/sampling-templates-core` | `strataColumnsOf` | Funktion | Schichtspalten des Blatts in der Reihenfolge der Schichten: die Spalten der ersten Schichtzeile (in den Blättern 04–16 D–J und AA–AM, in der Altvorlage X3 E–K und AA–AM); leer bei … | `model/definition` |
| `@auditcore/sampling-templates-core` | `strataRows` | Funktion | Zeilen der Schichtzeilen eines Blatts (für die Zahl der belegten Schichten). | `view/sheetView` |
| `@auditcore/sampling-templates-core` | `stratumCell` | Funktion | Zelle einer Schicht in einer Zeile (`stratumCell('D', 9)` → `D9`). | `model/strata` |
| `@auditcore/sampling-templates-core` | `subsampleNeeds` | Funktion | Unterscheidet das Methodenblatt die Summen nach Schicht (Schichtzeile) bzw. nach Zeitraum (`period`)? | `model/list` |
| `@auditcore/sampling-templates-core` | `subsampleTargets` | Funktion | Felder eines Methodenblatts, die eine Summe aus den Unterstichproben aufnehmen. | `model/list` |
| `@auditcore/sampling-templates-core` | `sumRow` | Funktion | `SUMME(D<zeile>:J<zeile>)`, in der Webfassung über alle Schichtspalten. | `model/strata` |
| `@auditcore/sampling-templates-core` | `summaryOf` | Funktion | Ergebnisübersicht eines Methodenblatts für den Kontext von Blatt 18. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `tableOf` | Funktion | Nachschlagetabelle eines Blatts (X1a) oder `undefined`. | `sheets/registry` |
| `@auditcore/sampling-templates-core` | `tableSheet` | Funktion | Nachschlagetabelle anmelden: kein Rechenblatt, aber als Datentabelle anzeigbar. | `model/sheet` |
| `@auditcore/sampling-templates-core` | `toneOf` | Funktion | Einstufung eines Prüfhinweises nach dem führenden Zeichen der Vorlage. | `excel/index` |
| `@auditcore/sampling-templates-core` | `totalRow` | Funktion | Summe einer Schichtzeile als angezeigter Wert: `SUMME(D<zeile>:J<zeile>)`, solange mindestens eine Schicht einen Wert trägt. | `model/strata` |
| `@auditcore/sampling-templates-core` | `translateValue` | Funktion | Anzeige eines Texts aus dem Rechenkern oder eines Listeneintrags in der Sprache der Oberfläche. | `model/texts` |
| `@auditcore/sampling-templates-core` | `unfounded` | Funktion | Wert ohne Grundlage: `shown` ist, was die Vorlage zeigt, obwohl die geprüfte bzw. summierte Größe fehlt (z. B. | `model/policy` |
| `@auditcore/sampling-templates-core` | `usedStrata` | Funktion | Anzahl der belegten Schichten: höchste Schicht mit einem Wert in einer der Zeilen. | `model/strata` |
| `@auditcore/sampling-templates-core` | `withMessages` | Funktion | Kataloge mit überschriebenen Texten einer Anwendung. | `i18n/messages` |
| `@auditcore/sampling-templates-core` | `workspaceChecksum` | Funktion | Prüfsumme der Eingaben eines Arbeitsstands – dieselbe, die die Arbeitsstandsdatei und der Excel-Export tragen. Damit lässt sich ein Ausdruck einem Arbeitsstand zuordnen. | `workspace/save` |
| `@auditcore/sampling-templates-core` | `workspaceFileName` | Funktion | – | `workspace/filenames` |
| `@auditcore/sampling-templates-core` | `zValue` | Funktion | Koeffizient z bzw. z' zum Konfidenzniveau; entspricht `INDEX(01_Parameter!C5:D9;VERGLEICH(niveau;01_Parameter!B5:B9;0);WENN(testart="einseitig";2;1))`. | `sheets/01_Parameter/index` |
<!-- api-overview:end -->

## Konfiguration

- **Arbeitsstand:** Formatkennung `flowaudit-stichprobe`, Formatfassung 1,
  größte Datei 2 MiB (`openWorkspace(text, { maxSize })`). Ältere Fassungen
  hebt `MIGRATIONS` an, neuere werden abgelehnt.
- **Blätter:** Alle Funktionen nehmen wahlweise ein eigenes Register
  (`sheets`), Standard ist `SHEETS`.
- **Sprache:** `samplingTemplatesMessages` (Deutsch und Englisch),
  überschreibbar mit `withMessages({ de, en })`. Bezeichnungen, Fundstellen
  und Prüfhinweise der Vorlage sind deutsch maßgeblich; `localizeSheet`
  liefert je Blatt eine gekennzeichnete englische Arbeitsübersetzung
  (vorhanden für alle Blätter; die Altvorlagen sind in der Vorlage englisch).
  Gespeicherte Werte bleiben deutsch.
- **Fehlende Angaben:** Was die Webfassung zeigt, wenn eine Eingabe fehlt und
  die Vorlage trotzdem einen Wert zeigt, steht an einer Stelle:
  `MISSING_POLICY` in `src/model/policy.ts` (Fallarten `requiredInput`,
  `sampleDeviation`, `partialErrorSum`, `withoutBasis`). `evaluateSheet`
  wendet sie an; `computeWorkspace(state, sheets, policy)` und
  `createContext({ policy })` nehmen eine andere Richtlinie für Vergleiche
  (`TEMPLATE_POLICY`: wie die Vorlage; `STRICT_POLICY`).
- **Dateinamen:** `saveWorkspace` und `exportWorkbook` nehmen `filePrefix`
  (Standard „Stichprobe“).
- **Theming:** `style.css` liest nur die FlowAudit-Designtoken `--fa-*`
  (Zuordnung eigener Tokens: README der Vue-Bindung).
- **Werkzeuge** (nur zur Entwicklung, brauchen die Vorlage):
  `AUDITCORE_SAMPLING_TEMPLATES_DIR` zeigt auf das Verzeichnis mit der
  Arbeitsmappe und `vorlage_zellen.json`; sonst `.vorlage/` im Paket (von git
  ausgeschlossen). `AUDITCORE_SAMPLING_ENGINE03` aktiviert den lokalen Abgleich
  mit dem Referenz-Rechenkern.

## Herkunft und Charakterisierung

Neu geschrieben. Fachliche und rechnerische Referenz ist ausschließlich die
Excel-Arbeitsmappe „Stichprobenvorlagen 2021–2027, Fassung 4“ (Arbeitsentwurf
einer Prüfbehörde, Stand Oktober 2026, keine amtliche Fassung; nicht im
Repository). Jedes Blatt ist gegen die Vorlage charakterisiert
(LibreOffice-Neuberechnung; Zellen mit Ganzzahlformat exakt, übrige auf 1e-9
relativ, Texte wortgleich):

| Blatt | Fälle | Zellen | gleich | begründet abweichend | Toleranzkante | unbegründet | abweichend „wie die Vorlage“ |
|---|---:|---:|---:|---:|---:|---:|---:|
| `02_Grundgesamtheit` | 159 | 3.021 | 2.948 | 73 | 0 | 0 | 0 |
| `03_MUS_1Z` | 783 | 29.754 | 29.446 | 308 | 0 | 0 | 0 |
| `04_MUS_1Z_S` | 381 | 46.482 | 45.466 | 1.016 | 0 | 0 | 0 |
| `05_MUS_2Z` | 541 | 35.165 | 33.223 | 1.942 | 0 | 0 | 0 |
| `06_MUS_2Z_S` | 635 | 150.495 | 147.167 | 3.327 | 1 | 0 | 0 |
| `07_MUS_3Z` | 612 | 56.916 | 52.646 | 4.270 | 0 | 0 | 0 |
| `08_SRS_1Z` | 660 | 24.420 | 24.210 | 210 | 0 | 0 | 0 |
| `09_SRS_1Z_S` | 421 | 32.417 | 31.639 | 778 | 0 | 0 | 0 |
| `10_SRS_2Z` | 714 | 42.840 | 39.426 | 3.414 | 0 | 0 | 0 |
| `11_SRS_2Z_S` | 724 | 118.736 | 115.100 | 3.636 | 0 | 0 | 0 |
| `12_SRS_3Z` | 785 | 67.510 | 61.572 | 5.937 | 1 | 0 | 0 |
| `13_NS_GW` | 399 | 8.778 | 8.661 | 117 | 0 | 0 | 0 |
| `14_NS_GW_S` | 410 | 16.400 | 16.099 | 301 | 0 | 0 | 0 |
| `15_NS_PPS` | 406 | 10.556 | 10.334 | 222 | 0 | 0 | 0 |
| `16_NS_PPS_S` | 412 | 28.840 | 28.192 | 648 | 0 | 0 | 0 |
| `17_Unterstichprobe` | 102 | 612 | 577 | 35 | 0 | 0 | 0 |
| `18_GFQ_AnhIII` | 677 | 14.894 | 14.609 | 285 | 0 | 0 | 0 |
| `20_Druck_KOM` | 588 | 19.404 | 19.161 | 243 | 0 | 0 | 0 |
| `X1_KonsMUS_2017` | 213 | 2.769 | 2.588 | 181 | 0 | 0 | 0 |
| `X2_DiffSch_2017` | 434 | 5.642 | 5.449 | 193 | 0 | 0 | 0 |
| `X3_DiffSch_S_2017` | 234 | 8.424 | 7.842 | 582 | 0 | 0 | 0 |
| `X4_DiffSch_2Z_2017` | 241 | 4.820 | 4.490 | 330 | 0 | 0 | 0 |
| **Summe** | 10.531 | 728.895 | 700.845 | 28.048 | 2 | 0 | 0 |

„Begründet abweichend“ heißt: Die Webfassung zeigt keinen Wert, wo die Vorlage
einen zeigt, weil eine Eingabe fehlt; die Gegenprobe ergibt den Wert der
Vorlage. Sind alle Pflichteingaben vorhanden, zeigt die Webfassung immer, was
die Vorlage zeigt. „Toleranzkante“ sind zwei Würdigungen von Prüfsonden mit
17-stelliger Eingabe, die genau auf der Vergleichstoleranz liegen; mit der um
eine letzte Stelle verschobenen Eingabe stimmt der Text. „Wie die Vorlage“ ist
dieselbe Rechnung unter der Richtlinie, die jede fehlende Angabe mit 0
rechnet: Dann stimmt jede Zelle. Von den 10.531 Fällen stammen 6.805 aus der
unabhängigen Gesamtabnahme (eigener Generator, Einzellücken-Matrix,
Schwellen- und Ganzzahlsonden), 3.726 aus dem Bau; je Blatt gehören mindestens
100 zufällige vollständige Belegungen dazu.

**Grenze des Nachweises:** Alle Sollwerte stammen aus der Neuberechnung der
Vorlage mit LibreOffice 24.2. Eine Gegenprobe mit Microsoft Excel steht aus;
ob Excel an Schwellen und beim Aufrunden in jedem Fall gleich entscheidet, ist
nicht geprüft. Die Oberfläche nennt das in der Fußzeile. Einzelheiten:
[PROVENANCE.md](PROVENANCE.md), [docs/abgleich.md](docs/abgleich.md).

## Bewusste Verhaltensabweichungen

Die Webfassung zeigt nie einen anderen Wert als die Vorlage, an manchen
Stellen keinen. Nach der geltenden Richtlinie (vorläufige Vorgabe des
Auftraggebers): „Angabe fehlt“ mit Nennung der Eingabe, wo die Vorlage wegen
einer fehlenden Pflichteingabe mit 0 weiterrechnet; kein Wert, wo die Vorlage
einen ohne Grundlage zeigt (bestandener Prüfhinweis ohne geprüfte Größe,
Summe 0 über leere Schichten); wie die Vorlage mit 0 gerechnet und als „Keine
Angabe, daher mit 0 berechnet.“ ausgewiesen bei fehlender Standardabweichung
der Stichprobe und fehlender Fehlersumme einer von mehreren Schichten bzw.
Zeiträumen. Die Variante „durchgehend wie die Vorlage“ ist ebenfalls für jedes
Blatt geprüft und an einer Stelle einschaltbar.
Vergleiche und Aufrunden folgen dem an LibreOffice gemessenen Verhalten;
Microsoft Excel ist nicht gegengeprüft. Vollständig:
[docs/abweichungen.md](docs/abweichungen.md).

## Abhängigkeiten

`@auditcore/common@0.1.2` (Zahleneingabe und -ausgabe, Datum), `fflate@^0.8.3`
(MIT, ohne eigene Abhängigkeiten; nur im Einstieg `./workbook`). Bewusst keine
Tabellenkalkulationsbibliothek: ExcelJS besteht die Lizenzprüfung des
Repositorys nicht und bringt 193 Pakete mit, die Community-Fassung von SheetJS
schreibt keine Zellformate. Der Excel-Austausch ist deshalb ein kleiner eigener
OOXML-Schreiber und -Leser mit schmaler Schnittstelle
(`exportWorkbook`, `importWorkbook`).

## Sicherheit und Datenschutz

Keine Netzwerkzugriffe, keine Telemetrie, kein Zugriff auf Web Storage. Dateien
werden vor der Verwendung streng geprüft: Größenlimit, Abbruch bei Schlüsseln
wie `__proto__`, feste Muster für Blatt- und Zellnamen, nur Zahlen, Texte und
`null` als Werte, Abgleich mit den Eingabezellen der Methodendefinition.
`.xlsx`-Dateien werden nur bis 20 MiB gelesen (je Teil höchstens 40 MiB
entpackt, höchstens eine Million Zellen, Zeitgrenze 8 s), entpackt wird nur
das Nötige; DTDs und externe Bezüge werden nicht ausgewertet. Was beim Import
der ausgefüllten Vorlage nicht oder umgedeutet übernommen wird, nennt die
Rückgabe je Zelle. Die Prüfsumme erkennt
Veränderungen außerhalb der Anwendung, sie ist kein Schutz gegen absichtliche
Fälschung. Beispielwerte sind erfunden. Die Bibliothek trifft keine
Prüfungsentscheidung.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`), wie es das Repository für alle Workspace-Pakete vorschreibt.
Offen vor einer Veröffentlichung: Bezeichnungen, Fundstellen, Prüfhinweistexte
und Rechenwege sind aus dem Arbeitsentwurf einer Behörde abgeleitet; die
Zustimmung des Dienstherrn (§ 43 UrhG) steht aus, das Ausgangsmaterial sah
EUPL-1.2 vor. Welche Inhalte der Vorlage im Paket stecken: `PROVENANCE.md`.

## Änderungen

[CHANGELOG.md](CHANGELOG.md)
