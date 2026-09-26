# @auditcore/ui-react

## Zweck

Native React-Komponenten (React 18/19) der FlowAudit-Oberflächen von Tabelle bis Kanban – ohne Vue, auf den Kernen `@auditcore/ui-core` und `@auditcore/kanban-core`.

Für React-Anwendungen wie regulierung. Die Komponenten erfüllen dieselben
Verträge wie die Vue-Fassung `@auditcore/ui`: gleiche Props- und
Ereignis-Semantik, gleiche REST-Verträge, gleiche Texte, gleiches Markup
und gleiche Barrierefreiheit (Tastatur, ARIA). Fachlogik, Texte und
Zustandsautomaten kommen aus `@auditcore/ui-core` (Kanban: `@auditcore/kanban-core`); dieses Paket enthält nur
die React-Darstellung. Dazu kommen React-Hooks auf Basis von
`@auditcore/common` (Toasts, Media-Query, Klick außerhalb, Sortierung,
Entprellen, Token).

## Installation

Standardweg ist die npm-Registry; npm löst die übrigen `@auditcore`-Pakete
der Abhängigkeitshülle selbst auf:

```sh
npm install @auditcore/ui-react
```

Ohne Registry-Zugang (Intranet, offline) bleibt der signierte Tarball aus
dem GitHub-Release von auditcore; dann gehört jedes Paket der Hülle
ausdrücklich in die `package.json`:

```sh
npm install @auditcore/ui-react@https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore-ui-react-1.1.0.tgz
```

Anleitung für Vue, React und Web Components mit Integritätsprüfung und
`vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

Abhängigkeitshülle: dazu `@auditcore/ui-core`, `@auditcore/kanban-core` und `@auditcore/common`; Peer-Abhängigkeiten `react` und `react-dom` (18.3 oder 19), kein Vue. Stile: `@auditcore/ui-core/style.css`.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @auditcore/ui-react`).

## Schnellstart

```tsx
import { FlowauditSynopsis, FlowauditTable, createSynopsisRestClient } from '@auditcore/ui-react'
import type { TableColumn } from '@auditcore/common'
import '@auditcore/ui-core/style.css'

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

Kanban-Board über den REST-Vertrag von `auditcore_kanban` (`docs/kanban/rest-api.md`):

```tsx
import { RestBoardPort } from '@auditcore/kanban-core'
import { FlowauditKanbanBoard, FlowauditKanbanBoards } from '@auditcore/ui-react'
import { useState } from 'react'
import '@auditcore/ui-core/style.css'

const port = new RestBoardPort({ baseUrl: '/api/kanban', userId: 'anna.becker' })

export function Aufgaben() {
  const [boardId, setBoardId] = useState('')
  return (
    <>
      <FlowauditKanbanBoards port={port} activeId={boardId} onBoardSelect={setBoardId} />
      {boardId ? <FlowauditKanbanBoard port={port} boardId={boardId} onCardOpen={(card) => console.info(card.id)} /> : null}
    </>
  )
}
```

## Einbindung

- **React:** Komponenten wie gewohnt einsetzen und einmal
  `@auditcore/ui-core/style.css` laden. Sprache über die Prop `locale`, einen
  `LocaleProvider` oder `setDefaultLocale`. Ereignisse sind `onXxx`-Props und
  erhalten die Nutzdaten direkt (z. B. `onRowUpdate(update)`,
  `onAssessmentChange({ step, id, version, status })`). Was in Vue ein
  `v-model` ist, ist hier gesteuert (`sort`/`onSortChange`,
  `layout`/`onLayoutChange`) oder ungesteuert (`defaultSort`,
  `defaultLayout`); der Vue-Slot `cell-<key>` heißt `renderCell`.
- **Ports:** Datenzugriffe laufen über Ports aus `@auditcore/ui-core`
  (`createSynopsisRestClient`, `createDataProtectionRestPort`), `fetch` und
  Kopfzeilen sind injizierbar (Anmeldetoken der Anwendung).
- **Kanban:** `FlowauditKanbanBoard` und `FlowauditKanbanBoards` sind nativ
  (Zustandsautomaten aus `@auditcore/kanban-core`: `createBoardController`,
  `createMoveController`, `createPointerDrag`, `createBoardListController`,
  `createColumnEditor`, `createShareSearch`). Ohne `port` bearbeitet das
  Board ein übergebenes `board` lokal (In-Memory). Tastatur: Leertaste nimmt
  eine Karte auf, Pfeiltasten verschieben, Leertaste legt ab, Escape bricht ab,
  Strg+Pfeil verschiebt direkt; Board-Kürzel N, F und /.
  (`defineFlowauditElements()` aufrufen, `@auditcore/ui/style.css` laden,
  `@auditcore/ui` und Vue installieren).

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
  4. Export in `src/index.ts`.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (241):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@auditcore/ui-react` | `Badge` | Funktion | – | `base/Badge` |
