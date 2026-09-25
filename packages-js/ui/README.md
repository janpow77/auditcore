# @flowaudit/ui

## Zweck

Gemeinsame Oberflächenkomponenten der FlowAudit-Anwendungen als Vue-3-Komponenten und Web Components, mit Designtoken, Hell-/Dunkelmodus und Sprachunterstützung.

Für die Frontends der FlowAudit-Anwendungen, unabhängig davon, ob sie Vue,
React (über `@flowaudit/ui-react`) oder kein Framework nutzen. Jede
Komponente gibt es als Vue-Komponente, als Web Component `<flowaudit-…>` und
als React-Hülle. Fachdaten kommen über Props oder Ports; das Paket speichert
nichts selbst.

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
Tarball (zusammen mit `@flowaudit/kanban-core`). Die Stile kommen immer aus
`@flowaudit/ui/style.css`.

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
  `useTheme`, `useFocusTrap`, `useId`.

  ```vue
  <FaTable :columns="columns" :rows="rows" clickable @row-click="open" />
  <KanbanBoard :port="port" board-id="b1" @board-change="save" />
  ```

- **Web Component:** `defineFlowauditElements({ only?, locale? })` aus
  `@flowaudit/ui/elements` registriert `<flowaudit-table>`,
  `<flowaudit-kanban-board>`, `<flowaudit-kanban-boards>`,
  `<flowaudit-sampling>`, `<flowaudit-benford>`,
  `<flowaudit-screening-review>` und `<flowaudit-risk-flags>` im Light DOM
  (kein Shadow DOM, Designtoken der Seite gelten). Objekte und Listen werden
  als JS-Eigenschaften gesetzt, Ereignisse sind `CustomEvent`s in kebab-case
  mit den emit-Argumenten in `detail`. `vue` wird dabei als Abhängigkeit
  mitgeladen.
- **React:** über die Hüllen in `@flowaudit/ui-react` (`FlowauditTable`,
  `FlowauditKanbanBoard`, `FlowauditKanbanBoards`, `FlowauditSampling`,
  `FlowauditBenford`, `FlowauditScreeningReview`, `FlowauditRiskFlags`,
  `FlowauditVvt`, `FlowauditDsfa`).

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

