import type { ChecklistItem } from '@flowaudit/kanban-core'
import type { Locale } from '@flowaudit/ui-core'
import { useState, type FocusEvent, type KeyboardEvent } from 'react'
import { Button } from '../base/Button'
import { classes } from '../store'
import { useKanbanDialogText } from './text'

export interface CardChecklistEditorProps {
  items: readonly ChecklistItem[]
  readOnly?: boolean
  locale?: Locale
  onChange: (items: ChecklistItem[]) => void
}

type Row = { item: ChecklistItem; index: number; props: CardChecklistEditorProps }

function ChecklistRow({ item, index, props }: Row) {
  const { t } = useKanbanDialogText(props.locale)
  const [text, setText] = useState(item.text)
  const [source, setSource] = useState(item.text)
  if (source !== item.text) {
    setSource(item.text)
    setText(item.text)
  }
  const replace = (patch: Partial<ChecklistItem>): void => props.onChange(props.items.map((entry, position) => (position === index ? { ...entry, ...patch } : entry)))
  // Wie `@change` in Vue: beim Verlassen bzw. mit Enter übernehmen, nur bei geändertem Text.
  const commit = (event: FocusEvent<HTMLInputElement> | KeyboardEvent<HTMLInputElement>): void => {
    const value = event.currentTarget.value.trim()
    if (value && value !== item.text) replace({ text: value })
  }
  return (
    <li className={classes('fa-kanban-detail__item', item.done && 'is-done')}>
      <input type="checkbox" checked={item.done} disabled={props.readOnly} aria-label={item.text} onChange={() => replace({ done: !item.done })} />
      <input type="text" value={text} readOnly={props.readOnly} aria-label={t('checklist')} onChange={(event) => setText(event.target.value)} onBlur={commit} onKeyDown={(event) => event.key === 'Enter' && commit(event)} />
      {props.readOnly ? null : <Button size="sm" variant="ghost" icon="close" iconOnly label={t('removeItem', { text: item.text })} onClick={() => props.onChange(props.items.filter((_, position) => position !== index))} />}
    </li>
  )
}

/** Checkliste einer Karte wie `CardChecklistEditor.vue`. */
export function CardChecklistEditor(props: CardChecklistEditorProps) {
  const { t } = useKanbanDialogText(props.locale)
  const [draft, setDraft] = useState('')
  const { items, readOnly = false } = props
  const done = items.filter((item) => item.done).length
  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>): void => {
    if (event.key !== 'Enter') return
    event.preventDefault()
    const text = draft.trim()
    setDraft('')
    if (text) props.onChange([...items, { text, done: false }])
  }
  return (
    <div className="fa-kanban-detail__section">
      <span className="fa-kanban-detail__label">
        {t('checklist')}
        {items.length ? ` · ${t('checklistSummary', { done, total: items.length })}` : null}
      </span>
      {items.length ? (
        <ul className="fa-kanban-detail__list">
          {items.map((item, index) => <ChecklistRow key={index} item={item} index={index} props={props} />)}
        </ul>
      ) : null}
      {readOnly ? null : <input className="fa-field__input" placeholder={t('checklistPlaceholder')} aria-label={t('checklistPlaceholder')} value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={onKeyDown} />}
    </div>
  )
}