| `@auditcore/ui-react` | `BadgeProps` | Schnittstelle | – | `base/Badge` |
| `@auditcore/ui-react` | `BenfordAnalysis` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `BenfordInputs` | Schnittstelle | – | `benford/useBenford` |
| `@auditcore/ui-react` | `BenfordPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `Button` | Funktion | Schaltfläche wie `FaButton` (gleiche Klassen, ARIA und Zustände). | `base/Button` |
| `@auditcore/ui-react` | `ButtonProps` | Schnittstelle | – | `base/Button` |
| `@auditcore/ui-react` | `CardAppearance` | Funktion | Kartendesign wie `CardAppearance.vue`: Farbe, eigene Farbe, Hintergrundbild (höchstens 2 MB). | `kanban/CardAppearance` |
| `@auditcore/ui-react` | `CardAppearanceProps` | Schnittstelle | – | `kanban/CardAppearance` |
| `@auditcore/ui-react` | `CardChecklistEditor` | Funktion | Checkliste einer Karte wie `CardChecklistEditor.vue`. | `kanban/CardChecklistEditor` |
| `@auditcore/ui-react` | `CardChecklistEditorProps` | Schnittstelle | – | `kanban/CardChecklistEditor` |
| `@auditcore/ui-react` | `CardReferences` | Funktion | Verknüpfungen und Anhänge einer Karte wie `CardReferences.vue`. | `kanban/CardReferences` |
| `@auditcore/ui-react` | `CardReferencesProps` | Schnittstelle | – | `kanban/CardReferences` |
| `@auditcore/ui-react` | `CardTagsEditor` | Funktion | Tags einer Karte wie `CardTagsEditor.vue` (Enter fügt hinzu, Schaltfläche entfernt). | `kanban/CardTagsEditor` |
| `@auditcore/ui-react` | `CardTagsEditorProps` | Schnittstelle | – | `kanban/CardTagsEditor` |
| `@auditcore/ui-react` | `CellValue` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `ColumnEditorRow` | Funktion | Zeile des Spalteneditors wie `ColumnEditorRow.vue`. | `kanban/ColumnEditorRow` |
| `@auditcore/ui-react` | `ColumnEditorRowProps` | Schnittstelle | – | `kanban/ColumnEditorRow` |
| `@auditcore/ui-react` | `Comparison` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ComparisonForm` | Funktion | Formular „Neuer Vergleich“ wie `ComparisonForm.vue`. | `documents/ComparisonForm` |
| `@auditcore/ui-react` | `ComparisonFormProps` | Schnittstelle | – | `documents/ComparisonForm` |
| `@auditcore/ui-react` | `ComparisonList` | Funktion | Gespeicherte Vergleiche mit Suche, Öffnen, Löschen und JSON-Import (wie `ComparisonList.vue`). | `documents/ComparisonList` |
| `@auditcore/ui-react` | `ComparisonListProps` | Schnittstelle | – | `documents/ComparisonList` |
| `@auditcore/ui-react` | `ComparisonResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ComparisonsError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ComparisonsInputs` | Schnittstelle | – | `documents/useComparisons` |
| `@auditcore/ui-react` | `ComparisonsPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `DataProtectionError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `DataProtectionPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `DbKanbanCard` | Funktion | Karte der Datenbankansicht wie `DbKanbanCard.vue` (Ziehen, Strg+Pfeil). | `dbkanban/DbKanbanCard` |
| `@auditcore/ui-react` | `DbKanbanCardProps` | Schnittstelle | – | `dbkanban/DbKanbanCard` |
| `@auditcore/ui-react` | `DbKanbanColumn` | Funktion | Spalte der Datenbankansicht wie `DbKanbanColumn.vue` (Ablegen setzt den Wert). | `dbkanban/DbKanbanColumn` |
| `@auditcore/ui-react` | `DbKanbanColumnProps` | Schnittstelle | – | `dbkanban/DbKanbanColumn` |
| `@auditcore/ui-react` | `DbKanbanError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `DbKanbanInputs` | Schnittstelle | – | `dbkanban/useDbKanban` |
| `@auditcore/ui-react` | `DecimalSeparator` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `Delimiter` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `Dialog` | Funktion | Modaler Dialog wie `FaDialog`: Fokusfalle, Escape, Rückgabe des Fokus, beschriftet über Titel und Beschreibung. | `base/Dialog` |
| `@auditcore/ui-react` | `DialogProps` | Schnittstelle | – | `base/Dialog` |
| `@auditcore/ui-react` | `DownloadFile` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `DsfaStep` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `Evaluation` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `EvaluationResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ExportPayload` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ExtractionInputs` | Schnittstelle | – | `extraction/useExtraction` |
| `@auditcore/ui-react` | `ExtractionPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ExtractionRun` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ExtrapolationInputs` | Schnittstelle | – | `extrapolation/useExtrapolation` |
| `@auditcore/ui-react` | `ExtrapolationPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `FetchLike` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `FlowauditBenford` | Funktion | Benford-Analyse als native React-Komponente (Vertrag wie `<flowaudit-benford>`): Werte (Eigenschaft oder Datei), Test, Bewertungsprofil, Kennzahlen mit MAD, Chi² und z je Ziffer, S … | `benford/FlowauditBenford` |
| `@auditcore/ui-react` | `FlowauditBenfordProps` | Typ | – | `benford/FlowauditBenford` |
| `@auditcore/ui-react` | `FlowauditComparisons` | Konstante | Dokumentvergleiche als native React-Komponente (Vertrag wie `<flowaudit-comparisons>`): zwei Fassungen hochladen, gespeicherte Vergleiche suchen, öffnen (eingebettete Synopse), lös … | `documents/FlowauditComparisons` |
| `@auditcore/ui-react` | `FlowauditComparisonsHandle` | Schnittstelle | – | `documents/FlowauditComparisons` |
| `@auditcore/ui-react` | `FlowauditComparisonsProps` | Schnittstelle | – | `documents/FlowauditComparisons` |
| `@auditcore/ui-react` | `FlowauditDbKanban` | Funktion | Datenbankansicht als Kanban, native React-Komponente (Vertrag wie `<flowaudit-db-kanban>`): Datensätze nach einer Auswahl-Eigenschaft gruppiert, Ablegen oder Strg+Pfeil setzt den Z … | `dbkanban/FlowauditDbKanban` |
| `@auditcore/ui-react` | `FlowauditDbKanbanProps` | Typ | – | `dbkanban/FlowauditDbKanban` |
| `@auditcore/ui-react` | `FlowauditDsfa` | Funktion | Datenschutz-Folgenabschätzung (Art. 35 DSGVO) als native React-Komponente – Vertrag, Texte und Ablauf wie `<flowaudit-dsfa>`: Übersicht, Schwellwertanalyse, Risiko, Vorschlag der B … | `dataprotection/FlowauditDsfa` |
| `@auditcore/ui-react` | `FlowauditDsfaProps` | Schnittstelle | – | `dataprotection/FlowauditDsfa` |
| `@auditcore/ui-react` | `FlowauditExtraction` | Funktion | Belegerkennung als native React-Komponente (Vertrag wie `<flowaudit-extraction>`): Dokument hochladen, Profil wählen, erkannte Felder mit Konfidenz und Validierungsbefunde. | `extraction/FlowauditExtraction` |
| `@auditcore/ui-react` | `FlowauditExtractionProps` | Typ | – | `extraction/FlowauditExtraction` |
| `@auditcore/ui-react` | `FlowauditExtrapolation` | Funktion | Hochrechnung von Stichprobenfehlern als native React-Komponente (Vertrag wie `<flowaudit-extrapolation>`): Methode und Konfidenzniveau, Schichten und geprüfte Einheiten mit zufälli … | `extrapolation/FlowauditExtrapolation` |
| `@auditcore/ui-react` | `FlowauditExtrapolationProps` | Typ | – | `extrapolation/FlowauditExtrapolation` |
| `@auditcore/ui-react` | `FlowauditGeoMap` | Funktion | Geo-Karte als native React-Komponente (Vertrag wie `<flowaudit-geo-map>`): Karte, Bezugspunkt mit UTM, Umkreis, Punkt in Fläche, Vereinfachung, GeoPackage. | `geo/FlowauditGeoMap` |
| `@auditcore/ui-react` | `FlowauditGeoMapProps` | Schnittstelle | – | `geo/FlowauditGeoMap` |
| `@auditcore/ui-react` | `FlowauditIdentifierCheck` | Funktion | „Kennung prüfen“ als native React-Komponente (Vertrag wie `<flowaudit-identifier-check>`): Prüfprofil, Einzelprüfung mit Begründung und Stapelprüfung aus einer Tabelle. | `identifiers/FlowauditIdentifierCheck` |
| `@auditcore/ui-react` | `FlowauditIdentifierCheckProps` | Typ | – | `identifiers/FlowauditIdentifierCheck` |
| `@auditcore/ui-react` | `FlowauditKanbanBoard` | Konstante | – | `kanban/FlowauditKanbanBoard` |
| `@auditcore/ui-react` | `FlowauditKanbanBoardHandle` | Schnittstelle | Methoden über `ref` (wie `defineExpose` der Vue-Fassung). | `kanban/FlowauditKanbanBoard` |
| `@auditcore/ui-react` | `FlowauditKanbanBoardProps` | Schnittstelle | – | `kanban/FlowauditKanbanBoard` |
| `@auditcore/ui-react` | `FlowauditKanbanBoards` | Konstante | Boardliste wie `KanbanBoardList.vue` (eigene und geteilte Boards, Anheften, Löschen, Anlegen). | `kanban/FlowauditKanbanBoards` |
| `@auditcore/ui-react` | `FlowauditKanbanBoardsHandle` | Schnittstelle | – | `kanban/FlowauditKanbanBoards` |
| `@auditcore/ui-react` | `FlowauditKanbanBoardsProps` | Schnittstelle | – | `kanban/FlowauditKanbanBoards` |
| `@auditcore/ui-react` | `FlowauditReportExport` | Funktion | Tabellenexport nach Excel als native React-Komponente (Vertrag wie `<flowaudit-report-export>`): Formatprofil wählen, Vorschau der Spaltenformate und ersten Zeilen, XLSX-Export. | `reporting/FlowauditReportExport` |
| `@auditcore/ui-react` | `FlowauditReportExportProps` | Typ | – | `reporting/FlowauditReportExport` |
| `@auditcore/ui-react` | `FlowauditRiskFlags` | Funktion | Risiko-Merkmale als native React-Komponente – Vertrag, Texte und Markup wie `<flowaudit-risk-flags>`: Verteilung je Merkmal, Filter, Tabelle je Datensatz, Detailkarten mit Begründu … | `risk/FlowauditRiskFlags` |
| `@auditcore/ui-react` | `FlowauditRiskFlagsProps` | Schnittstelle | – | `risk/FlowauditRiskFlags` |
| `@auditcore/ui-react` | `FlowauditSampling` | Funktion | Stichprobenrechner als native React-Komponente (Vertrag wie `<flowaudit-sampling>`): Methodenprofil, Stichprobenumfang mit Herleitung, Grundgesamtheit (Eigenschaft oder Datei), Aus … | `sampling/FlowauditSampling` |
| `@auditcore/ui-react` | `FlowauditSamplingProps` | Typ | – | `sampling/FlowauditSampling` |
| `@auditcore/ui-react` | `FlowauditScreeningReview` | Funktion | Screening-Trefferprüfung (Sanktionslisten, PEP) als native React-Komponente – Vertrag, Texte und Ablauf wie `<flowaudit-screening-review>`: Prüflauf anlegen, Treffer filtern, vergl … | `screening/FlowauditScreeningReview` |
| `@auditcore/ui-react` | `FlowauditScreeningReviewProps` | Schnittstelle | – | `screening/FlowauditScreeningReview` |
| `@auditcore/ui-react` | `FlowauditSynopsis` | Konstante | Synopse / Versionsvergleich als native React-Komponente (Vertrag wie `<flowaudit-synopsis>`): Seiten- oder Inline-Ansicht, Wortdifferenz, Filter, Navigation mit N/J und P/K, Export … | `synopsis/FlowauditSynopsis` |
| `@auditcore/ui-react` | `FlowauditSynopsisHandle` | Schnittstelle | Methoden über `ref` (wie `defineExpose` der Vue-Fassung). | `synopsis/FlowauditSynopsis` |
| `@auditcore/ui-react` | `FlowauditSynopsisProps` | Schnittstelle | – | `synopsis/FlowauditSynopsis` |
| `@auditcore/ui-react` | `FlowauditTable` | Funktion | Tabelle wie `FaTable`: Sortierung per Schaltfläche (aria-sort), anklickbare Zeilen per Maus und Enter. | `table/FlowauditTable` |
| `@auditcore/ui-react` | `FlowauditTableProps` | Schnittstelle | – | `table/FlowauditTable` |
| `@auditcore/ui-react` | `FlowauditVvt` | Funktion | Verzeichnis von Verarbeitungstätigkeiten (Art. | `dataprotection/FlowauditVvt` |
| `@auditcore/ui-react` | `FlowauditVvtProps` | Schnittstelle | – | `dataprotection/FlowauditVvt` |
| `@auditcore/ui-react` | `GeoArea` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `GeoPoint` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `GeoPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `HitView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `Icon` | Funktion | – | `base/Icon` |
| `@auditcore/ui-react` | `IconProps` | Schnittstelle | – | `base/Icon` |
| `@auditcore/ui-react` | `IdentifierBatchAnswer` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `IdentifierInputs` | Schnittstelle | – | `identifiers/useIdentifierCheck` |
| `@auditcore/ui-react` | `IdentifierResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `IdentifiersPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ImportRequest` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ImportedColumns` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `KanbanCard` | Funktion | Karte wie `KanbanCard.vue` (gleiches Markup, Tastatur und Zeiger über das Board). | `kanban/KanbanCard` |
| `@auditcore/ui-react` | `KanbanCardDetail` | Funktion | Detailansicht einer Karte wie `KanbanCardDetail.vue` (seitlicher Dialog). | `kanban/KanbanCardDetail` |
| `@auditcore/ui-react` | `KanbanCardDetailProps` | Schnittstelle | – | `kanban/KanbanCardDetail` |
| `@auditcore/ui-react` | `KanbanCardProps` | Schnittstelle | – | `kanban/KanbanCard` |
| `@auditcore/ui-react` | `KanbanColumn` | Funktion | Spalte wie `KanbanColumn.vue` (Kopf mit WIP-Anzeige, Kartenliste, Hinzufügen). | `kanban/KanbanColumn` |
| `@auditcore/ui-react` | `KanbanColumnProps` | Schnittstelle | – | `kanban/KanbanColumn` |
| `@auditcore/ui-react` | `KanbanSettingsDialog` | Funktion | Spalten, Farben und WIP-Limits wie `KanbanSettingsDialog.vue` (Prüfung über die Kernlogik). | `kanban/KanbanSettingsDialog` |
| `@auditcore/ui-react` | `KanbanSettingsDialogProps` | Schnittstelle | – | `kanban/KanbanSettingsDialog` |
| `@auditcore/ui-react` | `KanbanShareDialog` | Funktion | Freigaben eines Boards wie `KanbanShareDialog.vue` (Personensuche, Rechte, Entfernen mit Bestätigung). | `kanban/KanbanShareDialog` |
| `@auditcore/ui-react` | `KanbanShareDialogProps` | Schnittstelle | – | `kanban/KanbanShareDialog` |
| `@auditcore/ui-react` | `KanbanToolbar` | Funktion | Werkzeugleiste wie `KanbanToolbar.vue` (Titel, Fortschritt, Suche, Filter, Aktionen). | `kanban/KanbanToolbar` |
| `@auditcore/ui-react` | `KanbanToolbarProps` | Schnittstelle | – | `kanban/KanbanToolbar` |
| `@auditcore/ui-react` | `LatLon` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `Locale` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `LocaleProvider` | Funktion | Sprache für alle Komponenten im Teilbaum (Gegenstück zu `provideLocale` in Vue). | `i18n` |
| `@auditcore/ui-react` | `NextSortOptions` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `NumberColumn` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `ParsedTable` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `PopulationItem` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ProfileDetail` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `RecordMove` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `RecordPort` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui-react` | `RecordRow` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui-react` | `RecordTable` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui-react` | `ReportExportInputs` | Schnittstelle | – | `reporting/useReportExport` |
| `@auditcore/ui-react` | `ReportTableInput` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ReportingPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ResidualResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `RestError` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `RestOptions` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `RiskFilter` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `RiskFlagCard` | Funktion | Treffer oder unbestimmtes Merkmal eines Datensatzes mit Begründung, Eingabewerten und Schwellen, wie `RiskFlagCard`. | `risk/RiskFlagCard` |
| `@auditcore/ui-react` | `RiskFlagCardProps` | Schnittstelle | – | `risk/RiskFlagCard` |
| `@auditcore/ui-react` | `RiskFlagFilter` | Funktion | Filter nach Merkmal, Zustand und Suchtext, wie `RiskFlagFilter`. | `risk/RiskFlagFilter` |
| `@auditcore/ui-react` | `RiskFlagFilterProps` | Schnittstelle | – | `risk/RiskFlagFilter` |
| `@auditcore/ui-react` | `RiskFlagState` | Funktion | Zustand eines Merkmals mit Symbol (Farbe ist nie der einzige Bedeutungsträger), wie `RiskFlagState`. | `risk/RiskFlagState` |
| `@auditcore/ui-react` | `RiskFlagStateProps` | Schnittstelle | – | `risk/RiskFlagState` |
| `@auditcore/ui-react` | `RiskFlagSummary` | Funktion | Verteilung je Merkmal mit Summen und Befunden über alle Datensätze, wie `RiskFlagSummary`. | `risk/RiskFlagSummary` |
| `@auditcore/ui-react` | `RiskFlagSummaryProps` | Schnittstelle | – | `risk/RiskFlagSummary` |
| `@auditcore/ui-react` | `RiskFlagTable` | Funktion | Merkmale je Datensatz; Zeilen per Maus und Enter wählbar, wie `RiskFlagTable`. | `risk/RiskFlagTable` |
| `@auditcore/ui-react` | `RiskFlagTableProps` | Schnittstelle | – | `risk/RiskFlagTable` |
| `@auditcore/ui-react` | `RiskPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `RiskProfileInfo` | Funktion | Profil, Regeln und Eingabefelder (Pflicht/optional, Folge bei Fehlen), wie `RiskProfileInfo`. | `risk/RiskProfileInfo` |
| `@auditcore/ui-react` | `RiskProfileInfoProps` | Schnittstelle | – | `risk/RiskProfileInfo` |
| `@auditcore/ui-react` | `RiskRecordDetail` | Funktion | Detailansicht eines Datensatzes (Karten je Treffer/unbestimmtem Merkmal, Bewertung), wie `RiskRecordDetail`. | `risk/RiskRecordDetail` |
| `@auditcore/ui-react` | `RiskRecordDetailProps` | Schnittstelle | – | `risk/RiskRecordDetail` |
| `@auditcore/ui-react` | `RowUpdate` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `RunView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `SamplingInputs` | Schnittstelle | – | `sampling/useSampling` |
| `@auditcore/ui-react` | `SamplingPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ScreeningError` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ScreeningPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `SelectionResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `SettingsView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `SizeResult` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `SortDirection` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `SortState` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `SourcesView` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `SynopsisLayout` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `SynopsisPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `TableColumn` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `TableImport` | Funktion | Datei-Import wie `TableImport` (Vue): CSV/TSV/Text lesen, Spalten zuordnen, Werte übernehmen. | `tabular/TableImport` |
| `@auditcore/ui-react` | `TableImportProps` | Schnittstelle | – | `tabular/TableImport` |
| `@auditcore/ui-react` | `TableRow` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `TextField` | Funktion | Eingabefeld wie `FaTextField` (Beschriftung, Hinweis, Fehler mit aria-describedby). | `base/TextField` |
| `@auditcore/ui-react` | `TextFieldProps` | Schnittstelle | – | `base/TextField` |
| `@auditcore/ui-react` | `TileSource` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ToastProvider` | Funktion | Stellt eine eigene Warteschlange für den Teilbaum bereit (z. B. je Mandant oder im Test). | `hooks/toast` |
| `@auditcore/ui-react` | `UseAuthToken` | Schnittstelle | – | `hooks/state` |
| `@auditcore/ui-react` | `UseBenford` | Schnittstelle | – | `benford/useBenford` |
| `@auditcore/ui-react` | `UseComparisons` | Schnittstelle | – | `documents/useComparisons` |
| `@auditcore/ui-react` | `UseDbKanban` | Schnittstelle | – | `dbkanban/useDbKanban` |
| `@auditcore/ui-react` | `UseExtraction` | Schnittstelle | – | `extraction/useExtraction` |
| `@auditcore/ui-react` | `UseExtrapolation` | Schnittstelle | – | `extrapolation/useExtrapolation` |
| `@auditcore/ui-react` | `UseIdentifierCheck` | Schnittstelle | – | `identifiers/useIdentifierCheck` |
| `@auditcore/ui-react` | `UseReportExport` | Schnittstelle | – | `reporting/useReportExport` |
| `@auditcore/ui-react` | `UseRiskFlags` | Schnittstelle | – | `risk/useRiskFlags` |
| `@auditcore/ui-react` | `UseSampling` | Schnittstelle | – | `sampling/useSampling` |
| `@auditcore/ui-react` | `UseScreeningReview` | Schnittstelle | – | `screening/useScreeningReview` |
| `@auditcore/ui-react` | `UseSort` | Schnittstelle | – | `hooks/state` |
| `@auditcore/ui-react` | `UseSortOptions` | Schnittstelle | – | `hooks/state` |
| `@auditcore/ui-react` | `UseToast` | Schnittstelle | – | `hooks/toast` |
| `@auditcore/ui-react` | `UseTranslation` | Schnittstelle | – | `i18n` |
| `@auditcore/ui-react` | `VvtExport` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `WorkbookPreview` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `ariaSort` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `columnCells` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `compareValues` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `createBenfordRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `createDataProtectionRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `createExtractionRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `createExtrapolationRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `createGeoRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `createIdentifiersRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `createMemoryRecordPort` | Re-Export | – | `@auditcore/kanban-core` |
| `@auditcore/ui-react` | `createReportingRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `createRiskRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `createSamplingRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `createScreeningRestPort` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `createSynopsisRestClient` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `detectDecimal` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `detectDelimiter` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `formatDate` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `formatNumber` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `formatPercent` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `guessNumberColumn` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `localeTag` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `nextSort` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `numberColumn` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `parseNumber` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `parseTable` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `requestFile` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `requestJson` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `saveFile` | Re-Export | – | `@auditcore/common/browser` |
| `@auditcore/ui-react` | `setDefaultLocale` | Re-Export | – | `@auditcore/ui-core` |
| `@auditcore/ui-react` | `sharedToastQueue` | Funktion | Anwendungsweite Warteschlange (einmal je Seite), wenn kein `ToastProvider` gesetzt ist. | `hooks/toast` |
| `@auditcore/ui-react` | `sortRows` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `splitLine` | Re-Export | – | `@auditcore/common` |
| `@auditcore/ui-react` | `useAuthToken` | Funktion | Zugangstoken aus einem `TokenStore` (`@auditcore/common`), neu gerendert bei jeder Änderung. | `hooks/state` |
| `@auditcore/ui-react` | `useBenford` | Funktion | React-Anbindung der Benford-Analyse aus `@auditcore/ui-core` (dieselbe Logik wie `useBenford` in Vue). | `benford/useBenford` |
| `@auditcore/ui-react` | `useClickOutside` | Funktion | Ruft `handler` bei Klick außerhalb der Elemente und bei Escape; abgemeldet beim Unmount. | `hooks/dom` |
| `@auditcore/ui-react` | `useComparisons` | Funktion | React-Anbindung der Vergleichsverwaltung aus `@auditcore/ui-core` (dieselbe Logik wie `useComparisons` in Vue). | `documents/useComparisons` |
| `@auditcore/ui-react` | `useDbKanban` | Funktion | React-Anbindung der Datenbankansicht aus `@auditcore/ui-core` (dieselbe Logik wie `useDbKanban` in Vue). | `dbkanban/useDbKanban` |
| `@auditcore/ui-react` | `useDebouncedCallback` | Funktion | Entprellte, stabile Funktion; ruft immer die neueste `fn` auf und verwirft einen ausstehenden Aufruf beim Unmount. | `hooks/state` |
| `@auditcore/ui-react` | `useElementId` | Funktion | Stabile, CSS-taugliche Kennung je Instanz für aria-Verknüpfungen (wie `useId` der Vue-Fassung). | `store` |
| `@auditcore/ui-react` | `useExtraction` | Funktion | React-Anbindung der Belegerkennung aus `@auditcore/ui-core` (dieselbe Logik wie `useExtraction` in Vue). | `extraction/useExtraction` |
| `@auditcore/ui-react` | `useExtrapolation` | Funktion | React-Anbindung der Hochrechnung aus `@auditcore/ui-core` (dieselbe Logik wie `useExtrapolation` in Vue). | `extrapolation/useExtrapolation` |
| `@auditcore/ui-react` | `useIdentifierCheck` | Funktion | React-Anbindung von „Kennung prüfen“ aus `@auditcore/ui-core` (dieselbe Logik wie `useIdentifierCheck` in Vue). | `identifiers/useIdentifierCheck` |
| `@auditcore/ui-react` | `useKanbanBoard` | Funktion | – | `kanban/useKanbanBoard` |
| `@auditcore/ui-react` | `useKanbanMover` | Funktion | Verschieben per Tastatur und Zeiger über dem Board-Controller. | `kanban/useKanbanBoard` |
| `@auditcore/ui-react` | `useKanbanShortcuts` | Funktion | Tastenkürzel N, F und /, solange das Board angezeigt wird. | `kanban/useKanbanBoard` |
| `@auditcore/ui-react` | `useLocale` | Funktion | Sprache: Prop vor Provider vor Standardsprache (`setDefaultLocale`). | `i18n` |
| `@auditcore/ui-react` | `useMediaQuery` | Funktion | Stand einer Media-Query, z. B. `useMediaQuery('(max-width: 768px)')`; serverseitig `false`. | `hooks/dom` |
| `@auditcore/ui-react` | `useReportExport` | Funktion | React-Anbindung des Tabellenexports aus `@auditcore/ui-core` (dieselbe Logik wie `useReportExport` in Vue). | `reporting/useReportExport` |
| `@auditcore/ui-react` | `useRiskFlags` | Funktion | React-Anbindung des Zustandsautomaten aus `@auditcore/ui-core` (dieselbe Logik wie `useRiskFlags`/`useRiskProfile` in Vue). | `risk/useRiskFlags` |
| `@auditcore/ui-react` | `useSampling` | Funktion | React-Anbindung des Stichprobenrechners aus `@auditcore/ui-core` (dieselbe Logik wie `useSampling` in Vue). | `sampling/useSampling` |
| `@auditcore/ui-react` | `useScreeningReview` | Funktion | React-Anbindung des Zustandsautomaten aus `@auditcore/ui-core` (dieselbe Logik wie `useScreeningReview` in Vue). | `screening/useScreeningReview` |
| `@auditcore/ui-react` | `useSort` | Funktion | Sortierzustand und sortierte Zeilen (Kern `table/sort` aus `@auditcore/common`). | `hooks/state` |
| `@auditcore/ui-react` | `useStoreState` | Funktion | Stand eines Kern-Controllers (`@auditcore/ui-core`) als React-Zustand. | `store` |
| `@auditcore/ui-react` | `useToast` | Funktion | Toasts über der framework-freien Warteschlange aus `@auditcore/common` (Provider, sonst gemeinsame Warteschlange). | `hooks/toast` |
| `@auditcore/ui-react` | `useTranslation` | Funktion | Übersetzung mit den Katalogen aus `@auditcore/ui-core` (gleiche Texte wie die Vue-Fassung). | `i18n` |
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
- `FlowauditIdentifierCheck` (`port`, `locale`; `onIdentifierChecked`,
  `onBatchChecked`, `onError`), Vertrag `identifiers_ui/1`
  ([`docs/ui/identifiers-rest.md`](../../docs/ui/identifiers-rest.md)):
  Einzelprüfung mit Begründung und Stapelprüfung aus einer Tabelle.
