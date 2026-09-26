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

Anwendungen beziehen das Paket als Tarball aus dem GitHub-Release von
auditcore (noch nicht auf npm veröffentlicht), zusammen mit allen
`@flowaudit`-Paketen seiner Abhängigkeitshülle. Anleitung für Vue, React und
Web Components mit Integritätsprüfung und `vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

```sh
npm install @flowaudit/ui@https://github.com/janpow77/auditcore/releases/download/v<release>/flowaudit-ui-0.3.0.tgz
```

Abhängigkeitshülle: dazu `@flowaudit/ui-core`, `@flowaudit/common` und `@flowaudit/kanban-core`; Peer-Abhängigkeit `vue` ^3.5. Stile: immer `@flowaudit/ui/style.css`.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @flowaudit/ui`).

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
  Stichprobe, Benford und „Kennung prüfen“ nativ in `@flowaudit/ui-react` (ohne Vue, gleiche
  Stichprobe, Benford und Dokumentvergleiche nativ in `@flowaudit/ui-react` (ohne Vue, gleiche
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
Exporte der Einstiegspunkte aus `package.json#exports` (770):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/ui` | `ACCEPTED_EXTENSIONS` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ANSWER_VALUES` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Activity` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ActivityGroup` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ActorView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AgeKey` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `AllocationMethod` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AllocationRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AllocationResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AnalyseError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AnalyseInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AnalyseRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AnalyseValidation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AnswerInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AnswerValue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ApiErrorBody` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AreaGeometry` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AssessmentExportFormat` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AssessmentStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AssessmentSummary` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `AssessmentView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BADGE_COLORS` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `BadgeTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordAnalysis` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordBusy` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordCallbacks` | Re-Export | – | `./useBenford` |
| `@flowaudit/ui` | `BenfordCatalogue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordData` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordDistribution` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordMessageKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordMetricTexts` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordPanel` | Vue-Komponente | – | `benford/BenfordPanel.vue` |
| `@flowaudit/ui` | `BenfordPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordSource` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordTest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BenfordTranslate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BlockProgress` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BlockView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Breakdown` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BreakdownRow` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `BreakdownStep` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ButtonSize` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ButtonVariant` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `CARD_COLORS` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `CHANGE_STATUSES` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `COLUMN_COLORS` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `COMPARISON_KINDS` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `COMPARISON_MODES` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Catalogs` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `CellValue` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `ChartBar` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ChartBox` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ChartGeometry` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ClientExportFormat` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ColumnCheck` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ColumnPreview` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ColumnView` | Re-Export | – | `./useKanbanBoard` |
| `@flowaudit/ui` | `CompareFields` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `CompareForm` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `CompareRow` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Comparison` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonForm` | Vue-Komponente | – | `documents/ComparisonForm.vue` |
| `@flowaudit/ui` | `ComparisonKind` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonList` | Vue-Komponente | – | `documents/ComparisonList.vue` |
| `@flowaudit/ui` | `ComparisonMetadata` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonMode` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonRow` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonSummary` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonsController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonsData` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonsError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonsMessageKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonsPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonsSource` | Schnittstelle | – | `documents/useComparisons` |
| `@flowaudit/ui` | `ComparisonsTranslate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ComparisonsView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Completeness` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ConfidenceLevel` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Conformity` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ConformityProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ConformityRow` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ConsolidatedParagraph` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `CoordinateError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DATAPROTECTION_CONTRACT` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DEFAULT_BOX` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DEFAULT_FILTER` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DEFAULT_FORM` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DEFAULT_LOCALE` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DEFAULT_MAX_UPLOAD_BYTES` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DEFAULT_SYNOPSIS_FILTER` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DataProtectionError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DataProtectionKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DataProtectionPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DataProtectionProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DataProtectionTranslate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DatasetFinding` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DbCardView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DbColumnView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DbKanbanController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DbKanbanData` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DbKanbanError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DbKanbanMessageKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DbKanbanSource` | Schnittstelle | – | `dbkanban/useDbKanban` |
| `@flowaudit/ui` | `DbKanbanTranslate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DbKanbanView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DecimalSeparator` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `DecisionInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DecisionRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DecisionView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DegenerateRing` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Delimiter` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `DerivationStep` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DiffField` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DiffSegment` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DiffSide` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DistributionRow` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DossierFieldView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `DownloadFile` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `DsfaHooks` | Re-Export | – | `./useDsfa` |
| `@flowaudit/ui` | `DsfaState` | Schnittstelle | – | `dataprotection/useDsfa` |
| `@flowaudit/ui` | `DsfaStep` | Re-Export | – | `./useDsfa` |
| `@flowaudit/ui` | `EMPTY_EVALUATION` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `EarthModel` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ElementDefinition` | Schnittstelle | Eine Komponente, die als Web Component `flowaudit-<name>` bereitgestellt wird. | `elements/define` |
| `@flowaudit/ui` | `ElementTag` | Typ | – | `elements/define` |
| `@flowaudit/ui` | `EntryView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `EvaluateRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Evaluation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExportFormat` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExportInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExportPayload` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExportTexts` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExportedFile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractedField` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionBusy` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionCallbacks` | Re-Export | – | `./useExtraction` |
| `@flowaudit/ui` | `ExtractionCatalogue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionData` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionFinding` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionMessageKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionOcrSummary` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionRun` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionSource` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ExtractionValidation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FLAG_STATES` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FaBadge` | Vue-Komponente | – | `base/FaBadge.vue` |
| `@flowaudit/ui` | `FaButton` | Vue-Komponente | – | `base/FaButton.vue` |
| `@flowaudit/ui` | `FaComparisons` | Vue-Komponente | – | `documents/FaComparisons.vue` |
| `@flowaudit/ui` | `FaDbKanban` | Vue-Komponente | – | `dbkanban/FaDbKanban.vue` |
| `@flowaudit/ui` | `FaDialog` | Vue-Komponente | – | `base/FaDialog.vue` |
| `@flowaudit/ui` | `FaDsfa` | Vue-Komponente | – | `dataprotection/FaDsfa.vue` |
| `@flowaudit/ui` | `FaExtraction` | Vue-Komponente | – | `extraction/FaExtraction.vue` |
| `@flowaudit/ui` | `FaGeoMap` | Vue-Komponente | – | `geo/FaGeoMap.vue` |
| `@flowaudit/ui` | `FaIcon` | Vue-Komponente | – | `base/FaIcon.vue` |
| `@flowaudit/ui` | `FaSynopsis` | Vue-Komponente | – | `synopsis/FaSynopsis.vue` |
| `@flowaudit/ui` | `FaTable` | Vue-Komponente | – | `table/FaTable.vue` |
| `@flowaudit/ui` | `FaTextField` | Vue-Komponente | – | `base/FaTextField.vue` |
| `@flowaudit/ui` | `FaVvt` | Vue-Komponente | – | `dataprotection/FaVvt.vue` |
| `@flowaudit/ui` | `FetchLike` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `FieldEntry` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FieldError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FieldErrorCode` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FieldKind` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FieldUse` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FieldValue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FieldView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FilterOptions` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FindingView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FlagEntry` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FlagHit` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FlagState` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FlowauditUiOptions` | Schnittstelle | – | `plugin` |
| `@flowaudit/ui` | `FormatProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FreshnessStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `FreshnessView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `GeoArea` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `GeoBusy` | Re-Export | – | `./useGeoMap` |
| `@flowaudit/ui` | `GeoCatalogue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `GeoHint` | Re-Export | – | `./useGeoMap` |
| `@flowaudit/ui` | `GeoMapCallbacks` | Re-Export | – | `./useGeoMap` |
| `@flowaudit/ui` | `GeoPackageArea` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `GeoPackageResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `GeoPoint` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `GeoPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `GeoRestOptions` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `GeocodeHit` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `GeocodeResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `HitFilter` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `HitView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ICONS` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `INITIAL_BENFORD` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `INITIAL_EXTRACTION` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `INITIAL_REPORTING` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `INITIAL_SAMPLING` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `IconName` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `IdentifierBatchAnswer` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `IdentifierCallbacks` | Re-Export | – | `./useIdentifierCheck` |
| `@flowaudit/ui` | `IdentifierCatalogue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `IdentifierCheck` | Vue-Komponente | – | `identifiers/IdentifierCheck.vue` |
| `@flowaudit/ui` | `IdentifierController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `IdentifierData` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `IdentifierResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `IdentifiersPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ImportRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ImportedColumns` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `JsonObject` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `JsonValue` | Re-Export | – | `@flowaudit/ui-core` |
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
| `@flowaudit/ui` | `LatLon` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `LevelTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `LevelView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ListInfo` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Locale` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `LocateRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `LocateResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `LogEntry` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `LogView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `MAX_CARD_IMAGE_BYTES` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `MeasureView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `MessageParams` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `MethodGroup` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `MethodKind` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `MethodProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `MethodStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `MovePreview` | Re-Export | – | `./movePreview` |
| `@flowaudit/ui` | `NamedOption` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `NextSortOptions` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `NumberColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `Outcome` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `OverviewRow` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `PRIORITY_TONES` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `ParameterSpec` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ParsedTable` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `Person` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `PopulationItem` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Position` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `PriorityTone` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `ProfileDetail` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ProfileReference` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ProfileStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ProfileSummary` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ProfileView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Proposal` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `QuestionView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ROW_STATUSES` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RadiusHit` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RadiusRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RadiusResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RecordMove` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RecordPort` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `RecordProperty` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `RecordRow` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `RecordTable` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `RecordValue` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `RecordView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterColumn` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterContent` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterExportFormat` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterExportInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterIssue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterState` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RegisterStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RelativeKey` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `ReportCell` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportColumnType` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportExportPanel` | Vue-Komponente | – | `reporting/ReportExportPanel.vue` |
| `@flowaudit/ui` | `ReportTableInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportingBusy` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportingCallbacks` | Re-Export | – | `./useReportExport` |
| `@flowaudit/ui` | `ReportingCatalogue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportingController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportingData` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportingError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportingMessageKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportingPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportingSource` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReportingTranslate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RestClientOptions` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RestError` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `RestOptions` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `ReviewEvents` | Re-Export | – | `./useScreeningReview` |
| `@flowaudit/ui` | `ReviewStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ReviewView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RiskController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RiskData` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RiskDistributionRow` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RiskFilter` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RiskFlagCard` | Vue-Komponente | – | `risk/RiskFlagCard.vue` |
| `@flowaudit/ui` | `RiskFlagFilter` | Vue-Komponente | – | `risk/RiskFlagFilter.vue` |
| `@flowaudit/ui` | `RiskFlagState` | Vue-Komponente | – | `risk/RiskFlagState.vue` |
| `@flowaudit/ui` | `RiskFlagSummary` | Vue-Komponente | – | `risk/RiskFlagSummary.vue` |
| `@flowaudit/ui` | `RiskFlagTable` | Vue-Komponente | – | `risk/RiskFlagTable.vue` |
| `@flowaudit/ui` | `RiskFlags` | Vue-Komponente | – | `risk/RiskFlags.vue` |
| `@flowaudit/ui` | `RiskInputs` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RiskMessageKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RiskPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RiskProfileInfo` | Vue-Komponente | – | `risk/RiskProfileInfo.vue` |
| `@flowaudit/ui` | `RiskRecordDetail` | Vue-Komponente | – | `risk/RiskRecordDetail.vue` |
| `@flowaudit/ui` | `RiskSelection` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RiskTranslate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RowStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RowUpdate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RowView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RuleView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RunQuery` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RunRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RunRequestRecord` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RunSummary` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `RunView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Runner` | Schnittstelle | – | `rest/runner` |
| `@flowaudit/ui` | `SCREENING_CONTRACT` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `STATE_FILTER_KEYS` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `STATE_ICONS` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `STATE_KEYS` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SamplingBusy` | Re-Export | – | `./useSampling` |
| `@flowaudit/ui` | `SamplingCallbacks` | Re-Export | – | `./useSampling` |
| `@flowaudit/ui` | `SamplingCatalogue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SamplingController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SamplingData` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SamplingMessageKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SamplingPanel` | Vue-Komponente | – | `sampling/SamplingPanel.vue` |
| `@flowaudit/ui` | `SamplingPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SamplingSource` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SamplingTranslate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScenarioInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScenarioResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScoreClass` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScreeningController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScreeningData` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScreeningError` | Re-Export | – | `./useScreeningReview` |
| `@flowaudit/ui` | `ScreeningKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScreeningKind` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScreeningPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScreeningReview` | Vue-Komponente | – | `screening/ScreeningReview.vue` |
| `@flowaudit/ui` | `ScreeningReviewState` | Schnittstelle | – | `screening/useScreeningReview` |
| `@flowaudit/ui` | `ScreeningSelection` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ScreeningTranslate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SecondReviewRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SecondReviewView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SegmentKind` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SelectionError` | Re-Export | – | `./useSampling` |
| `@flowaudit/ui` | `SelectionInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SelectionRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SelectionResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SelectionRow` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SelectionTexts` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SelectionValidation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SelectionVariant` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ServerExportFormat` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SettingsView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Severity` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ShortValues` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SimplifyRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SimplifyResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SimplifyUnit` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SizeRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SizeResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SizeValidation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SortDirection` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `SortState` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `SourceView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SourcesView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `StateFilter` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `StratumCount` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `StratumResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SubjectInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SubjectRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SubjectStatus` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SubjectView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `SummaryView` | Re-Export | – | `@flowaudit/ui-core` |
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
| `@flowaudit/ui` | `TOLERANCE_STEPS` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `TabItem` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `TableColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `TableImport` | Vue-Komponente | – | `tabular/TableImport.vue` |
| `@flowaudit/ui` | `TableImportController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `TableImportData` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `TablePreview` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `TableRow` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `TabularMessageKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ThemeMode` | Typ | – | `theme/theme` |
| `@flowaudit/ui` | `TileSource` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Tone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Totals` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `Translate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `UseAuthToken` | Schnittstelle | – | `composables/useAuthToken` |
| `@flowaudit/ui` | `UseBenford` | Schnittstelle | – | `benford/useBenford` |
| `@flowaudit/ui` | `UseComparisons` | Schnittstelle | – | `documents/useComparisons` |
| `@flowaudit/ui` | `UseDbKanban` | Schnittstelle | – | `dbkanban/useDbKanban` |
| `@flowaudit/ui` | `UseExtraction` | Schnittstelle | – | `extraction/useExtraction` |
| `@flowaudit/ui` | `UseGeoMap` | Schnittstelle | – | `geo/useGeoMap` |
| `@flowaudit/ui` | `UseI18n` | Schnittstelle | – | `i18n/i18n` |
| `@flowaudit/ui` | `UseIdentifierCheck` | Schnittstelle | – | `identifiers/useIdentifierCheck` |
| `@flowaudit/ui` | `UseReportExport` | Schnittstelle | – | `reporting/useReportExport` |
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
| `@flowaudit/ui` | `UtmInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `UtmInputError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `UtmPointRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `UtmPointResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `UtmRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `UtmResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `VersionSummary` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `VersionView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ViewMessage` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ViewOptions` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `VvtExport` | Re-Export | – | `./useVvt` |
| `@flowaudit/ui` | `VvtExportFormat` | Re-Export | – | `./useVvt` |
| `@flowaudit/ui` | `VvtHooks` | Re-Export | – | `./useVvt` |
| `@flowaudit/ui` | `VvtState` | Schnittstelle | – | `dataprotection/useVvt` |
| `@flowaudit/ui` | `WORD_LIMIT` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `WhenMissingColumns` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `WorkbookPreview` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `WorkbookRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `acceptsHit` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `activityKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `addScenario` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `analyseErrorKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `answerOf` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `applyPreview` | Re-Export | – | `./movePreview` |
| `@flowaudit/ui` | `applyRowOverrides` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `applyTheme` | Funktion | Setzt das Farbschema am Element (Standard: Dokumentwurzel); 'system' folgt dem Betriebssystem. | `theme/theme` |
| `@flowaudit/ui` | `areasFromGeoPackage` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ariaSort` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `axisMaximum` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `badgePrefix` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `badgeStyle` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `bandTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `baseMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordBarTitle` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordChartTitle` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordDigitColumns` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordDigitRows` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordElement` | Konstante | `<flowaudit-benford>`: Eigenschaften `port` (BenfordPort), `values`, `locale`; Ereignisse `analysis-completed`, `error`. | `benford/element` |
| `@flowaudit/ui` | `benfordMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordMetricTexts` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordTickText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordValues` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `benfordValuesText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `blockProgress` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `breakdownRows` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `buildAnalyseRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `buildRowView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `buildSelectionRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `buildSizeRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `buildSynopsisView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `buildWorkbookRequest` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `cardAge` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `cardStyle` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `cellText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `changeIds` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `chartGeometry` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `cloneContent` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `codeLabel` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `columnCells` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `compareValues` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `comparisonRows` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `comparisonsElement` | Konstante | `<flowaudit-comparisons>`: `port` als JS-Eigenschaft (z. B. | `documents/element` |
| `@flowaudit/ui` | `comparisonsMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `comparisonsView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `completeness` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `completenessTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `confidenceText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `coverIssues` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createBenfordController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createBenfordRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createComparisonsController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createDataProtectionRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createDbKanbanController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createExtractionController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createExtractionRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createFlowauditUi` | Funktion | Vue-Plugin: stellt die Sprache app-weit bereit. | `plugin` |
| `@flowaudit/ui` | `createGeoRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createIdentifierController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createIdentifiersRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createMemoryRecordPort` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `createReportingController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createReportingRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createRiskController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createRiskRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createRunner` | Funktion | Gemeinsamer Ablauf für Portanfragen: Beschäftigt-Status, Fehlermeldung, Rückruf. | `rest/runner` |
| `@flowaudit/ui` | `createSamplingController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createSamplingRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createScreeningController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createScreeningRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createSynopsisRestClient` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `createTableImportController` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `currentVersion` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `dataprotectionError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `dataprotectionMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `dbKanbanElement` | Konstante | `<flowaudit-db-kanban>`: `port` (RecordPort) oder `table` als JS-Eigenschaft; Ereignisse `record-move`, `record-add`, `table-change`, `update:groupBy`, `error`. | `dbkanban/element` |
| `@flowaudit/ui` | `dbKanbanMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `dbKanbanView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `decisionTitle` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `defineMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `derivationColumns` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `derivationRows` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `detectDecimal` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `detectDelimiter` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `diffSegments` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `digitLabel` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `displayName` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `displayValue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `distribution` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `downloadText` | Re-Export | – | `./useSynopsisExport` |
| `@flowaudit/ui` | `dsfaElement` | Konstante | `<flowaudit-dsfa>`: Eigenschaften `port`, `activityId`, `actor`, `editable`, `locale`; Ereignisse `assessment-change`, `error`. | `dataprotection/element` |
| `@flowaudit/ui` | `editedBy` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `emptyActivity` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `emptyContent` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `emptyFilter` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `emptyScenario` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `escapeHtml` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `escapeMarkdown` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `evaluationRules` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `excludedLines` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `exportFilename` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `extractionElement` | Konstante | `<flowaudit-extraction>`: Eigenschaften `port` (ExtractionPort), `result`, `locale`; Ereignisse `extraction-completed`, `error`. | `extraction/element` |
| `@flowaudit/ui` | `extractionMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `extractionValidation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `fieldIssues` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `fieldValue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `fileSize` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `filterOptions` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `filterRecords` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `filterRows` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `filterSubjects` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `filterSummaries` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `flagState` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `focusRow` | Re-Export | – | `./useSynopsisNavigation` |
| `@flowaudit/ui` | `focusableWithin` | Re-Export | – | `./useFocusTrap` |
| `@flowaudit/ui` | `formProblems` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `formatAmount` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `formatDate` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `formatDegrees` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `formatDistance` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `formatMetres` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `formatNumber` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `formatPercent` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `formatShare` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `formatValue` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `geoMapElement` | Konstante | `<flowaudit-geo-map>`: Eigenschaften `port` (GeoPort), `points`, `areas`, `tiles` (TileSource), `center`, `zoom`, `locale`; Ereignisse `radius-completed`, `location-checked`, `area … | `geo/element` |
| `@flowaudit/ui` | `geoMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `groupByDepartment` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `groupRecords` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `guessNumberColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `hasPartialStrata` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `identifierCheckElement` | Konstante | `<flowaudit-identifier-check>`: Eigenschaften `port` (IdentifiersPort), `locale`; Ereignisse `identifier-checked`, `batch-checked`, `error`. | `identifiers/element` |
| `@flowaudit/ui` | `identifierMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `importDelimiterText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `importOptionalColumn` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `importPreview` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `importRejectedLines` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `initialTexts` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `initials` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `interpolate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `isDeviation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `isIconName` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `isLocale` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `isPercent` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `isStratifiedPopulation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `issuesFor` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `itemsFromImport` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `kanbanBoardElement` | Konstante | `<flowaudit-kanban-board>`: Eigenschaften `port` (BoardPort) und `boardId` oder `board` (+ `userId`) für lokale Bearbeitung; Ereignisse `board-change`, `error`, `fullscreen`, `navi … | `kanban/element` |
| `@flowaudit/ui` | `kanbanBoardListElement` | Konstante | `<flowaudit-kanban-boards>`: Boardliste mit Eigenschaft `port`; Ereignisse `board-select`, `created`. | `kanban/element` |
| `@flowaudit/ui` | `kanbanDialogMessages` | Re-Export | – | `./messages` |
| `@flowaudit/ui` | `kanbanMessages` | Re-Export | – | `./messages` |
| `@flowaudit/ui` | `lcsOperations` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `levelLabel` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `levelTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `localeTag` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `mayRelease` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `methodGroups` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `methodStatusKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `methodTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `ndiffOperations` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `needsShortValues` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `nextOpenHit` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `nextSort` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `numberColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `pairs` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parameterLabel` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parameterUnit` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseConditions` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseCount` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseDegrees` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseImport` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseInput` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseLatLon` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseMetres` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseNumber` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `parseSubjects` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `parseTable` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `parseUtm` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `placementFor` | Re-Export | – | `./movePreview` |
| `@flowaudit/ui` | `plainSegments` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `populationSuggestions` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `populationText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `positionText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `positiveSum` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `preview` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `printHtml` | Re-Export | – | `./useSynopsisExport` |
| `@flowaudit/ui` | `profileHintText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `profileStatusText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `provideLocale` | Funktion | Stellt die Sprache für alle Nachfahren bereit (App-Ebene oder Teilbaum). | `i18n/i18n` |
| `@flowaudit/ui` | `readTheme` | Funktion | Liest das explizit gesetzte Farbschema; ohne Attribut 'system'. | `theme/theme` |
| `@flowaudit/ui` | `recommendationTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `recordEntries` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `recordLabel` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `recordRules` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `registerCsv` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `registerFilename` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `registerHtml` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `registerMarkdown` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `relativeTime` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `removeScenario` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `reportCellText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `reportExportElement` | Konstante | `<flowaudit-report-export>`: Eigenschaften `port` (ReportingPort), `tables`, `filename`, `locale`; Ereignisse `preview-completed`, `export-completed`, `error`. | `reporting/element` |
| `@flowaudit/ui` | `reportingErrorKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `reportingMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `reportingProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `reportingSampleNote` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `reportingSheetHeading` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `reportingTablesText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `reportingWorkbookText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `requestFile` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `requestJson` | Re-Export | – | `./client` |
| `@flowaudit/ui` | `requirementKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `resolvedTheme` | Funktion | Tatsächlich wirksames Schema, auch wenn 'system' gewählt ist. | `theme/theme` |
| `@flowaudit/ui` | `riskFlagsElement` | Konstante | `<flowaudit-risk-flags>`: Eigenschaften `evaluation` (Antwort von `POST /evaluate`) und `profile` (Antwort von `GET /profiles/{id}/{version}`) als JS-Objekte; Ereignisse `record-se … | `risk/element` |
| `@flowaudit/ui` | `riskMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `riskTableColumns` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `riskTableRows` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `sameSurvey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `samplingElement` | Konstante | `<flowaudit-sampling>`: Eigenschaften `port` (SamplingPort), `items` (Grundgesamtheit), `locale`; Ereignisse `size-calculated`, `selection-drawn`, `error`. | `sampling/element` |
| `@flowaudit/ui` | `samplingFieldError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `samplingInputNumber` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `samplingMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `samplingPopulation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `samplingProfile` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `saveFile` | Re-Export | – | `./download` |
| `@flowaudit/ui` | `screeningMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `screeningReviewElement` | Konstante | `<flowaudit-screening-review>`: Eigenschaften `port` (ScreeningPort), `runId`, `locale`; Ereignisse `run-created`, `decided`, `error`. | `screening/element` |
| `@flowaudit/ui` | `screeningTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `segmentsText` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `selectRisk` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `selectScreening` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `selectionColumns` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `selectionErrorKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `selectionRows` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `selectionTexts` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `setDefaultLocale` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `severityTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `sharedToastQueue` | Funktion | Anwendungsweite Warteschlange (einmal je Seite). | `composables/useToast` |
| `@flowaudit/ui` | `sizeTexts` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `sortRows` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `splitLine` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui` | `stateTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `statusHintKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `statusKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `statusLabel` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `statusTone` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `stepChange` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `strataColumns` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `strataOf` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `strataRows` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `summaryView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `surveyFrom` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `synopsisElement` | Konstante | `<flowaudit-synopsis>`: `comparison`/`result` und `port` als JS-Eigenschaften; Ereignisse `row-update`, `export`, `navigate`, `update:layout`. | `synopsis/element` |
| `@flowaudit/ui` | `synopsisMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `synopsisPortOf` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `tableElement` | Konstante | `<flowaudit-table>`: Spalten und Zeilen als JS-Eigenschaften, Ereignisse `row-click`, `sort-change`. | `table/element` |
| `@flowaudit/ui` | `tabularMessages` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `textOn` | Re-Export | – | `@flowaudit/kanban-core` |
| `@flowaudit/ui` | `toCompareFields` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `toHtml` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `toMarkdown` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `toggleMeasure` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `totals` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `translate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `triggeredDataset` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `useAuthToken` | Funktion | Reaktiver Zugriff auf einen `TokenStore` aus `@flowaudit/common`. | `composables/useAuthToken` |
| `@flowaudit/ui` | `useBenford` | Funktion | Vue-Anbindung der Benford-Analyse aus `@flowaudit/ui-core` (`createBenfordController`). | `benford/useBenford` |
| `@flowaudit/ui` | `useClickOutside` | Funktion | Ruft `handler` bei Klick außerhalb der Elemente (Template-Refs) und bei Escape; abgemeldet beim Aufräumen. | `composables/useDom` |
| `@flowaudit/ui` | `useComparisons` | Funktion | – | `documents/useComparisons` |
| `@flowaudit/ui` | `useDbKanban` | Funktion | – | `dbkanban/useDbKanban` |
| `@flowaudit/ui` | `useDebouncedFn` | Funktion | Entprellte Funktion; ein ausstehender Aufruf wird beim Abbau der Komponente verworfen. | `composables/useDebounced` |
| `@flowaudit/ui` | `useDebouncedRef` | Funktion | Folgt `source` erst nach `ms` Ruhe (z. B. Suchfeld → Anfrage). | `composables/useDebounced` |
| `@flowaudit/ui` | `useDsfa` | Funktion | – | `dataprotection/useDsfa` |
| `@flowaudit/ui` | `useExtraction` | Funktion | Vue-Anbindung der Belegerkennung aus `@flowaudit/ui-core` (`createExtractionController`). | `extraction/useExtraction` |
| `@flowaudit/ui` | `useFocusTrap` | Funktion | Hält den Tastaturfokus im Container, solange `active` wahr ist, und gibt ihn danach an das zuvor fokussierte Element zurück. | `composables/useFocusTrap` |
| `@flowaudit/ui` | `useGeoMap` | Funktion | Zustand und Abläufe der Geo-Karte; jede Berechnung läuft über den Port. | `geo/useGeoMap` |
| `@flowaudit/ui` | `useI18n` | Funktion | Composable für Komponenten. `override` (z. B. eine Prop `locale`) hat Vorrang vor der bereitgestellten Sprache. | `i18n/i18n` |
| `@flowaudit/ui` | `useId` | Funktion | Eindeutige, stabile ID je Komponenteninstanz für aria-Verknüpfungen. | `composables/useId` |
| `@flowaudit/ui` | `useIdentifierCheck` | Funktion | Vue-Anbindung von „Kennung prüfen“ aus `@flowaudit/ui-core` (`createIdentifierController`). | `identifiers/useIdentifierCheck` |
| `@flowaudit/ui` | `useKanbanActions` | Funktion | – | `kanban/useKanbanActions` |
| `@flowaudit/ui` | `useKanbanBoard` | Funktion | – | `kanban/useKanbanBoard` |
| `@flowaudit/ui` | `useKanbanFilter` | Funktion | Such- und Filterzustand des Boards (Toolbar) als CardFilter der Kernlogik. | `kanban/useKanbanFilter` |
| `@flowaudit/ui` | `useLocale` | Funktion | – | `i18n/i18n` |
| `@flowaudit/ui` | `useMediaQuery` | Funktion | Reaktiver Stand einer Media-Query, z. B. `useMediaQuery('(max-width: 768px)')`. | `composables/useDom` |
| `@flowaudit/ui` | `useMoveController` | Funktion | – | `kanban/useMoveController` |
| `@flowaudit/ui` | `useReportExport` | Funktion | Vue-Anbindung des Tabellenexports aus `@flowaudit/ui-core` (`createReportingController`). | `reporting/useReportExport` |
| `@flowaudit/ui` | `useRiskFlags` | Funktion | Vue-Anbindung des Zustandsautomaten aus `@flowaudit/ui-core` (Filter, Auswahl, abgeleitete Daten). | `risk/useRiskFlags` |
| `@flowaudit/ui` | `useRiskProfile` | Funktion | Profilbeschreibung zur Auswertung: die übergebene, sonst über den Port nachgeladen (Profil und Version der Auswertung, nie ein Standardprofil). | `risk/useRiskProfile` |
| `@flowaudit/ui` | `useSampling` | Funktion | Vue-Anbindung des Stichprobenrechners aus `@flowaudit/ui-core` (`createSamplingController`); Getter halten Props reaktiv. | `sampling/useSampling` |
| `@flowaudit/ui` | `useScreeningReview` | Funktion | Stand, Auswahl und Aktionen der Trefferprüfung; die Logik liegt im Kern (`createScreeningController`). | `screening/useScreeningReview` |
| `@flowaudit/ui` | `useSort` | Funktion | Sortierzustand und sortierte Zeilen für eigene Tabellen (FaTable sortiert selbst). | `composables/useSort` |
| `@flowaudit/ui` | `useStore` | Funktion | Stand eines Kern-Controllers (`@flowaudit/ui-core`) als reaktive Vue-Referenz. | `composables/useStore` |
| `@flowaudit/ui` | `useSynopsis` | Funktion | Vue-Anbindung des Zustandsautomaten aus `@flowaudit/ui-core` (Laden, Filter, Zeilenänderungen, Navigation). | `synopsis/useSynopsis` |
| `@flowaudit/ui` | `useSynopsisExport` | Funktion | Exporte der sichtbaren, ausgewählten Zeilen; `onExport` erhält jedes Ergebnis. | `synopsis/useSynopsisExport` |
| `@flowaudit/ui` | `useSynopsisNavigation` | Funktion | Navigation zwischen Änderungen mit Schaltflächen und Tasten N/J bzw. P/K. | `synopsis/useSynopsisNavigation` |
| `@flowaudit/ui` | `useTableImport` | Funktion | Vue-Anbindung des Datei-Imports aus `@flowaudit/ui-core` (Datei lesen, Spalten zuordnen, Vorschau). | `tabular/useTableImport` |
| `@flowaudit/ui` | `useTheme` | Funktion | Composable: reaktives Farbschema, synchron mit dem Attribut am Element. | `theme/theme` |
| `@flowaudit/ui` | `useThrottledFn` | Funktion | Gedrosselte Funktion; ein ausstehender Aufruf wird beim Abbau der Komponente verworfen. | `composables/useDebounced` |
| `@flowaudit/ui` | `useToast` | Funktion | Toasts als reaktive Liste über der framework-freien Warteschlange aus `@flowaudit/common`. | `composables/useToast` |
| `@flowaudit/ui` | `useVvt` | Funktion | – | `dataprotection/useVvt` |
| `@flowaudit/ui` | `utmErrorKey` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `validateDecision` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `vertexCount` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui` | `vvtElement` | Konstante | `<flowaudit-vvt>`: Eigenschaften `port` (DataProtectionPort), `actor`, `editable`, `locale`; Ereignisse `draft-saved`, `released`, `exported`, `error`. | `dataprotection/element` |
| `@flowaudit/ui` | `whenMissingKey` | Re-Export | – | `@flowaudit/ui-core` |
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
| `<flowaudit-comparisons>` | `FaComparisons` | `documents/element.ts` |
| `<flowaudit-db-kanban>` | `FaDbKanban` | `dbkanban/element.ts` |
| `<flowaudit-dsfa>` | `FaDsfa` | `dataprotection/element.ts` |
| `<flowaudit-extraction>` | `FaExtraction` | `extraction/element.ts` |
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
- Leaflet (BSD-2-Clause) für `FaGeoMap` kommt seit 0.3.0 über
  `@flowaudit/ui-core` (erst beim Anzeigen einer Karte dynamisch geladen,
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
