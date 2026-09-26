# @auditcore/ui-core

## Zweck

Framework-freier Kern der FlowAudit-Oberflächen: Texte, Datentypen der REST-Verträge, View-Modelle, Zustandsautomaten, Ports, Exporte und Stile – gemeinsam für Vue und React.

`@auditcore/ui` (Vue 3, Web Components) und `@auditcore/ui-react` (natives
React 18) rendern dieselben Komponenten aus diesem Kern. Fachlogik steht nur
hier: Wortvergleich und Filter der Synopse, Vollständigkeit und Freigabe des
Verzeichnisses von Verarbeitungstätigkeiten, Vorschau und Entscheidung der
Datenschutz-Folgenabschätzung, Zustand und Verteilung der Risiko-Merkmale,
Trefferprüfung beim Screening, Eingabeprüfung und Anfragen von Stichprobe und
Benford-Analyse samt Diagrammgeometrie, Formularprüfung, Liste und Import der
Dokumentvergleiche, Gruppieren und Verschieben der Datenbankansicht als Kanban.
Die Oberflächenpakete binden die
Zustandsautomaten nur an ihr Framework an. Kein Vue, kein React, kein
eigener Netzwerkzugriff außer über die Ports.

## Installation

Standardweg ist die npm-Registry; npm löst die übrigen `@auditcore`-Pakete
der Abhängigkeitshülle selbst auf:

```sh
npm install @auditcore/ui-core
```

Ohne Registry-Zugang (Intranet, offline) bleibt der signierte Tarball aus
dem GitHub-Release von auditcore; dann gehört jedes Paket der Hülle
ausdrücklich in die `package.json`:

```sh
npm install @auditcore/ui-core@https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore-ui-core-0.2.0.tgz
```

Anleitung für Vue, React und Web Components mit Integritätsprüfung und
`vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

Abhängigkeitshülle: dazu `@auditcore/common`. Stile: `@auditcore/ui-core/style.css` (Designtoken `--fa-*` und Komponentenstile).

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @auditcore/ui-core`).

## Schnellstart

```ts
import {
  createSynopsisController,
  selectSynopsis,
  synopsisMessages,
  translator,
  type ComparisonResult,
} from '@auditcore/ui-core'

const t = translator(synopsisMessages, 'de')
const controller = createSynopsisController(() => t)

export function positionAfterNext(result: ComparisonResult): string {
  const inputs = { result }
  controller.go(selectSynopsis(controller.store.get(), inputs, t), 1)
  return selectSynopsis(controller.store.get(), inputs, t).position // „Änderung 1 von …“
}
```

## Einbindung

- **Vue:** `@auditcore/ui` spiegelt den Zustand eines Controllers mit
  `useStore(controller.store)` in ein `shallowRef` und leitet Anzeigewerte
  mit `computed(() => selectSynopsis(…))`, `comparisonsView(…)`, `vvtView(…)`,
  `dsfaDerived(…)` oder `selectRisk(…)` ab.
- **React:** `@auditcore/ui-react` liest denselben Zustand mit
  `useSyncExternalStore(controller.store.subscribe, controller.store.get)`.
- **Ohne Framework:** Controller erzeugen, `store.subscribe` abonnieren und
  bei jeder Änderung aus `store.get()` neu zeichnen.
