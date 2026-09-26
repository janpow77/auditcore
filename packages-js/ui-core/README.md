# @flowaudit/ui-core

## Zweck

Framework-freier Kern der FlowAudit-Oberflächen: Texte, Datentypen der REST-Verträge, View-Modelle, Zustandsautomaten, Ports, Exporte und Stile – gemeinsam für Vue und React.

`@flowaudit/ui` (Vue 3, Web Components) und `@flowaudit/ui-react` (natives
React 18) rendern dieselben Komponenten aus diesem Kern. Fachlogik steht nur
hier: Wortvergleich und Filter der Synopse, Vollständigkeit und Freigabe des
Verzeichnisses von Verarbeitungstätigkeiten, Vorschau und Entscheidung der
Datenschutz-Folgenabschätzung, Zustand und Verteilung der Risiko-Merkmale,
Trefferprüfung beim Screening, Eingabeprüfung und Anfragen von Stichprobe und
Benford-Analyse samt Diagrammgeometrie, Formularprüfung, Liste und Import der
Dokumentvergleiche. Die Oberflächenpakete binden die
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
  mit `computed(() => selectSynopsis(…))`, `comparisonsView(…)`, `vvtView(…)`,
  `dsfaDerived(…)` oder `selectRisk(…)` ab.
- **React:** `@flowaudit/ui-react` liest denselben Zustand mit
  `useSyncExternalStore(controller.store.subscribe, controller.store.get)`.
- **Ohne Framework:** Controller erzeugen, `store.subscribe` abonnieren und
  bei jeder Änderung aus `store.get()` neu zeichnen.
