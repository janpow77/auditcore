# @flowaudit/ui-core

## Zweck

Framework-freier Kern der FlowAudit-Oberflächen: Texte, Datentypen der REST-Verträge, View-Modelle, Zustandsautomaten, Ports, Exporte und Stile – gemeinsam für Vue und React.

`@flowaudit/ui` (Vue 3, Web Components) und `@flowaudit/ui-react` (natives
React 18) rendern dieselben Komponenten aus diesem Kern. Fachlogik steht nur
hier: Wortvergleich und Filter der Synopse, Formularprüfung, Liste und Import
der Dokumentvergleiche, Vollständigkeit und Freigabe des
Verzeichnisses von Verarbeitungstätigkeiten, Vorschau und Entscheidung der
Datenschutz-Folgenabschätzung. Die Oberflächenpakete binden die
Zustandsautomaten nur an ihr Framework an. Kein Vue, kein React, kein
eigener Netzwerkzugriff außer über die Ports.

## Installation

Im auditcore-Repository ist das Paket Teil des npm-Workspace:

```sh
npm ci                                # im Repository-Stamm
npm run build -w @flowaudit/ui-core   # dist/: ESM und Typen; Stile unter styles/
```

Im Anwendungsrepository (meist indirekt über `@flowaudit/ui` oder
`@flowaudit/ui-react`):

```sh
npm install @flowaudit/ui-core @flowaudit/common
```

Das Paket ist nicht in einer npm-Registry veröffentlicht; Bezug über den
Workspace oder ein mit `npm pack -w @flowaudit/ui-core` erzeugtes Tarball
(zusammen mit `@flowaudit/common`).

## Schnellstart

```ts
import {
  createSynopsisController,
  selectSynopsis,
  synopsisMessages,
  translator,
  type ComparisonResult,
} from '@flowaudit/ui-core'

const t = translator(synopsisMessages, 'de')
const controller = createSynopsisController(() => t)

export function positionAfterNext(result: ComparisonResult): string {
  const inputs = { result }
  controller.go(selectSynopsis(controller.store.get(), inputs, t), 1)
  return selectSynopsis(controller.store.get(), inputs, t).position // „Änderung 1 von …“
}
```

## Einbindung

- **Vue:** `@flowaudit/ui` spiegelt den Zustand eines Controllers mit
  `useStore(controller.store)` in ein `shallowRef` und leitet Anzeigewerte
  mit `computed(() => selectSynopsis(…))`, `comparisonsView(…)`, `vvtView(…)`
  oder `dsfaDerived(…)` ab.
- **React:** `@flowaudit/ui-react` liest denselben Zustand mit
  `useSyncExternalStore(controller.store.subscribe, controller.store.get)`.
- **Ohne Framework:** Controller erzeugen, `store.subscribe` abonnieren und
  bei jeder Änderung aus `store.get()` neu zeichnen.
