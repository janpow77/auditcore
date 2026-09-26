/**
 * Overlays of the canvas: page break guides (display only), the popover for
 * colour and role choice, and the status bar below the canvas.
 */

import type { ReactNode } from 'react'
import type { ViewboxLike } from '@auditcore/bpmn-flowaudit'
import { pageGrid, popoverPosition } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { useI18n } from '../i18n'

export function PageGrid({ view, viewbox, width, height }: { view: string; viewbox: ViewboxLike; width: number; height: number }) {
  const { t } = useI18n()
  if (view === 'aus') return null
  const grid = pageGrid(view, viewbox, width, height, t('canvas.page'))
  return (
    <svg className="fa-page-grid" width={width} height={height} aria-hidden="true">
      {grid.vertical.map((x, index) => <line key={`v${index}`} x1={x} y1="0" x2={x} y2={height} />)}
      {grid.horizontal.map((y, index) => <line key={`h${index}`} x1="0" y1={y} x2={width} y2={y} />)}
      {grid.pages.map((page, index) => <text key={`p${index}`} x={page.x} y={page.y}>{page.label}</text>)}
    </svg>
  )
}

export interface CanvasPopoverProps {
  x: number
  y: number
  width: number
  height: number
  title: string
  onClose: () => void
  children?: ReactNode
}

export function CanvasPopover({ x, y, width, height, title, onClose, children }: CanvasPopoverProps) {
  return (
    <div className="fa-menu fa-canvas-popover" role="dialog" aria-label={title} style={popoverPosition(x, y, width, height)} onKeyDown={(event) => event.key === 'Escape' && onClose()} onMouseDown={(event) => event.stopPropagation()}>
      <p className="fa-label">{title}</p>
      {children}
    </div>
  )
}

export interface StatusBarProps {
  scale: number
  count: { fehler: number; warnung: number; hinweis: number }
  profile?: string
  message?: string
  onIssues?: () => void
}

export function StatusBar({ scale, count, profile, message, onIssues }: StatusBarProps) {
  const { t } = useI18n()
  return (
    <footer className="fa-statusbar">
      <button type="button" className="fa-statusbar__issues" onClick={onIssues}>
        <FaIcon name="error" size={14} />
        <span>{count.fehler}</span>
        <FaIcon name="warning" size={14} />
        <span>{count.warnung}</span>
        <FaIcon name="hint" size={14} />
        <span>{count.hinweis}</span>
        <span className="fa-sr-only">{t('editor.status.issues', { errors: count.fehler, warnings: count.warnung, notes: count.hinweis })}</span>
      </button>
      <span className="fa-statusbar__message" role="status" aria-live="polite">{message}</span>
      {profile ? <span className="fa-statusbar__item">{profile}</span> : null}
      <span className="fa-statusbar__item">{t('editor.status.zoom', { percent: Math.round(scale * 100) })}</span>
    </footer>
  )
}