- **Stile:** `import '@flowaudit/ui-core/style.css'` (Designtoken `--fa-*`,
  Basis, Tabelle, Synopse, Datenschutz, Geo, Risiko-Merkmale, Screening,
  Datei-Import, Stichprobe, Benford, Dokumentvergleiche); einzelne Dateien unter
  `@flowaudit/ui-core/styles/*.css`. `@flowaudit/ui/style.css` enthält sie bereits.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (686):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/ui-core` | `ACCEPTED_EXTENSIONS` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `ANSWER_VALUES` | Konstante | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `Activity` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ActivityGroup` | Schnittstelle | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `ActorView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `AllocationMethod` | Typ | – | `sampling/types` |
| `@flowaudit/ui-core` | `AllocationRequest` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `AllocationResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `AnalyseError` | Typ | – | `benford/model` |
| `@flowaudit/ui-core` | `AnalyseInput` | Schnittstelle | – | `benford/model` |
| `@flowaudit/ui-core` | `AnalyseRequest` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui-core` | `AnalyseValidation` | Typ | – | `benford/model` |
| `@flowaudit/ui-core` | `AnswerInput` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `AnswerValue` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ApiErrorBody` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `AreaGeometry` | Typ | GeoJSON-Fläche in Achsenfolge Länge, Breite (RFC 7946). | `geo/types` |
| `@flowaudit/ui-core` | `AssessmentExportFormat` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `AssessmentStatus` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `AssessmentSummary` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `AssessmentView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `BadgeTone` | Typ | – | `base/types` |
| `@flowaudit/ui-core` | `BenfordAnalysis` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui-core` | `BenfordBusy` | Typ | – | `benford/controller` |
| `@flowaudit/ui-core` | `BenfordCallbacks` | Schnittstelle | – | `benford/controller` |
| `@flowaudit/ui-core` | `BenfordCatalogue` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui-core` | `BenfordController` | Typ | – | `benford/controller` |
| `@flowaudit/ui-core` | `BenfordData` | Schnittstelle | Stand der Benford-Analyse; `error` ist die Meldung der letzten abgelehnten Anfrage. | `benford/controller` |
| `@flowaudit/ui-core` | `BenfordDistribution` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui-core` | `BenfordMessageKey` | Typ | – | `benford/messages` |
| `@flowaudit/ui-core` | `BenfordMetricTexts` | Schnittstelle | – | `benford/view` |
| `@flowaudit/ui-core` | `BenfordPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createBenfordRestPort`. | `benford/types` |
| `@flowaudit/ui-core` | `BenfordSource` | Schnittstelle | – | `benford/controller` |
| `@flowaudit/ui-core` | `BenfordTest` | Typ | Typen des REST-Vertrags `docs/ui/benford-rest.md` (auditcore_statistics.web). | `benford/types` |
| `@flowaudit/ui-core` | `BenfordTranslate` | Typ | – | `benford/view` |
| `@flowaudit/ui-core` | `BlockProgress` | Schnittstelle | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `BlockView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `Breakdown` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `BreakdownRow` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui-core` | `BreakdownStep` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `BreakdownTone` | Typ | – | `screening/view` |
| `@flowaudit/ui-core` | `ButtonSize` | Typ | – | `base/types` |
| `@flowaudit/ui-core` | `ButtonVariant` | Typ | – | `base/types` |
| `@flowaudit/ui-core` | `CHANGE_STATUSES` | Konstante | Vorgabe des Filters „Alle Änderungen“: alles außer unverändert. | `synopsis/types` |
| `@flowaudit/ui-core` | `COMPARISON_KINDS` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `COMPARISON_MODES` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `CONTRACT` | Konstante | – | `screening/types` |
| `@flowaudit/ui-core` | `Catalogs` | Schnittstelle | Kataloge je Sprache; Deutsch ist vollständig, Englisch darf (noch) lückenhaft sein. | `i18n` |
| `@flowaudit/ui-core` | `ChartBar` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui-core` | `ChartBox` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui-core` | `ChartGeometry` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui-core` | `ClientExportFormat` | Typ | – | `synopsis/types` |
| `@flowaudit/ui-core` | `ColumnCheck` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui-core` | `CompareFields` | Schnittstelle | – | `synopsis/port` |
| `@flowaudit/ui-core` | `CompareForm` | Schnittstelle | – | `documents/form` |
| `@flowaudit/ui-core` | `CompareRow` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `Comparison` | Schnittstelle | Ein gespeicherter Vergleich (`GET /comparisons/{id}`). | `synopsis/types` |
| `@flowaudit/ui-core` | `ComparisonKind` | Typ | – | `documents/form` |
| `@flowaudit/ui-core` | `ComparisonMetadata` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `ComparisonMode` | Typ | – | `documents/form` |
| `@flowaudit/ui-core` | `ComparisonProfile` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `ComparisonResult` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `ComparisonRow` | Schnittstelle | – | `screening/view` |
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
| `@flowaudit/ui-core` | `Conclusion` | Typ | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `ConfidenceLevel` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `Conformity` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui-core` | `ConformityProfile` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui-core` | `ConformityRow` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui-core` | `ConsolidatedParagraph` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui-core` | `CoordinateError` | Typ | – | `geo/model` |
| `@flowaudit/ui-core` | `DATAPROTECTION_CONTRACT` | Konstante | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `DEFAULT_BOX` | Konstante | – | `benford/chart` |
| `@flowaudit/ui-core` | `DEFAULT_FILTER` | Konstante | – | `risk/state` |
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
| `@flowaudit/ui-core` | `DatasetFinding` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui-core` | `DecisionForm` | Schnittstelle | Eingabefelder der Entscheidung, vorbelegt aus der Fassung bzw. dem Vorschlag. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `DecisionInput` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `DecisionRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `DecisionView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `DegenerateRing` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `DerivationStep` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `DiffField` | Typ | – | `synopsis/types` |
| `@flowaudit/ui-core` | `DiffSegment` | Schnittstelle | – | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `DiffSide` | Typ | – | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `DistributionRow` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui-core` | `DossierFieldView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `DsfaController` | Typ | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaControllerOptions` | Schnittstelle | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaData` | Schnittstelle | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaDerived` | Schnittstelle | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaHooks` | Schnittstelle | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaStep` | Typ | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `DsfaTab` | Typ | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `EMPTY_EVALUATION` | Konstante | – | `risk/controller` |
| `@flowaudit/ui-core` | `EMPTY_RESIDUAL` | Konstante | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `EarthModel` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `EntryView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `EvaluateRequest` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui-core` | `Evaluation` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui-core` | `EvaluationRequest` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `EvaluationResult` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `EvaluationValidation` | Typ | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `ExportFormat` | Typ | – | `sampling/types` |
| `@flowaudit/ui-core` | `ExportInput` | Schnittstelle | – | `synopsis/exporters` |
| `@flowaudit/ui-core` | `ExportPayload` | Schnittstelle | Ergebnis eines Exports in der Oberfläche (Ereignis `export`). | `synopsis/types` |
| `@flowaudit/ui-core` | `ExportTexts` | Schnittstelle | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `ExportedFile` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ExtrapolationBusy` | Typ | – | `extrapolation/controller` |
| `@flowaudit/ui-core` | `ExtrapolationCallbacks` | Schnittstelle | – | `extrapolation/controller` |
| `@flowaudit/ui-core` | `ExtrapolationCatalogue` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `ExtrapolationController` | Typ | – | `extrapolation/controller` |
| `@flowaudit/ui-core` | `ExtrapolationData` | Schnittstelle | Stand der Hochrechnung; `error` ist die Meldung der letzten abgelehnten Anfrage. | `extrapolation/controller` |
| `@flowaudit/ui-core` | `ExtrapolationExportFormat` | Typ | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `ExtrapolationField` | Schnittstelle | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `ExtrapolationForm` | Schnittstelle | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `ExtrapolationFormError` | Typ | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `ExtrapolationIssue` | Typ | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `ExtrapolationIssues` | Typ | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `ExtrapolationMessageKey` | Typ | – | `extrapolation/messages` |
| `@flowaudit/ui-core` | `ExtrapolationMethod` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `ExtrapolationMethodGroup` | Schnittstelle | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `ExtrapolationMetric` | Schnittstelle | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `ExtrapolationPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createExtrapolationRestPort`. | `extrapolation/types` |
| `@flowaudit/ui-core` | `ExtrapolationSource` | Schnittstelle | – | `extrapolation/controller` |
| `@flowaudit/ui-core` | `ExtrapolationStep` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `ExtrapolationTranslate` | Typ | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `FLAG_STATES` | Konstante | – | `risk/state` |
| `@flowaudit/ui-core` | `FactorProfileInfo` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `FieldEntry` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui-core` | `FieldError` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui-core` | `FieldErrorCode` | Typ | – | `sampling/model` |
| `@flowaudit/ui-core` | `FieldKind` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `FieldUse` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui-core` | `FieldValue` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `FieldView` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `FilterOptions` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui-core` | `FindingView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `FlagEntry` | Schnittstelle | Ein Eintrag der Detailansicht: Treffer oder unbestimmtes Merkmal eines Datensatzes. | `risk/state` |
| `@flowaudit/ui-core` | `FlagHit` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui-core` | `FlagState` | Typ | Zustand einer Regel für einen Datensatz. | `risk/state` |
| `@flowaudit/ui-core` | `FocusTrap` | Schnittstelle | – | `focus` |
| `@flowaudit/ui-core` | `FormProblem` | Schnittstelle | Ein Befund der Formularprüfung: Textschlüssel und Platzhalter. | `documents/form` |
| `@flowaudit/ui-core` | `FreshnessStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui-core` | `FreshnessView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `GeoArea` | Schnittstelle | Fläche auf der Karte (z. B. Schutzgebiet); `notes` sind Hinweise zur Geometrie. | `geo/types` |
| `@flowaudit/ui-core` | `GeoBusy` | Typ | – | `geo/controller` |
| `@flowaudit/ui-core` | `GeoCatalogue` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `GeoController` | Typ | – | `geo/controller` |
| `@flowaudit/ui-core` | `GeoControllerOptions` | Schnittstelle | – | `geo/controller` |
| `@flowaudit/ui-core` | `GeoData` | Schnittstelle | – | `geo/controller` |
| `@flowaudit/ui-core` | `GeoField` | Typ | Einfache Eingabefelder, die die Oberfläche direkt setzen darf. | `geo/controller` |
| `@flowaudit/ui-core` | `GeoHint` | Typ | – | `geo/controller` |
| `@flowaudit/ui-core` | `GeoInputs` | Schnittstelle | Eingaben der Komponente (Props). | `geo/controller` |
| `@flowaudit/ui-core` | `GeoMapCallbacks` | Schnittstelle | – | `geo/controller` |
| `@flowaudit/ui-core` | `GeoMessageKey` | Typ | – | `geo/messages` |
| `@flowaudit/ui-core` | `GeoPackageArea` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `GeoPackageResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `GeoPoint` | Schnittstelle | Punkt auf der Karte (z. B. Vorhabenstandort); `id` ist die Kennung in Ergebnissen. | `geo/types` |
| `@flowaudit/ui-core` | `GeoPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createGeoRestPort`. | `geo/types` |
| `@flowaudit/ui-core` | `GeoRestOptions` | Schnittstelle | – | `geo/rest-port` |
| `@flowaudit/ui-core` | `GeoSelection` | Schnittstelle | – | `geo/controller` |
| `@flowaudit/ui-core` | `GeocodeHit` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `GeocodeResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `HitFilter` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui-core` | `HitView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `ICONS` | Konstante | Eigene Strichsymbole (24er-Raster, Strichstärke über CSS). Jede Zeile ist eine Liste von SVG-Pfaden; neue Symbole nur hier ergänzen. | `base/icons` |
| `@flowaudit/ui-core` | `IDLE` | Konstante | – | `store` |
| `@flowaudit/ui-core` | `INITIAL_BENFORD` | Konstante | – | `benford/controller` |
| `@flowaudit/ui-core` | `INITIAL_COMPARISONS` | Konstante | – | `documents/controller` |
| `@flowaudit/ui-core` | `INITIAL_EXTRAPOLATION` | Konstante | – | `extrapolation/controller` |
| `@flowaudit/ui-core` | `INITIAL_SAMPLING` | Konstante | – | `sampling/controller` |
| `@flowaudit/ui-core` | `IconName` | Typ | – | `base/icons` |
| `@flowaudit/ui-core` | `ImportParse` | Typ | – | `documents/importing` |
| `@flowaudit/ui-core` | `ImportRequest` | Schnittstelle | Anfrage von `POST /comparisons/import`: ein fertiges Ergebnis aus der Auftragssteuerung ablegen. | `synopsis/port` |
| `@flowaudit/ui-core` | `ImportedColumns` | Schnittstelle | Übernommene Spalten einer Datei. | `tabular/tableImport` |
| `@flowaudit/ui-core` | `JsonObject` | Typ | – | `risk/types` |
| `@flowaudit/ui-core` | `JsonValue` | Typ | Datentypen des REST-Vertrags `auditcore_risk.web` (docs/ui/risk-rest.md). Die Komponenten lesen nur diese Felder; unbekannte Felder werden ignoriert. | `risk/types` |
| `@flowaudit/ui-core` | `KeyTitle` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `LOCALES` | Konstante | – | `i18n` |
| `@flowaudit/ui-core` | `LatLon` | Schnittstelle | Typen des REST-Vertrags `docs/ui/geo-rest.md` (auditcore_geo.web). | `geo/types` |
| `@flowaudit/ui-core` | `LevelTone` | Typ | – | `benford/model` |
| `@flowaudit/ui-core` | `LevelView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ListInfo` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `Locale` | Typ | Framework-freier Kern der Sprachunterstützung: Kataloge, Platzhalter, Rückfall auf Deutsch. | `i18n` |
| `@flowaudit/ui-core` | `LocateRequest` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `LocateResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `LogEntry` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `LogView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `MAX_THRESHOLD` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `MAX_TITLE` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `MIN_THRESHOLD` | Konstante | – | `documents/form` |
| `@flowaudit/ui-core` | `MapLayers` | Schnittstelle | – | `geo/mapView` |
| `@flowaudit/ui-core` | `MapView` | Schnittstelle | – | `geo/mapView` |
| `@flowaudit/ui-core` | `MapViewOptions` | Schnittstelle | – | `geo/mapView` |
| `@flowaudit/ui-core` | `MatchState` | Typ | – | `screening/view` |
| `@flowaudit/ui-core` | `MeasureView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `MessageParams` | Typ | – | `i18n` |
| `@flowaudit/ui-core` | `MethodGroup` | Schnittstelle | – | `sampling/view` |
| `@flowaudit/ui-core` | `MethodKind` | Typ | – | `sampling/types` |
| `@flowaudit/ui-core` | `MethodProfile` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `MethodStatus` | Typ | – | `sampling/types` |
| `@flowaudit/ui-core` | `NO_DEPARTMENT` | Konstante | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `NamedOption` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `Outcome` | Typ | – | `screening/types` |
| `@flowaudit/ui-core` | `OverviewRow` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ParameterSpec` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `Person` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `PopulationItem` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `Position` | Typ | – | `geo/types` |
| `@flowaudit/ui-core` | `ProblemView` | Schnittstelle | – | `documents/view` |
| `@flowaudit/ui-core` | `ProfileDetail` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui-core` | `ProfileOption` | Schnittstelle | – | `documents/view` |
| `@flowaudit/ui-core` | `ProfileReference` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui-core` | `ProfileStatus` | Typ | – | `risk/types` |
| `@flowaudit/ui-core` | `ProfileSummary` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui-core` | `ProfileView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `Projection` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `Proposal` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `QuestionView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RESIDUAL_FIELDS` | Konstante | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `ROW_STATUSES` | Konstante | – | `synopsis/types` |
| `@flowaudit/ui-core` | `RadiusHit` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `RadiusRequest` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `RadiusResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `RecordView` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui-core` | `RegisterColumn` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RegisterContent` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RegisterExportFormat` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RegisterExportInput` | Schnittstelle | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `RegisterIssue` | Schnittstelle | Hinweis der Vollständigkeitsprüfung; `subject` = `<Tätigkeits-ID>:<Feld>` oder `deckblatt:<Teil>`. | `dataprotection/types` |
| `@flowaudit/ui-core` | `RegisterState` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RegisterStatus` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `RequestState` | Schnittstelle | Beschäftigt-Status, Fehler und Erfolgsmeldung einer Portanfrage (gemeinsam für alle Controller). | `store` |
| `@flowaudit/ui-core` | `ResidualErrorRate` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `ResidualForm` | Schnittstelle | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `ResidualRequest` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `ResidualResult` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `ResidualRow` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `ResidualValidation` | Typ | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `RestClientOptions` | Typ | Optionen wie bei `src/rest`: `baseUrl` (z. B. `/api/synopsis`), injizierbares `fetch`, Kopfzeilen. | `synopsis/port` |
| `@flowaudit/ui-core` | `ReviewEvents` | Schnittstelle | – | `screening/controller` |
| `@flowaudit/ui-core` | `ReviewStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui-core` | `ReviewView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `RiskController` | Typ | – | `risk/controller` |
| `@flowaudit/ui-core` | `RiskData` | Schnittstelle | – | `risk/controller` |
| `@flowaudit/ui-core` | `RiskDistributionRow` | Schnittstelle | – | `risk/state` |
| `@flowaudit/ui-core` | `RiskFilter` | Schnittstelle | – | `risk/state` |
| `@flowaudit/ui-core` | `RiskInputs` | Schnittstelle | Eingaben der Gesamtansicht (Props). | `risk/controller` |
| `@flowaudit/ui-core` | `RiskMessageKey` | Typ | – | `risk/messages` |
| `@flowaudit/ui-core` | `RiskPort` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui-core` | `RiskSelection` | Schnittstelle | Alles, was die Gesamtansicht aus Stand und Auswertung anzeigt (reine Funktion). | `risk/controller` |
| `@flowaudit/ui-core` | `RiskTranslate` | Typ | – | `risk/controller` |
| `@flowaudit/ui-core` | `RowStatus` | Typ | JSON-Formen des REST-Vertrags (docs/ui/synopsis-rest.md). Sie entsprechen `ComparisonResult.to_dict()` aus `auditcore_documents`; die Oberfläche kennt keine zweite Datenform. | `synopsis/types` |
| `@flowaudit/ui-core` | `RowUpdate` | Schnittstelle | Änderung einer Zeile (`PATCH /comparisons/{id}/rows`). | `synopsis/types` |
| `@flowaudit/ui-core` | `RowView` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `RuleView` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui-core` | `RunQuery` | Typ | – | `screening/types` |
| `@flowaudit/ui-core` | `RunRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `RunRequestRecord` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `RunSummary` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `RunView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `SCREENING_CONTRACT` | Konstante | – | `screening/types` |
| `@flowaudit/ui-core` | `SCREENING_KINDS` | Konstante | – | `screening/runForm` |
| `@flowaudit/ui-core` | `STATE_FILTER_KEYS` | Konstante | – | `risk/labels` |
| `@flowaudit/ui-core` | `STATE_ICONS` | Konstante | Symbol je Zustand: Farbe ist nie der einzige Träger der Bedeutung. | `risk/format` |
| `@flowaudit/ui-core` | `STATE_KEYS` | Konstante | – | `risk/labels` |
| `@flowaudit/ui-core` | `STRATUM_FIELDS` | Konstante | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `SamplingBusy` | Typ | – | `sampling/controller` |
| `@flowaudit/ui-core` | `SamplingCallbacks` | Schnittstelle | – | `sampling/controller` |
| `@flowaudit/ui-core` | `SamplingCatalogue` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `SamplingController` | Typ | – | `sampling/controller` |
| `@flowaudit/ui-core` | `SamplingData` | Schnittstelle | Stand des Stichprobenrechners; `error` ist die Meldung der letzten abgelehnten Anfrage. | `sampling/controller` |
| `@flowaudit/ui-core` | `SamplingMessageKey` | Typ | – | `sampling/messages` |
| `@flowaudit/ui-core` | `SamplingPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createSamplingRestPort`. | `sampling/types` |
| `@flowaudit/ui-core` | `SamplingSource` | Schnittstelle | – | `sampling/controller` |
| `@flowaudit/ui-core` | `SamplingTranslate` | Typ | – | `sampling/view` |
| `@flowaudit/ui-core` | `ScenarioInput` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ScenarioResult` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ScoreClass` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `ScreeningController` | Typ | – | `screening/controller` |
| `@flowaudit/ui-core` | `ScreeningData` | Schnittstelle | – | `screening/controller` |
| `@flowaudit/ui-core` | `ScreeningDecisionForm` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui-core` | `ScreeningError` | Schnittstelle | Fehler einer Portanfrage: Meldung des Servers bzw. `network_error` mit Status 0. | `screening/controller` |
| `@flowaudit/ui-core` | `ScreeningKey` | Typ | – | `screening/messages` |
| `@flowaudit/ui-core` | `ScreeningKind` | Typ | – | `screening/types` |
| `@flowaudit/ui-core` | `ScreeningPort` | Schnittstelle | Port der Screening-Trefferprüfung. Die Komponente ruft nie selbst `fetch` auf; `createScreeningRestPort` ist die mitgelieferte REST-Umsetzung. | `screening/types` |
| `@flowaudit/ui-core` | `ScreeningRunFormState` | Schnittstelle | – | `screening/runForm` |
| `@flowaudit/ui-core` | `ScreeningSelection` | Schnittstelle | – | `screening/controller` |
| `@flowaudit/ui-core` | `ScreeningTranslate` | Typ | – | `screening/messages` |
| `@flowaudit/ui-core` | `SecondReviewRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `SecondReviewView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `SegmentKind` | Typ | Wortdifferenz für die Anzeige, ohne Vue. Bevorzugt die vom Server gelieferte `difflib.ndiff`-Folge (`"  "` gleich, `"- "` entfallen, `"+ "` neu, `"? "` Hinweis); fehlt sie (Gesetze … | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `SelectionError` | Typ | – | `sampling/controller` |
| `@flowaudit/ui-core` | `SelectionInput` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui-core` | `SelectionRequest` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `SelectionResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `SelectionRow` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `SelectionTexts` | Schnittstelle | – | `sampling/view` |
| `@flowaudit/ui-core` | `SelectionValidation` | Typ | – | `sampling/model` |
| `@flowaudit/ui-core` | `SelectionVariant` | Typ | – | `sampling/types` |
| `@flowaudit/ui-core` | `ServerExportFormat` | Typ | – | `synopsis/types` |
| `@flowaudit/ui-core` | `ServerExportLink` | Schnittstelle | – | `synopsis/controller` |
| `@flowaudit/ui-core` | `SettingsView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `Severity` | Typ | – | `risk/types` |
| `@flowaudit/ui-core` | `ShortValues` | Typ | – | `benford/types` |
| `@flowaudit/ui-core` | `SimplifyRequest` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `SimplifyResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `SimplifyUnit` | Typ | – | `geo/types` |
| `@flowaudit/ui-core` | `SizeRequest` | Typ | – | `sampling/types` |
| `@flowaudit/ui-core` | `SizeResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `SizeValidation` | Typ | – | `sampling/model` |
| `@flowaudit/ui-core` | `SourceView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `SourcesView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `StateFilter` | Typ | Filter: `affected` = Treffer oder unbestimmt; `all` = jeder Datensatz. | `risk/state` |
| `@flowaudit/ui-core` | `Store` | Schnittstelle | Kleinster gemeinsamer Zustandsspeicher der Controller. | `store` |
| `@flowaudit/ui-core` | `StratumCount` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui-core` | `StratumInput` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `StratumProjection` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `StratumResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui-core` | `StratumRow` | Schnittstelle | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `SubjectInput` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `SubjectRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui-core` | `SubjectStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui-core` | `SubjectView` | Schnittstelle | – | `screening/types` |
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
| `@flowaudit/ui-core` | `TOLERANCE_STEPS` | Konstante | Stufen des Toleranzreglers der Vereinfachung (Meter bzw. Grad). | `geo/model` |
| `@flowaudit/ui-core` | `TabItem` | Schnittstelle | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `TableImportController` | Typ | – | `tabular/tableImport` |
| `@flowaudit/ui-core` | `TableImportData` | Schnittstelle | – | `tabular/tableImport` |
| `@flowaudit/ui-core` | `TabularMessageKey` | Typ | – | `tabular/messages` |
| `@flowaudit/ui-core` | `TileSource` | Schnittstelle | Kachelquelle der Anwendung; ohne Quelle zeigt die Karte keinen Hintergrund. | `geo/types` |
| `@flowaudit/ui-core` | `Tone` | Typ | Farbton wie `FaBadge` (`tone`). | `risk/format` |
| `@flowaudit/ui-core` | `TotalErrorRate` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `Totals` | Schnittstelle | – | `risk/state` |
| `@flowaudit/ui-core` | `Translate` | Typ | – | `i18n` |
| `@flowaudit/ui-core` | `UNIT_FIELDS` | Konstante | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `UNIT_FLAGS` | Konstante | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `UnitInput` | Schnittstelle | – | `extrapolation/types` |
| `@flowaudit/ui-core` | `UnitRow` | Schnittstelle | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `UploadFile` | Schnittstelle | Datei aus einem Eingabefeld (im Browser `File`). | `documents/form` |
| `@flowaudit/ui-core` | `UtmRequest` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `UtmResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui-core` | `VersionSummary` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `VersionView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui-core` | `ViewMessage` | Schnittstelle | Meldung als Katalogschlüssel mit Platzhaltern; die Komponente übersetzt sie. | `screening/view` |
| `@flowaudit/ui-core` | `ViewOptions` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `VvtController` | Typ | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtControllerOptions` | Schnittstelle | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtData` | Schnittstelle | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtExport` | Schnittstelle | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtExportFormat` | Typ | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtHooks` | Schnittstelle | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `VvtView` | Schnittstelle | Abgeleitete Werte eines Stands (reine Funktion, von beiden Oberflächen genutzt). | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `WORD_LIMIT` | Konstante | Oberhalb dieser Wortzahl je Seite wird nicht wortweise verglichen. | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `WhenMissingColumns` | Typ | – | `risk/types` |
| `@flowaudit/ui-core` | `acceptsHit` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `activityKey` | Funktion | Schlüssel einer Tätigkeit für die Zuordnung der Hinweise (Kennung, sonst Name wie in der Bibliothek). | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `addScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `analyseErrorKey` | Funktion | – | `benford/view` |
| `@flowaudit/ui-core` | `answerOf` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `applyRowOverrides` | Funktion | Zeilen mit lokalen Änderungen (Auswahl, Grund) zusammenführen. | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `areasFromGeoPackage` | Funktion | Flächen aus einer GeoPackage-Antwort; Kennungen erhalten die Herkunft als Präfix. | `geo/model` |
| `@flowaudit/ui-core` | `asComparisonsError` | Funktion | – | `documents/controller` |
| `@flowaudit/ui-core` | `asScreeningError` | Funktion | – | `screening/controller` |
| `@flowaudit/ui-core` | `awaitsSecondReview` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `axisMaximum` | Funktion | Obergrenze der y-Achse: nächstes Vielfaches des Tickabstands über dem Maximum. | `benford/chart` |
| `@flowaudit/ui-core` | `bandTone` | Funktion | Stufe eines Risikos nach Rang im Profil: höchste Stufe rot, zweithöchste gelb. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `baseMessages` | Konstante | Texte der Basiskomponenten. | `messages` |
| `@flowaudit/ui-core` | `benfordBarTitle` | Funktion | Titel eines Balkens (Tooltip und Vorlesetext). | `benford/view` |
| `@flowaudit/ui-core` | `benfordChartTitle` | Funktion | – | `benford/view` |
| `@flowaudit/ui-core` | `benfordDigitColumns` | Funktion | – | `benford/view` |
| `@flowaudit/ui-core` | `benfordDigitRows` | Funktion | – | `benford/view` |
| `@flowaudit/ui-core` | `benfordMessages` | Konstante | Texte der Benford-Analyse. | `benford/messages` |
| `@flowaudit/ui-core` | `benfordMetricTexts` | Funktion | – | `benford/view` |
| `@flowaudit/ui-core` | `benfordProfile` | Funktion | – | `benford/controller` |
| `@flowaudit/ui-core` | `benfordTickText` | Funktion | – | `benford/view` |
| `@flowaudit/ui-core` | `benfordValues` | Funktion | – | `benford/controller` |
| `@flowaudit/ui-core` | `benfordValuesText` | Funktion | – | `benford/view` |
| `@flowaudit/ui-core` | `blockProgress` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `breakdownRows` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `buildAnalyseRequest` | Funktion | Anfrage für `POST /analyze`; Test, Profil und ggf. Regel für kurze Werte sind Pflicht. | `benford/model` |
| `@flowaudit/ui-core` | `buildEvaluationRequest` | Funktion | Anfrage für `POST /evaluate`; bei Befunden die Feldschlüssel mit ihrem Fehler. | `extrapolation/model` |
| `@flowaudit/ui-core` | `buildResidualRequest` | Funktion | Anfrage für `POST /residual`; die Gesamtfehlerquote wird in Prozent eingegeben. | `extrapolation/model` |
| `@flowaudit/ui-core` | `buildRowView` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `buildRunRequest` | Funktion | Anfrage aus dem Formular; bei Fehlern `request: null` und die Meldungen als Katalogschlüssel. | `screening/runForm` |
| `@flowaudit/ui-core` | `buildSelectionRequest` | Funktion | Anfrage für `POST /selection`; ein leerer Seed überlässt dem Server die Erzeugung. | `sampling/model` |
| `@flowaudit/ui-core` | `buildSizeRequest` | Funktion | Anfrage für `POST /size`; jedes Feld ist Pflicht, nichts wird still ergänzt. | `sampling/model` |
| `@flowaudit/ui-core` | `buildSynopsisExport` | Funktion | Export der sichtbaren Zeilen (HTML, Markdown, Druckansicht). | `synopsis/controller` |
| `@flowaudit/ui-core` | `buildSynopsisView` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `buildVvtExport` | Funktion | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `canDecide` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `canReleaseAssessment` | Funktion | Freigabe möglich: Vier-Augen-Vorprüfung, keine ungespeicherten Eingaben, keine Sperrgründe. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `cellAlignClass` | Funktion | – | `table` |
| `@flowaudit/ui-core` | `cellText` | Funktion | – | `table` |
| `@flowaudit/ui-core` | `changeIds` | Funktion | Kennungen der Änderungszeilen in Anzeigereihenfolge (Ziel der Navigation). | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `chartGeometry` | Funktion | – | `benford/chart` |
| `@flowaudit/ui-core` | `cloneContent` | Funktion | Tiefe Kopie (JSON-Daten), damit Eingaben den gelesenen Stand nie verändern. | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `codeLabel` | Funktion | Beschriftung eines Codes aus dem Vertrag (Status, Stufe, Hinweis); unbekannte Codes bleiben stehen. | `screening/messages` |
| `@flowaudit/ui-core` | `comparisonRows` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `comparisonsMessages` | Konstante | Texte der Vergleichsverwaltung (`<flowaudit-comparisons>`): Hochladen, gespeicherte Vergleiche, Import und Löschen. Begriffe wie in der Synopse. | `documents/messages` |
| `@flowaudit/ui-core` | `comparisonsView` | Funktion | – | `documents/view` |
| `@flowaudit/ui-core` | `completeness` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `completenessTone` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `conclusionLabel` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `conclusionTone` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `confidenceChoices` | Funktion | Konfidenzniveaus, die die gewählte Methode mit Tabellenwerten erlaubt. | `extrapolation/model` |
| `@flowaudit/ui-core` | `confidenceText` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `coverIssues` | Funktion | Hinweise zum Deckblatt (Verantwortlicher, DSB). | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `createBenfordController` | Funktion | – | `benford/controller` |
| `@flowaudit/ui-core` | `createBenfordRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_statistics.web` (Starlette oder FastAPI). | `benford/rest-port` |
| `@flowaudit/ui-core` | `createComparisonsController` | Funktion | – | `documents/controller` |
| `@flowaudit/ui-core` | `createDataProtectionRestPort` | Funktion | Port auf den REST-Vertrag `dataprotection_ui/1` von `auditcore_dataprotection.web`. | `dataprotection/rest-port` |
| `@flowaudit/ui-core` | `createDelay` | Funktion | Verzögerter Aufruf, der bei jeder neuen Eingabe neu startet (Vorschau, Vollständigkeitsprüfung). | `store` |
| `@flowaudit/ui-core` | `createDsfaController` | Funktion | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `createExtrapolationController` | Funktion | – | `extrapolation/controller` |
| `@flowaudit/ui-core` | `createExtrapolationRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_extrapolation.web` (Starlette oder FastAPI). | `extrapolation/rest-port` |
| `@flowaudit/ui-core` | `createFocusTrap` | Funktion | – | `focus` |
| `@flowaudit/ui-core` | `createGeoController` | Funktion | – | `geo/controller` |
| `@flowaudit/ui-core` | `createGeoRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_geo.web` (Starlette oder FastAPI). | `geo/rest-port` |
| `@flowaudit/ui-core` | `createLeafletView` | Funktion | Legt die Leaflet-Karte im Element an. | `geo/mapView` |
| `@flowaudit/ui-core` | `createRiskController` | Funktion | – | `risk/controller` |
| `@flowaudit/ui-core` | `createRiskRestPort` | Funktion | REST-Umsetzung des Ports, z. B. `createRiskRestPort({ baseUrl: '/api/risk' })`. | `risk/port` |
| `@flowaudit/ui-core` | `createRunner` | Funktion | Führt eine Portanfrage aus: setzt `busy`, fängt Fehler (über `toError`) und meldet sie an `onError`. Ohne Port geschieht nichts (`null`). | `store` |
| `@flowaudit/ui-core` | `createSamplingController` | Funktion | – | `sampling/controller` |
| `@flowaudit/ui-core` | `createSamplingRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_sampling.web` (Starlette oder FastAPI). | `sampling/rest-port` |
| `@flowaudit/ui-core` | `createScreeningController` | Funktion | – | `screening/controller` |
| `@flowaudit/ui-core` | `createScreeningRestPort` | Funktion | Port auf den REST-Vertrag `screening_review/1` von `auditcore_registry_sources.web`. | `screening/rest-port` |
| `@flowaudit/ui-core` | `createStore` | Funktion | – | `store` |
| `@flowaudit/ui-core` | `createSynopsisController` | Funktion | – | `synopsis/controller` |
| `@flowaudit/ui-core` | `createSynopsisRestClient` | Funktion | – | `synopsis/port` |
| `@flowaudit/ui-core` | `createTableImportController` | Funktion | – | `tabular/tableImport` |
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
| `@flowaudit/ui-core` | `derivationColumns` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `derivationRows` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `diffSegments` | Funktion | Segmente einer Seite. `ndiff` hat Vorrang; ohne sie wird nachgerechnet. Ist keine Wortdifferenz möglich, bleibt der Text unmarkiert (seitenweise) bzw. | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `digitLabel` | Funktion | Anzeige einer Ziffer: zweite Ziffer 0–9, sonst Zahl. | `benford/model` |
| `@flowaudit/ui-core` | `displayName` | Funktion | Bezeichnung für Listen: Name, sonst Kennung. | `geo/model` |
| `@flowaudit/ui-core` | `displayValue` | Funktion | Anzeigewert eines Feldes; Wahrheitswerte und Leerwerte über die Texte der Komponente. | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `distribution` | Funktion | Verteilung je Regel in Profilreihenfolge (nur Datensatzregeln). | `risk/state` |
| `@flowaudit/ui-core` | `downloadText` | Funktion | Text als Datei anbieten (Blob-URL); ohne Blob-Unterstützung geschieht nichts. | `download` |
| `@flowaudit/ui-core` | `dsfaDerived` | Funktion | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `dsfaReadonly` | Funktion | Nur lesen: nicht bearbeitbar oder gesperrte (freigegebene) Fassung. | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `dsfaTabs` | Funktion | – | `dataprotection/dsfa` |
| `@flowaudit/ui-core` | `editedBy` | Funktion | Vier-Augen-Prinzip vorab anzeigen: wer den Entwurf bearbeitet hat, kann ihn nicht freigeben. | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `emptyActivity` | Funktion | Tätigkeit ohne Kennung (die vergibt der Server beim Speichern). | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `emptyContent` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `emptyFilter` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `emptyScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `emptyStratum` | Funktion | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `emptyUnit` | Funktion | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `escapeHtml` | Funktion | – | `synopsis/exporters` |
| `@flowaudit/ui-core` | `escapeMapHtml` | Funktion | Leaflet setzt Tooltips und Namensnennung als HTML; Daten gehen deshalb nur als Text hinein. | `geo/mapView` |
| `@flowaudit/ui-core` | `escapeMarkdown` | Funktion | – | `synopsis/exporters` |
| `@flowaudit/ui-core` | `evaluationRules` | Funktion | Regeln der Auswertung; ohne `rules` aus den Codes der Datensätze abgeleitet. | `risk/state` |
| `@flowaudit/ui-core` | `excludedLines` | Funktion | Hinweise auf Elemente außerhalb der Auswahlbasis. | `sampling/view` |
| `@flowaudit/ui-core` | `exportFilename` | Funktion | – | `synopsis/exporters` |
| `@flowaudit/ui-core` | `extrapolationAmount` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationCellLabel` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationConfidenceLabel` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationFormErrorKey` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationFormMessage` | Funktion | Sammelmeldung unter dem Formular: fehlende Auswahl oder markierte Felder. | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationInputNumber` | Funktion | Zahl als Eingabetext (ohne Tausendertrenner). | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationIssueKey` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationIssueText` | Funktion | Meldung eines Feldes (leer ohne Befund). | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationMessages` | Konstante | Texte der Hochrechnung (TER) und der Restfehlerquote (RER). | `extrapolation/messages` |
| `@flowaudit/ui-core` | `extrapolationMethod` | Funktion | – | `extrapolation/controller` |
| `@flowaudit/ui-core` | `extrapolationMethodById` | Funktion | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `extrapolationMethodGroups` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationRate` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationStepColumns` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `extrapolationStepRows` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `fieldIssues` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `fieldValue` | Funktion | Prüft ein Eingabefeld und liefert den Vertragswert (Prozent → Anteil). | `sampling/model` |
| `@flowaudit/ui-core` | `filterOptions` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `filterRecords` | Funktion | – | `risk/state` |
| `@flowaudit/ui-core` | `filterRows` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `filterSubjects` | Funktion | Subjects with only the hits passing the filter; subjects themselves stay visible. | `screening/view` |
| `@flowaudit/ui-core` | `filterSummaries` | Funktion | Suche in Titel und Dateinamen, ohne Groß-/Kleinschreibung; neueste zuerst wie der Server. | `documents/list` |
| `@flowaudit/ui-core` | `findHit` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `flagState` | Funktion | – | `risk/state` |
| `@flowaudit/ui-core` | `focusRow` | Funktion | Zeile fokussieren und sichtbar machen; Zeilen tragen `data-row-id` und `tabindex="-1"`. | `synopsis/navigation` |
| `@flowaudit/ui-core` | `focusableWithin` | Funktion | – | `focus` |
| `@flowaudit/ui-core` | `formProblems` | Funktion | Alle Befunde in Formularreihenfolge; leer heißt: absendbar. | `documents/form` |
| `@flowaudit/ui-core` | `formatAge` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `formatAmount` | Funktion | – | `risk/format` |
| `@flowaudit/ui-core` | `formatBytes` | Funktion | Größenangabe wie „20 MiB“ oder „512 KiB“. | `documents/form` |
| `@flowaudit/ui-core` | `formatDateTime` | Funktion | Datum und Uhrzeit in der Sprache der Oberfläche; ungültige Angaben bleiben stehen. | `documents/list` |
| `@flowaudit/ui-core` | `formatDegrees` | Funktion | Grad mit sechs Nachkommastellen (≈ 0,1 m). | `geo/model` |
| `@flowaudit/ui-core` | `formatDistance` | Funktion | Entfernung sprachabhängig: unter 1 km in Metern, sonst in Kilometern mit zwei Stellen. | `geo/model` |
| `@flowaudit/ui-core` | `formatMetres` | Funktion | Rechts-/Hochwert in Metern mit zwei Nachkommastellen, ohne Tausendertrennung. | `geo/model` |
| `@flowaudit/ui-core` | `formatPoints` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `formatScore` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `formatScreeningDate` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `formatShare` | Funktion | – | `risk/format` |
| `@flowaudit/ui-core` | `formatValue` | Funktion | – | `risk/format` |
| `@flowaudit/ui-core` | `freshnessTone` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `geoMessages` | Konstante | Texte der Geo-Karte. | `geo/messages` |
| `@flowaudit/ui-core` | `getDefaultLocale` | Funktion | – | `i18n` |
| `@flowaudit/ui-core` | `groupByDepartment` | Funktion | Referate wie in der Quelle: konfigurierte zuerst, dann unbekannte; leere entfallen. | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `hasAcceptedExtension` | Funktion | – | `documents/form` |
| `@flowaudit/ui-core` | `hasPartialStrata` | Funktion | Teilweise geschichtete Grundgesamtheit (der Server lehnt sie ab). | `sampling/model` |
| `@flowaudit/ui-core` | `importDelimiterText` | Funktion | Anzeige des Trennzeichens („Tabulator“ für `\t`). | `tabular/tableImport` |
| `@flowaudit/ui-core` | `importOptionalColumn` | Funktion | Optionale Spalte aus einem Auswahlwert (`''` = keine). | `tabular/tableImport` |
| `@flowaudit/ui-core` | `importPreview` | Funktion | Vorschau der übernommenen Werte (reine Funktion). | `tabular/tableImport` |
| `@flowaudit/ui-core` | `importRejectedLines` | Funktion | Die ersten zehn unlesbaren Zeilen als Liste. | `tabular/tableImport` |
| `@flowaudit/ui-core` | `indicatorLabels` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `initialTexts` | Funktion | Startwerte der Textfelder: vorgeschlagene Werte der Profile, sonst leer. | `sampling/model` |
| `@flowaudit/ui-core` | `interpolate` | Funktion | Ersetzt {name}-Platzhalter; unbekannte Platzhalter bleiben sichtbar stehen. | `i18n` |
| `@flowaudit/ui-core` | `involvesPdf` | Funktion | PDF-Dateien vergleicht der Server immer als Fließtext. | `documents/form` |
| `@flowaudit/ui-core` | `isDeviation` | Funktion | Abweichung vom Vorschlag verlangt eine Begründung (Bibliothek prüft Mindestlänge). | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `isIconName` | Funktion | – | `base/icons` |
| `@flowaudit/ui-core` | `isLocale` | Funktion | – | `i18n` |
| `@flowaudit/ui-core` | `isPercent` | Funktion | Anteile werden in Prozent eingegeben und angezeigt. | `sampling/model` |
| `@flowaudit/ui-core` | `isStratifiedPopulation` | Funktion | – | `sampling/controller` |
| `@flowaudit/ui-core` | `issuesFor` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `itemsFromImport` | Funktion | Übernommene Dateispalten → Elemente der Grundgesamtheit (Kennung sonst laufende Nummer). | `sampling/model` |
| `@flowaudit/ui-core` | `kindProfiles` | Funktion | – | `screening/runForm` |
| `@flowaudit/ui-core` | `kindSources` | Funktion | – | `screening/runForm` |
| `@flowaudit/ui-core` | `lcsOperations` | Funktion | Längste gemeinsame Teilfolge über Wörter; `null` oberhalb von {@link WORD_LIMIT}. | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `levelLabel` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `levelTone` | Funktion | Farbton der MAD-Stufe 0–3 (enge … keine Übereinstimmung). | `benford/model` |
| `@flowaudit/ui-core` | `looksLikeResult` | Funktion | Kennzeichen eines `ComparisonResult.to_dict()`; Einzelheiten prüft `ComparisonResult.from_dict`. | `documents/importing` |
| `@flowaudit/ui-core` | `mayRelease` | Funktion | Vier-Augen-Prinzip vorab anzeigen; maßgeblich bleibt die Prüfung des Servers. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `methodGroups` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `methodStatusKey` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `methodTone` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `navigationDirection` | Funktion | Richtung für N/J (nächste) bzw. P/K (vorige Änderung); in Eingabefeldern und mit Modifikatoren `null`. | `synopsis/navigation` |
| `@flowaudit/ui-core` | `ndiffOperations` | Funktion | ndiff-Zeilen in Operationen übersetzen; Hinweiszeilen (`? `) entfallen. | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `needsShortValues` | Funktion | Zweistellige Tests (erste zwei Ziffern, zweite Ziffer) verlangen eine Regel für kurze Werte. | `benford/model` |
| `@flowaudit/ui-core` | `nextOpenHit` | Funktion | The next hit still needing work after ``currentId`` (open, deferred or pending). | `screening/view` |
| `@flowaudit/ui-core` | `pairs` | Funktion | Objekt als Liste `[Schlüssel, Wert]` in Einfügereihenfolge (für deklarative Tabellen). | `risk/state` |
| `@flowaudit/ui-core` | `parameterLabel` | Funktion | – | `risk/format` |
| `@flowaudit/ui-core` | `parameterUnit` | Funktion | Einheit hinter dem Eingabefeld (Prozent, Euro oder keine). | `sampling/view` |
| `@flowaudit/ui-core` | `parseConditions` | Funktion | Auflagen: eine je Zeile, leere Zeilen entfallen. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `parseCount` | Funktion | Eingabe eines Zahlfeldes: leer → null, sonst nichtnegative ganze Zahl; ungültig → undefined. | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `parseDegrees` | Funktion | Dezimalgrad aus Texteingabe; Komma und Punkt sind als Dezimaltrenner erlaubt, Tausendertrennzeichen nicht. Ungültiges ergibt `null`. | `geo/model` |
| `@flowaudit/ui-core` | `parseImport` | Funktion | – | `documents/importing` |
| `@flowaudit/ui-core` | `parseInput` | Funktion | Eingabetext (deutsch oder englisch notiert) → Zahl; leer → null, unlesbar → undefined. | `sampling/model` |
| `@flowaudit/ui-core` | `parseLatLon` | Funktion | Punkt aus zwei Texteingaben mit Wertebereichsprüfung. | `geo/model` |
| `@flowaudit/ui-core` | `parseSubjects` | Funktion | One subject per line: ``Name; Geburtsdatum; Land; Bezug`` (only the name is required). | `screening/view` |
| `@flowaudit/ui-core` | `plainSegments` | Funktion | – | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `populationSuggestions` | Funktion | Vorschlagswerte aus der Grundgesamtheit (Summe positiver Werte bzw. Anzahl). | `sampling/model` |
| `@flowaudit/ui-core` | `populationText` | Funktion | Zusammenfassung der Grundgesamtheit; leer, wenn keine Elemente vorliegen. | `sampling/view` |
| `@flowaudit/ui-core` | `positionText` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `positiveSum` | Funktion | Summe der positiven Werte (Auswahlbasis der Variante „portal“). | `sampling/model` |
| `@flowaudit/ui-core` | `printHtml` | Funktion | Druckansicht in einem unsichtbaren Rahmen öffnen („Als PDF speichern“ im Druckdialog). Kein Pop-up, daher auch mit Pop-up-Blocker nutzbar. | `download` |
| `@flowaudit/ui-core` | `profileHintText` | Funktion | Warnhinweis für nicht freigegebene Profile, sonst leer. | `risk/controller` |
| `@flowaudit/ui-core` | `profileKeyOf` | Funktion | – | `screening/runForm` |
| `@flowaudit/ui-core` | `profileStatusText` | Funktion | Sichtbarer Profilstatus („freigegeben“ …) oder der Rohwert. | `risk/controller` |
| `@flowaudit/ui-core` | `readExtrapolationAmount` | Funktion | Zahl eines Textfelds oder der Befund; leere, nicht verlangte Felder ergeben 0. | `extrapolation/model` |
| `@flowaudit/ui-core` | `recommendationTone` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `recordEntries` | Funktion | Treffer und unbestimmte Merkmale eines Datensatzes in Profilreihenfolge. | `risk/state` |
| `@flowaudit/ui-core` | `recordLabel` | Funktion | – | `risk/state` |
| `@flowaudit/ui-core` | `recordRules` | Funktion | – | `risk/state` |
| `@flowaudit/ui-core` | `registerCsv` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `registerFilename` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `registerHtml` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `registerMarkdown` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui-core` | `removeScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `replaceHit` | Funktion | Replace one hit (after a decision) without reloading the whole run. | `screening/view` |
| `@flowaudit/ui-core` | `requirementKey` | Funktion | – | `risk/labels` |
| `@flowaudit/ui-core` | `requiresFourEyes` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `residualColumns` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `residualFormFrom` | Funktion | RER-Formular aus einer Auswertung: A = Buchwert, D = Gesamtfehlerquote (in Prozent). | `extrapolation/model` |
| `@flowaudit/ui-core` | `residualMetrics` | Funktion | Kennzahlen der Restfehlerquote (K, L, M). | `extrapolation/view` |
| `@flowaudit/ui-core` | `residualRows` | Funktion | – | `extrapolation/view` |
| `@flowaudit/ui-core` | `riskMessages` | Konstante | Sichtbare Texte der Risiko-Komponenten (Deutsch vollständig, Englisch vorbereitet). | `risk/messages` |
| `@flowaudit/ui-core` | `riskTableColumns` | Funktion | – | `risk/controller` |
| `@flowaudit/ui-core` | `riskTableRows` | Funktion | – | `risk/controller` |
| `@flowaudit/ui-core` | `rowKeyOf` | Funktion | Schlüssel einer Zeile aus `rowKey`, sonst Position. | `table` |
| `@flowaudit/ui-core` | `runFormDefaults` | Funktion | Vorbelegung bei Wechsel der Prüfart oder neuen Einstellungen: empfohlenes Profil, alle Listen, Standard-Mindestwert. | `screening/runForm` |
| `@flowaudit/ui-core` | `sameSurvey` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `samplingFieldError` | Funktion | Fehlermeldung eines Eingabefelds, leer ohne Fehler. | `sampling/view` |
| `@flowaudit/ui-core` | `samplingInputNumber` | Funktion | Zahlformat der Eingabefelder (ohne Tausendertrennung, bis 6 Nachkommastellen). | `sampling/view` |
| `@flowaudit/ui-core` | `samplingMessages` | Konstante | Texte des Stichprobenrechners. | `sampling/messages` |
| `@flowaudit/ui-core` | `samplingPopulation` | Funktion | – | `sampling/controller` |
| `@flowaudit/ui-core` | `samplingProfile` | Funktion | – | `sampling/controller` |
| `@flowaudit/ui-core` | `scorePercent` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `screeningMessages` | Konstante | Texte der Screening-Trefferprüfung (Sanktionslisten, PEP). | `screening/messages` |
| `@flowaudit/ui-core` | `screeningTone` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `segmentsText` | Funktion | – | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `selectGeo` | Funktion | – | `geo/controller` |
| `@flowaudit/ui-core` | `selectRisk` | Funktion | – | `risk/controller` |
| `@flowaudit/ui-core` | `selectScreening` | Funktion | – | `screening/controller` |
| `@flowaudit/ui-core` | `selectSynopsis` | Funktion | – | `synopsis/controller` |
| `@flowaudit/ui-core` | `selectedProfile` | Funktion | – | `screening/runForm` |
| `@flowaudit/ui-core` | `selectionColumns` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `selectionErrorKey` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `selectionRows` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `selectionTexts` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `setDefaultLocale` | Funktion | Sprache ohne Provider (Web Components, React ohne `LocaleProvider`). | `i18n` |
| `@flowaudit/ui-core` | `severityTone` | Funktion | – | `risk/format` |
| `@flowaudit/ui-core` | `sizeTexts` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `sortIcon` | Funktion | – | `table` |
| `@flowaudit/ui-core` | `stateTone` | Funktion | – | `risk/format` |
| `@flowaudit/ui-core` | `statusHintKey` | Funktion | Hinweis für nicht freigegebene Profile, sonst `null`. | `risk/labels` |
| `@flowaudit/ui-core` | `statusKey` | Funktion | – | `risk/labels` |
| `@flowaudit/ui-core` | `statusLabel` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `statusTone` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `stepChange` | Funktion | Nächste bzw. vorige Änderung; ohne aktuelle Position beginnt `+1` bei der ersten und `-1` bei der letzten. Am Rand bleibt die Position stehen. | `synopsis/viewModel` |
| `@flowaudit/ui-core` | `strataColumns` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `strataOf` | Funktion | Schichten in Reihenfolge ihres ersten Auftretens; leer, wenn kein Element geschichtet ist. | `sampling/model` |
| `@flowaudit/ui-core` | `strataRows` | Funktion | – | `sampling/view` |
| `@flowaudit/ui-core` | `stratumRows` | Funktion | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `subscribeDefaultLocale` | Funktion | Meldet Änderungen der Standardsprache; liefert die Abmeldung. | `i18n` |
| `@flowaudit/ui-core` | `summaryOf` | Funktion | Eintrag der Liste aus einem gespeicherten Vergleich (nach Anlegen oder Import). | `documents/list` |
| `@flowaudit/ui-core` | `summaryView` | Funktion | – | `documents/list` |
| `@flowaudit/ui-core` | `surveyFrom` | Funktion | Bearbeitbare Kopie der gespeicherten Erhebung. | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `synopsisBase` | Funktion | Ergebnisobjekt vor lokalen Änderungen: Prop `result`, sonst gespeicherter oder geladener Vergleich. | `synopsis/controller` |
| `@flowaudit/ui-core` | `synopsisId` | Funktion | Kennung des angezeigten Vergleichs (für Speichern und Server-Exporte). | `synopsis/controller` |
| `@flowaudit/ui-core` | `synopsisMessages` | Konstante | Sichtbare Texte der Synopse; Begriffe wie im audit_designer und in ecohesion. | `synopsis/messages` |
| `@flowaudit/ui-core` | `synopsisPortOf` | Funktion | Der Port als Datenzugang der eingebetteten Synopse, wenn er Vergleiche laden kann. | `documents/controller` |
| `@flowaudit/ui-core` | `tabularMessages` | Konstante | Texte des Datei-Imports (Stichprobe, Benford). | `tabular/messages` |
| `@flowaudit/ui-core` | `terMetrics` | Funktion | Kennzahlen der Gesamtfehlerquote in fester Reihenfolge. | `extrapolation/view` |
| `@flowaudit/ui-core` | `toCompareFields` | Funktion | Formularfelder für `POST /comparisons`; Gesetzessynopse ohne die Optionen des Standardvergleichs. | `documents/form` |
| `@flowaudit/ui-core` | `toHtml` | Funktion | Eigenständiges HTML-Dokument mit Druck-CSS (keine externen Ressourcen). | `synopsis/exporters` |
| `@flowaudit/ui-core` | `toMarkdown` | Funktion | Markdown: gestrichene Wörter als ~~…~~, neue als **…**. | `synopsis/exporters` |
| `@flowaudit/ui-core` | `toggleMeasure` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `toggleSection` | Funktion | Abschnitt ein- oder ausschalten; Reihenfolge wie `ROW_STATUSES`. | `documents/form` |
| `@flowaudit/ui-core` | `totals` | Funktion | – | `risk/state` |
| `@flowaudit/ui-core` | `translate` | Funktion | Übersetzt mit Rückfall auf Deutsch und zuletzt auf den Schlüssel. | `i18n` |
| `@flowaudit/ui-core` | `translator` | Funktion | Übersetzungsfunktion für eine feste Sprache. | `i18n` |
| `@flowaudit/ui-core` | `triggeredDataset` | Funktion | – | `risk/state` |
| `@flowaudit/ui-core` | `unitRows` | Funktion | – | `extrapolation/model` |
| `@flowaudit/ui-core` | `validateDecision` | Funktion | – | `screening/view` |
| `@flowaudit/ui-core` | `vertexCount` | Funktion | Anzahl der Stützpunkte einer Fläche (Schlusspunkte mitgezählt). | `geo/model` |
| `@flowaudit/ui-core` | `vvtExportTexts` | Funktion | Beschriftungen der Exporte (Druckansicht, Markdown, CSV). | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `vvtFourEyes` | Funktion | Vier-Augen-Hinweis: die angemeldete Person hat den offenen Entwurf bearbeitet. | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `vvtVersionLabel` | Funktion | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `vvtView` | Funktion | – | `dataprotection/vvt` |
| `@flowaudit/ui-core` | `whenMissingKey` | Funktion | – | `risk/labels` |
| `@flowaudit/ui-core` | `wholeSegments` | Funktion | Ganze Texte als Streichung und Einfügung (neue/entfallene Stellen, Rückfall). | `synopsis/wordDiff` |
| `@flowaudit/ui-core` | `withActivity` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `withAnswer` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `withDepartments` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `withField` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `withJustification` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `withPerson` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `withScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui-core` | `withoutActivity` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui-core` | `wrapTarget` | Funktion | Nächstes Fokusziel beim Tabben am Rand des Containers, sonst null (Browser übernimmt). | `focus` |
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
- `leaflet` ^1.9.4 (Laufzeit, BSD-2-Clause; Kartenansicht der Geo-Karte, erst
  beim Anzeigen einer Karte dynamisch geladen, Grundstile in `styles/geo.css`)

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
