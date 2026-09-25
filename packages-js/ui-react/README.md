# @flowaudit/ui-react

## Zweck

React-18-Hüllen für die Web Components aus `@flowaudit/ui` sowie React-Hooks auf Basis von `@flowaudit/common` (Toasts, Media-Query, Klick außerhalb, Sortierung, Entprellen, Token).

Für React-Anwendungen, die die gemeinsamen FlowAudit-Komponenten nutzen
wollen, ohne selbst Vue zu schreiben. React 18 setzt an Custom Elements nur
Attribute; die Hüllen übernehmen die Übergabe von Objekten, Listen und Zahlen
als JS-Eigenschaften und das Abonnieren der `CustomEvent`s. Die Hooks
ersetzen die bisher in mehreren React-Apps kopierten Varianten.

## Installation

Im auditcore-Repository ist das Paket Teil des npm-Workspace:

```sh
npm ci                                 # im Repository-Stamm
npm run build -w @flowaudit/ui-react   # dist/: ESM und Typen
```

Im Anwendungsrepository mit allen Peer-Abhängigkeiten:

```sh
npm install @flowaudit/ui-react @flowaudit/ui @flowaudit/common @flowaudit/kanban-core react react-dom vue
```

Das Paket ist noch nicht in einer npm-Registry veröffentlicht; bis dahin
Bezug über den Workspace oder mit `npm pack -w @flowaudit/ui-react` erzeugte
Tarballs (zusammen mit `@flowaudit/ui`, `@flowaudit/common` und
`@flowaudit/kanban-core`).

## Schnellstart

```tsx
import { FlowauditTable, defineFlowauditElements } from '@flowaudit/ui-react'
import type { TableColumn } from '@flowaudit/ui'
import '@flowaudit/ui/style.css'

defineFlowauditElements({ locale: 'de' })

const columns: TableColumn[] = [
  { key: 'beleg', label: 'Beleg', sortable: true },
  { key: 'betrag', label: 'Betrag', align: 'end' },
]
const rows = [{ beleg: 'R-2026-001', betrag: 1250.5 }]

export function Belege({ open }: { open: (row: unknown) => void }) {
  return <FlowauditTable columns={columns} rows={rows} caption="Belege" clickable onRowClick={(row) => open(row)} />
}
```

## Einbindung

- **React:** `defineFlowauditElements()` einmal beim Start aufrufen (wird aus
  `@flowaudit/ui/elements` weitergereicht), `@flowaudit/ui/style.css` laden,
  dann die Hüllen wie normale React-Komponenten verwenden. Handler erhalten
  das erste emit-Argument der Vue-Komponente und das `CustomEvent`.
- **Web Component:** jede Hülle rendert das Element `<flowaudit-…>` aus
  `@flowaudit/ui` (`flowaudit-table`, `flowaudit-kanban-board`,
  `flowaudit-kanban-boards`, `flowaudit-sampling`, `flowaudit-benford`,
  `flowaudit-screening-review`, `flowaudit-risk-flags`); `ref` zeigt auf
  dieses DOM-Element.
- **Vue** läuft innerhalb der Web Components und muss daher installiert
  sein, auch wenn die Anwendung selbst nur React nutzt.

Eigene Hüllen für weitere Elemente:

```ts
import { createElementComponent } from '@flowaudit/ui-react'

export const FlowauditTableLite = createElementComponent<{ rows: readonly object[] }, { onRowClick: string }>(
  'flowaudit-table',
  { properties: ['rows'], events: { onRowClick: 'row-click' } },
)
```

Hooks auf Basis von `@flowaudit/common`:

```tsx
import { createTokenStore } from '@flowaudit/common'
import { useAuthToken, useMediaQuery, useSort, useToast } from '@flowaudit/ui-react'

const tokens = createTokenStore({ storage: 'session' })

export function Belegliste({ rows }: { rows: readonly { beleg: string; betrag: number }[] }) {
  const { sorted, toggle, ariaSortFor } = useSort(rows)
  const { headers } = useAuthToken(tokens)
  const narrow = useMediaQuery('(max-width: 768px)')
  const toast = useToast()
  return (
    <table data-narrow={narrow} onClick={() => toast.info(`${Object.keys(headers).length} Kopfzeile(n)`)}>
      <thead>
        <tr><th aria-sort={ariaSortFor('betrag')} onClick={() => toggle('betrag')}>Betrag</th></tr>
      </thead>
      <tbody>{sorted.map((row) => <tr key={row.beleg}><td>{row.betrag}</td></tr>)}</tbody>
    </table>
  )
}
```

`useToast()` nutzt ohne `ToastProvider` die anwendungsweite Warteschlange
(`sharedToastQueue()`); `useDebouncedCallback(fn, ms)` verwirft einen
ausstehenden Aufruf beim Unmount; `useClickOutside(ref, handler)` meldet
auch Escape. Außerdem reicht das Paket die framework-freien Teile weiter,
die bisher nur in `@flowaudit/ui` lagen (`formatDate`, `requestJson`,
`sortRows`, `parseNumber` … unter denselben Namen).

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (73):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/ui-react` | `BaseElementProps` | Schnittstelle | – | `createElementComponent` |
| `@flowaudit/ui-react` | `CellValue` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `DecimalSeparator` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `Delimiter` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `DownloadFile` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `ElementComponentOptions` | Schnittstelle | – | `createElementComponent` |
| `@flowaudit/ui-react` | `EventHandlers` | Typ | Ereignis-Handler einer Hülle erhalten das erste Argument des Vue-emit (CustomEvent.detail[0]). | `createElementComponent` |
| `@flowaudit/ui-react` | `FetchLike` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `FlowauditBenford` | Konstante | `<flowaudit-benford>` als React-Komponente: Verteilung, MAD, Chi², z je Ziffer. | `elements` |
| `@flowaudit/ui-react` | `FlowauditBenfordProps` | Schnittstelle | – | `elements` |
| `@flowaudit/ui-react` | `FlowauditDataProtectionError` | Typ | – | `dataprotection` |
| `@flowaudit/ui-react` | `FlowauditDsfa` | Konstante | `<flowaudit-dsfa>` als React-Komponente: Schwellwertanalyse, Risiko, Entscheidung, Freigabe (Art. 35 DSGVO). | `dataprotection` |
| `@flowaudit/ui-react` | `FlowauditDsfaProps` | Schnittstelle | – | `dataprotection` |
| `@flowaudit/ui-react` | `FlowauditKanbanBoard` | Konstante | `<flowaudit-kanban-board>` als React-Komponente. | `kanban` |
| `@flowaudit/ui-react` | `FlowauditKanbanBoardProps` | Schnittstelle | – | `kanban` |
| `@flowaudit/ui-react` | `FlowauditKanbanBoards` | Konstante | `<flowaudit-kanban-boards>` (Boardliste) als React-Komponente. | `kanban` |
| `@flowaudit/ui-react` | `FlowauditKanbanBoardsProps` | Schnittstelle | – | `kanban` |
| `@flowaudit/ui-react` | `FlowauditRiskFlags` | Konstante | `<flowaudit-risk-flags>` als React-Komponente; `onRecordSelect` erhält den Index oder `null`. | `elements` |
| `@flowaudit/ui-react` | `FlowauditRiskFlagsProps` | Schnittstelle | – | `elements` |
| `@flowaudit/ui-react` | `FlowauditSampling` | Konstante | `<flowaudit-sampling>` als React-Komponente: Stichprobenumfang, Auswahl mit Seed, Export. | `elements` |
| `@flowaudit/ui-react` | `FlowauditSamplingProps` | Schnittstelle | – | `elements` |
| `@flowaudit/ui-react` | `FlowauditScreeningError` | Typ | Nutzdaten des Ereignisses `error` der Screening-Trefferprüfung. | `elements` |
| `@flowaudit/ui-react` | `FlowauditScreeningReview` | Konstante | `<flowaudit-screening-review>` als React-Komponente: Sanktionslisten-/PEP-Treffer prüfen und entscheiden. | `elements` |
| `@flowaudit/ui-react` | `FlowauditScreeningReviewProps` | Schnittstelle | – | `elements` |
| `@flowaudit/ui-react` | `FlowauditSynopsis` | Konstante | `<flowaudit-synopsis>` als React-Komponente (Synopse / Versionsvergleich). | `synopsis` |
| `@flowaudit/ui-react` | `FlowauditSynopsisProps` | Schnittstelle | – | `synopsis` |
| `@flowaudit/ui-react` | `FlowauditTable` | Konstante | `<flowaudit-table>` als React-Komponente. | `elements` |
| `@flowaudit/ui-react` | `FlowauditTableProps` | Schnittstelle | – | `elements` |
| `@flowaudit/ui-react` | `FlowauditVvt` | Konstante | `<flowaudit-vvt>` als React-Komponente: Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO). | `dataprotection` |
| `@flowaudit/ui-react` | `FlowauditVvtProps` | Schnittstelle | – | `dataprotection` |
| `@flowaudit/ui-react` | `NextSortOptions` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `NumberColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `ParsedTable` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `RestError` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `RestOptions` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `SortDirection` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `SortState` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `TableColumn` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `TableRow` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `ToastProvider` | Funktion | Stellt eine eigene Warteschlange für den Teilbaum bereit (z. B. je Mandant oder im Test). | `hooks/toast` |
| `@flowaudit/ui-react` | `UseAuthToken` | Schnittstelle | – | `hooks/state` |
| `@flowaudit/ui-react` | `UseSort` | Schnittstelle | – | `hooks/state` |
| `@flowaudit/ui-react` | `UseSortOptions` | Schnittstelle | – | `hooks/state` |
| `@flowaudit/ui-react` | `UseToast` | Schnittstelle | – | `hooks/toast` |
| `@flowaudit/ui-react` | `ariaSort` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `columnCells` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `compareValues` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `createElementComponent` | Funktion | Erzeugt eine React-18-Komponente für ein Custom Element. | `createElementComponent` |
| `@flowaudit/ui-react` | `defineFlowauditElements` | Re-Export | – | `@flowaudit/ui/elements` |
| `@flowaudit/ui-react` | `detectDecimal` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `detectDelimiter` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `eventPayload` | Funktion | Liest das erste emit-Argument aus Vue-CustomEvents (detail ist ein Argument-Array). | `createElementComponent` |
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
| `@flowaudit/ui-react` | `sharedToastQueue` | Funktion | Anwendungsweite Warteschlange (einmal je Seite), wenn kein `ToastProvider` gesetzt ist. | `hooks/toast` |
| `@flowaudit/ui-react` | `sortRows` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `splitLine` | Re-Export | – | `@flowaudit/common` |
| `@flowaudit/ui-react` | `useAuthToken` | Funktion | Zugangstoken aus einem `TokenStore` (`@flowaudit/common`), neu gerendert bei jeder Änderung. | `hooks/state` |
| `@flowaudit/ui-react` | `useClickOutside` | Funktion | Ruft `handler` bei Klick außerhalb der Elemente und bei Escape; abgemeldet beim Unmount. | `hooks/dom` |
| `@flowaudit/ui-react` | `useDebouncedCallback` | Funktion | Entprellte, stabile Funktion; ruft immer die neueste `fn` auf und verwirft einen ausstehenden Aufruf beim Unmount. | `hooks/state` |
| `@flowaudit/ui-react` | `useMediaQuery` | Funktion | Stand einer Media-Query, z. B. `useMediaQuery('(max-width: 768px)')`; serverseitig `false`. | `hooks/dom` |
| `@flowaudit/ui-react` | `useSort` | Funktion | Sortierzustand und sortierte Zeilen (Kern `table/sort` aus `@flowaudit/common`). | `hooks/state` |
| `@flowaudit/ui-react` | `useToast` | Funktion | Toasts über der framework-freien Warteschlange aus `@flowaudit/common` (Provider, sonst gemeinsame Warteschlange). | `hooks/toast` |
<!-- api-overview:end -->