- `FlowauditKanbanBoard`: `port` + `boardId` oder `board` (+ `userId`,
  `users`), `readOnly`, `sharedByName`, `showFullscreen`, `today`, `locale`,
  `renderCardExtra`; `onBoardChange`, `onError`, `onFullscreen`,
  `onNavigate(link, card)`, `onAttachment(attachment, card)`, `onCardOpen`;
  über `ref` `reload()` und `board`. `FlowauditKanbanBoards`: `port`,
  `activeId`, `now`, `locale`; `onBoardSelect`, `onCreated`; über `ref`
  `reload()`. Vertrag: [`docs/kanban/rest-api.md`](../../docs/kanban/rest-api.md).
- Bausteine wie in Vue: `KanbanCard`, `KanbanColumn`, `KanbanToolbar`,
  `KanbanCardDetail`, `KanbanSettingsDialog`, `KanbanShareDialog`,
  `CardAppearance`, `CardChecklistEditor`, `CardReferences`,
  `CardTagsEditor`, `ColumnEditorRow`, dazu `Dialog`.
- Hooks: `useSort`, `useToast` (mit `ToastProvider`), `useMediaQuery`,
  `useClickOutside`, `useDebouncedCallback`, `useAuthToken`,
  `useTranslation`, `useStoreState`.
