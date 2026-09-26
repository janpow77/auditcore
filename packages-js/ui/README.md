# @auditcore/ui

## Zweck

Gemeinsame Oberflächenkomponenten der FlowAudit-Anwendungen als Vue-3-Komponenten und Web Components, mit Designtoken, Hell-/Dunkelmodus und Sprachunterstützung.

Für die Frontends der FlowAudit-Anwendungen, die Vue oder kein Framework
nutzen. Jede Komponente gibt es als Vue-Komponente und als Web Component
`<flowaudit-…>`. React-Anwendungen nutzen die native React-Fassung
`@auditcore/ui-react` (Tabelle, Synopse, VVT, DSFA); beide Fassungen teilen
Texte, Verträge, View-Modelle und Zustandsautomaten aus `@auditcore/ui-core`.
Fachdaten kommen über Props oder Ports; das Paket speichert nichts selbst.

## Installation

Standardweg ist die npm-Registry; npm löst die übrigen `@auditcore`-Pakete
der Abhängigkeitshülle selbst auf:

```sh
npm install @auditcore/ui
```

Ohne Registry-Zugang (Intranet, offline) bleibt der signierte Tarball aus
dem GitHub-Release von auditcore; dann gehört jedes Paket der Hülle
ausdrücklich in die `package.json`:

```sh
npm install @auditcore/ui@https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore-ui-0.3.0.tgz
```

Anleitung für Vue, React und Web Components mit Integritätsprüfung und
`vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

Abhängigkeitshülle: dazu `@auditcore/ui-core`, `@auditcore/common` und `@auditcore/kanban-core`; Peer-Abhängigkeit `vue` ^3.5. Stile: immer `@auditcore/ui/style.css`.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @auditcore/ui`).

## Schnellstart

