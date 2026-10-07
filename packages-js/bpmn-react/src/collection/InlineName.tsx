/**
 * Name shown as text; a click turns it into a one-line field. Enter or
 * leaving the field saves, Escape discards. Blanks are trimmed; an empty
 * name is not saved, the old one stays.
 */

import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { useI18n } from '../i18n'

export interface InlineNameProps {
  text: string
  readonly?: boolean
  onSave: (text: string) => void
}

export function InlineName({ text, readonly, onSave }: InlineNameProps) {
  const { t } = useI18n()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const field = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (editing) field.current?.select()
  }, [editing])

  const start = () => {
    if (readonly) return
    setDraft(text)
    setEditing(true)
  }
  const finish = (save: boolean) => {
    if (!editing) return
    setEditing(false)
    const value = draft.trim()
    if (save && value && value !== text) onSave(value)
  }
  const onKey = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape') finish(false)
    else if (event.key === 'Enter') {
      event.preventDefault()
      finish(true)
    }
  }

  if (editing) {
    return (
      <input
        ref={field}
        className="fa-input fa-inline-name__field"
        value={draft}
        aria-label={t('collection.name.field', { name: text })}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={onKey}
        onBlur={() => finish(true)}
      />
    )
  }
  return (
    <button
      type="button"
      className="fa-inline-name"
      title={t('collection.name.edit')}
      aria-label={`${t('collection.name.edit')}: ${text}`}
      disabled={readonly}
      onClick={start}
    >
      {text}
    </button>
  )
}
