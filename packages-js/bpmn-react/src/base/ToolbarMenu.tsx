/**
 * Button with a popover menu: opens on click, closes on Escape, on click
 * outside and after choosing an item (`children` receives `close`).
 */

import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { classes } from '../hooks'
import { FaIcon } from './FaIcon'

export interface ToolbarMenuProps {
  label: string
  icon: string
  showLabel?: boolean
  align?: 'left' | 'right'
  children: (close: () => void) => ReactNode
}

export function ToolbarMenu({ label, icon, showLabel, align, children }: ToolbarMenuProps) {
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement | null>(null)
  const close = () => setOpen(false)

  useEffect(() => {
    const onDocument = (event: MouseEvent) => {
      if (root.current && !root.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDocument)
    return () => document.removeEventListener('mousedown', onDocument)
  }, [])

  const onKey = (event: KeyboardEvent) => {
    if (event.key !== 'Escape' || !open) return
    close()
    root.current?.querySelector<HTMLElement>('button')?.focus()
  }

  return (
    <div ref={root} className="fa-toolbar-menu" onKeyDown={onKey}>
      <button type="button" className={showLabel ? 'fa-btn fa-btn--ghost' : 'fa-icon-btn'} aria-label={label} title={label} aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen(!open)}>
        <FaIcon name={icon} />
        {showLabel ? <span>{label}</span> : null}
        {showLabel ? <FaIcon name="chevron-down" size={14} /> : null}
      </button>
      {open ? (
        <div className={classes('fa-menu', align === 'right' && 'fa-menu--right')} role="menu">
          {children(close)}
        </div>
      ) : null}
    </div>
  )
}
