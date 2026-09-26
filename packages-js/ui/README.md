# @flowaudit/ui

## Zweck

Gemeinsame Oberflächenkomponenten der FlowAudit-Anwendungen als Vue-3-Komponenten und Web Components, mit Designtoken, Hell-/Dunkelmodus und Sprachunterstützung.

Für die Frontends der FlowAudit-Anwendungen, die Vue oder kein Framework
nutzen. Jede Komponente gibt es als Vue-Komponente und als Web Component
`<flowaudit-…>`. React-Anwendungen nutzen die native React-Fassung
`@flowaudit/ui-react` (Tabelle, Synopse, VVT, DSFA); beide Fassungen teilen
Texte, Verträge, View-Modelle und Zustandsautomaten aus `@flowaudit/ui-core`.
Fachdaten kommen über Props oder Ports; das Paket speichert nichts selbst.

## Installation

Im auditcore-Repository ist das Paket Teil des npm-Workspace:

```sh
npm ci                           # im Repository-Stamm
npm run build -w @flowaudit/ui   # dist/: ESM, Typen, ui.css
npm run demo -w @flowaudit/ui    # Demo-Seite zur Sichtprüfung
```

Im Anwendungsrepository (Vue 3.5 als Peer-Abhängigkeit):

```sh
npm install @flowaudit/ui vue
```

Das Paket ist noch nicht in einer npm-Registry veröffentlicht; bis dahin
Bezug über den Workspace oder ein mit `npm pack -w @flowaudit/ui` erzeugtes
Tarball (zusammen mit `@flowaudit/ui-core`, `@flowaudit/kanban-core` und `@flowaudit/common`). Die Stile kommen immer aus
`@flowaudit/ui/style.css` (enthält die Stile aus `@flowaudit/ui-core`).

## Schnellstart

```ts
import { createApp, h } from 'vue'
import { createFlowauditUi, FaTable, formatNumber, type TableColumn } from '@flowaudit/ui'
import '@flowaudit/ui/style.css'

const columns: TableColumn[] = [
  { key: 'beleg', label: 'Beleg', sortable: true },
  { key: 'betrag', label: 'Betrag', align: 'end', format: (value) => formatNumber(Number(value), 'de') },
]
const rows = [
  { beleg: 'R-2026-001', betrag: 1250.5 },
  { beleg: 'R-2026-002', betrag: 980 },
]

const app = createApp({ render: () => h(FaTable, { columns, rows, caption: 'Belege', clickable: true }) })
app.use(createFlowauditUi({ locale: 'de' }))
app.mount('#app')
```

Ohne Vue in der Host-Anwendung (Web Components):

```ts
import { defineFlowauditElements } from '@flowaudit/ui/elements'
import '@flowaudit/ui/style.css'

defineFlowauditElements({ locale: 'de' })

const table = document.createElement('flowaudit-table') as HTMLElement & { columns: unknown; rows: unknown }
table.columns = [{ key: 'beleg', label: 'Beleg' }]
table.rows = [{ beleg: 'R-2026-001' }]
table.addEventListener('row-click', (event) => console.log((event as CustomEvent<unknown[]>).detail[0]))
document.body.append(table)
```

## Einbindung

- **Vue:** Plugin `createFlowauditUi({ locale })` stellt die Sprache app-weit
  bereit; Komponenten direkt importieren (`FaButton`, `FaDialog`, `FaTable`,
  `KanbanBoard` …). Composables für eigene Komponenten: `useI18n`,
  `useTheme`, `useFocusTrap`, `useId` sowie – auf Basis von
  `@flowaudit/common` – `useToast`, `useMediaQuery`, `useClickOutside`,
  `useSort`, `useDebouncedFn`, `useDebouncedRef`, `useThrottledFn` und
  `useAuthToken`. Sie melden ihre Abonnements beim Abbau der Komponente
  (Effekt-Scope) selbst ab.

  ```vue
  <FaTable :columns="columns" :rows="rows" clickable @row-click="open" />
  <KanbanBoard :port="port" board-id="b1" @board-change="save" />
  ```

- **Web Component:** `defineFlowauditElements({ only?, locale? })` aus
  `@flowaudit/ui/elements` registriert `<flowaudit-table>`,
  `<flowaudit-kanban-board>`, `<flowaudit-kanban-boards>`,
  `<flowaudit-sampling>`, `<flowaudit-benford>`,
  `<flowaudit-screening-review>`, `<flowaudit-risk-flags>` und
  `<flowaudit-geo-map>` im Light DOM
  (kein Shadow DOM, Designtoken der Seite gelten). Objekte und Listen werden
  als JS-Eigenschaften gesetzt, Ereignisse sind `CustomEvent`s in kebab-case
  mit den emit-Argumenten in `detail`. `vue` wird dabei als Abhängigkeit
  mitgeladen.
- **React:** Tabelle, Synopse, VVT und DSFA nativ in `@flowaudit/ui-react`
  (ohne Vue, gleiche Texte und Verträge, Paritätstests gegen diese Fassung).
  Die übrigen Komponenten stehen dort nur noch als veraltete Hüllen unter
  `@flowaudit/ui-react/elements` (brauchen Vue).

Fachkomponenten und ihre REST-Verträge:

| Komponente | Element | Zweck | Vertrag |
|---|---|---|---|
| `KanbanBoard`, `KanbanBoardList` | `<flowaudit-kanban-board>`, `<flowaudit-kanban-boards>` | Kanban-Boards über einen `BoardPort` | [`docs/kanban/oberflaeche.md`](../../docs/kanban/oberflaeche.md) |
| `SamplingPanel` | `<flowaudit-sampling>` | Stichprobenumfang und -ziehung über `auditcore_sampling.web` | [`docs/ui/sampling-rest.md`](../../docs/ui/sampling-rest.md) |
| `BenfordPanel` | `<flowaudit-benford>` | Benford-Analyse über `auditcore_statistics.web` | [`docs/ui/benford-rest.md`](../../docs/ui/benford-rest.md) |
| `ScreeningReview` | `<flowaudit-screening-review>` | Trefferprüfung beim Sanktions-/PEP-Screening | [`docs/ui/screening-rest.md`](../../docs/ui/screening-rest.md) |
| `FaVvt` | `<flowaudit-vvt>` | Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO) über `auditcore_dataprotection.web`: Pflichtangaben, Vollständigkeitsprüfung der Bibliothek, Entwurf, Vier-Augen-Freigabe, Versionen, Druckansicht/Markdown/CSV | [`docs/ui/dataprotection-rest.md`](../../docs/ui/dataprotection-rest.md) |
| `FaDsfa` | `<flowaudit-dsfa>` | Datenschutz-Folgenabschätzung (Art. 35 DSGVO): Schwellwertanalyse mit Muss-Liste, Risikoszenarien mit Berechnung der Bibliothek, Entscheidung, DSB, Freigabe, Bericht | [`docs/ui/dataprotection-rest.md`](../../docs/ui/dataprotection-rest.md) |
| `RiskFlags` | `<flowaudit-risk-flags>` | Risiko-Merkmale aus `auditcore_risk.web`: Verteilung, Filter, Zustand je Datensatz, Begründung; „unbestimmt“ und „übersprungen“ als eigene Zustände | [`docs/ui/risk-rest.md`](../../docs/ui/risk-rest.md) |
| `FaGeoMap` | `<flowaudit-geo-map>` | Karte (Leaflet, BSD-2-Clause) mit Punkten und Flächen, Umkreissuche mit Erdmodell, Punkt in Fläche mit Randregel, UTM, Douglas-Peucker, GeoPackage über `auditcore_geo.web`; Kacheln nur über die Eigenschaft `tiles`, Adresssuche nur auf ausdrücklichen Wunsch | [`docs/ui/geo-rest.md`](../../docs/ui/geo-rest.md) |

