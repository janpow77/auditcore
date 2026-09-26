# @flowaudit/ui-react

## Zweck

Native React-18-Komponenten der FlowAudit-Oberflächen (Basis, Tabelle, Synopse, VVT, DSFA, Geo-Karte, Risiko-Merkmale, Screening, Stichprobe, Benford) ohne Vue und ohne Web Components, auf dem gemeinsamen Kern `@flowaudit/ui-core`.

Für React-Anwendungen wie regulierung. Die Komponenten erfüllen dieselben
Verträge wie die Vue-Fassung `@flowaudit/ui`: gleiche Props- und
Ereignis-Semantik, gleiche REST-Verträge, gleiche Texte, gleiches Markup
und gleiche Barrierefreiheit (Tastatur, ARIA). Fachlogik, Texte und
Zustandsautomaten kommen aus `@flowaudit/ui-core`; dieses Paket enthält nur
die React-Darstellung. Dazu kommen React-Hooks auf Basis von
`@flowaudit/common` (Toasts, Media-Query, Klick außerhalb, Sortierung,
Entprellen, Token).

## Installation

Im auditcore-Repository ist das Paket Teil des npm-Workspace:

```sh
npm ci                                 # im Repository-Stamm
npm run build -w @flowaudit/ui-react   # dist/: ESM und Typen
```

Im Anwendungsrepository:

```sh
npm install @flowaudit/ui-react @flowaudit/ui-core @flowaudit/common react react-dom
```

Das Paket ist nicht in einer npm-Registry veröffentlicht; Bezug über den
Workspace oder mit `npm pack` erzeugte Tarballs von `@flowaudit/ui-react`,
`@flowaudit/ui-core` und `@flowaudit/common`. Vue wird nur für den
veralteten Einstieg `@flowaudit/ui-react/elements` gebraucht.

## Schnellstart

```tsx
import { FlowauditSynopsis, FlowauditTable, createSynopsisRestClient } from '@flowaudit/ui-react'
import type { TableColumn } from '@flowaudit/common'
import '@flowaudit/ui-core/style.css'

const columns: TableColumn[] = [
  { key: 'beleg', label: 'Beleg', sortable: true },
  { key: 'betrag', label: 'Betrag', align: 'end' },
]
const rows = [{ id: 'r1', beleg: 'R-2026-001', betrag: 1250.5 }]
const synopsis = createSynopsisRestClient({ baseUrl: '/api/synopsis' })

export function Belege({ open }: { open: (row: unknown) => void }) {
  return <FlowauditTable columns={columns} rows={rows} caption="Belege" clickable onRowClick={open} />
}

export function Vergleich({ id }: { id: string }) {
  return <FlowauditSynopsis comparisonId={id} port={synopsis} onNavigate={(rowId) => console.info(rowId)} />
}
```

## Einbindung

- **React:** Komponenten wie gewohnt einsetzen und einmal
  `@flowaudit/ui-core/style.css` laden. Sprache über die Prop `locale`, einen
  `LocaleProvider` oder `setDefaultLocale`. Ereignisse sind `onXxx`-Props und
  erhalten die Nutzdaten direkt (z. B. `onRowUpdate(update)`,
  `onAssessmentChange({ step, id, version, status })`). Was in Vue ein
  `v-model` ist, ist hier gesteuert (`sort`/`onSortChange`,
  `layout`/`onLayoutChange`) oder ungesteuert (`defaultSort`,
  `defaultLayout`); der Vue-Slot `cell-<key>` heißt `renderCell`.
- **Ports:** Datenzugriffe laufen über Ports aus `@flowaudit/ui-core`
  (`createSynopsisRestClient`, `createDataProtectionRestPort`), `fetch` und
  Kopfzeilen sind injizierbar (Anmeldetoken der Anwendung).
- **Web Component (veraltet):** Kanban gibt es noch nicht nativ; seine
  Hüllen um die Vue-Web-Components stehen unter `@flowaudit/ui-react/elements`
  (`defineFlowauditElements()` aufrufen, `@flowaudit/ui/style.css` laden,
  `@flowaudit/ui`, `@flowaudit/kanban-core` und Vue installieren).

