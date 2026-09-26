/**
 * Text input or text area that commits like Vue's `@change`: on blur and (for
 * inputs) on Enter, only when the text differs from the bound value. The DOM
 * value follows later changes of `value` without remounting the field.
 */

import { useLayoutEffect, useRef, type FocusEvent, type InputHTMLAttributes, type KeyboardEvent } from 'react'

type Field = HTMLInputElement | HTMLTextAreaElement

export interface CommitFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'value' | 'defaultValue' | 'onBlur' | 'onKeyDown'> {
  value: string
  onCommit: (raw: string) => void
  multiline?: boolean
  rows?: number
}

export function CommitField({ value, onCommit, multiline, rows, ...rest }: CommitFieldProps) {
  const ref = useRef<Field | null>(null)

  useLayoutEffect(() => {
    if (ref.current && ref.current.value !== value) ref.current.value = value
  }, [value])

  const commit = (event: FocusEvent<Field> | KeyboardEvent<Field>) => {
    const raw = event.currentTarget.value
    if (raw !== value) onCommit(raw)
  }

  if (multiline) {
    const { className, disabled, placeholder, readOnly } = rest
    return <textarea ref={(node) => void (ref.current = node)} className={className} rows={rows} disabled={disabled} placeholder={placeholder} readOnly={readOnly} defaultValue={value} onBlur={commit} />
  }
  return <input ref={(node) => void (ref.current = node)} {...rest} defaultValue={value} onBlur={commit} onKeyDown={(event) => event.key === 'Enter' && commit(event)} />
}