Kanban-Oberfläche mit Ports, Tastaturbedienung und Barrierefreiheit:
[`docs/kanban/oberflaeche.md`](../../docs/kanban/oberflaeche.md). Neue
Komponenten: [`docs/ui/beitragen.md`](../../docs/ui/beitragen.md).

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (560):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/ui` | `ANSWER_VALUES` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Activity` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ActivityGroup` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ActorView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `AgeKey` | Typ | – | `kanban/cardView` |
| `@flowaudit/ui` | `AllocationMethod` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `AllocationRequest` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `AllocationResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `AnalyseError` | Typ | – | `benford/model` |
| `@flowaudit/ui` | `AnalyseInput` | Schnittstelle | – | `benford/model` |
| `@flowaudit/ui` | `AnalyseRequest` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `AnalyseValidation` | Typ | – | `benford/model` |
| `@flowaudit/ui` | `AnswerInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AnswerValue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ApiErrorBody` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `AreaGeometry` | Typ | GeoJSON-Fläche in Achsenfolge Länge, Breite (RFC 7946). | `geo/types` |
| `@flowaudit/ui` | `AssessmentExportFormat` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AssessmentStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AssessmentSummary` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AssessmentView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BADGE_COLORS` | Konstante | Badge-Farben je Präfix (WorkspaceTaskCard: VP, SYS/SP, JKB, PRJ), sonst grau. | `kanban/cardView` |
| `@flowaudit/ui` | `BadgeTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordAnalysis` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `BenfordCallbacks` | Schnittstelle | – | `benford/useBenford` |
| `@flowaudit/ui` | `BenfordCatalogue` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `BenfordDistribution` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `BenfordPanel` | Vue-Komponente | – | `benford/BenfordPanel.vue` |
| `@flowaudit/ui` | `BenfordPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createBenfordRestPort`. | `benford/types` |
| `@flowaudit/ui` | `BenfordTest` | Typ | Typen des REST-Vertrags `docs/ui/benford-rest.md` (auditcore_statistics.web). | `benford/types` |
| `@flowaudit/ui` | `BlockProgress` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BlockView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Breakdown` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `BreakdownRow` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `BreakdownStep` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `ButtonSize` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ButtonVariant` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `CARD_COLORS` | Konstante | Kartenfarben zur Auswahl (TaskDetail colorPresets). | `kanban/cardView` |
| `@flowaudit/ui` | `CHANGE_STATUSES` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `COLUMN_COLORS` | Konstante | Spaltenfarben (BoardSettingsDialog PRESET_COLORS). | `kanban/cardView` |
| `@flowaudit/ui` | `CONTRACT` | Konstante | – | `screening/types` |
| `@flowaudit/ui` | `Catalogs` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `CellValue` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `ChartBar` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui` | `ChartBox` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui` | `ChartGeometry` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui` | `ClientExportFormat` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ColumnCheck` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui` | `ColumnView` | Schnittstelle | – | `kanban/useKanbanBoard` |
| `@flowaudit/ui` | `CompareFields` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `CompareRow` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Comparison` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonMetadata` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonRow` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `ComparisonSummary` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Completeness` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ConfidenceLevel` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `Conformity` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `ConformityProfile` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `ConformityRow` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `ConsolidatedParagraph` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `CoordinateError` | Typ | – | `geo/model` |
| `@flowaudit/ui` | `DATAPROTECTION_CONTRACT` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DEFAULT_BOX` | Konstante | – | `benford/chart` |
| `@flowaudit/ui` | `DEFAULT_FILTER` | Konstante | – | `risk/view/state` |
| `@flowaudit/ui` | `DEFAULT_LOCALE` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DEFAULT_SYNOPSIS_FILTER` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DataProtectionError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DataProtectionKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DataProtectionPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DataProtectionProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DataProtectionTranslate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DatasetFinding` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `DecimalSeparator` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `DecisionInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DecisionRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `DecisionView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `DegenerateRing` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `Delimiter` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `DerivationStep` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `DiffField` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DiffSegment` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DiffSide` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DistributionRow` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `DossierFieldView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DownloadFile` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `DsfaHooks` | Re-Export | – | `./useDsfa` |
| `@flowaudit/ui` | `DsfaState` | Schnittstelle | – | `dataprotection/useDsfa` |
| `@flowaudit/ui` | `DsfaStep` | Re-Export | – | `./useDsfa` |
| `@flowaudit/ui` | `EarthModel` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `ElementDefinition` | Schnittstelle | Eine Komponente, die als Web Component `flowaudit-<name>` bereitgestellt wird. | `elements/define` |
| `@flowaudit/ui` | `ElementTag` | Typ | – | `elements/define` |
| `@flowaudit/ui` | `EntryView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `EvaluateRequest` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui` | `Evaluation` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `ExportFormat` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `ExportInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExportPayload` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExportTexts` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExportedFile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FLAG_STATES` | Konstante | – | `risk/view/state` |
| `@flowaudit/ui` | `FaBadge` | Vue-Komponente | – | `base/FaBadge.vue` |
| `@flowaudit/ui` | `FaButton` | Vue-Komponente | – | `base/FaButton.vue` |
| `@flowaudit/ui` | `FaDialog` | Vue-Komponente | – | `base/FaDialog.vue` |
| `@flowaudit/ui` | `FaDsfa` | Vue-Komponente | – | `dataprotection/FaDsfa.vue` |
| `@flowaudit/ui` | `FaGeoMap` | Vue-Komponente | – | `geo/FaGeoMap.vue` |
| `@flowaudit/ui` | `FaIcon` | Vue-Komponente | – | `base/FaIcon.vue` |
| `@flowaudit/ui` | `FaSynopsis` | Vue-Komponente | – | `synopsis/FaSynopsis.vue` |
| `@flowaudit/ui` | `FaTable` | Vue-Komponente | – | `table/FaTable.vue` |
| `@flowaudit/ui` | `FaTextField` | Vue-Komponente | – | `base/FaTextField.vue` |
| `@flowaudit/ui` | `FaVvt` | Vue-Komponente | – | `dataprotection/FaVvt.vue` |
| `@flowaudit/ui` | `FetchLike` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `FieldEntry` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `FieldError` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui` | `FieldErrorCode` | Typ | – | `sampling/model` |
| `@flowaudit/ui` | `FieldKind` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FieldUse` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `FieldValue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FieldView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FilterOptions` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `FindingView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `FlagEntry` | Schnittstelle | Ein Eintrag der Detailansicht: Treffer oder unbestimmtes Merkmal eines Datensatzes. | `risk/view/state` |
| `@flowaudit/ui` | `FlagHit` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `FlagState` | Typ | Zustand einer Regel für einen Datensatz. | `risk/view/state` |
| `@flowaudit/ui` | `FlowauditUiOptions` | Schnittstelle | – | `plugin` |
| `@flowaudit/ui` | `FreshnessStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `FreshnessView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `GeoArea` | Schnittstelle | Fläche auf der Karte (z. B. Schutzgebiet); `notes` sind Hinweise zur Geometrie. | `geo/types` |
| `@flowaudit/ui` | `GeoBusy` | Typ | – | `geo/useGeoAreas` |
| `@flowaudit/ui` | `GeoCatalogue` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `GeoHint` | Typ | – | `geo/useGeoAreas` |
| `@flowaudit/ui` | `GeoMapCallbacks` | Schnittstelle | – | `geo/useGeoMap` |
| `@flowaudit/ui` | `GeoPackageArea` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `GeoPackageResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `GeoPoint` | Schnittstelle | Punkt auf der Karte (z. B. Vorhabenstandort); `id` ist die Kennung in Ergebnissen. | `geo/types` |
| `@flowaudit/ui` | `GeoPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createGeoRestPort`. | `geo/types` |
| `@flowaudit/ui` | `GeoRestOptions` | Schnittstelle | – | `geo/rest-port` |
| `@flowaudit/ui` | `GeocodeHit` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `GeocodeResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `HitFilter` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `HitView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `ICONS` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `IconName` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ImportedColumns` | Schnittstelle | Übernommene Spalten einer Datei. | `tabular/useTableImport` |
| `@flowaudit/ui` | `JsonObject` | Typ | – | `risk/types` |
| `@flowaudit/ui` | `JsonValue` | Typ | Datentypen des REST-Vertrags `auditcore_risk.web` (docs/ui/risk-rest.md). Die Komponenten lesen nur diese Felder; unbekannte Felder werden ignoriert. | `risk/types` |
| `@flowaudit/ui` | `KanbanBoard` | Vue-Komponente | – | `kanban/KanbanBoard.vue` |
| `@flowaudit/ui` | `KanbanBoardList` | Vue-Komponente | – | `kanban/KanbanBoardList.vue` |
| `@flowaudit/ui` | `KanbanBoardOptions` | Schnittstelle | – | `kanban/useKanbanBoard` |
| `@flowaudit/ui` | `KanbanCard` | Vue-Komponente | – | `kanban/KanbanCard.vue` |
| `@flowaudit/ui` | `KanbanCardDetail` | Vue-Komponente | – | `kanban/KanbanCardDetail.vue` |
| `@flowaudit/ui` | `KanbanColumn` | Vue-Komponente | – | `kanban/KanbanColumn.vue` |
| `@flowaudit/ui` | `KanbanSettingsDialog` | Vue-Komponente | – | `kanban/KanbanSettingsDialog.vue` |
| `@flowaudit/ui` | `KanbanShareDialog` | Vue-Komponente | – | `kanban/KanbanShareDialog.vue` |
| `@flowaudit/ui` | `KeyTitle` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `LOCALES` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `LOCALE_KEY` | Konstante | – | `i18n/i18n` |
| `@flowaudit/ui` | `LatLon` | Schnittstelle | Typen des REST-Vertrags `docs/ui/geo-rest.md` (auditcore_geo.web). | `geo/types` |
| `@flowaudit/ui` | `LevelTone` | Typ | – | `benford/model` |
| `@flowaudit/ui` | `LevelView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ListInfo` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Locale` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `LocateRequest` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `LocateResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `LogEntry` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `LogView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `MeasureView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `MessageParams` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `MethodKind` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `MethodProfile` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `MethodStatus` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `MovePreview` | Schnittstelle | – | `kanban/movePreview` |
| `@flowaudit/ui` | `NamedOption` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `NextSortOptions` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `NumberColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `Outcome` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `OverviewRow` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `PRIORITY_TONES` | Konstante | – | `kanban/cardView` |
| `@flowaudit/ui` | `ParameterSpec` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `ParsedTable` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `Person` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `PopulationItem` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `Position` | Typ | – | `geo/types` |
| `@flowaudit/ui` | `ProfileDetail` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `ProfileReference` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `ProfileStatus` | Typ | – | `risk/types` |
| `@flowaudit/ui` | `ProfileSummary` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui` | `ProfileView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Proposal` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `QuestionView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ROW_STATUSES` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RadiusHit` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `RadiusRequest` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `RadiusResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `RecordView` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `RegisterColumn` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterContent` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterExportFormat` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterExportInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterIssue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterState` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RelativeKey` | Typ | – | `kanban/cardView` |
| `@flowaudit/ui` | `RestClientOptions` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RestError` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `RestOptions` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `ReviewEvents` | Schnittstelle | – | `screening/useScreeningReview` |
| `@flowaudit/ui` | `ReviewStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `ReviewView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `RiskDistributionRow` | Schnittstelle | – | `risk/view/state` |
| `@flowaudit/ui` | `RiskFilter` | Schnittstelle | – | `risk/view/state` |
| `@flowaudit/ui` | `RiskFlagCard` | Vue-Komponente | – | `risk/RiskFlagCard.vue` |
| `@flowaudit/ui` | `RiskFlagFilter` | Vue-Komponente | – | `risk/RiskFlagFilter.vue` |
| `@flowaudit/ui` | `RiskFlagState` | Vue-Komponente | – | `risk/RiskFlagState.vue` |
| `@flowaudit/ui` | `RiskFlagSummary` | Vue-Komponente | – | `risk/RiskFlagSummary.vue` |
| `@flowaudit/ui` | `RiskFlagTable` | Vue-Komponente | – | `risk/RiskFlagTable.vue` |
| `@flowaudit/ui` | `RiskFlags` | Vue-Komponente | – | `risk/RiskFlags.vue` |
| `@flowaudit/ui` | `RiskMessageKey` | Typ | – | `risk/messages` |
| `@flowaudit/ui` | `RiskPort` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui` | `RiskProfileInfo` | Vue-Komponente | – | `risk/RiskProfileInfo.vue` |
| `@flowaudit/ui` | `RiskRecordDetail` | Vue-Komponente | – | `risk/RiskRecordDetail.vue` |
| `@flowaudit/ui` | `RowStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RowUpdate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RowView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RuleView` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `RunQuery` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `RunRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `RunRequestRecord` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `RunSummary` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `RunView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Runner` | Schnittstelle | – | `rest/runner` |
| `@flowaudit/ui` | `SCREENING_CONTRACT` | Konstante | – | `screening/types` |
| `@flowaudit/ui` | `STATE_FILTER_KEYS` | Konstante | – | `risk/view/labels` |
| `@flowaudit/ui` | `STATE_ICONS` | Konstante | Symbol je Zustand: Farbe ist nie der einzige Träger der Bedeutung. | `risk/view/format` |
| `@flowaudit/ui` | `STATE_KEYS` | Konstante | – | `risk/view/labels` |
| `@flowaudit/ui` | `SamplingCallbacks` | Schnittstelle | – | `sampling/useSampling` |
| `@flowaudit/ui` | `SamplingCatalogue` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SamplingPanel` | Vue-Komponente | – | `sampling/SamplingPanel.vue` |
| `@flowaudit/ui` | `SamplingPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createSamplingRestPort`. | `sampling/types` |
| `@flowaudit/ui` | `ScenarioInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScenarioResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScoreClass` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `ScreeningError` | Schnittstelle | Fehler einer Portanfrage: Meldung des Servers bzw. `network_error` mit Status 0. | `screening/useScreeningReview` |
| `@flowaudit/ui` | `ScreeningKey` | Typ | – | `screening/messages` |
| `@flowaudit/ui` | `ScreeningKind` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `ScreeningPort` | Schnittstelle | Port der Screening-Trefferprüfung. Die Komponente ruft nie selbst `fetch` auf; `createScreeningRestPort` ist die mitgelieferte REST-Umsetzung. | `screening/types` |
| `@flowaudit/ui` | `ScreeningReview` | Vue-Komponente | – | `screening/ScreeningReview.vue` |
| `@flowaudit/ui` | `ScreeningReviewState` | Typ | – | `screening/useScreeningReview` |
| `@flowaudit/ui` | `ScreeningTranslate` | Typ | – | `screening/messages` |
| `@flowaudit/ui` | `SecondReviewRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SecondReviewView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SegmentKind` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SelectionError` | Typ | – | `sampling/useSampling` |
| `@flowaudit/ui` | `SelectionInput` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui` | `SelectionRequest` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SelectionResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SelectionRow` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SelectionValidation` | Typ | – | `sampling/model` |
| `@flowaudit/ui` | `SelectionVariant` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `ServerExportFormat` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SettingsView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Severity` | Typ | – | `risk/types` |
| `@flowaudit/ui` | `ShortValues` | Typ | – | `benford/types` |
| `@flowaudit/ui` | `SimplifyRequest` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `SimplifyResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `SimplifyUnit` | Typ | – | `geo/types` |
| `@flowaudit/ui` | `SizeRequest` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `SizeResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SizeValidation` | Typ | – | `sampling/model` |
| `@flowaudit/ui` | `SortDirection` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `SortState` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `SourceView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SourcesView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `StateFilter` | Typ | Filter: `affected` = Treffer oder unbestimmt; `all` = jeder Datensatz. | `risk/view/state` |
| `@flowaudit/ui` | `StratumCount` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui` | `StratumResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SubjectInput` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SubjectRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SubjectStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `SubjectView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SurveyInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SynopsisFilterState` | Re-Export | – | `./useSynopsis` |
| `@flowaudit/ui` | `SynopsisLayout` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SynopsisMessageKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SynopsisPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SynopsisRestClient` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SynopsisRowFilter` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SynopsisSource` | Schnittstelle | Eingaben der Komponente, als Getter übergeben (Props bleiben reaktiv). | `synopsis/useSynopsis` |
| `@flowaudit/ui` | `SynopsisTranslate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SynopsisView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `TOLERANCE_STEPS` | Konstante | Stufen des Toleranzreglers der Vereinfachung (Meter bzw. Grad). | `geo/model` |
| `@flowaudit/ui` | `TabItem` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `TableColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `TableImport` | Vue-Komponente | – | `tabular/TableImport.vue` |
| `@flowaudit/ui` | `TableRow` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `ThemeMode` | Typ | – | `theme/theme` |
| `@flowaudit/ui` | `TileSource` | Schnittstelle | Kachelquelle der Anwendung; ohne Quelle zeigt die Karte keinen Hintergrund. | `geo/types` |
| `@flowaudit/ui` | `Tone` | Typ | Farbton wie `FaBadge` (`tone`). | `risk/view/format` |
| `@flowaudit/ui` | `Totals` | Schnittstelle | – | `risk/view/state` |
| `@flowaudit/ui` | `Translate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `UseAuthToken` | Schnittstelle | – | `composables/useAuthToken` |
| `@flowaudit/ui` | `UseBenford` | Schnittstelle | – | `benford/useBenford` |
| `@flowaudit/ui` | `UseGeoAreas` | Schnittstelle | – | `geo/useGeoAreas` |
| `@flowaudit/ui` | `UseGeoMap` | Schnittstelle | – | `geo/useGeoMap` |
| `@flowaudit/ui` | `UseGeoReference` | Schnittstelle | – | `geo/useGeoReference` |
| `@flowaudit/ui` | `UseI18n` | Schnittstelle | – | `i18n/i18n` |
| `@flowaudit/ui` | `UseRiskFlags` | Schnittstelle | – | `risk/useRiskFlags` |
| `@flowaudit/ui` | `UseSampling` | Schnittstelle | – | `sampling/useSampling` |
| `@flowaudit/ui` | `UseSort` | Schnittstelle | – | `composables/useSort` |
| `@flowaudit/ui` | `UseSortOptions` | Schnittstelle | – | `composables/useSort` |
| `@flowaudit/ui` | `UseSynopsis` | Schnittstelle | – | `synopsis/useSynopsis` |
| `@flowaudit/ui` | `UseSynopsisExport` | Schnittstelle | – | `synopsis/useSynopsisExport` |
| `@flowaudit/ui` | `UseSynopsisNavigation` | Schnittstelle | – | `synopsis/useSynopsisNavigation` |
| `@flowaudit/ui` | `UseTableImport` | Schnittstelle | – | `tabular/useTableImport` |
| `@flowaudit/ui` | `UseTheme` | Schnittstelle | – | `theme/theme` |
| `@flowaudit/ui` | `UseToast` | Schnittstelle | – | `composables/useToast` |
| `@flowaudit/ui` | `UtmRequest` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `UtmResult` | Schnittstelle | – | `geo/types` |
| `@flowaudit/ui` | `VersionSummary` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `VersionView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ViewMessage` | Schnittstelle | Meldung als Katalogschlüssel mit Platzhaltern; die Komponente übersetzt sie. | `screening/view` |
| `@flowaudit/ui` | `ViewOptions` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `VvtExport` | Re-Export | – | `./useVvt` |
| `@flowaudit/ui` | `VvtExportFormat` | Re-Export | – | `./useVvt` |
| `@flowaudit/ui` | `VvtHooks` | Re-Export | – | `./useVvt` |
| `@flowaudit/ui` | `VvtState` | Schnittstelle | – | `dataprotection/useVvt` |
| `@flowaudit/ui` | `WORD_LIMIT` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `WhenMissingColumns` | Typ | – | `risk/types` |
| `@flowaudit/ui` | `acceptsHit` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `activityKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `addScenario` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `answerOf` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `applyPreview` | Funktion | Spaltenansicht mit der bewegten Karte an der Vorschauposition. | `kanban/movePreview` |
| `@flowaudit/ui` | `applyRowOverrides` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `applyTheme` | Funktion | Setzt das Farbschema am Element (Standard: Dokumentwurzel); 'system' folgt dem Betriebssystem. | `theme/theme` |
| `@flowaudit/ui` | `areasFromGeoPackage` | Funktion | Flächen aus einer GeoPackage-Antwort; Kennungen erhalten die Herkunft als Präfix. | `geo/model` |
| `@flowaudit/ui` | `ariaSort` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `axisMaximum` | Funktion | Obergrenze der y-Achse: nächstes Vielfaches des Tickabstands über dem Maximum. | `benford/chart` |
| `@flowaudit/ui` | `badgePrefix` | Funktion | – | `kanban/cardView` |
| `@flowaudit/ui` | `badgeStyle` | Funktion | – | `kanban/cardView` |
| `@flowaudit/ui` | `bandTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `baseMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordElement` | Konstante | `<flowaudit-benford>`: Eigenschaften `port` (BenfordPort), `values`, `locale`; Ereignisse `analysis-completed`, `error`. | `benford/element` |
| `@flowaudit/ui` | `benfordMessages` | Konstante | Texte der Benford-Analyse. | `benford/messages` |
| `@flowaudit/ui` | `blockProgress` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `breakdownRows` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `buildAnalyseRequest` | Funktion | Anfrage für `POST /analyze`; Test, Profil und ggf. Regel für kurze Werte sind Pflicht. | `benford/model` |
| `@flowaudit/ui` | `buildRowView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `buildSelectionRequest` | Funktion | Anfrage für `POST /selection`; ein leerer Seed überlässt dem Server die Erzeugung. | `sampling/model` |
| `@flowaudit/ui` | `buildSizeRequest` | Funktion | Anfrage für `POST /size`; jedes Feld ist Pflicht, nichts wird still ergänzt. | `sampling/model` |
| `@flowaudit/ui` | `buildSynopsisView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `cardAge` | Funktion | Alter einer Karte in Stufen wie WorkspaceTaskCard (neu, Stunden, Tage, Wochen, Monate). | `kanban/cardView` |
| `@flowaudit/ui` | `changeIds` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `chartGeometry` | Funktion | – | `benford/chart` |
| `@flowaudit/ui` | `cloneContent` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `codeLabel` | Funktion | Beschriftung eines Codes aus dem Vertrag (Status, Stufe, Hinweis); unbekannte Codes bleiben stehen. | `screening/messages` |
| `@flowaudit/ui` | `columnCells` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `compareValues` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `comparisonRows` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `completeness` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `completenessTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `coverIssues` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createBenfordRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_statistics.web` (Starlette oder FastAPI). | `benford/rest-port` |
| `@flowaudit/ui` | `createDataProtectionRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createFlowauditUi` | Funktion | Vue-Plugin: stellt die Sprache app-weit bereit. | `plugin` |
| `@flowaudit/ui` | `createGeoRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_geo.web` (Starlette oder FastAPI). | `geo/rest-port` |
| `@flowaudit/ui` | `createRiskRestPort` | Funktion | REST-Umsetzung des Ports, z. B. `createRiskRestPort({ baseUrl: '/api/risk' })`. | `risk/port` |
| `@flowaudit/ui` | `createRunner` | Funktion | Gemeinsamer Ablauf für Portanfragen: Beschäftigt-Status, Fehlermeldung, Rückruf. | `rest/runner` |
| `@flowaudit/ui` | `createSamplingRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_sampling.web` (Starlette oder FastAPI). | `sampling/rest-port` |
| `@flowaudit/ui` | `createScreeningRestPort` | Funktion | Port auf den REST-Vertrag `screening_review/1` von `auditcore_registry_sources.web`. | `screening/rest-port` |
| `@flowaudit/ui` | `createSynopsisRestClient` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `currentVersion` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `dataprotectionError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `dataprotectionMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `decisionTitle` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `defineMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `detectDecimal` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `detectDelimiter` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `diffSegments` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `digitLabel` | Funktion | Anzeige einer Ziffer: zweite Ziffer 0–9, sonst Zahl. | `benford/model` |
| `@flowaudit/ui` | `displayName` | Funktion | Bezeichnung für Listen: Name, sonst Kennung. | `geo/model` |
| `@flowaudit/ui` | `displayValue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `distribution` | Funktion | Verteilung je Regel in Profilreihenfolge (nur Datensatzregeln). | `risk/view/state` |
| `@flowaudit/ui` | `downloadText` | Re-Export | – | `./useSynopsisExport` |
| `@flowaudit/ui` | `dsfaElement` | Konstante | `<flowaudit-dsfa>`: Eigenschaften `port`, `activityId`, `actor`, `editable`, `locale`; Ereignisse `assessment-change`, `error`. | `dataprotection/element` |
| `@flowaudit/ui` | `editedBy` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `emptyActivity` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `emptyContent` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `emptyFilter` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `emptyScenario` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `escapeHtml` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `escapeMarkdown` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `evaluationRules` | Funktion | Regeln der Auswertung; ohne `rules` aus den Codes der Datensätze abgeleitet. | `risk/view/state` |
| `@flowaudit/ui` | `exportFilename` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `fieldIssues` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `fieldValue` | Funktion | Prüft ein Eingabefeld und liefert den Vertragswert (Prozent → Anteil). | `sampling/model` |
| `@flowaudit/ui` | `filterOptions` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `filterRecords` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `filterRows` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `filterSubjects` | Funktion | Subjects with only the hits passing the filter; subjects themselves stay visible. | `screening/view` |
| `@flowaudit/ui` | `flagState` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `focusRow` | Re-Export | – | `./useSynopsisNavigation` |
| `@flowaudit/ui` | `focusableWithin` | Funktion | – | `composables/useFocusTrap` |
| `@flowaudit/ui` | `formatAmount` | Funktion | – | `risk/view/format` |
| `@flowaudit/ui` | `formatDate` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `formatDegrees` | Funktion | Grad mit sechs Nachkommastellen (≈ 0,1 m). | `geo/model` |
| `@flowaudit/ui` | `formatDistance` | Funktion | Entfernung sprachabhängig: unter 1 km in Metern, sonst in Kilometern mit zwei Stellen. | `geo/model` |
| `@flowaudit/ui` | `formatMetres` | Funktion | Rechts-/Hochwert in Metern mit zwei Nachkommastellen, ohne Tausendertrennung. | `geo/model` |
| `@flowaudit/ui` | `formatNumber` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `formatPercent` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `formatShare` | Funktion | – | `risk/view/format` |
| `@flowaudit/ui` | `formatValue` | Funktion | Wert eines Eingabefelds: leer ausdrücklich, Zahlen im Sprachformat. | `risk/view/format` |
| `@flowaudit/ui` | `geoMapElement` | Konstante | `<flowaudit-geo-map>`: Eigenschaften `port` (GeoPort), `points`, `areas`, `tiles` (TileSource), `center`, `zoom`, `locale`; Ereignisse `radius-completed`, `location-checked`, `area … | `geo/element` |
| `@flowaudit/ui` | `geoMessages` | Konstante | Texte der Geo-Karte. | `geo/messages` |
| `@flowaudit/ui` | `groupByDepartment` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `guessNumberColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `hasPartialStrata` | Funktion | Teilweise geschichtete Grundgesamtheit (der Server lehnt sie ab). | `sampling/model` |
| `@flowaudit/ui` | `initialTexts` | Funktion | Startwerte der Textfelder: vorgeschlagene Werte der Profile, sonst leer. | `sampling/model` |
| `@flowaudit/ui` | `initials` | Funktion | Initialen aus einem Namen: erster und letzter Namensteil. | `kanban/cardView` |
| `@flowaudit/ui` | `interpolate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `isDeviation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `isIconName` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `isLocale` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `isPercent` | Funktion | Anteile werden in Prozent eingegeben und angezeigt. | `sampling/model` |
| `@flowaudit/ui` | `issuesFor` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `itemsFromImport` | Funktion | Übernommene Dateispalten → Elemente der Grundgesamtheit (Kennung sonst laufende Nummer). | `sampling/model` |
| `@flowaudit/ui` | `kanbanBoardElement` | Konstante | `<flowaudit-kanban-board>`: Eigenschaften `port` (BoardPort) und `boardId` oder `board` (+ `userId`) für lokale Bearbeitung; Ereignisse `board-change`, `error`, `fullscreen`, `navi … | `kanban/element` |
| `@flowaudit/ui` | `kanbanBoardListElement` | Konstante | `<flowaudit-kanban-boards>`: Boardliste mit Eigenschaft `port`; Ereignisse `board-select`, `created`. | `kanban/element` |
| `@flowaudit/ui` | `kanbanDialogMessages` | Konstante | Texte von Detailansicht, Einstellungen, Teilen und Boardliste. | `kanban/messages` |
| `@flowaudit/ui` | `kanbanMessages` | Konstante | Texte der Kanban-Komponenten; Englisch vorbereitet. | `kanban/messages` |
| `@flowaudit/ui` | `lcsOperations` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `levelLabel` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `levelTone` | Funktion | Farbton der MAD-Stufe 0–3 (enge … keine Übereinstimmung). | `benford/model` |
| `@flowaudit/ui` | `localeTag` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `mayRelease` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ndiffOperations` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `needsShortValues` | Funktion | Zweistellige Tests (erste zwei Ziffern, zweite Ziffer) verlangen eine Regel für kurze Werte. | `benford/model` |
| `@flowaudit/ui` | `nextOpenHit` | Funktion | The next hit still needing work after ``currentId`` (open, deferred or pending). | `screening/view` |
| `@flowaudit/ui` | `nextSort` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `numberColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `pairs` | Funktion | Objekt als Liste `[Schlüssel, Wert]` in Einfügereihenfolge (für deklarative Tabellen). | `risk/view/state` |
| `@flowaudit/ui` | `parameterLabel` | Funktion | – | `risk/view/format` |
| `@flowaudit/ui` | `parseConditions` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseCount` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseDegrees` | Funktion | Dezimalgrad aus Texteingabe; Komma und Punkt sind als Dezimaltrenner erlaubt, Tausendertrennzeichen nicht. Ungültiges ergibt `null`. | `geo/model` |
| `@flowaudit/ui` | `parseInput` | Funktion | Eingabetext (deutsch oder englisch notiert) → Zahl; leer → null, unlesbar → undefined. | `sampling/model` |
| `@flowaudit/ui` | `parseLatLon` | Funktion | Punkt aus zwei Texteingaben mit Wertebereichsprüfung. | `geo/model` |
| `@flowaudit/ui` | `parseNumber` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `parseSubjects` | Funktion | One subject per line: ``Name; Geburtsdatum; Land; Bezug`` (only the name is required). | `screening/view` |
| `@flowaudit/ui` | `parseTable` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `placementFor` | Funktion | Platzierung für den Port aus der sichtbaren Nachbarschaft: vor der Karte an `index`, sonst hinter der letzten sichtbaren Karte, sonst ans Ende. | `kanban/movePreview` |
| `@flowaudit/ui` | `plainSegments` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `populationSuggestions` | Funktion | Vorschlagswerte aus der Grundgesamtheit (Summe positiver Werte bzw. Anzahl). | `sampling/model` |
| `@flowaudit/ui` | `positionText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `positiveSum` | Funktion | Summe der positiven Werte (Auswahlbasis der Variante „portal“). | `sampling/model` |
| `@flowaudit/ui` | `preview` | Funktion | – | `kanban/cardView` |
| `@flowaudit/ui` | `printHtml` | Re-Export | – | `./useSynopsisExport` |
| `@flowaudit/ui` | `provideLocale` | Funktion | Stellt die Sprache für alle Nachfahren bereit (App-Ebene oder Teilbaum). | `i18n/i18n` |
| `@flowaudit/ui` | `readTheme` | Funktion | Liest das explizit gesetzte Farbschema; ohne Attribut 'system'. | `theme/theme` |
| `@flowaudit/ui` | `recommendationTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `recordEntries` | Funktion | Treffer und unbestimmte Merkmale eines Datensatzes in Profilreihenfolge. | `risk/view/state` |
| `@flowaudit/ui` | `recordLabel` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `recordRules` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `registerCsv` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `registerFilename` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `registerHtml` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `registerMarkdown` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `relativeTime` | Funktion | Relative Zeit für die Boardliste (WorkspaceSidebar.relativeTime). | `kanban/cardView` |
| `@flowaudit/ui` | `removeScenario` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `requestFile` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `requestJson` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `requirementKey` | Funktion | – | `risk/view/labels` |
| `@flowaudit/ui` | `resolvedTheme` | Funktion | Tatsächlich wirksames Schema, auch wenn 'system' gewählt ist. | `theme/theme` |
| `@flowaudit/ui` | `riskFlagsElement` | Konstante | `<flowaudit-risk-flags>`: Eigenschaften `evaluation` (Antwort von `POST /evaluate`) und `profile` (Antwort von `GET /profiles/{id}/{version}`) als JS-Objekte; Ereignisse `record-se … | `risk/element` |
| `@flowaudit/ui` | `riskMessages` | Konstante | Sichtbare Texte der Risiko-Komponenten (Deutsch vollständig, Englisch vorbereitet). | `risk/messages` |
| `@flowaudit/ui` | `sameSurvey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `samplingElement` | Konstante | `<flowaudit-sampling>`: Eigenschaften `port` (SamplingPort), `items` (Grundgesamtheit), `locale`; Ereignisse `size-calculated`, `selection-drawn`, `error`. | `sampling/element` |
| `@flowaudit/ui` | `samplingMessages` | Konstante | Texte des Stichprobenrechners. | `sampling/messages` |
| `@flowaudit/ui` | `saveFile` | Re-Export | – | `./download` |
| `@flowaudit/ui` | `screeningMessages` | Konstante | Texte der Screening-Trefferprüfung (Sanktionslisten, PEP). | `screening/messages` |
| `@flowaudit/ui` | `screeningReviewElement` | Konstante | `<flowaudit-screening-review>`: Eigenschaften `port` (ScreeningPort), `runId`, `locale`; Ereignisse `run-created`, `decided`, `error`. | `screening/element` |
| `@flowaudit/ui` | `screeningTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `segmentsText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `setDefaultLocale` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `severityTone` | Funktion | – | `risk/view/format` |
| `@flowaudit/ui` | `sharedToastQueue` | Funktion | Anwendungsweite Warteschlange (einmal je Seite). | `composables/useToast` |
| `@flowaudit/ui` | `sortRows` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `splitLine` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `stateTone` | Funktion | – | `risk/view/format` |
| `@flowaudit/ui` | `statusHintKey` | Funktion | Hinweis für nicht freigegebene Profile, sonst `null`. | `risk/view/labels` |
| `@flowaudit/ui` | `statusKey` | Funktion | – | `risk/view/labels` |
| `@flowaudit/ui` | `statusLabel` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `statusTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `stepChange` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `strataOf` | Funktion | Schichten in Reihenfolge ihres ersten Auftretens; leer, wenn kein Element geschichtet ist. | `sampling/model` |
| `@flowaudit/ui` | `surveyFrom` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `synopsisElement` | Konstante | `<flowaudit-synopsis>`: `comparison`/`result` und `port` als JS-Eigenschaften; Ereignisse `row-update`, `export`, `navigate`, `update:layout`. | `synopsis/element` |
| `@flowaudit/ui` | `synopsisMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `tableElement` | Konstante | `<flowaudit-table>`: Spalten und Zeilen als JS-Eigenschaften, Ereignisse `row-click`, `sort-change`. | `table/element` |
| `@flowaudit/ui` | `tabularMessages` | Konstante | Texte des Datei-Imports (Stichprobe, Benford). | `tabular/messages` |
| `@flowaudit/ui` | `textOn` | Funktion | Lesbare Schriftfarbe auf einer Kartenfarbe (Luminanzschwelle wie im Original). | `kanban/cardView` |
| `@flowaudit/ui` | `toHtml` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `toMarkdown` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `toggleMeasure` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `totals` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `translate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `triggeredDataset` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `useAuthToken` | Funktion | Reaktiver Zugriff auf einen `TokenStore` aus `@flowaudit/common`. | `composables/useAuthToken` |
| `@flowaudit/ui` | `useBenford` | Funktion | Zustand und Ablauf der Benford-Analyse; Berechnung ausschließlich über den Port. | `benford/useBenford` |
| `@flowaudit/ui` | `useClickOutside` | Funktion | Ruft `handler` bei Klick außerhalb der Elemente (Template-Refs) und bei Escape; abgemeldet beim Aufräumen. | `composables/useDom` |
| `@flowaudit/ui` | `useDebouncedFn` | Funktion | Entprellte Funktion; ein ausstehender Aufruf wird beim Abbau der Komponente verworfen. | `composables/useDebounced` |
| `@flowaudit/ui` | `useDebouncedRef` | Funktion | Folgt `source` erst nach `ms` Ruhe (z. B. Suchfeld → Anfrage). | `composables/useDebounced` |
| `@flowaudit/ui` | `useDsfa` | Funktion | – | `dataprotection/useDsfa` |
| `@flowaudit/ui` | `useFocusTrap` | Funktion | Hält den Tastaturfokus im Container, solange `active` wahr ist, und gibt ihn danach an das zuvor fokussierte Element zurück. | `composables/useFocusTrap` |
| `@flowaudit/ui` | `useGeoAreas` | Funktion | Flächen (übergeben und aus GeoPackage geladen), Auswahl und Vereinfachung. | `geo/useGeoAreas` |
| `@flowaudit/ui` | `useGeoMap` | Funktion | Zustand und Abläufe der Geo-Karte; jede Berechnung läuft über den Port. | `geo/useGeoMap` |
| `@flowaudit/ui` | `useGeoReference` | Funktion | Bezugspunkt mit Texteingabe, UTM-Anzeige und (nur freigegeben) Adresssuche. | `geo/useGeoReference` |
| `@flowaudit/ui` | `useI18n` | Funktion | Composable für Komponenten. `override` (z. B. eine Prop `locale`) hat Vorrang vor der bereitgestellten Sprache. | `i18n/i18n` |
| `@flowaudit/ui` | `useId` | Funktion | Eindeutige, stabile ID je Komponenteninstanz für aria-Verknüpfungen. | `composables/useId` |
| `@flowaudit/ui` | `useKanbanActions` | Funktion | – | `kanban/useKanbanActions` |
| `@flowaudit/ui` | `useKanbanBoard` | Funktion | – | `kanban/useKanbanBoard` |
| `@flowaudit/ui` | `useKanbanFilter` | Funktion | Such- und Filterzustand des Boards (Toolbar) als CardFilter der Kernlogik. | `kanban/useKanbanFilter` |
| `@flowaudit/ui` | `useLocale` | Funktion | – | `i18n/i18n` |
| `@flowaudit/ui` | `useMediaQuery` | Funktion | Reaktiver Stand einer Media-Query, z. B. `useMediaQuery('(max-width: 768px)')`. | `composables/useDom` |
| `@flowaudit/ui` | `useMoveController` | Funktion | – | `kanban/useMoveController` |
| `@flowaudit/ui` | `useRiskFlags` | Funktion | Zustand und abgeleitete Daten der Gesamtansicht; ohne DOM testbar. | `risk/useRiskFlags` |
| `@flowaudit/ui` | `useRiskProfile` | Funktion | Profilbeschreibung zur Auswertung: die übergebene, sonst über den Port nachgeladen (Profil und Version der Auswertung, nie ein Standardprofil). | `risk/useRiskProfile` |
| `@flowaudit/ui` | `useSampling` | Funktion | Zustand und Abläufe des Stichprobenrechners. Die Fachlogik liegt im Port; hier werden nur Eingaben geprüft, Anfragen gebildet und Ergebnisse gehalten. | `sampling/useSampling` |
| `@flowaudit/ui` | `useScreeningReview` | Funktion | – | `screening/useScreeningReview` |
| `@flowaudit/ui` | `useSort` | Funktion | Sortierzustand und sortierte Zeilen für eigene Tabellen (FaTable sortiert selbst). | `composables/useSort` |
| `@flowaudit/ui` | `useStore` | Funktion | Stand eines Kern-Controllers (`@flowaudit/ui-core`) als reaktive Vue-Referenz. | `composables/useStore` |
| `@flowaudit/ui` | `useSynopsis` | Funktion | Vue-Anbindung des Zustandsautomaten aus `@flowaudit/ui-core` (Laden, Filter, Zeilenänderungen, Navigation). | `synopsis/useSynopsis` |
| `@flowaudit/ui` | `useSynopsisExport` | Funktion | Exporte der sichtbaren, ausgewählten Zeilen; `onExport` erhält jedes Ergebnis. | `synopsis/useSynopsisExport` |
| `@flowaudit/ui` | `useSynopsisNavigation` | Funktion | Navigation zwischen Änderungen mit Schaltflächen und Tasten N/J bzw. P/K. | `synopsis/useSynopsisNavigation` |
| `@flowaudit/ui` | `useTableImport` | Funktion | Datei lesen, Spalten zuordnen und eine Vorschau der übernommenen Werte bilden. | `tabular/useTableImport` |
| `@flowaudit/ui` | `useTheme` | Funktion | Composable: reaktives Farbschema, synchron mit dem Attribut am Element. | `theme/theme` |
| `@flowaudit/ui` | `useThrottledFn` | Funktion | Gedrosselte Funktion; ein ausstehender Aufruf wird beim Abbau der Komponente verworfen. | `composables/useDebounced` |
| `@flowaudit/ui` | `useToast` | Funktion | Toasts als reaktive Liste über der framework-freien Warteschlange aus `@flowaudit/common`. | `composables/useToast` |
| `@flowaudit/ui` | `useVvt` | Funktion | – | `dataprotection/useVvt` |
| `@flowaudit/ui` | `validateDecision` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `vertexCount` | Funktion | Anzahl der Stützpunkte einer Fläche (Schlusspunkte mitgezählt). | `geo/model` |
| `@flowaudit/ui` | `vvtElement` | Konstante | `<flowaudit-vvt>`: Eigenschaften `port` (DataProtectionPort), `actor`, `editable`, `locale`; Ereignisse `draft-saved`, `released`, `exported`, `error`. | `dataprotection/element` |
| `@flowaudit/ui` | `whenMissingKey` | Funktion | – | `risk/view/labels` |
| `@flowaudit/ui` | `wholeSegments` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `withActivity` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `withAnswer` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `withDepartments` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `withField` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `withJustification` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `withPerson` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `withScenario` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `withoutActivity` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui/elements` | `DefineOptions` | Schnittstelle | – | `elements` |
| `@flowaudit/ui/elements` | `ELEMENTS` | Konstante | Alle Web Components von | `registry` |
| `@flowaudit/ui/elements` | `ElementDefinition` | Schnittstelle | Eine Komponente, die als Web Component `flowaudit-<name>` bereitgestellt wird. | `elements/define` |
| `@flowaudit/ui/elements` | `ElementTag` | Typ | – | `elements/define` |
| `@flowaudit/ui/elements` | `defineElement` | Funktion | Registriert eine Komponente als Custom Element im Light DOM (kein Shadow DOM): Designtoken und `@flowaudit/ui/style.css` der Seite gelten direkt. | `elements/define` |
| `@flowaudit/ui/elements` | `defineElements` | Funktion | – | `elements/define` |
| `@flowaudit/ui/elements` | `defineFlowauditElements` | Funktion | – | `elements` |

