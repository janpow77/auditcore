import { COLUMN_COLORS, type Column } from '@flowaudit/kanban-core'
import type { Locale } from '@flowaudit/ui-core'
import type { ChangeEvent, CSSProperties } from 'react'
import { Button } from '../base/Button'
import { useKanbanDialogText } from './text'

export interface ColumnEditorRowProps {
  column: Column
  first?: boolean
  last?: boolean
  canRemove?: boolean
  locale?: Locale
  onUpdate: (patch: Partial<Column>) => void
  onRemove: () => void
  onMove: (step: -1 | 1) => void
}

function limitOf(event: ChangeEvent<HTMLInputElement>): number | null {
  const value = event.target.value
  return value === '' ? null : Math.max(0, Math.floor(Number(value)))
}

function ColorPicker({ column, locale, onUpdate }: ColumnEditorRowProps) {
  const { t } = useKanbanDialogText(locale)
  return (
    <div className="fa-kanban-settings__colors" role="group" aria-label={t('columnColor', { label: column.label })}>
      {COLUMN_COLORS.map((color) => (
        <button key={color} type="button" className="fa-kanban-detail__swatch" style={{ background: color }} aria-label={color} aria-pressed={column.color === color} onClick={() => onUpdate({ color })} />
      ))}
      <input type="color" value={column.color} aria-label={t('columnColor', { label: column.label })} onChange={(event) => onUpdate({ color: event.target.value })} />
    </div>
  )
}

/** Zeile des Spalteneditors wie `ColumnEditorRow.vue`. */
export function ColumnEditorRow(props: ColumnEditorRowProps) {
  const { t } = useKanbanDialogText(props.locale)
  const { column } = props
  const dot = { '--fa-kanban-column-color': column.color, width: '1rem', height: '1rem' } as CSSProperties
  return (
    <li className="fa-kanban-settings__row" data-column-editor={column.id}>
      <span className="fa-kanban-column__dot" style={dot} aria-hidden="true" />
      <label className="fa-field">
        <span className="fa-field__label">{t('columnLabel')}</span>
        <input className="fa-field__input" value={column.label} maxLength={80} onChange={(event) => props.onUpdate({ label: event.target.value })} />
      </label>
      <label className="fa-field">
        <span className="fa-field__label">{t('wipLimit')}</span>
        <input className="fa-field__input" type="number" min="1" value={column.wip_limit ?? ''} onChange={(event) => props.onUpdate({ wip_limit: limitOf(event) })} />
      </label>
      <label className="fa-kanban-settings__check">
        <input type="checkbox" checked={column.done} onChange={(event) => props.onUpdate({ done: event.target.checked })} />
        {t('doneColumn')}
      </label>
      <div className="fa-kanban-detail__row">
        <Button size="sm" variant="ghost" icon="chevron-up" iconOnly label={t('moveUp')} disabled={props.first} onClick={() => props.onMove(-1)} />
        <Button size="sm" variant="ghost" icon="chevron-down" iconOnly label={t('moveDown')} disabled={props.last} onClick={() => props.onMove(1)} />
        <Button size="sm" variant="ghost" icon="trash" iconOnly label={t('removeColumn', { label: column.label })} disabled={!(props.canRemove ?? true)} onClick={props.onRemove} />
      </div>
      <ColorPicker {...props} />
    </li>
  )
}
