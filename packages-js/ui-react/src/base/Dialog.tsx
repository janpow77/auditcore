import { useEffect, useRef, type KeyboardEvent, type MouseEvent, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { baseMessages, createFocusTrap, type Locale } from '@flowaudit/ui-core'
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
  /** Schließen per Schaltfläche, Escape oder Hintergrund (Gegenstück zu `update:open`/`close`). */
  onClose: () => void
  footer?: ReactNode
  children?: ReactNode
}

function useTrap(open: boolean) {
  const panel = useRef<HTMLElement | null>(null)
  useEffect(() => {
    if (!open) return undefined
    const trap = createFocusTrap(() => panel.current)
    trap.activate()
    return trap.deactivate
  }, [open])
  return panel
}

/** Modaler Dialog wie `FaDialog`: Fokusfalle, Escape, Rückgabe des Fokus, beschriftet über Titel und Beschreibung. */
export function Dialog(props: DialogProps) {
  const { open, title, description = '', size = 'md', placement = 'center', closeOnBackdrop = true } = props
  const panel = useTrap(open)
  const titleId = useElementId('fa-dialog-title')
  const descriptionId = useElementId('fa-dialog-description')
  const { t } = useTranslation(baseMessages, props.locale)
  if (!open) return null
  const onBackdrop = (event: MouseEvent<HTMLDivElement>): void => {
    if (closeOnBackdrop && event.target === event.currentTarget) props.onClose()
  }
  const onKeyDown = (event: KeyboardEvent<HTMLElement>): void => {
    if (event.key !== 'Escape') return
    event.stopPropagation()
    event.preventDefault()
    props.onClose()
  }
  return createPortal(
    <div className={`fa-dialog fa-dialog--${placement}`} onMouseDown={onBackdrop}>
      <section ref={panel} className={`fa-dialog__panel fa-dialog__panel--${size}`} role="dialog" aria-modal="true" aria-labelledby={titleId} aria-describedby={description ? descriptionId : undefined} tabIndex={-1} onKeyDown={onKeyDown}>
        <header className="fa-dialog__header">
          <div>
            <h2 id={titleId} className="fa-dialog__title">{title}</h2>
            {description ? <p id={descriptionId} className="fa-dialog__description">{description}</p> : null}
          </div>
          <Button variant="ghost" icon="close" iconOnly label={t('close')} onClick={props.onClose} />
        </header>
        <div className="fa-dialog__body">{props.children}</div>
        {props.footer ? <footer className="fa-dialog__footer">{props.footer}</footer> : null}
      </section>
    </div>,
    document.body,
  )
}
