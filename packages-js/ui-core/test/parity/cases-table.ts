/** Paritätsfälle der Tabelle (Vue `FaTable` ↔ React `FlowauditTable`); synthetische Belege. */
import type { SortState, TableColumn, TableRow } from '@auditcore/common'
import type { ParityCase } from './cases'

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