Kanban-Oberfläche mit Ports, Tastaturbedienung und Barrierefreiheit:
[`docs/kanban/oberflaeche.md`](../../docs/kanban/oberflaeche.md). Neue
Komponenten: [`docs/ui/beitragen.md`](../../docs/ui/beitragen.md).

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (499):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/ui` | `ANSWER_VALUES` | Konstante | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `Activity` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui` | `ActivityGroup` | Schnittstelle | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `ActorView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `AgeKey` | Typ | – | `kanban/cardView` |
| `@flowaudit/ui` | `AllocationMethod` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `AllocationRequest` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `AllocationResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `AnalyseError` | Typ | – | `benford/model` |
| `@flowaudit/ui` | `AnalyseInput` | Schnittstelle | – | `benford/model` |
| `@flowaudit/ui` | `AnalyseRequest` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `AnalyseValidation` | Typ | – | `benford/model` |
| `@flowaudit/ui` | `AnswerInput` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `AnswerValue` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui` | `ApiErrorBody` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `AssessmentExportFormat` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui` | `AssessmentStatus` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui` | `AssessmentSummary` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `AssessmentView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `BADGE_COLORS` | Konstante | Badge-Farben je Präfix (WorkspaceTaskCard: VP, SYS/SP, JKB, PRJ), sonst grau. | `kanban/cardView` |
| `@flowaudit/ui` | `BadgeTone` | Typ | – | `base/types` |
| `@flowaudit/ui` | `BenfordAnalysis` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `BenfordCallbacks` | Schnittstelle | – | `benford/useBenford` |
| `@flowaudit/ui` | `BenfordCatalogue` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `BenfordDistribution` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `BenfordPanel` | Vue-Komponente | – | `benford/BenfordPanel.vue` |
| `@flowaudit/ui` | `BenfordPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createBenfordRestPort`. | `benford/types` |
| `@flowaudit/ui` | `BenfordTest` | Typ | Typen des REST-Vertrags `docs/ui/benford-rest.md` (auditcore_statistics.web). | `benford/types` |
| `@flowaudit/ui` | `BlockProgress` | Schnittstelle | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `BlockView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `Breakdown` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `BreakdownRow` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `BreakdownStep` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `ButtonSize` | Typ | – | `base/types` |
| `@flowaudit/ui` | `ButtonVariant` | Typ | – | `base/types` |
| `@flowaudit/ui` | `CARD_COLORS` | Konstante | Kartenfarben zur Auswahl (TaskDetail colorPresets). | `kanban/cardView` |
| `@flowaudit/ui` | `CHANGE_STATUSES` | Konstante | Vorgabe des Filters „Alle Änderungen“: alles außer unverändert. | `synopsis/types` |
| `@flowaudit/ui` | `COLUMN_COLORS` | Konstante | Spaltenfarben (BoardSettingsDialog PRESET_COLORS). | `kanban/cardView` |
| `@flowaudit/ui` | `CONTRACT` | Konstante | – | `screening/types` |
| `@flowaudit/ui` | `Catalogs` | Schnittstelle | Kataloge je Sprache; Deutsch ist vollständig, Englisch darf (noch) lückenhaft sein. | `i18n/i18n` |
| `@flowaudit/ui` | `CellValue` | Typ | – | `table/sort` |
| `@flowaudit/ui` | `ChartBar` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui` | `ChartBox` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui` | `ChartGeometry` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui` | `ClientExportFormat` | Typ | – | `synopsis/types` |
| `@flowaudit/ui` | `ColumnCheck` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui` | `ColumnView` | Schnittstelle | – | `kanban/useKanbanBoard` |
| `@flowaudit/ui` | `CompareFields` | Schnittstelle | – | `synopsis/port` |
| `@flowaudit/ui` | `CompareRow` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui` | `Comparison` | Schnittstelle | Ein gespeicherter Vergleich (`GET /comparisons/{id}`). | `synopsis/types` |
| `@flowaudit/ui` | `ComparisonMetadata` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui` | `ComparisonProfile` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui` | `ComparisonResult` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui` | `ComparisonRow` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `ComparisonSummary` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui` | `Completeness` | Schnittstelle | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `ConfidenceLevel` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `Conformity` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `ConformityProfile` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `ConformityRow` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `ConsolidatedParagraph` | Schnittstelle | – | `synopsis/types` |
| `@flowaudit/ui` | `DATAPROTECTION_CONTRACT` | Konstante | – | `dataprotection/types` |
| `@flowaudit/ui` | `DEFAULT_BOX` | Konstante | – | `benford/chart` |
| `@flowaudit/ui` | `DEFAULT_FILTER` | Konstante | – | `risk/view/state` |
| `@flowaudit/ui` | `DEFAULT_LOCALE` | Konstante | – | `i18n/i18n` |
| `@flowaudit/ui` | `DEFAULT_SYNOPSIS_FILTER` | Konstante | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `DataProtectionError` | Schnittstelle | Fehler einer Portanfrage: Code und Meldung des Servers bzw. `network_error` mit Status 0. | `dataprotection/requests` |
| `@flowaudit/ui` | `DataProtectionKey` | Typ | – | `dataprotection/messages` |
| `@flowaudit/ui` | `DataProtectionPort` | Schnittstelle | Datenzugang der Komponenten. Die mitgelieferte Umsetzung ist `createDataProtectionRestPort`; Anwendungen können eigene Ports übergeben. | `dataprotection/types` |
| `@flowaudit/ui` | `DataProtectionProfile` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `DataProtectionTranslate` | Typ | – | `dataprotection/messages` |
| `@flowaudit/ui` | `DatasetFinding` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `DecimalSeparator` | Typ | – | `tabular/parse` |
| `@flowaudit/ui` | `DecisionInput` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `DecisionRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `DecisionView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Delimiter` | Typ | Einlesen einfacher Tabellendateien (CSV/TSV/Text) ohne Bibliothek. | `tabular/parse` |
| `@flowaudit/ui` | `DerivationStep` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `DiffField` | Typ | – | `synopsis/types` |
| `@flowaudit/ui` | `DiffSegment` | Schnittstelle | – | `synopsis/wordDiff` |
| `@flowaudit/ui` | `DiffSide` | Typ | – | `synopsis/wordDiff` |
| `@flowaudit/ui` | `DistributionRow` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `DossierFieldView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `DownloadFile` | Schnittstelle | Heruntergeladene Datei (Export). | `rest/client` |
| `@flowaudit/ui` | `DsfaHooks` | Schnittstelle | – | `dataprotection/useDsfa` |
| `@flowaudit/ui` | `DsfaState` | Schnittstelle | – | `dataprotection/useDsfa` |
| `@flowaudit/ui` | `DsfaStep` | Typ | – | `dataprotection/useDsfa` |
| `@flowaudit/ui` | `ElementDefinition` | Schnittstelle | Eine Komponente, die als Web Component `flowaudit-<name>` bereitgestellt wird. | `elements/define` |
| `@flowaudit/ui` | `ElementTag` | Typ | – | `elements/define` |
| `@flowaudit/ui` | `EntryView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `EvaluateRequest` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui` | `Evaluation` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `ExportFormat` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `ExportInput` | Schnittstelle | – | `synopsis/exporters` |
| `@flowaudit/ui` | `ExportPayload` | Schnittstelle | Ergebnis eines Exports in der Oberfläche (Ereignis `export`). | `synopsis/types` |
| `@flowaudit/ui` | `ExportTexts` | Schnittstelle | – | `dataprotection/exporters` |
| `@flowaudit/ui` | `ExportedFile` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `FLAG_STATES` | Konstante | – | `risk/view/state` |
| `@flowaudit/ui` | `FaBadge` | Vue-Komponente | – | `base/FaBadge.vue` |
| `@flowaudit/ui` | `FaButton` | Vue-Komponente | – | `base/FaButton.vue` |
| `@flowaudit/ui` | `FaDialog` | Vue-Komponente | – | `base/FaDialog.vue` |
| `@flowaudit/ui` | `FaDsfa` | Vue-Komponente | – | `dataprotection/FaDsfa.vue` |
| `@flowaudit/ui` | `FaIcon` | Vue-Komponente | – | `base/FaIcon.vue` |
| `@flowaudit/ui` | `FaSynopsis` | Vue-Komponente | – | `synopsis/FaSynopsis.vue` |
| `@flowaudit/ui` | `FaTable` | Vue-Komponente | – | `table/FaTable.vue` |
| `@flowaudit/ui` | `FaTextField` | Vue-Komponente | – | `base/FaTextField.vue` |
| `@flowaudit/ui` | `FaVvt` | Vue-Komponente | – | `dataprotection/FaVvt.vue` |
| `@flowaudit/ui` | `FetchLike` | Typ | Kleiner JSON-Client für die REST-Ports der Fachkomponenten. | `rest/client` |
| `@flowaudit/ui` | `FieldEntry` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `FieldError` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui` | `FieldErrorCode` | Typ | – | `sampling/model` |
| `@flowaudit/ui` | `FieldKind` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui` | `FieldUse` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `FieldValue` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui` | `FieldView` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `FilterOptions` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `FindingView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `FlagEntry` | Schnittstelle | Ein Eintrag der Detailansicht: Treffer oder unbestimmtes Merkmal eines Datensatzes. | `risk/view/state` |
| `@flowaudit/ui` | `FlagHit` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `FlagState` | Typ | Zustand einer Regel für einen Datensatz. | `risk/view/state` |
| `@flowaudit/ui` | `FlowauditUiOptions` | Schnittstelle | – | `plugin` |
| `@flowaudit/ui` | `FreshnessStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `FreshnessView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `HitFilter` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `HitView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `ICONS` | Konstante | Eigene Strichsymbole (24er-Raster, Strichstärke über CSS). Jede Zeile ist eine Liste von SVG-Pfaden; neue Symbole nur hier ergänzen. | `base/icons` |
| `@flowaudit/ui` | `IconName` | Typ | – | `base/icons` |
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
| `@flowaudit/ui` | `KeyTitle` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `LOCALES` | Konstante | – | `i18n/i18n` |
| `@flowaudit/ui` | `LOCALE_KEY` | Konstante | – | `i18n/i18n` |
| `@flowaudit/ui` | `LevelTone` | Typ | – | `benford/model` |
| `@flowaudit/ui` | `LevelView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `ListInfo` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Locale` | Typ | – | `i18n/i18n` |
| `@flowaudit/ui` | `LogEntry` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `LogView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `MeasureView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `MessageParams` | Typ | – | `i18n/i18n` |
| `@flowaudit/ui` | `MethodKind` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `MethodProfile` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `MethodStatus` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `MovePreview` | Schnittstelle | – | `kanban/movePreview` |
| `@flowaudit/ui` | `NamedOption` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `NumberColumn` | Schnittstelle | – | `tabular/parse` |
| `@flowaudit/ui` | `Outcome` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `OverviewRow` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `PRIORITY_TONES` | Konstante | – | `kanban/cardView` |
| `@flowaudit/ui` | `ParameterSpec` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `ParsedTable` | Schnittstelle | – | `tabular/parse` |
| `@flowaudit/ui` | `Person` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `PopulationItem` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `ProfileDetail` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `ProfileReference` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `ProfileStatus` | Typ | – | `risk/types` |
| `@flowaudit/ui` | `ProfileSummary` | Schnittstelle | – | `risk/port` |
| `@flowaudit/ui` | `ProfileView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Proposal` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `QuestionView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `ROW_STATUSES` | Konstante | – | `synopsis/types` |
| `@flowaudit/ui` | `RecordView` | Schnittstelle | – | `risk/types` |
| `@flowaudit/ui` | `RegisterColumn` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `RegisterContent` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `RegisterExportFormat` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui` | `RegisterExportInput` | Schnittstelle | – | `dataprotection/exporters` |
| `@flowaudit/ui` | `RegisterIssue` | Schnittstelle | Hinweis der Vollständigkeitsprüfung; `subject` = `<Tätigkeits-ID>:<Feld>` oder `deckblatt:<Teil>`. | `dataprotection/types` |
| `@flowaudit/ui` | `RegisterState` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `RegisterStatus` | Typ | – | `dataprotection/types` |
| `@flowaudit/ui` | `RelativeKey` | Typ | – | `kanban/cardView` |
| `@flowaudit/ui` | `RestClientOptions` | Typ | Optionen wie bei `src/rest`: `baseUrl` (z. B. `/api/synopsis`), injizierbares `fetch`, Kopfzeilen. | `synopsis/port` |
| `@flowaudit/ui` | `RestError` | Klasse | Fehler der REST-Schnittstelle mit Status, Code und deutscher Meldung des Servers. | `rest/client` |
| `@flowaudit/ui` | `RestOptions` | Schnittstelle | – | `rest/client` |
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
| `@flowaudit/ui` | `RowStatus` | Typ | JSON-Formen des REST-Vertrags (docs/ui/synopsis-rest.md). Sie entsprechen `ComparisonResult.to_dict()` aus `auditcore_documents`; die Oberfläche kennt keine zweite Datenform. | `synopsis/types` |
| `@flowaudit/ui` | `RowUpdate` | Schnittstelle | Änderung einer Zeile (`PATCH /comparisons/{id}/rows`). | `synopsis/types` |
| `@flowaudit/ui` | `RowView` | Schnittstelle | – | `synopsis/viewModel` |
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
| `@flowaudit/ui` | `ScenarioInput` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `ScenarioResult` | Schnittstelle | – | `dataprotection/types` |
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
| `@flowaudit/ui` | `SegmentKind` | Typ | Wortdifferenz für die Anzeige, ohne Vue. Bevorzugt die vom Server gelieferte `difflib.ndiff`-Folge (`"  "` gleich, `"- "` entfallen, `"+ "` neu, `"? "` Hinweis); fehlt sie (Gesetze … | `synopsis/wordDiff` |
| `@flowaudit/ui` | `SelectionError` | Typ | – | `sampling/useSampling` |
| `@flowaudit/ui` | `SelectionInput` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui` | `SelectionRequest` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SelectionResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SelectionRow` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SelectionValidation` | Typ | – | `sampling/model` |
| `@flowaudit/ui` | `SelectionVariant` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `ServerExportFormat` | Typ | – | `synopsis/types` |
| `@flowaudit/ui` | `SettingsView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Severity` | Typ | – | `risk/types` |
| `@flowaudit/ui` | `ShortValues` | Typ | – | `benford/types` |
| `@flowaudit/ui` | `SizeRequest` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `SizeResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SizeValidation` | Typ | – | `sampling/model` |
| `@flowaudit/ui` | `SortDirection` | Typ | – | `table/sort` |
| `@flowaudit/ui` | `SortState` | Schnittstelle | – | `table/sort` |
| `@flowaudit/ui` | `SourceView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SourcesView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `StateFilter` | Typ | Filter: `affected` = Treffer oder unbestimmt; `all` = jeder Datensatz. | `risk/view/state` |
| `@flowaudit/ui` | `StratumCount` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui` | `StratumResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SubjectInput` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SubjectRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SubjectStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `SubjectView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SurveyInput` | Schnittstelle | Erhebung einer Folgenabschätzung, wie sie `POST /assessments/{id}` erwartet. | `dataprotection/types` |
| `@flowaudit/ui` | `SynopsisFilterState` | Schnittstelle | – | `synopsis/useSynopsis` |
| `@flowaudit/ui` | `SynopsisLayout` | Typ | – | `synopsis/types` |
| `@flowaudit/ui` | `SynopsisMessageKey` | Typ | – | `synopsis/messages` |
| `@flowaudit/ui` | `SynopsisPort` | Schnittstelle | – | `synopsis/port` |
| `@flowaudit/ui` | `SynopsisRestClient` | Schnittstelle | – | `synopsis/port` |
| `@flowaudit/ui` | `SynopsisRowFilter` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `SynopsisSource` | Schnittstelle | Eingaben der Komponente, als Getter übergeben (Props bleiben reaktiv). | `synopsis/useSynopsis` |
| `@flowaudit/ui` | `SynopsisTranslate` | Typ | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `SynopsisView` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `TabItem` | Schnittstelle | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `TableColumn` | Schnittstelle | – | `table/sort` |
| `@flowaudit/ui` | `TableImport` | Vue-Komponente | – | `tabular/TableImport.vue` |
| `@flowaudit/ui` | `TableRow` | Typ | – | `table/sort` |
| `@flowaudit/ui` | `ThemeMode` | Typ | – | `theme/theme` |
| `@flowaudit/ui` | `Tone` | Typ | Farbton wie `FaBadge` (`tone`). | `risk/view/format` |
| `@flowaudit/ui` | `Totals` | Schnittstelle | – | `risk/view/state` |
| `@flowaudit/ui` | `Translate` | Typ | – | `i18n/i18n` |
| `@flowaudit/ui` | `UseBenford` | Schnittstelle | – | `benford/useBenford` |
| `@flowaudit/ui` | `UseI18n` | Schnittstelle | – | `i18n/i18n` |
| `@flowaudit/ui` | `UseRiskFlags` | Schnittstelle | – | `risk/useRiskFlags` |
| `@flowaudit/ui` | `UseSampling` | Schnittstelle | – | `sampling/useSampling` |
| `@flowaudit/ui` | `UseSynopsis` | Schnittstelle | – | `synopsis/useSynopsis` |
| `@flowaudit/ui` | `UseSynopsisExport` | Schnittstelle | – | `synopsis/useSynopsisExport` |
| `@flowaudit/ui` | `UseSynopsisNavigation` | Schnittstelle | – | `synopsis/useSynopsisNavigation` |
| `@flowaudit/ui` | `UseTableImport` | Schnittstelle | – | `tabular/useTableImport` |
| `@flowaudit/ui` | `UseTheme` | Schnittstelle | – | `theme/theme` |
| `@flowaudit/ui` | `VersionSummary` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `VersionView` | Schnittstelle | – | `dataprotection/types` |
| `@flowaudit/ui` | `ViewMessage` | Schnittstelle | Meldung als Katalogschlüssel mit Platzhaltern; die Komponente übersetzt sie. | `screening/view` |
| `@flowaudit/ui` | `ViewOptions` | Schnittstelle | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `VvtExport` | Schnittstelle | – | `dataprotection/useVvt` |
| `@flowaudit/ui` | `VvtExportFormat` | Typ | – | `dataprotection/useVvt` |
| `@flowaudit/ui` | `VvtHooks` | Schnittstelle | – | `dataprotection/useVvt` |
| `@flowaudit/ui` | `VvtState` | Schnittstelle | – | `dataprotection/useVvt` |
| `@flowaudit/ui` | `WORD_LIMIT` | Konstante | Oberhalb dieser Wortzahl je Seite wird nicht wortweise verglichen. | `synopsis/wordDiff` |
| `@flowaudit/ui` | `WhenMissingColumns` | Typ | – | `risk/types` |
| `@flowaudit/ui` | `acceptsHit` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `activityKey` | Funktion | Schlüssel einer Tätigkeit für die Zuordnung der Hinweise (Kennung, sonst Name wie in der Bibliothek). | `dataprotection/registerView` |
| `@flowaudit/ui` | `addScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `answerOf` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `applyPreview` | Funktion | Spaltenansicht mit der bewegten Karte an der Vorschauposition. | `kanban/movePreview` |
| `@flowaudit/ui` | `applyRowOverrides` | Funktion | Zeilen mit lokalen Änderungen (Auswahl, Grund) zusammenführen. | `synopsis/viewModel` |
| `@flowaudit/ui` | `applyTheme` | Funktion | Setzt das Farbschema am Element (Standard: Dokumentwurzel); 'system' folgt dem Betriebssystem. | `theme/theme` |
| `@flowaudit/ui` | `ariaSort` | Funktion | – | `table/sort` |
| `@flowaudit/ui` | `axisMaximum` | Funktion | Obergrenze der y-Achse: nächstes Vielfaches des Tickabstands über dem Maximum. | `benford/chart` |
| `@flowaudit/ui` | `badgePrefix` | Funktion | – | `kanban/cardView` |
| `@flowaudit/ui` | `badgeStyle` | Funktion | – | `kanban/cardView` |
| `@flowaudit/ui` | `bandTone` | Funktion | Stufe eines Risikos nach Rang im Profil: höchste Stufe rot, zweithöchste gelb. | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `baseMessages` | Konstante | Texte der Basiskomponenten. | `i18n/messages` |
| `@flowaudit/ui` | `benfordElement` | Konstante | `<flowaudit-benford>`: Eigenschaften `port` (BenfordPort), `values`, `locale`; Ereignisse `analysis-completed`, `error`. | `benford/element` |
| `@flowaudit/ui` | `benfordMessages` | Konstante | Texte der Benford-Analyse. | `benford/messages` |
| `@flowaudit/ui` | `blockProgress` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `breakdownRows` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `buildAnalyseRequest` | Funktion | Anfrage für `POST /analyze`; Test, Profil und ggf. Regel für kurze Werte sind Pflicht. | `benford/model` |
| `@flowaudit/ui` | `buildRowView` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `buildSelectionRequest` | Funktion | Anfrage für `POST /selection`; ein leerer Seed überlässt dem Server die Erzeugung. | `sampling/model` |
| `@flowaudit/ui` | `buildSizeRequest` | Funktion | Anfrage für `POST /size`; jedes Feld ist Pflicht, nichts wird still ergänzt. | `sampling/model` |
| `@flowaudit/ui` | `buildSynopsisView` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `cardAge` | Funktion | Alter einer Karte in Stufen wie WorkspaceTaskCard (neu, Stunden, Tage, Wochen, Monate). | `kanban/cardView` |
| `@flowaudit/ui` | `changeIds` | Funktion | Kennungen der Änderungszeilen in Anzeigereihenfolge (Ziel der Navigation). | `synopsis/viewModel` |
| `@flowaudit/ui` | `chartGeometry` | Funktion | – | `benford/chart` |
| `@flowaudit/ui` | `cloneContent` | Funktion | Tiefe Kopie (JSON-Daten), damit Eingaben den gelesenen Stand nie verändern. | `dataprotection/registerView` |
| `@flowaudit/ui` | `codeLabel` | Funktion | Beschriftung eines Codes aus dem Vertrag (Status, Stufe, Hinweis); unbekannte Codes bleiben stehen. | `screening/messages` |
| `@flowaudit/ui` | `columnCells` | Funktion | Zellen einer Spalte. | `tabular/parse` |
| `@flowaudit/ui` | `compareValues` | Funktion | Vergleich: leere Werte immer zuletzt, Zahlen/Daten numerisch, Text sprachsensitiv. | `table/sort` |
| `@flowaudit/ui` | `comparisonRows` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `completeness` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `completenessTone` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `coverIssues` | Funktion | Hinweise zum Deckblatt (Verantwortlicher, DSB). | `dataprotection/registerView` |
| `@flowaudit/ui` | `createBenfordRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_statistics.web` (Starlette oder FastAPI). | `benford/rest-port` |
| `@flowaudit/ui` | `createDataProtectionRestPort` | Funktion | Port auf den REST-Vertrag `dataprotection_ui/1` von `auditcore_dataprotection.web`. | `dataprotection/rest-port` |
| `@flowaudit/ui` | `createFlowauditUi` | Funktion | Vue-Plugin: stellt die Sprache app-weit bereit. | `plugin` |
| `@flowaudit/ui` | `createRiskRestPort` | Funktion | REST-Umsetzung des Ports, z. B. `createRiskRestPort({ baseUrl: '/api/risk' })`. | `risk/port` |
| `@flowaudit/ui` | `createRunner` | Funktion | Gemeinsamer Ablauf für Portanfragen: Beschäftigt-Status, Fehlermeldung, Rückruf. | `rest/runner` |
| `@flowaudit/ui` | `createSamplingRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_sampling.web` (Starlette oder FastAPI). | `sampling/rest-port` |
| `@flowaudit/ui` | `createScreeningRestPort` | Funktion | Port auf den REST-Vertrag `screening_review/1` von `auditcore_registry_sources.web`. | `screening/rest-port` |
| `@flowaudit/ui` | `createSynopsisRestClient` | Funktion | – | `synopsis/port` |
| `@flowaudit/ui` | `csvCell` | Funktion | Eine CSV-Zelle für Excel-DE (Trenner „;“, Formelschutz, Zahlen mit Dezimalkomma). | `dataprotection/exporters` |
| `@flowaudit/ui` | `csvDocument` | Funktion | Ganze CSV-Datei: BOM, Zellen nach `csvCell`, Zeilenende CRLF. | `dataprotection/exporters` |
| `@flowaudit/ui` | `currentVersion` | Funktion | Angezeigte Fassung: offener Entwurf vor Freigabe (dort wird gearbeitet). | `dataprotection/registerView` |
| `@flowaudit/ui` | `dataprotectionError` | Funktion | – | `dataprotection/requests` |
| `@flowaudit/ui` | `dataprotectionMessages` | Konstante | Texte von `<flowaudit-vvt>` und `<flowaudit-dsfa>`. | `dataprotection/messages` |
| `@flowaudit/ui` | `decisionTitle` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `defineMessages` | Funktion | Typisiert Kataloge einer Komponente; die Schlüssel ergeben sich aus dem deutschen Katalog. | `i18n/i18n` |
| `@flowaudit/ui` | `detectDecimal` | Funktion | Dezimaltrenner einer Spalte: stehen beide Zeichen in einer Zelle, ist das letzte der Dezimaltrenner; ein Trenner ohne genau drei Folgeziffern ist ebenfalls eindeutig. | `tabular/parse` |
| `@flowaudit/ui` | `detectDelimiter` | Funktion | Häufigstes Trennzeichen der ersten Zeile; eine Spalte ohne Trenner ergibt ';'. | `tabular/parse` |
| `@flowaudit/ui` | `diffSegments` | Funktion | Segmente einer Seite. `ndiff` hat Vorrang; ohne sie wird nachgerechnet. Ist keine Wortdifferenz möglich, bleibt der Text unmarkiert (seitenweise) bzw. | `synopsis/wordDiff` |
| `@flowaudit/ui` | `digitLabel` | Funktion | Anzeige einer Ziffer: zweite Ziffer 0–9, sonst Zahl. | `benford/model` |
| `@flowaudit/ui` | `displayValue` | Funktion | Anzeigewert eines Feldes; Wahrheitswerte und Leerwerte über die Texte der Komponente. | `dataprotection/registerView` |
| `@flowaudit/ui` | `distribution` | Funktion | Verteilung je Regel in Profilreihenfolge (nur Datensatzregeln). | `risk/view/state` |
| `@flowaudit/ui` | `downloadText` | Funktion | Text als Datei anbieten (Blob-URL); ohne Blob-Unterstützung geschieht nichts. | `synopsis/useSynopsisExport` |
| `@flowaudit/ui` | `dsfaElement` | Konstante | `<flowaudit-dsfa>`: Eigenschaften `port`, `activityId`, `actor`, `editable`, `locale`; Ereignisse `assessment-change`, `error`. | `dataprotection/element` |
| `@flowaudit/ui` | `editedBy` | Funktion | Vier-Augen-Prinzip vorab anzeigen: wer den Entwurf bearbeitet hat, kann ihn nicht freigeben. | `dataprotection/registerView` |
| `@flowaudit/ui` | `emptyActivity` | Funktion | Tätigkeit ohne Kennung (die vergibt der Server beim Speichern). | `dataprotection/registerView` |
| `@flowaudit/ui` | `emptyContent` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `emptyFilter` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `emptyScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `escapeHtml` | Funktion | – | `synopsis/exporters` |
| `@flowaudit/ui` | `escapeMarkdown` | Funktion | – | `synopsis/exporters` |
| `@flowaudit/ui` | `evaluationRules` | Funktion | Regeln der Auswertung; ohne `rules` aus den Codes der Datensätze abgeleitet. | `risk/view/state` |
| `@flowaudit/ui` | `exportFilename` | Funktion | – | `synopsis/exporters` |
| `@flowaudit/ui` | `fieldIssues` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `fieldValue` | Funktion | Prüft ein Eingabefeld und liefert den Vertragswert (Prozent → Anteil). | `sampling/model` |
| `@flowaudit/ui` | `filterOptions` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `filterRecords` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `filterRows` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `filterSubjects` | Funktion | Subjects with only the hits passing the filter; subjects themselves stay visible. | `screening/view` |
| `@flowaudit/ui` | `flagState` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `focusRow` | Funktion | Zeile fokussieren und sichtbar machen; Zeilen tragen `data-row-id` und `tabindex="-1"`. | `synopsis/useSynopsisNavigation` |
| `@flowaudit/ui` | `focusableWithin` | Funktion | – | `composables/useFocusTrap` |
| `@flowaudit/ui` | `formatAmount` | Funktion | – | `risk/view/format` |
| `@flowaudit/ui` | `formatDate` | Funktion | Datum (ISO-Zeichenkette oder Date) kurz und sprachabhängig; ungültige Werte bleiben leer. | `i18n/format` |
| `@flowaudit/ui` | `formatNumber` | Funktion | – | `i18n/format` |
| `@flowaudit/ui` | `formatPercent` | Funktion | – | `i18n/format` |
| `@flowaudit/ui` | `formatShare` | Funktion | – | `risk/view/format` |
| `@flowaudit/ui` | `formatValue` | Funktion | Wert eines Eingabefelds: leer ausdrücklich, Zahlen im Sprachformat. | `risk/view/format` |
| `@flowaudit/ui` | `groupByDepartment` | Funktion | Referate wie in der Quelle: konfigurierte zuerst, dann unbekannte; leere entfallen. | `dataprotection/registerView` |
| `@flowaudit/ui` | `guessNumberColumn` | Funktion | Index der ersten Spalte, deren nicht leere Zellen überwiegend (≥ 60 %) Zahlen sind; sonst 0. | `tabular/parse` |
| `@flowaudit/ui` | `hasPartialStrata` | Funktion | Teilweise geschichtete Grundgesamtheit (der Server lehnt sie ab). | `sampling/model` |
| `@flowaudit/ui` | `initialTexts` | Funktion | Startwerte der Textfelder: vorgeschlagene Werte der Profile, sonst leer. | `sampling/model` |
| `@flowaudit/ui` | `initials` | Funktion | Initialen aus einem Namen: erster und letzter Namensteil. | `kanban/cardView` |
| `@flowaudit/ui` | `interpolate` | Funktion | Ersetzt {name}-Platzhalter; unbekannte Platzhalter bleiben sichtbar stehen. | `i18n/i18n` |
| `@flowaudit/ui` | `isDeviation` | Funktion | Abweichung vom Vorschlag verlangt eine Begründung (Bibliothek prüft Mindestlänge). | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `isIconName` | Funktion | – | `base/icons` |
| `@flowaudit/ui` | `isLocale` | Funktion | – | `i18n/i18n` |
| `@flowaudit/ui` | `isPercent` | Funktion | Anteile werden in Prozent eingegeben und angezeigt. | `sampling/model` |
| `@flowaudit/ui` | `issuesFor` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `itemsFromImport` | Funktion | Übernommene Dateispalten → Elemente der Grundgesamtheit (Kennung sonst laufende Nummer). | `sampling/model` |
| `@flowaudit/ui` | `kanbanBoardElement` | Konstante | `<flowaudit-kanban-board>`: Eigenschaften `port` (BoardPort) und `boardId` oder `board` (+ `userId`) für lokale Bearbeitung; Ereignisse `board-change`, `error`, `fullscreen`, `navi … | `kanban/element` |
| `@flowaudit/ui` | `kanbanBoardListElement` | Konstante | `<flowaudit-kanban-boards>`: Boardliste mit Eigenschaft `port`; Ereignisse `board-select`, `created`. | `kanban/element` |
| `@flowaudit/ui` | `kanbanDialogMessages` | Konstante | Texte von Detailansicht, Einstellungen, Teilen und Boardliste. | `kanban/messages` |
| `@flowaudit/ui` | `kanbanMessages` | Konstante | Texte der Kanban-Komponenten; Englisch vorbereitet. | `kanban/messages` |
| `@flowaudit/ui` | `lcsOperations` | Funktion | Längste gemeinsame Teilfolge über Wörter; `null` oberhalb von {@link WORD_LIMIT}. | `synopsis/wordDiff` |
| `@flowaudit/ui` | `levelLabel` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `levelTone` | Funktion | Farbton der MAD-Stufe 0–3 (enge … keine Übereinstimmung). | `benford/model` |
| `@flowaudit/ui` | `localeTag` | Funktion | – | `i18n/format` |
| `@flowaudit/ui` | `mayRelease` | Funktion | Vier-Augen-Prinzip vorab anzeigen; maßgeblich bleibt die Prüfung des Servers. | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `ndiffOperations` | Funktion | ndiff-Zeilen in Operationen übersetzen; Hinweiszeilen (`? `) entfallen. | `synopsis/wordDiff` |
| `@flowaudit/ui` | `needsShortValues` | Funktion | Zweistellige Tests (erste zwei Ziffern, zweite Ziffer) verlangen eine Regel für kurze Werte. | `benford/model` |
| `@flowaudit/ui` | `nextOpenHit` | Funktion | The next hit still needing work after ``currentId`` (open, deferred or pending). | `screening/view` |
| `@flowaudit/ui` | `nextSort` | Funktion | Nächster Zustand beim Klick auf eine Spalte: aufsteigend → absteigend → unsortiert. | `table/sort` |
| `@flowaudit/ui` | `numberColumn` | Funktion | Eine Spalte als Zahlen; unlesbare Zellen werden verworfen und gemeldet. | `tabular/parse` |
| `@flowaudit/ui` | `pairs` | Funktion | Objekt als Liste `[Schlüssel, Wert]` in Einfügereihenfolge (für deklarative Tabellen). | `risk/view/state` |
| `@flowaudit/ui` | `parameterLabel` | Funktion | – | `risk/view/format` |
| `@flowaudit/ui` | `parseConditions` | Funktion | Auflagen: eine je Zeile, leere Zeilen entfallen. | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `parseCount` | Funktion | Eingabe eines Zahlfeldes: leer → null, sonst nichtnegative ganze Zahl; ungültig → undefined. | `dataprotection/registerView` |
| `@flowaudit/ui` | `parseInput` | Funktion | Eingabetext (deutsch oder englisch notiert) → Zahl; leer → null, unlesbar → undefined. | `sampling/model` |
| `@flowaudit/ui` | `parseNumber` | Funktion | Zelle → Zahl mit ausdrücklichem Dezimaltrenner; der jeweils andere Trenner gilt als Tausenderpunkt. Leer ergibt `null` (fehlend), Unlesbares `undefined`. | `tabular/parse` |
| `@flowaudit/ui` | `parseSubjects` | Funktion | One subject per line: ``Name; Geburtsdatum; Land; Bezug`` (only the name is required). | `screening/view` |
| `@flowaudit/ui` | `parseTable` | Funktion | Text → Tabelle. `hasHeader` legt fest, ob die erste Zeile Spaltennamen enthält; sonst heißen die Spalten „Spalte 1“, „Spalte 2“ … | `tabular/parse` |
| `@flowaudit/ui` | `placementFor` | Funktion | Platzierung für den Port aus der sichtbaren Nachbarschaft: vor der Karte an `index`, sonst hinter der letzten sichtbaren Karte, sonst ans Ende. | `kanban/movePreview` |
| `@flowaudit/ui` | `plainSegments` | Funktion | – | `synopsis/wordDiff` |
| `@flowaudit/ui` | `populationSuggestions` | Funktion | Vorschlagswerte aus der Grundgesamtheit (Summe positiver Werte bzw. Anzahl). | `sampling/model` |
| `@flowaudit/ui` | `positionText` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `positiveSum` | Funktion | Summe der positiven Werte (Auswahlbasis der Variante „portal“). | `sampling/model` |
| `@flowaudit/ui` | `preview` | Funktion | – | `kanban/cardView` |
| `@flowaudit/ui` | `printHtml` | Funktion | Druckansicht in einem unsichtbaren Rahmen öffnen („Als PDF speichern“ im Druckdialog). Kein Pop-up, daher auch mit Pop-up-Blocker nutzbar. | `synopsis/useSynopsisExport` |
| `@flowaudit/ui` | `provideLocale` | Funktion | Stellt die Sprache für alle Nachfahren bereit (App-Ebene oder Teilbaum). | `i18n/i18n` |
| `@flowaudit/ui` | `readTheme` | Funktion | Liest das explizit gesetzte Farbschema; ohne Attribut 'system'. | `theme/theme` |
| `@flowaudit/ui` | `recommendationTone` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `recordEntries` | Funktion | Treffer und unbestimmte Merkmale eines Datensatzes in Profilreihenfolge. | `risk/view/state` |
| `@flowaudit/ui` | `recordLabel` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `recordRules` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `registerCsv` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui` | `registerFilename` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui` | `registerHtml` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui` | `registerMarkdown` | Funktion | – | `dataprotection/exporters` |
| `@flowaudit/ui` | `relativeTime` | Funktion | Relative Zeit für die Boardliste (WorkspaceSidebar.relativeTime). | `kanban/cardView` |
| `@flowaudit/ui` | `removeScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `requestFile` | Funktion | POST mit Dateiantwort; der Dateiname kommt aus `Content-Disposition`. | `rest/client` |
| `@flowaudit/ui` | `requestJson` | Funktion | GET/POST mit JSON-Antwort. Der Antworttyp ist der dokumentierte REST-Vertrag. | `rest/client` |
| `@flowaudit/ui` | `requirementKey` | Funktion | – | `risk/view/labels` |
| `@flowaudit/ui` | `resolvedTheme` | Funktion | Tatsächlich wirksames Schema, auch wenn 'system' gewählt ist. | `theme/theme` |
| `@flowaudit/ui` | `riskFlagsElement` | Konstante | `<flowaudit-risk-flags>`: Eigenschaften `evaluation` (Antwort von `POST /evaluate`) und `profile` (Antwort von `GET /profiles/{id}/{version}`) als JS-Objekte; Ereignisse `record-se … | `risk/element` |
| `@flowaudit/ui` | `riskMessages` | Konstante | Sichtbare Texte der Risiko-Komponenten (Deutsch vollständig, Englisch vorbereitet). | `risk/messages` |
| `@flowaudit/ui` | `sameSurvey` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `samplingElement` | Konstante | `<flowaudit-sampling>`: Eigenschaften `port` (SamplingPort), `items` (Grundgesamtheit), `locale`; Ereignisse `size-calculated`, `selection-drawn`, `error`. | `sampling/element` |
| `@flowaudit/ui` | `samplingMessages` | Konstante | Texte des Stichprobenrechners. | `sampling/messages` |
| `@flowaudit/ui` | `saveFile` | Funktion | Bietet eine Datei im Browser zum Speichern an. | `rest/download` |
| `@flowaudit/ui` | `screeningMessages` | Konstante | Texte der Screening-Trefferprüfung (Sanktionslisten, PEP). | `screening/messages` |
| `@flowaudit/ui` | `screeningReviewElement` | Konstante | `<flowaudit-screening-review>`: Eigenschaften `port` (ScreeningPort), `runId`, `locale`; Ereignisse `run-created`, `decided`, `error`. | `screening/element` |
| `@flowaudit/ui` | `screeningTone` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `segmentsText` | Funktion | – | `synopsis/wordDiff` |
| `@flowaudit/ui` | `setDefaultLocale` | Funktion | Sprache ohne Provider, z. B. für Web Components ohne umgebende Vue-App. | `i18n/i18n` |
| `@flowaudit/ui` | `severityTone` | Funktion | – | `risk/view/format` |
| `@flowaudit/ui` | `sortRows` | Funktion | Stabile Sortierung einer Kopie; die Eingabe bleibt unverändert. | `table/sort` |
| `@flowaudit/ui` | `splitLine` | Funktion | Eine Zeile mit Anführungszeichen nach RFC 4180 (doppelte "" als Maskierung). | `tabular/parse` |
| `@flowaudit/ui` | `stateTone` | Funktion | – | `risk/view/format` |
| `@flowaudit/ui` | `statusHintKey` | Funktion | Hinweis für nicht freigegebene Profile, sonst `null`. | `risk/view/labels` |
| `@flowaudit/ui` | `statusKey` | Funktion | – | `risk/view/labels` |
| `@flowaudit/ui` | `statusLabel` | Funktion | – | `synopsis/viewModel` |
| `@flowaudit/ui` | `statusTone` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `stepChange` | Funktion | Nächste bzw. vorige Änderung; ohne aktuelle Position beginnt `+1` bei der ersten und `-1` bei der letzten. Am Rand bleibt die Position stehen. | `synopsis/viewModel` |
| `@flowaudit/ui` | `strataOf` | Funktion | Schichten in Reihenfolge ihres ersten Auftretens; leer, wenn kein Element geschichtet ist. | `sampling/model` |
| `@flowaudit/ui` | `surveyFrom` | Funktion | Bearbeitbare Kopie der gespeicherten Erhebung. | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `synopsisElement` | Konstante | `<flowaudit-synopsis>`: `comparison`/`result` und `port` als JS-Eigenschaften; Ereignisse `row-update`, `export`, `navigate`, `update:layout`. | `synopsis/element` |
| `@flowaudit/ui` | `synopsisMessages` | Konstante | Sichtbare Texte der Synopse; Begriffe wie im audit_designer und in ecohesion. | `synopsis/messages` |
| `@flowaudit/ui` | `tableElement` | Konstante | `<flowaudit-table>`: Spalten und Zeilen als JS-Eigenschaften, Ereignisse `row-click`, `sort-change`. | `table/element` |
| `@flowaudit/ui` | `tabularMessages` | Konstante | Texte des Datei-Imports (Stichprobe, Benford). | `tabular/messages` |
| `@flowaudit/ui` | `textOn` | Funktion | Lesbare Schriftfarbe auf einer Kartenfarbe (Luminanzschwelle wie im Original). | `kanban/cardView` |
| `@flowaudit/ui` | `toHtml` | Funktion | Eigenständiges HTML-Dokument mit Druck-CSS (keine externen Ressourcen). | `synopsis/exporters` |
| `@flowaudit/ui` | `toMarkdown` | Funktion | Markdown: gestrichene Wörter als ~~…~~, neue als **…**. | `synopsis/exporters` |
| `@flowaudit/ui` | `toggleMeasure` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `totals` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `translate` | Funktion | Übersetzt mit Rückfall auf Deutsch und zuletzt auf den Schlüssel. | `i18n/i18n` |
| `@flowaudit/ui` | `triggeredDataset` | Funktion | – | `risk/view/state` |
| `@flowaudit/ui` | `useBenford` | Funktion | Zustand und Ablauf der Benford-Analyse; Berechnung ausschließlich über den Port. | `benford/useBenford` |
| `@flowaudit/ui` | `useDsfa` | Funktion | – | `dataprotection/useDsfa` |
| `@flowaudit/ui` | `useFocusTrap` | Funktion | Hält den Tastaturfokus im Container, solange `active` wahr ist, und gibt ihn danach an das zuvor fokussierte Element zurück. | `composables/useFocusTrap` |
| `@flowaudit/ui` | `useI18n` | Funktion | Composable für Komponenten. `override` (z. B. eine Prop `locale`) hat Vorrang vor der bereitgestellten Sprache. | `i18n/i18n` |
| `@flowaudit/ui` | `useId` | Funktion | Eindeutige, stabile ID je Komponenteninstanz für aria-Verknüpfungen. | `composables/useId` |
| `@flowaudit/ui` | `useKanbanActions` | Funktion | – | `kanban/useKanbanActions` |
| `@flowaudit/ui` | `useKanbanBoard` | Funktion | – | `kanban/useKanbanBoard` |
| `@flowaudit/ui` | `useKanbanFilter` | Funktion | Such- und Filterzustand des Boards (Toolbar) als CardFilter der Kernlogik. | `kanban/useKanbanFilter` |
| `@flowaudit/ui` | `useLocale` | Funktion | – | `i18n/i18n` |
| `@flowaudit/ui` | `useMoveController` | Funktion | – | `kanban/useMoveController` |
| `@flowaudit/ui` | `useRiskFlags` | Funktion | Zustand und abgeleitete Daten der Gesamtansicht; ohne DOM testbar. | `risk/useRiskFlags` |
| `@flowaudit/ui` | `useRiskProfile` | Funktion | Profilbeschreibung zur Auswertung: die übergebene, sonst über den Port nachgeladen (Profil und Version der Auswertung, nie ein Standardprofil). | `risk/useRiskProfile` |
| `@flowaudit/ui` | `useSampling` | Funktion | Zustand und Abläufe des Stichprobenrechners. Die Fachlogik liegt im Port; hier werden nur Eingaben geprüft, Anfragen gebildet und Ergebnisse gehalten. | `sampling/useSampling` |
| `@flowaudit/ui` | `useScreeningReview` | Funktion | – | `screening/useScreeningReview` |
| `@flowaudit/ui` | `useSynopsis` | Funktion | – | `synopsis/useSynopsis` |
| `@flowaudit/ui` | `useSynopsisExport` | Funktion | Exporte der sichtbaren, ausgewählten Zeilen; `onExport` erhält jedes Ergebnis. | `synopsis/useSynopsisExport` |
| `@flowaudit/ui` | `useSynopsisNavigation` | Funktion | Navigation zwischen Änderungen mit Schaltflächen und Tasten N/J bzw. P/K. | `synopsis/useSynopsisNavigation` |
| `@flowaudit/ui` | `useTableImport` | Funktion | Datei lesen, Spalten zuordnen und eine Vorschau der übernommenen Werte bilden. | `tabular/useTableImport` |
| `@flowaudit/ui` | `useTheme` | Funktion | Composable: reaktives Farbschema, synchron mit dem Attribut am Element. | `theme/theme` |
| `@flowaudit/ui` | `useVvt` | Funktion | – | `dataprotection/useVvt` |
| `@flowaudit/ui` | `validateDecision` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `vvtElement` | Konstante | `<flowaudit-vvt>`: Eigenschaften `port` (DataProtectionPort), `actor`, `editable`, `locale`; Ereignisse `draft-saved`, `released`, `exported`, `error`. | `dataprotection/element` |
| `@flowaudit/ui` | `whenMissingKey` | Funktion | – | `risk/view/labels` |
| `@flowaudit/ui` | `wholeSegments` | Funktion | Ganze Texte als Streichung und Einfügung (neue/entfallene Stellen, Rückfall). | `synopsis/wordDiff` |
| `@flowaudit/ui` | `withActivity` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `withAnswer` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `withDepartments` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `withField` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `withJustification` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `withPerson` | Funktion | – | `dataprotection/registerView` |
| `@flowaudit/ui` | `withScenario` | Funktion | – | `dataprotection/dsfaView` |
| `@flowaudit/ui` | `withoutActivity` | Funktion | – | `dataprotection/registerView` |
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
  `formatNumber`, `formatPercent`.