- **Stile:** `import '@auditcore/ui-core/style.css'` (Designtoken `--fa-*`,
  Basis, Tabelle, Synopse, Datenschutz, Geo, Risiko-Merkmale, Screening,
  Datei-Import, Stichprobe, Benford, Dokumentvergleiche); einzelne Dateien unter
  `@auditcore/ui-core/styles/*.css`. `@auditcore/ui/style.css` enthält sie bereits.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (849):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@auditcore/ui-core` | `ACCEPTED_EXTENSIONS` | Konstante | – | `documents/form` |
| `@auditcore/ui-core` | `ANSWER_VALUES` | Konstante | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `Activity` | Typ | – | `dataprotection/types` |
| `@auditcore/ui-core` | `ActivityGroup` | Schnittstelle | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `ActorView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `AllocationMethod` | Typ | – | `sampling/types` |
| `@auditcore/ui-core` | `AllocationRequest` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `AllocationResult` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `AnalyseError` | Typ | – | `benford/model` |
| `@auditcore/ui-core` | `AnalyseInput` | Schnittstelle | – | `benford/model` |
| `@auditcore/ui-core` | `AnalyseRequest` | Schnittstelle | – | `benford/types` |
| `@auditcore/ui-core` | `AnalyseValidation` | Typ | – | `benford/model` |
| `@auditcore/ui-core` | `AnswerInput` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `AnswerValue` | Typ | – | `dataprotection/types` |
| `@auditcore/ui-core` | `ApiErrorBody` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `AreaGeometry` | Typ | GeoJSON-Fläche in Achsenfolge Länge, Breite (RFC 7946). | `geo/types` |
| `@auditcore/ui-core` | `AssessmentExportFormat` | Typ | – | `dataprotection/types` |
| `@auditcore/ui-core` | `AssessmentStatus` | Typ | – | `dataprotection/types` |
| `@auditcore/ui-core` | `AssessmentSummary` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `AssessmentView` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `BadgeTone` | Typ | – | `base/types` |
| `@auditcore/ui-core` | `BenfordAnalysis` | Schnittstelle | – | `benford/types` |
| `@auditcore/ui-core` | `BenfordBusy` | Typ | – | `benford/controller` |
| `@auditcore/ui-core` | `BenfordCallbacks` | Schnittstelle | – | `benford/controller` |
| `@auditcore/ui-core` | `BenfordCatalogue` | Schnittstelle | – | `benford/types` |
| `@auditcore/ui-core` | `BenfordController` | Typ | – | `benford/controller` |
| `@auditcore/ui-core` | `BenfordData` | Schnittstelle | Stand der Benford-Analyse; `error` ist die Meldung der letzten abgelehnten Anfrage. | `benford/controller` |
| `@auditcore/ui-core` | `BenfordDistribution` | Schnittstelle | – | `benford/types` |
| `@auditcore/ui-core` | `BenfordMessageKey` | Typ | – | `benford/messages` |
| `@auditcore/ui-core` | `BenfordMetricTexts` | Schnittstelle | – | `benford/view` |
| `@auditcore/ui-core` | `BenfordPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createBenfordRestPort`. | `benford/types` |
| `@auditcore/ui-core` | `BenfordSource` | Schnittstelle | – | `benford/controller` |
| `@auditcore/ui-core` | `BenfordTest` | Typ | Typen des REST-Vertrags `docs/ui/benford-rest.md` (auditcore_statistics.web). | `benford/types` |
| `@auditcore/ui-core` | `BenfordTranslate` | Typ | – | `benford/view` |
| `@auditcore/ui-core` | `BlockProgress` | Schnittstelle | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `BlockView` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `Breakdown` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `BreakdownRow` | Schnittstelle | – | `screening/view` |
| `@auditcore/ui-core` | `BreakdownStep` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `BreakdownTone` | Typ | – | `screening/view` |
| `@auditcore/ui-core` | `ButtonSize` | Typ | – | `base/types` |
| `@auditcore/ui-core` | `ButtonVariant` | Typ | – | `base/types` |
| `@auditcore/ui-core` | `CHANGE_STATUSES` | Konstante | Vorgabe des Filters „Alle Änderungen“: alles außer unverändert. | `synopsis/types` |
| `@auditcore/ui-core` | `COMPARISON_KINDS` | Konstante | – | `documents/form` |
| `@auditcore/ui-core` | `COMPARISON_MODES` | Konstante | – | `documents/form` |
| `@auditcore/ui-core` | `CONTRACT` | Konstante | – | `screening/types` |
| `@auditcore/ui-core` | `Catalogs` | Schnittstelle | Kataloge je Sprache; Deutsch ist vollständig, Englisch darf (noch) lückenhaft sein. | `i18n` |
| `@auditcore/ui-core` | `ChartBar` | Schnittstelle | – | `benford/chart` |
| `@auditcore/ui-core` | `ChartBox` | Schnittstelle | – | `benford/chart` |
| `@auditcore/ui-core` | `ChartGeometry` | Schnittstelle | – | `benford/chart` |
| `@auditcore/ui-core` | `ClientExportFormat` | Typ | – | `synopsis/types` |
| `@auditcore/ui-core` | `ColumnCheck` | Schnittstelle | – | `risk/port` |
| `@auditcore/ui-core` | `ColumnPreview` | Schnittstelle | – | `reporting/types` |
| `@auditcore/ui-core` | `CompareFields` | Schnittstelle | – | `synopsis/port` |
| `@auditcore/ui-core` | `CompareForm` | Schnittstelle | – | `documents/form` |
| `@auditcore/ui-core` | `CompareRow` | Schnittstelle | – | `synopsis/types` |
| `@auditcore/ui-core` | `Comparison` | Schnittstelle | Ein gespeicherter Vergleich (`GET /comparisons/{id}`). | `synopsis/types` |
| `@auditcore/ui-core` | `ComparisonKind` | Typ | – | `documents/form` |
| `@auditcore/ui-core` | `ComparisonMetadata` | Schnittstelle | – | `synopsis/types` |
| `@auditcore/ui-core` | `ComparisonMode` | Typ | – | `documents/form` |
| `@auditcore/ui-core` | `ComparisonProfile` | Schnittstelle | – | `synopsis/types` |
| `@auditcore/ui-core` | `ComparisonResult` | Schnittstelle | – | `synopsis/types` |
| `@auditcore/ui-core` | `ComparisonRow` | Schnittstelle | – | `screening/view` |
| `@auditcore/ui-core` | `ComparisonSummary` | Schnittstelle | – | `synopsis/types` |
| `@auditcore/ui-core` | `ComparisonsBusy` | Typ | – | `documents/controller` |
| `@auditcore/ui-core` | `ComparisonsController` | Typ | – | `documents/controller` |
| `@auditcore/ui-core` | `ComparisonsControllerOptions` | Schnittstelle | – | `documents/controller` |
| `@auditcore/ui-core` | `ComparisonsData` | Schnittstelle | – | `documents/controller` |
| `@auditcore/ui-core` | `ComparisonsError` | Schnittstelle | Fehler einer Portanfrage: Meldung des Servers bzw. `network_error` mit Status 0. | `documents/controller` |
| `@auditcore/ui-core` | `ComparisonsHooks` | Schnittstelle | – | `documents/controller` |
| `@auditcore/ui-core` | `ComparisonsMessageKey` | Typ | – | `documents/messages` |
| `@auditcore/ui-core` | `ComparisonsPort` | Typ | Port zur Anwendung: {@link createSynopsisRestClient } erfüllt ihn vollständig. `load`/`updateRows`/`exportUrl` braucht nur die eingebettete Synopse, `importResult` nur der Import. | `documents/controller` |
| `@auditcore/ui-core` | `ComparisonsTranslate` | Typ | – | `documents/messages` |
| `@auditcore/ui-core` | `ComparisonsView` | Schnittstelle | – | `documents/view` |
| `@auditcore/ui-core` | `ComparisonsViewOptions` | Schnittstelle | – | `documents/view` |
| `@auditcore/ui-core` | `Completeness` | Schnittstelle | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `Conclusion` | Typ | – | `extrapolation/types` |
| `@auditcore/ui-core` | `ConfidenceLevel` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `Conformity` | Schnittstelle | – | `benford/types` |
| `@auditcore/ui-core` | `ConformityProfile` | Schnittstelle | – | `benford/types` |
| `@auditcore/ui-core` | `ConformityRow` | Schnittstelle | – | `benford/types` |
| `@auditcore/ui-core` | `ConsolidatedParagraph` | Schnittstelle | – | `synopsis/types` |
| `@auditcore/ui-core` | `CoordinateError` | Typ | – | `geo/model` |
| `@auditcore/ui-core` | `DATAPROTECTION_CONTRACT` | Konstante | – | `dataprotection/types` |
| `@auditcore/ui-core` | `DEFAULT_BOX` | Konstante | – | `benford/chart` |
| `@auditcore/ui-core` | `DEFAULT_FILTER` | Konstante | – | `risk/state` |
| `@auditcore/ui-core` | `DEFAULT_FORM` | Konstante | – | `documents/form` |
| `@auditcore/ui-core` | `DEFAULT_LOCALE` | Konstante | – | `i18n` |
| `@auditcore/ui-core` | `DEFAULT_MAX_UPLOAD_BYTES` | Konstante | Vorgabe des Servers (`ServiceSettings.max_upload_bytes`). | `documents/form` |
| `@auditcore/ui-core` | `DEFAULT_SYNOPSIS_FILTER` | Konstante | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `DSFA_NOTICES` | Konstante | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `DataProtectionError` | Schnittstelle | Fehler einer Portanfrage: Code und Meldung des Servers bzw. `network_error` mit Status 0. | `dataprotection/requests` |
| `@auditcore/ui-core` | `DataProtectionKey` | Typ | – | `dataprotection/messages` |
| `@auditcore/ui-core` | `DataProtectionPort` | Schnittstelle | Datenzugang der Komponenten. Die mitgelieferte Umsetzung ist `createDataProtectionRestPort`; Anwendungen können eigene Ports übergeben. | `dataprotection/types` |
| `@auditcore/ui-core` | `DataProtectionProfile` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `DataProtectionRequestHooks` | Schnittstelle | – | `dataprotection/requests` |
| `@auditcore/ui-core` | `DataProtectionTranslate` | Typ | – | `dataprotection/messages` |
| `@auditcore/ui-core` | `DatasetFinding` | Schnittstelle | – | `risk/types` |
| `@auditcore/ui-core` | `DbCardView` | Schnittstelle | – | `dbkanban/view` |
| `@auditcore/ui-core` | `DbColumnView` | Schnittstelle | – | `dbkanban/view` |
| `@auditcore/ui-core` | `DbFieldView` | Schnittstelle | – | `dbkanban/view` |
| `@auditcore/ui-core` | `DbGroupOption` | Schnittstelle | – | `dbkanban/view` |
| `@auditcore/ui-core` | `DbKanbanBusy` | Typ | – | `dbkanban/controller` |
| `@auditcore/ui-core` | `DbKanbanController` | Typ | – | `dbkanban/controller` |
| `@auditcore/ui-core` | `DbKanbanControllerOptions` | Schnittstelle | – | `dbkanban/controller` |
| `@auditcore/ui-core` | `DbKanbanData` | Schnittstelle | – | `dbkanban/controller` |
| `@auditcore/ui-core` | `DbKanbanError` | Schnittstelle | – | `dbkanban/controller` |
| `@auditcore/ui-core` | `DbKanbanHooks` | Schnittstelle | – | `dbkanban/controller` |
| `@auditcore/ui-core` | `DbKanbanMessageKey` | Typ | – | `dbkanban/messages` |
| `@auditcore/ui-core` | `DbKanbanTranslate` | Typ | – | `dbkanban/messages` |
| `@auditcore/ui-core` | `DbKanbanView` | Schnittstelle | – | `dbkanban/view` |
| `@auditcore/ui-core` | `DecisionForm` | Schnittstelle | Eingabefelder der Entscheidung, vorbelegt aus der Fassung bzw. dem Vorschlag. | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `DecisionInput` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `DecisionRequest` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `DecisionView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `DegenerateRing` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `DerivationStep` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `DiffField` | Typ | – | `synopsis/types` |
| `@auditcore/ui-core` | `DiffSegment` | Schnittstelle | – | `synopsis/wordDiff` |
| `@auditcore/ui-core` | `DiffSide` | Typ | – | `synopsis/wordDiff` |
| `@auditcore/ui-core` | `DistributionRow` | Schnittstelle | – | `benford/types` |
| `@auditcore/ui-core` | `DossierFieldView` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `DsfaController` | Typ | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `DsfaControllerOptions` | Schnittstelle | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `DsfaData` | Schnittstelle | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `DsfaDerived` | Schnittstelle | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `DsfaHooks` | Schnittstelle | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `DsfaStep` | Typ | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `DsfaTab` | Typ | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `EMPTY_EVALUATION` | Konstante | – | `risk/controller` |
| `@auditcore/ui-core` | `EMPTY_RESIDUAL` | Konstante | – | `extrapolation/model` |
| `@auditcore/ui-core` | `EarthModel` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `EntryView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `EvaluateRequest` | Schnittstelle | – | `risk/port` |
| `@auditcore/ui-core` | `Evaluation` | Schnittstelle | – | `risk/types` |
| `@auditcore/ui-core` | `EvaluationRequest` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `EvaluationResult` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `EvaluationValidation` | Typ | – | `extrapolation/model` |
| `@auditcore/ui-core` | `ExportFormat` | Typ | – | `sampling/types` |
| `@auditcore/ui-core` | `ExportInput` | Schnittstelle | – | `synopsis/exporters` |
| `@auditcore/ui-core` | `ExportPayload` | Schnittstelle | Ergebnis eines Exports in der Oberfläche (Ereignis `export`). | `synopsis/types` |
| `@auditcore/ui-core` | `ExportTexts` | Schnittstelle | – | `dataprotection/exporters` |
| `@auditcore/ui-core` | `ExportedFile` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `ExtractedField` | Schnittstelle | – | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionBusy` | Typ | – | `extraction/controller` |
| `@auditcore/ui-core` | `ExtractionCallbacks` | Schnittstelle | – | `extraction/controller` |
| `@auditcore/ui-core` | `ExtractionCatalogue` | Schnittstelle | – | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionController` | Typ | – | `extraction/controller` |
| `@auditcore/ui-core` | `ExtractionData` | Schnittstelle | – | `extraction/controller` |
| `@auditcore/ui-core` | `ExtractionFieldDecision` | Typ | – | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionFinding` | Schnittstelle | – | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionJson` | Typ | – | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionMessageKey` | Typ | – | `extraction/messages` |
| `@auditcore/ui-core` | `ExtractionOcrQuality` | Typ | – | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionOcrSummary` | Schnittstelle | – | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createExtractionRestPort`. Die Oberfläche erkennt nichts selbst. | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionProfile` | Schnittstelle | Typen des REST-Vertrags `documents_extraction/1` (`docs/ui/extraction-rest.md`, auditcore_documents.web). | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionRun` | Schnittstelle | – | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionRunStatus` | Typ | – | `extraction/types` |
| `@auditcore/ui-core` | `ExtractionSource` | Schnittstelle | – | `extraction/controller` |
| `@auditcore/ui-core` | `ExtractionTone` | Typ | – | `extraction/view` |
| `@auditcore/ui-core` | `ExtractionTranslate` | Typ | – | `extraction/view` |
| `@auditcore/ui-core` | `ExtractionValidation` | Typ | – | `extraction/controller` |
| `@auditcore/ui-core` | `ExtrapolationBusy` | Typ | – | `extrapolation/controller` |
| `@auditcore/ui-core` | `ExtrapolationCallbacks` | Schnittstelle | – | `extrapolation/controller` |
| `@auditcore/ui-core` | `ExtrapolationCatalogue` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `ExtrapolationController` | Typ | – | `extrapolation/controller` |
| `@auditcore/ui-core` | `ExtrapolationData` | Schnittstelle | Stand der Hochrechnung; `error` ist die Meldung der letzten abgelehnten Anfrage. | `extrapolation/controller` |
| `@auditcore/ui-core` | `ExtrapolationExportFormat` | Typ | – | `extrapolation/types` |
| `@auditcore/ui-core` | `ExtrapolationField` | Schnittstelle | – | `extrapolation/view` |
| `@auditcore/ui-core` | `ExtrapolationForm` | Schnittstelle | – | `extrapolation/model` |
| `@auditcore/ui-core` | `ExtrapolationFormError` | Typ | – | `extrapolation/model` |
| `@auditcore/ui-core` | `ExtrapolationIssue` | Typ | – | `extrapolation/model` |
| `@auditcore/ui-core` | `ExtrapolationIssues` | Typ | – | `extrapolation/model` |
| `@auditcore/ui-core` | `ExtrapolationMessageKey` | Typ | – | `extrapolation/messages` |
| `@auditcore/ui-core` | `ExtrapolationMethod` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `ExtrapolationMethodGroup` | Schnittstelle | – | `extrapolation/view` |
| `@auditcore/ui-core` | `ExtrapolationMetric` | Schnittstelle | – | `extrapolation/view` |
| `@auditcore/ui-core` | `ExtrapolationPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createExtrapolationRestPort`. | `extrapolation/types` |
| `@auditcore/ui-core` | `ExtrapolationSource` | Schnittstelle | – | `extrapolation/controller` |
| `@auditcore/ui-core` | `ExtrapolationStep` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `ExtrapolationTranslate` | Typ | – | `extrapolation/view` |
| `@auditcore/ui-core` | `FLAG_STATES` | Konstante | – | `risk/state` |
| `@auditcore/ui-core` | `FactorProfileInfo` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `FieldEntry` | Schnittstelle | – | `risk/types` |
| `@auditcore/ui-core` | `FieldError` | Schnittstelle | – | `sampling/model` |
| `@auditcore/ui-core` | `FieldErrorCode` | Typ | – | `sampling/model` |
| `@auditcore/ui-core` | `FieldKind` | Typ | – | `dataprotection/types` |
| `@auditcore/ui-core` | `FieldUse` | Schnittstelle | – | `risk/types` |
| `@auditcore/ui-core` | `FieldValue` | Typ | – | `dataprotection/types` |
| `@auditcore/ui-core` | `FieldView` | Schnittstelle | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `FilterOptions` | Schnittstelle | – | `screening/view` |
| `@auditcore/ui-core` | `FindingView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `FlagEntry` | Schnittstelle | Ein Eintrag der Detailansicht: Treffer oder unbestimmtes Merkmal eines Datensatzes. | `risk/state` |
| `@auditcore/ui-core` | `FlagHit` | Schnittstelle | – | `risk/types` |
| `@auditcore/ui-core` | `FlagState` | Typ | Zustand einer Regel für einen Datensatz. | `risk/state` |
| `@auditcore/ui-core` | `FocusTrap` | Schnittstelle | – | `focus` |
| `@auditcore/ui-core` | `FormProblem` | Schnittstelle | Ein Befund der Formularprüfung: Textschlüssel und Platzhalter. | `documents/form` |
| `@auditcore/ui-core` | `FormatProfile` | Schnittstelle | – | `reporting/types` |
| `@auditcore/ui-core` | `FreshnessStatus` | Typ | – | `screening/types` |
| `@auditcore/ui-core` | `FreshnessView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `GeoArea` | Schnittstelle | Fläche auf der Karte (z. B. Schutzgebiet); `notes` sind Hinweise zur Geometrie. | `geo/types` |
| `@auditcore/ui-core` | `GeoBusy` | Typ | – | `geo/controller` |
| `@auditcore/ui-core` | `GeoCatalogue` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `GeoController` | Typ | – | `geo/controller` |
| `@auditcore/ui-core` | `GeoControllerOptions` | Schnittstelle | – | `geo/controller` |
| `@auditcore/ui-core` | `GeoData` | Schnittstelle | – | `geo/controller` |
| `@auditcore/ui-core` | `GeoField` | Typ | Einfache Eingabefelder, die die Oberfläche direkt setzen darf. | `geo/controller` |
| `@auditcore/ui-core` | `GeoHint` | Typ | – | `geo/controller` |
| `@auditcore/ui-core` | `GeoInputs` | Schnittstelle | Eingaben der Komponente (Props). | `geo/controller` |
| `@auditcore/ui-core` | `GeoMapCallbacks` | Schnittstelle | – | `geo/controller` |
| `@auditcore/ui-core` | `GeoMessageKey` | Typ | – | `geo/messages` |
| `@auditcore/ui-core` | `GeoPackageArea` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `GeoPackageResult` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `GeoPoint` | Schnittstelle | Punkt auf der Karte (z. B. Vorhabenstandort); `id` ist die Kennung in Ergebnissen. | `geo/types` |
| `@auditcore/ui-core` | `GeoPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createGeoRestPort`. | `geo/types` |
| `@auditcore/ui-core` | `GeoRestOptions` | Schnittstelle | – | `geo/rest-port` |
| `@auditcore/ui-core` | `GeoSelection` | Schnittstelle | – | `geo/controller` |
| `@auditcore/ui-core` | `GeocodeHit` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `GeocodeResult` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `HitFilter` | Schnittstelle | – | `screening/view` |
| `@auditcore/ui-core` | `HitView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `ICONS` | Konstante | Eigene Strichsymbole (24er-Raster, Strichstärke über CSS). Jede Zeile ist eine Liste von SVG-Pfaden; neue Symbole nur hier ergänzen. | `base/icons` |
| `@auditcore/ui-core` | `IDLE` | Konstante | – | `store` |
| `@auditcore/ui-core` | `INITIAL_BENFORD` | Konstante | – | `benford/controller` |
| `@auditcore/ui-core` | `INITIAL_COMPARISONS` | Konstante | – | `documents/controller` |
| `@auditcore/ui-core` | `INITIAL_DB_KANBAN` | Konstante | – | `dbkanban/controller` |
| `@auditcore/ui-core` | `INITIAL_EXTRACTION` | Konstante | – | `extraction/controller` |
| `@auditcore/ui-core` | `INITIAL_EXTRAPOLATION` | Konstante | – | `extrapolation/controller` |
| `@auditcore/ui-core` | `INITIAL_IDENTIFIERS` | Konstante | – | `identifiers/controller` |
| `@auditcore/ui-core` | `INITIAL_REPORTING` | Konstante | – | `reporting/controller` |
| `@auditcore/ui-core` | `INITIAL_SAMPLING` | Konstante | – | `sampling/controller` |
| `@auditcore/ui-core` | `IconName` | Typ | – | `base/icons` |
| `@auditcore/ui-core` | `IdentifierBatchAnswer` | Schnittstelle | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierBatchItem` | Schnittstelle | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierBatchLine` | Schnittstelle | Anzeigezeile der Stapelprüfung (Tabelle und CSV). | `identifiers/model` |
| `@auditcore/ui-core` | `IdentifierBatchMapping` | Schnittstelle | – | `identifiers/model` |
| `@auditcore/ui-core` | `IdentifierBatchRequest` | Schnittstelle | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierBatchRow` | Typ | Zeile der Stapelprüfung: Ergebnisfelder oder `error` (Art unbekannt bzw. vom Profil nicht geprüft). | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierBatchSummary` | Schnittstelle | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierBusy` | Typ | – | `identifiers/controller` |
| `@auditcore/ui-core` | `IdentifierCallbacks` | Schnittstelle | – | `identifiers/controller` |
| `@auditcore/ui-core` | `IdentifierCatalogue` | Schnittstelle | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierCheckAnswer` | Schnittstelle | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierCheckInput` | Schnittstelle | – | `identifiers/model` |
| `@auditcore/ui-core` | `IdentifierCheckRequest` | Schnittstelle | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierColumn` | Typ | – | `identifiers/model` |
| `@auditcore/ui-core` | `IdentifierColumnField` | Schnittstelle | – | `identifiers/model` |
| `@auditcore/ui-core` | `IdentifierController` | Typ | – | `identifiers/controller` |
| `@auditcore/ui-core` | `IdentifierData` | Schnittstelle | – | `identifiers/controller` |
| `@auditcore/ui-core` | `IdentifierDetailValue` | Typ | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierError` | Typ | – | `identifiers/model` |
| `@auditcore/ui-core` | `IdentifierField` | Typ | Einfache Eingabefelder, die die Oberfläche direkt setzen darf. | `identifiers/controller` |
| `@auditcore/ui-core` | `IdentifierKindInfo` | Schnittstelle | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierMessageKey` | Typ | – | `identifiers/messages` |
| `@auditcore/ui-core` | `IdentifierProfileInfo` | Schnittstelle | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierResult` | Schnittstelle | – | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierSource` | Schnittstelle | – | `identifiers/controller` |
| `@auditcore/ui-core` | `IdentifierStatus` | Typ | Typen des REST-Vertrags `identifiers_ui/1` (`docs/ui/identifiers-rest.md`, auditcore_identifiers.web). | `identifiers/types` |
| `@auditcore/ui-core` | `IdentifierTone` | Typ | – | `identifiers/model` |
| `@auditcore/ui-core` | `IdentifierTranslate` | Typ | – | `identifiers/model` |
| `@auditcore/ui-core` | `IdentifierValidation` | Typ | – | `identifiers/model` |
| `@auditcore/ui-core` | `IdentifiersPort` | Schnittstelle | Schnittstelle zur Fachlogik; Standardumsetzung `createIdentifiersRestPort`. | `identifiers/types` |
| `@auditcore/ui-core` | `ImportParse` | Typ | – | `documents/importing` |
| `@auditcore/ui-core` | `ImportRequest` | Schnittstelle | Anfrage von `POST /comparisons/import`: ein fertiges Ergebnis aus der Auftragssteuerung ablegen. | `synopsis/port` |
| `@auditcore/ui-core` | `ImportedColumns` | Schnittstelle | Übernommene Spalten einer Datei. | `tabular/tableImport` |
| `@auditcore/ui-core` | `JsonObject` | Typ | – | `risk/types` |
| `@auditcore/ui-core` | `JsonValue` | Typ | Datentypen des REST-Vertrags `auditcore_risk.web` (docs/ui/risk-rest.md). Die Komponenten lesen nur diese Felder; unbekannte Felder werden ignoriert. | `risk/types` |
| `@auditcore/ui-core` | `KanbanDialogMessageKey` | Typ | – | `kanban/messages` |
| `@auditcore/ui-core` | `KanbanMessageKey` | Typ | – | `kanban/messages` |
| `@auditcore/ui-core` | `KeyTitle` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `LOCALES` | Konstante | – | `i18n` |
| `@auditcore/ui-core` | `LatLon` | Schnittstelle | Typen des REST-Vertrags `docs/ui/geo-rest.md` (auditcore_geo.web). | `geo/types` |
| `@auditcore/ui-core` | `LevelTone` | Typ | – | `benford/model` |
| `@auditcore/ui-core` | `LevelView` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `ListInfo` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `Locale` | Typ | Framework-freier Kern der Sprachunterstützung: Kataloge, Platzhalter, Rückfall auf Deutsch. | `i18n` |
| `@auditcore/ui-core` | `LocateRequest` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `LocateResult` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `LogEntry` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `LogView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `MAX_THRESHOLD` | Konstante | – | `documents/form` |
| `@auditcore/ui-core` | `MAX_TITLE` | Konstante | – | `documents/form` |
| `@auditcore/ui-core` | `MIN_THRESHOLD` | Konstante | – | `documents/form` |
| `@auditcore/ui-core` | `MapLayers` | Schnittstelle | – | `geo/mapView` |
| `@auditcore/ui-core` | `MapView` | Schnittstelle | – | `geo/mapView` |
| `@auditcore/ui-core` | `MapViewOptions` | Schnittstelle | – | `geo/mapView` |
| `@auditcore/ui-core` | `MatchState` | Typ | – | `screening/view` |
| `@auditcore/ui-core` | `MeasureView` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `MessageParams` | Typ | – | `i18n` |
| `@auditcore/ui-core` | `MethodGroup` | Schnittstelle | – | `sampling/view` |
| `@auditcore/ui-core` | `MethodKind` | Typ | – | `sampling/types` |
| `@auditcore/ui-core` | `MethodProfile` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `MethodStatus` | Typ | – | `sampling/types` |
| `@auditcore/ui-core` | `NO_DEPARTMENT` | Konstante | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `NamedOption` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `Outcome` | Typ | – | `screening/types` |
| `@auditcore/ui-core` | `OverviewRow` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `ParameterSpec` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `Person` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `PopulationItem` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `Position` | Typ | – | `geo/types` |
| `@auditcore/ui-core` | `ProblemView` | Schnittstelle | – | `documents/view` |
| `@auditcore/ui-core` | `ProfileDetail` | Schnittstelle | – | `risk/types` |
| `@auditcore/ui-core` | `ProfileOption` | Schnittstelle | – | `documents/view` |
| `@auditcore/ui-core` | `ProfileReference` | Schnittstelle | – | `risk/types` |
| `@auditcore/ui-core` | `ProfileStatus` | Typ | – | `risk/types` |
| `@auditcore/ui-core` | `ProfileSummary` | Schnittstelle | – | `risk/port` |
| `@auditcore/ui-core` | `ProfileView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `Projection` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `Proposal` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `QuestionView` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `RESIDUAL_FIELDS` | Konstante | – | `extrapolation/view` |
| `@auditcore/ui-core` | `ROW_STATUSES` | Konstante | – | `synopsis/types` |
| `@auditcore/ui-core` | `RadiusHit` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `RadiusRequest` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `RadiusResult` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `RecordMove` | Schnittstelle | Verschiebung einer Karte: der gesetzte Zellwert (`null` = ohne Wert). | `dbkanban/controller` |
| `@auditcore/ui-core` | `RecordView` | Schnittstelle | – | `risk/types` |
| `@auditcore/ui-core` | `RegisterColumn` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `RegisterContent` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `RegisterExportFormat` | Typ | – | `dataprotection/types` |
| `@auditcore/ui-core` | `RegisterExportInput` | Schnittstelle | – | `dataprotection/exporters` |
| `@auditcore/ui-core` | `RegisterIssue` | Schnittstelle | Hinweis der Vollständigkeitsprüfung; `subject` = `<Tätigkeits-ID>:<Feld>` oder `deckblatt:<Teil>`. | `dataprotection/types` |
| `@auditcore/ui-core` | `RegisterState` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `RegisterStatus` | Typ | – | `dataprotection/types` |
| `@auditcore/ui-core` | `ReportCell` | Typ | – | `reporting/types` |
| `@auditcore/ui-core` | `ReportColumnType` | Typ | Spaltentyp: `json` übernimmt den JSON-Typ wie gesendet; `date`/`datetime` erwarten ISO-Text. | `reporting/types` |
| `@auditcore/ui-core` | `ReportTableInput` | Schnittstelle | Eine Tabelle (ein Blatt) der Anwendung; Zeilen in Spaltenreihenfolge. | `reporting/types` |
| `@auditcore/ui-core` | `ReportingBusy` | Typ | – | `reporting/controller` |
| `@auditcore/ui-core` | `ReportingCallbacks` | Schnittstelle | – | `reporting/controller` |
| `@auditcore/ui-core` | `ReportingCatalogue` | Schnittstelle | – | `reporting/types` |
| `@auditcore/ui-core` | `ReportingController` | Typ | – | `reporting/controller` |
| `@auditcore/ui-core` | `ReportingData` | Schnittstelle | – | `reporting/controller` |
| `@auditcore/ui-core` | `ReportingError` | Typ | – | `reporting/controller` |
| `@auditcore/ui-core` | `ReportingMessageKey` | Typ | – | `reporting/messages` |
| `@auditcore/ui-core` | `ReportingPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createReportingRestPort`. | `reporting/types` |
| `@auditcore/ui-core` | `ReportingSource` | Schnittstelle | – | `reporting/controller` |
| `@auditcore/ui-core` | `ReportingTranslate` | Typ | – | `reporting/view` |
| `@auditcore/ui-core` | `RequestState` | Schnittstelle | Beschäftigt-Status, Fehler und Erfolgsmeldung einer Portanfrage (gemeinsam für alle Controller). | `store` |
| `@auditcore/ui-core` | `ResidualErrorRate` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `ResidualForm` | Schnittstelle | – | `extrapolation/model` |
| `@auditcore/ui-core` | `ResidualRequest` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `ResidualResult` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `ResidualRow` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `ResidualValidation` | Typ | – | `extrapolation/model` |
| `@auditcore/ui-core` | `RestClientOptions` | Typ | Optionen wie bei `src/rest`: `baseUrl` (z. B. `/api/synopsis`), injizierbares `fetch`, Kopfzeilen. | `synopsis/port` |
| `@auditcore/ui-core` | `ReviewEvents` | Schnittstelle | – | `screening/controller` |
| `@auditcore/ui-core` | `ReviewStatus` | Typ | – | `screening/types` |
| `@auditcore/ui-core` | `ReviewView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `RiskController` | Typ | – | `risk/controller` |
| `@auditcore/ui-core` | `RiskData` | Schnittstelle | – | `risk/controller` |
| `@auditcore/ui-core` | `RiskDistributionRow` | Schnittstelle | – | `risk/state` |
| `@auditcore/ui-core` | `RiskFilter` | Schnittstelle | – | `risk/state` |
| `@auditcore/ui-core` | `RiskInputs` | Schnittstelle | Eingaben der Gesamtansicht (Props). | `risk/controller` |
| `@auditcore/ui-core` | `RiskMessageKey` | Typ | – | `risk/messages` |
| `@auditcore/ui-core` | `RiskPort` | Schnittstelle | – | `risk/port` |
| `@auditcore/ui-core` | `RiskSelection` | Schnittstelle | Alles, was die Gesamtansicht aus Stand und Auswertung anzeigt (reine Funktion). | `risk/controller` |
| `@auditcore/ui-core` | `RiskTranslate` | Typ | – | `risk/controller` |
| `@auditcore/ui-core` | `RowStatus` | Typ | JSON-Formen des REST-Vertrags (docs/ui/synopsis-rest.md). Sie entsprechen `ComparisonResult.to_dict()` aus `auditcore_documents`; die Oberfläche kennt keine zweite Datenform. | `synopsis/types` |
| `@auditcore/ui-core` | `RowUpdate` | Schnittstelle | Änderung einer Zeile (`PATCH /comparisons/{id}/rows`). | `synopsis/types` |
| `@auditcore/ui-core` | `RowView` | Schnittstelle | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `RuleView` | Schnittstelle | – | `risk/types` |
| `@auditcore/ui-core` | `RunQuery` | Typ | – | `screening/types` |
| `@auditcore/ui-core` | `RunRequest` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `RunRequestRecord` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `RunSummary` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `RunView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `SCREENING_CONTRACT` | Konstante | – | `screening/types` |
| `@auditcore/ui-core` | `SCREENING_KINDS` | Konstante | – | `screening/runForm` |
| `@auditcore/ui-core` | `STATE_FILTER_KEYS` | Konstante | – | `risk/labels` |
| `@auditcore/ui-core` | `STATE_ICONS` | Konstante | Symbol je Zustand: Farbe ist nie der einzige Träger der Bedeutung. | `risk/format` |
| `@auditcore/ui-core` | `STATE_KEYS` | Konstante | – | `risk/labels` |
| `@auditcore/ui-core` | `STRATUM_FIELDS` | Konstante | – | `extrapolation/view` |
| `@auditcore/ui-core` | `SamplingBusy` | Typ | – | `sampling/controller` |
| `@auditcore/ui-core` | `SamplingCallbacks` | Schnittstelle | – | `sampling/controller` |
| `@auditcore/ui-core` | `SamplingCatalogue` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `SamplingController` | Typ | – | `sampling/controller` |
| `@auditcore/ui-core` | `SamplingData` | Schnittstelle | Stand des Stichprobenrechners; `error` ist die Meldung der letzten abgelehnten Anfrage. | `sampling/controller` |
| `@auditcore/ui-core` | `SamplingMessageKey` | Typ | – | `sampling/messages` |
| `@auditcore/ui-core` | `SamplingPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createSamplingRestPort`. | `sampling/types` |
| `@auditcore/ui-core` | `SamplingSource` | Schnittstelle | – | `sampling/controller` |
| `@auditcore/ui-core` | `SamplingTranslate` | Typ | – | `sampling/view` |
| `@auditcore/ui-core` | `ScenarioInput` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `ScenarioResult` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `ScoreClass` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `ScreeningController` | Typ | – | `screening/controller` |
| `@auditcore/ui-core` | `ScreeningData` | Schnittstelle | – | `screening/controller` |
| `@auditcore/ui-core` | `ScreeningDecisionForm` | Schnittstelle | – | `screening/view` |
| `@auditcore/ui-core` | `ScreeningError` | Schnittstelle | Fehler einer Portanfrage: Meldung des Servers bzw. `network_error` mit Status 0. | `screening/controller` |
| `@auditcore/ui-core` | `ScreeningKey` | Typ | – | `screening/messages` |
| `@auditcore/ui-core` | `ScreeningKind` | Typ | – | `screening/types` |
| `@auditcore/ui-core` | `ScreeningPort` | Schnittstelle | Port der Screening-Trefferprüfung. Die Komponente ruft nie selbst `fetch` auf; `createScreeningRestPort` ist die mitgelieferte REST-Umsetzung. | `screening/types` |
| `@auditcore/ui-core` | `ScreeningRunFormState` | Schnittstelle | – | `screening/runForm` |
| `@auditcore/ui-core` | `ScreeningSelection` | Schnittstelle | – | `screening/controller` |
| `@auditcore/ui-core` | `ScreeningTranslate` | Typ | – | `screening/messages` |
| `@auditcore/ui-core` | `SecondReviewRequest` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `SecondReviewView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `SegmentKind` | Typ | Wortdifferenz für die Anzeige, ohne Vue. Bevorzugt die vom Server gelieferte `difflib.ndiff`-Folge (`"  "` gleich, `"- "` entfallen, `"+ "` neu, `"? "` Hinweis); fehlt sie (Gesetze … | `synopsis/wordDiff` |
| `@auditcore/ui-core` | `SelectionError` | Typ | – | `sampling/controller` |
| `@auditcore/ui-core` | `SelectionInput` | Schnittstelle | – | `sampling/model` |
| `@auditcore/ui-core` | `SelectionRequest` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `SelectionResult` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `SelectionRow` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `SelectionTexts` | Schnittstelle | – | `sampling/view` |
| `@auditcore/ui-core` | `SelectionValidation` | Typ | – | `sampling/model` |
| `@auditcore/ui-core` | `SelectionVariant` | Typ | – | `sampling/types` |
| `@auditcore/ui-core` | `ServerExportFormat` | Typ | – | `synopsis/types` |
| `@auditcore/ui-core` | `ServerExportLink` | Schnittstelle | – | `synopsis/controller` |
| `@auditcore/ui-core` | `SettingsView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `Severity` | Typ | – | `risk/types` |
| `@auditcore/ui-core` | `ShortValues` | Typ | – | `benford/types` |
| `@auditcore/ui-core` | `SimplifyRequest` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `SimplifyResult` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `SimplifyUnit` | Typ | – | `geo/types` |
| `@auditcore/ui-core` | `SizeRequest` | Typ | – | `sampling/types` |
| `@auditcore/ui-core` | `SizeResult` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `SizeValidation` | Typ | – | `sampling/model` |
| `@auditcore/ui-core` | `SourceView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `SourcesView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `StateFilter` | Typ | Filter: `affected` = Treffer oder unbestimmt; `all` = jeder Datensatz. | `risk/state` |
| `@auditcore/ui-core` | `Store` | Schnittstelle | Kleinster gemeinsamer Zustandsspeicher der Controller. | `store` |
| `@auditcore/ui-core` | `StratumCount` | Schnittstelle | – | `sampling/model` |
| `@auditcore/ui-core` | `StratumInput` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `StratumProjection` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `StratumResult` | Schnittstelle | – | `sampling/types` |
| `@auditcore/ui-core` | `StratumRow` | Schnittstelle | – | `extrapolation/model` |
| `@auditcore/ui-core` | `SubjectInput` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `SubjectRequest` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `SubjectStatus` | Typ | – | `screening/types` |
| `@auditcore/ui-core` | `SubjectView` | Schnittstelle | – | `screening/types` |
| `@auditcore/ui-core` | `SummaryView` | Schnittstelle | – | `documents/list` |
| `@auditcore/ui-core` | `SurveyInput` | Schnittstelle | Erhebung einer Folgenabschätzung, wie sie `POST /assessments/{id}` erwartet. | `dataprotection/types` |
| `@auditcore/ui-core` | `SynopsisController` | Typ | – | `synopsis/controller` |
| `@auditcore/ui-core` | `SynopsisData` | Schnittstelle | – | `synopsis/controller` |
| `@auditcore/ui-core` | `SynopsisFilterState` | Schnittstelle | – | `synopsis/controller` |
| `@auditcore/ui-core` | `SynopsisInputs` | Schnittstelle | Eingaben der Komponente (Props). | `synopsis/controller` |
| `@auditcore/ui-core` | `SynopsisLayout` | Typ | – | `synopsis/types` |
| `@auditcore/ui-core` | `SynopsisMessageKey` | Typ | – | `synopsis/messages` |
| `@auditcore/ui-core` | `SynopsisPort` | Schnittstelle | – | `synopsis/port` |
| `@auditcore/ui-core` | `SynopsisRestClient` | Schnittstelle | – | `synopsis/port` |
| `@auditcore/ui-core` | `SynopsisRowFilter` | Schnittstelle | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `SynopsisSelection` | Schnittstelle | Alles, was die Oberfläche aus Stand und Eingaben anzeigt (reine Funktion). | `synopsis/controller` |
| `@auditcore/ui-core` | `SynopsisTranslate` | Typ | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `SynopsisView` | Schnittstelle | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `TOLERANCE_STEPS` | Konstante | Stufen des Toleranzreglers der Vereinfachung (Meter bzw. Grad). | `geo/model` |
| `@auditcore/ui-core` | `TabItem` | Schnittstelle | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `TableImportController` | Typ | – | `tabular/tableImport` |
| `@auditcore/ui-core` | `TableImportData` | Schnittstelle | – | `tabular/tableImport` |
| `@auditcore/ui-core` | `TablePreview` | Schnittstelle | – | `reporting/types` |
| `@auditcore/ui-core` | `TabularMessageKey` | Typ | – | `tabular/messages` |
| `@auditcore/ui-core` | `TileSource` | Schnittstelle | Kachelquelle der Anwendung; ohne Quelle zeigt die Karte keinen Hintergrund. | `geo/types` |
| `@auditcore/ui-core` | `Tone` | Typ | Farbton wie `FaBadge` (`tone`). | `risk/format` |
| `@auditcore/ui-core` | `TotalErrorRate` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `Totals` | Schnittstelle | – | `risk/state` |
| `@auditcore/ui-core` | `Translate` | Typ | – | `i18n` |
| `@auditcore/ui-core` | `UNIT_FIELDS` | Konstante | – | `extrapolation/view` |
| `@auditcore/ui-core` | `UNIT_FLAGS` | Konstante | – | `extrapolation/view` |
| `@auditcore/ui-core` | `UnitInput` | Schnittstelle | – | `extrapolation/types` |
| `@auditcore/ui-core` | `UnitRow` | Schnittstelle | – | `extrapolation/model` |
| `@auditcore/ui-core` | `UploadFile` | Schnittstelle | Datei aus einem Eingabefeld (im Browser `File`). | `documents/form` |
| `@auditcore/ui-core` | `UtmInput` | Schnittstelle | – | `geo/model` |
| `@auditcore/ui-core` | `UtmInputError` | Typ | – | `geo/model` |
| `@auditcore/ui-core` | `UtmPointRequest` | Schnittstelle | `POST /utm/geographisch`: Punkt aus Rechts-/Hochwert, Zone und Halbkugel. | `geo/types` |
| `@auditcore/ui-core` | `UtmPointResult` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `UtmRequest` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `UtmResult` | Schnittstelle | – | `geo/types` |
| `@auditcore/ui-core` | `VersionSummary` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `VersionView` | Schnittstelle | – | `dataprotection/types` |
| `@auditcore/ui-core` | `ViewMessage` | Schnittstelle | Meldung als Katalogschlüssel mit Platzhaltern; die Komponente übersetzt sie. | `screening/view` |
| `@auditcore/ui-core` | `ViewOptions` | Schnittstelle | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `VvtController` | Typ | – | `dataprotection/vvt` |
| `@auditcore/ui-core` | `VvtControllerOptions` | Schnittstelle | – | `dataprotection/vvt` |
| `@auditcore/ui-core` | `VvtData` | Schnittstelle | – | `dataprotection/vvt` |
| `@auditcore/ui-core` | `VvtExport` | Schnittstelle | – | `dataprotection/vvt` |
| `@auditcore/ui-core` | `VvtExportFormat` | Typ | – | `dataprotection/vvt` |
| `@auditcore/ui-core` | `VvtHooks` | Schnittstelle | – | `dataprotection/vvt` |
| `@auditcore/ui-core` | `VvtView` | Schnittstelle | Abgeleitete Werte eines Stands (reine Funktion, von beiden Oberflächen genutzt). | `dataprotection/vvt` |
| `@auditcore/ui-core` | `WORD_LIMIT` | Konstante | Oberhalb dieser Wortzahl je Seite wird nicht wortweise verglichen. | `synopsis/wordDiff` |
| `@auditcore/ui-core` | `WhenMissingColumns` | Typ | – | `risk/types` |
| `@auditcore/ui-core` | `WorkbookPreview` | Schnittstelle | – | `reporting/types` |
| `@auditcore/ui-core` | `WorkbookRequest` | Schnittstelle | – | `reporting/types` |
| `@auditcore/ui-core` | `acceptsHit` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `activityKey` | Funktion | Schlüssel einer Tätigkeit für die Zuordnung der Hinweise (Kennung, sonst Name wie in der Bibliothek). | `dataprotection/registerView` |
| `@auditcore/ui-core` | `addScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `analyseErrorKey` | Funktion | – | `benford/view` |
| `@auditcore/ui-core` | `answerOf` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `applyRowOverrides` | Funktion | Zeilen mit lokalen Änderungen (Auswahl, Grund) zusammenführen. | `synopsis/viewModel` |
| `@auditcore/ui-core` | `areasFromGeoPackage` | Funktion | Flächen aus einer GeoPackage-Antwort; Kennungen erhalten die Herkunft als Präfix. | `geo/model` |
| `@auditcore/ui-core` | `asComparisonsError` | Funktion | – | `documents/controller` |
| `@auditcore/ui-core` | `asDbKanbanError` | Funktion | – | `dbkanban/controller` |
| `@auditcore/ui-core` | `asScreeningError` | Funktion | – | `screening/controller` |
| `@auditcore/ui-core` | `awaitsSecondReview` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `axisMaximum` | Funktion | Obergrenze der y-Achse: nächstes Vielfaches des Tickabstands über dem Maximum. | `benford/chart` |
| `@auditcore/ui-core` | `bandTone` | Funktion | Stufe eines Risikos nach Rang im Profil: höchste Stufe rot, zweithöchste gelb. | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `baseMessages` | Konstante | Texte der Basiskomponenten. | `messages` |
| `@auditcore/ui-core` | `benfordBarTitle` | Funktion | Titel eines Balkens (Tooltip und Vorlesetext). | `benford/view` |
| `@auditcore/ui-core` | `benfordChartTitle` | Funktion | – | `benford/view` |
| `@auditcore/ui-core` | `benfordDigitColumns` | Funktion | – | `benford/view` |
| `@auditcore/ui-core` | `benfordDigitRows` | Funktion | – | `benford/view` |
| `@auditcore/ui-core` | `benfordMessages` | Konstante | Texte der Benford-Analyse. | `benford/messages` |
| `@auditcore/ui-core` | `benfordMetricTexts` | Funktion | – | `benford/view` |
| `@auditcore/ui-core` | `benfordProfile` | Funktion | – | `benford/controller` |
| `@auditcore/ui-core` | `benfordTickText` | Funktion | – | `benford/view` |
| `@auditcore/ui-core` | `benfordValues` | Funktion | – | `benford/controller` |
| `@auditcore/ui-core` | `benfordValuesText` | Funktion | – | `benford/view` |
| `@auditcore/ui-core` | `blockProgress` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `breakdownRows` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `buildAnalyseRequest` | Funktion | Anfrage für `POST /analyze`; Test, Profil und ggf. Regel für kurze Werte sind Pflicht. | `benford/model` |
| `@auditcore/ui-core` | `buildEvaluationRequest` | Funktion | Anfrage für `POST /evaluate`; bei Befunden die Feldschlüssel mit ihrem Fehler. | `extrapolation/model` |
| `@auditcore/ui-core` | `buildIdentifierBatch` | Funktion | Anfrage für `POST /check/batch` aus der geladenen Tabelle und der Spaltenzuordnung. | `identifiers/model` |
| `@auditcore/ui-core` | `buildIdentifierCheck` | Funktion | Anfrage für `POST /check`; Profil und Kennungsart sind Pflicht, ein leerer Wert ergibt „fehlt“. | `identifiers/model` |
| `@auditcore/ui-core` | `buildResidualRequest` | Funktion | Anfrage für `POST /residual`; die Gesamtfehlerquote wird in Prozent eingegeben. | `extrapolation/model` |
| `@auditcore/ui-core` | `buildRowView` | Funktion | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `buildRunRequest` | Funktion | Anfrage aus dem Formular; bei Fehlern `request: null` und die Meldungen als Katalogschlüssel. | `screening/runForm` |
| `@auditcore/ui-core` | `buildSelectionRequest` | Funktion | Anfrage für `POST /selection`; ein leerer Seed überlässt dem Server die Erzeugung. | `sampling/model` |
| `@auditcore/ui-core` | `buildSizeRequest` | Funktion | Anfrage für `POST /size`; jedes Feld ist Pflicht, nichts wird still ergänzt. | `sampling/model` |
| `@auditcore/ui-core` | `buildSynopsisExport` | Funktion | Export der sichtbaren Zeilen (HTML, Markdown, Druckansicht). | `synopsis/controller` |
| `@auditcore/ui-core` | `buildSynopsisView` | Funktion | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `buildVvtExport` | Funktion | – | `dataprotection/vvt` |
| `@auditcore/ui-core` | `buildWorkbookRequest` | Funktion | Anfrage aus Zustand und Tabellen oder der erste fehlende Punkt. | `reporting/controller` |
| `@auditcore/ui-core` | `canDecide` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `canReleaseAssessment` | Funktion | Freigabe möglich: Vier-Augen-Vorprüfung, keine ungespeicherten Eingaben, keine Sperrgründe. | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `cellAlignClass` | Funktion | – | `table/index` |
| `@auditcore/ui-core` | `cellText` | Funktion | – | `table/index` |
| `@auditcore/ui-core` | `changeIds` | Funktion | Kennungen der Änderungszeilen in Anzeigereihenfolge (Ziel der Navigation). | `synopsis/viewModel` |
| `@auditcore/ui-core` | `chartGeometry` | Funktion | – | `benford/chart` |
| `@auditcore/ui-core` | `cloneContent` | Funktion | Tiefe Kopie (JSON-Daten), damit Eingaben den gelesenen Stand nie verändern. | `dataprotection/registerView` |
| `@auditcore/ui-core` | `codeLabel` | Funktion | Beschriftung eines Codes aus dem Vertrag (Status, Stufe, Hinweis); unbekannte Codes bleiben stehen. | `screening/messages` |
| `@auditcore/ui-core` | `columnLabel` | Funktion | – | `dbkanban/view` |
| `@auditcore/ui-core` | `comparisonRows` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `comparisonsMessages` | Konstante | Texte der Vergleichsverwaltung (`<flowaudit-comparisons>`): Hochladen, gespeicherte Vergleiche, Import und Löschen. Begriffe wie in der Synopse. | `documents/messages` |
| `@auditcore/ui-core` | `comparisonsView` | Funktion | – | `documents/view` |
| `@auditcore/ui-core` | `completeness` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `completenessTone` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `conclusionLabel` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `conclusionTone` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `confidenceChoices` | Funktion | Konfidenzniveaus, die die gewählte Methode mit Tabellenwerten erlaubt. | `extrapolation/model` |
| `@auditcore/ui-core` | `confidenceText` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `coverIssues` | Funktion | Hinweise zum Deckblatt (Verantwortlicher, DSB). | `dataprotection/registerView` |
| `@auditcore/ui-core` | `createBenfordController` | Funktion | – | `benford/controller` |
| `@auditcore/ui-core` | `createBenfordRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_statistics.web` (Starlette oder FastAPI). | `benford/rest-port` |
| `@auditcore/ui-core` | `createComparisonsController` | Funktion | – | `documents/controller` |
| `@auditcore/ui-core` | `createDataProtectionRestPort` | Funktion | Port auf den REST-Vertrag `dataprotection_ui/1` von `auditcore_dataprotection.web`. | `dataprotection/rest-port` |
| `@auditcore/ui-core` | `createDbKanbanController` | Funktion | – | `dbkanban/controller` |
| `@auditcore/ui-core` | `createDelay` | Funktion | Verzögerter Aufruf, der bei jeder neuen Eingabe neu startet (Vorschau, Vollständigkeitsprüfung). | `store` |
| `@auditcore/ui-core` | `createDsfaController` | Funktion | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `createExtractionController` | Funktion | – | `extraction/controller` |
| `@auditcore/ui-core` | `createExtractionRestPort` | Funktion | Port auf den REST-Vertrag `documents_extraction/1` von `auditcore_documents.web` (Starlette oder FastAPI). | `extraction/rest-port` |
| `@auditcore/ui-core` | `createExtrapolationController` | Funktion | – | `extrapolation/controller` |
| `@auditcore/ui-core` | `createExtrapolationRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_extrapolation.web` (Starlette oder FastAPI). | `extrapolation/rest-port` |
| `@auditcore/ui-core` | `createFocusTrap` | Funktion | – | `focus` |
| `@auditcore/ui-core` | `createGeoController` | Funktion | – | `geo/controller` |
| `@auditcore/ui-core` | `createGeoRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_geo.web` (Starlette oder FastAPI). | `geo/rest-port` |
| `@auditcore/ui-core` | `createIdentifierController` | Funktion | – | `identifiers/controller` |
| `@auditcore/ui-core` | `createIdentifiersRestPort` | Funktion | Port auf den REST-Vertrag `identifiers_ui/1` von `auditcore_identifiers.web` (Starlette oder FastAPI). | `identifiers/rest-port` |
| `@auditcore/ui-core` | `createLeafletView` | Funktion | Legt die Leaflet-Karte im Element an. | `geo/mapView` |
| `@auditcore/ui-core` | `createReportingController` | Funktion | – | `reporting/controller` |
| `@auditcore/ui-core` | `createReportingRestPort` | Funktion | Port auf den REST-Vertrag `reporting_ui/1` von `auditcore_reporting.web` (Starlette oder FastAPI). | `reporting/rest-port` |
| `@auditcore/ui-core` | `createRiskController` | Funktion | – | `risk/controller` |
| `@auditcore/ui-core` | `createRiskRestPort` | Funktion | REST-Umsetzung des Ports, z. B. `createRiskRestPort({ baseUrl: '/api/risk' })`. | `risk/port` |
| `@auditcore/ui-core` | `createRunner` | Funktion | Führt eine Portanfrage aus: setzt `busy`, fängt Fehler (über `toError`) und meldet sie an `onError`. Ohne Port geschieht nichts (`null`). | `store` |
| `@auditcore/ui-core` | `createSamplingController` | Funktion | – | `sampling/controller` |
| `@auditcore/ui-core` | `createSamplingRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_sampling.web` (Starlette oder FastAPI). | `sampling/rest-port` |
| `@auditcore/ui-core` | `createScreeningController` | Funktion | – | `screening/controller` |
| `@auditcore/ui-core` | `createScreeningRestPort` | Funktion | Port auf den REST-Vertrag `screening_review/1` von `auditcore_registry_sources.web`. | `screening/rest-port` |
| `@auditcore/ui-core` | `createStore` | Funktion | – | `store` |
| `@auditcore/ui-core` | `createSynopsisController` | Funktion | – | `synopsis/controller` |
| `@auditcore/ui-core` | `createSynopsisRestClient` | Funktion | – | `synopsis/port` |
| `@auditcore/ui-core` | `createTableImportController` | Funktion | – | `tabular/tableImport` |
| `@auditcore/ui-core` | `createVvtController` | Funktion | – | `dataprotection/vvt` |
| `@auditcore/ui-core` | `currentVersion` | Funktion | Angezeigte Fassung: offener Entwurf vor Freigabe (dort wird gearbeitet). | `dataprotection/registerView` |
| `@auditcore/ui-core` | `dataprotectionError` | Funktion | – | `dataprotection/requests` |
| `@auditcore/ui-core` | `dataprotectionLabel` | Funktion | – | `dataprotection/requests` |
| `@auditcore/ui-core` | `dataprotectionMessages` | Konstante | Texte von `<flowaudit-vvt>` und `<flowaudit-dsfa>`. | `dataprotection/messages` |
| `@auditcore/ui-core` | `dataprotectionStatusLabel` | Funktion | Übersetzter Status (`entwurf`, `freigegeben`, …); unbekannte Werte bleiben stehen. | `dataprotection/requests` |
| `@auditcore/ui-core` | `dbKanbanMessages` | Konstante | Texte der Datenbankansicht als Kanban (`<flowaudit-db-kanban>`). | `dbkanban/messages` |
| `@auditcore/ui-core` | `dbKanbanView` | Funktion | – | `dbkanban/view` |
| `@auditcore/ui-core` | `decisionForm` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `decisionTitle` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `defaultProfile` | Funktion | Standardprofil des Servers (`default: true`), sonst das erste. | `documents/form` |
| `@auditcore/ui-core` | `defineMessages` | Funktion | Typisiert Kataloge einer Komponente; die Schlüssel ergeben sich aus dem deutschen Katalog. | `i18n` |
| `@auditcore/ui-core` | `deliverExport` | Funktion | Export ausliefern: Druckansicht (`print`) oder Datei. | `download` |
| `@auditcore/ui-core` | `derivationColumns` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `derivationRows` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `diffSegments` | Funktion | Segmente einer Seite. `ndiff` hat Vorrang; ohne sie wird nachgerechnet. Ist keine Wortdifferenz möglich, bleibt der Text unmarkiert (seitenweise) bzw. | `synopsis/wordDiff` |
| `@auditcore/ui-core` | `digitLabel` | Funktion | Anzeige einer Ziffer: zweite Ziffer 0–9, sonst Zahl. | `benford/model` |
| `@auditcore/ui-core` | `displayName` | Funktion | Bezeichnung für Listen: Name, sonst Kennung. | `geo/model` |
| `@auditcore/ui-core` | `displayValue` | Funktion | Anzeigewert eines Feldes; Wahrheitswerte und Leerwerte über die Texte der Komponente. | `dataprotection/registerView` |
| `@auditcore/ui-core` | `distribution` | Funktion | Verteilung je Regel in Profilreihenfolge (nur Datensatzregeln). | `risk/state` |
| `@auditcore/ui-core` | `downloadText` | Funktion | Text als Datei anbieten (Blob-URL); ohne Blob-Unterstützung geschieht nichts. | `download` |
| `@auditcore/ui-core` | `dsfaDerived` | Funktion | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `dsfaReadonly` | Funktion | Nur lesen: nicht bearbeitbar oder gesperrte (freigegebene) Fassung. | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `dsfaTabs` | Funktion | – | `dataprotection/dsfa` |
| `@auditcore/ui-core` | `editedBy` | Funktion | Vier-Augen-Prinzip vorab anzeigen: wer den Entwurf bearbeitet hat, kann ihn nicht freigeben. | `dataprotection/registerView` |
| `@auditcore/ui-core` | `emptyActivity` | Funktion | Tätigkeit ohne Kennung (die vergibt der Server beim Speichern). | `dataprotection/registerView` |
| `@auditcore/ui-core` | `emptyContent` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `emptyFilter` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `emptyScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `emptyStratum` | Funktion | – | `extrapolation/model` |
| `@auditcore/ui-core` | `emptyUnit` | Funktion | – | `extrapolation/model` |
| `@auditcore/ui-core` | `escapeHtml` | Funktion | – | `synopsis/exporters` |
| `@auditcore/ui-core` | `escapeMapHtml` | Funktion | Leaflet setzt Tooltips und Namensnennung als HTML; Daten gehen deshalb nur als Text hinein. | `geo/mapView` |
| `@auditcore/ui-core` | `escapeMarkdown` | Funktion | – | `synopsis/exporters` |
| `@auditcore/ui-core` | `evaluationRules` | Funktion | Regeln der Auswertung; ohne `rules` aus den Codes der Datensätze abgeleitet. | `risk/state` |
| `@auditcore/ui-core` | `excludedLines` | Funktion | Hinweise auf Elemente außerhalb der Auswahlbasis. | `sampling/view` |
| `@auditcore/ui-core` | `exportFilename` | Funktion | – | `synopsis/exporters` |
| `@auditcore/ui-core` | `extractionAccept` | Funktion | Dateiauswahl der Oberfläche (`accept`) aus den zulässigen Typen. | `extraction/view` |
| `@auditcore/ui-core` | `extractionConfidenceText` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionConfidenceTone` | Funktion | Ton einer Feldkonfidenz gegen den Schwellwert des Profils. | `extraction/view` |
| `@auditcore/ui-core` | `extractionDecisionText` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionDecisionTone` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionDocumentText` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionFieldLabel` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionFieldThreshold` | Funktion | Schwellwert der Feldkonfidenz des gelaufenen Profils (nur Donut). | `extraction/view` |
| `@auditcore/ui-core` | `extractionMessages` | Konstante | Texte der Belegerkennung (`<flowaudit-extraction>`). | `extraction/messages` |
| `@auditcore/ui-core` | `extractionOcrText` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionOutcomeTone` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionProfileText` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionProposalText` | Funktion | Donut-Vorschlag, wenn er nicht übernommen wurde (sonst leer). | `extraction/view` |
| `@auditcore/ui-core` | `extractionRuleLabel` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionSizeText` | Funktion | Dateigröße in MiB (bzw. KiB unter 1 MiB). | `extraction/view` |
| `@auditcore/ui-core` | `extractionStatusText` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionStatusTone` | Funktion | – | `extraction/view` |
| `@auditcore/ui-core` | `extractionValidation` | Funktion | Prüfung vor dem Senden (reine Funktion). | `extraction/controller` |
| `@auditcore/ui-core` | `extractionValidationText` | Funktion | Meldung zur Prüfung vor dem Senden. | `extraction/view` |
| `@auditcore/ui-core` | `extractionValueText` | Funktion | Wert eines Feldes als Text (Zahlen sprachabhängig, Listen mit Komma). | `extraction/view` |
| `@auditcore/ui-core` | `extrapolationAmount` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationCellLabel` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationConfidenceLabel` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationFormErrorKey` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationFormMessage` | Funktion | Sammelmeldung unter dem Formular: fehlende Auswahl oder markierte Felder. | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationInputNumber` | Funktion | Zahl als Eingabetext (ohne Tausendertrenner). | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationIssueKey` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationIssueText` | Funktion | Meldung eines Feldes (leer ohne Befund). | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationMessages` | Konstante | Texte der Hochrechnung (TER) und der Restfehlerquote (RER). | `extrapolation/messages` |
| `@auditcore/ui-core` | `extrapolationMethod` | Funktion | – | `extrapolation/controller` |
| `@auditcore/ui-core` | `extrapolationMethodById` | Funktion | – | `extrapolation/model` |
| `@auditcore/ui-core` | `extrapolationMethodGroups` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationRate` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationStepColumns` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `extrapolationStepRows` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `fieldIssues` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `fieldValue` | Funktion | Prüft ein Eingabefeld und liefert den Vertragswert (Prozent → Anteil). | `sampling/model` |
| `@auditcore/ui-core` | `filterOptions` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `filterRecords` | Funktion | – | `risk/state` |
| `@auditcore/ui-core` | `filterRows` | Funktion | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `filterSubjects` | Funktion | Subjects with only the hits passing the filter; subjects themselves stay visible. | `screening/view` |
| `@auditcore/ui-core` | `filterSummaries` | Funktion | Suche in Titel und Dateinamen, ohne Groß-/Kleinschreibung; neueste zuerst wie der Server. | `documents/list` |
| `@auditcore/ui-core` | `findHit` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `findIdentifierProfile` | Funktion | – | `identifiers/model` |
| `@auditcore/ui-core` | `flagState` | Funktion | – | `risk/state` |
| `@auditcore/ui-core` | `focusRow` | Funktion | Zeile fokussieren und sichtbar machen; Zeilen tragen `data-row-id` und `tabindex="-1"`. | `synopsis/navigation` |
| `@auditcore/ui-core` | `focusableWithin` | Funktion | – | `focus` |
| `@auditcore/ui-core` | `formProblems` | Funktion | Alle Befunde in Formularreihenfolge; leer heißt: absendbar. | `documents/form` |
| `@auditcore/ui-core` | `formatAge` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `formatAmount` | Funktion | – | `risk/format` |
| `@auditcore/ui-core` | `formatBytes` | Funktion | Größenangabe wie „20 MiB“ oder „512 KiB“. | `documents/form` |
| `@auditcore/ui-core` | `formatDateTime` | Funktion | Datum und Uhrzeit in der Sprache der Oberfläche; ungültige Angaben bleiben stehen. | `documents/list` |
| `@auditcore/ui-core` | `formatDegrees` | Funktion | Grad mit sechs Nachkommastellen (≈ 0,1 m). | `geo/model` |
| `@auditcore/ui-core` | `formatDistance` | Funktion | Entfernung sprachabhängig: unter 1 km in Metern, sonst in Kilometern mit zwei Stellen. | `geo/model` |
| `@auditcore/ui-core` | `formatMetres` | Funktion | Rechts-/Hochwert in Metern mit zwei Nachkommastellen, ohne Tausendertrennung. | `geo/model` |
| `@auditcore/ui-core` | `formatPoints` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `formatScore` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `formatScreeningDate` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `formatShare` | Funktion | – | `risk/format` |
| `@auditcore/ui-core` | `formatValue` | Funktion | – | `risk/format` |
| `@auditcore/ui-core` | `freshnessTone` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `geoMessages` | Konstante | Texte der Geo-Karte. | `geo/messages` |
| `@auditcore/ui-core` | `getDefaultLocale` | Funktion | – | `i18n` |
| `@auditcore/ui-core` | `groupByDepartment` | Funktion | Referate wie in der Quelle: konfigurierte zuerst, dann unbekannte; leere entfallen. | `dataprotection/registerView` |
| `@auditcore/ui-core` | `hasAcceptedExtension` | Funktion | – | `documents/form` |
| `@auditcore/ui-core` | `hasPartialStrata` | Funktion | Teilweise geschichtete Grundgesamtheit (der Server lehnt sie ab). | `sampling/model` |
| `@auditcore/ui-core` | `identifierBatchCsv` | Funktion | CSV (Excel-DE) der Stapelprüfung mit denselben Spalten wie die Tabelle (alle Zeilen). | `identifiers/model` |
| `@auditcore/ui-core` | `identifierBatchLines` | Funktion | – | `identifiers/model` |
| `@auditcore/ui-core` | `identifierBatchMapping` | Funktion | Zuordnung aus beiden Zuständen (Tabelle und Kennungsprüfung). | `identifiers/controller` |
| `@auditcore/ui-core` | `identifierBatchSummary` | Funktion | – | `identifiers/model` |
| `@auditcore/ui-core` | `identifierColumnFields` | Funktion | Spaltenauswahl der Stapelprüfung; die Spalte mit Kennungsart nur ohne feste Art. | `identifiers/model` |
| `@auditcore/ui-core` | `identifierErrorKey` | Funktion | – | `identifiers/model` |
| `@auditcore/ui-core` | `identifierFacts` | Funktion | Einzelheiten (`details`) mit deutschen Bezeichnungen aus dem Katalog. | `identifiers/model` |
| `@auditcore/ui-core` | `identifierMessages` | Konstante | Texte von „Kennung prüfen“. | `identifiers/messages` |
| `@auditcore/ui-core` | `identifierProfileKinds` | Funktion | Kennungsarten, die das gewählte Profil prüft (ohne Profil: keine). | `identifiers/model` |
| `@auditcore/ui-core` | `identifierProfileLabel` | Funktion | Anzeige eines Profils in der Auswahl: Empfehlung und Altverhalten sichtbar. | `identifiers/model` |
| `@auditcore/ui-core` | `identifierReasonText` | Funktion | Begründung eines Ergebnisses: Meldung der Bibliothek, bei „gültig“ der Satz zum Profil. | `identifiers/model` |
| `@auditcore/ui-core` | `identifierRowKind` | Funktion | – | `identifiers/model` |
| `@auditcore/ui-core` | `identifierRowReason` | Funktion | Begründung einer Stapelzeile; gültige Zeilen nur mit eigener Meldung der Bibliothek (Tabelle bleibt knapp). | `identifiers/model` |
| `@auditcore/ui-core` | `identifierRowStatus` | Funktion | Status einer Stapelzeile; `null` = nicht prüfbar. | `identifiers/model` |
| `@auditcore/ui-core` | `identifierRowValue` | Funktion | – | `identifiers/model` |
| `@auditcore/ui-core` | `identifierStatusText` | Funktion | – | `identifiers/model` |
| `@auditcore/ui-core` | `identifierStatusTone` | Funktion | – | `identifiers/model` |
| `@auditcore/ui-core` | `importDelimiterText` | Funktion | Anzeige des Trennzeichens („Tabulator“ für `\t`). | `tabular/tableImport` |
| `@auditcore/ui-core` | `importOptionalColumn` | Funktion | Optionale Spalte aus einem Auswahlwert (`''` = keine). | `tabular/tableImport` |
| `@auditcore/ui-core` | `importPreview` | Funktion | Vorschau der übernommenen Werte (reine Funktion). | `tabular/tableImport` |
| `@auditcore/ui-core` | `importRejectedLines` | Funktion | Die ersten zehn unlesbaren Zeilen als Liste. | `tabular/tableImport` |
| `@auditcore/ui-core` | `indicatorLabels` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `initialGroupBy` | Funktion | Vorgabe: gewünschte Eigenschaft, falls gruppierbar, sonst die erste Auswahl-Eigenschaft. | `dbkanban/controller` |
| `@auditcore/ui-core` | `initialTexts` | Funktion | Startwerte der Textfelder: vorgeschlagene Werte der Profile, sonst leer. | `sampling/model` |
| `@auditcore/ui-core` | `interpolate` | Funktion | Ersetzt {name}-Platzhalter; unbekannte Platzhalter bleiben sichtbar stehen. | `i18n` |
| `@auditcore/ui-core` | `involvesPdf` | Funktion | PDF-Dateien vergleicht der Server immer als Fließtext. | `documents/form` |
| `@auditcore/ui-core` | `isDeviation` | Funktion | Abweichung vom Vorschlag verlangt eine Begründung (Bibliothek prüft Mindestlänge). | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `isIconName` | Funktion | – | `base/icons` |
| `@auditcore/ui-core` | `isLocale` | Funktion | – | `i18n` |
| `@auditcore/ui-core` | `isPercent` | Funktion | Anteile werden in Prozent eingegeben und angezeigt. | `sampling/model` |
| `@auditcore/ui-core` | `isStratifiedPopulation` | Funktion | – | `sampling/controller` |
| `@auditcore/ui-core` | `issuesFor` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `itemsFromImport` | Funktion | Übernommene Dateispalten → Elemente der Grundgesamtheit (Kennung sonst laufende Nummer). | `sampling/model` |
| `@auditcore/ui-core` | `kanbanDialogMessages` | Konstante | Texte von Detailansicht, Einstellungen, Teilen und Boardliste. | `kanban/messages` |
| `@auditcore/ui-core` | `kanbanMessages` | Konstante | Texte der Kanban-Komponenten; Englisch vorbereitet. | `kanban/messages` |
| `@auditcore/ui-core` | `kindNeedsCountry` | Funktion | – | `identifiers/model` |
| `@auditcore/ui-core` | `kindProfiles` | Funktion | – | `screening/runForm` |
| `@auditcore/ui-core` | `kindSources` | Funktion | – | `screening/runForm` |
| `@auditcore/ui-core` | `lcsOperations` | Funktion | Längste gemeinsame Teilfolge über Wörter; `null` oberhalb von {@link WORD_LIMIT}. | `synopsis/wordDiff` |
| `@auditcore/ui-core` | `levelLabel` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `levelTone` | Funktion | Farbton der MAD-Stufe 0–3 (enge … keine Übereinstimmung). | `benford/model` |
| `@auditcore/ui-core` | `looksLikeResult` | Funktion | Kennzeichen eines `ComparisonResult.to_dict()`; Einzelheiten prüft `ComparisonResult.from_dict`. | `documents/importing` |
| `@auditcore/ui-core` | `mayRelease` | Funktion | Vier-Augen-Prinzip vorab anzeigen; maßgeblich bleibt die Prüfung des Servers. | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `methodGroups` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `methodStatusKey` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `methodTone` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `navigationDirection` | Funktion | Richtung für N/J (nächste) bzw. P/K (vorige Änderung); in Eingabefeldern und mit Modifikatoren `null`. | `synopsis/navigation` |
| `@auditcore/ui-core` | `ndiffOperations` | Funktion | ndiff-Zeilen in Operationen übersetzen; Hinweiszeilen (`? `) entfallen. | `synopsis/wordDiff` |
| `@auditcore/ui-core` | `needsShortValues` | Funktion | Zweistellige Tests (erste zwei Ziffern, zweite Ziffer) verlangen eine Regel für kurze Werte. | `benford/model` |
| `@auditcore/ui-core` | `nextOpenHit` | Funktion | The next hit still needing work after ``currentId`` (open, deferred or pending). | `screening/view` |
| `@auditcore/ui-core` | `pairs` | Funktion | Objekt als Liste `[Schlüssel, Wert]` in Einfügereihenfolge (für deklarative Tabellen). | `risk/state` |
| `@auditcore/ui-core` | `parameterLabel` | Funktion | – | `risk/format` |
| `@auditcore/ui-core` | `parameterUnit` | Funktion | Einheit hinter dem Eingabefeld (Prozent, Euro oder keine). | `sampling/view` |
| `@auditcore/ui-core` | `parseConditions` | Funktion | Auflagen: eine je Zeile, leere Zeilen entfallen. | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `parseCount` | Funktion | Eingabe eines Zahlfeldes: leer → null, sonst nichtnegative ganze Zahl; ungültig → undefined. | `dataprotection/registerView` |
| `@auditcore/ui-core` | `parseDegrees` | Funktion | Dezimalgrad aus Texteingabe; Komma und Punkt sind als Dezimaltrenner erlaubt, Tausendertrennzeichen nicht. Ungültiges ergibt `null`. | `geo/model` |
| `@auditcore/ui-core` | `parseImport` | Funktion | – | `documents/importing` |
| `@auditcore/ui-core` | `parseInput` | Funktion | Eingabetext (deutsch oder englisch notiert) → Zahl; leer → null, unlesbar → undefined. | `sampling/model` |
| `@auditcore/ui-core` | `parseLatLon` | Funktion | Punkt aus zwei Texteingaben mit Wertebereichsprüfung. | `geo/model` |
| `@auditcore/ui-core` | `parseMetres` | Funktion | Meter aus Texteingabe (Komma oder Punkt, keine Tausendertrennung); Ungültiges ergibt `null`. | `geo/model` |
| `@auditcore/ui-core` | `parseSubjects` | Funktion | One subject per line: ``Name; Geburtsdatum; Land; Bezug`` (only the name is required). | `screening/view` |
| `@auditcore/ui-core` | `parseUtm` | Funktion | UTM-Eingabe mit Wertebereichsprüfung: Zone 1–60, Ostwert 0–1 000 000 m, Nordwert 0–10 000 000 m. | `geo/model` |
| `@auditcore/ui-core` | `plainSegments` | Funktion | – | `synopsis/wordDiff` |
| `@auditcore/ui-core` | `populationSuggestions` | Funktion | Vorschlagswerte aus der Grundgesamtheit (Summe positiver Werte bzw. Anzahl). | `sampling/model` |
| `@auditcore/ui-core` | `populationText` | Funktion | Zusammenfassung der Grundgesamtheit; leer, wenn keine Elemente vorliegen. | `sampling/view` |
| `@auditcore/ui-core` | `positionText` | Funktion | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `positiveSum` | Funktion | Summe der positiven Werte (Auswahlbasis der Variante „portal“). | `sampling/model` |
| `@auditcore/ui-core` | `printHtml` | Funktion | Druckansicht in einem unsichtbaren Rahmen öffnen („Als PDF speichern“ im Druckdialog). Kein Pop-up, daher auch mit Pop-up-Blocker nutzbar. | `download` |
| `@auditcore/ui-core` | `profileHintText` | Funktion | Warnhinweis für nicht freigegebene Profile, sonst leer. | `risk/controller` |
| `@auditcore/ui-core` | `profileKeyOf` | Funktion | – | `screening/runForm` |
| `@auditcore/ui-core` | `profileStatusText` | Funktion | Sichtbarer Profilstatus („freigegeben“ …) oder der Rohwert. | `risk/controller` |
| `@auditcore/ui-core` | `readExtrapolationAmount` | Funktion | Zahl eines Textfelds oder der Befund; leere, nicht verlangte Felder ergeben 0. | `extrapolation/model` |
| `@auditcore/ui-core` | `recommendationTone` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `recordEntries` | Funktion | Treffer und unbestimmte Merkmale eines Datensatzes in Profilreihenfolge. | `risk/state` |
| `@auditcore/ui-core` | `recordLabel` | Funktion | – | `risk/state` |
| `@auditcore/ui-core` | `recordRules` | Funktion | – | `risk/state` |
| `@auditcore/ui-core` | `registerCsv` | Funktion | – | `dataprotection/exporters` |
| `@auditcore/ui-core` | `registerFilename` | Funktion | – | `dataprotection/exporters` |
| `@auditcore/ui-core` | `registerHtml` | Funktion | – | `dataprotection/exporters` |
| `@auditcore/ui-core` | `registerMarkdown` | Funktion | – | `dataprotection/exporters` |
| `@auditcore/ui-core` | `removeScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `replaceHit` | Funktion | Replace one hit (after a decision) without reloading the whole run. | `screening/view` |
| `@auditcore/ui-core` | `reportCellText` | Funktion | Zelle der Vorschau: Werte wie gesendet (Zahlen sprachabhängig), leer als „—“. | `reporting/view` |
| `@auditcore/ui-core` | `reportingErrorKey` | Funktion | – | `reporting/view` |
| `@auditcore/ui-core` | `reportingMessages` | Konstante | Texte des Tabellenexports (Berichtsexport nach Excel). | `reporting/messages` |
| `@auditcore/ui-core` | `reportingProfile` | Funktion | – | `reporting/controller` |
| `@auditcore/ui-core` | `reportingSampleNote` | Funktion | Hinweis, wenn die Vorschau nur einen Teil der Zeilen zeigt; sonst leer. | `reporting/view` |
| `@auditcore/ui-core` | `reportingSheetHeading` | Funktion | – | `reporting/view` |
| `@auditcore/ui-core` | `reportingTablesText` | Funktion | – | `reporting/view` |
| `@auditcore/ui-core` | `reportingWorkbookText` | Funktion | – | `reporting/view` |
| `@auditcore/ui-core` | `requirementKey` | Funktion | – | `risk/labels` |
| `@auditcore/ui-core` | `requiresFourEyes` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `residualColumns` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `residualFormFrom` | Funktion | RER-Formular aus einer Auswertung: A = Buchwert, D = Gesamtfehlerquote (in Prozent). | `extrapolation/model` |
| `@auditcore/ui-core` | `residualMetrics` | Funktion | Kennzahlen der Restfehlerquote (K, L, M). | `extrapolation/view` |
| `@auditcore/ui-core` | `residualRows` | Funktion | – | `extrapolation/view` |
| `@auditcore/ui-core` | `resolveIdentifierKind` | Funktion | Kennungsart aus einer Tabellenzelle: Kennung oder Bezeichnung des Katalogs, sonst unverändert (Server meldet sie). | `identifiers/model` |
| `@auditcore/ui-core` | `riskMessages` | Konstante | Sichtbare Texte der Risiko-Komponenten (Deutsch vollständig, Englisch vorbereitet). | `risk/messages` |
| `@auditcore/ui-core` | `riskTableColumns` | Funktion | – | `risk/controller` |
| `@auditcore/ui-core` | `riskTableRows` | Funktion | – | `risk/controller` |
| `@auditcore/ui-core` | `rowKeyOf` | Funktion | Schlüssel einer Zeile aus `rowKey`, sonst Position. | `table/index` |
| `@auditcore/ui-core` | `runFormDefaults` | Funktion | Vorbelegung bei Wechsel der Prüfart oder neuen Einstellungen: empfohlenes Profil, alle Listen, Standard-Mindestwert. | `screening/runForm` |
| `@auditcore/ui-core` | `sameSurvey` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `samplingFieldError` | Funktion | Fehlermeldung eines Eingabefelds, leer ohne Fehler. | `sampling/view` |
| `@auditcore/ui-core` | `samplingInputNumber` | Funktion | Zahlformat der Eingabefelder (ohne Tausendertrennung, bis 6 Nachkommastellen). | `sampling/view` |
| `@auditcore/ui-core` | `samplingMessages` | Konstante | Texte des Stichprobenrechners. | `sampling/messages` |
| `@auditcore/ui-core` | `samplingPopulation` | Funktion | – | `sampling/controller` |
| `@auditcore/ui-core` | `samplingProfile` | Funktion | – | `sampling/controller` |
| `@auditcore/ui-core` | `scorePercent` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `screeningMessages` | Konstante | Texte der Screening-Trefferprüfung (Sanktionslisten, PEP). | `screening/messages` |
| `@auditcore/ui-core` | `screeningTone` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `segmentsText` | Funktion | – | `synopsis/wordDiff` |
| `@auditcore/ui-core` | `selectGeo` | Funktion | – | `geo/controller` |
| `@auditcore/ui-core` | `selectRisk` | Funktion | – | `risk/controller` |
| `@auditcore/ui-core` | `selectScreening` | Funktion | – | `screening/controller` |
| `@auditcore/ui-core` | `selectSynopsis` | Funktion | – | `synopsis/controller` |
| `@auditcore/ui-core` | `selectedProfile` | Funktion | – | `screening/runForm` |
| `@auditcore/ui-core` | `selectionColumns` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `selectionErrorKey` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `selectionRows` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `selectionTexts` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `setDefaultLocale` | Funktion | Sprache ohne Provider (Web Components, React ohne `LocaleProvider`). | `i18n` |
| `@auditcore/ui-core` | `severityTone` | Funktion | – | `risk/format` |
| `@auditcore/ui-core` | `sizeTexts` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `sortIcon` | Funktion | – | `table/index` |
| `@auditcore/ui-core` | `splitExtractionFindings` | Funktion | Auffällige Befunde (nicht bestanden, prüfen) zuerst nach Gewicht; bestandene getrennt. | `extraction/view` |
| `@auditcore/ui-core` | `stateTone` | Funktion | – | `risk/format` |
| `@auditcore/ui-core` | `statusHintKey` | Funktion | Hinweis für nicht freigegebene Profile, sonst `null`. | `risk/labels` |
| `@auditcore/ui-core` | `statusKey` | Funktion | – | `risk/labels` |
| `@auditcore/ui-core` | `statusLabel` | Funktion | – | `synopsis/viewModel` |
| `@auditcore/ui-core` | `statusTone` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `stepChange` | Funktion | Nächste bzw. vorige Änderung; ohne aktuelle Position beginnt `+1` bei der ersten und `-1` bei der letzten. Am Rand bleibt die Position stehen. | `synopsis/viewModel` |
| `@auditcore/ui-core` | `strataColumns` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `strataOf` | Funktion | Schichten in Reihenfolge ihres ersten Auftretens; leer, wenn kein Element geschichtet ist. | `sampling/model` |
| `@auditcore/ui-core` | `strataRows` | Funktion | – | `sampling/view` |
| `@auditcore/ui-core` | `stratumRows` | Funktion | – | `extrapolation/model` |
| `@auditcore/ui-core` | `subscribeDefaultLocale` | Funktion | Meldet Änderungen der Standardsprache; liefert die Abmeldung. | `i18n` |
| `@auditcore/ui-core` | `summaryOf` | Funktion | Eintrag der Liste aus einem gespeicherten Vergleich (nach Anlegen oder Import). | `documents/list` |
| `@auditcore/ui-core` | `summaryView` | Funktion | – | `documents/list` |
| `@auditcore/ui-core` | `surveyFrom` | Funktion | Bearbeitbare Kopie der gespeicherten Erhebung. | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `synopsisBase` | Funktion | Ergebnisobjekt vor lokalen Änderungen: Prop `result`, sonst gespeicherter oder geladener Vergleich. | `synopsis/controller` |
| `@auditcore/ui-core` | `synopsisId` | Funktion | Kennung des angezeigten Vergleichs (für Speichern und Server-Exporte). | `synopsis/controller` |
| `@auditcore/ui-core` | `synopsisMessages` | Konstante | Sichtbare Texte der Synopse; Begriffe wie im audit_designer und in ecohesion. | `synopsis/messages` |
| `@auditcore/ui-core` | `synopsisPortOf` | Funktion | Der Port als Datenzugang der eingebetteten Synopse, wenn er Vergleiche laden kann. | `documents/controller` |
| `@auditcore/ui-core` | `tabularMessages` | Konstante | Texte des Datei-Imports (Stichprobe, Benford). | `tabular/messages` |
| `@auditcore/ui-core` | `terMetrics` | Funktion | Kennzahlen der Gesamtfehlerquote in fester Reihenfolge. | `extrapolation/view` |
| `@auditcore/ui-core` | `titleProperty` | Funktion | Titel-Eigenschaft: die erste Texteigenschaft (wie die erste Spalte der Tabellenansicht). | `dbkanban/view` |
| `@auditcore/ui-core` | `toCompareFields` | Funktion | Formularfelder für `POST /comparisons`; Gesetzessynopse ohne die Optionen des Standardvergleichs. | `documents/form` |
| `@auditcore/ui-core` | `toHtml` | Funktion | Eigenständiges HTML-Dokument mit Druck-CSS (keine externen Ressourcen). | `synopsis/exporters` |
| `@auditcore/ui-core` | `toMarkdown` | Funktion | Markdown: gestrichene Wörter als ~~…~~, neue als **…**. | `synopsis/exporters` |
| `@auditcore/ui-core` | `toggleMeasure` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `toggleSection` | Funktion | Abschnitt ein- oder ausschalten; Reihenfolge wie `ROW_STATUSES`. | `documents/form` |
| `@auditcore/ui-core` | `totals` | Funktion | – | `risk/state` |
| `@auditcore/ui-core` | `translate` | Funktion | Übersetzt mit Rückfall auf Deutsch und zuletzt auf den Schlüssel. | `i18n` |
| `@auditcore/ui-core` | `translator` | Funktion | Übersetzungsfunktion für eine feste Sprache. | `i18n` |
| `@auditcore/ui-core` | `triggeredDataset` | Funktion | – | `risk/state` |
| `@auditcore/ui-core` | `unitRows` | Funktion | – | `extrapolation/model` |
| `@auditcore/ui-core` | `utmErrorKey` | Funktion | Text der Fehlermeldung einer UTM-Eingabe. | `geo/model` |
| `@auditcore/ui-core` | `validateDecision` | Funktion | – | `screening/view` |
| `@auditcore/ui-core` | `vertexCount` | Funktion | Anzahl der Stützpunkte einer Fläche (Schlusspunkte mitgezählt). | `geo/model` |
| `@auditcore/ui-core` | `visibleIdentifierRows` | Funktion | Zeilen der Ergebnistabelle; wahlweise nur ungültige, fehlende und nicht prüfbare. | `identifiers/model` |
| `@auditcore/ui-core` | `vvtExportTexts` | Funktion | Beschriftungen der Exporte (Druckansicht, Markdown, CSV). | `dataprotection/vvt` |
| `@auditcore/ui-core` | `vvtFourEyes` | Funktion | Vier-Augen-Hinweis: die angemeldete Person hat den offenen Entwurf bearbeitet. | `dataprotection/vvt` |
| `@auditcore/ui-core` | `vvtVersionLabel` | Funktion | – | `dataprotection/vvt` |
| `@auditcore/ui-core` | `vvtView` | Funktion | – | `dataprotection/vvt` |
| `@auditcore/ui-core` | `whenMissingKey` | Funktion | – | `risk/labels` |
| `@auditcore/ui-core` | `wholeSegments` | Funktion | Ganze Texte als Streichung und Einfügung (neue/entfallene Stellen, Rückfall). | `synopsis/wordDiff` |
| `@auditcore/ui-core` | `withActivity` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `withAnswer` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `withDepartments` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `withField` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `withJustification` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `withPerson` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `withScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@auditcore/ui-core` | `withoutActivity` | Funktion | – | `dataprotection/registerView` |
| `@auditcore/ui-core` | `wrapTarget` | Funktion | Nächstes Fokusziel beim Tabben am Rand des Containers, sonst null (Browser übernimmt). | `focus` |
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

Aus `@auditcore/ui` 0.2.0 herausgelöst (Texte, Typen, View-Modelle, Exporte,
Ports und Stile unverändert; die Zustandsautomaten sind die bisherigen
Composables `useSynopsis`, `useVvt` und `useDsfa` ohne Vue-Reaktivität).
Die bisherigen Kerntests laufen hier unverändert; die gemeinsamen
Paritätsfälle unter `test/parity` prüfen die Vue- und die React-Fassung
gegen dieselben Erwartungen ([Parität Vue ↔ React](../../docs/ui/react-paritaet.md)).

## Abhängigkeiten

- `@auditcore/common` 0.1.0 (Laufzeit: REST-Client, Formatierung,
  CSV mit Formelschutz, `saveFile`)
- `@auditcore/kanban-core` 0.2.0 (Laufzeit, MIT, ohne weitere Abhängigkeiten:
  Gruppierung und `RecordPort` der Datenbankansicht als Kanban)
- `leaflet` ^1.9.4 (Laufzeit, BSD-2-Clause; Kartenansicht der Geo-Karte, erst
  beim Anzeigen einer Karte dynamisch geladen, Grundstile in `styles/geo.css`)

Node ≥ 20.19 für Bau und Tests.

## Sicherheit und Datenschutz

Keine eigene Datenhaltung und kein Browser-Speicher. Netzwerkzugriffe nur
über die Ports, die die Anwendung übergibt. Exporte (HTML, Markdown, CSV)
escapen alle Inhalte; CSV mit Formelschutz aus `@auditcore/common`. Die
Vier-Augen-Hinweise sind reine Anzeige, maßgeblich ist die Prüfung des Servers.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Neu entwickelt in auditcore, kein übernommener Fremdcode.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
