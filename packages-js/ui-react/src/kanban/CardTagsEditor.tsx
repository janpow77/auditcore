import type { Locale } from '@flowaudit/ui-core'
import { useState, type KeyboardEvent } from 'react'
import { Icon } from '../base/Icon'
import { useKanbanDialogText } from './text'

export interface CardTagsEditorProps {
  tags: readonly string[]
  readOnly?: boolean
  locale?: Locale
  onChange: (tags: string[]) => void
}

/** Tags einer Karte wie `CardTagsEditor.vue` (Enter fügt hinzu, Schaltfläche entfernt). */
export function CardTagsEditor({ tags, readOnly = false, locale, onChange }: CardTagsEditorProps) {
  const { t } = useKanbanDialogText(locale)
  const [draft, setDraft] = useState('')
  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>): void => {
    if (event.key !== 'Enter') return
    event.preventDefault()
    const tag = draft.trim()
    setDraft('')
    if (tag && !tags.includes(tag)) onChange([...tags, tag])
  }
  return (
    <div className="fa-kanban-detail__section">
      <span className="fa-kanban-detail__label">{t('tags')}</span>
      <div className="fa-kanban-detail__row">
        {tags.map((tag) => (
          <span key={tag} className="fa-badge fa-badge--accent">
            {tag}
            {readOnly ? null : (
              <button type="button" className="fa-kanban-detail__chip-remove" aria-label={t('removeTag', { tag })} onClick={() => onChange(tags.filter((entry) => entry !== tag))}>
                <Icon name="close" size={11} />
              </button>
            )}
          </span>
        ))}
      </div>
      {readOnly ? null : <input className="fa-field__input" placeholder={t('tagPlaceholder')} aria-label={t('tagPlaceholder')} value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={onKeyDown} />}
    </div>
  )
}