- **REST-Hilfen** für Port-Umsetzungen: `requestJson`, `requestFile`
  (`fetch` injizierbar, Fehler als `RestError`), `createRunner`, `saveFile`.
- **Kanban:** Komponenten arbeiten über einen `BoardPort` aus
  `@flowaudit/kanban-core` (`MemoryBoardPort` oder `RestBoardPort`).

## Herkunft und Charakterisierung

Neu in auditcore entwickelt (PR #80 Gerüst, #84 Kanban, #83 Stichprobe
und Benford, #111 Screening, #88 Risiko-Merkmale, VVT/DSFA). Die fachliche Parität
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
Geprüft mit Vitest (happy-dom) und Playwright gegen die Demo-Seite
(`npm run e2e -w @flowaudit/ui`).

## Abhängigkeiten

- `@flowaudit/kanban-core` 0.1.0 (Laufzeit, Kanban-Regeln und Ports)
- `vue` ^3.5.0 (Peer-Abhängigkeit; auch für den Web-Component-Einstieg)

Node ≥ 20.19 für Bau und Tests. Typprüfung mit `vue-tsc`.

## Sicherheit und Datenschutz

Texte werden über Vue-Templates ausgegeben und damit escaped; das Paket
verwendet kein `v-html`. `format`-Funktionen von Tabellenspalten liefern
Text, kein HTML. Netzwerkzugriffe gibt es nur über die Ports bzw.
`requestJson`/`requestFile` mit der vom Consumer gesetzten URL und
Kopfzeilen; Authentifizierung und Rechteentscheidung liegen beim Server.
Das Paket speichert weder in `localStorage` noch in anderen Browser-Speichern;
angezeigte Daten (etwa Namen in Kanban-Freigaben) stammen ausschließlich aus
Props und Ports der Anwendung.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Eigene Symbole (`FaIcon`), keine übernommenen
Fremdkomponenten.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
