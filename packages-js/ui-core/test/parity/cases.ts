/**
 * Gemeinsame Paritätsfälle: Vue-Fassung (`@flowaudit/ui`) und React-Fassung
 * (`@flowaudit/ui-react`) werden mit denselben Eingaben gerendert und gegen
 * dieselben Erwartungen (Texte, Rollen, Namen) sowie gegeneinander (DOM)
 * geprüft. Daten: Fixtures der echten Python-Backends, keine Personendaten.
 */
import type { SortState, TableColumn, TableRow } from '@flowaudit/common'
import type { Comparison, SynopsisPort } from '../../src'
import { article, checklist, standard } from '../synopsis/fixtures'

export interface Expectation {
  /** Texte, die im gerenderten Teilbaum vorkommen müssen. */
  texts?: readonly string[]
  /** Zugängliche Rollen mit Namen (`getByRole(role, { name })`). */
  roles?: ReadonlyArray<readonly [string, string | RegExp]>
  /** Anzahl Treffer je CSS-Selektor. */
  counts?: Readonly<Record<string, number>>
}

export interface ParityCase<P> {
  name: string
  props: () => P
  expect: Expectation
}

export interface SynopsisCaseProps {
  comparison?: Comparison | null
  comparisonId?: string
  port?: SynopsisPort | null
  editable?: boolean
  layout?: 'side-by-side' | 'inline'
  oldLabel?: string
  newLabel?: string
  locale?: 'de' | 'en'
}

const port = (comparison: Comparison): SynopsisPort => ({
  load: async () => comparison,
  updateRows: async () => comparison,
  exportUrl: (id, format) => `/api/synopsis/comparisons/${id}/export?format=${format}`,
})

export const synopsisCases: ReadonlyArray<ParityCase<SynopsisCaseProps>> = [
  {
    name: 'Standardvergleich nebeneinander',
    props: () => ({ comparison: standard }),
    expect: {
      texts: ['3 geändert · 2 entfallen · 3 neu', 'keine Prüfungsentscheidung', '8 Änderungen in dieser Ansicht'],
      roles: [['heading', standard.title], ['region', 'Ansicht, Filter und Export'], ['button', 'Nächste Änderung']],
      counts: { article: 8, 'h4.fa-synopsis-row__side-title': 16 },
    },
  },
  {
    name: 'Inline-Ansicht mit eigenen Bezeichnungen',
    props: () => ({ comparison: standard, layout: 'inline', oldLabel: 'Richtlinie 2025', newLabel: 'Richtlinie 2026' }),
    expect: { counts: { '.fa-synopsis-row__inline': 8, '.fa-synopsis-row__sides': 0 } },
  },
  {
    name: 'Checkliste bearbeitbar mit Server-Exporten',
    props: () => ({ comparison: checklist, editable: true, port: port(checklist) }),
    expect: {
      texts: ['5 von 6 Zeilen für die Ausgabe ausgewählt'],
      roles: [['link', 'Word (DOCX)'], ['checkbox', /Nur ausgewählte/]],
      counts: { '.fa-synopsis-row__include input': 5, textarea: 5 },
    },
  },
  {
    name: 'Gesetzessynopse mit offenen Befehlen',
    props: () => ({ comparison: article }),
    expect: { roles: [['region', 'Offene Änderungsbefehle']], counts: { details: 1 } },
  },
  { name: 'ohne Vergleich', props: () => ({}), expect: { texts: ['Kein Vergleich ausgewählt.'] } },
  {
    name: 'englische Oberfläche',
    props: () => ({ comparison: standard, locale: 'en' }),
    expect: { roles: [['button', 'Next change']] },
  },
]

export interface TableCaseProps {
  columns: readonly TableColumn[]
  rows: readonly TableRow[]
  caption?: string
  emptyText?: string
  clickable?: boolean
  sort?: SortState | null
  locale?: 'de' | 'en'
}

const columns: TableColumn[] = [
  { key: 'beleg', label: 'Beleg', sortable: true },
  { key: 'betrag', label: 'Betrag', align: 'end', sortable: true, format: (value) => `${Number(value).toFixed(2).replace('.', ',')} €` },
  { key: 'art', label: 'Art', align: 'center' },
]
const rows: TableRow[] = [
  { id: 'r1', beleg: 'R-2026-002', betrag: 980, art: 'Rechnung' },
  { id: 'r2', beleg: 'R-2026-001', betrag: 1250.5, art: 'Gutschrift' },
]

export const tableCases: ReadonlyArray<ParityCase<TableCaseProps>> = [
  {
    name: 'Belege sortierbar und anklickbar',
    props: () => ({ columns, rows, caption: 'Belege', clickable: true }),
    expect: { roles: [['button', 'Nach Beleg sortieren'], ['table', 'Belege']], texts: ['1250,50 €'], counts: { 'tbody tr[tabindex="0"]': 2 } },
  },
  {
    name: 'absteigend nach Betrag',
    props: () => ({ columns, rows, sort: { key: 'betrag', direction: 'desc' } }),
    expect: { counts: { 'th[aria-sort="descending"]': 1 } },
  },
  { name: 'leer', props: () => ({ columns, rows: [], emptyText: 'Keine Belege' }), expect: { texts: ['Keine Belege'] } },
  { name: 'englisch leer', props: () => ({ columns, rows: [], locale: 'en' }), expect: { texts: ['No entries'] } },
]