- **Stile:** `import '@flowaudit/ui-core/style.css'` (Designtoken `--fa-*`,
  Basis, Tabelle, Synopse, Dokumentvergleiche, Datenschutz); einzelne Dateien unter
  `@flowaudit/ui-core/styles/*.css`. `@flowaudit/ui/style.css` enthält sie bereits.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (271):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/ui-core` | `ACCEPTED_EXTENSIONS` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `ANSWER_VALUES` | Konstante | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `Activity` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ActivityGroup` | Schnittstelle | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `AnswerInput` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `AnswerValue` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `AssessmentExportFormat` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `AssessmentStatus` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `AssessmentSummary` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `AssessmentView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `BadgeTone` | Typ | – | `base/types` |
| `@flowaudit/ui-core` | `BlockProgress` | Schnittstelle | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `BlockView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ButtonSize` | Typ | – | `base/types` |
| `@flowaudit/ui-core` | `ButtonVariant` | Typ | – | `base/types` |
| `@flowaudit/ui-core` | `CHANGE_STATUSES` | Konstante | Vorgabe des Filters „Alle Änderungen“: alles außer unverändert. | `synopsis/types` |
| `@flowaudit/ui-core` | `COMPARISON_KINDS` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `COMPARISON_MODES` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `Catalogs` | Schnittstelle | Kataloge je Sprache; Deutsch ist vollständig, Englisch darf (noch) lückenhaft sein. | `i18n` |
| `@flowaudit/ui-core` | `ClientExportFormat` | Typ | – | `synopsis/types` |
| `@flowaudit/ui-core` | `CompareFields` | Schnittstelle | – | `synopsis/port` |
| `@flowaudit/ui-core` | `CompareForm` | Schnittstelle | – | `documents/form` |
| `@flowaudit/ui-core` | `CompareRow` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `Comparison` | Schnittstelle | Ein gespeicherter Vergleich (`GET /comparisons/{id}`). | `synopsis/types` |
| `@flowaudit/ui-core` | `ComparisonKind` | Typ | – | `documents/form` |
| `@flowaudit/ui-core` | `ComparisonMetadata` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `ComparisonMode` | Typ | – | `documents/form` |
| `@flowaudit/ui-core` | `ComparisonProfile` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `ComparisonResult` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `ComparisonSummary` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `ComparisonsBusy` | Typ | – | `documents/controller` |
| `@flowaudit/ui-core` | `ComparisonsController` | Typ | – | `documents/controller` |
| `@flowaudit/ui-core` | `ComparisonsControllerOptions` | Schnittstelle | – | `documents/controller` |
| `@flowaudit/ui-core` | `ComparisonsData` | Schnittstelle | – | `documents/controller` |
| `@flowaudit/ui-core` | `ComparisonsError` | Schnittstelle | Fehler einer Portanfrage: Meldung des Servers bzw. `network_error` mit Status 0. | `documents/controller` |
| `@flowaudit/ui-core` | `ComparisonsHooks` | Schnittstelle | – | `documents/controller` |
| `@flowaudit/ui-core` | `ComparisonsMessageKey` | Typ | – | `documents/messages` |
| `@flowaudit/ui-core` | `ComparisonsPort` | Typ | Port zur Anwendung: {@link createSynopsisRestClient } erfüllt ihn vollständig. `load`/`updateRows`/`exportUrl` braucht nur die eingebettete Synopse, `importResult` nur der Import. | `documents/controller` |
| `@flowaudit/ui-core` | `ComparisonsTranslate` | Typ | – | `documents/messages` |
| `@flowaudit/ui-core` | `ComparisonsView` | Schnittstelle | – | `documents/view` |
| `@flowaudit/ui-core` | `ComparisonsViewOptions` | Schnittstelle | – | `documents/view` |
| `@flowaudit/ui-core` | `Completeness` | Schnittstelle | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `ConsolidatedParagraph` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `DATAPROTECTION_CONTRACT` | Konstante | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `DEFAULT_FORM` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `DEFAULT_LOCALE` | Konstante | – | `i18n` |
| `@flowaudit/ui-core` | `DEFAULT_MAX_UPLOAD_BYTES` | Konstante | Vorgabe des Servers (`ServiceSettings.max_upload_bytes`). | `documents/form` |
| `@flowaudit/ui-core` | `DEFAULT_SYNOPSIS_FILTER` | Konstante | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `DSFA_NOTICES` | Konstante | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DataProtectionError` | Schnittstelle | Fehler einer Portanfrage: Code und Meldung des Servers bzw. `network_error` mit Status 0. | `dataprotection/requests` |
| `@flowaudit/ui-core` | `DataProtectionKey` | Typ | – | `dataprotection/messages` |
| `@flowaudit/ui-core` | `DataProtectionPort` | Schnittstelle | Datenzugang der Komponenten. Die mitgelieferte Umsetzung ist `createDataProtectionRestPort`; Anwendungen können eigene Ports übergeben. | `dataprotection/types` |
| `@flowaudit/ui-core` | `DataProtectionProfile` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `DataProtectionRequestHooks` | Schnittstelle | – | `dataprotection/requests` |
| `@flowaudit/ui-core` | `DataProtectionTranslate` | Typ | – | `dataprotection/messages` |
| `@flowaudit/ui-core` | `DecisionForm` | Schnittstelle | Eingabefelder der Entscheidung, vorbelegt aus der Fassung bzw. dem Vorschlag. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `DecisionInput` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `DiffField` | Typ | – | `synopsis/types` |
| `@flowaudit/ui-core` | `DiffSegment` | Schnittstelle | – | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `DiffSide` | Typ | – | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `DossierFieldView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `DsfaController` | Typ | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaControllerOptions` | Schnittstelle | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaData` | Schnittstelle | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaDerived` | Schnittstelle | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaHooks` | Schnittstelle | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaStep` | Typ | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaTab` | Typ | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `ExportInput` | Schnittstelle | – | `synopsis/exporters` |
| `@flowaudit/ui-core` | `ExportPayload` | Schnittstelle | Ergebnis eines Exports in der Oberfläche (Ereignis `export`). | `synopsis/types` |
| `@flowaudit/ui-core` | `ExportTexts` | Schnittstelle | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `ExportedFile` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `FieldKind` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `FieldValue` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `FieldView` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `FormProblem` | Schnittstelle | Ein Befund der Formularprüfung: Textschlüssel und Platzhalter. | `documents/form` |
| `@flowaudit/ui-core` | `ICONS` | Konstante | Eigene Strichsymbole (24er-Raster, Strichstärke über CSS). Jede Zeile ist eine Liste von SVG-Pfaden; neue Symbole nur hier ergänzen. | `base/icons` |
| `@flowaudit/ui-core` | `IDLE` | Konstante | – | `store` |
| `@flowaudit/ui-core` | `INITIAL_COMPARISONS` | Konstante | – | `documents/controller` |
| `@flowaudit/ui-core` | `IconName` | Typ | – | `base/icons` |
| `@flowaudit/ui-core` | `ImportParse` | Typ | – | `documents/importing` |
| `@flowaudit/ui-core` | `ImportRequest` | Schnittstelle | Anfrage von `POST /comparisons/import`: ein fertiges Ergebnis aus der Auftragssteuerung ablegen. | `synopsis/port` |
| `@flowaudit/ui-core` | `KeyTitle` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `LOCALES` | Konstante | – | `i18n` |
| `@flowaudit/ui-core` | `LevelView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `Locale` | Typ | Framework-freier Kern der Sprachunterstützung: Kataloge, Platzhalter, Rückfall auf Deutsch. | `i18n` |
| `@flowaudit/ui-core` | `MAX_THRESHOLD` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `MAX_TITLE` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `MIN_THRESHOLD` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `MeasureView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `MessageParams` | Typ | – | `i18n` |
| `@flowaudit/ui-core` | `NO_DEPARTMENT` | Konstante | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `OverviewRow` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `Person` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ProblemView` | Schnittstelle | – | `documents/view` |
| `@flowaudit/ui-core` | `ProfileOption` | Schnittstelle | – | `documents/view` |
| `@flowaudit/ui-core` | `Proposal` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `QuestionView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ROW_STATUSES` | Konstante | – | `synopsis/types` |
| `@flowaudit/ui-core` | `RegisterColumn` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RegisterContent` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RegisterExportFormat` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RegisterExportInput` | Schnittstelle | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `RegisterIssue` | Schnittstelle | Hinweis der Vollständigkeitsprüfung; `subject` = `<Tätigkeits-ID>:<Feld>` oder `deckblatt:<Teil>`. | `dataprotection/types` |
| `@flowaudit/ui-core` | `RegisterState` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RegisterStatus` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RequestState` | Schnittstelle | Beschäftigt-Status, Fehler und Erfolgsmeldung einer Portanfrage (gemeinsam für alle Controller). | `store` |
| `@flowaudit/ui-core` | `RestClientOptions` | Typ | Optionen wie bei `src/rest`: `baseUrl` (z. B. `/api/synopsis`), injizierbares `fetch`, Kopfzeilen. | `synopsis/port` |
| `@flowaudit/ui-core` | `RowStatus` | Typ | JSON-Formen des REST-Vertrags (docs/ui/synopsis-rest.md). Sie entsprechen `ComparisonResult.to_dict()` aus `auditcore_documents`; die Oberfläche kennt keine zweite Datenform. | `synopsis/types` |
| `@flowaudit/ui-core` | `RowUpdate` | Schnittstelle | Änderung einer Zeile (`PATCH /comparisons/{id}/rows`). | `synopsis/types` |
| `@flowaudit/ui-core` | `RowView` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `ScenarioInput` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ScenarioResult` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `SegmentKind` | Typ | Wortdifferenz für die Anzeige, ohne Vue. Bevorzugt die vom Server gelieferte `difflib.ndiff`-Folge (`"  "` gleich, `"- "` entfallen, `"+ "` neu, `"? "` Hinweis); fehlt sie (Gesetze … | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `ServerExportFormat` | Typ | – | `synopsis/types` |
| `@flowaudit/ui-core` | `ServerExportLink` | Schnittstelle | – | `synopsis/controller` |
| `@flowaudit/ui-core` | `Store` | Schnittstelle | Kleinster gemeinsamer Zustandsspeicher der Controller. | `store` |
| `@flowaudit/ui-core` | `SummaryView` | Schnittstelle | – | `documents/list` |
| `@flowaudit/ui-core` | `SurveyInput` | Schnittstelle | Erhebung einer Folgenabschätzung, wie sie `POST /assessments/{id}` erwartet. | `dataprotection/types` |
| `@flowaudit/ui-core` | `SynopsisController` | Typ | – | `synopsis/controller` |
| `@flowaudit/ui-core` | `SynopsisData` | Schnittstelle | – | `synopsis/controller` |
| `@flowaudit/ui-core` | `SynopsisFilterState` | Schnittstelle | – | `synopsis/controller` |
| `@flowaudit/ui-core` | `SynopsisInputs` | Schnittstelle | Eingaben der Komponente (Props). | `synopsis/controller` |
| `@flowaudit/ui-core` | `SynopsisLayout` | Typ | – | `synopsis/types` |
| `@flowaudit/ui-core` | `SynopsisMessageKey` | Typ | – | `synopsis/messages` |
| `@flowaudit/ui-core` | `SynopsisPort` | Schnittstelle | – | `synopsis/port` |
| `@flowaudit/ui-core` | `SynopsisRestClient` | Schnittstelle | – | `synopsis/port` |
| `@flowaudit/ui-core` | `SynopsisRowFilter` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `SynopsisSelection` | Schnittstelle | Alles, was die Oberfläche aus Stand und Eingaben anzeigt (reine Funktion). | `synopsis/controller` |
| `@flowaudit/ui-core` | `SynopsisTranslate` | Typ | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `SynopsisView` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `TabItem` | Schnittstelle | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `Translate` | Typ | – | `i18n` |
| `@flowaudit/ui-core` | `UploadFile` | Schnittstelle | Datei aus einem Eingabefeld (im Browser `File`). | `documents/form` |
| `@flowaudit/ui-core` | `VersionSummary` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `VersionView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ViewOptions` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `VvtController` | Typ | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtControllerOptions` | Schnittstelle | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtData` | Schnittstelle | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtExport` | Schnittstelle | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtExportFormat` | Typ | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtHooks` | Schnittstelle | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtView` | Schnittstelle | Abgeleitete Werte eines Stands (reine Funktion, von beiden Oberflächen genutzt). | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `WORD_LIMIT` | Konstante | Oberhalb dieser Wortzahl je Seite wird nicht wortweise verglichen. | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `activityKey` | Funktion | Schlüssel einer Tätigkeit für die Zuordnung der Hinweise (Kennung, sonst Name wie in der Bibliothek). | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `addScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `answerOf` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `applyRowOverrides` | Funktion | Zeilen mit lokalen Änderungen (Auswahl, Grund) zusammenführen. | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `asComparisonsError` | Funktion | – | `documents/controller` |
| `@flowaudit/ui-core` | `bandTone` | Funktion | Stufe eines Risikos nach Rang im Profil: höchste Stufe rot, zweithöchste gelb. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `baseMessages` | Konstante | Texte der Basiskomponenten. | `messages` |
| `@flowaudit/ui-core` | `blockProgress` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `buildRowView` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `buildSynopsisExport` | Funktion | Export der sichtbaren Zeilen (HTML, Markdown, Druckansicht). | `synopsis/controller` |
| `@flowaudit/ui-core` | `buildSynopsisView` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `buildVvtExport` | Funktion | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `canReleaseAssessment` | Funktion | Freigabe möglich: Vier-Augen-Vorprüfung, keine ungespeicherten Eingaben, keine Sperrgründe. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `cellAlignClass` | Funktion | – | `table` |
| `@flowaudit/ui-core` | `cellText` | Funktion | – | `table` |
| `@flowaudit/ui-core` | `changeIds` | Funktion | Kennungen der Änderungszeilen in Anzeigereihenfolge (Ziel der Navigation). | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `cloneContent` | Funktion | Tiefe Kopie (JSON-Daten), damit Eingaben den gelesenen Stand nie verändern. | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `comparisonsMessages` | Konstante | Texte der Vergleichsverwaltung (`<flowaudit-comparisons>`): Hochladen, gespeicherte Vergleiche, Import und Löschen. Begriffe wie in der Synopse. | `documents/messages` |
| `@flowaudit/ui-core` | `comparisonsView` | Funktion | – | `documents/view` |
| `@flowaudit/ui-core` | `completeness` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `completenessTone` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `coverIssues` | Funktion | Hinweise zum Deckblatt (Verantwortlicher, DSB). | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `createComparisonsController` | Funktion | – | `documents/controller` |
| `@flowaudit/ui-core` | `createDataProtectionRestPort` | Funktion | Port auf den REST-Vertrag `dataprotection_ui/1` von `auditcore_dataprotection.web`. | `dataprotection/rest-port` |
| `@flowaudit/ui-core` | `createDelay` | Funktion | Verzögerter Aufruf, der bei jeder neuen Eingabe neu startet (Vorschau, Vollständigkeitsprüfung). | `store` |
| `@flowaudit/ui-core` | `createDsfaController` | Funktion | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `createRunner` | Funktion | Führt eine Portanfrage aus: setzt `busy`, fängt Fehler (über `toError`) und meldet sie an `onError`. Ohne Port geschieht nichts (`null`). | `store` |
| `@flowaudit/ui-core` | `createStore` | Funktion | – | `store` |
| `@flowaudit/ui-core` | `createSynopsisController` | Funktion | – | `synopsis/controller` |
| `@flowaudit/ui-core` | `createSynopsisRestClient` | Funktion | – | `synopsis/port` |
| `@flowaudit/ui-core` | `createVvtController` | Funktion | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `currentVersion` | Funktion | Angezeigte Fassung: offener Entwurf vor Freigabe (dort wird gearbeitet). | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `dataprotectionError` | Funktion | – | `dataprotection/requests` |
| `@flowaudit/ui-core` | `dataprotectionLabel` | Funktion | – | `dataprotection/requests` |
| `@flowaudit/ui-core` | `dataprotectionMessages` | Konstante | Texte von `<flowaudit-vvt>` und `<flowaudit-dsfa>`. | `dataprotection/messages` |
| `@flowaudit/ui-core` | `dataprotectionStatusLabel` | Funktion | Übersetzter Status (`entwurf`, `freigegeben`, …); unbekannte Werte bleiben stehen. | `dataprotection/requests` |
| `@flowaudit/ui-core` | `decisionForm` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `decisionTitle` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `defaultProfile` | Funktion | Standardprofil des Servers (`default: true`), sonst das erste. | `documents/form` |
| `@flowaudit/ui-core` | `defineMessages` | Funktion | Typisiert Kataloge einer Komponente; die Schlüssel ergeben sich aus dem deutschen Katalog. | `i18n` |
| `@flowaudit/ui-core` | `deliverExport` | Funktion | Export ausliefern: Druckansicht (`print`) oder Datei. | `download` |
| `@flowaudit/ui-core` | `diffSegments` | Funktion | Segmente einer Seite. `ndiff` hat Vorrang; ohne sie wird nachgerechnet. Ist keine Wortdifferenz möglich, bleibt der Text unmarkiert (seitenweise) bzw. | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `displayValue` | Funktion | Anzeigewert eines Feldes; Wahrheitswerte und Leerwerte über die Texte der Komponente. | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `downloadText` | Funktion | Text als Datei anbieten (Blob-URL); ohne Blob-Unterstützung geschieht nichts. | `download` |
| `@flowaudit/ui-core` | `dsfaDerived` | Funktion | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `dsfaReadonly` | Funktion | Nur lesen: nicht bearbeitbar oder gesperrte (freigegebene) Fassung. | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `dsfaTabs` | Funktion | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `editedBy` | Funktion | Vier-Augen-Prinzip vorab anzeigen: wer den Entwurf bearbeitet hat, kann ihn nicht freigeben. | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `emptyActivity` | Funktion | Tätigkeit ohne Kennung (die vergibt der Server beim Speichern). | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `emptyContent` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `emptyScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `escapeHtml` | Funktion | – | `synopsis/exporters` |
| `@flowaudit/ui-core` | `escapeMarkdown` | Funktion | – | `synopsis/exporters` |
| `@flowaudit/ui-core` | `exportFilename` | Funktion | – | `synopsis/exporters` |
| `@flowaudit/ui-core` | `fieldIssues` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `filterRows` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `filterSummaries` | Funktion | Suche in Titel und Dateinamen, ohne Groß-/Kleinschreibung; neueste zuerst wie der Server. | `documents/list` |
| `@flowaudit/ui-core` | `focusRow` | Funktion | Zeile fokussieren und sichtbar machen; Zeilen tragen `data-row-id` und `tabindex="-1"`. | `synopsis/navigation` |
| `@flowaudit/ui-core` | `formProblems` | Funktion | Alle Befunde in Formularreihenfolge; leer heißt: absendbar. | `documents/form` |
| `@flowaudit/ui-core` | `formatBytes` | Funktion | Größenangabe wie „20 MiB“ oder „512 KiB“. | `documents/form` |
| `@flowaudit/ui-core` | `formatDateTime` | Funktion | Datum und Uhrzeit in der Sprache der Oberfläche; ungültige Angaben bleiben stehen. | `documents/list` |
| `@flowaudit/ui-core` | `getDefaultLocale` | Funktion | – | `i18n` |
| `@flowaudit/ui-core` | `groupByDepartment` | Funktion | Referate wie in der Quelle: konfigurierte zuerst, dann unbekannte; leere entfallen. | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `hasAcceptedExtension` | Funktion | – | `documents/form` |
| `@flowaudit/ui-core` | `interpolate` | Funktion | Ersetzt {name}-Platzhalter; unbekannte Platzhalter bleiben sichtbar stehen. | `i18n` |
| `@flowaudit/ui-core` | `involvesPdf` | Funktion | PDF-Dateien vergleicht der Server immer als Fließtext. | `documents/form` |
| `@flowaudit/ui-core` | `isDeviation` | Funktion | Abweichung vom Vorschlag verlangt eine Begründung (Bibliothek prüft Mindestlänge). | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `isIconName` | Funktion | – | `base/icons` |
| `@flowaudit/ui-core` | `isLocale` | Funktion | – | `i18n` |
| `@flowaudit/ui-core` | `issuesFor` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `lcsOperations` | Funktion | Längste gemeinsame Teilfolge über Wörter; `null` oberhalb von {@link WORD_LIMIT}. | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `levelLabel` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `looksLikeResult` | Funktion | Kennzeichen eines `ComparisonResult.to_dict()`; Einzelheiten prüft `ComparisonResult.from_dict`. | `documents/importing` |
| `@flowaudit/ui-core` | `mayRelease` | Funktion | Vier-Augen-Prinzip vorab anzeigen; maßgeblich bleibt die Prüfung des Servers. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `navigationDirection` | Funktion | Richtung für N/J (nächste) bzw. P/K (vorige Änderung); in Eingabefeldern und mit Modifikatoren `null`. | `synopsis/navigation` |
| `@flowaudit/ui-core` | `ndiffOperations` | Funktion | ndiff-Zeilen in Operationen übersetzen; Hinweiszeilen (`? `) entfallen. | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `parseConditions` | Funktion | Auflagen: eine je Zeile, leere Zeilen entfallen. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `parseCount` | Funktion | Eingabe eines Zahlfeldes: leer → null, sonst nichtnegative ganze Zahl; ungültig → undefined. | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `parseImport` | Funktion | – | `documents/importing` |
| `@flowaudit/ui-core` | `plainSegments` | Funktion | – | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `positionText` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `printHtml` | Funktion | Druckansicht in einem unsichtbaren Rahmen öffnen („Als PDF speichern“ im Druckdialog). Kein Pop-up, daher auch mit Pop-up-Blocker nutzbar. | `download` |
| `@flowaudit/ui-core` | `recommendationTone` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `registerCsv` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `registerFilename` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `registerHtml` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `registerMarkdown` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `removeScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `rowKeyOf` | Funktion | Schlüssel einer Zeile aus `rowKey`, sonst Position. | `table` |
| `@flowaudit/ui-core` | `sameSurvey` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `screeningTone` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `segmentsText` | Funktion | – | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `selectSynopsis` | Funktion | – | `synopsis/controller` |
| `@flowaudit/ui-core` | `setDefaultLocale` | Funktion | Sprache ohne Provider (Web Components, React ohne `LocaleProvider`). | `i18n` |
| `@flowaudit/ui-core` | `sortIcon` | Funktion | – | `table` |
| `@flowaudit/ui-core` | `statusLabel` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `statusTone` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `stepChange` | Funktion | Nächste bzw. vorige Änderung; ohne aktuelle Position beginnt `+1` bei der ersten und `-1` bei der letzten. Am Rand bleibt die Position stehen. | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `subscribeDefaultLocale` | Funktion | Meldet Änderungen der Standardsprache; liefert die Abmeldung. | `i18n` |
| `@flowaudit/ui-core` | `summaryOf` | Funktion | Eintrag der Liste aus einem gespeicherten Vergleich (nach Anlegen oder Import). | `documents/list` |
| `@flowaudit/ui-core` | `summaryView` | Funktion | – | `documents/list` |
| `@flowaudit/ui-core` | `surveyFrom` | Funktion | Bearbeitbare Kopie der gespeicherten Erhebung. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `synopsisBase` | Funktion | Ergebnisobjekt vor lokalen Änderungen: Prop `result`, sonst gespeicherter oder geladener Vergleich. | `synopsis/controller` |
| `@flowaudit/ui-core` | `synopsisId` | Funktion | Kennung des angezeigten Vergleichs (für Speichern und Server-Exporte). | `synopsis/controller` |
| `@flowaudit/ui-core` | `synopsisMessages` | Konstante | Sichtbare Texte der Synopse; Begriffe wie im audit_designer und in ecohesion. | `synopsis/messages` |
| `@flowaudit/ui-core` | `synopsisPortOf` | Funktion | Der Port als Datenzugang der eingebetteten Synopse, wenn er Vergleiche laden kann. | `documents/controller` |
| `@flowaudit/ui-core` | `toCompareFields` | Funktion | Formularfelder für `POST /comparisons`; Gesetzessynopse ohne die Optionen des Standardvergleichs. | `documents/form` |
| `@flowaudit/ui-core` | `toHtml` | Funktion | Eigenständiges HTML-Dokument mit Druck-CSS (keine externen Ressourcen). | `synopsis/exporters` |
| `@flowaudit/ui-core` | `toMarkdown` | Funktion | Markdown: gestrichene Wörter als ~~…~~, neue als **…**. | `synopsis/exporters` |
| `@flowaudit/ui-core` | `toggleMeasure` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `toggleSection` | Funktion | Abschnitt ein- oder ausschalten; Reihenfolge wie `ROW_STATUSES`. | `documents/form` |
| `@flowaudit/ui-core` | `translate` | Funktion | Übersetzt mit Rückfall auf Deutsch und zuletzt auf den Schlüssel. | `i18n` |
| `@flowaudit/ui-core` | `translator` | Funktion | Übersetzungsfunktion für eine feste Sprache. | `i18n` |
| `@flowaudit/ui-core` | `vvtExportTexts` | Funktion | Beschriftungen der Exporte (Druckansicht, Markdown, CSV). | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `vvtFourEyes` | Funktion | Vier-Augen-Hinweis: die angemeldete Person hat den offenen Entwurf bearbeitet. | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `vvtVersionLabel` | Funktion | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `vvtView` | Funktion | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `wholeSegments` | Funktion | Ganze Texte als Streichung und Einfügung (neue/entfallene Stellen, Rückfall). | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `withActivity` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `withAnswer` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `withDepartments` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `withField` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `withJustification` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `withPerson` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `withScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `withoutActivity` | Funktion | – | `dataprotection/registerView` |
<!-- api-overview:end -->

## Konfiguration

- Sprache: `translator(catalogs, locale)` für eine feste Sprache,
  `setDefaultLocale`/`subscribeDefaultLocale` für die Standardsprache ohne
  Provider (Web Components, React ohne `LocaleProvider`).
- Controller: `createSynopsisController(t)`, `createVvtController({ port, t,
  checkDelay, onSaved, onReleased, onError })`, `createDsfaController({ port,
  t, previewDelay, onChanged, onError })`; `port` und `t` sind Getter, damit
  die Oberfläche sie austauschen kann. `dispose()` beendet laufende Verzögerungen.
- Ports: `createSynopsisRestClient({ baseUrl })` (Vertrag
  [`synopsis-rest.md`](../../docs/ui/synopsis-rest.md)) und
  `createDataProtectionRestPort({ baseUrl })` (Vertrag `dataprotection_ui/1`,
  [`dataprotection-rest.md`](../../docs/ui/dataprotection-rest.md)); `fetch`
  und Kopfzeilen sind injizierbar (z. B. Anmeldetoken der Anwendung).

## Herkunft und Charakterisierung

Aus `@flowaudit/ui` 0.2.0 herausgelöst (Texte, Typen, View-Modelle, Exporte,
Ports und Stile unverändert; die Zustandsautomaten sind die bisherigen
Composables `useSynopsis`, `useVvt` und `useDsfa` ohne Vue-Reaktivität).
Die bisherigen Kerntests laufen hier unverändert; die gemeinsamen
Paritätsfälle unter `test/parity` prüfen die Vue- und die React-Fassung
gegen dieselben Erwartungen ([Parität Vue ↔ React](../../docs/ui/react-paritaet.md)).

## Abhängigkeiten

- `@flowaudit/common` 0.1.0 (Laufzeit: REST-Client, Formatierung,
  CSV mit Formelschutz, `saveFile`)

Node ≥ 20.19 für Bau und Tests.

## Sicherheit und Datenschutz

Keine eigene Datenhaltung und kein Browser-Speicher. Netzwerkzugriffe nur
über die Ports, die die Anwendung übergibt. Exporte (HTML, Markdown, CSV)
escapen alle Inhalte; CSV mit Formelschutz aus `@flowaudit/common`. Die
Vier-Augen-Hinweise sind reine Anzeige, maßgeblich ist die Prüfung des Servers.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Neu entwickelt in auditcore, kein übernommener Fremdcode.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