Web Components:

| Element | Vue-Komponente | Definiert in |
|---|---|---|
| `<flowaudit-benford>` | `BenfordPanel` | `benford/element.ts` |
| `<flowaudit-dsfa>` | `FaDsfa` | `dataprotection/element.ts` |
| `<flowaudit-geo-map>` | `FaGeoMap` | `geo/element.ts` |
| `<flowaudit-kanban-board>` | `KanbanBoard` | `kanban/element.ts` |
| `<flowaudit-kanban-boards>` | `KanbanBoardList` | `kanban/element.ts` |
| `<flowaudit-risk-flags>` | `RiskFlags` | `risk/element.ts` |
| `<flowaudit-sampling>` | `SamplingPanel` | `sampling/element.ts` |
| `<flowaudit-screening-review>` | `ScreeningReview` | `screening/element.ts` |
| `<flowaudit-synopsis>` | `FaSynopsis` | `synopsis/element.ts` |
| `<flowaudit-table>` | `FaTable` | `table/element.ts` |
| `<flowaudit-vvt>` | `FaVvt` | `dataprotection/element.ts` |

### Props und Ereignisse der Vue-Komponenten

#### `BenfordPanel`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `BenfordPort \| null` | nein | `null` | Fachlogik, z. B. `createBenfordRestPort({ baseUrl: '/api/benford' })`. |
| `values` | `readonly (number \| null)[]` | nein | `() => []` | Zu prüfende Beträge; alternativ Datei-Import in der Komponente. |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `analysis-completed` | `[result: BenfordAnalysis]` | – |
| `error` | `[message: string]` | – |

