import type { ChangeEvent, FocusEvent } from 'react'
import type { BadgeTone, FieldView, RowUpdate, RowView, SynopsisLayout, SynopsisTranslate } from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { classes, useElementId } from '../store'
import { SynopsisText } from './SynopsisText'

export interface SynopsisRowProps {
  row: RowView
  layout: SynopsisLayout
  oldLabel: string
  newLabel: string
  reasonLabel: string
  editable: boolean
  active: boolean
  t: SynopsisTranslate
  onUpdate: (patch: Omit<RowUpdate, 'row_id'>) => void
  onActivate: () => void
}

const TONES: Record<string, BadgeTone> = { changed: 'accent', added: 'success', removed: 'danger', moved: 'warning' }

interface ScreenReaderTexts {
  srRemoved: string
  srAdded: string
  srEnd: string
}

function Field({ field, segments, sr }: { field: FieldView; segments: FieldView['old']; sr: ScreenReaderTexts }) {
  return (
    <div className="fa-synopsis-row__field">
      <strong>{field.label}</strong>
      <SynopsisText segments={segments} {...sr} />
    </div>
  )
}

function Sides({ row, oldLabel, newLabel, t, sr }: SynopsisRowProps & { sr: ScreenReaderTexts }) {
  return (
    <div className="fa-synopsis-row__sides">
      {(['old', 'new'] as const).map((side) => {
        const label = side === 'old' ? oldLabel : newLabel
        return (
          <section key={side} className="fa-synopsis-row__side" aria-label={label}>
            <h4 className="fa-synopsis-row__side-title">{label}</h4>
            <SynopsisText segments={row[side]} empty={side === 'old' ? t('emptyOld') : t('emptyNew')} {...sr} />
            {row.fields.filter((entry) => entry[side].length > 0).map((field) => <Field key={field.field} field={field} segments={field[side]} sr={sr} />)}
          </section>
        )
      })}
    </div>
  )
}

function Reason({ row, editable, reasonLabel, t, onUpdate }: SynopsisRowProps) {
  // Wie `@change` der Vue-Fassung: erst beim Verlassen und nur bei geändertem Text.
  const onReason = (event: ChangeEvent<HTMLTextAreaElement> | FocusEvent<HTMLTextAreaElement>): void => {
    if (event.target.value !== row.reason) onUpdate({ reason: event.target.value })
  }
  return (
    <footer className="fa-synopsis-row__reason">
      {editable ? (
        <label className="fa-synopsis-row__reason-edit">
          <span>{reasonLabel}</span>
          <textarea key={row.reason} defaultValue={row.reason} rows={2} maxLength={4000} placeholder={t('reasonPlaceholder')} onBlur={onReason} />
        </label>
      ) : (
        <p><strong>{reasonLabel}:</strong> {row.reason}</p>
      )}
      {row.reasonSource === 'flowagent' ? (
        <p className={classes('fa-synopsis-row__hint', !!row.reasonVerified && 'fa-synopsis-row__hint--ok')}>
          {t('flowagent')} · {row.reasonVerified ? t('flowagentVerified') : t('flowagentCheck')}
        </p>
      ) : null}
      {row.reasonWarning ? <p className="fa-synopsis-row__hint">{row.reasonWarning}</p> : null}
    </footer>
  )
}

/** Eine Zeile der Synopse (Seite an Seite oder Inline), Auswahl und Grund optional bearbeitbar. */
export function SynopsisRow(props: SynopsisRowProps) {
  const { row, t, editable, active } = props
  const id = useElementId('fa-synopsis-row')
  const sr = { srRemoved: t('srRemoved'), srAdded: t('srAdded'), srEnd: t('srEnd') }
  const className = classes('fa-synopsis-row', `fa-synopsis-row--${row.status}`, active && 'fa-synopsis-row--active', !row.selected && 'fa-synopsis-row--muted')
  return (
    <article className={className} data-row-id={row.id} aria-labelledby={`${id}-title`} aria-current={active ? 'true' : undefined} tabIndex={-1} onFocus={props.onActivate}>
      <header className="fa-synopsis-row__head">
        <Badge tone={TONES[row.status] ?? 'neutral'}>{row.statusLabel}</Badge>
        <h3 id={`${id}-title`} className="fa-synopsis-row__title">
          {row.location || '—'}<span className="fa-sr-only">, {row.statusLabel}</span>
        </h3>
        {editable ? (
          <label className="fa-synopsis-row__include">
            <input type="checkbox" checked={row.selected} onChange={(event) => props.onUpdate({ selected: event.target.checked })} /> {t('include')}
          </label>
        ) : null}
      </header>
      {props.layout === 'side-by-side' ? (
        <Sides {...props} sr={sr} />
      ) : (
        <div className="fa-synopsis-row__inline">
          <SynopsisText segments={row.inline} {...sr} />
          {row.fields.map((field) => <Field key={field.field} field={field} segments={field.inline} sr={sr} />)}
        </div>
      )}
      {editable || row.reason ? <Reason {...props} /> : null}
    </article>
  )
}
