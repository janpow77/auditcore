/**
 * Description shown as text; a click turns it into a text field. Enter or
 * leaving the field saves, Escape discards. Without a text a quiet
 * placeholder („Keine Beschreibung“) stands in its place.
 */

import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { classes } from '../hooks'
import { useI18n } from '../i18n'

export interface InlineDescriptionProps {
  text: string
  name: string
  readonly?: boolean
  onSave: (text: string) => void
}

export function InlineDescription({ text, name, readonly, onSave }: InlineDescriptionProps) {
  const { t } = useI18n()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const field = useRef<HTMLTextAreaElement | null>(null)

  useEffect(() => {
    if (editing) field.current?.focus()
  }, [editing])

  const start = () => {
    if (readonly) return
    setDraft(text)
    setEditing(true)
  }
  const finish = (save: boolean) => {
    if (!editing) return
    setEditing(false)
    if (save && draft.trim() !== text.trim()) onSave(draft.trim())
  }
  const onKey = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Escape') finish(false)
    else if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      finish(true)
    }
  }

  if (editing) {
    return (
      <textarea
        ref={field}
        className="fa-input fa-describe__field"
        rows={3}
        value={draft}
        aria-label={t('collection.description.field', { name })}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={onKey}
        onBlur={() => finish(true)}
      />
    )
  }
  return (
    <button
      type="button"
      className={classes('fa-describe', !text && 'fa-describe--empty')}
      title={text || t('collection.description.edit')}
      aria-label={`${t('collection.description.edit')}: ${name}`}
      disabled={readonly}
      onClick={start}
    >
      {text || t('collection.description.none')}
    </button>
  )
}