```ts
import { createApp, h } from 'vue'
import { createFlowauditUi, FaTable, formatNumber, type TableColumn } from '@auditcore/ui'
import '@auditcore/ui/style.css'

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
import { defineFlowauditElements } from '@auditcore/ui/elements'
import '@auditcore/ui/style.css'

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
  `@auditcore/common` – `useToast`, `useMediaQuery`, `useClickOutside`,
  `useSort`, `useDebouncedFn`, `useDebouncedRef`, `useThrottledFn` und
  `useAuthToken`. Sie melden ihre Abonnements beim Abbau der Komponente
  (Effekt-Scope) selbst ab.

  ```vue
  <FaTable :columns="columns" :rows="rows" clickable @row-click="open" />
  <KanbanBoard :port="port" board-id="b1" @board-change="save" />
  ```

- **Web Component:** `defineFlowauditElements({ only?, locale? })` aus
  `@auditcore/ui/elements` registriert `<flowaudit-table>`,
  `<flowaudit-kanban-board>`, `<flowaudit-kanban-boards>`,
  `<flowaudit-db-kanban>`, `<flowaudit-sampling>`, `<flowaudit-benford>`,
  `<flowaudit-screening-review>`, `<flowaudit-risk-flags>`,
  `<flowaudit-synopsis>`, `<flowaudit-comparisons>`, `<flowaudit-vvt>`,
  `<flowaudit-dsfa>`, `<flowaudit-geo-map>` und
  `<flowaudit-identifier-check>` im Light DOM
  (kein Shadow DOM, Designtoken der Seite gelten). Objekte und Listen werden
  als JS-Eigenschaften gesetzt, Ereignisse sind `CustomEvent`s in kebab-case
  mit den emit-Argumenten in `detail`. `vue` wird dabei als Abhängigkeit
  mitgeladen.
- **React:** Tabelle, Synopse, VVT, DSFA, Risiko-Merkmale, Screening,
  Stichprobe, Benford und „Kennung prüfen“ nativ in `@auditcore/ui-react` (ohne Vue, gleiche
  Stichprobe, Benford und Dokumentvergleiche nativ in `@auditcore/ui-react` (ohne Vue, gleiche
  Texte und Verträge, Paritätstests gegen diese Fassung), ebenso die
  Geo-Karte, Kanban und die Datenbankansicht.

Fachkomponenten und ihre REST-Verträge:

| Komponente | Element | Zweck | Vertrag |
|---|---|---|---|
| `KanbanBoard`, `KanbanBoardList` | `<flowaudit-kanban-board>`, `<flowaudit-kanban-boards>` | Kanban-Boards über einen `BoardPort` | [`docs/kanban/oberflaeche.md`](../../docs/kanban/oberflaeche.md) |
| `FaSynopsis` | `<flowaudit-synopsis>` | Synopse eines Dokumentvergleichs (Seite an Seite oder fortlaufend, Wortdifferenz, Auswahl und Grund je Zeile, Ausgaben) | [`docs/ui/synopsis-rest.md`](../../docs/ui/synopsis-rest.md) |
| `FaComparisons` | `<flowaudit-comparisons>` | Dokumentvergleiche über `auditcore_documents.web` verwalten: zwei Fassungen (DOCX, DOCM, PDF) hochladen, Standardvergleich oder Gesetzessynopse mit Optionen und Profil, gespeicherte Vergleiche suchen, öffnen (eingebettete Synopse), löschen, fertige Ergebnisse als JSON importieren | [`docs/ui/synopsis-rest.md`](../../docs/ui/synopsis-rest.md) |
| `FaDbKanban` | `<flowaudit-db-kanban>` | Datenbankansicht als Kanban (useDbKanban): Datensätze einer Tabelle nach einer Auswahl-Eigenschaft gruppiert, Spalte „Ohne Wert“, Ablegen oder Strg+Pfeil setzt den Zellwert, Eintrag je Spalte anlegen; Datenquelle als `RecordPort` (`load`, `updateCell`, `addRow`) oder Tabelle mit `table-change` | [`docs/kanban/oberflaeche.md`](../../docs/kanban/oberflaeche.md) |
| `SamplingPanel` | `<flowaudit-sampling>` | Stichprobenumfang und -ziehung über `auditcore_sampling.web` | [`docs/ui/sampling-rest.md`](../../docs/ui/sampling-rest.md) |
| `BenfordPanel` | `<flowaudit-benford>` | Benford-Analyse über `auditcore_statistics.web` | [`docs/ui/benford-rest.md`](../../docs/ui/benford-rest.md) |
| `IdentifierCheck` | `<flowaudit-identifier-check>` | Kennung prüfen über `auditcore_identifiers.web`: IBAN, BIC, USt-IdNr., Steuer-ID, Steuernummer, LEI, Handelsregisternummer mit Prüfprofil, Begründung und Einzelheiten; Stapelprüfung aus CSV/TSV mit Spaltenzuordnung und CSV-Export | [`docs/ui/identifiers-rest.md`](../../docs/ui/identifiers-rest.md) |
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
Exporte der Einstiegspunkte aus `package.json#exports` (804):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@auditcore/ui` | `ACCEPTED_EXTENSIONS` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ANSWER_VALUES` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Activity` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ActivityGroup` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ActorView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AgeKey` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `AllocationMethod` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AllocationRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AllocationResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AnalyseError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AnalyseInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AnalyseRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AnalyseValidation` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AnswerInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AnswerValue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ApiErrorBody` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AreaGeometry` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AssessmentExportFormat` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AssessmentStatus` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AssessmentSummary` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `AssessmentView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BADGE_COLORS` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `BadgeTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordAnalysis` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordBusy` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordCallbacks` | Re-Export | – | `./useBenford` |
| `@auditcore/ui` | `BenfordCatalogue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordDistribution` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordMessageKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordMetricTexts` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordPanel` | Vue-Komponente | – | `benford/BenfordPanel.vue` |
| `@auditcore/ui` | `BenfordPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordSource` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordTest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BenfordTranslate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BlockProgress` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BlockView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Breakdown` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BreakdownRow` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `BreakdownStep` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ButtonSize` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ButtonVariant` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `CARD_COLORS` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `CHANGE_STATUSES` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `COLUMN_COLORS` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `COMPARISON_KINDS` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `COMPARISON_MODES` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `CardAppearance` | Vue-Komponente | – | `kanban/CardAppearance.vue` |
| `@auditcore/ui` | `CardChecklistEditor` | Vue-Komponente | – | `kanban/CardChecklistEditor.vue` |
| `@auditcore/ui` | `CardReferences` | Vue-Komponente | – | `kanban/CardReferences.vue` |
| `@auditcore/ui` | `CardTagsEditor` | Vue-Komponente | – | `kanban/CardTagsEditor.vue` |
| `@auditcore/ui` | `Catalogs` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `CellValue` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `ChartBar` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ChartBox` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ChartGeometry` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ClientExportFormat` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ColumnCheck` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ColumnEditorRow` | Vue-Komponente | – | `kanban/ColumnEditorRow.vue` |
| `@auditcore/ui` | `ColumnPreview` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ColumnView` | Re-Export | – | `./useKanbanBoard` |
| `@auditcore/ui` | `CompareFields` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `CompareForm` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `CompareRow` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Comparison` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonForm` | Vue-Komponente | – | `documents/ComparisonForm.vue` |
| `@auditcore/ui` | `ComparisonKind` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonList` | Vue-Komponente | – | `documents/ComparisonList.vue` |
| `@auditcore/ui` | `ComparisonMetadata` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonMode` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonProfile` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonRow` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonSummary` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonsController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonsData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonsError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonsMessageKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonsPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonsSource` | Schnittstelle | – | `documents/useComparisons` |
| `@auditcore/ui` | `ComparisonsTranslate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ComparisonsView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Completeness` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ConfidenceLevel` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Conformity` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ConformityProfile` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ConformityRow` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ConsolidatedParagraph` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `CoordinateError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DATAPROTECTION_CONTRACT` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DEFAULT_BOX` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DEFAULT_FILTER` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DEFAULT_FORM` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DEFAULT_LOCALE` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DEFAULT_MAX_UPLOAD_BYTES` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DEFAULT_SYNOPSIS_FILTER` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DataProtectionError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DataProtectionKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DataProtectionPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DataProtectionProfile` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DataProtectionTranslate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DatasetFinding` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DbCardView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DbColumnView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DbKanbanCard` | Vue-Komponente | – | `dbkanban/DbKanbanCard.vue` |
| `@auditcore/ui` | `DbKanbanColumn` | Vue-Komponente | – | `dbkanban/DbKanbanColumn.vue` |
| `@auditcore/ui` | `DbKanbanController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DbKanbanData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DbKanbanError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DbKanbanMessageKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DbKanbanSource` | Schnittstelle | – | `dbkanban/useDbKanban` |
| `@auditcore/ui` | `DbKanbanTranslate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DbKanbanView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DecimalSeparator` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `DecisionInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DecisionRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DecisionView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DegenerateRing` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Delimiter` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `DerivationStep` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DiffField` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DiffSegment` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DiffSide` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DistributionRow` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DossierFieldView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `DownloadFile` | Re-Export | – | `./client` |
| `@auditcore/ui` | `DsfaHooks` | Re-Export | – | `./useDsfa` |
| `@auditcore/ui` | `DsfaState` | Schnittstelle | – | `dataprotection/useDsfa` |
| `@auditcore/ui` | `DsfaStep` | Re-Export | – | `./useDsfa` |
| `@auditcore/ui` | `EMPTY_EVALUATION` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `EarthModel` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ElementDefinition` | Schnittstelle | Eine Komponente, die als Web Component `flowaudit-<name>` bereitgestellt wird. | `elements/define` |
| `@auditcore/ui` | `ElementTag` | Typ | – | `elements/define` |
| `@auditcore/ui` | `EntryView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `EvaluateRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Evaluation` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `EvaluationRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `EvaluationResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExportFormat` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExportInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExportPayload` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExportTexts` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExportedFile` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractedField` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionBusy` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionCallbacks` | Re-Export | – | `./useExtraction` |
| `@auditcore/ui` | `ExtractionCatalogue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionFinding` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionMessageKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionOcrSummary` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionProfile` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionRun` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionSource` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtractionValidation` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtrapolationCallbacks` | Re-Export | – | `./useExtrapolation` |
| `@auditcore/ui` | `ExtrapolationCatalogue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtrapolationController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtrapolationData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ExtrapolationPanel` | Vue-Komponente | – | `extrapolation/ExtrapolationPanel.vue` |
| `@auditcore/ui` | `ExtrapolationPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FLAG_STATES` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FaBadge` | Vue-Komponente | – | `base/FaBadge.vue` |
| `@auditcore/ui` | `FaButton` | Vue-Komponente | – | `base/FaButton.vue` |
| `@auditcore/ui` | `FaComparisons` | Vue-Komponente | – | `documents/FaComparisons.vue` |
| `@auditcore/ui` | `FaDbKanban` | Vue-Komponente | – | `dbkanban/FaDbKanban.vue` |
| `@auditcore/ui` | `FaDialog` | Vue-Komponente | – | `base/FaDialog.vue` |
| `@auditcore/ui` | `FaDsfa` | Vue-Komponente | – | `dataprotection/FaDsfa.vue` |
| `@auditcore/ui` | `FaExtraction` | Vue-Komponente | – | `extraction/FaExtraction.vue` |
| `@auditcore/ui` | `FaGeoMap` | Vue-Komponente | – | `geo/FaGeoMap.vue` |
| `@auditcore/ui` | `FaIcon` | Vue-Komponente | – | `base/FaIcon.vue` |
| `@auditcore/ui` | `FaSynopsis` | Vue-Komponente | – | `synopsis/FaSynopsis.vue` |
| `@auditcore/ui` | `FaTable` | Vue-Komponente | – | `table/FaTable.vue` |
| `@auditcore/ui` | `FaTextField` | Vue-Komponente | – | `base/FaTextField.vue` |
| `@auditcore/ui` | `FaVvt` | Vue-Komponente | – | `dataprotection/FaVvt.vue` |
| `@auditcore/ui` | `FetchLike` | Re-Export | – | `./client` |
| `@auditcore/ui` | `FieldEntry` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FieldError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FieldErrorCode` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FieldKind` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FieldUse` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FieldValue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FieldView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FilterOptions` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FindingView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FlagEntry` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FlagHit` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FlagState` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FlowauditUiOptions` | Schnittstelle | – | `plugin` |
| `@auditcore/ui` | `FormatProfile` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FreshnessStatus` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `FreshnessView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `GeoArea` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `GeoBusy` | Re-Export | – | `./useGeoMap` |
| `@auditcore/ui` | `GeoCatalogue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `GeoHint` | Re-Export | – | `./useGeoMap` |
| `@auditcore/ui` | `GeoMapCallbacks` | Re-Export | – | `./useGeoMap` |
| `@auditcore/ui` | `GeoPackageArea` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `GeoPackageResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `GeoPoint` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `GeoPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `GeoRestOptions` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `GeocodeHit` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `GeocodeResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `HitFilter` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `HitView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ICONS` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `INITIAL_BENFORD` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `INITIAL_EXTRACTION` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `INITIAL_EXTRAPOLATION` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `INITIAL_REPORTING` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `INITIAL_SAMPLING` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `IconName` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `IdentifierBatchAnswer` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `IdentifierCallbacks` | Re-Export | – | `./useIdentifierCheck` |
| `@auditcore/ui` | `IdentifierCatalogue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `IdentifierCheck` | Vue-Komponente | – | `identifiers/IdentifierCheck.vue` |
| `@auditcore/ui` | `IdentifierController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `IdentifierData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `IdentifierResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `IdentifiersPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ImportRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ImportedColumns` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `JsonObject` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `JsonValue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `KanbanBoard` | Vue-Komponente | – | `kanban/KanbanBoard.vue` |
| `@auditcore/ui` | `KanbanBoardList` | Vue-Komponente | – | `kanban/KanbanBoardList.vue` |
| `@auditcore/ui` | `KanbanBoardOptions` | Schnittstelle | – | `kanban/useKanbanBoard` |
| `@auditcore/ui` | `KanbanCard` | Vue-Komponente | – | `kanban/KanbanCard.vue` |
| `@auditcore/ui` | `KanbanCardDetail` | Vue-Komponente | – | `kanban/KanbanCardDetail.vue` |
| `@auditcore/ui` | `KanbanColumn` | Vue-Komponente | – | `kanban/KanbanColumn.vue` |
| `@auditcore/ui` | `KanbanSettingsDialog` | Vue-Komponente | – | `kanban/KanbanSettingsDialog.vue` |
| `@auditcore/ui` | `KanbanShareDialog` | Vue-Komponente | – | `kanban/KanbanShareDialog.vue` |
| `@auditcore/ui` | `KanbanToolbar` | Vue-Komponente | – | `kanban/KanbanToolbar.vue` |
| `@auditcore/ui` | `KeyTitle` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `LOCALES` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `LOCALE_KEY` | Konstante | – | `i18n/i18n` |
| `@auditcore/ui` | `LatLon` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `LevelTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `LevelView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ListInfo` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Locale` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `LocateRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `LocateResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `LogEntry` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `LogView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `MAX_CARD_IMAGE_BYTES` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `MeasureView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `MessageParams` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `MethodGroup` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `MethodKind` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `MethodProfile` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `MethodStatus` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `MovePreview` | Re-Export | – | `./movePreview` |
| `@auditcore/ui` | `NamedOption` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `NextSortOptions` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `NumberColumn` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `Outcome` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `OverviewRow` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `PRIORITY_TONES` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `ParameterSpec` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ParsedTable` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `Person` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `PopulationItem` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Position` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `PriorityTone` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `ProfileDetail` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ProfileReference` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ProfileStatus` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ProfileSummary` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ProfileView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Proposal` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `QuestionView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ROW_STATUSES` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RadiusHit` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RadiusRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RadiusResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RecordMove` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RecordPort` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `RecordProperty` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `RecordRow` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `RecordTable` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `RecordValue` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `RecordView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RegisterColumn` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RegisterContent` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RegisterExportFormat` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RegisterExportInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RegisterIssue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RegisterState` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RegisterStatus` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RelativeKey` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `ReportCell` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportColumnType` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportExportPanel` | Vue-Komponente | – | `reporting/ReportExportPanel.vue` |
| `@auditcore/ui` | `ReportTableInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportingBusy` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportingCallbacks` | Re-Export | – | `./useReportExport` |
| `@auditcore/ui` | `ReportingCatalogue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportingController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportingData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportingError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportingMessageKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportingPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportingSource` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReportingTranslate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ResidualRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ResidualResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RestClientOptions` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RestError` | Re-Export | – | `./client` |
| `@auditcore/ui` | `RestOptions` | Re-Export | – | `./client` |
| `@auditcore/ui` | `ReviewEvents` | Re-Export | – | `./useScreeningReview` |
| `@auditcore/ui` | `ReviewStatus` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ReviewView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RiskController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RiskData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RiskDistributionRow` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RiskFilter` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RiskFlagCard` | Vue-Komponente | – | `risk/RiskFlagCard.vue` |
| `@auditcore/ui` | `RiskFlagFilter` | Vue-Komponente | – | `risk/RiskFlagFilter.vue` |
| `@auditcore/ui` | `RiskFlagState` | Vue-Komponente | – | `risk/RiskFlagState.vue` |
| `@auditcore/ui` | `RiskFlagSummary` | Vue-Komponente | – | `risk/RiskFlagSummary.vue` |
| `@auditcore/ui` | `RiskFlagTable` | Vue-Komponente | – | `risk/RiskFlagTable.vue` |
| `@auditcore/ui` | `RiskFlags` | Vue-Komponente | – | `risk/RiskFlags.vue` |
| `@auditcore/ui` | `RiskInputs` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RiskMessageKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RiskPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RiskProfileInfo` | Vue-Komponente | – | `risk/RiskProfileInfo.vue` |
| `@auditcore/ui` | `RiskRecordDetail` | Vue-Komponente | – | `risk/RiskRecordDetail.vue` |
| `@auditcore/ui` | `RiskSelection` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RiskTranslate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RowStatus` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RowUpdate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RowView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RuleView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RunQuery` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RunRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RunRequestRecord` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RunSummary` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `RunView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Runner` | Schnittstelle | – | `rest/runner` |
| `@auditcore/ui` | `SCREENING_CONTRACT` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `STATE_FILTER_KEYS` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `STATE_ICONS` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `STATE_KEYS` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SamplingBusy` | Re-Export | – | `./useSampling` |
| `@auditcore/ui` | `SamplingCallbacks` | Re-Export | – | `./useSampling` |
| `@auditcore/ui` | `SamplingCatalogue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SamplingController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SamplingData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SamplingMessageKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SamplingPanel` | Vue-Komponente | – | `sampling/SamplingPanel.vue` |
| `@auditcore/ui` | `SamplingPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SamplingSource` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SamplingTranslate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ScenarioInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ScenarioResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ScoreClass` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ScreeningController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ScreeningData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ScreeningError` | Re-Export | – | `./useScreeningReview` |
| `@auditcore/ui` | `ScreeningKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ScreeningKind` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ScreeningPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ScreeningReview` | Vue-Komponente | – | `screening/ScreeningReview.vue` |
| `@auditcore/ui` | `ScreeningReviewState` | Schnittstelle | – | `screening/useScreeningReview` |
| `@auditcore/ui` | `ScreeningSelection` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ScreeningTranslate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SecondReviewRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SecondReviewView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SegmentKind` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SelectionError` | Re-Export | – | `./useSampling` |
| `@auditcore/ui` | `SelectionInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SelectionRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SelectionResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SelectionRow` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SelectionTexts` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SelectionValidation` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SelectionVariant` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ServerExportFormat` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SettingsView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Severity` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ShortValues` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SimplifyRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SimplifyResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SimplifyUnit` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SizeRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SizeResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SizeValidation` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SortDirection` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `SortState` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `SourceView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SourcesView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `StateFilter` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `StratumCount` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `StratumInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `StratumResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SubjectInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SubjectRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SubjectStatus` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SubjectView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SummaryView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SurveyInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SynopsisFilterState` | Re-Export | – | `./useSynopsis` |
| `@auditcore/ui` | `SynopsisLayout` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SynopsisMessageKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SynopsisPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SynopsisRestClient` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SynopsisRowFilter` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SynopsisSource` | Schnittstelle | Eingaben der Komponente, als Getter übergeben (Props bleiben reaktiv). | `synopsis/useSynopsis` |
| `@auditcore/ui` | `SynopsisTranslate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `SynopsisView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `TOLERANCE_STEPS` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `TabItem` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `TableColumn` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `TableImport` | Vue-Komponente | – | `tabular/TableImport.vue` |
| `@auditcore/ui` | `TableImportController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `TableImportData` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `TablePreview` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `TableRow` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `TabularMessageKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ThemeMode` | Typ | – | `theme/theme` |
| `@auditcore/ui` | `TileSource` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Tone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Totals` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `Translate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `UnitInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `UseAuthToken` | Schnittstelle | – | `composables/useAuthToken` |
| `@auditcore/ui` | `UseBenford` | Schnittstelle | – | `benford/useBenford` |
| `@auditcore/ui` | `UseComparisons` | Schnittstelle | – | `documents/useComparisons` |
| `@auditcore/ui` | `UseDbKanban` | Schnittstelle | – | `dbkanban/useDbKanban` |
| `@auditcore/ui` | `UseExtraction` | Schnittstelle | – | `extraction/useExtraction` |
| `@auditcore/ui` | `UseExtrapolation` | Schnittstelle | – | `extrapolation/useExtrapolation` |
| `@auditcore/ui` | `UseGeoMap` | Schnittstelle | – | `geo/useGeoMap` |
| `@auditcore/ui` | `UseI18n` | Schnittstelle | – | `i18n/i18n` |
| `@auditcore/ui` | `UseIdentifierCheck` | Schnittstelle | – | `identifiers/useIdentifierCheck` |
| `@auditcore/ui` | `UseReportExport` | Schnittstelle | – | `reporting/useReportExport` |
| `@auditcore/ui` | `UseRiskFlags` | Schnittstelle | – | `risk/useRiskFlags` |
| `@auditcore/ui` | `UseSampling` | Schnittstelle | – | `sampling/useSampling` |
| `@auditcore/ui` | `UseSort` | Schnittstelle | – | `composables/useSort` |
| `@auditcore/ui` | `UseSortOptions` | Schnittstelle | – | `composables/useSort` |
| `@auditcore/ui` | `UseSynopsis` | Schnittstelle | – | `synopsis/useSynopsis` |
| `@auditcore/ui` | `UseSynopsisExport` | Schnittstelle | – | `synopsis/useSynopsisExport` |
| `@auditcore/ui` | `UseSynopsisNavigation` | Schnittstelle | – | `synopsis/useSynopsisNavigation` |
| `@auditcore/ui` | `UseTableImport` | Schnittstelle | – | `tabular/useTableImport` |
| `@auditcore/ui` | `UseTheme` | Schnittstelle | – | `theme/theme` |
| `@auditcore/ui` | `UseToast` | Schnittstelle | – | `composables/useToast` |
| `@auditcore/ui` | `UtmInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `UtmInputError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `UtmPointRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `UtmPointResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `UtmRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `UtmResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `VersionSummary` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `VersionView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ViewMessage` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ViewOptions` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `VvtExport` | Re-Export | – | `./useVvt` |
| `@auditcore/ui` | `VvtExportFormat` | Re-Export | – | `./useVvt` |
| `@auditcore/ui` | `VvtHooks` | Re-Export | – | `./useVvt` |
| `@auditcore/ui` | `VvtState` | Schnittstelle | – | `dataprotection/useVvt` |
| `@auditcore/ui` | `WORD_LIMIT` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `WhenMissingColumns` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `WorkbookPreview` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `WorkbookRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `acceptsHit` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `activityKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `addScenario` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `analyseErrorKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `answerOf` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `applyPreview` | Re-Export | – | `./movePreview` |
| `@auditcore/ui` | `applyRowOverrides` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `applyTheme` | Funktion | Setzt das Farbschema am Element (Standard: Dokumentwurzel); 'system' folgt dem Betriebssystem. | `theme/theme` |
| `@auditcore/ui` | `areasFromGeoPackage` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ariaSort` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `axisMaximum` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `badgePrefix` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `badgeStyle` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `bandTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `baseMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `benfordBarTitle` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `benfordChartTitle` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `benfordDigitColumns` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `benfordDigitRows` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `benfordElement` | Konstante | `<flowaudit-benford>`: Eigenschaften `port` (BenfordPort), `values`, `locale`; Ereignisse `analysis-completed`, `error`. | `benford/element` |
| `@auditcore/ui` | `benfordMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `benfordMetricTexts` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `benfordProfile` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `benfordTickText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `benfordValues` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `benfordValuesText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `blockProgress` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `breakdownRows` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `buildAnalyseRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `buildEvaluationRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `buildResidualRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `buildRowView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `buildSelectionRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `buildSizeRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `buildSynopsisView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `buildWorkbookRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `cardAge` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `cardStyle` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `cellText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `changeIds` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `chartGeometry` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `cloneContent` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `codeLabel` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `columnCells` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `compareValues` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `comparisonRows` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `comparisonsElement` | Konstante | `<flowaudit-comparisons>`: `port` als JS-Eigenschaft (z. B. | `documents/element` |
| `@auditcore/ui` | `comparisonsMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `comparisonsView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `completeness` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `completenessTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `conclusionLabel` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `conclusionTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `confidenceText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `coverIssues` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createBenfordController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createBenfordRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createComparisonsController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createDataProtectionRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createDbKanbanController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createExtractionController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createExtractionRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createExtrapolationController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createExtrapolationRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createFlowauditUi` | Funktion | Vue-Plugin: stellt die Sprache app-weit bereit. | `plugin` |
| `@auditcore/ui` | `createGeoRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createIdentifierController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createIdentifiersRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createMemoryRecordPort` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `createReportingController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createReportingRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createRiskController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createRiskRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createRunner` | Funktion | Gemeinsamer Ablauf für Portanfragen: Beschäftigt-Status, Fehlermeldung, Rückruf. | `rest/runner` |
| `@auditcore/ui` | `createSamplingController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createSamplingRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createScreeningController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createScreeningRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createSynopsisRestClient` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `createTableImportController` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `currentVersion` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `dataprotectionError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `dataprotectionMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `dbKanbanElement` | Konstante | `<flowaudit-db-kanban>`: `port` (RecordPort) oder `table` als JS-Eigenschaft; Ereignisse `record-move`, `record-add`, `table-change`, `update:groupBy`, `error`. | `dbkanban/element` |
| `@auditcore/ui` | `dbKanbanMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `dbKanbanView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `decisionTitle` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `defineMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `derivationColumns` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `derivationRows` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `detectDecimal` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `detectDelimiter` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `diffSegments` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `digitLabel` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `displayName` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `displayValue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `distribution` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `downloadText` | Re-Export | – | `./useSynopsisExport` |
| `@auditcore/ui` | `dsfaElement` | Konstante | `<flowaudit-dsfa>`: Eigenschaften `port`, `activityId`, `actor`, `editable`, `locale`; Ereignisse `assessment-change`, `error`. | `dataprotection/element` |
| `@auditcore/ui` | `editedBy` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `emptyActivity` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `emptyContent` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `emptyFilter` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `emptyScenario` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `escapeHtml` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `escapeMarkdown` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `evaluationRules` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `excludedLines` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `exportFilename` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `extractionElement` | Konstante | `<flowaudit-extraction>`: Eigenschaften `port` (ExtractionPort), `result`, `locale`; Ereignisse `extraction-completed`, `error`. | `extraction/element` |
| `@auditcore/ui` | `extractionMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `extractionValidation` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `extrapolationElement` | Konstante | `<flowaudit-extrapolation>`: Eigenschaften `port` (ExtrapolationPort), `strata`, `units`, `locale`; Ereignisse `evaluation-completed`, `residual-computed`, `error`. | `extrapolation/element` |
| `@auditcore/ui` | `extrapolationMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `extrapolationMethod` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `fieldIssues` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `fieldValue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `fileSize` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `filterOptions` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `filterRecords` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `filterRows` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `filterSubjects` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `filterSummaries` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `flagState` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `focusRow` | Re-Export | – | `./useSynopsisNavigation` |
| `@auditcore/ui` | `focusableWithin` | Re-Export | – | `./useFocusTrap` |
| `@auditcore/ui` | `formProblems` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `formatAmount` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `formatDate` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `formatDegrees` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `formatDistance` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `formatMetres` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `formatNumber` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `formatPercent` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `formatShare` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `formatValue` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `geoMapElement` | Konstante | `<flowaudit-geo-map>`: Eigenschaften `port` (GeoPort), `points`, `areas`, `tiles` (TileSource), `center`, `zoom`, `locale`; Ereignisse `radius-completed`, `location-checked`, `area … | `geo/element` |
| `@auditcore/ui` | `geoMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `groupByDepartment` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `groupRecords` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `guessNumberColumn` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `hasPartialStrata` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `identifierCheckElement` | Konstante | `<flowaudit-identifier-check>`: Eigenschaften `port` (IdentifiersPort), `locale`; Ereignisse `identifier-checked`, `batch-checked`, `error`. | `identifiers/element` |
| `@auditcore/ui` | `identifierMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `importDelimiterText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `importOptionalColumn` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `importPreview` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `importRejectedLines` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `initialTexts` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `initials` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `interpolate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `isDeviation` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `isIconName` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `isLocale` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `isPercent` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `isStratifiedPopulation` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `issuesFor` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `itemsFromImport` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `kanbanBoardElement` | Konstante | `<flowaudit-kanban-board>`: Eigenschaften `port` (BoardPort) und `boardId` oder `board` (+ `userId`) für lokale Bearbeitung; Ereignisse `board-change`, `error`, `fullscreen`, `navi … | `kanban/element` |
| `@auditcore/ui` | `kanbanBoardListElement` | Konstante | `<flowaudit-kanban-boards>`: Boardliste mit Eigenschaft `port`; Ereignisse `board-select`, `created`. | `kanban/element` |
| `@auditcore/ui` | `kanbanDialogMessages` | Re-Export | – | `./messages` |
| `@auditcore/ui` | `kanbanMessages` | Re-Export | – | `./messages` |
| `@auditcore/ui` | `lcsOperations` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `levelLabel` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `levelTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `localeTag` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `mayRelease` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `methodGroups` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `methodStatusKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `methodTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `ndiffOperations` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `needsShortValues` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `nextOpenHit` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `nextSort` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `numberColumn` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `pairs` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parameterLabel` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parameterUnit` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parseConditions` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parseCount` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parseDegrees` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parseImport` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parseInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parseLatLon` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parseMetres` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parseNumber` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `parseSubjects` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `parseTable` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `parseUtm` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `placementFor` | Re-Export | – | `./movePreview` |
| `@auditcore/ui` | `plainSegments` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `populationSuggestions` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `populationText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `positionText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `positiveSum` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `preview` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `printHtml` | Re-Export | – | `./useSynopsisExport` |
| `@auditcore/ui` | `profileHintText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `profileStatusText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `provideLocale` | Funktion | Stellt die Sprache für alle Nachfahren bereit (App-Ebene oder Teilbaum). | `i18n/i18n` |
| `@auditcore/ui` | `readTheme` | Funktion | Liest das explizit gesetzte Farbschema; ohne Attribut 'system'. | `theme/theme` |
| `@auditcore/ui` | `recommendationTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `recordEntries` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `recordLabel` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `recordRules` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `registerCsv` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `registerFilename` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `registerHtml` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `registerMarkdown` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `relativeTime` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `removeScenario` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `reportCellText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `reportExportElement` | Konstante | `<flowaudit-report-export>`: Eigenschaften `port` (ReportingPort), `tables`, `filename`, `locale`; Ereignisse `preview-completed`, `export-completed`, `error`. | `reporting/element` |
| `@auditcore/ui` | `reportingErrorKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `reportingMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `reportingProfile` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `reportingSampleNote` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `reportingSheetHeading` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `reportingTablesText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `reportingWorkbookText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `requestFile` | Re-Export | – | `./client` |
| `@auditcore/ui` | `requestJson` | Re-Export | – | `./client` |
| `@auditcore/ui` | `requirementKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `residualMetrics` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `resolvedTheme` | Funktion | Tatsächlich wirksames Schema, auch wenn 'system' gewählt ist. | `theme/theme` |
| `@auditcore/ui` | `riskFlagsElement` | Konstante | `<flowaudit-risk-flags>`: Eigenschaften `evaluation` (Antwort von `POST /evaluate`) und `profile` (Antwort von `GET /profiles/{id}/{version}`) als JS-Objekte; Ereignisse `record-se … | `risk/element` |
| `@auditcore/ui` | `riskMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `riskTableColumns` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `riskTableRows` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `sameSurvey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `samplingElement` | Konstante | `<flowaudit-sampling>`: Eigenschaften `port` (SamplingPort), `items` (Grundgesamtheit), `locale`; Ereignisse `size-calculated`, `selection-drawn`, `error`. | `sampling/element` |
| `@auditcore/ui` | `samplingFieldError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `samplingInputNumber` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `samplingMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `samplingPopulation` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `samplingProfile` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `saveFile` | Re-Export | – | `./download` |
| `@auditcore/ui` | `screeningMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `screeningReviewElement` | Konstante | `<flowaudit-screening-review>`: Eigenschaften `port` (ScreeningPort), `runId`, `locale`; Ereignisse `run-created`, `decided`, `error`. | `screening/element` |
| `@auditcore/ui` | `screeningTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `segmentsText` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `selectRisk` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `selectScreening` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `selectionColumns` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `selectionErrorKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `selectionRows` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `selectionTexts` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `setDefaultLocale` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `severityTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `sharedToastQueue` | Funktion | Anwendungsweite Warteschlange (einmal je Seite). | `composables/useToast` |
| `@auditcore/ui` | `sizeTexts` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `sortRows` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `splitLine` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui` | `stateTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `statusHintKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `statusKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `statusLabel` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `statusTone` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `stepChange` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `strataColumns` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `strataOf` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `strataRows` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `summaryView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `surveyFrom` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `synopsisElement` | Konstante | `<flowaudit-synopsis>`: `comparison`/`result` und `port` als JS-Eigenschaften; Ereignisse `row-update`, `export`, `navigate`, `update:layout`. | `synopsis/element` |
| `@auditcore/ui` | `synopsisMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `synopsisPortOf` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `tableElement` | Konstante | `<flowaudit-table>`: Spalten und Zeilen als JS-Eigenschaften, Ereignisse `row-click`, `sort-change`. | `table/element` |
| `@auditcore/ui` | `tabularMessages` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `terMetrics` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `textOn` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui` | `toCompareFields` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `toHtml` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `toMarkdown` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `toggleMeasure` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `totals` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `translate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `triggeredDataset` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `useAuthToken` | Funktion | Reaktiver Zugriff auf einen `TokenStore` aus `@auditcore/common`. | `composables/useAuthToken` |
| `@auditcore/ui` | `useBenford` | Funktion | Vue-Anbindung der Benford-Analyse aus `@auditcore/ui-core` (`createBenfordController`). | `benford/useBenford` |
| `@auditcore/ui` | `useClickOutside` | Funktion | Ruft `handler` bei Klick außerhalb der Elemente (Template-Refs) und bei Escape; abgemeldet beim Aufräumen. | `composables/useDom` |
| `@auditcore/ui` | `useComparisons` | Funktion | – | `documents/useComparisons` |
| `@auditcore/ui` | `useDbKanban` | Funktion | – | `dbkanban/useDbKanban` |
| `@auditcore/ui` | `useDebouncedFn` | Funktion | Entprellte Funktion; ein ausstehender Aufruf wird beim Abbau der Komponente verworfen. | `composables/useDebounced` |
| `@auditcore/ui` | `useDebouncedRef` | Funktion | Folgt `source` erst nach `ms` Ruhe (z. B. Suchfeld → Anfrage). | `composables/useDebounced` |
| `@auditcore/ui` | `useDsfa` | Funktion | – | `dataprotection/useDsfa` |
| `@auditcore/ui` | `useExtraction` | Funktion | Vue-Anbindung der Belegerkennung aus `@auditcore/ui-core` (`createExtractionController`). | `extraction/useExtraction` |
| `@auditcore/ui` | `useExtrapolation` | Funktion | Vue-Anbindung der Hochrechnung aus `@auditcore/ui-core` (`createExtrapolationController`). | `extrapolation/useExtrapolation` |
| `@auditcore/ui` | `useFocusTrap` | Funktion | Hält den Tastaturfokus im Container, solange `active` wahr ist, und gibt ihn danach an das zuvor fokussierte Element zurück. | `composables/useFocusTrap` |
| `@auditcore/ui` | `useGeoMap` | Funktion | Zustand und Abläufe der Geo-Karte; jede Berechnung läuft über den Port. | `geo/useGeoMap` |
| `@auditcore/ui` | `useI18n` | Funktion | Composable für Komponenten. `override` (z. B. eine Prop `locale`) hat Vorrang vor der bereitgestellten Sprache. | `i18n/i18n` |
| `@auditcore/ui` | `useId` | Funktion | Eindeutige, stabile ID je Komponenteninstanz für aria-Verknüpfungen. | `composables/useId` |
| `@auditcore/ui` | `useIdentifierCheck` | Funktion | Vue-Anbindung von „Kennung prüfen“ aus `@auditcore/ui-core` (`createIdentifierController`). | `identifiers/useIdentifierCheck` |
| `@auditcore/ui` | `useKanbanActions` | Funktion | – | `kanban/useKanbanActions` |
| `@auditcore/ui` | `useKanbanBoard` | Funktion | – | `kanban/useKanbanBoard` |
| `@auditcore/ui` | `useKanbanFilter` | Funktion | Such- und Filterzustand des Boards (Toolbar) als CardFilter der Kernlogik. | `kanban/useKanbanFilter` |
| `@auditcore/ui` | `useLocale` | Funktion | – | `i18n/i18n` |
| `@auditcore/ui` | `useMediaQuery` | Funktion | Reaktiver Stand einer Media-Query, z. B. `useMediaQuery('(max-width: 768px)')`. | `composables/useDom` |
| `@auditcore/ui` | `useMoveController` | Funktion | – | `kanban/useMoveController` |
| `@auditcore/ui` | `useReportExport` | Funktion | Vue-Anbindung des Tabellenexports aus `@auditcore/ui-core` (`createReportingController`). | `reporting/useReportExport` |
| `@auditcore/ui` | `useRiskFlags` | Funktion | Vue-Anbindung des Zustandsautomaten aus `@auditcore/ui-core` (Filter, Auswahl, abgeleitete Daten). | `risk/useRiskFlags` |
| `@auditcore/ui` | `useRiskProfile` | Funktion | Profilbeschreibung zur Auswertung: die übergebene, sonst über den Port nachgeladen (Profil und Version der Auswertung, nie ein Standardprofil). | `risk/useRiskProfile` |
| `@auditcore/ui` | `useSampling` | Funktion | Vue-Anbindung des Stichprobenrechners aus `@auditcore/ui-core` (`createSamplingController`); Getter halten Props reaktiv. | `sampling/useSampling` |
| `@auditcore/ui` | `useScreeningReview` | Funktion | Stand, Auswahl und Aktionen der Trefferprüfung; die Logik liegt im Kern (`createScreeningController`). | `screening/useScreeningReview` |
| `@auditcore/ui` | `useSort` | Funktion | Sortierzustand und sortierte Zeilen für eigene Tabellen (FaTable sortiert selbst). | `composables/useSort` |
| `@auditcore/ui` | `useStore` | Funktion | Stand eines Kern-Controllers (`@auditcore/ui-core`) als reaktive Vue-Referenz. | `composables/useStore` |
| `@auditcore/ui` | `useSynopsis` | Funktion | Vue-Anbindung des Zustandsautomaten aus `@auditcore/ui-core` (Laden, Filter, Zeilenänderungen, Navigation). | `synopsis/useSynopsis` |
| `@auditcore/ui` | `useSynopsisExport` | Funktion | Exporte der sichtbaren, ausgewählten Zeilen; `onExport` erhält jedes Ergebnis. | `synopsis/useSynopsisExport` |
| `@auditcore/ui` | `useSynopsisNavigation` | Funktion | Navigation zwischen Änderungen mit Schaltflächen und Tasten N/J bzw. P/K. | `synopsis/useSynopsisNavigation` |
| `@auditcore/ui` | `useTableImport` | Funktion | Vue-Anbindung des Datei-Imports aus `@auditcore/ui-core` (Datei lesen, Spalten zuordnen, Vorschau). | `tabular/useTableImport` |
| `@auditcore/ui` | `useTheme` | Funktion | Composable: reaktives Farbschema, synchron mit dem Attribut am Element. | `theme/theme` |
| `@auditcore/ui` | `useThrottledFn` | Funktion | Gedrosselte Funktion; ein ausstehender Aufruf wird beim Abbau der Komponente verworfen. | `composables/useDebounced` |
| `@auditcore/ui` | `useToast` | Funktion | Toasts als reaktive Liste über der framework-freien Warteschlange aus `@auditcore/common`. | `composables/useToast` |
| `@auditcore/ui` | `useVvt` | Funktion | – | `dataprotection/useVvt` |
| `@auditcore/ui` | `utmErrorKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `validateDecision` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `vertexCount` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `vvtElement` | Konstante | `<flowaudit-vvt>`: Eigenschaften `port` (DataProtectionPort), `actor`, `editable`, `locale`; Ereignisse `draft-saved`, `released`, `exported`, `error`. | `dataprotection/element` |
| `@auditcore/ui` | `whenMissingKey` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `wholeSegments` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `withActivity` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `withAnswer` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `withDepartments` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `withField` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `withJustification` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `withPerson` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `withScenario` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui` | `withoutActivity` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui/elements` | `DefineOptions` | Schnittstelle | – | `elements` |
| `@auditcore/ui/elements` | `ELEMENTS` | Konstante | Alle Web Components von | `registry` |
| `@auditcore/ui/elements` | `ElementDefinition` | Schnittstelle | Eine Komponente, die als Web Component `flowaudit-<name>` bereitgestellt wird. | `elements/define` |
| `@auditcore/ui/elements` | `ElementTag` | Typ | – | `elements/define` |
| `@auditcore/ui/elements` | `defineElement` | Funktion | Registriert eine Komponente als Custom Element im Light DOM (kein Shadow DOM): Designtoken und `@auditcore/ui/style.css` der Seite gelten direkt. | `elements/define` |
| `@auditcore/ui/elements` | `defineElements` | Funktion | – | `elements/define` |
| `@auditcore/ui/elements` | `defineFlowauditElements` | Funktion | – | `elements` |

Web Components:

| Element | Vue-Komponente | Definiert in |
|---|---|---|
| `<flowaudit-benford>` | `BenfordPanel` | `benford/element.ts` |
| `<flowaudit-comparisons>` | `FaComparisons` | `documents/element.ts` |
| `<flowaudit-db-kanban>` | `FaDbKanban` | `dbkanban/element.ts` |
| `<flowaudit-dsfa>` | `FaDsfa` | `dataprotection/element.ts` |
| `<flowaudit-extraction>` | `FaExtraction` | `extraction/element.ts` |
| `<flowaudit-extrapolation>` | `ExtrapolationPanel` | `extrapolation/element.ts` |
| `<flowaudit-geo-map>` | `FaGeoMap` | `geo/element.ts` |
| `<flowaudit-identifier-check>` | `IdentifierCheck` | `identifiers/element.ts` |
| `<flowaudit-kanban-board>` | `KanbanBoard` | `kanban/element.ts` |
| `<flowaudit-kanban-boards>` | `KanbanBoardList` | `kanban/element.ts` |
| `<flowaudit-report-export>` | `ReportExportPanel` | `reporting/element.ts` |
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

#### `CardAppearance`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `color` | `string \| null` | ja | – | – |
| `image` | `string \| null` | ja | – | – |
| `readOnly` | `boolean` | nein | `false` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `change` | `[patch: { color?: string; image?: string }]` | – |

#### `CardChecklistEditor`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `items` | `readonly ChecklistItem[]` | ja | – | – |
| `readOnly` | `boolean` | nein | `false` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `change` | `[items: ChecklistItem[]]` | – |

#### `CardReferences`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `links` | `readonly CardLink[]` | ja | – | – |
| `attachments` | `readonly Attachment[]` | ja | – | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `navigate` | `[link: CardLink]` | – |
| `attachment` | `[attachment: Attachment]` | – |

#### `CardTagsEditor`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `tags` | `readonly string[]` | ja | – | – |
| `readOnly` | `boolean` | nein | `false` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `change` | `[tags: string[]]` | – |

#### `ColumnEditorRow`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `column` | `Column` | ja | – | – |
| `first` | `boolean` | nein | `false` | – |
| `last` | `boolean` | nein | `false` | – |
| `canRemove` | `boolean` | nein | `true` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update` | `[patch: Partial<Column>]` | – |
| `remove` | `[]` | – |
| `move` | `[step: -1 \| 1]` | – |

#### `ComparisonForm`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `form` | `CompareForm` | ja | – | – |
| `view` | `ComparisonsView` | ja | – | – |
| `busy` | `boolean` | nein | `false` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `form-update` | `[patch: Partial<CompareForm>]` | – |
| `section-toggle` | `[status: RowStatus, enabled: boolean]` | – |
| `form-submit` | `[]` | – |
| `form-reset` | `[]` | – |

#### `ComparisonList`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `rows` | `SummaryView[]` | nein | `() => []` | – |
| `query` | `string` | nein | `''` | – |
| `countText` | `string` | nein | `''` | – |
| `emptyText` | `string \| null` | nein | `null` | – |
| `busy` | `boolean` | nein | `false` | – |
| `editable` | `boolean` | nein | `true` | Löschen und Import anbieten. |
| `canImport` | `boolean` | nein | `false` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `update:query` | `[query: string]` | – |
| `comparison-open` | `[id: string]` | – |
| `comparison-remove` | `[id: string]` | – |
| `result-import` | `[text: string]` | – |

#### `DbKanbanCard`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `card` | `DbCardView` | ja | – | – |
| `columnLabel` | `string` | ja | – | – |
| `editable` | `boolean` | nein | `true` | – |
| `dragging` | `boolean` | nein | `false` | – |
| `describedBy` | `string` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `card-drag` | `[id: string \| null]` | – |
| `card-step` | `[id: string, direction: 1 \| -1]` | – |

#### `DbKanbanColumn`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `column` | `DbColumnView` | ja | – | – |
| `editable` | `boolean` | nein | `true` | – |
| `canAdd` | `boolean` | nein | `false` | – |
| `dragging` | `string \| null` | nein | `null` | – |
| `over` | `boolean` | nein | `false` | – |
| `hintId` | `string` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `card-drag` | `[id: string \| null]` | – |
| `card-step` | `[id: string, direction: 1 \| -1]` | – |
| `card-drop` | `[id: string, column: string]` | – |
| `column-over` | `[column: string \| null]` | – |
| `card-add` | `[column: string]` | – |

#### `ExtrapolationPanel`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `ExtrapolationPort \| null` | nein | `null` | Fachlogik, z. B. `createExtrapolationRestPort({ baseUrl: '/api/extrapolation' })`. |
| `strata` | `readonly StratumInput[]` | nein | `() => []` | Schichten der Grundgesamtheit (vorbelegt, in der Komponente bearbeitbar). |
| `units` | `readonly UnitInput[]` | nein | `() => []` | Geprüfte Einheiten der Stichprobe mit ihren Fehlern. |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `evaluation-completed` | `[result: EvaluationResult]` | – |
| `residual-computed` | `[result: ResidualResult]` | – |
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

#### `FaComparisons`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `ComparisonsPort \| null` | nein | `null` | Datenzugang, z. B. `createSynopsisRestClient({ baseUrl: '/api/synopsis' })` (auditcore_documents.web). |
| `maxUploadBytes` | `number` | nein | `DEFAULT_MAX_UPLOAD_BYTES` | Größte Datei je Seite in Byte; wie `ServiceSettings.max_upload_bytes` des Servers. |
| `editable` | `boolean` | nein | `true` | `false`: nur Liste und Ansicht, kein Hochladen, Import oder Löschen. |
| `showSynopsis` | `boolean` | nein | `true` | Geöffneten Vergleich als Synopse einbetten (braucht `port.load`); sonst nur Ereignis `comparison-open`. |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `comparison-created` | `[comparison: Comparison]` | – |
| `comparison-imported` | `[comparison: Comparison]` | – |
| `comparison-removed` | `[id: string]` | – |
| `comparison-open` | `[id: string]` | – |
| `error` | `[error: ComparisonsError]` | – |

#### `FaDbKanban`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `RecordPort \| null` | nein | `null` | Datenquelle (Datenbank/REST der Anwendung) mit `load`, `updateCell` und optional `addRow`. |
| `table` | `RecordTable \| null` | nein | `null` | Ohne Port: Tabelle direkt übergeben; Änderungen kommen als Ereignis `table-change` zurück. |
| `editable` | `boolean` | nein | `true` | `false`: nur Ansicht, kein Verschieben und Anlegen. |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `record-move` | `[move: RecordMove]` | – |
| `record-add` | `[row: RecordRow]` | – |
| `table-change` | `[table: RecordTable]` | – |
| `error` | `[error: DbKanbanError]` | – |

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

#### `FaExtraction`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `ExtractionPort \| null` | nein | `null` | Fachlogik, z. B. `createExtractionRestPort({ baseUrl: '/api/extraction' })`. |
| `result` | `ExtractionRun \| null` | nein | `null` | Vorhandenes Ergebnis anzeigen (z. B. aus der Ablage der Anwendung). |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `extraction-completed` | `[result: ExtractionRun]` | – |
| `error` | `[message: string]` | – |

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

#### `IdentifierCheck`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `IdentifiersPort \| null` | nein | `null` | Fachlogik, z. B. `createIdentifiersRestPort({ baseUrl: '/api/kennungen' })`. |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `identifier-checked` | `[result: IdentifierResult]` | – |
| `batch-checked` | `[answer: IdentifierBatchAnswer]` | – |
| `error` | `[message: string]` | – |

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

#### `KanbanToolbar`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `title` | `string` | ja | – | – |
| `stats` | `BoardStats \| null` | ja | – | – |
| `filter` | `KanbanFilterState` | ja | – | – |
| `filterActive` | `boolean` | nein | `false` | – |
| `canRename` | `boolean` | nein | `false` | – |
| `canShare` | `boolean` | nein | `false` | – |
| `canConfigure` | `boolean` | nein | `false` | – |
| `showFullscreen` | `boolean` | nein | `true` | – |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `rename` | `[title: string]` | – |
| `share` | `[]` | – |
| `settings` | `[]` | – |
| `fullscreen` | `[]` | – |
| `reset-filter` | `[]` | – |
| `filter-change` | `[patch: Partial<KanbanFilterState>]` | – |

#### `ReportExportPanel`

| Prop | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `port` | `ReportingPort \| null` | nein | `null` | Fachlogik, z. B. `createReportingRestPort({ baseUrl: '/api/reporting' })`. |
| `tables` | `readonly ReportTableInput[]` | nein | `() => []` | Tabellen der Anwendung (je Tabelle ein Blatt). |
| `filename` | `string` | nein | `''` | Vorschlag für den Dateinamen (ohne oder mit `.xlsx`). |
| `locale` | `Locale` | nein | `undefined` | – |

| Ereignis | Nutzdaten | Beschreibung |
|---|---|---|
| `preview-completed` | `[result: WorkbookPreview]` | – |
| `export-completed` | `[file: DownloadFile]` | – |
| `error` | `[message: string]` | – |

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
  0.2.0 aus `@auditcore/common` weitergereicht; für Berliner Zeit und den
  Ersatzwert „—“ die gleichnamigen Funktionen aus `@auditcore/common`).
- **REST-Hilfen** für Port-Umsetzungen: `requestJson`, `requestFile`
  (`fetch` injizierbar, Fehler als `RestError`), `saveFile` – seit 0.2.0 aus
  `@auditcore/common` weitergereicht –, `createRunner`.
- **Toasts:** `useToast()` nutzt die anwendungsweite Warteschlange
  (`sharedToastQueue()`), `useToast(queue)` eine eigene aus
  `createToastQueue` (`@auditcore/common`).
- **Kanban:** Komponenten arbeiten über einen `BoardPort` aus
  `@auditcore/kanban-core` (`MemoryBoardPort` oder `RestBoardPort`).

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
Regeln kommen aus `@auditcore/kanban-core`. Ziehen per Pointer Events ist
eine eigene Umsetzung (vuedraggable/SortableJS geprüft und verworfen).
Seit 0.2.0 liegen die framework-freien Module (Formatierer, REST-Client,
Sortierung, Tabellen-Einlesen, `saveFile`) in `@auditcore/common` und werden
hier unter denselben Namen weitergereicht; die bisherigen Tests laufen
unverändert gegen die Weiterreichung. Seit 0.3.0 liegen Kern und Stile von
Basis, Tabelle, Synopse und Datenschutz in `@auditcore/ui-core`; die
Vue-Komponenten binden dessen Zustandsautomaten über `useStore` an
([Parität Vue ↔ React](../../docs/ui/react-paritaet.md)).
Geprüft mit Vitest (happy-dom) und Playwright gegen die Demo-Seite
(`npm run e2e -w @auditcore/ui`).

## Abhängigkeiten

- `@auditcore/common` 0.1.0 (Laufzeit, framework-freie Hilfsfunktionen)
- `@auditcore/ui-core` 0.1.0 (Laufzeit, framework-freier Kern: Texte,
  Verträge, View-Modelle, Zustandsautomaten, Stile)
- `@auditcore/kanban-core` 0.1.0 (Laufzeit, Kanban-Regeln und Ports)
- Leaflet (BSD-2-Clause) für `FaGeoMap` kommt seit 0.3.0 über
  `@auditcore/ui-core` (erst beim Anzeigen einer Karte dynamisch geladen,
  Stile in `ui.css`)
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
übergibt, siehe `@auditcore/common`);
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
