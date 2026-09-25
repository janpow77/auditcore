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
  `<flowaudit-kanban-board>` und `<flowaudit-kanban-boards>` im Light DOM
  (kein Shadow DOM, Designtoken der Seite gelten). Objekte und Listen werden
  als JS-Eigenschaften gesetzt, Ereignisse sind `CustomEvent`s in kebab-case
  mit den emit-Argumenten in `detail`. `vue` wird dabei als Abhängigkeit
  mitgeladen.
- **React:** über die Hüllen in `@flowaudit/ui-react` (`FlowauditTable`,
  `FlowauditKanbanBoard`, `FlowauditKanbanBoards`).

Kanban-Oberfläche mit Ports, Tastaturbedienung und Barrierefreiheit:
[`docs/kanban/oberflaeche.md`](../../docs/kanban/oberflaeche.md). Neue
Komponenten: [`docs/ui/beitragen.md`](../../docs/ui/beitragen.md).

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (262):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/ui` | `ActorView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `AgeKey` | Typ | – | `kanban/cardView` |
| `@flowaudit/ui` | `AllocationMethod` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `AllocationRequest` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `AllocationResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `AnalyseError` | Typ | – | `benford/model` |
| `@flowaudit/ui` | `AnalyseInput` | Schnittstelle | – | `benford/model` |
| `@flowaudit/ui` | `AnalyseRequest` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `AnalyseValidation` | Typ | – | `benford/model` |
| `@flowaudit/ui` | `ApiErrorBody` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `BADGE_COLORS` | Konstante | Badge-Farben je Präfix (WorkspaceTaskCard: VP, SYS/SP, JKB, PRJ), sonst grau. | `kanban/cardView` |
| `@flowaudit/ui` | `BadgeTone` | Typ | – | `base/types` |
| `@flowaudit/ui` | `BenfordAnalysis` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `BenfordCallbacks` | Schnittstelle | – | `benford/useBenford` |
| `@flowaudit/ui` | `BenfordCatalogue` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `BenfordDistribution` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `BenfordPanel` | Vue-Komponente | – | `benford/BenfordPanel.vue` |
| `@flowaudit/ui` | `BenfordPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createBenfordRestPort`. | `benford/types` |
| `@flowaudit/ui` | `BenfordTest` | Typ | Typen des REST-Vertrags `docs/ui/benford-rest.md` (auditcore_statistics.web). | `benford/types` |
| `@flowaudit/ui` | `Breakdown` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `BreakdownRow` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `BreakdownStep` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `ButtonSize` | Typ | – | `base/types` |
| `@flowaudit/ui` | `ButtonVariant` | Typ | – | `base/types` |
| `@flowaudit/ui` | `CARD_COLORS` | Konstante | Kartenfarben zur Auswahl (TaskDetail colorPresets). | `kanban/cardView` |
| `@flowaudit/ui` | `COLUMN_COLORS` | Konstante | Spaltenfarben (BoardSettingsDialog PRESET_COLORS). | `kanban/cardView` |
| `@flowaudit/ui` | `CONTRACT` | Konstante | – | `screening/types` |
| `@flowaudit/ui` | `Catalogs` | Schnittstelle | Kataloge je Sprache; Deutsch ist vollständig, Englisch darf (noch) lückenhaft sein. | `i18n/i18n` |
| `@flowaudit/ui` | `CellValue` | Typ | – | `table/sort` |
| `@flowaudit/ui` | `ChartBar` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui` | `ChartBox` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui` | `ChartGeometry` | Schnittstelle | – | `benford/chart` |
| `@flowaudit/ui` | `ColumnView` | Schnittstelle | – | `kanban/useKanbanBoard` |
| `@flowaudit/ui` | `ComparisonRow` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `ConfidenceLevel` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `Conformity` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `ConformityProfile` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `ConformityRow` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `DEFAULT_BOX` | Konstante | – | `benford/chart` |
| `@flowaudit/ui` | `DEFAULT_LOCALE` | Konstante | – | `i18n/i18n` |
| `@flowaudit/ui` | `DecimalSeparator` | Typ | – | `tabular/parse` |
| `@flowaudit/ui` | `DecisionRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `DecisionView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Delimiter` | Typ | Einlesen einfacher Tabellendateien (CSV/TSV/Text) ohne Bibliothek. | `tabular/parse` |
| `@flowaudit/ui` | `DerivationStep` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `DistributionRow` | Schnittstelle | – | `benford/types` |
| `@flowaudit/ui` | `DownloadFile` | Schnittstelle | Heruntergeladene Datei (Export). | `rest/client` |
| `@flowaudit/ui` | `ElementDefinition` | Schnittstelle | Eine Komponente, die als Web Component `flowaudit-<name>` bereitgestellt wird. | `elements/define` |
| `@flowaudit/ui` | `ElementTag` | Typ | – | `elements/define` |
| `@flowaudit/ui` | `EntryView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `ExportFormat` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `FaBadge` | Vue-Komponente | – | `base/FaBadge.vue` |
| `@flowaudit/ui` | `FaButton` | Vue-Komponente | – | `base/FaButton.vue` |
| `@flowaudit/ui` | `FaDialog` | Vue-Komponente | – | `base/FaDialog.vue` |
| `@flowaudit/ui` | `FaIcon` | Vue-Komponente | – | `base/FaIcon.vue` |
| `@flowaudit/ui` | `FaTable` | Vue-Komponente | – | `table/FaTable.vue` |
| `@flowaudit/ui` | `FaTextField` | Vue-Komponente | – | `base/FaTextField.vue` |
| `@flowaudit/ui` | `FetchLike` | Typ | Kleiner JSON-Client für die REST-Ports der Fachkomponenten. | `rest/client` |
| `@flowaudit/ui` | `FieldError` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui` | `FieldErrorCode` | Typ | – | `sampling/model` |
| `@flowaudit/ui` | `FilterOptions` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `FindingView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `FlowauditUiOptions` | Schnittstelle | – | `plugin` |
| `@flowaudit/ui` | `FreshnessStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `FreshnessView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `HitFilter` | Schnittstelle | – | `screening/view` |
| `@flowaudit/ui` | `HitView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `ICONS` | Konstante | Eigene Strichsymbole (24er-Raster, Strichstärke über CSS). Jede Zeile ist eine Liste von SVG-Pfaden; neue Symbole nur hier ergänzen. | `base/icons` |
| `@flowaudit/ui` | `IconName` | Typ | – | `base/icons` |
| `@flowaudit/ui` | `ImportedColumns` | Schnittstelle | Übernommene Spalten einer Datei. | `tabular/useTableImport` |
| `@flowaudit/ui` | `KanbanBoard` | Vue-Komponente | – | `kanban/KanbanBoard.vue` |
| `@flowaudit/ui` | `KanbanBoardList` | Vue-Komponente | – | `kanban/KanbanBoardList.vue` |
| `@flowaudit/ui` | `KanbanBoardOptions` | Schnittstelle | – | `kanban/useKanbanBoard` |
| `@flowaudit/ui` | `KanbanCard` | Vue-Komponente | – | `kanban/KanbanCard.vue` |
| `@flowaudit/ui` | `KanbanCardDetail` | Vue-Komponente | – | `kanban/KanbanCardDetail.vue` |
| `@flowaudit/ui` | `KanbanColumn` | Vue-Komponente | – | `kanban/KanbanColumn.vue` |
| `@flowaudit/ui` | `KanbanSettingsDialog` | Vue-Komponente | – | `kanban/KanbanSettingsDialog.vue` |
| `@flowaudit/ui` | `KanbanShareDialog` | Vue-Komponente | – | `kanban/KanbanShareDialog.vue` |
| `@flowaudit/ui` | `LOCALES` | Konstante | – | `i18n/i18n` |
| `@flowaudit/ui` | `LOCALE_KEY` | Konstante | – | `i18n/i18n` |
| `@flowaudit/ui` | `LevelTone` | Typ | – | `benford/model` |
| `@flowaudit/ui` | `ListInfo` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Locale` | Typ | – | `i18n/i18n` |
| `@flowaudit/ui` | `LogEntry` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `LogView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `MessageParams` | Typ | – | `i18n/i18n` |
| `@flowaudit/ui` | `MethodKind` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `MethodProfile` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `MethodStatus` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `MovePreview` | Schnittstelle | – | `kanban/movePreview` |
| `@flowaudit/ui` | `NamedOption` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `NumberColumn` | Schnittstelle | – | `tabular/parse` |
| `@flowaudit/ui` | `Outcome` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `PRIORITY_TONES` | Konstante | – | `kanban/cardView` |
| `@flowaudit/ui` | `ParameterSpec` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `ParsedTable` | Schnittstelle | – | `tabular/parse` |
| `@flowaudit/ui` | `PopulationItem` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `ProfileView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `RelativeKey` | Typ | – | `kanban/cardView` |
| `@flowaudit/ui` | `RestError` | Klasse | Fehler der REST-Schnittstelle mit Status, Code und deutscher Meldung des Servers. | `rest/client` |
| `@flowaudit/ui` | `RestOptions` | Schnittstelle | – | `rest/client` |
| `@flowaudit/ui` | `ReviewEvents` | Schnittstelle | – | `screening/useScreeningReview` |
| `@flowaudit/ui` | `ReviewStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `ReviewView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `RunQuery` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `RunRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `RunRequestRecord` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `RunSummary` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `RunView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `Runner` | Schnittstelle | – | `rest/runner` |
| `@flowaudit/ui` | `SCREENING_CONTRACT` | Konstante | – | `screening/types` |
| `@flowaudit/ui` | `SamplingCallbacks` | Schnittstelle | – | `sampling/useSampling` |
| `@flowaudit/ui` | `SamplingCatalogue` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SamplingPanel` | Vue-Komponente | – | `sampling/SamplingPanel.vue` |
| `@flowaudit/ui` | `SamplingPort` | Schnittstelle | Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createSamplingRestPort`. | `sampling/types` |
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
| `@flowaudit/ui` | `SelectionError` | Typ | – | `sampling/useSampling` |
| `@flowaudit/ui` | `SelectionInput` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui` | `SelectionRequest` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SelectionResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SelectionRow` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SelectionValidation` | Typ | – | `sampling/model` |
| `@flowaudit/ui` | `SelectionVariant` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `SettingsView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `ShortValues` | Typ | – | `benford/types` |
| `@flowaudit/ui` | `SizeRequest` | Typ | – | `sampling/types` |
| `@flowaudit/ui` | `SizeResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SizeValidation` | Typ | – | `sampling/model` |
| `@flowaudit/ui` | `SortDirection` | Typ | – | `table/sort` |
| `@flowaudit/ui` | `SortState` | Schnittstelle | – | `table/sort` |
| `@flowaudit/ui` | `SourceView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SourcesView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `StratumCount` | Schnittstelle | – | `sampling/model` |
| `@flowaudit/ui` | `StratumResult` | Schnittstelle | – | `sampling/types` |
| `@flowaudit/ui` | `SubjectInput` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SubjectRequest` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `SubjectStatus` | Typ | – | `screening/types` |
| `@flowaudit/ui` | `SubjectView` | Schnittstelle | – | `screening/types` |
| `@flowaudit/ui` | `TableColumn` | Schnittstelle | – | `table/sort` |
| `@flowaudit/ui` | `TableImport` | Vue-Komponente | – | `tabular/TableImport.vue` |
| `@flowaudit/ui` | `TableRow` | Typ | – | `table/sort` |
| `@flowaudit/ui` | `ThemeMode` | Typ | – | `theme/theme` |
| `@flowaudit/ui` | `Translate` | Typ | – | `i18n/i18n` |
| `@flowaudit/ui` | `UseBenford` | Schnittstelle | – | `benford/useBenford` |
| `@flowaudit/ui` | `UseI18n` | Schnittstelle | – | `i18n/i18n` |
| `@flowaudit/ui` | `UseSampling` | Schnittstelle | – | `sampling/useSampling` |
| `@flowaudit/ui` | `UseTableImport` | Schnittstelle | – | `tabular/useTableImport` |
| `@flowaudit/ui` | `UseTheme` | Schnittstelle | – | `theme/theme` |
| `@flowaudit/ui` | `ViewMessage` | Schnittstelle | Meldung als Katalogschlüssel mit Platzhaltern; die Komponente übersetzt sie. | `screening/view` |
| `@flowaudit/ui` | `acceptsHit` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `applyPreview` | Funktion | Spaltenansicht mit der bewegten Karte an der Vorschauposition. | `kanban/movePreview` |
| `@flowaudit/ui` | `applyTheme` | Funktion | Setzt das Farbschema am Element (Standard: Dokumentwurzel); 'system' folgt dem Betriebssystem. | `theme/theme` |
| `@flowaudit/ui` | `ariaSort` | Funktion | – | `table/sort` |
| `@flowaudit/ui` | `axisMaximum` | Funktion | Obergrenze der y-Achse: nächstes Vielfaches des Tickabstands über dem Maximum. | `benford/chart` |
| `@flowaudit/ui` | `badgePrefix` | Funktion | – | `kanban/cardView` |
| `@flowaudit/ui` | `badgeStyle` | Funktion | – | `kanban/cardView` |
| `@flowaudit/ui` | `baseMessages` | Konstante | Texte der Basiskomponenten. | `i18n/messages` |
| `@flowaudit/ui` | `benfordElement` | Konstante | `<flowaudit-benford>`: Eigenschaften `port` (BenfordPort), `values`, `locale`; Ereignisse `analysis-completed`, `error`. | `benford/element` |
| `@flowaudit/ui` | `benfordMessages` | Konstante | Texte der Benford-Analyse. | `benford/messages` |
| `@flowaudit/ui` | `breakdownRows` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `buildAnalyseRequest` | Funktion | Anfrage für `POST /analyze`; Test, Profil und ggf. Regel für kurze Werte sind Pflicht. | `benford/model` |
| `@flowaudit/ui` | `buildSelectionRequest` | Funktion | Anfrage für `POST /selection`; ein leerer Seed überlässt dem Server die Erzeugung. | `sampling/model` |
| `@flowaudit/ui` | `buildSizeRequest` | Funktion | Anfrage für `POST /size`; jedes Feld ist Pflicht, nichts wird still ergänzt. | `sampling/model` |
| `@flowaudit/ui` | `cardAge` | Funktion | Alter einer Karte in Stufen wie WorkspaceTaskCard (neu, Stunden, Tage, Wochen, Monate). | `kanban/cardView` |
| `@flowaudit/ui` | `chartGeometry` | Funktion | – | `benford/chart` |
| `@flowaudit/ui` | `codeLabel` | Funktion | Beschriftung eines Codes aus dem Vertrag (Status, Stufe, Hinweis); unbekannte Codes bleiben stehen. | `screening/messages` |
| `@flowaudit/ui` | `columnCells` | Funktion | Zellen einer Spalte. | `tabular/parse` |
| `@flowaudit/ui` | `compareValues` | Funktion | Vergleich: leere Werte immer zuletzt, Zahlen/Daten numerisch, Text sprachsensitiv. | `table/sort` |
| `@flowaudit/ui` | `comparisonRows` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `createBenfordRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_statistics.web` (Starlette oder FastAPI). | `benford/rest-port` |
| `@flowaudit/ui` | `createFlowauditUi` | Funktion | Vue-Plugin: stellt die Sprache app-weit bereit. | `plugin` |
| `@flowaudit/ui` | `createRunner` | Funktion | Gemeinsamer Ablauf für Portanfragen: Beschäftigt-Status, Fehlermeldung, Rückruf. | `rest/runner` |
| `@flowaudit/ui` | `createSamplingRestPort` | Funktion | Port auf den REST-Vertrag von `auditcore_sampling.web` (Starlette oder FastAPI). | `sampling/rest-port` |
| `@flowaudit/ui` | `createScreeningRestPort` | Funktion | Port auf den REST-Vertrag `screening_review/1` von `auditcore_registry_sources.web`. | `screening/rest-port` |
| `@flowaudit/ui` | `defineMessages` | Funktion | Typisiert Kataloge einer Komponente; die Schlüssel ergeben sich aus dem deutschen Katalog. | `i18n/i18n` |
| `@flowaudit/ui` | `detectDecimal` | Funktion | Dezimaltrenner einer Spalte: stehen beide Zeichen in einer Zelle, ist das letzte der Dezimaltrenner; ein Trenner ohne genau drei Folgeziffern ist ebenfalls eindeutig. | `tabular/parse` |
| `@flowaudit/ui` | `detectDelimiter` | Funktion | Häufigstes Trennzeichen der ersten Zeile; eine Spalte ohne Trenner ergibt ';'. | `tabular/parse` |
| `@flowaudit/ui` | `digitLabel` | Funktion | Anzeige einer Ziffer: zweite Ziffer 0–9, sonst Zahl. | `benford/model` |
| `@flowaudit/ui` | `emptyFilter` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `fieldValue` | Funktion | Prüft ein Eingabefeld und liefert den Vertragswert (Prozent → Anteil). | `sampling/model` |
| `@flowaudit/ui` | `filterOptions` | Funktion | – | `screening/view` |
| `@flowaudit/ui` | `filterSubjects` | Funktion | Subjects with only the hits passing the filter; subjects themselves stay visible. | `screening/view` |
| `@flowaudit/ui` | `focusableWithin` | Funktion | – | `composables/useFocusTrap` |
| `@flowaudit/ui` | `formatDate` | Funktion | Datum (ISO-Zeichenkette oder Date) kurz und sprachabhängig; ungültige Werte bleiben leer. | `i18n/format` |
| `@flowaudit/ui` | `formatNumber` | Funktion | – | `i18n/format` |
| `@flowaudit/ui` | `formatPercent` | Funktion | – | `i18n/format` |
| `@flowaudit/ui` | `guessNumberColumn` | Funktion | Index der ersten Spalte, deren nicht leere Zellen überwiegend (≥ 60 %) Zahlen sind; sonst 0. | `tabular/parse` |
| `@flowaudit/ui` | `hasPartialStrata` | Funktion | Teilweise geschichtete Grundgesamtheit (der Server lehnt sie ab). | `sampling/model` |
| `@flowaudit/ui` | `initialTexts` | Funktion | Startwerte der Textfelder: vorgeschlagene Werte der Profile, sonst leer. | `sampling/model` |
| `@flowaudit/ui` | `initials` | Funktion | Initialen aus einem Namen: erster und letzter Namensteil. | `kanban/cardView` |
| `@flowaudit/ui` | `interpolate` | Funktion | Ersetzt {name}-Platzhalter; unbekannte Platzhalter bleiben sichtbar stehen. | `i18n/i18n` |
| `@flowaudit/ui` | `isIconName` | Funktion | – | `base/icons` |
| `@flowaudit/ui` | `isLocale` | Funktion | – | `i18n/i18n` |
| `@flowaudit/ui` | `isPercent` | Funktion | Anteile werden in Prozent eingegeben und angezeigt. | `sampling/model` |
| `@flowaudit/ui` | `itemsFromImport` | Funktion | Übernommene Dateispalten → Elemente der Grundgesamtheit (Kennung sonst laufende Nummer). | `sampling/model` |
| `@flowaudit/ui` | `kanbanBoardElement` | Konstante | `<flowaudit-kanban-board>`: Eigenschaften `port` (BoardPort) und `boardId` oder `board` (+ `userId`) für lokale Bearbeitung; Ereignisse `board-change`, `error`, `fullscreen`, `navi … | `kanban/element` |
| `@flowaudit/ui` | `kanbanBoardListElement` | Konstante | `<flowaudit-kanban-boards>`: Boardliste mit Eigenschaft `port`; Ereignisse `board-select`, `created`. | `kanban/element` |
| `@flowaudit/ui` | `kanbanDialogMessages` | Konstante | Texte von Detailansicht, Einstellungen, Teilen und Boardliste. | `kanban/messages` |
| `@flowaudit/ui` | `kanbanMessages` | Konstante | Texte der Kanban-Komponenten; Englisch vorbereitet. | `kanban/messages` |
| `@flowaudit/ui` | `levelTone` | Funktion | Farbton der MAD-Stufe 0–3 (enge … keine Übereinstimmung). | `benford/model` |
| `@flowaudit/ui` | `localeTag` | Funktion | – | `i18n/format` |
| `@flowaudit/ui` | `needsShortValues` | Funktion | Zweistellige Tests (erste zwei Ziffern, zweite Ziffer) verlangen eine Regel für kurze Werte. | `benford/model` |
| `@flowaudit/ui` | `nextOpenHit` | Funktion | The next hit still needing work after ``currentId`` (open, deferred or pending). | `screening/view` |
| `@flowaudit/ui` | `nextSort` | Funktion | Nächster Zustand beim Klick auf eine Spalte: aufsteigend → absteigend → unsortiert. | `table/sort` |
| `@flowaudit/ui` | `numberColumn` | Funktion | Eine Spalte als Zahlen; unlesbare Zellen werden verworfen und gemeldet. | `tabular/parse` |
| `@flowaudit/ui` | `parseInput` | Funktion | Eingabetext (deutsch oder englisch notiert) → Zahl; leer → null, unlesbar → undefined. | `sampling/model` |
| `@flowaudit/ui` | `parseNumber` | Funktion | Zelle → Zahl mit ausdrücklichem Dezimaltrenner; der jeweils andere Trenner gilt als Tausenderpunkt. Leer ergibt `null` (fehlend), Unlesbares `undefined`. | `tabular/parse` |
| `@flowaudit/ui` | `parseSubjects` | Funktion | One subject per line: ``Name; Geburtsdatum; Land; Bezug`` (only the name is required). | `screening/view` |
| `@flowaudit/ui` | `parseTable` | Funktion | Text → Tabelle. `hasHeader` legt fest, ob die erste Zeile Spaltennamen enthält; sonst heißen die Spalten „Spalte 1“, „Spalte 2“ … | `tabular/parse` |
| `@flowaudit/ui` | `placementFor` | Funktion | Platzierung für den Port aus der sichtbaren Nachbarschaft: vor der Karte an `index`, sonst hinter der letzten sichtbaren Karte, sonst ans Ende. | `kanban/movePreview` |
| `@flowaudit/ui` | `populationSuggestions` | Funktion | Vorschlagswerte aus der Grundgesamtheit (Summe positiver Werte bzw. Anzahl). | `sampling/model` |
| `@flowaudit/ui` | `positiveSum` | Funktion | Summe der positiven Werte (Auswahlbasis der Variante „portal“). | `sampling/model` |
| `@flowaudit/ui` | `preview` | Funktion | – | `kanban/cardView` |
| `@flowaudit/ui` | `provideLocale` | Funktion | Stellt die Sprache für alle Nachfahren bereit (App-Ebene oder Teilbaum). | `i18n/i18n` |
| `@flowaudit/ui` | `readTheme` | Funktion | Liest das explizit gesetzte Farbschema; ohne Attribut 'system'. | `theme/theme` |
| `@flowaudit/ui` | `relativeTime` | Funktion | Relative Zeit für die Boardliste (WorkspaceSidebar.relativeTime). | `kanban/cardView` |
| `@flowaudit/ui` | `requestFile` | Funktion | POST mit Dateiantwort; der Dateiname kommt aus `Content-Disposition`. | `rest/client` |
| `@flowaudit/ui` | `requestJson` | Funktion | GET/POST mit JSON-Antwort. Der Antworttyp ist der dokumentierte REST-Vertrag. | `rest/client` |
| `@flowaudit/ui` | `resolvedTheme` | Funktion | Tatsächlich wirksames Schema, auch wenn 'system' gewählt ist. | `theme/theme` |
| `@flowaudit/ui` | `samplingElement` | Konstante | `<flowaudit-sampling>`: Eigenschaften `port` (SamplingPort), `items` (Grundgesamtheit), `locale`; Ereignisse `size-calculated`, `selection-drawn`, `error`. | `sampling/element` |
| `@flowaudit/ui` | `samplingMessages` | Konstante | Texte des Stichprobenrechners. | `sampling/messages` |
| `@flowaudit/ui` | `saveFile` | Funktion | Bietet eine Datei im Browser zum Speichern an. | `rest/download` |
| `@flowaudit/ui` | `screeningMessages` | Konstante | Texte der Screening-Trefferprüfung (Sanktionslisten, PEP). | `screening/messages` |
| `@flowaudit/ui` | `screeningReviewElement` | Konstante | `<flowaudit-screening-review>`: Eigenschaften `port` (ScreeningPort), `runId`, `locale`; Ereignisse `run-created`, `decided`, `error`. | `screening/element` |
| `@flowaudit/ui` | `setDefaultLocale` | Funktion | Sprache ohne Provider, z. B. für Web Components ohne umgebende Vue-App. | `i18n/i18n` |
| `@flowaudit/ui` | `sortRows` | Funktion | Stabile Sortierung einer Kopie; die Eingabe bleibt unverändert. | `table/sort` |
| `@flowaudit/ui` | `splitLine` | Funktion | Eine Zeile mit Anführungszeichen nach RFC 4180 (doppelte "" als Maskierung). | `tabular/parse` |
| `@flowaudit/ui` | `strataOf` | Funktion | Schichten in Reihenfolge ihres ersten Auftretens; leer, wenn kein Element geschichtet ist. | `sampling/model` |
| `@flowaudit/ui` | `tableElement` | Konstante | `<flowaudit-table>`: Spalten und Zeilen als JS-Eigenschaften, Ereignisse `row-click`, `sort-change`. | `table/element` |
| `@flowaudit/ui` | `tabularMessages` | Konstante | Texte des Datei-Imports (Stichprobe, Benford). | `tabular/messages` |
| `@flowaudit/ui` | `textOn` | Funktion | Lesbare Schriftfarbe auf einer Kartenfarbe (Luminanzschwelle wie im Original). | `kanban/cardView` |
| `@flowaudit/ui` | `translate` | Funktion | Übersetzt mit Rückfall auf Deutsch und zuletzt auf den Schlüssel. | `i18n/i18n` |
| `@flowaudit/ui` | `useBenford` | Funktion | Zustand und Ablauf der Benford-Analyse; Berechnung ausschließlich über den Port. | `benford/useBenford` |
| `@flowaudit/ui` | `useFocusTrap` | Funktion | Hält den Tastaturfokus im Container, solange `active` wahr ist, und gibt ihn danach an das zuvor fokussierte Element zurück. | `composables/useFocusTrap` |
| `@flowaudit/ui` | `useI18n` | Funktion | Composable für Komponenten. `override` (z. B. eine Prop `locale`) hat Vorrang vor der bereitgestellten Sprache. | `i18n/i18n` |
| `@flowaudit/ui` | `useId` | Funktion | Eindeutige, stabile ID je Komponenteninstanz für aria-Verknüpfungen. | `composables/useId` |
| `@flowaudit/ui` | `useKanbanActions` | Funktion | – | `kanban/useKanbanActions` |
| `@flowaudit/ui` | `useKanbanBoard` | Funktion | – | `kanban/useKanbanBoard` |
| `@flowaudit/ui` | `useKanbanFilter` | Funktion | Such- und Filterzustand des Boards (Toolbar) als CardFilter der Kernlogik. | `kanban/useKanbanFilter` |
| `@flowaudit/ui` | `useLocale` | Funktion | – | `i18n/i18n` |
| `@flowaudit/ui` | `useMoveController` | Funktion | – | `kanban/useMoveController` |
| `@flowaudit/ui` | `useSampling` | Funktion | Zustand und Abläufe des Stichprobenrechners. Die Fachlogik liegt im Port; hier werden nur Eingaben geprüft, Anfragen gebildet und Ergebnisse gehalten. | `sampling/useSampling` |
| `@flowaudit/ui` | `useScreeningReview` | Funktion | – | `screening/useScreeningReview` |
| `@flowaudit/ui` | `useTableImport` | Funktion | Datei lesen, Spalten zuordnen und eine Vorschau der übernommenen Werte bilden. | `tabular/useTableImport` |
| `@flowaudit/ui` | `useTheme` | Funktion | Composable: reaktives Farbschema, synchron mit dem Attribut am Element. | `theme/theme` |
| `@flowaudit/ui` | `validateDecision` | Funktion | – | `screening/view` |
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
| `<flowaudit-kanban-board>` | `KanbanBoard` | `kanban/element.ts` |
| `<flowaudit-kanban-boards>` | `KanbanBoardList` | `kanban/element.ts` |
| `<flowaudit-sampling>` | `SamplingPanel` | `sampling/element.ts` |
| `<flowaudit-screening-review>` | `ScreeningReview` | `screening/element.ts` |
| `<flowaudit-table>` | `FaTable` | `table/element.ts` |

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

#### `FaIcon`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `name` | `IconName` | ja | – | – |
| `size` | `number \| string` | nein | `18` | – |
| `label` | `string` | nein | `''` | Mit Beschriftung ist das Symbol bedeutungstragend (role="img"), sonst dekorativ. |

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

Neu in auditcore entwickelt (PR #80 Gerüst, PR #84 Kanban). Die
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
