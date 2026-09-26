import { useState } from 'react'
import {
  Button,
  FlowauditTable,
  LocaleProvider,
  formatNumber,
  type Locale,
  type SortState,
  type TableColumn,
  type TableRow,
} from '@flowaudit/ui-react'

const rows: TableRow[] = [
  { id: 'r1', beleg: 'R-2026-001', datum: '2026-03-02', betrag: 1250.5 },
  { id: 'r2', beleg: 'R-2026-002', datum: '2026-03-09', betrag: 980 },
  { id: 'r3', beleg: 'R-2026-003', datum: '2026-04-01', betrag: 12400 },
]

/** Hell/Dunkel: `data-fa-theme` am <html>; ohne Attribut gilt prefers-color-scheme. */
function toggleTheme(): void {
  const root = document.documentElement
  const dark = root.dataset.faTheme
    ? root.dataset.faTheme === 'dark'
    : window.matchMedia('(prefers-color-scheme: dark)').matches
  root.dataset.faTheme = dark ? 'light' : 'dark'
}

export function App() {
  const [locale, setLocale] = useState<Locale>('de')
  const [sort, setSort] = useState<SortState | null>(null)
  const [selected, setSelected] = useState<TableRow | null>(null)
  const columns: TableColumn[] = [
    { key: 'beleg', label: 'Beleg', sortable: true },
    { key: 'datum', label: 'Datum', sortable: true },
    { key: 'betrag', label: 'Betrag (EUR)', align: 'end', sortable: true, format: (value) => formatNumber(Number(value), locale) },
  ]
  return (
    <LocaleProvider locale={locale}>
      <main style={{ maxWidth: '48rem', margin: '2rem auto', padding: '0 1rem', fontFamily: 'var(--fa-font-sans)', color: 'var(--fa-color-text)' }}>
        <h1>Belege</h1>
        <p style={{ display: 'flex', gap: '0.5rem' }}>
          <Button onClick={toggleTheme}>Hell/Dunkel</Button>
          <Button onClick={() => setLocale(locale === 'de' ? 'en' : 'de')}>Sprache: {locale}</Button>
        </p>
        <FlowauditTable columns={columns} rows={rows} caption="Belege" clickable sort={sort} onSortChange={setSort} onRowClick={setSelected} />
        {selected ? <p role="status">Ausgewählt: {String(selected.beleg)}</p> : null}
      </main>
    </LocaleProvider>
  )
}
