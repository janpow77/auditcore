import type { Card, Column } from '@flowaudit/kanban-core'
import type { Locale, Translate } from '@flowaudit/ui-core'
import { useState } from 'react'
import { Button } from '../base/Button'
import { TextField } from '../base/TextField'
import { useKanbanDialogText } from './text'
import type { KanbanDialogMessageKey } from '@flowaudit/ui-core'

type Update = (fields: Record<string, unknown>) => void

/** Lokale Eingaben (Kennung, Titel, Beschreibung); eine neue Kartenfassung belegt sie neu (wie der Vue-watch). */
export function useCardDraft(card: Card) {
  const [source, setSource] = useState(card)
  const [badge, setBadge] = useState(card.badge ?? '')
  const [title, setTitle] = useState(card.title)
  const [description, setDescription] = useState(card.description)
  if (source !== card) {
    setSource(card)
    setBadge(card.badge ?? '')
    setTitle(card.title)
    setDescription(card.description)
  }
  return { badge, setBadge, title, setTitle, description, setDescription }
}

export type CardDraft = ReturnType<typeof useCardDraft>

interface TextsProps {
  card: Card
  draft: CardDraft
  readOnly: boolean
  label: Translate<KanbanDialogMessageKey>
  update: Update
}

/** Kennung und Titel; übernommen beim Verlassen bzw. mit Enter (wie `@change`/`@focusout` in Vue). */
export function CardTexts({ card, draft, readOnly, label: t, update }: TextsProps) {
  const commitBadge = (): void => {
    const badge = draft.badge.trim().toUpperCase()
    if (badge !== (card.badge ?? '')) update({ badge })
  }
  const commitTitle = (): void => {
    const value = draft.title.trim()
    if (value && value !== card.title) update({ title: value })
  }
  return (
    <div className="fa-kanban-detail__row">
      <TextField value={draft.badge} label={t('badge')} placeholder={t('badgePlaceholder')} disabled={readOnly} style={{ width: '7rem' }} onChange={draft.setBadge} onBlur={commitBadge} onKeyDown={(event) => event.key === 'Enter' && commitBadge()} />
      <TextField value={draft.title} label={t('title')} disabled={readOnly} style={{ flex: 1 }} onChange={draft.setTitle} onBlur={commitTitle} onKeyDown={(event) => event.key === 'Enter' && commitTitle()} />
    </div>
  )
}

interface FieldsProps {
  card: Card
  columns: readonly Column[]
  readOnly: boolean
  locale?: Locale
  update: Update
}

/** Spalte und Fälligkeit. */
export function CardFields({ card, columns, readOnly, locale, update }: FieldsProps) {
  const { t } = useKanbanDialogText(locale)
  return (
    <div className="fa-kanban-detail__row">
      <label className="fa-field">
        <span className="fa-field__label">{t('column')}</span>
        <select className="fa-kanban-select" value={card.column_id} disabled={readOnly} onChange={(event) => update({ column_id: event.target.value })}>
          {columns.map((column) => <option key={column.id} value={column.id}>{column.label}</option>)}
        </select>
      </label>
      <label className="fa-field">
        <span className="fa-field__label">{t('due')}</span>
        <input className="fa-field__input" type="date" value={card.due?.slice(0, 10) ?? ''} disabled={readOnly} onChange={(event) => update({ due: event.target.value })} />
      </label>
      {card.due && !readOnly ? <Button size="sm" variant="ghost" icon="close" iconOnly label={t('clearDue')} onClick={() => update({ due: '' })} /> : null}
    </div>
  )
}
