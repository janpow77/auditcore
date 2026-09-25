# @flowaudit/ui-react

## Zweck

React-18-Hüllen für die Web Components aus `@flowaudit/ui`: Objekte werden als Eigenschaften gesetzt und Ereignisse als `onXxx`-Handler verdrahtet.

Für React-Anwendungen, die die gemeinsamen FlowAudit-Komponenten nutzen
wollen, ohne selbst Vue zu schreiben. React 18 setzt an Custom Elements nur
Attribute; die Hüllen übernehmen die Übergabe von Objekten, Listen und Zahlen
als JS-Eigenschaften und das Abonnieren der `CustomEvent`s.

## Installation

Im auditcore-Repository ist das Paket Teil des npm-Workspace:

```sh
npm ci                                 # im Repository-Stamm
npm run build -w @flowaudit/ui-react   # dist/: ESM und Typen
```

Im Anwendungsrepository mit allen Peer-Abhängigkeiten:

```sh
npm install @flowaudit/ui-react @flowaudit/ui @flowaudit/kanban-core react react-dom vue
```

Das Paket ist noch nicht in einer npm-Registry veröffentlicht; bis dahin
Bezug über den Workspace oder mit `npm pack -w @flowaudit/ui-react` erzeugte
Tarballs (zusammen mit `@flowaudit/ui` und `@flowaudit/kanban-core`).

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

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (23):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@flowaudit/ui-react` | `BaseElementProps` | Schnittstelle | – | `createElementComponent` |
| `@flowaudit/ui-react` | `ElementComponentOptions` | Schnittstelle | – | `createElementComponent` |
| `@flowaudit/ui-react` | `EventHandlers` | Typ | Ereignis-Handler einer Hülle erhalten das erste Argument des Vue-emit (CustomEvent.detail[0]). | `createElementComponent` |
| `@flowaudit/ui-react` | `FlowauditBenford` | Konstante | `<flowaudit-benford>` als React-Komponente: Verteilung, MAD, Chi², z je Ziffer. | `elements` |
| `@flowaudit/ui-react` | `FlowauditBenfordProps` | Schnittstelle | – | `elements` |
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
| `@flowaudit/ui-react` | `createElementComponent` | Funktion | Erzeugt eine React-18-Komponente für ein Custom Element. | `createElementComponent` |
| `@flowaudit/ui-react` | `defineFlowauditElements` | Re-Export | – | `@flowaudit/ui/elements` |
| `@flowaudit/ui-react` | `eventPayload` | Funktion | Liest das erste emit-Argument aus Vue-CustomEvents (detail ist ein Argument-Array). | `createElementComponent` |
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
- Sprache und Theming wie in `@flowaudit/ui` (`locale`-Prop,
  `defineFlowauditElements({ locale })`, CSS-Variablen `--fa-*`).

## Herkunft und Charakterisierung

Neu in auditcore entwickelt (PR #80 Gerüst mit `FlowauditTable`, #84
Kanban, #83 Stichprobe und Benford, #111 Screening, #88 Risiko-Merkmale). Keine Übernahme aus Anwendungen; das Verhalten der Elemente
selbst dokumentiert `@flowaudit/ui`.

## Abhängigkeiten

Nur Peer-Abhängigkeiten, die die Anwendung bereitstellt:

- `@flowaudit/ui` ^0.1.0 und `@flowaudit/kanban-core` ^0.1.0
- `react` ^18.3.0 und `react-dom` ^18.3.0
- `vue` ^3.5.0 (Laufzeit der Web Components)

Node ≥ 20.19 für Bau und Tests.

## Sicherheit und Datenschutz

Die Hüllen erzeugen kein HTML aus Strings und greifen nicht auf Netzwerk
oder Browser-Speicher zu; sie setzen nur Eigenschaften und Ereignis-Listener
am Element. Escaping, Netzwerkzugriffe (über Ports) und Datenhaltung richten
sich nach `@flowaudit/ui` bzw. der Anwendung.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Neu entwickelt, kein übernommener Fremdcode.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