- Theming wie in `@auditcore/ui` über die CSS-Variablen `--fa-*`.

## Herkunft und Charakterisierung

Neu in auditcore entwickelt. Bis 0.2.0 enthielt das Paket nur Hüllen um die
Web Components aus `@auditcore/ui` (PR #80, #84, #83, #111, #88, #146,
Geo-Karte); ab 1.0.0 sind Basis, Tabelle, Synopse, VVT, DSFA, Geo-Karte,
Risiko-Merkmale, Screening, Stichprobe und Benford eigenständige
React-Implementierungen desselben Vertrags. Parität zur Vue-Fassung: dieselben
Fälle (`ui-core/test/parity`) gegen beide Fassungen, dazu ein Vergleich des
normalisierten DOM und des Formularzustands Vue ↔ React, auch nach
Interaktionen ([Parität Vue ↔ React](../../docs/ui/react-paritaet.md)).
Die Hooks (0.2.0) folgen [`docs/reports/app-helfer-ts.md`](../../docs/reports/app-helfer-ts.md)
(Abschnitt 7); ihre Logik steckt in `@auditcore/common`.

## Abhängigkeiten

- `@auditcore/ui-core` 0.1.0, `@auditcore/kanban-core` 0.2.0 und `@auditcore/common` 0.1.0 (Laufzeit)
- `react` und `react-dom` `^18.3.0 || ^19.0.0` (Peer-Abhängigkeiten)

Node ≥ 20.19 für Bau und Tests.

## Sicherheit und Datenschutz

Die Komponenten erzeugen kein HTML aus Strings (kein
`dangerouslySetInnerHTML`) und greifen nicht auf Netzwerk oder
Browser-Speicher zu; Daten kommen über Props oder die Ports der Anwendung.
Exporte escapen alle Inhalte (Kern `@auditcore/ui-core`), CSV mit
Formelschutz. Vier-Augen-Hinweise sind reine Anzeige, maßgeblich ist die
Prüfung des Servers. `useAuthToken` liest und schreibt nur über den
`TokenStore`, den die Anwendung übergibt.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Neu entwickelt, kein übernommener Fremdcode.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