#### `FaBadge`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `tone` | `BadgeTone` | nein | `'neutral'` | – |
| `label` | `string` | nein | `''` | – |

#### `FaButton`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `variant` | `ButtonVariant` | nein | `'secondary'` | – |
| `size` | `ButtonSize` | nein | `'md'` | – |
| `icon` | `IconName` | nein | `undefined` | – |
| `iconOnly` | `boolean` | nein | `false` | Nur Symbol: `label` wird dann zur zugänglichen Beschriftung und zum Tooltip. |
| `label` | `string` | nein | `''` | – |
| `type` | `'button' \| 'submit' \| 'reset'` | nein | `'button'` | – |
| `disabled` | `boolean` | nein | `false` | – |
| `loading` | `boolean` | nein | `false` | – |
| `pressed` | `boolean` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `click` | `[event: MouseEvent]` | – |

#### `FaDialog`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `open` | `boolean` | ja | – | – |
| `title` | `string` | ja | – | – |
| `description` | `string` | nein | `''` | – |
| `size` | `'sm' \| 'md' \| 'lg'` | nein | `'md'` | – |
| `placement` | `'center' \| 'side'` | nein | `'center'` | Seitliches Panel statt zentriertem Dialog. |
| `closeOnBackdrop` | `boolean` | nein | `true` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update:open` | `[open: boolean]` | – |
| `close` | `[]` | – |

#### `FaDsfa`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `DataProtectionPort \| null` | nein | `null` | Datenzugang (Vertrag dataprotection_ui/1), z. B. `createDataProtectionRestPort({ baseUrl: '/api/dataprotection' })`. |
| `activityId` | `string` | nein | `''` | Beim Laden zu öffnende Tätigkeit (Kennung aus dem Verzeichnis). |
| `actor` | `string` | nein | `''` | Kennung der angemeldeten Person; nur für den Vier-Augen-Hinweis, geprüft wird auf dem Server. |
| `editable` | `boolean` | nein | `true` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `assessment-change` | `[detail: { step: DsfaStep; id: string; version: number; status: string }]` | – |
| `error` | `[detail: DataProtectionError]` | – |

#### `FaGeoMap`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `GeoPort \| null` | nein | `null` | Fachlogik, z. B. `createGeoRestPort({ baseUrl: '/api/geo' })`. |
| `points` | `readonly GeoPoint[]` | nein | `() => []` | Punkte (Dezimalgrad, WGS 84/ETRS89). |
| `areas` | `readonly GeoArea[]` | nein | `() => []` | Flächen als GeoJSON-Polygon/-MultiPolygon. |
| `tiles` | `TileSource \| null` | nein | `null` | Kachelquelle der Anwendung; ohne Angabe kein Hintergrund und kein fremder Server. |
| `center` | `LatLon` | nein | `() => ({ lat: 51.163, lon: 10.448 })` | Anfangsausschnitt; ohne Punkte und Flächen gilt er dauerhaft. |
| `zoom` | `number` | nein | `6` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `radius-completed` | `[result: RadiusResult]` | – |
| `location-checked` | `[result: LocateResult]` | – |
| `areas-loaded` | `[areas: readonly GeoArea[], result: GeoPackageResult]` | – |
| `reference-change` | `[point: LatLon \| null]` | – |
| `error` | `[message: string]` | – |

#### `FaIcon`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `name` | `IconName` | ja | – | – |
| `size` | `number \| string` | nein | `18` | – |
| `label` | `string` | nein | `''` | Mit Beschriftung ist das Symbol bedeutungstragend (role="img"), sonst dekorativ. |

#### `FaSynopsis`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `comparison` | `Comparison \| null` | nein | `null` | Gespeicherter Vergleich (`GET /comparisons/{id}`). |
| `result` | `ComparisonResult \| null` | nein | `null` | Alternativ nur das Ergebnisobjekt (`ComparisonResult.to_dict()`). |
| `comparisonId` | `string` | nein | `undefined` | Mit `port`: Vergleich selbst laden. |
| `port` | `SynopsisPort \| null` | nein | `null` | – |
| `title` | `string` | nein | `''` | – |
| `oldLabel` | `string` | nein | `''` | – |
| `newLabel` | `string` | nein | `''` | – |
| `editable` | `boolean` | nein | `false` | Auswahl und Grund je Zeile bearbeiten (Vorschau vor der Ausgabe). |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `row-update` | `[update: RowUpdate]` | – |
| `export` | `[payload: ExportPayload]` | – |
| `navigate` | `[rowId: string]` | – |

#### `FaTable`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `columns` | `readonly TableColumn[]` | nein | `() => []` | – |
| `rows` | `readonly TableRow[]` | nein | `() => []` | – |
| `rowKey` | `string` | nein | `'id'` | – |
| `caption` | `string` | nein | `''` | – |
| `emptyText` | `string` | nein | `''` | – |
| `clickable` | `boolean` | nein | `false` | Zeilen sind anklickbar (Maus und Enter) und lösen `row-click` aus. |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `row-click` | `[row: TableRow]` | – |
| `sort-change` | `[sort: SortState \| null]` | – |

#### `FaTextField`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `label` | `string` | ja | – | – |
| `type` | `'text' \| 'search' \| 'email' \| 'date' \| 'number' \| 'password'` | nein | `'text'` | – |
| `placeholder` | `string` | nein | `''` | – |
| `hint` | `string` | nein | `''` | – |
| `error` | `string` | nein | `''` | – |
| `disabled` | `boolean` | nein | `false` | – |
| `required` | `boolean` | nein | `false` | – |
| `hideLabel` | `boolean` | nein | `false` | – |
| `autofocus` | `boolean` | nein | `false` | – |

#### `FaVvt`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `DataProtectionPort \| null` | nein | `null` | Datenzugang (Vertrag dataprotection_ui/1), z. B. `createDataProtectionRestPort({ baseUrl: '/api/dataprotection' })`. |
| `actor` | `string` | nein | `''` | Kennung der angemeldeten Person; nur für den Vier-Augen-Hinweis, geprüft wird auf dem Server. |
| `editable` | `boolean` | nein | `true` | `false`: nur Ansicht, keine Bearbeitung und Freigabe. |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `draft-saved` | `[detail: { version: number; revision: number }]` | – |
| `released` | `[detail: { version: number }]` | – |
| `exported` | `[detail: VvtExport]` | – |
| `error` | `[detail: DataProtectionError]` | – |

#### `KanbanBoard`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `BoardPort \| null` | nein | `null` | Speicher-/Rechte-Port; ohne Port wird `board` lokal (In-Memory) bearbeitet. |
| `boardId` | `string` | nein | `''` | – |
| `board` | `Board \| null` | nein | `null` | – |
| `userId` | `string` | nein | `''` | – |
| `users` | `readonly UserRef[]` | nein | `() => []` | – |
| `readOnly` | `boolean` | nein | `false` | – |
| `sharedByName` | `string` | nein | `''` | – |
| `showFullscreen` | `boolean` | nein | `true` | – |
| `today` | `string` | nein | `undefined` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `board-change` | `[board: Board]` | – |
| `error` | `[error: KanbanError]` | – |
| `fullscreen` | `[]` | – |
| `navigate` | `[link: CardLink, card: Card]` | – |
| `attachment` | `[attachment: Attachment, card: Card]` | – |
| `card-open` | `[card: Card]` | – |

#### `KanbanBoardList`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `BoardPort \| null` | nein | `null` | – |
| `activeId` | `string` | nein | `''` | – |
| `now` | `number` | nein | `() => Date.now()` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `board-select` | `[boardId: string]` | – |
| `created` | `[board: Board]` | – |

#### `KanbanCard`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `card` | `Card` | ja | – | – |
| `done` | `boolean` | nein | `false` | – |
| `today` | `string` | ja | – | – |
| `now` | `number` | nein | `() => Date.now()` | – |
| `canToggle` | `boolean` | nein | `false` | – |
| `grabbed` | `boolean` | nein | `false` | – |
| `dragging` | `boolean` | nein | `false` | – |
| `describedBy` | `string` | nein | `undefined` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `open` | `[card: Card]` | – |
| `toggle-done` | `[card: Card]` | – |

#### `KanbanCardDetail`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `card` | `Card \| null` | ja | – | – |
| `columns` | `readonly Column[]` | ja | – | – |
| `readOnly` | `boolean` | nein | `false` | – |
| `canDelete` | `boolean` | nein | `false` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `close` | `[]` | – |
| `update` | `[fields: Record<string, unknown>]` | – |
| `delete` | `[card: Card]` | – |
| `navigate` | `[link: CardLink]` | – |
| `attachment` | `[attachment: Attachment]` | – |

#### `KanbanColumn`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `view` | `ColumnView` | ja | – | – |
| `doneColumnId` | `string` | ja | – | – |
| `today` | `string` | ja | – | – |
| `canCreate` | `boolean` | nein | `false` | – |
| `canToggle` | `boolean` | nein | `false` | – |
| `grabbedId` | `string \| null` | nein | `null` | – |
| `draggingId` | `string \| null` | nein | `null` | – |
| `instructionsId` | `string` | nein | `undefined` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `add` | `[columnId: string]` | – |
| `open` | `[card: Card]` | – |
| `toggle-done` | `[card: Card]` | – |
| `card-keydown` | `[event: KeyboardEvent, card: Card]` | – |
| `card-pointerdown` | `[event: PointerEvent, card: Card]` | – |

#### `KanbanSettingsDialog`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `open` | `boolean` | ja | – | – |
| `columns` | `readonly Column[]` | ja | – | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `close` | `[]` | – |
| `save` | `[columns: Column[]]` | – |

#### `KanbanShareDialog`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `open` | `boolean` | ja | – | – |
| `shares` | `readonly Share[]` | ja | – | – |
| `search` | `((query: string) => Promise<UserRef[]>) \| null` | nein | `null` | – |
| `users` | `readonly UserRef[]` | nein | `() => []` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `close` | `[]` | – |
| `share` | `[userId: string, permission: SharePermission]` | – |
| `revoke` | `[userId: string]` | – |

#### `RiskFlagCard`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `entry` | `FlagEntry` | ja | – | – |
| `profile` | `ProfileReference \| null` | nein | `null` | – |
| `locale` | `Locale` | nein | `undefined` | – |

#### `RiskFlagFilter`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `rules` | `readonly RuleView[]` | nein | `() => []` | – |
| `shown` | `number` | nein | `0` | – |
| `total` | `number` | nein | `0` | – |
| `locale` | `Locale` | nein | `undefined` | – |

#### `RiskFlagState`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `state` | `FlagState` | ja | – | – |
| `code` | `string` | nein | `''` | Code für die Beschriftung (Tabellenzelle), sonst nur der Zustand. |
| `compact` | `boolean` | nein | `false` | Nur Symbol sichtbar, Text für Screenreader und Tooltip. |
| `locale` | `Locale` | nein | `undefined` | – |

#### `RiskFlagSummary`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `rows` | `readonly RiskDistributionRow[]` | nein | `() => []` | – |
| `totals` | `Totals \| null` | nein | `null` | – |
| `dataset` | `readonly DatasetFinding[]` | nein | `() => []` | – |
| `missingColumns` | `Readonly<Record<string, readonly string[]>>` | nein | `() => ({})` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `code-select` | `[code: string]` | – |

#### `RiskFlagTable`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `columns` | `readonly TableColumn[]` | nein | `() => []` | – |
| `rows` | `readonly TableRow[]` | nein | `() => []` | – |
| `codes` | `readonly string[]` | nein | `() => []` | Codes der Regelspalten (Zellen zeigen den Zustand). |
| `selected` | `number \| null` | nein | `null` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `record-select` | `[index: number]` | – |

#### `RiskFlags`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `evaluation` | `Evaluation \| null` | nein | `null` | Antwort von `POST /evaluate` (docs/ui/risk-rest.md). |
| `profile` | `ProfileDetail \| null` | nein | `null` | Antwort von `GET /profiles/{id}/{version}`; ohne sie entfällt die Profilansicht. |
| `port` | `RiskPort \| null` | nein | `null` | Optional: lädt die Profilbeschreibung nach, wenn `profile` fehlt (`createRiskRestPort`). |
| `heading` | `string` | nein | `''` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `record-select` | `[index: number \| null]` | – |
| `filter-change` | `[filter: RiskFilter]` | – |

#### `RiskProfileInfo`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `profile` | `ProfileDetail \| null` | nein | `null` | – |
| `locale` | `Locale` | nein | `undefined` | – |

#### `RiskRecordDetail`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `record` | `RecordView \| null` | nein | `null` | – |
| `entries` | `readonly FlagEntry[]` | nein | `() => []` | – |
| `profile` | `ProfileReference \| null` | nein | `null` | – |
| `locale` | `Locale` | nein | `undefined` | – |

#### `SamplingPanel`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `SamplingPort \| null` | nein | `null` | Fachlogik, z. B. `createSamplingRestPort({ baseUrl: '/api/sampling' })`. |
| `items` | `readonly PopulationItem[]` | nein | `() => []` | Grundgesamtheit; alternativ Datei-Import in der Komponente. |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `size-calculated` | `[result: SizeResult]` | – |
| `selection-drawn` | `[result: SelectionResult]` | – |
| `error` | `[message: string]` | – |

#### `ScreeningReview`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `ScreeningPort \| null` | nein | `null` | Datenzugang (Vertrag screening_review/1), z. B. `createScreeningRestPort({ baseUrl: '/api/screening' })`. |
| `runId` | `string` | nein | `''` | Beim Laden zu öffnender Prüflauf. |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `run-created` | `[detail: { runId: string }]` | – |
| `decided` | `[detail: { runId: string; hitId: string; status: string }]` | – |
| `error` | `[detail: ScreeningError]` | – |

#### `TableImport`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `mode` | `'values' \| 'items'` | nein | `'values'` | `items`: zusätzlich Kennungs- und Schichtspalte wählbar. |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `import` | `[columns: ImportedColumns]` | – |
<!-- api-overview:end -->

## Konfiguration

- **Theming:** alle Farben, Abstände, Radien und Schriften sind CSS-Variablen
  `--fa-*` (`src/theme/tokens.css`); Anwendungen überschreiben sie. Hell ist
  Standard, dunkel über `data-fa-theme="dark"` am Wurzelelement oder – ohne
  explizite Wahl – über `prefers-color-scheme`. `applyTheme('dark' | 'light'
  | 'system')`, `readTheme`, `resolvedTheme`, `useTheme`. Kanban nutzt
  zusätzlich `--fa-kanban-*`.
- **Sprache:** `Locale` ist `'de' | 'en'`, Standard Deutsch (vollständig),
  Englisch vorbereitet und darf Lücken haben (Rückfall auf Deutsch).
  `createFlowauditUi({ locale })` (auch als `Ref`), Prop `locale` an
  einzelnen Komponenten, `defineFlowauditElements({ locale })` bzw.
  `setDefaultLocale` für Web Components. Texte eigener Komponenten:
  `useI18n(defineMessages({ de, en }))`; Formatierer `formatDate`,
  `formatNumber`, `formatPercent` (Intl-Kurzformen in Rechnerzeit, seit
  0.2.0 aus `@flowaudit/common` weitergereicht; für Berliner Zeit und den
  Ersatzwert „—“ die gleichnamigen Funktionen aus `@flowaudit/common`).
- **REST-Hilfen** für Port-Umsetzungen: `requestJson`, `requestFile`
  (`fetch` injizierbar, Fehler als `RestError`), `saveFile` – seit 0.2.0 aus
  `@flowaudit/common` weitergereicht –, `createRunner`.
- **Toasts:** `useToast()` nutzt die anwendungsweite Warteschlange
  (`sharedToastQueue()`), `useToast(queue)` eine eigene aus
  `createToastQueue` (`@flowaudit/common`).
- **Kanban:** Komponenten arbeiten über einen `BoardPort` aus
  `@flowaudit/kanban-core` (`MemoryBoardPort` oder `RestBoardPort`).

## Herkunft und Charakterisierung

Neu in auditcore entwickelt (PR #80 Gerüst, #84 Kanban, #83 Stichprobe
und Benford, #111 Screening, #88 Risiko-Merkmale). Die fachliche Parität
der Komponenten zu den Quellanwendungen ist je Komponente dokumentiert:
[Stichprobe/Benford](../../docs/ui/sampling-benford-paritaet.md),
[Screening](../../docs/ui/screening-paritaet.md),
[Risiko-Merkmale](../../docs/ui/risk-flags-paritaet.md),
[VVT und DSFA](../../docs/ui/dataprotection-paritaet.md). Die
Kanban-Komponenten bilden die Bedienung des Workspace-Boards aus
`janpow77/audit_designer` und des Auftragsboards aus `janpow77/cockpit` nach
([Paritätsinventur](../../docs/kanban/paritaet-audit-designer.md)); die
Regeln kommen aus `@flowaudit/kanban-core`. Ziehen per Pointer Events ist
eine eigene Umsetzung (vuedraggable/SortableJS geprüft und verworfen).
Seit 0.2.0 liegen die framework-freien Module (Formatierer, REST-Client,
Sortierung, Tabellen-Einlesen, `saveFile`) in `@flowaudit/common` und werden
hier unter denselben Namen weitergereicht; die bisherigen Tests laufen
unverändert gegen die Weiterreichung. Seit 0.3.0 liegen Kern und Stile von
Basis, Tabelle, Synopse und Datenschutz in `@flowaudit/ui-core`; die
Vue-Komponenten binden dessen Zustandsautomaten über `useStore` an
([Parität Vue ↔ React](../../docs/ui/react-paritaet.md)).
Geprüft mit Vitest (happy-dom) und Playwright gegen die Demo-Seite
(`npm run e2e -w @flowaudit/ui`).

## Abhängigkeiten

- `@flowaudit/common` 0.1.0 (Laufzeit, framework-freie Hilfsfunktionen)
- `@flowaudit/ui-core` 0.1.0 (Laufzeit, framework-freier Kern: Texte,
  Verträge, View-Modelle, Zustandsautomaten, Stile)
- `@flowaudit/kanban-core` 0.1.0 (Laufzeit, Kanban-Regeln und Ports)
- `leaflet` ^1.9.4 (Laufzeit, BSD-2-Clause; Karte von `FaGeoMap`, erst beim
  Anzeigen einer Karte dynamisch geladen, Stile in `ui.css`)
- `vue` ^3.5.0 (Peer-Abhängigkeit; auch für den Web-Component-Einstieg)

Node ≥ 20.19 für Bau und Tests. Typprüfung mit `vue-tsc`.

## Sicherheit und Datenschutz

Texte werden über Vue-Templates ausgegeben und damit escaped; das Paket
verwendet kein `v-html`. `format`-Funktionen von Tabellenspalten liefern
Text, kein HTML. Netzwerkzugriffe gibt es nur über die Ports bzw.
`requestJson`/`requestFile` mit der vom Consumer gesetzten URL und
Kopfzeilen; Authentifizierung und Rechteentscheidung liegen beim Server.
Das Paket speichert weder in `localStorage` noch in anderen Browser-Speichern
(Ausnahme: `useAuthToken` schreibt über den `TokenStore`, den die Anwendung
übergibt, siehe `@flowaudit/common`);
angezeigte Daten (etwa Namen in Kanban-Freigaben) stammen ausschließlich aus
Props und Ports der Anwendung.

`FaGeoMap` lädt Kartenkacheln nur von der über `tiles` übergebenen Adresse;
ohne Angabe gibt es keinen Hintergrund und keine Anfrage an fremde Server.
Namensnennung und Beschriftungen gehen als Text (nicht als HTML) an Leaflet.
Adressen werden nie ohne ausdrückliche Freigabe versendet:
`createGeoRestPort({ geocoding: true })` und ein serverseitig angeschlossener
Geocoder sind beide nötig.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Eigene Symbole (`FaIcon`), keine übernommenen
Fremdkomponenten.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