## Konfiguration

- `createElementComponent<Props, Events>(tag, { properties, events })`:
  `properties` sind die Props, die als JS-Eigenschaften gesetzt werden
  (Objekte, Listen, Zahlen), `events` ordnet React-Handler den DOM-Ereignissen
  zu (`{ onRowClick: 'row-click' }`). Alle Hüllen akzeptieren zusätzlich
  `className`, `style`, `id` und `children`.
- `FlowauditTable`: `columns`, `rows`, `rowKey`, `caption`, `emptyText`,
  `clickable`, `sort`, `locale`; `onRowClick`, `onSortChange`.
- `FlowauditKanbanBoard` (`onBoardChange`, `onError`, `onFullscreen`,
  `onNavigate`, `onAttachment`, `onCardOpen`) und `FlowauditKanbanBoards`
  (`onBoardSelect`, `onCreated`); Props wie in
  [`docs/kanban/oberflaeche.md`](../../docs/kanban/oberflaeche.md).
- `FlowauditSampling` (`onSizeCalculated`, `onSelectionDrawn`, `onError`),
  `FlowauditBenford` (`port`, `values`, `locale`; `onAnalysisCompleted`,
  `onError`), `FlowauditScreeningReview` (`onRunCreated`, `onDecided`,
  `onError`), `FlowauditRiskFlags` (z. B. `evaluation`, `profile`;
  `onRecordSelect`, `onFilterChange`; Antworten von `auditcore_risk.web`,
  siehe [`docs/ui/risk-rest.md`](../../docs/ui/risk-rest.md)).
