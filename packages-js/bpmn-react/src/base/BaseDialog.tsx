/**
 * Accessible modal dialog: `role="dialog"`, labelled by its title, closes on
 * Escape and backdrop click, keeps focus inside and returns it afterwards
 * (focus trap of @auditcore/ui-core, as in the Vue dialog).
 */

import { useEffect, useRef, type KeyboardEvent, type ReactNode } from 'react'
import { createFocusTrap } from '@auditcore/ui-core'
import { useElementId } from '../hooks'
import { useI18n } from '../i18n'
import { FaIcon } from './FaIcon'

export interface BaseDialogProps {
  open: boolean
  title: string
  width?: string
  subtitle?: string
  onOpenChange?: (open: boolean) => void
  onClose?: () => void
  footer?: ReactNode
  children?: ReactNode
}

export function BaseDialog({ open, title, width = '640px', subtitle = '', onOpenChange, onClose, footer, children }: BaseDialogProps) {
  const { t } = useI18n()
  const panel = useRef<HTMLElement | null>(null)
  const titleId = useElementId('fa-dialog')

  useEffect(() => {
    if (!open) return undefined
    const trap = createFocusTrap(() => panel.current)
    trap.activate()
    return () => trap.deactivate()
  }, [open])

  if (!open) return null

  const close = () => {
    onOpenChange?.(false)
    onClose?.()
  }

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key !== 'Escape') return
    event.stopPropagation()
    close()
  }

  return (
    <div className="fa-dialog-backdrop" onMouseDown={(event) => event.target === event.currentTarget && close()}>
      <section ref={panel} className="fa-dialog" role="dialog" aria-modal="true" aria-labelledby={titleId} style={{ width }} onKeyDown={onKeyDown}>
        <header className="fa-dialog__head">
          <div>
            <h2 id={titleId} className="fa-dialog__title">{title}</h2>
            {subtitle ? <p className="fa-dialog__subtitle">{subtitle}</p> : null}
          </div>
          <button type="button" className="fa-icon-btn" aria-label={t('common.close')} onClick={close}>
            <FaIcon name="close" />
          </button>
        </header>
        <div className="fa-dialog__body">{children}</div>
        {footer ? <footer className="fa-dialog__foot">{footer}</footer> : null}
      </section>
    </div>
  )
}
