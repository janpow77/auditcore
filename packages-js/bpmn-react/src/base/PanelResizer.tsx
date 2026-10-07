/**
 * Handle between a side panel and the main area: drag (pointer), arrows or
 * Home/End to resize, double click for the standard width, the small button
 * collapses the panel. A collapsed panel leaves a narrow rail to show it
 * again – React counterpart of the Vue `PanelResizer`.
 */

import { useRef, useState, type KeyboardEvent, type PointerEvent } from 'react'
import { dragWidth, keyWidth, type PanelBounds, type PanelEdge } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from './FaIcon'
import { useI18n } from '../i18n'

export interface PanelResizerProps {
  width: number
  open: boolean
  bounds: PanelBounds
  edge: PanelEdge
  name: string
  onWidthChange: (width: number) => void
  onOpenChange: (open: boolean) => void
}

function Rail({ edge, name, onOpenChange }: Pick<PanelResizerProps, 'edge' | 'name' | 'onOpenChange'>) {
  const { t } = useI18n()
  const label = t('panel.expand', { name })
  return (
    <div className={`fa-panel-rail fa-panel-rail--${edge}`}>
      <button type="button" className="fa-panel-rail__button" title={label} aria-label={label} onClick={() => onOpenChange(true)}>
        <FaIcon name={edge === 'right' ? 'panel-right' : 'panel-left'} size={16} />
        <span className="fa-panel-rail__label">{name}</span>
      </button>
    </div>
  )
}

export function PanelResizer(props: PanelResizerProps) {
  const { t } = useI18n()
  const drag = useRef<{ x: number; width: number } | null>(null)
  const [active, setActive] = useState(false)
  if (!props.open) return <Rail edge={props.edge} name={props.name} onOpenChange={props.onOpenChange} />
  const collapse = t('panel.collapse', { name: props.name })

  const start = (event: PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) return
    drag.current = { x: event.clientX, width: props.width }
    setActive(true)
    event.currentTarget.setPointerCapture?.(event.pointerId)
    event.preventDefault()
  }
  const move = (event: PointerEvent<HTMLDivElement>) => {
    if (drag.current) props.onWidthChange(dragWidth(drag.current.width, drag.current.x, event.clientX, props.edge, props.bounds))
  }
  const stop = (event: PointerEvent<HTMLDivElement>) => {
    drag.current = null
    setActive(false)
    event.currentTarget.releasePointerCapture?.(event.pointerId)
  }
  const onKey = (event: KeyboardEvent<HTMLDivElement>) => {
    const width = keyWidth(props.width, event.key, props.edge, props.bounds)
    if (width === null) return
    event.preventDefault()
    props.onWidthChange(width)
  }

  return (
    <div
      className={`fa-resizer fa-resizer--${props.edge}${active ? ' fa-resizer--active' : ''}`}
      role="separator"
      aria-orientation="vertical"
      tabIndex={0}
      aria-label={t('panel.resize', { name: props.name })}
      aria-valuemin={props.bounds.min}
      aria-valuemax={props.bounds.max}
      aria-valuenow={props.width}
      onPointerDown={start}
      onPointerMove={move}
      onPointerUp={stop}
      onPointerCancel={stop}
      onKeyDown={onKey}
      onDoubleClick={() => props.onWidthChange(props.bounds.initial)}
    >
      <button
        type="button"
        className="fa-resizer__toggle"
        title={collapse}
        aria-label={collapse}
        onPointerDown={(event) => event.stopPropagation()}
        onDoubleClick={(event) => event.stopPropagation()}
        onClick={() => props.onOpenChange(false)}
      >
        <FaIcon name={props.edge === 'right' ? 'chevron-right' : 'chevron-left'} size={12} />
      </button>
    </div>
  )
}
