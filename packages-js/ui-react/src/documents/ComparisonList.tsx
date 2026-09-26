import { useRef, type ChangeEvent } from 'react'
import type { ComparisonsTranslate, SummaryView } from '@flowaudit/ui-core'
import { Badge } from '../base/Badge'
import { Button } from '../base/Button'
import { TextField } from '../base/TextField'
import { useElementId } from '../store'

export interface ComparisonListProps {
  rows?: readonly SummaryView[]
  query?: string
  countText?: string
  emptyText?: string | null
  busy?: boolean
  /** Löschen und Import anbieten. */
  editable?: boolean
  canImport?: boolean
  t: ComparisonsTranslate
  onQueryChange: (query: string) => void
  onComparisonOpen: (id: string) => void
  onComparisonRemove: (id: string) => void
  onResultImport: (text: string) => void
}

function Row({ row, props }: { row: SummaryView; props: ComparisonListProps }) {
  const { t, busy = false, editable = true } = props
  return (
    <li className="fa-comparisons-list__item" data-id={row.id}>
      <div className="fa-comparisons-list__main">
        <p className="fa-comparisons-list__title">{row.title}</p>
        <p className="fa-comparisons-list__meta">
          <Badge tone={row.kind === 'article_law' ? 'accent' : 'neutral'}>{row.kindLabel}</Badge>
          <time dateTime={row.createdIso}>{row.created}</time>
        </p>
        <p className="fa-comparisons-list__files">{row.files}</p>
        <p className="fa-comparisons-list__counts">{row.counts}</p>
      </div>
      <div className="fa-comparisons-list__actions">
        <Button size="sm" variant="primary" ariaLabel={t('openLabel', { title: row.title })} onClick={() => props.onComparisonOpen(row.id)}>{t('open')}</Button>
        {editable ? <Button size="sm" variant="ghost" icon="trash" iconOnly label={t('removeLabel', { title: row.title })} disabled={busy} onClick={() => props.onComparisonRemove(row.id)} /> : null}
      </div>
    </li>
  )
}

/** Gespeicherte Vergleiche mit Suche, Öffnen, Löschen und JSON-Import (wie `ComparisonList.vue`). */
export function ComparisonList(props: ComparisonListProps) {
  const { rows = [], t, emptyText = null, editable = true } = props
  const headingId = useElementId('fa-comparisons-list')
  const picker = useRef<HTMLInputElement | null>(null)
  const onImport = async (event: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const input = event.target
    const chosen = input.files?.[0]
    input.value = ''
    if (chosen) props.onResultImport(await chosen.text())
  }
  return (
    <section className="fa-comparisons-list" aria-labelledby={headingId}>
      <div className="fa-comparisons-list__head">
        <h3 id={headingId} className="fa-comparisons__subheading">{t('listHeading')}</h3>
        {editable && props.canImport ? (
          <>
            <Button size="sm" icon="paperclip" disabled={props.busy} onClick={() => picker.current?.click()}>{t('importLabel')}</Button>
            <input ref={picker} className="fa-sr-only" type="file" accept=".json,application/json" tabIndex={-1} aria-hidden="true" data-testid="comparisons-import" onChange={(event) => void onImport(event)} />
          </>
        ) : null}
      </div>
      <TextField value={props.query ?? ''} type="search" label={t('searchLabel')} onChange={props.onQueryChange} />
      <p className="fa-comparisons-list__count">{props.countText}</p>
      {emptyText ? <p className="fa-comparisons__state">{emptyText}</p> : (
        <ul className="fa-comparisons-list__items">{rows.map((row) => <Row key={row.id} row={row} props={props} />)}</ul>
      )}
    </section>
  )
}
