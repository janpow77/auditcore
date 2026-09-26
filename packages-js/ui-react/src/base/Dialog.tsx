import { useEffect, useRef, type KeyboardEvent, type MouseEvent, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { baseMessages, trapFocus, type Locale } from '@flowaudit/ui-core'
import { useTranslation } from '../i18n'
import { useElementId } from '../store'
import { Button } from './Button'

export interface DialogProps {
  open: boolean
  title: string
  description?: string
  size?: 'sm' | 'md' | 'lg'
  /** Seitliches Panel statt zentriertem Dialog. */
  placement?: 'center' | 'side'
  closeOnBackdrop?: boolean
  locale?: Locale
  footer?: ReactNode
  children?: ReactNode
  onClose: () => void
}

function DialogPanel(props: DialogProps) {
  const { t } = useTranslation(baseMessages, props.locale)
  const panel = useRef<HTMLElement | null>(null)
  const titleId = useElementId('fa-dialog-title')
  const descriptionId = useElementId('fa-dialog-description')
  // Wie `useFocusTrap` der Vue-Fassung: Fokus halten und beim Schließen zurückgeben.
  useEffect(() => (panel.current ? trapFocus(panel.current) : undefined), [])
  const onBackdrop = (event: MouseEvent<HTMLDivElement>): void => {
    if ((props.closeOnBackdrop ?? true) && event.target === event.currentTarget) props.onClose()
  }
  const onKeyDown = (event: KeyboardEvent<HTMLElement>): void => {
    if (event.key !== 'Escape') return
    event.stopPropagation()
    event.preventDefault()
    props.onClose()
  }
  return (
    <div className={`fa-dialog fa-dialog--${props.placement ?? 'center'}`} onMouseDown={onBackdrop}>
      <section
        ref={panel}
        className={`fa-dialog__panel fa-dialog__panel--${props.size ?? 'md'}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={props.description ? descriptionId : undefined}
        tabIndex={-1}
        onKeyDown={onKeyDown}
      >
        <header className="fa-dialog__header">
          <div>
            <h2 id={titleId} className="fa-dialog__title">{props.title}</h2>
            {props.description ? <p id={descriptionId} className="fa-dialog__description">{props.description}</p> : null}
          </div>
          <Button variant="ghost" icon="close" iconOnly label={t('close')} onClick={props.onClose} />
        </header>
        <div className="fa-dialog__body">{props.children}</div>
        {props.footer ? <footer className="fa-dialog__footer">{props.footer}</footer> : null}
      </section>
    </div>
  )
}

/** Dialog wie `FaDialog` (gleiche Klassen, ARIA, Fokusfalle, Escape, Klick auf den Hintergrund), im `body`. */
export function Dialog(props: DialogProps) {
  if (!props.open || typeof document === 'undefined') return null
  return createPortal(<DialogPanel {...props} />, document.body)
}