- `FlowauditVvt` (`port`, `actor`, `editable`, `locale`; `onDraftSaved`,
  `onReleased`, `onExported`, `onError`) und `FlowauditDsfa` (`port`,
  `activityId`, `actor`, `editable`, `locale`; `onAssessmentChange`,
  `onError`), siehe [`docs/ui/dataprotection-rest.md`](../../docs/ui/dataprotection-rest.md).
- Sprache und Theming wie in `@flowaudit/ui` (`locale`-Prop,
  `defineFlowauditElements({ locale })`, CSS-Variablen `--fa-*`).

## Herkunft und Charakterisierung

Neu in auditcore entwickelt (PR #80 Gerüst mit `FlowauditTable`, #84
Kanban, #83 Stichprobe und Benford, #111 Screening, #88 Risiko-Merkmale). Keine Übernahme aus Anwendungen; das Verhalten der Elemente
selbst dokumentiert `@flowaudit/ui`. Die Hooks (0.2.0) sind Neuentwicklungen
nach dem Zuschnitt in
[`docs/reports/app-helfer-ts.md`](../../docs/reports/app-helfer-ts.md)
(Abschnitt 7); ihre Logik steckt in `@flowaudit/common` und wird dort gegen
die gemeinsamen Vertragsfälle geprüft.

## Abhängigkeiten

Nur Peer-Abhängigkeiten, die die Anwendung bereitstellt:

- `@flowaudit/ui` ^0.2.0, `@flowaudit/common` ^0.1.0 und
  `@flowaudit/kanban-core` ^0.1.0
- `react` ^18.3.0 und `react-dom` ^18.3.0
- `vue` ^3.5.0 (Laufzeit der Web Components)

Node ≥ 20.19 für Bau und Tests.

## Sicherheit und Datenschutz

Die Hüllen erzeugen kein HTML aus Strings und greifen nicht auf Netzwerk
oder Browser-Speicher zu; sie setzen nur Eigenschaften und Ereignis-Listener
am Element. `useAuthToken` liest und schreibt nur über den `TokenStore`, den
die Anwendung übergibt (Speicherwahl und Hinweise in `@flowaudit/common`). Escaping, Netzwerkzugriffe (über Ports) und Datenhaltung richten
sich nach `@flowaudit/ui` bzw. der Anwendung.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Neu entwickelt, kein übernommener Fremdcode.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
