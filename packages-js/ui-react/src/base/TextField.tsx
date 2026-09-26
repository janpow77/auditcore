import { useLayoutEffect, useRef, type CSSProperties, type FocusEvent, type KeyboardEvent, type Ref } from 'react'
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
  /** Wie `autofocus` in Vue: Attribut am Feld, Dialoge fokussieren es beim Öffnen. */
  autoFocus?: boolean
  /** Klasse und Stil am äußeren Element (wie durchgereichte Attribute in Vue). */
  className?: string
  style?: CSSProperties
  inputRef?: Ref<HTMLInputElement>
  onKeyDown?: (event: KeyboardEvent<HTMLInputElement>) => void
  onBlur?: (event: FocusEvent<HTMLInputElement>) => void
}

function fieldClass({ error, className }: TextFieldProps): string {
  return classes('fa-field', !!error && 'fa-field--error', className)
}

function assignRef(ref: Ref<HTMLInputElement> | undefined, element: HTMLInputElement | null): void {
  if (typeof ref === 'function') ref(element as HTMLInputElement)
  else if (ref) (ref as { current: HTMLInputElement | null }).current = element
}

/** Eingabefeld wie `FaTextField` (Beschriftung, Hinweis, Fehler mit aria-describedby). */
export function TextField(input: TextFieldProps) {
  const props = { type: 'text' as const, placeholder: '', ...input }
  const id = useElementId('fa-field')
  const own = useRef<HTMLInputElement | null>(null)
  const note = props.error || props.hint
  const autoFocus = props.autoFocus ?? false
  // React setzt `autoFocus` nicht als Attribut; Vue schon – Fokusfallen suchen `[autofocus]`.
  useLayoutEffect(() => {
    own.current?.toggleAttribute('autofocus', autoFocus)
  }, [autoFocus])
  const setRef = (element: HTMLInputElement | null): void => {
    own.current = element
    assignRef(props.inputRef, element)
  }
  return (
    <div className={fieldClass(props)} style={props.style}>
      <label htmlFor={id} className={classes('fa-field__label', props.hideLabel && 'fa-sr-only')}>{props.label}</label>
      <input
        ref={setRef}
        id={id}
        className="fa-field__input"
        type={props.type}
        placeholder={props.placeholder}
        disabled={props.disabled}
        required={props.required}
        aria-invalid={props.error ? 'true' : undefined}
        aria-describedby={note ? `${id}-note` : undefined}
        value={props.value}
        onChange={(event) => props.onChange(event.target.value)}
        onKeyDown={props.onKeyDown}
        onBlur={props.onBlur}
      />
      {note ? <p id={`${id}-note`} className="fa-field__note" role={props.error ? 'alert' : undefined}>{note}</p> : null}
    </div>
  )
}