- **Muster für weitere native Komponenten** (verbindlich, Einzelheiten in
  [`docs/ui/beitragen.md`](../../docs/ui/beitragen.md)):
  1. Kernlogik framework-frei in `packages-js/ui-core/src/<komponente>/`:
     `messages.ts`, Datentypen, Port, View-Funktionen und ein Controller
     (`createStore` + reine Selektoren, Vorlage `synopsis/controller.ts`,
     `dataprotection/vvt.ts`); Stile in `ui-core/styles/<komponente>.css`.
  2. Vue (`packages-js/ui`) bindet den Controller mit `useStore` an; React hier
     unter `src/<komponente>/` mit `useStoreState`, `useElementId`,
     `useTranslation`, gleichem Markup (Klassen, ARIA, Texte) wie die SFC.
  3. Paritätsfälle in `ui-core/test/parity/cases-<komponente>.ts`; Vue prüft
     sie in `ui/test/parity*.spec.ts`, React in
     `test/parity/<komponente>.spec.tsx` mit `renderBoth` und `expectParity`
     (Erwartungen, normalisiertes DOM, Formularzustand, auch nach Interaktionen).
  4. Export in `src/index.ts`; eine abgelöste Hülle aus `src/elements.ts` entfernen.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (165):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/ui-react` | `Badge` | Funktion | – | `base/Badge` |
| `@flowaudit/ui-react` | `BadgeProps` | Schnittstelle | – | `base/Badge` |
| `@flowaudit/ui-react` | `BenfordAnalysis` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `BenfordInputs` | Schnittstelle | – | `benford/useBenford` |
| `@flowaudit/ui-react` | `BenfordPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `Button` | Funktion | Schaltfläche wie `FaButton` (gleiche Klassen, ARIA und Zustände). | `base/Button` |
| `@flowaudit/ui-react` | `ButtonProps` | Schnittstelle | – | `base/Button` |
| `@flowaudit/ui-react` | `CellValue` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `Comparison` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `ComparisonResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `DataProtectionError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `DataProtectionPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `DecimalSeparator` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `Delimiter` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `Dialog` | Funktion | Modaler Dialog wie `FaDialog`: Fokusfalle, Escape, Rückgabe des Fokus, beschriftet über Titel und Beschreibung. | `base/Dialog` |
| `@flowaudit/ui-react` | `DialogProps` | Schnittstelle | – | `base/Dialog` |
| `@flowaudit/ui-react` | `DownloadFile` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `DsfaStep` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `Evaluation` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `ExportPayload` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `ExtractionInputs` | Schnittstelle | – | `extraction/useExtraction` |
| `@flowaudit/ui-react` | `ExtractionPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `ExtractionRun` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `FetchLike` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `FlowauditBenford` | Funktion | Benford-Analyse als native React-Komponente (Vertrag wie `<flowaudit-benford>`): Werte (Eigenschaft oder Datei), Test, Bewertungsprofil, Kennzahlen mit MAD, Chi² und z je Ziffer, S … | `benford/FlowauditBenford` |
| `@flowaudit/ui-react` | `FlowauditBenfordProps` | Typ | – | `benford/FlowauditBenford` |
| `@flowaudit/ui-react` | `FlowauditDsfa` | Funktion | Datenschutz-Folgenabschätzung (Art. 35 DSGVO) als native React-Komponente – Vertrag, Texte und Ablauf wie `<flowaudit-dsfa>`: Übersicht, Schwellwertanalyse, Risiko, Vorschlag der B … | `dataprotection/FlowauditDsfa` |
| `@flowaudit/ui-react` | `FlowauditDsfaProps` | Schnittstelle | – | `dataprotection/FlowauditDsfa` |
| `@flowaudit/ui-react` | `FlowauditExtraction` | Funktion | Belegerkennung als native React-Komponente (Vertrag wie `<flowaudit-extraction>`): Dokument hochladen, Profil wählen, erkannte Felder mit Konfidenz und Validierungsbefunde. | `extraction/FlowauditExtraction` |
| `@flowaudit/ui-react` | `FlowauditExtractionProps` | Typ | – | `extraction/FlowauditExtraction` |
| `@flowaudit/ui-react` | `FlowauditGeoMap` | Funktion | Geo-Karte als native React-Komponente (Vertrag wie `<flowaudit-geo-map>`): Karte, Bezugspunkt mit UTM, Umkreis, Punkt in Fläche, Vereinfachung, GeoPackage. | `geo/FlowauditGeoMap` |
| `@flowaudit/ui-react` | `FlowauditGeoMapProps` | Schnittstelle | – | `geo/FlowauditGeoMap` |
| `@flowaudit/ui-react` | `FlowauditRiskFlags` | Funktion | Risiko-Merkmale als native React-Komponente – Vertrag, Texte und Markup wie `<flowaudit-risk-flags>`: Verteilung je Merkmal, Filter, Tabelle je Datensatz, Detailkarten mit Begründu … | `risk/FlowauditRiskFlags` |
| `@flowaudit/ui-react` | `FlowauditRiskFlagsProps` | Schnittstelle | – | `risk/FlowauditRiskFlags` |
| `@flowaudit/ui-react` | `FlowauditSampling` | Funktion | Stichprobenrechner als native React-Komponente (Vertrag wie `<flowaudit-sampling>`): Methodenprofil, Stichprobenumfang mit Herleitung, Grundgesamtheit (Eigenschaft oder Datei), Aus … | `sampling/FlowauditSampling` |
| `@flowaudit/ui-react` | `FlowauditSamplingProps` | Typ | – | `sampling/FlowauditSampling` |
| `@flowaudit/ui-react` | `FlowauditScreeningReview` | Funktion | Screening-Trefferprüfung (Sanktionslisten, PEP) als native React-Komponente – Vertrag, Texte und Ablauf wie `<flowaudit-screening-review>`: Prüflauf anlegen, Treffer filtern, vergl … | `screening/FlowauditScreeningReview` |
| `@flowaudit/ui-react` | `FlowauditScreeningReviewProps` | Schnittstelle | – | `screening/FlowauditScreeningReview` |
| `@flowaudit/ui-react` | `FlowauditSynopsis` | Konstante | Synopse / Versionsvergleich als native React-Komponente (Vertrag wie `<flowaudit-synopsis>`): Seiten- oder Inline-Ansicht, Wortdifferenz, Filter, Navigation mit N/J und P/K, Export … | `synopsis/FlowauditSynopsis` |
| `@flowaudit/ui-react` | `FlowauditSynopsisHandle` | Schnittstelle | Methoden über `ref` (wie `defineExpose` der Vue-Fassung). | `synopsis/FlowauditSynopsis` |
| `@flowaudit/ui-react` | `FlowauditSynopsisProps` | Schnittstelle | – | `synopsis/FlowauditSynopsis` |
| `@flowaudit/ui-react` | `FlowauditTable` | Funktion | Tabelle wie `FaTable`: Sortierung per Schaltfläche (aria-sort), anklickbare Zeilen per Maus und Enter. | `table/FlowauditTable` |
| `@flowaudit/ui-react` | `FlowauditTableProps` | Schnittstelle | – | `table/FlowauditTable` |
| `@flowaudit/ui-react` | `FlowauditVvt` | Funktion | Verzeichnis von Verarbeitungstätigkeiten (Art. | `dataprotection/FlowauditVvt` |
| `@flowaudit/ui-react` | `FlowauditVvtProps` | Schnittstelle | – | `dataprotection/FlowauditVvt` |
| `@flowaudit/ui-react` | `GeoArea` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `GeoPoint` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `GeoPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `HitView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `Icon` | Funktion | – | `base/Icon` |
| `@flowaudit/ui-react` | `IconProps` | Schnittstelle | – | `base/Icon` |
| `@flowaudit/ui-react` | `ImportedColumns` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `LatLon` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `Locale` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `LocaleProvider` | Funktion | Sprache für alle Komponenten im Teilbaum (Gegenstück zu `provideLocale` in Vue). | `i18n` |
| `@flowaudit/ui-react` | `NextSortOptions` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `NumberColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `ParsedTable` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `PopulationItem` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `ProfileDetail` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `RestError` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `RestOptions` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `RiskFilter` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `RiskFlagCard` | Funktion | Treffer oder unbestimmtes Merkmal eines Datensatzes mit Begründung, Eingabewerten und Schwellen, wie `RiskFlagCard`. | `risk/RiskFlagCard` |
| `@flowaudit/ui-react` | `RiskFlagCardProps` | Schnittstelle | – | `risk/RiskFlagCard` |
| `@flowaudit/ui-react` | `RiskFlagFilter` | Funktion | Filter nach Merkmal, Zustand und Suchtext, wie `RiskFlagFilter`. | `risk/RiskFlagFilter` |
| `@flowaudit/ui-react` | `RiskFlagFilterProps` | Schnittstelle | – | `risk/RiskFlagFilter` |
| `@flowaudit/ui-react` | `RiskFlagState` | Funktion | Zustand eines Merkmals mit Symbol (Farbe ist nie der einzige Bedeutungsträger), wie `RiskFlagState`. | `risk/RiskFlagState` |
| `@flowaudit/ui-react` | `RiskFlagStateProps` | Schnittstelle | – | `risk/RiskFlagState` |
| `@flowaudit/ui-react` | `RiskFlagSummary` | Funktion | Verteilung je Merkmal mit Summen und Befunden über alle Datensätze, wie `RiskFlagSummary`. | `risk/RiskFlagSummary` |
| `@flowaudit/ui-react` | `RiskFlagSummaryProps` | Schnittstelle | – | `risk/RiskFlagSummary` |
| `@flowaudit/ui-react` | `RiskFlagTable` | Funktion | Merkmale je Datensatz; Zeilen per Maus und Enter wählbar, wie `RiskFlagTable`. | `risk/RiskFlagTable` |
| `@flowaudit/ui-react` | `RiskFlagTableProps` | Schnittstelle | – | `risk/RiskFlagTable` |
| `@flowaudit/ui-react` | `RiskPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `RiskProfileInfo` | Funktion | Profil, Regeln und Eingabefelder (Pflicht/optional, Folge bei Fehlen), wie `RiskProfileInfo`. | `risk/RiskProfileInfo` |
| `@flowaudit/ui-react` | `RiskProfileInfoProps` | Schnittstelle | – | `risk/RiskProfileInfo` |
| `@flowaudit/ui-react` | `RiskRecordDetail` | Funktion | Detailansicht eines Datensatzes (Karten je Treffer/unbestimmtem Merkmal, Bewertung), wie `RiskRecordDetail`. | `risk/RiskRecordDetail` |
| `@flowaudit/ui-react` | `RiskRecordDetailProps` | Schnittstelle | – | `risk/RiskRecordDetail` |
| `@flowaudit/ui-react` | `RowUpdate` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `RunView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `SamplingInputs` | Schnittstelle | – | `sampling/useSampling` |
| `@flowaudit/ui-react` | `SamplingPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `ScreeningError` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `ScreeningPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `SelectionResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `SettingsView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `SizeResult` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `SortDirection` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `SortState` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `SourcesView` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `SynopsisLayout` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `SynopsisPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `TableColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `TableImport` | Funktion | Datei-Import wie `TableImport` (Vue): CSV/TSV/Text lesen, Spalten zuordnen, Werte übernehmen. | `tabular/TableImport` |
| `@flowaudit/ui-react` | `TableImportProps` | Schnittstelle | – | `tabular/TableImport` |
| `@flowaudit/ui-react` | `TableRow` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `TextField` | Funktion | Eingabefeld wie `FaTextField` (Beschriftung, Hinweis, Fehler mit aria-describedby). | `base/TextField` |
| `@flowaudit/ui-react` | `TextFieldProps` | Schnittstelle | – | `base/TextField` |
| `@flowaudit/ui-react` | `TileSource` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `ToastProvider` | Funktion | Stellt eine eigene Warteschlange für den Teilbaum bereit (z. B. je Mandant oder im Test). | `hooks/toast` |
| `@flowaudit/ui-react` | `UseAuthToken` | Schnittstelle | – | `hooks/state` |
| `@flowaudit/ui-react` | `UseBenford` | Schnittstelle | – | `benford/useBenford` |
| `@flowaudit/ui-react` | `UseExtraction` | Schnittstelle | – | `extraction/useExtraction` |
| `@flowaudit/ui-react` | `UseRiskFlags` | Schnittstelle | – | `risk/useRiskFlags` |
| `@flowaudit/ui-react` | `UseSampling` | Schnittstelle | – | `sampling/useSampling` |
| `@flowaudit/ui-react` | `UseScreeningReview` | Schnittstelle | – | `screening/useScreeningReview` |
| `@flowaudit/ui-react` | `UseSort` | Schnittstelle | – | `hooks/state` |
| `@flowaudit/ui-react` | `UseSortOptions` | Schnittstelle | – | `hooks/state` |
| `@flowaudit/ui-react` | `UseToast` | Schnittstelle | – | `hooks/toast` |
| `@flowaudit/ui-react` | `UseTranslation` | Schnittstelle | – | `i18n` |
| `@flowaudit/ui-react` | `VvtExport` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `ariaSort` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `columnCells` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `compareValues` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `createBenfordRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `createDataProtectionRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `createExtractionRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `createGeoRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `createRiskRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `createSamplingRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `createScreeningRestPort` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `createSynopsisRestClient` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `detectDecimal` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `detectDelimiter` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `formatDate` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `formatNumber` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `formatPercent` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `guessNumberColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `localeTag` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `nextSort` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `numberColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `parseNumber` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `parseTable` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `requestFile` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `requestJson` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `saveFile` | Re-Export | – | `@flowaudit/common/browser` |
| `@flowaudit/ui-react` | `setDefaultLocale` | Re-Export | – | `@flowaudit/ui-core` |
| `@flowaudit/ui-react` | `sharedToastQueue` | Funktion | Anwendungsweite Warteschlange (einmal je Seite), wenn kein `ToastProvider` gesetzt ist. | `hooks/toast` |
| `@flowaudit/ui-react` | `sortRows` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `splitLine` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `useAuthToken` | Funktion | Zugangstoken aus einem `TokenStore` (`@flowaudit/common`), neu gerendert bei jeder Änderung. | `hooks/state` |
| `@flowaudit/ui-react` | `useBenford` | Funktion | React-Anbindung der Benford-Analyse aus `@flowaudit/ui-core` (dieselbe Logik wie `useBenford` in Vue). | `benford/useBenford` |
| `@flowaudit/ui-react` | `useClickOutside` | Funktion | Ruft `handler` bei Klick außerhalb der Elemente und bei Escape; abgemeldet beim Unmount. | `hooks/dom` |
| `@flowaudit/ui-react` | `useDebouncedCallback` | Funktion | Entprellte, stabile Funktion; ruft immer die neueste `fn` auf und verwirft einen ausstehenden Aufruf beim Unmount. | `hooks/state` |
| `@flowaudit/ui-react` | `useElementId` | Funktion | Stabile, CSS-taugliche Kennung je Instanz für aria-Verknüpfungen (wie `useId` der Vue-Fassung). | `store` |
| `@flowaudit/ui-react` | `useExtraction` | Funktion | React-Anbindung der Belegerkennung aus `@flowaudit/ui-core` (dieselbe Logik wie `useExtraction` in Vue). | `extraction/useExtraction` |
| `@flowaudit/ui-react` | `useLocale` | Funktion | Sprache: Prop vor Provider vor Standardsprache (`setDefaultLocale`). | `i18n` |
| `@flowaudit/ui-react` | `useMediaQuery` | Funktion | Stand einer Media-Query, z. B. `useMediaQuery('(max-width: 768px)')`; serverseitig `false`. | `hooks/dom` |
| `@flowaudit/ui-react` | `useRiskFlags` | Funktion | React-Anbindung des Zustandsautomaten aus `@flowaudit/ui-core` (dieselbe Logik wie `useRiskFlags`/`useRiskProfile` in Vue). | `risk/useRiskFlags` |
| `@flowaudit/ui-react` | `useSampling` | Funktion | React-Anbindung des Stichprobenrechners aus `@flowaudit/ui-core` (dieselbe Logik wie `useSampling` in Vue). | `sampling/useSampling` |
| `@flowaudit/ui-react` | `useScreeningReview` | Funktion | React-Anbindung des Zustandsautomaten aus `@flowaudit/ui-core` (dieselbe Logik wie `useScreeningReview` in Vue). | `screening/useScreeningReview` |
| `@flowaudit/ui-react` | `useSort` | Funktion | Sortierzustand und sortierte Zeilen (Kern `table/sort` aus `@flowaudit/common`). | `hooks/state` |
| `@flowaudit/ui-react` | `useStoreState` | Funktion | Stand eines Kern-Controllers (`@flowaudit/ui-core`) als React-Zustand. | `store` |
| `@flowaudit/ui-react` | `useToast` | Funktion | Toasts über der framework-freien Warteschlange aus `@flowaudit/common` (Provider, sonst gemeinsame Warteschlange). | `hooks/toast` |
| `@flowaudit/ui-react` | `useTranslation` | Funktion | Übersetzung mit den Katalogen aus `@flowaudit/ui-core` (gleiche Texte wie die Vue-Fassung). | `i18n` |
| `@flowaudit/ui-react/elements` | `BaseElementProps` | Schnittstelle | – | `legacy/createElementComponent` |
| `@flowaudit/ui-react/elements` | `ElementComponentOptions` | Schnittstelle | – | `legacy/createElementComponent` |
| `@flowaudit/ui-react/elements` | `EventHandlers` | Typ | Ereignis-Handler einer Hülle erhalten das erste Argument des Vue-emit (CustomEvent.detail[0]). | `legacy/createElementComponent` |
| `@flowaudit/ui-react/elements` | `FlowauditKanbanBoard` | Konstante | `<flowaudit-kanban-board>` als React-Komponente. | `legacy/kanban` |
| `@flowaudit/ui-react/elements` | `FlowauditKanbanBoardProps` | Schnittstelle | – | `legacy/kanban` |
| `@flowaudit/ui-react/elements` | `FlowauditKanbanBoards` | Konstante | `<flowaudit-kanban-boards>` (Boardliste) als React-Komponente. | `legacy/kanban` |
| `@flowaudit/ui-react/elements` | `FlowauditKanbanBoardsProps` | Schnittstelle | – | `legacy/kanban` |
| `@flowaudit/ui-react/elements` | `createElementComponent` | Funktion | Erzeugt eine React-18-Komponente für ein Custom Element. | `legacy/createElementComponent` |
| `@flowaudit/ui-react/elements` | `defineFlowauditElements` | Re-Export | – | `@flowaudit/ui/elements` |
| `@flowaudit/ui-react/elements` | `eventPayload` | Funktion | Liest das erste emit-Argument aus Vue-CustomEvents (detail ist ein Argument-Array). | `legacy/createElementComponent` |
<!-- api-overview:end -->

## Konfiguration

- `FlowauditTable`: `columns`, `rows`, `rowKey`, `caption`, `emptyText`,
  `clickable`, `locale`, `sort`/`defaultSort`, `renderCell`;
  `onRowClick`, `onSortChange`.
- `FlowauditSynopsis`: `comparison` oder `result` oder `comparisonId` mit
  `port`, `title`, `oldLabel`, `newLabel`, `editable`, `locale`,
  `layout`/`defaultLayout`; `onLayoutChange`, `onRowUpdate`, `onExport`,
  `onNavigate`; über `ref` `next()`, `previous()`, `exportAs(format)`.
  Vertrag: [`docs/ui/synopsis-rest.md`](../../docs/ui/synopsis-rest.md).
- `FlowauditVvt` (`port`, `actor`, `editable`, `locale`; `onDraftSaved`,
  `onReleased`, `onExported`, `onError`) und `FlowauditDsfa` (`port`,
  `activityId`, `actor`, `editable`, `locale`; `onAssessmentChange`,
  `onError`), Vertrag `dataprotection_ui/1`
  ([`docs/ui/dataprotection-rest.md`](../../docs/ui/dataprotection-rest.md)).
- `FlowauditGeoMap` (`port`, `points`, `areas`, `tiles`, `center`, `zoom`,
  `locale`; `onRadiusCompleted`, `onLocationChecked`, `onAreasLoaded`,
  `onReferenceChange`, `onError`), Vertrag `auditcore_geo.web`
  ([`docs/ui/geo-rest.md`](../../docs/ui/geo-rest.md)); Leaflet lädt erst beim Anzeigen.
- `FlowauditRiskFlags` (`evaluation`, `profile`, `port`, `heading`,
  `locale`; `onRecordSelect(index | null)`, `onFilterChange(filter)`),
  Vertrag `auditcore_risk.web` ([`docs/ui/risk-rest.md`](../../docs/ui/risk-rest.md));
  Teilkomponenten `RiskFlagSummary`, `RiskFlagFilter` (gesteuert:
  `filter`/`onFilterChange`), `RiskFlagTable`, `RiskFlagCard`,
  `RiskFlagState`, `RiskRecordDetail`, `RiskProfileInfo`.
- `FlowauditScreeningReview` (`port`, `runId`, `locale`;
  `onRunCreated({ runId })`, `onDecided({ runId, hitId, status })`,
  `onError(error)`), Vertrag `screening_review/1`
  ([`docs/ui/screening-rest.md`](../../docs/ui/screening-rest.md)).
- `FlowauditSampling` (`port`, `items`, `locale`; `onSizeCalculated`,
  `onSelectionDrawn`, `onError`), Vertrag `auditcore_sampling.web`
  ([`docs/ui/sampling-rest.md`](../../docs/ui/sampling-rest.md)), und
  `FlowauditBenford` (`port`, `values`, `locale`; `onAnalysisCompleted`,
  `onError`), Vertrag `auditcore_statistics.web`
  ([`docs/ui/benford-rest.md`](../../docs/ui/benford-rest.md)); beide mit
  Datei-Import `TableImport`.
- Hooks: `useSort`, `useToast` (mit `ToastProvider`), `useMediaQuery`,
  `useClickOutside`, `useDebouncedCallback`, `useAuthToken`,
  `useTranslation`, `useStoreState`.
- Theming wie in `@flowaudit/ui` über die CSS-Variablen `--fa-*`.

## Herkunft und Charakterisierung

Neu in auditcore entwickelt. Bis 0.2.0 enthielt das Paket nur Hüllen um die
Web Components aus `@flowaudit/ui` (PR #80, #84, #83, #111, #88, #146,
Geo-Karte); ab 1.0.0 sind Basis, Tabelle, Synopse, VVT, DSFA, Geo-Karte,
Risiko-Merkmale, Screening, Stichprobe und Benford eigenständige
React-Implementierungen desselben Vertrags. Parität zur Vue-Fassung: dieselben
Fälle (`ui-core/test/parity`) gegen beide Fassungen, dazu ein Vergleich des
normalisierten DOM und des Formularzustands Vue ↔ React, auch nach
Interaktionen ([Parität Vue ↔ React](../../docs/ui/react-paritaet.md)).
Die Hooks (0.2.0) folgen [`docs/reports/app-helfer-ts.md`](../../docs/reports/app-helfer-ts.md)
(Abschnitt 7); ihre Logik steckt in `@flowaudit/common`.

## Abhängigkeiten

- `@flowaudit/ui-core` 0.1.0 und `@flowaudit/common` 0.1.0 (Laufzeit)
- `react` ^18.3.0 und `react-dom` ^18.3.0 (Peer-Abhängigkeiten)
- nur für `@flowaudit/ui-react/elements` (optional): `@flowaudit/ui` ^0.3.0,
  `@flowaudit/kanban-core` ^0.1.0 und `vue` ^3.5.0

Node ≥ 20.19 für Bau und Tests.

## Sicherheit und Datenschutz

Die Komponenten erzeugen kein HTML aus Strings (kein
`dangerouslySetInnerHTML`) und greifen nicht auf Netzwerk oder
Browser-Speicher zu; Daten kommen über Props oder die Ports der Anwendung.
Exporte escapen alle Inhalte (Kern `@flowaudit/ui-core`), CSV mit
Formelschutz. Vier-Augen-Hinweise sind reine Anzeige, maßgeblich ist die
Prüfung des Servers. `useAuthToken` liest und schreibt nur über den
`TokenStore`, den die Anwendung übergibt.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Neu entwickelt, kein übernommener Fremdcode.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
