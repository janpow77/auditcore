import type { KeyboardEvent } from 'react'
import { classes, useElementId } from '../store'

export interface TextFieldProps {
  label: string
  value: string
  onChange: (value: string) => void
  type?: 'text' | 'search' | 'email' | 'date' | 'number' | 'password'
  placeholder?: string
  hint?: string
  error?: string
  disabled?: boolean
  required?: boolean
  hideLabel?: boolean
  onKeyDown?: (event: KeyboardEvent<HTMLInputElement>) => void
}

/** Eingabefeld wie `FaTextField` (Beschriftung, Hinweis, Fehler mit aria-describedby). */
export function TextField(props: TextFieldProps) {
  const id = useElementId('fa-field')
  const note = props.error || props.hint
  return (
    <div className={classes('fa-field', !!props.error && 'fa-field--error')}>
      <label htmlFor={id} className={classes('fa-field__label', props.hideLabel && 'fa-sr-only')}>{props.label}</label>
      <input
        id={id}
        className="fa-field__input"
        type={props.type ?? 'text'}
        placeholder={props.placeholder ?? ''}
        disabled={props.disabled}
        required={props.required}
        aria-invalid={props.error ? 'true' : undefined}
        aria-describedby={note ? `${id}-note` : undefined}
        value={props.value}
        onChange={(event) => props.onChange(event.target.value)}
        onKeyDown={props.onKeyDown}
      />
      {note ? <p id={`${id}-note`} className="fa-field__note" role={props.error ? 'alert' : undefined}>{note}</p> : null}
    </div>
  )
}
